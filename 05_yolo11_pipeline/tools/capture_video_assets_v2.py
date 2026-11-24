"""
튜토리얼 영상 v2 용 '실제 실행 결과' 수집 스크립트

영상에 나오는 그림·숫자를 모두 실제 코드를 돌려서 얻습니다. (가짜 그림 없음)
  1) Haar: 학습된 cascade.xml 의 Haar 특징(사각형) 추출, 슬라이딩 윈도우 개수 계산
  2) YOLO: 원시 출력 텐서 크기, NMS 전/후 후보 박스, 특징맵(feature map)
  3) 라벨링 도구(02_label_tool.py) 실제 화면 — 마우스/키 입력을 흉내 내어 캡처
  4) 실제 카메라 연속 프레임 추론 + 주행 코드의 StableTrigger(연속 N프레임 확인) 동작

전제: python run_pipeline.py --demo, python tools/haar_vs_yolo_experiment.py 를 먼저 실행
출력: demo/video_v2_assets/
"""
from __future__ import annotations

import json
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
OUT = ROOT / "demo/video_v2_assets"
HV = ROOT / "demo/haar_vs_yolo"
DATA = REPO / "04_cascade/park_data_example"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(REPO / "source"))


def haar_assets(meta):
    xml = DATA / "classifier/cascade.xml"
    root = ET.parse(xml).getroot()[0]
    W, H = int(root.findtext("width")), int(root.findtext("height"))
    feats = [[list(map(float, r.text.split())) for r in f.find("rects")] for f in root.find("features")]
    stages = []
    for st in root.find("stages"):
        weak = []
        for wc in st.find("weakClassifiers"):
            nodes = wc.findtext("internalNodes").split()
            weak.append({"feature": int(nodes[2]), "threshold": float(nodes[3]),
                         "leaf": list(map(float, wc.findtext("leafValues").split()))})
        stages.append({"threshold": float(st.findtext("stageThreshold")), "weak": weak})
    used = [{"stage": i, "rects": feats[w["feature"]]} for i, s in enumerate(stages) for w in s["weak"]]
    # 320x240 이미지에서 검사하는 창 개수 (OpenCV detectMultiScale 방식, scaleFactor=1.1)
    n_win, scales, f = 0, 0, 1.0
    while W * f <= 320 and H * f <= 240:
        sw, sh = int(round(320 / f)), int(round(240 / f))
        step = 1 if f > 2 else 2
        n_win += max(0, (sw - W) // step + 1) * max(0, (sh - H) // step + 1)
        scales += 1
        f *= 1.1
    meta["haar"] = {"window": [W, H], "n_stages": len(stages), "stages": stages, "used_features": used,
                    "n_windows_320x240": n_win, "n_scales": scales,
                    "n_features_total": len(feats)}
    print(f"[haar] window {W}x{H}, stages {len(stages)}, features {len(feats)}, windows {n_win:,} / {scales} scales")


def yolo_assets(meta):
    import torch
    from ultralytics import YOLO
    m = YOLO(str(HV / "yolo_ox.pt"))
    img = cv2.imread(str(HV / "dataset/images/test") + "/" + sorted(
        p.name for p in (HV / "dataset/images/test").glob("n_*.jpg"))[10])
    cv2.imwrite(str(OUT / "yolo_input.jpg"), img)
    # 원시 출력 텐서
    x = torch.from_numpy(cv2.resize(img, (320, 320))[:, :, ::-1].copy()).permute(2, 0, 1)[None].float() / 255
    net = m.model.eval()
    with torch.no_grad():
        out = net(x)
    raw = out[0] if isinstance(out, (list, tuple)) else out
    meta["yolo_raw_shape"] = list(raw.shape)
    # 특징맵 (backbone 층별)
    feats = {}
    hooks = [net.model[i].register_forward_hook(lambda mod, inp, o, i=i: feats.__setitem__(i, o.detach()))
             for i in (0, 2, 4, 6)]
    with torch.no_grad():
        net(x)
    for h in hooks:
        h.remove()
    fm_info = []
    for i, t in feats.items():
        t = t[0]
        idx = torch.argsort(t.abs().mean((1, 2)), descending=True)[:4]
        tiles = []
        for c in idx:
            a = t[c].numpy()
            a = (255 * (a - a.min()) / (a.max() - a.min() + 1e-6)).astype(np.uint8)
            tiles.append(cv2.applyColorMap(cv2.resize(a, (160, 160), interpolation=cv2.INTER_NEAREST),
                                           cv2.COLORMAP_VIRIDIS))
        cv2.imwrite(str(OUT / f"feat_L{i}.png"), np.hstack(tiles))
        fm_info.append({"layer": i, "shape": list(t.shape)})
    meta["feature_maps"] = fm_info
    # NMS 전/후
    raw_r = m.predict(img, imgsz=320, conf=0.01, iou=0.99, max_det=1000, verbose=False)[0]
    fin_r = m.predict(img, imgsz=320, conf=0.5, iou=0.7, verbose=False)[0]
    meta["nms"] = {"raw_candidates": int(raw_r.boxes.shape[0]), "final": int(fin_r.boxes.shape[0]),
                   "raw_conf": [round(float(c), 3) for c in raw_r.boxes.conf[:30]],
                   "final_det": [(m.names[int(c)], round(float(s), 2)) for c, s in
                                 zip(fin_r.boxes.cls, fin_r.boxes.conf)]}
    a = img.copy()
    for (x1, y1, x2, y2), c in zip(raw_r.boxes.xyxy.tolist(), raw_r.boxes.conf.tolist()):
        col = (0, int(255 * c), int(255 * (1 - c)))
        cv2.rectangle(a, (int(x1), int(y1)), (int(x2), int(y2)), col, 1)
    cv2.imwrite(str(OUT / "nms_before.jpg"), a)
    cv2.imwrite(str(OUT / "nms_after.jpg"), fin_r.plot())
    m.info(verbose=False)
    n_params = sum(p.numel() for p in net.parameters())
    meta["yolo_params"] = n_params
    print(f"[yolo] raw {meta['yolo_raw_shape']}, candidates {meta['nms']['raw_candidates']} → {meta['nms']['final']}"
          f", params {n_params:,}")


def label_tool_frames(meta):
    import importlib.util
    spec = importlib.util.spec_from_file_location("lt", ROOT / "scripts/02_label_tool.py")
    lt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lt)
    frames = []
    lt.cv2.imshow = lambda win, im: frames.append(im.copy())
    imgs_dir = ROOT / "demo/labeled/images"
    tmp_labels = OUT / "label_tool_labels"
    tmp_labels.mkdir(parents=True, exist_ok=True)
    for f in tmp_labels.glob("*.txt"):
        f.unlink()
    images = [imgs_dir / "demo_0011.jpg", imgs_dir / "demo_0012.jpg"]
    tool = lt.LabelTool(images, imgs_dir, tmp_labels, ["car", "green", "oo", "red", "xx"])
    tool.load()
    log = []

    def snap(note):
        tool.render()
        log.append(note)

    gt = [l.split() for l in (ROOT / "demo/labeled/labels/demo_0011.txt").read_text().split("\n") if l.strip()]
    h, w = tool.img.shape[:2]
    snap("start")
    for c, xc, yc, bw, bh in gt:
        c, xc, yc, bw, bh = int(c), float(xc), float(yc), float(bw), float(bh)
        tool.cls = c
        snap(f"key {c}")
        x1, y1 = (xc - bw / 2) * w * tool.scale, (yc - bh / 2) * h * tool.scale
        x2, y2 = (xc + bw / 2) * w * tool.scale, (yc + bh / 2) * h * tool.scale
        tool.on_mouse(lt.cv2.EVENT_LBUTTONDOWN, int(x1), int(y1), 0, None)
        for k in range(1, 7):
            tool.on_mouse(lt.cv2.EVENT_MOUSEMOVE, int(x1 + (x2 - x1) * k / 6), int(y1 + (y2 - y1) * k / 6), 0, None)
            snap(f"drag {k}")
        tool.on_mouse(lt.cv2.EVENT_LBUTTONUP, int(x2), int(y2), 0, None)
        snap("box done")
    tool.save(force=True)
    snap("saved")
    for i, fr in enumerate(frames):
        cv2.imwrite(str(OUT / f"label_tool_{i:02d}.png"), fr)
    meta["label_tool"] = {"frames": len(frames), "log": log,
                          "saved_txt": (tmp_labels / "demo_0011.txt").read_text()}
    print(f"[label tool] {len(frames)} frames captured")


