"""
[8단계] 추론 (이미지 / 폴더 / 동영상 / 카메라) + 속도 측정

새로운 데이터(학습에 쓰지 않은 실제 주행 영상 등)에 모델을 적용해 결과를 눈으로 확인합니다.
디스플레이가 없는 라즈베리파이(SSH)에서도 동작합니다 (--show 없이 실행하면 파일로만 저장).

입력:
  --weights : .pt / *_ncnn_model / .onnx  (기본: models/best.pt)
  --source  : 이미지 파일 / 폴더 / 동영상 / 카메라 번호 / rtsp·http 스트림

출력:
  runs/predict/<날짜_시간>/  — 박스를 그린 이미지(원본 이름) 또는 result.mp4

처리 흐름 (main):
  1) 설정 로드 — conf / imgsz / device (.pt 가 아니면 CPU 고정)
     → 명령행으로 주지 않은 값은 터미널에서 물어봄 (엔터 = 기본값, -y 면 생략)
  2) 모델 로드
  3) --benchmark N 이면 속도만 측정하고 종료
  4) 소스 종류 판별
     4-a) 카메라/동영상/스트림 → 프레임 루프 (FPS 표시, mp4 저장, 화면 표시)
     4-b) 이미지/폴더          → 파일별 추론, 결과 이미지 저장, 탐지 목록 출력
  5) 평균 추론 시간·탐지 횟수 요약 출력

사용 예:
  python scripts/08_predict.py                                    # 값을 하나씩 물어봄 (엔터 = 기본값,
                                                                  #   source 기본 = test 이미지 폴더)
  python scripts/08_predict.py --source datasets/raspbot/images/test
  python scripts/08_predict.py --source drive.mp4
  python scripts/08_predict.py --source 0 --show                 # USB 카메라
  python scripts/08_predict.py --source 0 --max-frames 300        # 헤드리스, 300프레임 저장
  python scripts/08_predict.py --weights models/best_ncnn_model --source 0 --show
  python scripts/08_predict.py --benchmark 100                    # 속도만 측정
"""
from __future__ import annotations

import argparse
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

from common import (IMG_EXTS, VIDEO_EXTS, add_config_arg, add_yes_arg, ask, banner,
                    default_weights, has_display, interactive, list_images, load_config, path_of,
                    pick_device)


def benchmark(model, imgsz, device, n):
    """무작위 이미지로 n 회 추론해 지연시간 통계(평균/중앙값/p95/FPS)를 출력.

    카메라·디스크 I/O 없이 순수 모델 속도만 재므로 기기 간(PC vs 라즈베리파이) 비교에 적합합니다.
    """
    img = (np.random.rand(240, 320, 3) * 255).astype(np.uint8)   # Raspbot 카메라 해상도
    for _ in range(5):                         # 워밍업 5회 (초기화 비용을 통계에서 제외)
        model.predict(img, imgsz=imgsz, device=device, verbose=False)
    ts = []
    for _ in range(n):
        t0 = time.perf_counter()
        model.predict(img, imgsz=imgsz, device=device, verbose=False)
        ts.append((time.perf_counter() - t0) * 1000)   # ms 단위
    ts.sort()                                  # 정렬해 두면 중앙값·p95 를 인덱스로 바로 구할 수 있음
    print(f"  {n}회 | 평균 {statistics.mean(ts):.1f}ms | 중앙값 {ts[n // 2]:.1f}ms | "
          f"p95 {ts[int(0.95 * (n - 1))]:.1f}ms | ≈ {1000 / statistics.mean(ts):.1f} FPS")


