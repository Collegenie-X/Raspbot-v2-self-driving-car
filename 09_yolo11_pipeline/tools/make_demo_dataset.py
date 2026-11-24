"""
가상(합성) 데이터셋 생성기 — 실제 데이터 없이 파이프라인 전체를 체험/점검할 때 사용

Raspbot 클래스(car, green, oo, red, xx)를 단순 도형으로 그려 라벨과 함께 저장합니다.
  car   : 차체 + 바퀴 2개      green/red : 신호등 원
  oo    : 파란 판 위 흰 O       xx        : 노란 판 위 검은 X
※ 실제 성능과는 무관합니다. '코드가 끝까지 도는지' 확인하는 용도입니다.

사용 예:
  python tools/make_demo_dataset.py --n 240
"""
from __future__ import annotations

import argparse
import random
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from common import (labeled_dirs, load_config, write_yolo_labels, xyxy_to_yolo)  # noqa: E402


def background(rng, w, h):
    base = np.array([rng.randint(60, 200) for _ in range(3)], np.uint8)
    img = np.full((h, w, 3), base, np.uint8)
    noise = np.random.default_rng(rng.randint(0, 10**6)).normal(0, 12, (h, w, 3))
    img = np.clip(img + noise, 0, 255).astype(np.uint8)
    for _ in range(rng.randint(2, 6)):   # 방해 도형
        c = tuple(rng.randint(0, 255) for _ in range(3))
        x, y = rng.randint(0, w), rng.randint(0, h)
        cv2.line(img, (x, y), (x + rng.randint(-200, 200), y + rng.randint(-200, 200)), c, rng.randint(1, 6))
    return img


def draw_obj(img, cls, x, y, s):
    """(x,y) 좌상단, 크기 s 인 객체를 그리고 박스 (x1,y1,x2,y2) 반환."""
    if cls == 0:   # car
        w, h = int(s * 1.6), s
        cv2.rectangle(img, (x, y), (x + w, y + int(h * 0.75)), (40, 40, 200), -1)
        cv2.rectangle(img, (x + w // 5, y - h // 4), (x + w * 4 // 5, y), (60, 60, 220), -1)
        for cx in (x + w // 4, x + w * 3 // 4):
            cv2.circle(img, (cx, y + int(h * 0.75)), h // 4, (20, 20, 20), -1)
        return x, y - h // 4, x + w, y + h
    if cls in (1, 3):   # green / red 신호등
        cv2.rectangle(img, (x, y), (x + s, y + s), (30, 30, 30), -1)
        cv2.circle(img, (x + s // 2, y + s // 2), int(s * 0.4), (0, 220, 0) if cls == 1 else (0, 0, 230), -1)
        return x, y, x + s, y + s
    if cls == 2:   # oo
        cv2.rectangle(img, (x, y), (x + s, y + s), (200, 100, 20), -1)
        cv2.circle(img, (x + s // 2, y + s // 2), int(s * 0.33), (255, 255, 255), max(2, s // 8))
        return x, y, x + s, y + s
    # xx
    cv2.rectangle(img, (x, y), (x + s, y + s), (0, 210, 240), -1)
    m, t = s // 5, max(2, s // 8)
    cv2.line(img, (x + m, y + m), (x + s - m, y + s - m), (0, 0, 0), t)
    cv2.line(img, (x + s - m, y + m), (x + m, y + s - m), (0, 0, 0), t)
    return x, y, x + s, y + s


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default="config.demo.yaml")
    ap.add_argument("--n", type=int, default=240)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    cfg = load_config(args.config)
    images_dir, labels_dir = labeled_dirs(cfg)
    for d in (images_dir, labels_dir):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
    rng = random.Random(args.seed)
    W, H = 640, 480

    for i in range(args.n):
        img = background(rng, W, H)
        boxes, placed = [], []
        for _ in range(0 if i % 12 == 0 else rng.randint(1, 3)):   # 1/12 은 배경 이미지
            cls = rng.randrange(len(cfg["classes"]))
            s = rng.randint(36, 110)
            for _try in range(20):
                x, y = rng.randint(5, W - int(s * 1.7) - 5), rng.randint(s // 3 + 5, H - s - 5)
                if all(x > b[2] + 5 or x + s * 1.7 < b[0] - 5 or y + s < b[1] - 5 or y - s // 3 > b[3] + 5
                       for b in placed):
                    box = draw_obj(img, cls, x, y, s)
                    placed.append(box)
                    boxes.append(xyxy_to_yolo(cls, *box, W, H))
                    break
        if rng.random() < 0.3:
            img = cv2.GaussianBlur(img, (5, 5), 0)
        cv2.imwrite(str(images_dir / f"demo_{i:04d}.jpg"), img)
        write_yolo_labels(labels_dir / f"demo_{i:04d}.txt", boxes)

    (labels_dir.parent / "classes.txt").write_text("\n".join(cfg["classes"]) + "\n", encoding="utf-8")
    print(f"[demo] 가상 이미지 {args.n} 장 생성 → {images_dir.parent}")


if __name__ == "__main__":
    main()
