"""
[9단계] 배포용 변환 (ONNX / NCNN) + 변환 결과 검증

라즈베리파이 CPU 에서는 PyTorch(.pt) 보다 NCNN / ONNX 가 2~4배 빠릅니다.
변환 후 같은 test 이미지로 원본(.pt)과 결과를 비교해 '변환해도 정확도가 유지되는지' 확인합니다.

출력:
  models/best.onnx
  models/best_ncnn_model/   (폴더 통째로 라즈베리파이에 복사)
  reports/export_check.md

사용 예:
  python scripts/09_export.py                             # 값을 하나씩 물어봄 (엔터 = 기본값)
  python scripts/09_export.py -y                          # 묻지 않고 기본값으로 바로 실행
  python scripts/09_export.py --formats ncnn --imgsz 320  # 준 값은 묻지 않음

처리 흐름:
  1) 인자/설정 로드 → 변환 형식, imgsz, conf, 원본 가중치 결정 (CLI > config)
     → 명령행으로 주지 않은 값은 터미널에서 물어봄 (엔터 = 기본값, -y 면 생략)
  2) 비교용 샘플 이미지 준비 (test split, 없으면 val split 에서 최대 n-check 장)
  3) 원본 .pt 로 기준(reference) 결과 + 평균 지연시간 측정
  4) 형식마다: export → 변환된 모델 로드 → 같은 이미지로 추론 → 지연시간 / 일치율 계산
  5) 콘솔 표 + reports/export_check.md 저장

'일치율' 정의:
  이미지마다 '탐지된 클래스 ID 를 정렬한 리스트'가 .pt 결과와 완전히 같으면 일치로 봅니다.
  (박스 좌표·신뢰도 차이는 보지 않는 단순 지표 — 클래스/개수가 바뀌는 큰 변화를 잡아내는 용도)

자세한 구조 분석: scripts/09_export.md
"""
from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path

import cv2

from common import (add_config_arg, add_yes_arg, ask, banner, default_weights, interactive,
                    list_images, load_config, path_of)


def evaluate(model, images, imgsz, conf):
    """이미지별 (클래스 집합) 과 평균 지연시간.

    model : Ultralytics YOLO 객체 (.pt / .onnx / ncnn 무엇이든 같은 API)
    images: BGR ndarray 리스트 (디스크 I/O 를 시간 측정에서 빼기 위해 미리 읽어 둔 것)
    반환  : (dets, mean_ms)
            dets    = [[정렬된 클래스 ID...], ...]  이미지 순서대로
            mean_ms = 이미지 1장 평균 추론 시간(ms, CPU)
    """
    dets, ts = [], []
    # 워밍업 1회: 첫 추론은 모델 초기화/메모리 할당 때문에 느리므로 측정에서 제외
    model.predict(images[0], imgsz=imgsz, conf=conf, device="cpu", verbose=False)
    for im in images:
        t0 = time.perf_counter()
        r = model.predict(im, imgsz=imgsz, conf=conf, device="cpu", verbose=False)[0]
        ts.append((time.perf_counter() - t0) * 1000)          # 초 → ms
        # 비교를 위해 탐지 클래스 ID 를 정렬 (탐지 순서가 달라도 같은 결과로 취급)
        dets.append(sorted(int(c) for c in r.boxes.cls.tolist()))
    return dets, statistics.mean(ts)


