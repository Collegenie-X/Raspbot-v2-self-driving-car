"""
[6단계] 모델 검증 — 표준 지표(mAP)로 합격/불합격 판정

Ultralytics model.val() 로 정답 라벨과 비교하여 지표를 계산하고,
config 의 validate.thresholds 와 비교해 PASS / FAIL 을 판정합니다.

  Precision    : 모델이 "있다"고 한 것 중 실제로 맞은 비율   (오탐이 적을수록 ↑)
  Recall       : 실제 객체 중 모델이 찾아낸 비율             (놓친 게 적을수록 ↑)
  mAP50        : IoU 0.5 기준 평균 정밀도 (탐지 성공 여부)
  mAP50-95     : IoU 0.5~0.95 평균 (박스 위치 정확도까지 반영, 더 엄격)

입력:
  models/best.pt (5단계 결과)  +  datasets/raspbot/data.yaml (4단계 결과)

출력:
  reports/validate_<split>.md / .json
  runs/val/<split>/ (PR 곡선, 혼동행렬, 예측 샘플 이미지)
종료 코드: PASS=0, FAIL=2  (자동화 파이프라인에서 사용)

처리 흐름 (main):
  1) 설정 로드 — 가중치/데이터/imgsz/device/합격 기준
     → 명령행으로 주지 않은 값은 터미널에서 물어봄 (엔터 = 기본값, -y 면 생략)
  2) model.val() 실행 → 정답 라벨과 비교해 지표 계산
  3) 전체 지표 + 클래스별 지표 정리
  4) 합격 기준(thresholds)과 비교 → PASS / FAIL
  5) 콘솔 출력 (클래스별 표, 속도, 합격 기준)
  6) 리포트 저장 (.json / .md) 후 종료 코드 반환

사용 예:
  python scripts/06_validate.py                 # 값을 하나씩 물어봄 (엔터 = 기본값, split=val)
  python scripts/06_validate.py -y              # 묻지 않고 기본값으로 바로 실행
  python scripts/06_validate.py --split test    # 최종 시험 (준 값은 묻지 않음)
  python scripts/06_validate.py --weights models/best.pt
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from common import (add_config_arg, add_yes_arg, ask, banner, data_yaml_path, default_weights,
                    interactive, load_config, path_of, pick_device)

SPLITS = ["train", "val", "test"]


def f1(p, r):
    """F1 점수 = Precision 과 Recall 의 조화평균 (둘 중 하나라도 낮으면 낮아짐). 분모 0 이면 0."""
    return 2 * p * r / (p + r) if p + r > 0 else 0.0


def main():
    """6단계 실행: model.val() 로 지표를 계산하고 합격 기준과 비교해 PASS/FAIL 을 판정한다."""
    ap = add_config_arg(argparse.ArgumentParser(description=__doc__,
                                                formatter_class=argparse.RawDescriptionHelpFormatter))
    ap.add_argument("--weights", help="검증할 모델 (기본: models/best.pt)")
    ap.add_argument("--split", choices=SPLITS, help="검증할 데이터 (기본: val)")
    ap.add_argument("--imgsz", type=int)
    ap.add_argument("--device")
    add_yes_arg(ap)
    args = ap.parse_args()

    # ── 1) 설정 로드 ──
    cfg = load_config(args.config)
    vc = cfg.get("validate", {})
    th = vc.get("thresholds", {})               # 합격 기준 (예: map50 ≥ 0.80)
    # 우선순위: 명령행 > config > 기본값
    weights = Path(args.weights) if args.weights else default_weights(cfg)
    split = args.split or "val"
    imgsz = args.imgsz or vc.get("imgsz", 640)
    device_pref = args.device or cfg["train"].get("device", "auto")

    # ── 1-1) 대화형 입력: 명령행으로 주지 않은 값만 물어봄 (엔터 = 기본값) ──
    #   -y 를 주었거나, 터미널이 아닌 환경(파이프/run_pipeline 등)에서는 묻지 않음
    if interactive(args):
        print("\n  검증 설정 (그냥 엔터 → [ ] 안의 기본값 사용)")
        if args.weights is None:
            weights = Path(ask("모델(weights)", weights))
        if args.split is None:
            split = ask("split", split, choices=SPLITS)
        if args.imgsz is None:
            imgsz = ask("imgsz", imgsz, int)
        if args.device is None:
            device_pref = ask("device (auto/cpu/mps/0)", device_pref)

    # ultralytics 는 import 가 무거워서(torch 로드) --help / 입력 단계가 빠르도록 이 시점에 import
    from ultralytics import YOLO

    data_yaml = data_yaml_path(cfg)
    device = pick_device(device_pref)

    banner("6단계", f"모델 검증 (split={split})")
    for p in (weights, data_yaml):
        if not p.exists():
            sys.exit(f"[ERROR] 파일이 없습니다: {p}")

    # ── 2) model.val() 실행 ──
    model = YOLO(str(weights))
    # conf=0.001: mAP 는 '모든 신뢰도 구간'의 PR 곡선 면적이므로 낮은 conf 예측까지 포함하는 것이 표준
    # iou=0.6: NMS(겹친 박스 제거) 기준
    m = model.val(data=str(data_yaml), split=split, imgsz=imgsz,
                  conf=vc.get("conf", 0.001), iou=vc.get("iou", 0.6), device=device,
                  project=str(path_of(cfg, "runs") / "val"), name=split, exist_ok=True,
                  plots=True, verbose=False)

    # ── 3) 전체 / 클래스별 지표 정리 ──
    names = model.names                         # {class_id: 이름}
    overall = {
        # m.box.mp / mr = 클래스 평균 Precision / Recall, map50 / map = mAP50 / mAP50-95
        "precision": float(m.box.mp), "recall": float(m.box.mr),
        "f1": f1(float(m.box.mp), float(m.box.mr)),
        "map50": float(m.box.map50), "map50_95": float(m.box.map),
    }
    per_class = []
    # ap_class_index = 이 split 에 정답이 존재해 평가된 클래스 id 목록
    for i, cid in enumerate(m.box.ap_class_index):
        p, r, ap50, ap = (float(x) for x in m.box.class_result(i))   # (P, R, mAP50, mAP50-95)
        per_class.append({"id": int(cid), "name": names[int(cid)], "precision": p, "recall": r,
                          "f1": f1(p, r), "map50": ap50, "map50_95": ap})
    # 정답이 하나도 없어 평가되지 않은 클래스
    missing = [names[i] for i in range(len(names)) if i not in {c["id"] for c in per_class}]

    # ---------------- 합격 판정 ----------------
    # ── 4) 합격 기준과 비교 ── checks 원소: (지표 이름, 값, 기준, 통과 여부)
    checks = []
    for key in ("map50", "map50_95", "precision", "recall"):
        if key in th:                           # config 에 지정된 기준만 검사
            checks.append((key, overall[key], th[key], overall[key] >= th[key]))
    if "per_class_map50_min" in th:             # 클래스 하나라도 너무 낮으면 FAIL (평균에 가려지는 것 방지)
        for c in per_class:
            checks.append((f"map50[{c['name']}]", c["map50"], th["per_class_map50_min"],
                           c["map50"] >= th["per_class_map50_min"]))
    passed = all(c[3] for c in checks)          # 모든 기준을 통과해야 PASS

    # ---------------- 출력 ----------------
    # ── 5) 콘솔 출력 ──
    print(f"\n  {'클래스':<12}{'P':>8}{'R':>8}{'F1':>8}{'mAP50':>8}{'mAP50-95':>10}")
    for c in per_class:
        print(f"  {c['name']:<12}{c['precision']:>8.3f}{c['recall']:>8.3f}{c['f1']:>8.3f}"
              f"{c['map50']:>8.3f}{c['map50_95']:>10.3f}")
    o = overall
    print(f"  {'[전체]':<11}{o['precision']:>8.3f}{o['recall']:>8.3f}{o['f1']:>8.3f}"
          f"{o['map50']:>8.3f}{o['map50_95']:>10.3f}")
    if missing:
        print(f"  ⚠ 이 split 에 정답이 없는 클래스: {missing} (평가 불가)")
    sp = m.speed                                # 이미지 1장당 단계별 소요 시간(ms)
    print(f"\n  속도(이미지당): 전처리 {sp['preprocess']:.1f}ms | 추론 {sp['inference']:.1f}ms | "
          f"후처리 {sp['postprocess']:.1f}ms  (device={device})")
    print("\n  ── 합격 기준 ──")
    for k, v, t, ok in checks:
        print(f"  {'✅' if ok else '❌'} {k:<18} {v:.3f}  (기준 ≥ {t})")
    print(f"\n  최종 판정: {'PASS ✅' if passed else 'FAIL ❌'}")

    # ---------------- 리포트 ----------------
    # ── 6) 리포트 저장 (.json = 기계용, .md = 사람용) ──
    report_dir = path_of(cfg, "reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    result = {"evaluated_at": datetime.now().isoformat(timespec="seconds"), "weights": str(weights),
              "split": split, "imgsz": imgsz, "device": device, "overall": overall,
              "per_class": per_class, "missing_classes": missing, "speed_ms": sp,
              "checks": [{"metric": k, "value": v, "threshold": t, "pass": ok} for k, v, t, ok in checks],
              "passed": passed, "plots_dir": str(m.save_dir)}
    (report_dir / f"validate_{split}.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    md = [f"# 모델 검증 리포트 ({split})", "",
          f"- 모델: `{weights}`", f"- 일시: {result['evaluated_at']}", f"- imgsz: {imgsz} / device: {device}",
          f"- **판정: {'PASS ✅' if passed else 'FAIL ❌'}**", "",
          "| 클래스 | Precision | Recall | F1 | mAP50 | mAP50-95 |", "|---|---|---|---|---|---|"]
    md += [f"| {c['name']} | {c['precision']:.3f} | {c['recall']:.3f} | {c['f1']:.3f} | "
           f"{c['map50']:.3f} | {c['map50_95']:.3f} |" for c in per_class]
    md += [f"| **전체** | **{o['precision']:.3f}** | **{o['recall']:.3f}** | **{o['f1']:.3f}** | "
           f"**{o['map50']:.3f}** | **{o['map50_95']:.3f}** |", "", "## 합격 기준", "",
           "| 지표 | 값 | 기준 | 결과 |", "|---|---|---|---|"]
    md += [f"| {k} | {v:.3f} | ≥ {t} | {'✅' if ok else '❌'} |" for k, v, t, ok in checks]
    md += ["", f"그래프/혼동행렬: `{m.save_dir}`"]
    if not passed:                              # FAIL 이면 지표 패턴별 개선 방법 안내
        md += ["", "## 개선 가이드", "",
               "- Recall 낮음 → 놓치는 객체: 해당 상황(거리/조명/각도) 데이터 추가, 라벨 누락 점검",
               "- Precision 낮음 → 오탐: 헷갈리는 배경 이미지(빈 라벨) 추가, 클래스 정의 명확화",
               "- 특정 클래스만 낮음 → 그 클래스 데이터 보강, 혼동행렬에서 어떤 클래스와 헷갈리는지 확인",
               "- mAP50 은 높은데 mAP50-95 낮음 → 박스를 더 타이트하게 라벨링",
               "- 전체적으로 낮음 → epochs ↑, 모델 크기 ↑(yolo11s), imgsz ↑"]
    (report_dir / f"validate_{split}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"  리포트: {report_dir / f'validate_{split}.md'}")
    print(f"  그래프: {m.save_dir}")
    if split != "test":
        print("  다음 단계 → python scripts/07_test.py")
    sys.exit(0 if passed else 2)                # 종료 코드: PASS=0, FAIL=2 (run_pipeline 등 자동화에서 판정)


if __name__ == "__main__":
    main()
