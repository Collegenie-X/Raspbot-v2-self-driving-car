"""
Haar Cascade vs YOLO11 — 같은 데이터로 직접 비교하는 실습 실험

04_cascade/park_data_example 의 실제 Raspbot 카메라 데이터를 그대로 사용합니다.
  p/  : O 표지판 사진 39장 (Haar 학습에 쓴 positive)
  n/  : X 표지판이 찍힌 카메라 프레임 93장 (Haar 학습에 쓴 negative)
  classifier/cascade.xml : 이 데이터로 학습된 Haar Cascade (O 표지판 검출기, 32x24 창, 4단계)

실험 순서
  1) 흰 카드 영역을 자동으로 찾아 YOLO 라벨(oo / xx) 생성
  2) 앞 70% = train, 뒤 30% = test (연속 프레임 누수를 막기 위해 순서대로 분할)
  3) YOLO11n 을 train 으로 학습 (CPU 로 1~2분)
  4) test 이미지 + 일부러 망가뜨린 이미지(어둡게/회전/흐림/작게)로 두 방식 비교
     - Haar: O 검출기 1개 → "O 를 찾았나"(재현율), "X 를 O 로 착각했나"(오탐)
     - YOLO: oo/xx 를 한 번에 → 클래스까지 맞혔나
  ⚠ Haar 는 test 의 O 사진까지 포함해 학습됐습니다 (Haar 에게 유리한 조건).

출력: demo/haar_vs_yolo/ (results.json, samples.jpg, 학습 결과)
※ OpenCV 5.0 기본 패키지에는 cv2.CascadeClassifier 가 없어 opencv-python<5 가 필요합니다.

사용 예:
  python tools/haar_vs_yolo_experiment.py
  python tools/haar_vs_yolo_experiment.py --epochs 40 --skip-train
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
DATA = REPO / "04_cascade/park_data_example"
CASCADE = DATA / "classifier/cascade.xml"
OUT = ROOT / "demo/haar_vs_yolo"
NAMES = ["oo", "xx"]


# ------------------------------------------------------------------ 1) 자동 라벨
def card_box(img):
    """검은 배경 위 흰 카드의 바운딩 박스 (x1,y1,x2,y2). 상단 벽 영역은 제외."""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    h, w = g.shape
    _, th = cv2.threshold(cv2.GaussianBlur(g, (5, 5), 0), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    k = max(5, int(min(h, w) * 0.08)) | 1     # 카드 위의 검은 O/X 선을 메워 카드 한 덩어리로
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (k, k)))
    cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best = None
    for c in cnts:
        x, y, bw, bh = cv2.boundingRect(c)
        if y <= 2 and bw > 0.3 * w and bh < 0.25 * h:   # 화면 위쪽 벽(가로로 긴 밝은 띠)
            continue
        area = cv2.contourArea(c)
        if area > 0.01 * w * h and (best is None or area > best[0]):
            best = (area, (x, y, x + bw, y + bh))
    return best[1] if best else None


def build_dataset(train_ratio=0.7):
    ds = OUT / "dataset"
    if ds.exists():
        shutil.rmtree(ds)
    items = {"train": [], "test": []}
    for cls, folder in ((0, "p"), (1, "n")):
        files = sorted((DATA / folder).glob("*.jpg"), key=lambda p: p.stem)
        n_train = int(len(files) * train_ratio)
        for i, f in enumerate(files):
            split = "train" if i < n_train else "test"
            img = cv2.imread(str(f))
            box = card_box(img)
            h, w = img.shape[:2]
            (ds / "images" / split).mkdir(parents=True, exist_ok=True)
            (ds / "labels" / split).mkdir(parents=True, exist_ok=True)
            name = f"{folder}_{f.stem}"
            cv2.imwrite(str(ds / "images" / split / f"{name}.jpg"), img)
            if box is None:      # 카드가 없는 빈 화면 = 배경 이미지 (빈 라벨)
                (ds / "labels" / split / f"{name}.txt").write_text("")
                items[split].append((name, -1, None))
                continue
            x1, y1, x2, y2 = box
            (ds / "labels" / split / f"{name}.txt").write_text(
                f"{cls} {(x1 + x2) / 2 / w:.6f} {(y1 + y2) / 2 / h:.6f} {(x2 - x1) / w:.6f} {(y2 - y1) / h:.6f}\n")
            items[split].append((name, cls, box))
    (ds / "data.yaml").write_text(
        f"path: {ds}\ntrain: images/train\nval: images/test\nnames: {{0: oo, 1: xx}}\n", encoding="utf-8")
    return ds, items


# ------------------------------------------------------------------ 2) 변형 (강건성 테스트)
def perturb(img, kind):
    if kind == "원본":
        return img
    if kind == "어둡게":
        return np.clip(img.astype(np.float32) * 0.35, 0, 255).astype(np.uint8)
    if kind == "회전 25°":
        h, w = img.shape[:2]
        M = cv2.getRotationMatrix2D((w / 2, h / 2), 25, 1.0)
        return cv2.warpAffine(img, M, (w, h), borderValue=(0, 0, 0))
    if kind == "흐림":
        return cv2.GaussianBlur(img, (11, 11), 0)
    if kind == "작게":
        h, w = img.shape[:2]
        small = cv2.resize(img, (int(w * 0.45), int(h * 0.45)))
        canvas = np.zeros_like(img)
        y0, x0 = (h - small.shape[0]) // 2, (w - small.shape[1]) // 2
        canvas[y0:y0 + small.shape[0], x0:x0 + small.shape[1]] = small
        return canvas
    raise ValueError(kind)


KINDS = ["원본", "어둡게", "회전 25°", "흐림", "작게"]


def haar_detect(cascade, img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cascade.detectMultiScale(g, scaleFactor=1.05, minNeighbors=3, minSize=(16, 12))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--skip-train", action="store_true")
    args = ap.parse_args()

    if not hasattr(cv2, "CascadeClassifier"):
        sys.exit(f"[ERROR] OpenCV {cv2.__version__} 에는 CascadeClassifier 가 없습니다. pip install 'opencv-python<5'")
    from ultralytics import YOLO

    OUT.mkdir(parents=True, exist_ok=True)
    ds, items = build_dataset()
    cnt = lambda sp, c: sum(1 for _, k, _ in items[sp] if k == c)  # noqa: E731
    print(f"[1] 자동 라벨: train O{cnt('train', 0)}/X{cnt('train', 1)}/배경{cnt('train', -1)}  "
          f"test O{cnt('test', 0)}/X{cnt('test', 1)}/배경{cnt('test', -1)}")

    weights = OUT / "yolo_ox.pt"
    if not (args.skip_train and weights.exists()):
        t0 = time.time()
        m = YOLO(str(ROOT / "yolo11n.pt") if (ROOT / "yolo11n.pt").exists() else "yolo11n.pt")
        m.train(data=str(ds / "data.yaml"), epochs=args.epochs, imgsz=320, batch=16, device="cpu",
                project=str(OUT / "runs"), name="ox", exist_ok=True, plots=True, verbose=False,
                fliplr=0.0, workers=2, seed=0)
        shutil.copy2(Path(m.trainer.save_dir) / "weights/best.pt", weights)
        print(f"[2] YOLO 학습 완료 {time.time() - t0:.0f}s")
    yolo = YOLO(str(weights))
    cascade = cv2.CascadeClassifier(str(CASCADE))

    results = {k: {"haar_o_hit": 0, "haar_x_false": 0, "yolo_o_hit": 0, "yolo_x_hit": 0, "yolo_wrong": 0,
                   "n_o": 0, "n_x": 0, "n_bg": 0, "haar_bg_false": 0,
                   "yolo_bg_false": 0, "haar_ms": [], "yolo_ms": []} for k in KINDS}
    samples = []
    o_test = [n for n, c, _ in items["test"] if c == 0]
    x_test = [n for n, c, _ in items["test"] if c == 1]
    sample_names = {o_test[len(o_test) // 2], x_test[len(x_test) // 2]}
    for name, cls, _ in items["test"]:
        base = cv2.imread(str(ds / "images/test" / f"{name}.jpg"))
        for k in KINDS:
            img = perturb(base, k)
            r = results[k]
            t = time.perf_counter()
            hd = haar_detect(cascade, img)
            r["haar_ms"].append((time.perf_counter() - t) * 1000)
            t = time.perf_counter()
            yp = yolo.predict(img, imgsz=320, conf=0.5, verbose=False, device="cpu")[0]
            r["yolo_ms"].append((time.perf_counter() - t) * 1000)
            ycls = [int(c) for c in yp.boxes.cls.tolist()]
            if cls == 0:
                r["n_o"] += 1
                r["haar_o_hit"] += int(len(hd) > 0)
                r["yolo_o_hit"] += int(0 in ycls)
                r["yolo_wrong"] += int(1 in ycls)
            elif cls == -1:
                r["n_bg"] += 1
                r["haar_bg_false"] += int(len(hd) > 0)
                r["yolo_bg_false"] += int(len(ycls) > 0)
            else:
                r["n_x"] += 1
                r["haar_x_false"] += int(len(hd) > 0)
                r["yolo_x_hit"] += int(1 in ycls)
                r["yolo_wrong"] += int(0 in ycls)
            if name in sample_names:
                samples.append((name, k, img, hd, yp))

    summary = {}
    print(f"\n{'조건':<8}{'Haar O재현율':>12}{'Haar X오탐':>11}{'YOLO O재현율':>12}{'YOLO X재현율':>12}{'YOLO 오분류':>10}"
          f"{'Haar배경오탐':>10}{'YOLO배경오탐':>10}{'Haar ms':>9}{'YOLO ms':>9}")
    for k in KINDS:
        r = results[k]
        s = {"haar_o_recall": r["haar_o_hit"] / r["n_o"], "haar_x_false_rate": r["haar_x_false"] / r["n_x"],
             "yolo_o_recall": r["yolo_o_hit"] / r["n_o"], "yolo_x_recall": r["yolo_x_hit"] / r["n_x"],
             "yolo_wrong": r["yolo_wrong"], "n_o": r["n_o"], "n_x": r["n_x"], "n_bg": r["n_bg"],
             "haar_bg_false": r["haar_bg_false"], "yolo_bg_false": r["yolo_bg_false"],
             "haar_ms": float(np.median(r["haar_ms"])), "yolo_ms": float(np.median(r["yolo_ms"]))}
        summary[k] = s
        print(f"{k:<8}{s['haar_o_recall']:>12.0%}{s['haar_x_false_rate']:>11.0%}{s['yolo_o_recall']:>12.0%}"
              f"{s['yolo_x_recall']:>12.0%}{s['yolo_wrong']:>10}{s['haar_bg_false']:>7}/{s['n_bg']}"
              f"{s['yolo_bg_false']:>7}/{s['n_bg']}{s['haar_ms']:>9.1f}{s['yolo_ms']:>9.1f}")

    # 샘플 이미지 (위: Haar, 아래: YOLO)
    tiles = []
    for name, k, img, hd, yp in samples:
        a = img.copy()
        for (x, y, w, h) in hd:
            cv2.rectangle(a, (x, y), (x + w, y + h), (0, 0, 255), 2)
        b = yp.plot()
        tiles.append((name, k, a, b))
    out_imgs = {}
    for name, k, a, b in tiles:
        out_imgs.setdefault(name, []).append((k, a, b))
    for name, lst in out_imgs.items():
        rows = []
        for k, a, b in lst:
            a = cv2.resize(a, (320, 240))
            b = cv2.resize(b, (320, 240))
            rows.append(np.vstack([a, b]))
        cv2.imwrite(str(OUT / f"samples_{name}.jpg"), np.hstack(rows))

    (OUT / "results.json").write_text(json.dumps({
        "cascade": str(CASCADE.relative_to(REPO)), "window": list(cascade.getOriginalWindowSize()),
        "opencv": cv2.__version__, "train": len(items["train"]), "test": len(items["test"]),
        "epochs": args.epochs, "summary": summary}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n결과: {OUT / 'results.json'}")


if __name__ == "__main__":
    main()