def main():
    """CLI 진입점: 원본 기준 측정 → 형식별 변환·검증 → 리포트 작성."""
    # ── 1) 인자 / 설정 ──
    ap = add_config_arg(argparse.ArgumentParser(description=__doc__,
                                                formatter_class=argparse.RawDescriptionHelpFormatter))
    ap.add_argument("--weights")
    ap.add_argument("--formats", nargs="+", help="onnx ncnn openvino tflite ...")
    ap.add_argument("--imgsz", type=int)
    ap.add_argument("--n-check", type=int, default=30, help="비교에 쓸 test 이미지 수")
    add_yes_arg(ap)
    args = ap.parse_args()

    cfg = load_config(args.config)
    ec = cfg.get("export", {})
    formats = args.formats or ec.get("formats", ["onnx"])
    imgsz = args.imgsz or ec.get("imgsz", 320)                 # 변환 시 입력 크기가 '고정'됨 → 운영과 같게
    conf = cfg.get("predict", {}).get("conf", 0.5)            # 비교도 실제 운영 conf 로
    weights = Path(args.weights) if args.weights else default_weights(cfg)

    # ── 1-1) 대화형 입력: 명령행으로 주지 않은 값만 물어봄 (엔터 = 기본값) ──
    #   -y 를 주었거나, 터미널이 아닌 환경(파이프/run_pipeline 등)에서는 묻지 않음
    if interactive(args):
        print("\n  변환 설정 (그냥 엔터 → [ ] 안의 기본값 사용)")
        if args.weights is None:
            weights = Path(ask("원본 모델(weights)", weights))
        if args.formats is None:
            # 여러 개는 공백 또는 쉼표로 구분: "onnx ncnn" / "onnx,ncnn"
            formats = ask("formats (onnx ncnn openvino tflite ...)", " ".join(formats))
            formats = formats.replace(",", " ").split() or ["onnx"]
        if args.imgsz is None:
            imgsz = ask("imgsz (운영 입력 크기와 같게)", imgsz, int)

    from ultralytics import YOLO               # 무거운 import 는 인자 파싱·입력 뒤에

    banner("9단계", f"배포용 변환 {formats} (imgsz={imgsz})")
    if not weights.exists():
        sys.exit(f"[ERROR] 모델이 없습니다: {weights}")

    # ── 2) 비교용 샘플 이미지 (test 우선, 없으면 val) ──
    ds = path_of(cfg, "dataset")
    sample = list_images(ds / "images" / "test")[:args.n_check] or list_images(ds / "images" / "val")[:args.n_check]
    images = [cv2.imread(str(p)) for p in sample]
    images = [im for im in images if im is not None]           # 읽기 실패한 파일 제거

    # ── 3) 원본(.pt) 기준 결과 ──
    base = YOLO(str(weights))
    results = []                                               # (형식, 경로, 평균 ms, 일치율)
    ref_dets, ref_ms = evaluate(base, images, imgsz, conf) if images else ([], 0)
    results.append(("pytorch (.pt)", str(weights), ref_ms, 1.0))   # 기준이므로 일치율 100%

    # ── 4) 형식별 변환 + 검증 ──
    for fmt in formats:
        try:
            # export 결과는 원본 가중치 옆에 생성됨 (models/best.onnx, models/best_ncnn_model/ ...)
            out = base.export(format=fmt, imgsz=imgsz, half=ec.get("half", False), device="cpu")
        except Exception as e:  # 패키지 미설치 등
            print(f"  ❌ {fmt} 변환 실패: {e}")
            results.append((fmt, f"실패: {e}", 0, 0))
            continue                                           # 한 형식이 실패해도 나머지는 계속
        print(f"  ✅ {fmt}: {out}")
        if not images:
            # 비교할 이미지가 없으면 변환만 하고 검증은 생략
            results.append((fmt, str(out), 0, 0))
            continue
        # 변환 모델은 메타데이터만으로 task 를 알 수 없을 수 있어 'detect' 를 명시
        exp = YOLO(str(out), task="detect")
        dets, ms = evaluate(exp, images, imgsz, conf)
        # 이미지별로 '정렬된 클래스 리스트'가 완전히 같은 비율
        agree = sum(a == b for a, b in zip(ref_dets, dets)) / len(dets)
        results.append((fmt, str(out), ms, agree))

    # ── 5) 결과 출력 + 리포트 ──
    print(f"\n  {'형식':<16}{'평균 지연(ms)':>14}{'.pt 와 결과 일치율':>20}")
    for fmt, _, ms, agree in results:
        print(f"  {fmt:<16}{ms:>14.1f}{agree:>19.0%}")
    if images:
        print(f"  (이 PC CPU 기준, test 이미지 {len(images)} 장. 라즈베리파이에서는 08_predict.py --benchmark 로 재측정)")

    md = ["# 변환 결과 검증", "", f"- 원본: `{weights}`", f"- imgsz={imgsz}, conf={conf}, 비교 이미지 {len(images)} 장",
          "", "| 형식 | 경로 | 평균 지연(ms, CPU) | .pt 와 탐지 결과 일치율 |", "|---|---|---|---|"]
    md += [f"| {f} | `{p}` | {ms:.1f} | {a:.0%} |" for f, p, ms, a in results]
    md += ["", "> 일치율이 95% 미만이면 half=false 확인, imgsz 를 학습/운영과 동일하게 맞추세요."]
    rp = path_of(cfg, "reports")
    rp.mkdir(parents=True, exist_ok=True)
    (rp / "export_check.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\n  리포트: {rp / 'export_check.md'}")
    print("  라즈베리파이 배포: models/best.pt (또는 best_ncnn_model/) → source/models/yolo/ 로 복사")


if __name__ == "__main__":
    main()
