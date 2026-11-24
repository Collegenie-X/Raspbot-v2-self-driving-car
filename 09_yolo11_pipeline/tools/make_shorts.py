"""
YOLO11 세로 쇼츠 시리즈 렌더러 (1080x1920, 30fps, 편당 약 60초)

화면 구성 (위→아래): 채널 라벨 · 제목 박스 · 노란 태그 · 비주얼(이미지 위주, 움직임) · 큰 자막 · 진행 바
대본: tools/shorts_script.py   나레이션: demo/shorts/audio/NN.mp3 (Higgsfield MiniMax, 없으면 macOS say)
그림: demo/shorts/illust/*.png (Higgsfield 생성) + 실제 실행 결과 (demo/*)

사용 예:
  python tools/make_shorts.py                 # 5편 모두
  python tools/make_shorts.py --ep ep2        # 한 편만
  python tools/make_shorts.py --ep ep1 --preview   # 비트별 미리보기 PNG
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
DEMO = ROOT / "demo"
SH = DEMO / "shorts"
VA_ASSETS = DEMO / "video_v2_assets"
HV = DEMO / "haar_vs_yolo"
sys.path.insert(0, str(ROOT / "tools"))
from shorts_script import EPISODES  # noqa: E402

W, H, FPS = 1080, 1920, 30
VX, VY, VW, VH = 60, 470, 960, 980          # 비주얼 영역
GAP, HEAD, TAIL = 0.3, 0.25, 0.9
TEMPO = 1.07          # 나레이션 속도 (쇼츠 템포, 음높이는 유지)

WHITE = (255, 255, 255)
YEL = (255, 214, 10)
CYAN = (56, 220, 255)
GREEN = (74, 222, 128)
RED = (255, 92, 92)
ORANGE = (255, 159, 67)
MUTED = (160, 174, 192)
DARK = (12, 18, 34)
PANEL = (22, 32, 56)

SD = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
MENLO = "/System/Library/Fonts/Menlo.ttc"
_F = {}


def F(size, w="b"):
    key = (size, w)
    if key not in _F:
        _F[key] = ImageFont.truetype(MENLO if w == "mono" else SD, size,
                                     index={"r": 0, "m": 2, "s": 4, "b": 6, "mono": 0}[w])
    return _F[key]


# ------------------------------------------------------------------ 애니메이션
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def back(x):
    x = clamp(x)
    c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def prog(t, st, dur=0.35):
    return ease((t - st) / dur) if dur > 0 else float(t >= st)


def lerp(a, b, k):
    return a + (b - a) * k


def rgba(c, a=1.0):
    return (*c[:3], int(255 * clamp(a)))


# ------------------------------------------------------------------ 그리기 유틸
def text_w(d, s, f):
    return d.textlength(s, font=f)


def text_c(d, cx, y, s, f, fill, stroke=0, sfill=(0, 0, 0)):
    d.text((cx - text_w(d, s, f) / 2, y), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)


def parse_hl(s):
    """'a **b** c' → [(a, False), (b, True), (c, False)]"""
    out = []
    for i, part in enumerate(re.split(r"\*\*", s)):
        if part:
            out.append((part, i % 2 == 1))
    return out


def rich_lines(d, s, f, maxw):
    """강조 표시를 유지한 채 단어 단위 줄바꿈."""
    tokens = []
    for seg, hl in parse_hl(s):
        for k, wd in enumerate(seg.split(" ")):
            if k > 0:
                tokens.append((" ", hl))
            if wd:
                tokens.append((wd, hl))
    lines, cur, cw = [], [], 0
    for tok, hl in tokens:
        w = text_w(d, tok, f)
        if cw + w > maxw and cur and tok != " ":
            lines.append(cur)
            cur, cw = [], 0
        if tok == " " and not cur:
            continue
        cur.append((tok, hl))
        cw += w
    if cur:
        lines.append(cur)
    return lines


def draw_rich_c(d, cx, y, s, f, base=WHITE, hl=YEL, stroke=6, lh=None, maxw=940, alpha=1.0):
    lines = rich_lines(d, s, f, maxw)
    lh = lh or int(f.size * 1.3)
    for i, ln in enumerate(lines):
        tw = sum(text_w(d, tok, f) for tok, _ in ln)
        x = cx - tw / 2
        for tok, h in ln:
            d.text((x, y + i * lh), tok, font=f, fill=rgba(hl if h else base, alpha), stroke_width=stroke,
                   stroke_fill=rgba((0, 0, 0), alpha))
            x += text_w(d, tok, f)
    return len(lines) * lh


def rr(d, box, fill=None, outline=None, r=28, w=4):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=w)


def chip(d, cx, y, s, f, fill=YEL, color=DARK, pad=26, alpha=1.0):
    tw = text_w(d, s, f)
    h = f.size + 26
    rr(d, (cx - tw / 2 - pad, y, cx + tw / 2 + pad, y + h), fill=rgba(fill, alpha), r=h // 2)
    d.text((cx - tw / 2, y + 9), s, font=f, fill=rgba(color, alpha))
    return h


def fit(img, w, h, mode="contain"):
    s = (min if mode == "contain" else max)(w / img.width, h / img.height)
    return img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)


def round_mask(size, r, alpha=1.0):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=r, fill=int(255 * clamp(alpha)))
    return m


def put(c, img, box, alpha=1.0, mode="contain", r=26, zoom=1.0, border=None, bw=5, pan=(0.5, 0.5)):
    """이미지를 box 안에 붙임. zoom>1 이면 확대 후 크롭(Ken Burns)."""
    x1, y1, x2, y2 = map(int, box)
    bw_, bh_ = x2 - x1, y2 - y1
    if alpha <= 0.01 or bw_ <= 2 or bh_ <= 2:
        return None
    im = fit(img, bw_ * zoom, bh_ * zoom, mode)
    if mode == "cover" or zoom > 1:
        cw, ch = min(im.width, bw_), min(im.height, bh_)
        ox = int((im.width - cw) * pan[0])
        oy = int((im.height - ch) * pan[1])
        im = im.crop((ox, oy, ox + cw, oy + ch))
    px, py = x1 + (bw_ - im.width) // 2, y1 + (bh_ - im.height) // 2
    c.paste(im.convert("RGB"), (px, py), round_mask(im.size, r, alpha))
    if border:
        ImageDraw.Draw(c).rounded_rectangle((px - 2, py - 2, px + im.width + 1, py + im.height + 1), radius=r,
                                            outline=rgba(border, alpha), width=bw)
    return px, py, im.width, im.height


def arrow(d, p1, p2, color, w=8, head=26):
    d.line([p1, p2], fill=color, width=w)
    ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    pts = [p2] + [(p2[0] + head * math.cos(ang + math.pi + s * 0.5), p2[1] + head * math.sin(ang + math.pi + s * 0.5))
                  for s in (-1, 1)]
    d.polygon(pts, fill=color)


def terminal(c, d, box, lines, t, start=0.0, size=30, cps=40, alpha=1.0, title="Terminal"):
    """lines: [(text, color, 'cmd'|'out')]"""
    x1, y1, x2, y2 = box
    rr(d, box, fill=rgba((14, 20, 36), 0.96 * alpha), outline=rgba((60, 76, 110), alpha), r=22, w=3)
    for i, col in enumerate([RED, YEL, GREEN]):
        d.ellipse((x1 + 24 + i * 32, y1 + 20, x1 + 44 + i * 32, y1 + 40), fill=rgba(col, alpha))
    d.text((x1 + 140, y1 + 14), title, font=F(24, "m"), fill=rgba(MUTED, alpha))
    y, now = y1 + 66, start
    fm, fk = F(size, "mono"), F(size, "m")
    for text, col, kind in lines:
        if y > y2 - size * 1.4:
            break
        if kind == "cmd":
            n = int((t - now) * cps)
            if n <= 0:
                break
            shown = ("$ " + text)[: n + 2]
            draw_mixed(d, x1 + 24, y, shown, size, col, alpha)
            now += len(text) / cps + 0.2
            if n < len(text):
                break
        else:
            if t < now:
                break
            draw_mixed(d, x1 + 24, y, text, size, col, alpha * prog(t, now, 0.2))
            now += 0.07
        y += size * 1.45


def draw_mixed(d, x, y, s, size, col, alpha=1.0):
    """영문=Menlo, 한글=SD 고딕."""
    fm, fk = F(size, "mono"), F(size, "m")
    for ch in s:
        f = fk if ord(ch) > 0x2fff else fm
        d.text((x, y + (-3 if f is fk else 0)), ch, font=f, fill=rgba(col, alpha))
        x += text_w(d, ch, f)
    return x


def bar(d, x, y, w, h, frac, col, bg=(40, 52, 80), alpha=1.0, r=12):
    rr(d, (x, y, x + w, y + h), fill=rgba(bg, alpha), r=r, w=0)
    if frac > 0.003:
        rr(d, (x, y, x + max(h, w * clamp(frac)), y + h), fill=rgba(col, alpha), r=r, w=0)


# ------------------------------------------------------------------ 데이터
class A:
    pass


def load_assets():
    A.ill = {p.stem: Image.open(p).convert("RGB") for p in (SH / "illust").glob("*.png")}
    A.meta = json.loads((VA_ASSETS / "meta.json").read_text(encoding="utf-8"))
    A.hv = json.loads((HV / "results.json").read_text(encoding="utf-8"))
    A.val = json.loads((DEMO / "reports/validate_val.json").read_text(encoding="utf-8"))
    A.yin_full = Image.open(VA_ASSETS / "yolo_input.jpg").convert("RGB")
    # 검은 배경이 넓은 카메라 화면 → 카드 주변을 4:3 으로 잘라 크게 보여줌
    from haar_vs_yolo_experiment import card_box
    x1, y1, x2, y2 = card_box(np.array(A.yin_full)[:, :, ::-1])
    cw = max(170, (x2 - x1) * 2.6)
    ch = cw * 0.75
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2 - 8
    bx1 = int(clamp(cx - cw / 2, 0, 320 - cw))
    by1 = int(clamp(cy - ch / 2, 0, 240 - ch))
    crop = (bx1, by1, int(bx1 + cw), int(by1 + ch))
    A.yin = A.yin_full.crop(crop)
    A.nms_b = Image.open(VA_ASSETS / "nms_before.jpg").convert("RGB").crop(crop)
    A.nms_a = Image.open(VA_ASSETS / "nms_after.jpg").convert("RGB").crop(crop)
    lb = Image.new("RGB", (320, 320), (114, 114, 114))      # YOLO 레터박스(회색 패딩)
    lb.paste(A.yin_full, (0, 40))
    A.letterbox = lb
    A.feats = [Image.open(VA_ASSETS / f"feat_L{i}.png").convert("RGB") for i in (0, 2, 4, 6)]
    A.label = [Image.open(p).convert("RGB") for p in sorted(VA_ASSETS.glob("label_tool_*.png"))]
    A.stream = [Image.open(p).convert("RGB") for p in sorted((VA_ASSETS / "stream").glob("*.jpg"))]
    A.p_imgs = [Image.open(p).convert("RGB") for p in sorted((REPO / "04_cascade/park_data_example/p").glob("*.jpg"))]
    A.n_imgs = [Image.open(p).convert("RGB") for p in
                sorted((REPO / "04_cascade/park_data_example/n").glob("*.jpg"), key=lambda p: int(p.stem.split("_")[-1]))]
    sp = Image.open(next(HV.glob("samples_p_*.jpg"))).convert("RGB")
    sn = Image.open(next(HV.glob("samples_n_*.jpg"))).convert("RGB")
    kinds = ["원본", "어둡게", "회전 25°", "흐림", "작게"]
    A.samp = {}
    for name, im in (("p", sp), ("n", sn)):
        for i, k in enumerate(kinds):
            A.samp[(name, k, "haar")] = im.crop((i * 320, 0, i * 320 + 320, 240))
            A.samp[(name, k, "yolo")] = im.crop((i * 320, 240, i * 320 + 320, 480))
    A.kinds = kinds
    A.pr = Image.open(DEMO / "runs/train/demo_yolo11/BoxPR_curve.png").convert("RGB")
    with open(DEMO / "runs/train/demo_yolo11/results.csv") as f:
        A.results = [{k.strip(): float(v) for k, v in r.items()} for r in csv.DictReader(f)]
    A.thumbs = [Image.open(p).convert("RGB").resize((120, 90)) for p in sorted((DEMO / "labeled/images").glob("*.jpg"))[1:41]]


# ------------------------------------------------------------------ 비주얼 (c: 960x980 RGBA, t: 비트 내 시간)
V = {}


def vis(name):
    def deco(fn):
        V[name] = fn
        return fn
    return deco


@vis("illust")
def v_illust(c, d, t, T, a):
    z = 1.0 + 0.08 * (t / max(T, 0.1)) if a.get("zoom") else 1.0
    put(c, A.ill[a["img"]], (0, 0, VW, VH), mode="cover", zoom=z, r=36)
    if a.get("badge"):
        k = prog(t, 0.6, 0.4)
        if k > 0:
            f = F(44, "mono")
            tw = text_w(d, a["badge"], f)
            rr(d, (VW / 2 - tw / 2 - 30, VH - 140, VW / 2 + tw / 2 + 30, VH - 60), fill=rgba(DARK, 0.85 * k),
               outline=rgba(YEL, k), r=20)
            d.text((VW / 2 - tw / 2, VH - 128), a["badge"], font=f, fill=rgba(YEL, k))


@vis("cover_photo")
def v_cover(c, d, t, T, a):
    put(c, A.ill["cover"], (0, 0, VW, VH), mode="cover", zoom=1.0 + 0.06 * t / T, r=36)
    k = back((t - 0.5) / 0.45)
    if t > 0.5:
        w = lerp(300, 620, k)
        put(c, A.yin, (VW / 2 - w / 2, VH - w * 0.75 - 70, VW / 2 + w / 2, VH - 70), border=CYAN, r=20)
        chip(d, VW / 2, VH - w * 0.75 - 130, "실제 라즈봇 카메라 320×240", F(32, "s"), fill=CYAN, alpha=clamp(k))


@vis("timer_detect")
def v_timer(c, d, t, T, a):
    put(c, A.nms_a, (20, 120, VW - 20, 840), border=CYAN, r=24, zoom=1.0 + 0.05 * t / T)
    v = 0.012 * clamp(t / 1.0)
    text_c(d, VW / 2, 0, f"{v:.3f}초", F(110, "b"), YEL, stroke=6)
    k = prog(t, 1.2)
    if k > 0:
        chip(d, VW / 2, 870, "실측 11.9ms · M2 CPU · 320px", F(34, "s"), fill=CYAN, alpha=k)


@vis("haar_scan_count")
def v_haar_scan(c, d, t, T, a):
    put(c, A.ill["haar"], (130, 0, VW - 130, 430), mode="cover", r=30)
    frame = A.n_imgs[20]
    px, py, pw, ph = put(c, frame, (60, 470, VW - 60, 470 + (VW - 120) * 0.75), r=16)
    s = pw / 320
    n = int(110364 * clamp(t / (T * 0.8)))
    step = int(t * 140)
    for k in range(3):
        sc = 1.0 + 0.6 * k
        ww, hh = 32 * sc * s, 24 * sc * s
        cols = int((pw - ww) / (12 * s)) + 1
        i = (step + k * 37) % (cols * 12)
        x = px + (i % cols) * 12 * s
        y = py + ((i // cols) % 12) * (ph - hh) / 11
        d.rectangle((x, y, x + ww, y + hh), outline=rgba([YEL, CYAN, ORANGE][k]), width=4)
    text_c(d, VW / 2, VH - 110, f"검사한 창 {n:,}개", F(62, "b"), YEL, stroke=5)


@vis("yolo_word")
def v_yolo_word(c, d, t, T, a):
    put(c, A.ill["yolo"], (160, 380, VW - 160, VH), mode="cover", r=30, alpha=prog(t, 0.8, 0.5))
    words = [("Y", "ou"), ("O", "nly"), ("L", "ook"), ("O", "nce")]
    for i, (big, rest) in enumerate(words):
        k = back((t - i * 0.25) / 0.35)
        if t < i * 0.25:
            continue
        x = 60 + i * 225
        f = F(int(150 * clamp(k, 0, 1.2)), "b")
        d.text((x + 20, 40), big, font=f, fill=YEL, stroke_width=4, stroke_fill=(0, 0, 0))
        d.text((x + 30, 230), big + rest, font=F(46, "s"), fill=rgba(WHITE, clamp(k)))


@vis("feature_maps")
def v_feats(c, d, t, T, a):
    put(c, A.yin, (330, 0, 630, 225), r=14, border=CYAN, bw=3)
    labels = ["1층 · 16채널 160×160", "3층 · 64채널 80×80", "5층 · 128채널 40×40", "7층 · 128채널 20×20"]
    descs = ["선 · 경계", "모서리 · 면", "부분 모양", "물체 의미"]
    for i, (fm, lb, ds) in enumerate(zip(A.feats, labels, descs)):
        k = prog(t, 0.3 + i * 0.55, 0.4)
        if k <= 0:
            continue
        y = 250 + i * 182
        put(c, fm, (20 + (1 - k) * 80, y, 620 + (1 - k) * 80, y + 150), alpha=k, r=10)
        d.text((650, y + 22), lb, font=F(30, "s"), fill=rgba(WHITE, k))
        d.text((650, y + 70), ds, font=F(40, "b"), fill=rgba(YEL, k))
        if i < 3:
            arrow(d, (320, y + 152), (320, y + 178), rgba(CYAN, k), 5, 14)


@vis("grid")
def v_grid(c, d, t, T, a):
    sizes = a["sizes"]
    idx = min(len(sizes) - 1, int(t / max(T, 0.1) * len(sizes)))
    n = sizes[idx]
    px, py, pw, ph = put(c, A.letterbox, (60, 60, VW - 60, VW - 60), r=10)
    k = prog(t - idx * T / len(sizes), 0, 0.4)
    for g in range(1, n):
        x = px + pw * g / n
        y = py + ph * g / n
        d.line([(x, py), (x, py + ph * k)], fill=rgba(CYAN, 0.75), width=2 if n > 20 else 3)
        d.line([(px, y), (px + pw * k, y)], fill=rgba(CYAN, 0.75), width=2 if n > 20 else 3)
    if n == 10 and len(sizes) == 1:   # 물체 중심 칸 강조
        from haar_vs_yolo_experiment import card_box
        bx = card_box(np.array(A.yin_full)[:, :, ::-1])
        cx, cy = (bx[0] + bx[2]) / 2 / 320, ((bx[1] + bx[3]) / 2 + 40) / 320
        gx, gy = int(cx * n), int(cy * n)
        kk = prog(t, 1.0)
        d.rectangle((px + pw * gx / n, py + ph * gy / n, px + pw * (gx + 1) / n, py + ph * (gy + 1) / n),
                    outline=rgba(YEL, kk), width=7)
    if len(sizes) > 1:
        sub = {40: "작은 물체 담당", 20: "중간 물체 담당", 10: "큰 물체 담당"}[n]
        d.text((70, VW - 50), "320×320 입력 (위아래 회색 = 패딩)", font=F(30, "m"), fill=MUTED)
        chip(d, VW / 2, VH - 110, f"{n}×{n} = {n * n:,}칸 · {sub}", F(40, "b"))


@vis("count_2100")
def v_2100(c, d, t, T, a):
    rows = [("40×40", 1600, CYAN), ("20×20", 400, GREEN), ("10×10", 100, ORANGE)]
    for i, (lb, v, col) in enumerate(rows):
        k = prog(t, i * 0.4, 0.4)
        y = 60 + i * 200
        d.text((120, y), lb, font=F(64, "b"), fill=rgba(col, k))
        d.text((520, y), f"{int(v * k):,}", font=F(84, "b"), fill=rgba(WHITE, k))
        if i:
            d.text((420, y), "+", font=F(84, "b"), fill=rgba(MUTED, k))
    k = prog(t, 1.4, 0.5)
    d.line([(100, 660), (VW - 100, 660)], fill=rgba(WHITE, k), width=6)
    text_c(d, VW / 2, 700, f"{int(2100 * k):,}", F(200, "b"), rgba(YEL, k), stroke=6)
    text_c(d, VW / 2, 920, "후보 박스 (입력 320px)", F(40, "s"), rgba(MUTED, k))


@vis("tensor")
def v_tensor(c, d, t, T, a):
    text_c(d, VW / 2, 20, "출력 텐서", F(48, "s"), MUTED)
    shape = A.meta["yolo_raw_shape"]
    text_c(d, VW / 2, 90, f"[{shape[0]}, {shape[1]}, {shape[2]}]", F(120, "b"), YEL, stroke=5)
    cells = [("x", CYAN), ("y", CYAN), ("w", CYAN), ("h", CYAN), ("oo", GREEN), ("xx", ORANGE)]
    for i, (s, col) in enumerate(cells):
        k = back((t - 0.5 - i * 0.18) / 0.35)
        if t < 0.5 + i * 0.18:
            continue
        x = 40 + i * 150
        rr(d, (x, 330, x + 135, 470), fill=rgba(PANEL), outline=rgba(col), r=18)
        text_c(d, x + 67, 360, s, F(int(64 * clamp(k, 0, 1.15)), "b"), col)
    k = prog(t, 1.8)
    d.text((60, 520), "박스 위치 4개", font=F(46, "b"), fill=rgba(CYAN, k))
    d.text((560, 520), "클래스 점수 2개", font=F(46, "b"), fill=rgba(GREEN, k))
    k = prog(t, 2.4)
    rr(d, (60, 640, VW - 60, 900), fill=rgba(PANEL, k), outline=rgba(YEL, k), r=24)
    text_c(d, VW / 2, 680, "× 2100칸 = 한 번에 계산", F(60, "b"), rgba(WHITE, k))
    text_c(d, VW / 2, 790, "창을 옮기지 않아요", F(48, "m"), rgba(YEL, k))


@vis("nms_before")
def v_nms_b(c, d, t, T, a):
    put(c, A.nms_b, (20, 40, VW - 20, 760), border=ORANGE, r=24, zoom=1.0 + 0.25 * ease(t / T), pan=(0.35, 0.35))
    chip(d, VW / 2, 820, f"후보 {A.meta['nms']['raw_candidates']}개 (점수 ≥ 0.01)", F(46, "b"), fill=ORANGE)


@vis("nms_after")
def v_nms_a(c, d, t, T, a):
    k = prog(t, 0.0, 0.7)
    put(c, A.nms_b, (20, 40, VW - 20, 760), r=24, zoom=1.25, pan=(0.35, 0.35), alpha=1 - k)
    put(c, A.nms_a, (20, 40, VW - 20, 760), r=24, zoom=1.25, pan=(0.35, 0.35), alpha=k, border=GREEN)
    name, sc = A.meta["nms"]["final_det"][0]
    kk = back((t - 0.6) / 0.4)
    if t > 0.6:
        chip(d, VW / 2, 820, f"최종 1개 · {name} {sc:.2f}", F(int(52 * clamp(kk, 0.5, 1.1)), "b"), fill=GREEN)


@vis("summary")
def v_summary(c, d, t, T, a):
    rr(d, (40, 60, VW - 40, VH - 80), fill=rgba(PANEL, 0.95), outline=YEL, r=36, w=5)
    text_c(d, VW / 2, 110, "한 줄 요약", F(56, "b"), YEL)
    for i, (k1, k2) in enumerate(a["items"]):
        k = prog(t, 0.3 + i * 0.45, 0.35)
        if k <= 0:
            continue
        y = 260 + i * 200
        d.ellipse((100, y, 180, y + 80), fill=rgba(CYAN, k))
        text_c(d, 140, y + 12, str(i + 1), F(50, "b"), rgba(DARK, k))
        d.text((220 + (1 - k) * 40, y + 2), k1, font=F(64, "b"), fill=rgba(WHITE, k))
        d.text((220 + (1 - k) * 40, y + 86), k2, font=F(38, "m"), fill=rgba(MUTED, k))


# ---------------- EP2
@vis("ox_collage")
def v_ox(c, d, t, T, a):
    imgs = [A.p_imgs[i] for i in (0, 9, 18, 27, 36)] + [A.n_imgs[i] for i in (0, 12, 24, 44, 60, 70, 84)]
    for i, im in enumerate(imgs):
        k = back((t - i * 0.08) / 0.35)
        if t < i * 0.08:
            continue
        r_, col = divmod(i, 3)
        x, y = 30 + col * 305, 20 + r_ * 225
        s = clamp(k, 0, 1.1)
        cx, cy = x + 145, y + 105
        put(c, im, (cx - 145 * s, cy - 105 * s, cx + 145 * s, cy + 105 * s), mode="cover", r=14,
            border=GREEN if i < 5 else ORANGE, bw=3)
    k = prog(t, 1.4)
    chip(d, VW / 2, 925, "O 사진 39장  ·  X 카메라 화면 93장", F(40, "b"), alpha=k)


@vis("haar_card")
def v_haar_card(c, d, t, T, a):
    put(c, A.ill["haar"], (0, 0, VW, 520), mode="cover", r=30, zoom=1 + 0.05 * t / T)
    hv = A.meta["haar"]
    rows = [("cascade.xml", WHITE), (f"창 크기 {hv['window'][0]}×{hv['window'][1]}", CYAN),
            (f"{hv['n_stages']}단계 · 단계마다 특징 1개", CYAN), ("흑백 이미지만 사용", ORANGE)]
    for i, (s, col) in enumerate(rows):
        k = prog(t, 0.4 + i * 0.3)
        y = 560 + i * 100
        d.text((80 + (1 - k) * 40, y), "• " + s, font=F(54, "b"), fill=rgba(col, k))


def haar_window_view(c, d, t, upto, label=True):
    o = A.p_imgs[5].convert("L").resize((32, 24), Image.BILINEAR).resize((768, 576), Image.NEAREST).convert("RGB")
    put(c, o, (96, 40, 864, 616), r=8)
    S = 24
    feats = A.meta["haar"]["used_features"]
    for j, f in enumerate(feats[:upto]):
        k = prog(t, j * 0.6, 0.35) if upto > 1 else 1.0
        layer = Image.new("RGBA", (768, 576), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        for x, y, w, h, wt in f["rects"]:
            col = (0, 0, 0, int(150 * k)) if wt < 0 else (255, 255, 255, int(170 * k))
            ld.rectangle((x * S, y * S, (x + w) * S, (y + h) * S), fill=col, outline=(255, 214, 10, int(255 * k)),
                         width=4)
        c.alpha_composite(layer, (96, 40))
    if label:
        for j in range(min(upto, 4)):
            k = prog(t, j * 0.6, 0.35) if upto > 1 else 1.0
            chip(d, 160 + j * 215, 650, f"{j + 1}단계 특징", F(34, "b"), fill=[CYAN, GREEN, ORANGE, YEL][j], alpha=k)


@vis("haar_features")
def v_haar_feat(c, d, t, T, a):
    haar_window_view(c, d, t, 4)
    text_c(d, VW / 2, 760, "32×24 흑백 창 (실제 학습된 특징 4개)", F(40, "s"), MUTED)


@vis("haar_diff")
def v_haar_diff(c, d, t, T, a):
    haar_window_view(c, d, 9, 1, label=False)
    k = prog(t, 0.3)
    rr(d, (60, 650, VW - 60, 930), fill=rgba(PANEL, k), outline=rgba(YEL, k), r=26)
    text_c(d, VW / 2, 680, "흰 영역 밝기  -  검은 영역 밝기", F(50, "b"), rgba(WHITE, k))
    text_c(d, VW / 2, 770, "> 기준값 ?", F(64, "b"), rgba(YEL, k))
    kk = prog(t, 1.2)
    text_c(d, VW / 2, 860, "→ 통과 / 탈락", F(44, "m"), rgba(CYAN, kk))


@vis("haar_stages")
def v_haar_stages(c, d, t, T, a):
    xs = [40, 270, 500, 730]
    for i, x in enumerate(xs):
        rr(d, (x, 280, x + 190, 480), fill=rgba(PANEL), outline=rgba([CYAN, GREEN, ORANGE, YEL][i]), r=24, w=5)
        text_c(d, x + 95, 345, f"{i + 1}단계", F(50, "b"), WHITE)
        if i < 3:
            arrow(d, (x + 194, 380), (x + 226, 380), MUTED, 6, 16)
    # 창 토큰: 대부분 앞 단계에서 탈락
    rng = np.random.default_rng(1)
    for j in range(14):
        st = j * 0.22
        u = (t - st) / 1.4
        if u < 0 or u > 1.2:
            continue
        dies = int(rng.choice([0, 0, 0, 1, 1, 2, 3, 4], 1)[0]) if j % 7 != 6 else 4
        pos = lerp(20, 940, clamp(u))
        stage_x = xs[min(dies, 3)] + 95 if dies < 4 else 1100
        if pos > stage_x and dies < 4:
            fall = (pos - stage_x) / 200
            d.rectangle((stage_x - 28, 500 + fall * 260, stage_x + 28, 540 + fall * 260), fill=rgba(RED, 1 - clamp(fall)))
        else:
            d.rectangle((pos - 28, 400, pos + 28, 440), outline=YEL, width=5)
    k = prog(t, 0.8)
    text_c(d, 480, 820, "대부분 1~2단계에서 탈락 → 빠름", F(50, "b"), rgba(YEL, k))
    text_c(d, 480, 150, "창 하나하나 검사 (원리 그림)", F(40, "s"), rgba(MUTED, 1))
    text_c(d, 825, 560, "통과 = O!", F(56, "b"), rgba(GREEN, prog(t, 1.6)))
    text_c(d, 480, 720, "탈락 ↓", F(44, "b"), rgba(RED, prog(t, 0.6)))


@vis("yolo_train_card")
def v_yolo_train(c, d, t, T, a):
    put(c, A.ill["training"], (130, 0, VW - 130, 600), mode="cover", r=30)
    lines = [("python tools/haar_vs_yolo_experiment.py", YEL, "cmd"),
             ("yolo11n · 40 epoch · CPU", WHITE, "out"),
             ("YOLO 학습 완료 170s", GREEN, "out"),
             ("val mAP50 0.995 · mAP50-95 0.912", GREEN, "out")]
    terminal(c, d, (20, 640, VW - 20, 960), lines, t, start=0.3, size=30, cps=60)


def duel_card(c, d, x, who, kind, val, col, t, st):
    k = back((t - st) / 0.4)
    if t < st:
        return
    put(c, A.samp[("p", kind, who)], (x, 120, x + 440, 450), r=20, border=col, mode="cover")
    text_c(d, x + 220, 30, "Haar" if who == "haar" else "YOLO11", F(56, "b"), col)
    text_c(d, x + 220, 480, f"{val:.0%}", F(int(150 * clamp(k, 0.3, 1.1)), "b"), col, stroke=5)
    text_c(d, x + 220, 680, "O 찾은 비율", F(38, "m"), MUTED)


@vis("duel")
def v_duel(c, d, t, T, a):
    s = A.hv["summary"][a["kind"]]
    duel_card(c, d, 20, "haar", a["kind"], s["haar_o_recall"], ORANGE, t, 0.0)
    duel_card(c, d, 500, "yolo", a["kind"], s["yolo_o_recall"], CYAN, t, 0.5)
    chip(d, VW / 2, 800, f"조건: {a['kind']}  ·  test O 사진 {s['n_o']}장", F(40, "b"))
    if s["haar_o_recall"] == 0:
        k = back((t - 1.0) / 0.4)
        if t > 1.0:
            d.line([(60, 140), (420, 430)], fill=RED, width=int(14 * clamp(k)))
            d.line([(420, 140), (60, 430)], fill=RED, width=int(14 * clamp(k)))


@vis("rotate_tease")
def v_rotate(c, d, t, T, a):
    ang = 25 * ease(t / max(T * 0.7, 0.1))
    im = A.p_imgs[30].resize((560, 420)).rotate(ang, expand=False, fillcolor=(0, 0, 0))
    put(c, im, (200, 150, 760, 570), r=20, border=YEL)
    text_c(d, VW / 2, 650, f"{ang:4.1f}°", F(170, "b"), YEL, stroke=6)


@vis("false_alarm")
def v_false(c, d, t, T, a):
    put(c, A.samp[("p", "흐림", "haar")], (240, 20, 720, 380), r=20, border=ORANGE, mode="cover")
    text_c(d, VW / 2, 390, "흐린 사진 (Haar 결과)", F(34, "m"), MUTED)
    for i, k_ in enumerate(A.kinds):
        v = A.hv["summary"][k_]["haar_x_false_rate"]
        k = prog(t, 0.3 + i * 0.15, 0.5)
        y = 470 + i * 95
        hl = k_ == "흐림"
        d.text((40, y), k_, font=F(42, "b"), fill=YEL if hl else WHITE)
        bar(d, 260, y + 6, 520, 48, v / 0.25 * k, RED if hl else ORANGE)
        d.text((800, y), f"{v * k:.0%}", font=F(46, "b"), fill=YEL if hl else WHITE)
    text_c(d, VW / 2, 945, "Haar: X를 O로 착각한 비율", F(34, "m"), MUTED)


@vis("all_bars")
def v_allbars(c, d, t, T, a):
    for i, k_ in enumerate(A.kinds):
        s = A.hv["summary"][k_]
        y = 40 + i * 175
        k = prog(t, 0.2 + i * 0.15, 0.5)
        d.text((40, y + 30), k_, font=F(44, "b"), fill=WHITE)
        bar(d, 280, y + 10, 560, 50, s["haar_o_recall"] * k, ORANGE)
        bar(d, 280, y + 75, 560, 50, s["yolo_o_recall"] * k, CYAN)
        d.text((860, y + 10), f"{s['haar_o_recall'] * k:.0%}", font=F(40, "b"), fill=ORANGE)
        d.text((860, y + 75), f"{s['yolo_o_recall'] * k:.0%}", font=F(40, "b"), fill=CYAN)
    rr(d, (280, 900, 320, 940), fill=ORANGE, r=8, w=0)
    d.text((335, 896), "Haar", font=F(38, "b"), fill=WHITE)
    rr(d, (520, 900, 560, 940), fill=CYAN, r=8, w=0)
    d.text((575, 896), "YOLO11", font=F(38, "b"), fill=WHITE)


@vis("speed")
def v_speed(c, d, t, T, a):
    put(c, A.ill["stopwatch"], (180, 0, VW - 180, 560), mode="cover", r=30)
    s = A.hv["summary"]["원본"]
    for i, (lb, v, col) in enumerate([("Haar", s["haar_ms"], ORANGE), ("YOLO11", s["yolo_ms"], CYAN)]):
        k = prog(t, 0.3 + i * 0.4, 0.6)
        y = 620 + i * 130
        d.text((40, y), lb, font=F(50, "b"), fill=col)
        bar(d, 280, y + 4, 520, 60, v / 16 * k, col)
        d.text((815, y + 2), f"{v * k:.1f}ms", font=F(46, "b"), fill=WHITE)
    text_c(d, VW / 2, 900, "이미지 1장 · M2 Max CPU 중앙값", F(34, "m"), MUTED)


@vis("experiment_cmd")
def v_exp_cmd(c, d, t, T, a):
    s = A.hv["summary"]
    lines = [("python tools/haar_vs_yolo_experiment.py", YEL, "cmd"), ("", WHITE, "out"),
             ("조건      Haar O   YOLO O   Haar 오탐", MUTED, "out")]
    for k_ in A.kinds:
        v = s[k_]
        lines.append((f"{k_:<7} {v['haar_o_recall']:>6.0%} {v['yolo_o_recall']:>8.0%} {v['haar_x_false_rate']:>9.0%}",
                      WHITE, "out"))
    lines += [("", WHITE, "out"), (f"test: O {s['원본']['n_o']} · X {s['원본']['n_x']} · 배경 {s['원본']['n_bg']}", CYAN, "out")]
    terminal(c, d, (10, 40, VW - 10, 820), lines, t, start=0.2, size=31, cps=55)
    k = prog(t, 2.0)
    text_c(d, VW / 2, 860, "⚠ Haar는 test O 사진으로도 학습됨 (Haar에 유리)".replace("⚠ ", ""), F(34, "m"), rgba(ORANGE, k))


# ---------------- EP3
@vis("timeline")
def v_timeline(c, d, t, T, a):
    items = [("2015", "YOLO 첫 공개", MUTED), ("2020", "YOLOv5 (Ultralytics)", MUTED),
             ("2023", "YOLOv8", MUTED), ("2024", "YOLO11", YEL)]
    d.line([(200, 80), (200, 880)], fill=(60, 76, 110), width=8)
    for i, (y_, lb, col) in enumerate(items):
        k = prog(t, 0.2 + i * 0.35)
        y = 100 + i * 230
        last = i == len(items) - 1
        r = 34 if last else 22
        d.ellipse((200 - r, y + 40 - r, 200 + r, y + 40 + r), fill=rgba(col, k))
        d.text((270, y), y_, font=F(70 if last else 56, "b"), fill=rgba(col, k))
        d.text((270, y + 85), lb, font=F(48 if last else 40, "b" if last else "m"), fill=rgba(WHITE, k))


@vis("spec_compare")
def v_spec(c, d, t, T, a):
    st = a["stage"]
    for i, (nm, col) in enumerate([("YOLOv8n", ORANGE), ("YOLO11n", CYAN)]):
        x = 40 + i * 470
        rr(d, (x, 20, x + 410, 150), fill=rgba(PANEL), outline=col, r=24)
        text_c(d, x + 205, 50, nm, F(60, "b"), col)
    rows = [("파라미터 (백만)", 3.2, 2.6, 3.5, "{:.1f}M", 1), ("COCO mAP50-95", 37.3, 39.5, 45, "{:.1f}", 2)]
    for j, (lb, v8, v11, mx, fmt, need) in enumerate(rows):
        if st < need:
            continue
        k = prog(t, 0.2, 0.7) if st == need else 1.0
        y = 220 + j * 330
        text_c(d, VW / 2, y, lb, F(46, "b"), WHITE)
        for i, (v, col) in enumerate([(v8, ORANGE), (v11, CYAN)]):
            x = 40 + i * 470
            bar(d, x, y + 80, 410, 70, v / mx * k, col)
            text_c(d, x + 205, y + 165, fmt.format(v), F(64, "b"), col)
    if st >= 1:
        text_c(d, VW / 2, 900, "Ultralytics 공식 비교표 (COCO, 640px)", F(32, "m"), MUTED)
    if st == 0:
        k = prog(t, 0.3)
        text_c(d, VW / 2, 420, "같은 회사 · 같은 사용법", F(56, "b"), rgba(YEL, k))
        text_c(d, VW / 2, 520, "나노(n) = 가장 작고 빠른 크기", F(44, "m"), rgba(WHITE, k))
        n_par = A.meta["yolo_params"]
        text_c(d, VW / 2, 680, f"우리 모델 실측: {n_par:,} 파라미터", F(42, "m"), rgba(CYAN, prog(t, 0.9)))


@vis("vs_table")
def v_vstable(c, d, t, T, a):
    side = a["side"]
    cards = [("Haar Cascade", ORANGE, ["사람이 만든 사각형 특징", "흑백만 사용", "클래스마다 xml 1개", "회전 · 조명에 약함"]),
             ("YOLO11", CYAN, ["스스로 배운 특징", "컬러 사용", "한 모델로 여러 클래스", "회전 · 흐림에도 강함"])]
    for i, (nm, col, rows) in enumerate(cards):
        y = 20 + i * 480
        on = i == side
        al = 1.0 if on else 0.35
        rr(d, (30, y, VW - 30, y + 450), fill=rgba(PANEL, 0.95), outline=rgba(col, al), r=30, w=6 if on else 3)
        d.text((70, y + 30), nm, font=F(60, "b"), fill=rgba(col, al))
        for j, r_ in enumerate(rows):
            k = prog(t, 0.2 + j * 0.25) if on else 1.0
            d.text((90, y + 130 + j * 76), ("✓ " if i else "· ") + r_, font=F(46, "b" if on else "m"),
                   fill=rgba(WHITE, al * k))


@vis("cv5_error")
def v_cv5(c, d, t, T, a):
    lines = [("python", WHITE, "cmd"), (">>> import cv2", WHITE, "out"), (">>> cv2.__version__", WHITE, "out"),
             ("'5.0.0'", GREEN, "out"), (">>> cv2.CascadeClassifier", WHITE, "out"),
             ("AttributeError: module 'cv2'", RED, "out"), ("has no attribute 'CascadeClassifier'", RED, "out")]
    terminal(c, d, (10, 30, VW - 10, 620), lines, t, start=0.2, size=36, cps=30)
    k = prog(t, 2.6)
    rr(d, (40, 680, VW - 40, 930), fill=rgba(PANEL, k), outline=rgba(YEL, k), r=26)
    text_c(d, VW / 2, 705, "하르를 계속 쓰려면", F(44, "m"), rgba(WHITE, k))
    text_c(d, VW / 2, 785, "opencv-python<5", F(64, "mono"), rgba(YEL, k))
    text_c(d, VW / 2, 870, "(이 PC에서 직접 확인)", F(34, "m"), rgba(MUTED, k))


@vis("code_card")
def v_code(c, d, t, T, a):
    rows = [("model = YOLO('yolo11n.pt')", WHITE, "불러오기"), ("model.train(data='data.yaml')", CYAN, "학습"),
            ("model.val()", GREEN, "검증"), ("model.export(format='ncnn')", YEL, "변환")]
    for i, (code, col, lb) in enumerate(rows):
        k = prog(t, 0.2 + i * 0.4)
        y = 40 + i * 225
        rr(d, (30 + (1 - k) * 60, y, VW - 30, y + 190), fill=rgba(PANEL, k), outline=rgba(col, k), r=24)
        d.text((70 + (1 - k) * 60, y + 22), lb, font=F(40, "b"), fill=rgba(col, k))
        d.text((70 + (1 - k) * 60, y + 95), code, font=F(40, "mono"), fill=rgba(WHITE, k))


# ---------------- EP4
@vis("setup")
def v_setup(c, d, t, T, a):
    put(c, A.ill["labeling"], (160, 0, VW - 160, 500), mode="cover", r=30)
    lines = [("pip install --prefer-binary \\", YEL, "cmd"), ("    -r requirements.txt", YEL, "out"),
             ("Successfully installed ultralytics ...", GREEN, "out"), ("python run_pipeline.py --demo", YEL, "cmd")]
    terminal(c, d, (10, 540, VW - 10, 950), lines, t, start=0.2, size=34, cps=55)


@vis("label_tool")
def v_label(c, d, t, T, a):
    fr = A.label
    if a["part"] == 0:
        im = fr[0]
    else:
        im = fr[min(len(fr) - 1, int(t / T * len(fr)))]
    put(c, im, (0, 60, VW, 60 + VW * im.height / im.width), r=18, border=CYAN, bw=4)
    text_c(d, VW / 2, 830, "scripts/02_label_tool.py (실제 화면)", F(36, "m"), MUTED)
    if a["part"] == 1:
        keys = ["숫자 키 = 클래스", "드래그 = 박스", "D = 저장"]
        chip(d, VW / 2, 890, keys[min(2, int(t / T * 3))], F(40, "b"))


@vis("label_txt")
def v_label_txt(c, d, t, T, a):
    put(c, A.label[-1], (180, 0, VW - 180, 450), r=16, border=CYAN, bw=3)
    lines = [("cat labels/demo_0011.txt", YEL, "cmd")] + [(l, WHITE, "out") for l in
                                                          A.meta["label_tool"]["saved_txt"].strip().split("\n")]
    terminal(c, d, (10, 500, VW - 10, 900), lines, t, start=0.2, size=38, cps=45)


@vis("label_fmt")
def v_label_fmt(c, d, t, T, a):
    toks = A.meta["label_tool"]["saved_txt"].split("\n")[0].split()
    labels = [("클래스", YEL), ("중심 x", CYAN), ("중심 y", CYAN), ("너비", GREEN), ("높이", GREEN)]
    x = 30
    for i, (tok, (lb, col)) in enumerate(zip(toks, labels)):
        k = prog(t, 0.2 + i * 0.3)
        w = 120 if i == 0 else 195
        rr(d, (x, 80, x + w - 12, 200), fill=rgba(PANEL, k), outline=rgba(col, k), r=18)
        text_c(d, x + (w - 12) / 2, 108, tok if i == 0 else tok[:6], F(48 if i == 0 else 40, "mono"), rgba(WHITE, k))
        text_c(d, x + (w - 12) / 2, 220, lb, F(36, "b"), rgba(col, k))
        x += w
    k = prog(t, 1.7)
    im = A.label[-1]
    placed = put(c, im, (160, 330, VW - 160, 330 + (VW - 320) * im.height / im.width), r=16, alpha=k)
    cls, xc, yc, bw, bh = int(toks[0]), *map(float, toks[1:])
    if placed:
        px, py, pw, ph = placed
        cx, cy = px + xc * pw, py + yc * ph
        d.ellipse((cx - 12, cy - 12, cx + 12, cy + 12), fill=rgba(YEL, k))
        d.rectangle((cx - bw * pw / 2, cy - bh * ph / 2, cx + bw * pw / 2, cy + bh * ph / 2), outline=rgba(YEL, k), width=5)
    text_c(d, VW / 2, 860, "픽셀 ÷ 이미지 크기 = 0~1", F(46, "b"), rgba(YEL, prog(t, 2.1)))


@vis("check_out")
def v_check(c, d, t, T, a):
    lines = [("python scripts/03_check_labels.py", YEL, "cmd"), ("", WHITE, "out"),
             ("클래스    박스수   분포", MUTED, "out"),
             ("0:car       82   █████", ORANGE, "out"), ("1:green     77   █████", GREEN, "out"),
             ("2:oo       100   ██████", CYAN, "out"), ("3:red       94   ██████", RED, "out"),
             ("4:xx        89   ██████", YEL, "out"), ("", WHITE, "out"), ("ERROR 0 건 | WARN 0 건", GREEN, "out")]
    terminal(c, d, (10, 40, VW - 10, 900), lines, t, start=0.2, size=40, cps=55)


@vis("split_anim")
def v_split(c, d, t, T, a):
    buckets = [("train 70%", "169장", CYAN, 28), ("val 20%", "47장", YEL, 8), ("test 10%", "24장", RED, 4)]
    for i, (nm, n, col, _) in enumerate(buckets):
        x = 20 + i * 315
        rr(d, (x, 560, x + 295, 940), fill=rgba(PANEL), outline=col, r=24, w=5)
        text_c(d, x + 147, 580, nm, F(44, "b"), col)
        text_c(d, x + 147, 640, n, F(40, "m"), WHITE)
    order = [0] * 28 + [1] * 8 + [2] * 4
    perm = np.random.default_rng(3).permutation(40)
    cnt = [0, 0, 0]
    for nidx in range(40):
        b = order[nidx]
        slot = cnt[b]
        cnt[b] += 1
        i = perm[nidx]
        r_, cc = divmod(i, 8)
        sx, sy = 20 + cc * 118, 20 + r_ * 100
        ex = 20 + b * 315 + 20 + (slot % 6) * 44
        ey = 710 + (slot // 6) * 40
        k = ease((t - 0.3 - nidx * 0.035) / 0.6)
        x, y = lerp(sx, ex, k), lerp(sy, ey, k)
        s = lerp(110, 40, k)
        put(c, A.thumbs[i], (x, y, x + s, y + s * 0.75), r=6, mode="cover")


@vis("train_cmd")
def v_train_cmd(c, d, t, T, a):
    put(c, A.ill["training"], (130, 0, VW - 130, 600), mode="cover", r=30)
    lines = [("python scripts/05_train.py", YEL, "cmd"), ("모델: yolo11n.pt | epochs 15 | imgsz 320", MUTED, "out")]
    terminal(c, d, (10, 650, VW - 10, 930), lines, t, start=0.2, size=34, cps=45)


@vis("curves")
def v_curves(c, d, t, T, a):
    rows = A.results
    N = len(rows)
    ep = clamp(t / (T * 0.85)) * (N - 1)

    def chart(y0, keys, title, vmax):
        rr(d, (10, y0, VW - 10, y0 + 430), fill=rgba(PANEL), outline=(60, 76, 110), r=24, w=3)
        d.text((40, y0 + 20), title, font=F(44, "b"), fill=WHITE)
        gx1, gy1, gx2, gy2 = 60, y0 + 100, VW - 60, y0 + 400
        for key, col, lb, li in keys:
            pts = []
            for i in range(N):
                if i > ep:
                    break
                pts.append((gx1 + (gx2 - gx1) * i / (N - 1), gy2 - (gy2 - gy1) * rows[i][key] / vmax))
            if int(ep) + 1 < N:
                fr = ep - int(ep)
                v = lerp(rows[int(ep)][key], rows[int(ep) + 1][key], fr)
                pts.append((gx1 + (gx2 - gx1) * ep / (N - 1), gy2 - (gy2 - gy1) * v / vmax))
            if len(pts) > 1:
                d.line(pts, fill=col, width=8, joint="curve")
            d.ellipse((pts[-1][0] - 10, pts[-1][1] - 10, pts[-1][0] + 10, pts[-1][1] + 10), fill=col)
            d.text((VW - 320, y0 + 22 + li * 44), "● " + lb, font=F(34, "b"), fill=col)

    chart(20, [("metrics/mAP50(B)", GREEN, "mAP50 ↑", 0), ("metrics/mAP50-95(B)", CYAN, "mAP50-95 ↑", 1)], "점수", 1.0)
    vmax = max(r["train/cls_loss"] for r in rows)
    chart(480, [("train/cls_loss", RED, "학습 손실 ↓", 0), ("val/cls_loss", ORANGE, "검증 손실 ↓", 1)], "손실", vmax)
    text_c(d, VW / 2, 925, f"epoch {int(ep) + 1} / {N}", F(44, "b"), YEL)


@vis("epoch_done")
def v_epoch_done(c, d, t, T, a):
    k = ease(t / 1.0)
    N = len(A.results)
    text_c(d, VW / 2, 80, f"{int(1 + (N - 1) * k)} / {N}", F(200, "b"), YEL, stroke=6)
    text_c(d, VW / 2, 330, "epoch", F(60, "m"), WHITE)
    bar(d, 80, 470, 800, 70, k, GREEN)
    kk = prog(t, 1.0)
    text_c(d, VW / 2, 600, "1.9분", F(150, "b"), rgba(WHITE, kk), stroke=5)
    text_c(d, VW / 2, 800, "M2 Max CPU · 가상 데이터 240장", F(40, "m"), rgba(MUTED, kk))


@vis("best_pt")
def v_best(c, d, t, T, a):
    k = back(t / 0.45)
    s = clamp(k, 0.2, 1.1)
    cx, cy = VW / 2, 300
    rr(d, (cx - 190 * s, cy - 230 * s, cx + 190 * s, cy + 230 * s), fill=PANEL, outline=YEL, r=30, w=6)
    text_c(d, cx, cy - 60 * s, "best.pt", F(int(80 * s), "b"), YEL)
    text_c(d, cx, cy + 50 * s, "5.3 MB", F(int(44 * s), "m"), MUTED)
    o = A.val["overall"]
    for i, (lb, v) in enumerate([("mAP50", o["map50"]), ("mAP50-95", o["map50_95"])]):
        kk = prog(t, 0.6 + i * 0.3)
        y = 620 + i * 140
        d.text((120, y), lb, font=F(56, "b"), fill=rgba(WHITE, kk))
        d.text((620, y), f"{v:.3f}", font=F(64, "b"), fill=rgba(GREEN, kk))
    text_c(d, VW / 2, 900, "models/best.pt 로 자동 복사", F(38, "m"), MUTED)


@vis("four_cmds")
def v_four(c, d, t, T, a):
    cmds = [("02_label_tool.py", "라벨링", YEL), ("03_check_labels.py", "점검", GREEN),
            ("04_split_dataset.py", "분할", CYAN), ("05_train.py", "학습", ORANGE)]
    for i, (cmd, lb, col) in enumerate(cmds):
        k = prog(t, 0.2 + i * 0.35)
        y = 30 + i * 230
        rr(d, (30, y, VW - 30, y + 200), fill=rgba(PANEL, k), outline=rgba(col, k), r=26)
        d.ellipse((60, y + 50, 160, y + 150), fill=rgba(col, k))
        text_c(d, 110, y + 68, str(i + 1), F(56, "b"), rgba(DARK, k))
        d.text((200, y + 30), lb, font=F(56, "b"), fill=rgba(col, k))
        d.text((200, y + 115), "python scripts/" + cmd, font=F(32, "mono"), fill=rgba(WHITE, k))


# ---------------- EP5
@vis("iou")
def v_iou(c, d, t, T, a):
    gx1, gy1, gx2, gy2 = 200, 180, 620, 600
    if a["phase"] == 0:
        off = lerp(330, 170, ease(t / T))
    else:
        off = lerp(170, 50, ease(t / (T * 0.7)))
    px1, py1, px2, py2 = gx1 + off, gy1 + off * 0.6, gx2 + off, gy2 + off * 0.6
    ix1, iy1, ix2, iy2 = max(gx1, px1), max(gy1, py1), min(gx2, px2), min(gy2, py2)
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    area = (gx2 - gx1) * (gy2 - gy1)
    iou = inter / (2 * area - inter)
    if inter > 0:
        d.rectangle((ix1, iy1, ix2, iy2), fill=(255, 214, 10, 110))
    d.rectangle((gx1, gy1, gx2, gy2), outline=GREEN, width=10)
    d.rectangle((px1, py1, px2, py2), outline=RED, width=10)
    d.text((gx1, gy1 - 70), "정답", font=F(50, "b"), fill=GREEN)
    d.text((px2 - 150, py2 + 10), "예측", font=F(50, "b"), fill=RED)
    ok = iou >= 0.5
    text_c(d, VW / 2, 10, f"IoU {iou:.2f}", F(110, "b"), GREEN if ok else YEL, stroke=6)
    if a["phase"] == 1:
        rr(d, (130, 860, VW - 130, 950), fill=rgba(PANEL), outline=GREEN if ok else RED, r=24)
        text_c(d, VW / 2, 872, "≥ 0.5  정답 (TP)" if ok else "< 0.5  틀림", F(50, "b"), GREEN if ok else RED)


@vis("pr_icons")
def v_pr(c, d, t, T, a):
    p = a["mode"] == "p"
    title = "모델이 '찾았다'고 한 것 5개" if p else "실제로 있는 표지판 5개"
    text_c(d, VW / 2, 20, title, F(48, "b"), WHITE)
    marks = [True, True, True, True, False]
    for i, ok in enumerate(marks):
        k = back((t - 0.2 - i * 0.2) / 0.35)
        if t < 0.2 + i * 0.2:
            continue
        x = 40 + i * 182
        s = clamp(k, 0, 1.1)
        rr(d, (x + 80 - 75 * s, 220 - 75 * s, x + 80 + 75 * s, 220 + 75 * s), fill=PANEL,
           outline=(GREEN if ok else RED), r=20, w=6)
        sym = ("✓" if ok else "×") if p else ("찾음" if ok else "놓침")
        text_c(d, x + 80, 185 if p else 198, sym, F(64 if p else 36, "b"), GREEN if ok else RED)
    k = prog(t, 1.4)
    text_c(d, VW / 2, 400, "4 ÷ 5 = 80%", F(130, "b"), rgba(YEL, k), stroke=5)
    text_c(d, VW / 2, 600, ("정밀도 = 맞은 수 ÷ 찾은 수" if p else "재현율 = 찾은 수 ÷ 실제 수"), F(52, "b"),
           rgba(CYAN, k))
    text_c(d, VW / 2, 700, ("낮으면 → 없는 신호에 멈춤" if p else "낮으면 → 빨간불을 놓침"), F(44, "m"), rgba(WHITE, k))
    text_c(d, VW / 2, 900, "(이해를 위한 예시)", F(34, "m"), MUTED)


@vis("pr_curve")
def v_prc(c, d, t, T, a):
    put(c, A.pr, (0, 40, VW, 40 + VW * A.pr.height / A.pr.width), r=20, zoom=1.0 + 0.05 * t / T)
    k = prog(t, 0.8)
    chip(d, VW / 2, 780, f"mAP50 = {A.val['overall']['map50']:.3f}", F(56, "b"), alpha=k)
    text_c(d, VW / 2, 890, "실제 학습 결과 BoxPR_curve.png", F(34, "m"), MUTED)


@vis("pass_stamp")
def v_pass(c, d, t, T, a):
    put(c, A.ill["exam"], (200, 0, VW - 200, 440), mode="cover", r=30)
    for i, ch in enumerate(A.val["checks"][:4]):
        k = prog(t, 0.2 + i * 0.25)
        y = 465 + i * 72
        d.text((80, y), ("✓ " if ch["pass"] else "× ") + ch["metric"], font=F(46, "b"), fill=rgba(GREEN, k))
        d.text((560, y), f"{ch['value']:.3f} ≥ {ch['threshold']}", font=F(42, "m"), fill=rgba(WHITE, k))
    k = back((t - 1.4) / 0.4)
    if t > 1.4:
        s = clamp(k, 0.3, 1.15)
        rr(d, (VW / 2 - 230 * s, 870 - 70 * s, VW / 2 + 230 * s, 870 + 70 * s), fill=rgba(DARK, 0.9), outline=GREEN,
           r=26, w=10)
        text_c(d, VW / 2, 870 - 62 * s, "PASS", F(int(110 * s), "b"), GREEN)


def stream_frame(c, d, i):
    im = A.stream[i]
    put(c, im, (0, 60, VW, 60 + VW * 0.75), r=20, border=CYAN, bw=4)
    row = A.meta["stream"][i]
    d.text((30, 0), f"frame {i:02d}", font=F(44, "mono"), fill=WHITE)
    d.text((VW - 300, 0), f"{row['ms']:.1f} ms", font=F(44, "mono"), fill=GREEN)


@vis("stream")
def v_stream(c, d, t, T, a):
    i = min(len(A.stream) - 1, a["from"] + int(t * 8))
    stream_frame(c, d, i)
    text_c(d, VW / 2, 820, "실제 Raspbot 카메라 연속 프레임 · YOLO11 추론", F(36, "m"), MUTED)


@vis("flicker")
def v_flicker(c, d, t, T, a):
    text_c(d, VW / 2, 20, "프레임별 감지 (예시)", F(46, "b"), WHITE)
    seq = [0] * 8 + [1] + [0] * 11
    for i, v in enumerate(seq):
        k = prog(t, i * 0.05, 0.2)
        x = 40 + i * 44
        col = RED if v else (60, 76, 110)
        rr(d, (x, 200 - v * 80, x + 34, 300), fill=rgba(col, k), r=8, w=0)
    k = prog(t, 1.2)
    text_c(d, VW / 2, 360, "오탐 1프레임에 바로 정지?", F(60, "b"), rgba(RED, k))
    put(c, A.ill["redlight"], (230, 470, VW - 230, VH - 20), mode="cover", r=30, alpha=prog(t, 1.6))


@vis("confirm")
def v_confirm(c, d, t, T, a):
    for j in range(3):
        k = back((t - j * 0.6) / 0.35)
        if t < j * 0.6:
            continue
        y = 20 + j * 300
        put(c, A.stream[j], (40, y, 420, y + 285), r=16, border=GREEN, bw=4)
        text_c(d, 690, y + 80, f"{j + 1} / 3", F(int(110 * clamp(k, 0.3, 1.1)), "b"), YEL if j < 2 else GREEN)
        d.text((520, y + 210), f"frame {j} · xx 감지", font=F(34, "m"), fill=WHITE)


@vis("fire_timeline")
def v_fire(c, d, t, T, a):
    rows = A.meta["stream"]
    fired = [r["i"] for r in rows if r["fired"]]
    k = back(t / 0.4)
    stream_frame(c, d, fired[0])
    if t < 2.0:
        rr(d, (200, 260, VW - 200, 420), fill=rgba(GREEN, 0.9), r=30, w=0)
        text_c(d, VW / 2, 285, "EVENT: xx", F(int(90 * clamp(k, 0.3, 1.1)), "b"), DARK)
    n = len(rows)
    x0, w = 30, (VW - 60) / n
    for r in rows:
        col = GREEN if r["present"] else (60, 76, 110)
        d.rectangle((x0 + r["i"] * w, 800, x0 + (r["i"] + 1) * w - 2, 860), fill=col)
    for i in fired:
        d.polygon([(x0 + (i + 0.5) * w, 770), (x0 + (i + 0.5) * w - 16, 740), (x0 + (i + 0.5) * w + 16, 740)], fill=YEL)
    pres = sum(r["present"] for r in rows)
    text_c(d, VW / 2, 880, f"{pres}프레임 연속 감지 → 이벤트 {len(fired)}번", F(42, "b"), YEL)


@vis("deploy")
def v_deploy(c, d, t, T, a):
    put(c, A.ill["raspi"], (180, 0, VW - 180, 520), mode="cover", r=30)
    lines = [("python scripts/09_export.py", YEL, "cmd"), ("ncnn: models/best_ncnn_model/", GREEN, "out"),
             ("scp -r models/best_ncnn_model \\", YEL, "cmd"), ("  pi@raspberrypi.local:~/source/models/yolo/", YEL, "out")]
    terminal(c, d, (10, 560, VW - 10, 950), lines, t, start=0.2, size=31, cps=60)


# ------------------------------------------------------------------ 프레임 합성
def make_bg(theme):
    top, bot = theme
    arr = np.zeros((H, W, 3), np.float32)
    g = np.linspace(0, 1, H)[:, None]
    for i in range(3):
        arr[:, :, i] = top[i] * (1 - g) + bot[i] * g
    yy, xx = np.mgrid[0:H, 0:W]
    vig = 1 - 0.35 * (((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2) * 2
    arr *= vig[:, :, None]
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for x in range(0, W, 90):     # 은은한 격자
        od.line([(x, 0), (x, H)], fill=(255, 255, 255, 10), width=1)
    for y in range(0, H, 90):
        od.line([(0, y), (W, y)], fill=(255, 255, 255, 10), width=1)
    img = img.convert("RGBA")
    img.alpha_composite(ov)
    return img.convert("RGB")


def header(img, ep, idx, n_ep):
    d = ImageDraw.Draw(img, "RGBA")
    text_c(d, W / 2, 48, f"라즈봇 AI 실습 · YOLO11 시리즈 {idx}/{n_ep}", F(30, "m"), (200, 210, 225))
    rr(d, (60, 100, W - 60, 330), fill=(10, 16, 32, 200), outline=CYAN, r=30, w=5)
    for i, ln in enumerate(ep["title"]):
        text_c(d, W / 2, 125 + i * 92, ln, F(74, "b"), WHITE)


def caption_layer(cap):
    layer = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    draw_rich_c(d, W / 2, 20, cap, F(70, "b"), stroke=7, maxw=W - 120, lh=96)
    return layer


def build_timeline(ep, use_hf):
    beats = []
    t = HEAD
    for i, b in enumerate(ep["beats"]):
        gidx = sum(len(e["beats"]) for e in EPISODES[:EPISODES.index(ep)]) + i
        mp3 = SH / "audio" / f"{gidx:02d}.mp3"
        wav = SH / "wav" / f"{gidx:02d}.wav"
        wav.parent.mkdir(parents=True, exist_ok=True)
        if mp3.exists() and use_hf:
            src = mp3
        else:
            src = SH / "wav" / f"{gidx:02d}_say.aiff"
            subprocess.run(["say", "-v", "Yuna", "-r", "190", "-o", str(src), b[2]], check=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af", f"atempo={TEMPO}", "-ar", "44100", "-ac", "1",
                        "-sample_fmt", "s16", str(wav)], check=True)
        with wave.open(str(wav)) as w:
            dur = w.getnframes() / w.getframerate()
        beats.append({"start": t, "dur": dur + GAP, "audio": wav, "speech_dur": dur})
        t += dur + GAP
    return beats, t + TAIL


def mix(beats, total, out):
    sr = 44100
    buf = np.zeros(int((total + 0.5) * sr), np.int32)
    for b in beats:
        with wave.open(str(b["audio"])) as w:
            data = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.int32)
        s = int(b["start"] * sr)
        buf[s:s + len(data)] += data[: len(buf) - s]
    buf = np.clip(buf, -32768, 32767).astype(np.int16)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(buf.tobytes())


def render_frame(ep, base, beats, total, caps, t):
    img = base.copy()
    bi = max([i for i, b in enumerate(beats) if b["start"] <= t] or [0])
    b = beats[bi]
    beat = ep["beats"][bi]
    bt, T = t - b["start"], b["dur"]
    d = ImageDraw.Draw(img, "RGBA")
    # 태그 (바뀔 때 튀어나옴)
    new_tag = bi == 0 or ep["beats"][bi - 1][0] != beat[0]
    k = back(bt / 0.3) if new_tag else 1.0
    f = F(int(44 * clamp(k, 0.6, 1.1)), "b")
    chip(d, W / 2, 360, beat[0], f)
    # 비주얼
    layer = Image.new("RGBA", (VW, VH), (0, 0, 0, 0))
    V[beat[3]](layer, ImageDraw.Draw(layer, "RGBA"), bt, T, beat[4])
    same_vis = bi > 0 and ep["beats"][bi - 1][3] == beat[3] and beat[3] in ("grid", "label_tool", "stream", "iou",
                                                                            "spec_compare", "vs_table", "duel")
    e = 1.0 if same_vis else ease(bt / 0.35)
    if e < 1:
        s = 0.94 + 0.06 * e
        layer = layer.resize((int(VW * s), int(VH * s)), Image.BILINEAR)
        alpha = layer.getchannel("A").point(lambda v: int(v * e))
        layer.putalpha(alpha)
    img.paste(layer, (VX + (VW - layer.width) // 2, VY + (VH - layer.height) // 2 + int((1 - e) * 40)), layer)
    # 자막
    cap = caps[bi]
    ck = back(bt / 0.25)
    if ck < 0.999:
        s = clamp(0.85 + 0.15 * ck, 0.85, 1.05)
        cap = cap.resize((int(W * s), int(cap.height * s)), Image.BILINEAR)
    img.paste(cap, ((W - cap.width) // 2, 1500), cap)
    # 진행 바
    d = ImageDraw.Draw(img)
    d.rectangle((0, H - 16, W, H), fill=(40, 48, 70))
    d.rectangle((0, H - 16, int(W * t / total), H), fill=YEL)
    return img.convert("RGB")


def srt(beats, ep, path):
    def ts(s):
        ms = int(s * 1000)
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    out = []
    for i, (b, beat) in enumerate(zip(beats, ep["beats"])):
        out += [str(i + 1), f"{ts(b['start'])} --> {ts(b['start'] + b['dur'] - 0.05)}", beat[1].replace("**", ""), ""]
    path.write_text("\n".join(out), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ep", nargs="*", help="ep1 ~ ep5 (기본: 전부)")
    ap.add_argument("--out", default=str(ROOT / "docs/video/shorts"))
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--no-hf", action="store_true", help="Higgsfield 음성 대신 macOS say 사용")
    args = ap.parse_args()
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg 필요")
    load_assets()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    eps = [e for e in EPISODES if not args.ep or e["id"] in args.ep]
    for n, ep in enumerate(EPISODES, 1):
        if ep not in eps:
            continue
        base = make_bg(ep["theme"])
        header(base, ep, n, len(EPISODES))
        caps = [caption_layer(b[1]) for b in ep["beats"]]
        beats, total = build_timeline(ep, not args.no_hf)
        print(f"[{ep['id']}] {len(beats)} beats, {total:.1f}s")
        if args.preview:
            pd = SH / "preview"
            pd.mkdir(exist_ok=True)
            for i, b in enumerate(beats):
                render_frame(ep, base, beats, total, caps, b["start"] + b["dur"] * 0.75).save(pd / f"{ep['id']}_{i:02d}.png")
            continue
        wav = SH / f"{ep['id']}_narration.wav"
        mix(beats, total, wav)
        mp4 = out / f"{n}_{ep['id']}_{ep['title'][0].replace(' ', '_')}.mp4"
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
               "-i", "-", "-i", str(wav), "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "160k", "-af", "loudnorm=I=-16:TP=-1.5", "-movflags", "+faststart",
               "-t", f"{total:.2f}", str(mp4)]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        nf = int(total * FPS)
        for fi in range(nf):
            p.stdin.write(render_frame(ep, base, beats, total, caps, fi / FPS).tobytes())
            if fi % 150 == 0:
                print(f"  {fi}/{nf}", end="\r")
        p.stdin.close()
        p.wait()
        sub_dir = out.parent / "자막"
        sub_dir.mkdir(parents=True, exist_ok=True)
        srt(beats, ep, sub_dir / mp4.with_suffix(".srt").name)
        print(f"  → {mp4.name} ({mp4.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