def main():
    """8단계 실행: 이미지/폴더/동영상/카메라에 모델을 적용하고 결과를 저장·표시한다."""
    ap = add_config_arg(argparse.ArgumentParser(description=__doc__,
                                                formatter_class=argparse.RawDescriptionHelpFormatter))
    ap.add_argument("--weights", help="모델 (.pt / *_ncnn_model / .onnx). 기본: models/best.pt")
    ap.add_argument("--source", help="이미지/폴더/동영상 경로 또는 카메라 번호(0)")
    ap.add_argument("--conf", type=float)
    ap.add_argument("--imgsz", type=int)
    ap.add_argument("--device")
    ap.add_argument("--show", action="store_true", help="화면에 표시")
    ap.add_argument("--no-save", action="store_true", help="결과 파일 저장 안 함")
    ap.add_argument("--max-frames", type=int, default=0, help="동영상/카메라 최대 프레임 (0=끝까지)")
    ap.add_argument("--benchmark", type=int, default=0, help="N회 반복 속도 측정만 수행")
    add_yes_arg(ap)
    args = ap.parse_args()

    # ── 1) 설정 로드 ──  우선순위: 명령행 > config > 기본값
    cfg = load_config(args.config)
    pc = cfg.get("predict", {})
    conf = args.conf or pc.get("conf", 0.5)
    imgsz = args.imgsz or pc.get("imgsz", 320)
    weights = Path(args.weights) if args.weights else default_weights(cfg)
    device_pref = args.device or cfg["train"].get("device", "auto")

    # ── 1-1) 대화형 입력: 명령행으로 주지 않은 값만 물어봄 (엔터 = 기본값) ──
    #   -y 를 주었거나, 터미널이 아닌 환경에서는 묻지 않음 (이때 --source 는 필수)
    if interactive(args):
        print("\n  추론 설정 (그냥 엔터 → [ ] 안의 기본값 사용)")
        if args.weights is None:
            weights = Path(ask("모델(weights) (.pt / *_ncnn_model / .onnx)", weights))
        if args.source is None and not args.benchmark:
            # 기본 소스 = 4단계에서 만든 test 이미지 폴더 (카메라는 0, 동영상은 파일 경로 입력)
            args.source = ask("source (이미지/폴더/동영상 경로, 카메라=0)",
                              str(path_of(cfg, "dataset") / "images" / "test"))
        if args.conf is None:
            conf = ask("conf (신뢰도 임계값 0~1)", conf, float)
        if args.imgsz is None:
            imgsz = ask("imgsz", imgsz, int)
        if args.device is None and weights.suffix == ".pt":   # 변환 모델은 어차피 cpu 고정
            device_pref = ask("device (auto/cpu/mps/0)", device_pref)

    # ultralytics 는 import 가 무거워서(torch 로드) --help / 입력 단계가 빠르도록 이 시점에 import
    from ultralytics import YOLO

    is_pt = weights.suffix == ".pt"
    # 변환 모델(NCNN/ONNX)은 CPU 용으로 만들었으므로 device 를 cpu 로 고정
    device = pick_device(device_pref) if is_pt else "cpu"

    # ── 2) 모델 로드 ──
    banner("8단계", "추론 / 속도 측정")
    if not weights.exists():
        sys.exit(f"[ERROR] 모델이 없습니다: {weights}")
    # task="detect": 변환 모델은 메타데이터에서 작업 종류를 못 읽을 수 있어 명시
    model = YOLO(str(weights), task="detect")
    print(f"  모델: {weights} | conf {conf} | imgsz {imgsz} | device {device}")

    # ── 3) 속도 측정 모드 ──
    if args.benchmark:
        benchmark(model, imgsz, device, args.benchmark)
        return
    if args.source is None:
        sys.exit("[ERROR] --source 를 지정하세요 (또는 --benchmark N)")
    if args.show and not has_display():        # SSH 등 화면 없는 환경에서 imshow 오류 방지
        print("  [WARN] 화면이 없어 --show 를 무시합니다 (헤드리스 모드).")
        args.show = False

    # 실행할 때마다 시간별 새 폴더 → 이전 결과를 덮어쓰지 않음
    out_dir = path_of(cfg, "runs") / "predict" / time.strftime("%Y%m%d_%H%M%S")
    if not args.no_save:
        out_dir.mkdir(parents=True, exist_ok=True)
    counts, frame_ms = Counter(), []           # 클래스별 탐지 횟수 / 프레임별 추론 시간(ms)

    def run(frame):
        """프레임 1장 추론 → 시간·클래스별 탐지 수를 기록하고 Ultralytics 결과 객체를 반환."""
        t0 = time.perf_counter()
        r = model.predict(frame, conf=conf, imgsz=imgsz, device=device, verbose=False)[0]
        frame_ms.append((time.perf_counter() - t0) * 1000)
        for c in r.boxes.cls.tolist():
            counts[model.names[int(c)]] += 1
        return r

    # ── 4) 소스 종류 판별 ──
    src = args.source
    src_path = Path(src)
    # 숫자("0") = 카메라 번호, 동영상 확장자, 네트워크 스트림 → 프레임 루프로 처리
    if src.isdigit() or src_path.suffix.lower() in VIDEO_EXTS or src.startswith(("rtsp://", "http")):
        # ── 4-a) 카메라 / 동영상 / 스트림 ──
        cap = cv2.VideoCapture(int(src) if src.isdigit() else src)
        if not cap.isOpened():
            sys.exit(f"[ERROR] 소스를 열 수 없습니다: {src}")
        fps_in = cap.get(cv2.CAP_PROP_FPS) or 15   # 카메라가 FPS 를 0 으로 알려주면 15 로 가정
        writer, n = None, 0
        print("  실행 중... (화면 모드: q 종료 / 헤드리스: Ctrl+C 종료)")
        try:
            while True:
                ok, frame = cap.read()
                if not ok:                     # 동영상 끝 또는 카메라 끊김
                    break
                vis = run(frame).plot()        # .plot() = 박스·라벨이 그려진 BGR 이미지
                fps = 1000 / statistics.mean(frame_ms[-30:])   # 최근 30프레임 이동평균 FPS
                cv2.putText(vis, f"{fps:.1f} FPS", (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                if not args.no_save:
                    if writer is None:         # 첫 프레임에서 크기를 알고 나서 VideoWriter 생성
                        h, w = vis.shape[:2]
                        writer = cv2.VideoWriter(str(out_dir / "result.mp4"),
                                                 cv2.VideoWriter_fourcc(*"mp4v"), fps_in, (w, h))
                    writer.write(vis)
                if args.show:
                    cv2.imshow("YOLO11 predict", vis)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                n += 1
                if n % 30 == 0 and not args.show:   # 헤드리스일 때 30프레임마다 진행 상황 한 줄 갱신
                    print(f"  frame {n} | {fps:.1f} FPS | 누적 {dict(counts)}", end="\r")
                if args.max_frames and n >= args.max_frames:
                    break
        except KeyboardInterrupt:              # Ctrl+C 로 멈춰도 아래에서 파일을 정상 마무리
            pass
        cap.release()
        if writer:
            writer.release()                   # release 해야 mp4 파일이 올바르게 닫힘
        print(f"\n  처리 프레임: {n}")
    else:
        # ── 4-b) 이미지 파일 / 폴더 ──
        files = list_images(src_path) if src_path.is_dir() else (
            [src_path] if src_path.suffix.lower() in IMG_EXTS else [])
        if not files:
            sys.exit(f"[ERROR] 이미지가 없습니다: {src}")
        for f in files:
            img = cv2.imread(str(f))
            if img is None:                    # 깨진 이미지는 건너뜀
                continue
            r = run(img)
            vis = r.plot()
            if not args.no_save:
                cv2.imwrite(str(out_dir / f.name), vis)
            if args.show:
                cv2.imshow("YOLO11 predict", vis)
                if cv2.waitKey(0) & 0xFF == ord("q"):   # waitKey(0): 키를 누를 때까지 한 장씩 보기
                    break
            # "클래스:신뢰도" 목록 (탐지 없으면 "-")
            dets = ", ".join(f"{model.names[int(c)]}:{s:.2f}" for c, s in
                             zip(r.boxes.cls.tolist(), r.boxes.conf.tolist())) or "-"
            print(f"  {f.name}: {dets}")
        print(f"  처리 이미지: {len(files)}")

    # ── 5) 요약 출력 ──
    if args.show:
        cv2.destroyAllWindows()
    if frame_ms:
        print(f"  평균 추론 {statistics.mean(frame_ms):.1f}ms (≈ {1000 / statistics.mean(frame_ms):.1f} FPS)")
    print(f"  탐지 횟수: {dict(counts) or '없음'}")
    if not args.no_save:
        print(f"  결과 저장: {out_dir}")


if __name__ == "__main__":
    main()
