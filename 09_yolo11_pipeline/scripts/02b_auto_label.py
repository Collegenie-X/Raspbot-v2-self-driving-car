"""
[2단계-보조] 자동 사전 라벨링 (Pre-labeling)

이미 학습된 모델(예: 이전 버전 best.pt)로 라벨이 없는 이미지에 박스를 미리 만들어 둡니다.
사람은 02_label_tool.py 로 '수정/검토'만 하면 되므로 라벨링 시간이 크게 줄어듭니다.

  ⚠ 자동 라벨은 반드시 사람이 검토하세요. 틀린 라벨을 그대로 학습하면 모델이 그 오류를 배웁니다.

모델의 클래스 이름과 config 의 classes 이름이 같은 것만 저장합니다 (이름 기준 매핑).

입력 : data/labeled/images/*.jpg, --weights 로 지정한 기존 모델
출력 : data/labeled/labels/*.txt (라벨 없는 이미지만, --overwrite 시 전부), classes.txt

처리 흐름 (main)
  1) 옵션 · 설정 로드
  2) 모델 로드 후 '모델 클래스 ID → config 클래스 ID' 매핑 만들기 (이름 기준)
  3) 대상 이미지 선택 (라벨이 없는 이미지, 또는 --overwrite 면 전체)
  4) 16장씩 묶어 추론 → 매핑된 클래스만 YOLO txt 로 저장
  5) classes.txt 저장 및 결과 출력

사용 예:
  python scripts/02b_auto_label.py --weights ../source/models/yolo/best.pt
  python scripts/02b_auto_label.py --weights models/best.pt --conf 0.4 --overwrite
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common import (add_config_arg, banner, label_path_for, labeled_dirs, list_images,
                    load_config, pick_device, write_yolo_labels)


def main():
    """기존 모델로 라벨 없는 이미지에 사전 라벨(YOLO txt)을 생성한다."""
    # ── 1) 옵션 · 설정 로드 ──
    ap = add_config_arg(argparse.ArgumentParser(description=__doc__,
                                                formatter_class=argparse.RawDescriptionHelpFormatter))
    ap.add_argument("--weights", required=True, help="사전 라벨링에 쓸 모델 (.pt)")
    ap.add_argument("--conf", type=float, default=0.4)       # 이 신뢰도 이상인 박스만 저장
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--overwrite", action="store_true", help="이미 있는 라벨도 덮어쓰기")
    args = ap.parse_args()

    from ultralytics import YOLO      # 무거운 라이브러리는 옵션 파싱 후에 import (--help 가 빨라짐)

    cfg = load_config(args.config)
    names = [n.lower() for n in cfg["classes"]]               # 대소문자 무시하고 비교하기 위해 소문자화
    images_dir, labels_dir = labeled_dirs(cfg)
    banner("2단계-보조", "자동 사전 라벨링")

    # ── 2) 모델 로드 + 클래스 매핑 ──
    model = YOLO(args.weights)
    model_names = {int(k): str(v).lower() for k, v in model.names.items()}   # {모델ID: 이름}
    # 모델 클래스 순서와 config 순서가 달라도 '이름'으로 맞춘다. config 에 없는 클래스는 제외.
    #   예) 모델 {0:'person', 1:'car'} / config ['car', ...] → id_map = {1: 0}
    id_map = {mid: names.index(n) for mid, n in model_names.items() if n in names}
    print(f"  모델 클래스: {model_names}")
    print(f"  매핑(모델→config): {id_map}")
    if not id_map:
        sys.exit("[ERROR] 모델 클래스와 config classes 이름이 하나도 일치하지 않습니다.")

    # ── 3) 대상 이미지 선택 ──
    targets = [p for p in list_images(images_dir)
               if args.overwrite or not label_path_for(p, images_dir, labels_dir).exists()]
    print(f"  대상 이미지: {len(targets)} 장")
    device = pick_device(cfg["train"].get("device", "auto"))

    # ── 4) 16장 단위 배치 추론 → 라벨 저장 ──
    n_boxes = 0
    for i in range(0, len(targets), 16):
        batch = targets[i:i + 16]                  # 한 번에 16장씩 (메모리 절약 + 속도)
        for img_path, r in zip(batch, model.predict([str(p) for p in batch], conf=args.conf,
                                                   imgsz=args.imgsz, device=device, verbose=False)):
            boxes = []
            # xywhn = (x_center, y_center, w, h) 정규화 좌표 → YOLO 라벨 형식 그대로 사용 가능
            for c, xywhn in zip(r.boxes.cls.tolist(), r.boxes.xywhn.tolist()):
                if int(c) in id_map:               # config 에 없는 클래스의 박스는 버림
                    boxes.append((id_map[int(c)], *xywhn))
            # 박스가 0개여도 빈 txt 가 생성됨 → 02_label_tool 에서 꼭 검토할 것
            write_yolo_labels(label_path_for(Path(img_path), images_dir, labels_dir), boxes)
            n_boxes += len(boxes)
        print(f"  {min(i + 16, len(targets))}/{len(targets)} ...", end="\r")   # \r: 같은 줄에 진행률 갱신

    # ── 5) classes.txt 저장 및 결과 출력 ──
    #   classes.txt: LabelImg 등 외부 도구가 클래스 이름을 읽을 때 사용
    (labels_dir.parent / "classes.txt").write_text("\n".join(cfg["classes"]) + "\n", encoding="utf-8")
    print(f"\n  생성된 박스: {n_boxes} 개")
    print("  다음 → python scripts/02_label_tool.py 로 반드시 검토/수정하세요.")


if __name__ == "__main__":
    main()