def live_stream(meta):
    """실제 카메라 연속 프레임 → YOLO → StableTrigger (주행 코드 그대로)."""
    from ultralytics import YOLO
    from raspbot.perception.yolo_events import StableTrigger
    m = YOLO(str(HV / "yolo_ox.pt"))
    files = sorted((DATA / "n").glob("*.jpg"), key=lambda p: int(p.stem.split("_")[-1]))
    trig = StableTrigger(confirm_frames=3, cooldown_s=0.0, release_frames=2)
    rows = []
    sd = OUT / "stream"
    sd.mkdir(parents=True, exist_ok=True)
    for f in sd.glob("*.jpg"):
        f.unlink()
    for i, f in enumerate(files[:60]):
        img = cv2.imread(str(f))
        t0 = time.perf_counter()
        r = m.predict(img, imgsz=320, conf=0.5, verbose=False)[0]
        ms = (time.perf_counter() - t0) * 1000
        present = any(m.names[int(c)] == "xx" for c in r.boxes.cls)
        fired = trig.update(present, now=i * 0.1)
        cv2.imwrite(str(sd / f"{i:03d}.jpg"), r.plot())
        rows.append({"i": i, "file": f.name, "present": present, "fired": fired, "ms": round(ms, 1),
                     "count": trig._present_count})
    meta["stream"] = rows
    print(f"[stream] {len(rows)} frames, fired at {[r['i'] for r in rows if r['fired']]}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    meta = {}
    haar_assets(meta)
    yolo_assets(meta)
    label_tool_frames(meta)
    live_stream(meta)
    (OUT / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"saved: {OUT}")


if __name__ == "__main__":
    main()
