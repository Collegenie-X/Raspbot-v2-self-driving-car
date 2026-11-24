"""
[5단계] YOLO11 모델 학습 (전이학습)

COCO 로 사전학습된 yolo11n.pt 에서 시작해 우리 데이터(data.yaml)로 미세조정합니다.

출력:
  runs/train/<project_name>/
    weights/best.pt   ← val mAP 가 가장 높았던 가중치
    weights/last.pt   ← 마지막 epoch (이어서 학습할 때 사용)
    results.csv / results.png / confusion_matrix.png / labels.jpg ...
  models/best.pt      ← 다음 단계들이 사용하는 최종 모델 (자동 복사)
  models/train_info.json

사용 예:
  python scripts/05_train.py                           # 값을 하나씩 물어봄 (엔터 = 기본값)
  python scripts/05_train.py -y                        # 묻지 않고 config 기본값으로 바로 실행
  python scripts/05_train.py --epochs 50 --batch 8 --model yolo11s.pt   # 준 값은 묻지 않음
  python scripts/05_train.py --resume                  # 중단된 학습 이어서

처리 흐름:
  1) 인자 파싱 → config 의 train 섹션을 복사한 뒤 CLI 인자로 덮어쓰기 (CLI > config)
     → CLI 로 주지 않은 값은 터미널에서 물어봄 (엔터 = 기본값, -y 면 생략)
  2) 디바이스 결정(auto → CUDA / CPU), 결과 폴더(runs/train/<name>) 결정
  3) data.yaml 존재 확인 (없으면 4단계 먼저)
  4) 학습 실행
       --resume : last.pt 를 열어 optimizer/epoch 상태까지 그대로 이어서 학습
       기본     : 사전학습 가중치로 새 학습 (train.extra 의 증강 인자도 그대로 전달)
  5) best.pt → models/best.pt 로 복사 (6~9단계가 이 파일을 기본값으로 사용)
  6) results.csv 요약 + 학습 정보를 models/train_info.json 으로 저장
  7) 콘솔에 결과 요약 출력

자세한 구조 분석: scripts/05_train.md
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

from common import (add_config_arg, add_yes_arg, ask, banner, data_yaml_path, interactive,
                    load_config, path_of, pick_device)


def summarize_results_csv(csv_path: Path) -> dict:
    """results.csv 에서 best(mAP50-95 최대) epoch 와 마지막 epoch 지표 추출.

    results.csv 는 Ultralytics 가 epoch 마다 한 줄씩 기록하는 학습 로그입니다.
    반환 예: {"best": {...}, "last": {...}, "epochs_run": 87}   (파일이 없거나 비면 {})
    """
    if not csv_path.exists():
        return {}
    with open(csv_path, encoding="utf-8") as f:
        # Ultralytics 버전에 따라 헤더/값에 공백 패딩이 있을 수 있어 strip() 으로 정리
        rows = [{k.strip(): v.strip() for k, v in r.items()} for r in csv.DictReader(f)]
    if not rows:
        return {}
    key = "metrics/mAP50-95(B)"          # (B) = Box(탐지) 지표. Ultralytics 가 best.pt 를 고르는 주 기준과 유사
    best = max(rows, key=lambda r: float(r.get(key, 0) or 0))   # 빈 문자열도 0 으로 처리
    # 한 행(row)에서 관심 지표만 골라 숫자로 변환하는 작은 헬퍼
    pick = lambda r: {  # noqa: E731
        "epoch": int(float(r["epoch"])),
        "precision": float(r.get("metrics/precision(B)", 0)),
        "recall": float(r.get("metrics/recall(B)", 0)),
        "mAP50": float(r.get("metrics/mAP50(B)", 0)),
        "mAP50-95": float(r.get(key, 0)),
    }
    return {"best": pick(best), "last": pick(rows[-1]), "epochs_run": len(rows)}


def main():
    """CLI 진입점: 설정 병합 → 학습(또는 이어서 학습) → best.pt 복사 → 학습 정보 기록."""
    # ── 1) 인자 파싱 (지정하지 않은 값은 None → config 값 사용) ──
    ap = add_config_arg(argparse.ArgumentParser(description=__doc__,
                                                formatter_class=argparse.RawDescriptionHelpFormatter))
    ap.add_argument("--model", help="시작 가중치 (예: yolo11n.pt, yolo11s.pt, models/best.pt)")
    ap.add_argument("--epochs", type=int)
    ap.add_argument("--imgsz", type=int)
    ap.add_argument("--batch", type=int)
    ap.add_argument("--device", help="auto / cpu / mps / 0")
    ap.add_argument("--name", help="실행 이름 (기본: project_name)")
    ap.add_argument("--resume", action="store_true", help="last.pt 에서 이어서 학습")
    add_yes_arg(ap)
    args = ap.parse_args()

    cfg = load_config(args.config)
    tc = dict(cfg["train"])                     # 원본 cfg 를 건드리지 않도록 복사본 사용
    for k in ("model", "epochs", "imgsz", "batch", "device"):
        if getattr(args, k) is not None:        # CLI 로 준 값만 덮어쓰기 (우선순위: CLI > config)
            tc[k] = getattr(args, k)
    name = args.name or cfg.get("project_name", "yolo11")

    # ── 1-1) 대화형 입력: CLI 로 주지 않은 값만 물어봄 (엔터 = 기본값) ──
    #   -y 를 주었거나, 터미널이 아닌 환경(파이프/백그라운드 실행)에서는 묻지 않음
    if interactive(args):
        print("\n  학습 설정 (그냥 엔터 → [ ] 안의 기본값 사용)")
        if args.name is None:
            name = ask("실행 이름(name)", name)
        if not args.resume:                     # resume 은 last.pt 에 저장된 설정을 그대로 씀
            prompts = [("model", "시작 가중치(model)", str), ("epochs", "epochs", int),
                       ("imgsz", "imgsz", int), ("batch", "batch (-1 = 자동)", int),
                       ("device", "device (auto/cpu/mps/0)", str)]
            for key, label, cast in prompts:
                if getattr(args, key) is None:
                    tc[key] = ask(label, tc.get(key), cast)

    # ultralytics 는 import 가 무거워서(torch 로드) --help / 입력 단계가 빠르도록 이 시점에 import
    from ultralytics import YOLO

    # ── 2) 디바이스 / 출력 경로 ──
    device = pick_device(tc.get("device", "auto"))       # "auto" → "0"(CUDA) 또는 "cpu"
    project = path_of(cfg, "runs") / "train"              # 최종 결과: runs/train/<name>/
    data_yaml = data_yaml_path(cfg)                       # datasets/raspbot/data.yaml

    banner("5단계", "YOLO11 학습")
    # ── 3) 사전 점검 ──
    if not data_yaml.exists():
        sys.exit(f"[ERROR] {data_yaml} 가 없습니다. 4단계 04_split_dataset.py 먼저 실행하세요.")

    # ── 4) 학습 ──
    t0 = time.time()
    if args.resume:
        # 이어서 학습: last.pt 안에 epoch/optimizer/학습 인자가 저장돼 있어 resume=True 만 주면 됨
        last = project / name / "weights" / "last.pt"
        if not last.exists():
            sys.exit(f"[ERROR] 이어서 학습할 {last} 가 없습니다.")
        print(f"  이어서 학습: {last}")
        model = YOLO(str(last))
        model.train(resume=True)
    else:
        print(f"  모델: {tc['model']} | epochs {tc['epochs']} | imgsz {tc['imgsz']} | "
              f"batch {tc['batch']} | device {device}")
        print(f"  데이터: {data_yaml}")
        # 'yolo11n.pt' 처럼 이름만 주면 Ultralytics 가 자동 다운로드 (COCO 사전학습 가중치)
        model = YOLO(tc["model"])
        model.train(
            data=str(data_yaml),                 # 데이터셋 정의 (경로, 클래스 수/이름)
            epochs=int(tc["epochs"]),            # 전체 데이터를 몇 바퀴 학습할지
            imgsz=int(tc["imgsz"]),              # 학습 입력 크기 (정사각형으로 letterbox)
            batch=int(tc["batch"]),              # 한 번에 처리할 이미지 수 (-1 = GPU 메모리 기준 자동)
            device=device,
            workers=int(tc.get("workers", 4)),   # 데이터 로딩 프로세스 수
            patience=int(tc.get("patience", 30)),  # N epoch 동안 val 성능 개선 없으면 조기 종료
            seed=int(tc.get("seed", 42)),        # 재현성
            project=str(project),
            name=name,
            exist_ok=True,                       # 같은 이름 폴더가 있어도 새 번호(name2..)를 만들지 않고 덮어씀
            plots=True,                          # results.png, confusion_matrix.png 등 그래프 저장
            **(tc.get("extra") or {}),           # 증강 등 추가 인자 (hsv_*, degrees, fliplr, mosaic ...)
        )
    minutes = (time.time() - t0) / 60

    # ── 5) best.pt → models/best.pt 복사 ──
    save_dir = Path(model.trainer.save_dir)      # 실제 결과 폴더 (resume 시에도 정확한 경로)
    best = save_dir / "weights" / "best.pt"
    if not best.exists():
        sys.exit(f"[ERROR] best.pt 가 생성되지 않았습니다: {best}")

    models_dir = path_of(cfg, "models")
    models_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best, models_dir / "best.pt")   # 6~9단계는 기본으로 models/best.pt 를 사용

    # ── 6) 학습 정보 기록 (나중에 '어떤 조건으로 만든 모델인지' 추적용) ──
    summary = summarize_results_csv(save_dir / "results.csv")
    info = {
        "trained_at": datetime.now().isoformat(timespec="seconds"),
        "duration_min": round(minutes, 1),
        "run_dir": str(save_dir),
        "base_model": tc["model"],
        "device": device,
        "classes": cfg["classes"],
        "params": {k: tc[k] for k in ("epochs", "imgsz", "batch") if k in tc},
        "results": summary,
    }
    (models_dir / "train_info.json").write_text(json.dumps(info, indent=2, ensure_ascii=False),
                                                encoding="utf-8")

    # ── 7) 결과 요약 출력 ──
    print("\n  ── 학습 결과 ──")
    print(f"  소요 시간: {minutes:.1f} 분 | 결과 폴더: {save_dir}")
    if summary:
        b = summary["best"]
        print(f"  best epoch {b['epoch']}: P {b['precision']:.3f} | R {b['recall']:.3f} | "
              f"mAP50 {b['mAP50']:.3f} | mAP50-95 {b['mAP50-95']:.3f}")
    print(f"  최종 모델: {models_dir / 'best.pt'}")
    print("  확인할 그래프: results.png (loss 감소 / mAP 증가), confusion_matrix.png, val_batch*_pred.jpg")
    print("  다음 단계 → python scripts/06_validate.py")


if __name__ == "__main__":
    main()
