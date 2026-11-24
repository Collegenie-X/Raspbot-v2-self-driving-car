"""
YOLO11 학습 튜토리얼 영상 생성기 (나레이션 + 자막 + 애니메이션, 1280x720 MP4)

라벨링 → 분할 → 학습 → 검증 → 테스트 → 추론 → 배포 9단계를 장면별로 설명하는 학습 영상을 만듭니다.
화면에 나오는 그래프·표·이미지는 데모 실행 결과(demo/)의 실제 데이터를 사용합니다.

필요한 것
  - macOS `say` 명령 + 한국어 음성 'Yuna'  (없으면 무음 영상 + 자막)
  - ffmpeg (brew install ffmpeg)
  - Pillow, OpenCV, numpy (requirements.txt 에 포함)
  - 데모 결과: 먼저 `python run_pipeline.py --demo` 실행

사용 예:
  python tools/make_tutorial_video.py
  python tools/make_tutorial_video.py --out docs/video/YOLO11_학습_튜토리얼.mp4 --rate 185
  python tools/make_tutorial_video.py --preview 5      # 5번 장면 미리보기 PNG 만 저장
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import subprocess
import sys
import unicodedata
import wave
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "demo"
sys.path.insert(0, str(ROOT / "tools"))
from make_demo_dataset import draw_obj  # noqa: E402  (클래스 아이콘 그리기 재사용)

W, H, FPS = 1280, 720, 24
GAP = 0.35            # 문장 사이 쉼(초)
TAIL = 0.9            # 장면 끝 여유(초)

# ------------------------------------------------------------------ 색상 / 폰트
BG = (15, 23, 42)
PANEL = (30, 41, 59)
PANEL2 = (51, 65, 85)
TXT = (226, 232, 240)
MUTED = (148, 163, 184)
GREEN = (74, 222, 128)
RED = (248, 113, 113)
YELLOW = (250, 204, 21)
BLUE = (96, 165, 250)
PURPLE = (192, 132, 252)
ORANGE = (251, 146, 60)
CYAN = (34, 211, 238)
STEP_COLORS = [None, CYAN, BLUE, PURPLE, PURPLE, ORANGE, GREEN, GREEN, YELLOW, RED]
CLASS_COLORS = {"car": (255, 112, 31), "green": (74, 222, 128), "oo": (96, 165, 250),
                "red": (248, 113, 113), "xx": (250, 204, 21)}
CLASSES = ["car", "green", "oo", "red", "xx"]

SD = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
MENLO = "/System/Library/Fonts/Menlo.ttc"
_fc: dict = {}


def font(size: int, weight: str = "r") -> ImageFont.FreeTypeFont:
    idx = {"r": 0, "m": 2, "s": 4, "b": 6}[weight]
    key = ("sd", size, idx)
    if key not in _fc:
        _fc[key] = ImageFont.truetype(SD, size, index=idx)
    return _fc[key]


def mono(size: int, korean: bool = False) -> ImageFont.FreeTypeFont:
    key = ("mono", size, korean)
    if key not in _fc:
        _fc[key] = ImageFont.truetype(SD if korean else MENLO, size, index=0)
    return _fc[key]


# ------------------------------------------------------------------ 애니메이션 유틸
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def prog(t, start, dur=0.6):
    return ease((t - start) / dur) if dur > 0 else float(t >= start)


def lerp(a, b, k):
    return a + (b - a) * k


def mix(c1, c2, k):
    return tuple(int(lerp(a, b, k)) for a, b in zip(c1, c2))


def fade(color, a, bg=BG):
    return mix(bg, color, a)


# ------------------------------------------------------------------ 그리기 유틸
def rrect(d, box, fill=None, outline=None, r=14, w=2):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=w)


def text_c(d, cx, y, s, f, fill):
    d.text((cx - d.textlength(s, font=f) / 2, y), s, font=f, fill=fill)


def wrap(s, f, maxw):
    lines, cur = [], ""
    for word in s.split(" "):
        cand = (cur + " " + word).strip()
        if ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(cand, font=f) <= maxw or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


SYMBOL_MAP = {"✅": ("✓", GREEN), "❌": ("✗", RED), "⚠": ("!", YELLOW)}


def draw_mono(d, x, y, s, size=17, fill=TXT, alpha=1.0, panel=PANEL):
    """터미널 스타일 고정폭 텍스트 (영문=Menlo, 한글=SD 고딕 2칸)."""
    cell = mono(size).getlength("M")
    for ch in s:
        col = fill
        if ch in SYMBOL_MAP:
            ch, col = SYMBOL_MAP[ch]
        wide = unicodedata.east_asian_width(ch) in ("W", "F")
        if wide:
            f = mono(int(size * 1.16), korean=True)
            gw = f.getlength(ch)
            d.text((x + (2 * cell - gw) / 2, y - size * 0.1), ch, font=f, fill=fade(col, alpha, panel))
        else:
            d.text((x, y), ch, font=mono(size), fill=fade(col, alpha, panel))
        x += cell * (2 if wide else 1)
    return x


def terminal(d, box, lines, t, start=0.0, cps=38, size=17, title="Terminal", line_gap=1.45):
    """lines: [(text, color, kind)] kind: 'cmd'(타이핑) | 'out'(한 줄씩). 반환: 종료 시각."""
    x1, y1, x2, y2 = box
    rrect(d, box, fill=PANEL, outline=PANEL2)
    d.rounded_rectangle((x1, y1, x2, y1 + 30), radius=14, fill=PANEL2)
    d.rectangle((x1, y1 + 16, x2, y1 + 30), fill=PANEL2)
    for i, c in enumerate([(248, 113, 113), (250, 204, 21), (74, 222, 128)]):
        d.ellipse((x1 + 14 + i * 20, y1 + 9, x1 + 26 + i * 20, y1 + 21), fill=c)
    text_c(d, (x1 + x2) / 2, y1 + 6, title, font(15, "m"), MUTED)
    cy, now = y1 + 44, start
    lh = size * line_gap
    for text, color, kind in lines:
        if cy > y2 - lh:
            break
        if kind == "cmd":
            n = int((t - now) * cps)
            if n <= 0:
                break
            shown = text[:n]
            xe = draw_mono(d, x1 + 16, cy, "$ ", size, GREEN)
            xe = draw_mono(d, xe, cy, shown, size, color)
            if n < len(text) and int(t * 3) % 2 == 0:
                d.rectangle((xe, cy + 2, xe + 9, cy + size + 2), fill=TXT)
            now += len(text) / cps + 0.25
            if n < len(text):
                break
        else:
            if t < now:
                break
            draw_mono(d, x1 + 16, cy, text, size, color, alpha=prog(t, now, 0.25))
            now += 0.09
        cy += lh
    return now


def paste_fit(img, src, box, alpha=1.0, border=None, radius=10):
    x1, y1, x2, y2 = box
    bw, bh = x2 - x1, y2 - y1
    s = min(bw / src.width, bh / src.height)
    im = src.resize((max(1, int(src.width * s)), max(1, int(src.height * s))), Image.LANCZOS)
    px, py = int(x1 + (bw - im.width) / 2), int(y1 + (bh - im.height) / 2)
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=radius,
                                           fill=int(255 * alpha))
    img.paste(im, (px, py), mask)
    if border and alpha > 0.05:
        ImageDraw.Draw(img).rounded_rectangle((px - 2, py - 2, px + im.width + 1, py + im.height + 1),
                                              radius=radius, outline=fade(border, alpha), width=2)
    return px, py, im.width, im.height


def arrow(d, p1, p2, color, w=4, head=12):
    d.line([p1, p2], fill=color, width=w)
    ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    for s in (-1, 1):
        a = ang + math.pi + s * 0.45
        d.line([p2, (p2[0] + head * math.cos(a), p2[1] + head * math.sin(a))], fill=color, width=w)


def cursor(d, x, y, pressed=False):
    pts = [(x, y), (x, y + 24), (x + 6, y + 18), (x + 11, y + 28), (x + 15, y + 26), (x + 10, y + 16),
           (x + 18, y + 16)]
    d.polygon(pts, fill=(255, 255, 255), outline=(0, 0, 0))
    if pressed:
        d.ellipse((x - 9, y - 9, x + 9, y + 9), outline=YELLOW, width=2)


def bullet_list(d, x, y, items, t, starts, size=26, gap=48, color=TXT, icon="•", icon_color=None):
    for i, (s, st) in enumerate(zip(items, starts)):
        a = prog(t, st, 0.5)
        if a <= 0:
            continue
        dx = (1 - a) * 30
        d.text((x + dx, y + i * gap), icon, font=font(size, "b"), fill=fade(icon_color or color, a))
        d.text((x + 34 + dx, y + i * gap), s, font=font(size, "m"), fill=fade(color, a))


# ------------------------------------------------------------------ 데이터 로드 (데모 결과)
def load_img(p: Path) -> Image.Image | None:
    return Image.open(p).convert("RGB") if p.exists() else None


def load_results_csv():
    p = DEMO / "runs/train/demo_yolo11/results.csv"
    rows = []
    if p.exists():
        with open(p) as f:
            for r in csv.DictReader(f):
                r = {k.strip(): float(v) for k, v in r.items()}
                rows.append(r)
    return rows


def load_json(p: Path, default):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def class_icon(cls_id: int, size=150) -> Image.Image:
    canvas = np.full((size, size, 3), (59, 41, 30), np.uint8)  # BGR(PANEL)
    s = int(size * (0.42 if cls_id == 0 else 0.6))
    x = (size - int(s * (1.6 if cls_id == 0 else 1))) // 2
    y = (size - s) // 2 + (s // 8 if cls_id == 0 else 0)
    draw_obj(canvas, cls_id, x, y, s)
    return Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))


# ------------------------------------------------------------------ 장면 정의
# 각 문장: (자막, 읽기용 텍스트 또는 None)  — 영어/기호는 읽기용 발음을 따로 적음
def S(caption, speech=None):
    return (caption, speech or caption)


SCENES = []


def scene(chip, title, step=None, chapter=None):
    def deco(fn):
        SCENES.append({"chip": chip, "title": title, "step": step, "draw": fn,
                       "chapter": chapter or title, "lines": fn.lines})
        return fn
    return deco


def narr(*lines):
    def deco(fn):
        fn.lines = list(lines)
        return fn
    return deco


class Assets:
    pass


A = Assets()


# ---------------- 0. 타이틀
@scene("INTRO", "", chapter="시작")
@narr(S("안녕하세요. 이 영상에서는 YOLO11로 우리만의 객체 인식 모델을 만드는 방법을 단계별로 배웁니다.",
        "안녕하세요. 이 영상에서는 욜로 일레븐으로 우리만의 객체 인식 모델을 만드는 방법을 단계별로 배웁니다."),
      S("목표는 라즈베리파이 자율주행 로봇이 신호등, 표지판, 앞 차량을 알아보게 만드는 것입니다."))
def sc_title(img, d, t, m, T):
    a = prog(t, 0.2, 0.9)
    text_c(d, W / 2, 190 - 20 * (1 - a), "YOLO11 객체 인식 모델 만들기", font(64, "b"), fade(TXT, a))
    b = prog(t, 0.8, 0.9)
    text_c(d, W / 2, 285, "수집 데이터 → 라벨링 → 학습 → 검증 → 테스트 → 배포", font(30, "m"), fade(CYAN, b))
    c = prog(t, 1.4, 0.9)
    text_c(d, W / 2, 345, "9단계 실습 가이드  ·  Raspbot V2 자율주행  ·  09_yolo11_pipeline", font(22), fade(MUTED, c))
    icons = A.icons
    k = prog(t, m[1], 1.0)
    for i, ic in enumerate(icons):
        kk = prog(t, m[1] + i * 0.2, 0.6)
        if kk > 0:
            x = 290 + i * 150
            paste_fit(img, ic, (x, 420 + 20 * (1 - kk), x + 110, 530 + 20 * (1 - kk)), alpha=kk,
                      border=CLASS_COLORS[CLASSES[i]])
            text_c(d, x + 55, 540, CLASSES[i], font(20, "s"), fade(CLASS_COLORS[CLASSES[i]], kk))
    _ = k


# ---------------- 1. 클래스
@scene("INTRO", "모델이 찾을 대상 = 클래스", chapter="클래스 정하기")
@narr(S("모델이 찾아야 할 대상을 클래스라고 합니다."),
      S("우리는 차량, 초록불, O 표지판, 빨간불, X 표지판, 이렇게 다섯 개의 클래스를 사용합니다.",
        "우리는 차량, 초록불, 오 표지판, 빨간불, 엑스 표지판, 이렇게 다섯 개의 클래스를 사용합니다."),
      S("클래스 목록과 순서는 config.yaml 파일 한 곳에서 관리하고, 순서가 곧 클래스 번호가 됩니다.",
        "클래스 목록과 순서는 컨피그 야믈 파일 한 곳에서 관리하고, 순서가 곧 클래스 번호가 됩니다."))
def sc_classes(img, d, t, m, T):
    names_ko = ["앞 차량", "초록불", "O 표지판", "빨간불", "X 표지판"]
    for i in range(5):
        a = prog(t, m[1] + i * 0.45, 0.5)
        x = 70 + i * 232
        if a <= 0:
            continue
        rrect(d, (x, 130, x + 210, 400), fill=fade(PANEL, a), outline=fade(CLASS_COLORS[CLASSES[i]], a))
        paste_fit(img, A.icons[i], (x + 30, 150, x + 180, 300), alpha=a)
        text_c(d, x + 105, 312, f"{i}: {CLASSES[i]}", font(28, "b"), fade(CLASS_COLORS[CLASSES[i]], a))
        text_c(d, x + 105, 352, names_ko[i], font(22, "m"), fade(TXT, a))
    a = prog(t, m[2], 0.6)
    if a > 0:
        lines = [("classes:", TXT, "out"), ("  - car     # 0", CLASS_COLORS["car"], "out"),
                 ("  - green   # 1", CLASS_COLORS["green"], "out"), ("  - oo      # 2", CLASS_COLORS["oo"], "out"),
                 ("  - red     # 3", CLASS_COLORS["red"], "out"), ("  - xx      # 4", CLASS_COLORS["xx"], "out")]
        terminal(d, (70, 425, 520, 590), lines, t, start=m[2], size=15, title="config.yaml", line_gap=1.3)
        d.text((560, 455), "순서 = class_id", font=font(30, "b"), fill=fade(YELLOW, a))
        d.text((560, 505), "한 번 학습한 뒤에는 순서를 바꾸지 마세요", font=font(22, "m"), fill=fade(MUTED, a))


# ---------------- 2. 전체 흐름
STEP_NAMES = ["데이터 정리", "라벨링", "라벨 점검", "데이터 분할", "학습", "검증", "테스트", "추론", "배포 변환"]
STEP_FILES = ["01_prepare_images", "02_label_tool", "03_check_labels", "04_split_dataset", "05_train",
              "06_validate", "07_test", "08_predict", "09_export"]


@scene("OVERVIEW", "전체 9단계 흐름", chapter="전체 흐름")
@narr(S("전체 과정은 아홉 단계입니다."),
      S("데이터 정리, 라벨링, 라벨 점검, 데이터 분할까지가 데이터 준비 단계입니다."),
      S("그 다음 학습, 검증, 테스트를 거치고, 마지막으로 실제 영상 추론과 배포용 변환을 합니다."),
      S("검증 기준을 통과하지 못하면 데이터를 보강해서 다시 학습하는 개선 루프를 돕니다."))
def sc_overview(img, d, t, m, T):
    pos = []
    for i in range(9):
        r, c = divmod(i, 3)
        if r == 1:
            c = 2 - c        # 뱀 모양 배치
        pos.append((150 + c * 360, 120 + r * 150))
    for i in range(8):
        a = prog(t, 0.3 + i * 0.15 + 0.1, 0.4)
        (x1, y1), (x2, y2) = pos[i], pos[i + 1]
        if a > 0:
            if y1 == y2:
                sx = x1 + 260 if x2 > x1 else x1
                ex = x2 if x2 > x1 else x2 + 260
                arrow(d, (sx + (8 if x2 > x1 else -8), y1 + 45), (ex - (8 if x2 > x1 else -8), y2 + 45), fade(MUTED, a), 3)
            else:
                arrow(d, (x1 + 130, y1 + 92), (x2 + 130, y2 - 6), fade(MUTED, a), 3)
    for i, (x, y) in enumerate(pos):
        a = prog(t, 0.3 + i * 0.15, 0.4)
        if a <= 0:
            continue
        hi = (i < 4 and m[1] <= t < m[2]) or (i >= 4 and m[2] <= t < m[3])
        col = STEP_COLORS[i + 1]
        rrect(d, (x, y, x + 260, y + 90), fill=fade(mix(PANEL, col, 0.35 if hi else 0.08), a),
              outline=fade(col, a), w=4 if hi else 2)
        d.text((x + 16, y + 12), f"{i + 1}", font=font(36, "b"), fill=fade(col, a))
        d.text((x + 62, y + 14), STEP_NAMES[i], font=font(26, "b"), fill=fade(TXT, a))
        d.text((x + 62, y + 52), STEP_FILES[i] + ".py", font=font(16), fill=fade(MUTED, a))
    a = prog(t, m[3], 0.8)
    if a > 0:   # 개선 루프: 6(검증) → 1(정리)
        (x6, y6), (x1_, y1_) = pos[5], pos[0]
        col = fade(RED, a)
        d.line([(x6, y6 + 45), (60, y6 + 45), (60, y1_ + 45)], fill=col, width=4)
        arrow(d, (60, y1_ + 45), (x1_ - 6, y1_ + 45), col, 4)
        d.text((72, y1_ + 100), "FAIL → 데이터 보강 후 재학습", font=font(20, "b"), fill=col)


# ---------------- 3. 설치
@scene("SETUP", "개발 환경 준비", chapter="환경 준비")
@narr(S("먼저 개발 환경을 준비합니다. 가상환경을 만들고 requirements 파일로 필요한 패키지를 설치합니다.",
        "먼저 개발 환경을 준비합니다. 가상환경을 만들고 리콰이어먼츠 파일로 필요한 패키지를 설치합니다."),
      S("--prefer-binary 옵션을 붙이면 미리 빌드된 패키지를 받아서 설치가 훨씬 빠릅니다.",
        "프리퍼 바이너리 옵션을 붙이면 미리 빌드된 패키지를 받아서 설치가 훨씬 빠릅니다."),
      S("GPU가 있으면 학습이 빠르고, 없다면 구글 코랩의 무료 GPU를 써도 좋습니다.",
        "지피유가 있으면 학습이 빠르고, 없다면 구글 코랩의 무료 지피유를 써도 좋습니다."))
def sc_setup(img, d, t, m, T):
    lines = [("cd 09_yolo11_pipeline", TXT, "cmd"), ("python3 -m venv .venv", TXT, "cmd"),
             ("source .venv/bin/activate", TXT, "cmd"),
             ("pip install --prefer-binary -r requirements.txt", YELLOW, "cmd"),
             ("Successfully installed ultralytics-8.4 torch-2.15 opencv-python-5.0 ...", GREEN, "out"),
             ("python -c \"import ultralytics; print(ultralytics.__version__)\"", TXT, "cmd"),
             ("8.4.218", GREEN, "out")]
    terminal(d, (60, 110, 800, 440), lines, t, start=0.6, cps=30)
    items = ["ultralytics  (YOLO11 · PyTorch)", "opencv-python · numpy · PyYAML", "onnx · ncnn  (배포 변환)"]
    bullet_list(d, 840, 140, items, t, [1.0, 1.6, 2.2], size=21, gap=46, icon="•", icon_color=CYAN)
    a = prog(t, m[2], 0.6)
    if a > 0:
        rrect(d, (60, 470, 1220, 580), fill=fade(PANEL, a), outline=fade(GREEN, a))
        d.text((90, 490), "학습 장치", font=font(24, "b"), fill=fade(GREEN, a))
        d.text((90, 530), "NVIDIA GPU (device 0)   >   Google Colab GPU   >   CPU (느리지만 데모는 2분)",
               font=font(22, "m"), fill=fade(TXT, a))


# ---------------- 4. 1단계 데이터 정리
@scene("STEP 1", "수집 데이터 정리", step=1, chapter="1단계 데이터 정리")
@narr(S("1단계는 수집한 데이터 정리입니다. 로봇 카메라로 찍은 사진과 동영상을 data/raw 폴더에 넣습니다.",
        "1단계는 수집한 데이터 정리입니다. 로봇 카메라로 찍은 사진과 동영상을 데이터 로 폴더에 넣습니다."),
      S("동영상은 일정 프레임마다 한 장씩 뽑고, 거의 똑같은 사진은 자동으로 걸러냅니다."),
      S("다양한 거리, 각도, 조명에서 찍은 사진이 많을수록 모델이 더 똑똑해집니다."))
def sc_prepare(img, d, t, m, T):
    frames = A.thumbs[:12]
    d.text((60, 105), "drive.mp4  (연속 프레임)", font=font(22, "s"), fill=MUTED)
    for i, fr in enumerate(frames):
        a = prog(t, 0.3 + i * 0.08, 0.3)
        x = 60 + i * 96
        if a > 0:
            paste_fit(img, fr, (x, 140, x + 90, 208), alpha=a)
    sel = [0, 4, 8]
    a = prog(t, m[1], 0.6)
    if a > 0:
        for i in range(12):
            x = 60 + i * 96
            if i in sel:
                d.rectangle((x - 3, 137, x + 93, 211), outline=fade(GREEN, a), width=3)
        d.text((60, 222), "N 프레임마다 1장 추출  (video_every_n)", font=font(20, "m"), fill=fade(GREEN, a))
        for j, i in enumerate(sel):
            k = prog(t, m[1] + 0.5 + j * 0.3, 0.6)
            sx, ex = 60 + i * 96 + 45, 160 + j * 190 + 80
            if k > 0:
                arrow(d, (sx, 250), (lerp(sx, ex, k), lerp(250, 290, k)), fade(GREEN, k), 3)
                paste_fit(img, frames[i], (160 + j * 190, 295, 160 + j * 190 + 160, 415), alpha=k, border=GREEN)
        k = prog(t, m[1] + 1.6, 0.6)
        if k > 0:
            x = 160 + 3 * 190
            paste_fit(img, frames[8], (x, 295, x + 160, 415), alpha=k * 0.6, border=RED)
            d.line([(x, 295), (x + 160, 415)], fill=fade(RED, k), width=5)
            d.line([(x + 160, 295), (x, 415)], fill=fade(RED, k), width=5)
            d.text((x + 5, 420), "중복 사진 제외 (dHash)", font=font(18, "s"), fill=fade(RED, k))
    lines = [("python scripts/01_prepare_images.py", YELLOW, "cmd"),
             ("  🎞  drive.mp4: 90 프레임 → 9 장 저장".replace("🎞  ", ""), TXT, "out"),
             ("  저장: 14 장 | 중복 제외: 0 | 작은 이미지 제외: 0 | 손상: 0", GREEN, "out")]
    terminal(d, (60, 455, 840, 590), lines, t, start=m[1] + 2.5, size=16)
    bullet_list(d, 880, 455, ["거리: 가까이 / 멀리", "각도: 정면 / 비스듬히", "조명: 밝음 / 어두움 / 역광"],
                t, [m[2], m[2] + 0.4, m[2] + 0.8], size=20, gap=40, icon="✓", icon_color=CYAN)


# ---------------- 5. 2단계 라벨링
@scene("STEP 2", "라벨링 (바운딩 박스 그리기)", step=2, chapter="2단계 라벨링")
@narr(S("2단계는 라벨링입니다. 이미지 속 객체마다 네모 박스를 그리고 클래스를 지정합니다."),
      S("라벨 도구에서 숫자 키로 클래스를 고르고, 마우스로 드래그해서 박스를 그립니다."),
      S("D 키를 누르면 저장하고 다음 이미지로 넘어갑니다.", "디 키를 누르면 저장하고 다음 이미지로 넘어갑니다."),
      S("라벨 파일에는 한 줄에 클래스 번호, 박스 중심 x와 y, 너비와 높이가 0에서 1 사이 값으로 저장됩니다.",
        "라벨 파일에는 한 줄에 클래스 번호, 박스 중심 엑스와 와이, 너비와 높이가 영에서 일 사이 값으로 저장됩니다."),
      S("박스는 객체에 딱 맞게, 그리고 하나도 빠짐없이 그리는 것이 가장 중요합니다."),
      S("이미 만든 모델이 있다면 자동 라벨링으로 초안을 만들고 사람은 검토만 하면 됩니다."))
def sc_label(img, d, t, m, T):
    src = A.label_img
    ix, iy, iw, ih = 60, 130, 640, 480
    view = (ix, iy, ix + 640, iy + 420)
    s = min(640 / src.width, 420 / src.height)
    vw, vh = int(src.width * s), int(src.height * s)
    img.paste(src.resize((vw, vh), Image.LANCZOS), (ix, iy))
    rrect(d, (ix - 2, iy - 32, ix + vw + 2, iy + vh + 2), outline=PANEL2, r=8)
    d.rectangle((ix - 1, iy - 31, ix + vw + 1, iy - 1), fill=PANEL2)
    boxes = A.label_boxes        # [(cls, x1,y1,x2,y2) normalized]
    t0, t1 = m[1], m[3]
    per = (t1 - t0) / max(1, len(boxes))
    done_lines = 0
    cur_cls = 0
    for k, (c, x1, y1, x2, y2) in enumerate(boxes):
        st = t0 + k * per
        p1 = (ix + x1 * vw, iy + y1 * vh)
        p2 = (ix + x2 * vw, iy + y2 * vh)
        if t < st:
            continue
        cur_cls = c
        u = (t - st) / per
        col = CLASS_COLORS[CLASSES[c]]
        if u < 0.25:            # 커서 이동
            cx, cy = lerp(ix + vw / 2, p1[0], ease(u / 0.25)), lerp(iy + vh / 2, p1[1], ease(u / 0.25))
            cursor(d, cx, cy)
        elif u < 0.7:           # 드래그
            k2 = ease((u - 0.25) / 0.45)
            ex, ey = lerp(p1[0], p2[0], k2), lerp(p1[1], p2[1], k2)
            d.rectangle((p1[0], p1[1], ex, ey), outline=col, width=3)
            cursor(d, ex, ey, pressed=True)
        else:
            d.rectangle((*p1, *p2), outline=col, width=3)
            tag = f"{c}:{CLASSES[c]}"
            tw = d.textlength(tag, font=font(16, "b"))
            d.rectangle((p1[0], p1[1] - 22, p1[0] + tw + 10, p1[1]), fill=col)
            d.text((p1[0] + 5, p1[1] - 21), tag, font=font(16, "b"), fill=(0, 0, 0))
            done_lines = k + 1
            if u < 0.95:
                cursor(d, p2[0], p2[1])
    nb = done_lines
    d.text((ix + 8, iy - 27), f"[12/240] demo_0011.jpg | class {cur_cls}:{CLASSES[cur_cls]} | boxes {nb}",
           font=font(16, "m"), fill=TXT)
    # 키 표시
    if t0 <= t < t1:
        key = str(cur_cls)
        rrect(d, (ix + vw - 90, iy + vh + 14, ix + vw, iy + vh + 56), fill=PANEL2, outline=YELLOW, r=8)
        text_c(d, ix + vw - 45, iy + vh + 20, f"키 {key}", font(22, "b"), YELLOW)
    if m[2] <= t < m[3]:
        k = prog(t, m[2], 0.3)
        rrect(d, (ix, iy + vh + 14, ix + 330, iy + vh + 56), fill=fade(PANEL2, k), outline=fade(GREEN, k), r=8)
        d.text((ix + 12, iy + vh + 20), "D: 저장 → 다음 이미지", font=font(22, "b"), fill=fade(GREEN, k))
    # 라벨 파일 패널
    lines = [(f"{c} {(x1 + x2) / 2:.4f} {(y1 + y2) / 2:.4f} {x2 - x1:.4f} {y2 - y1:.4f}",
              CLASS_COLORS[CLASSES[c]], "out") for c, x1, y1, x2, y2 in boxes[:done_lines]]
    terminal(d, (740, 100, 1220, 300), lines, t, start=0, size=17, title="labels/demo_0011.txt")
    a = prog(t, m[3], 0.6)
    if a > 0:
        rrect(d, (740, 320, 1220, 470), fill=fade(PANEL, a), outline=fade(CYAN, a))
        hdr = ["class", "x_center", "y_center", "width", "height"]
        cols = [CLASS_COLORS["car"], CYAN, CYAN, PURPLE, PURPLE]
        x = 760
        for h_, c_ in zip(hdr, cols):
            d.text((x, 335), h_, font=font(19, "b"), fill=fade(c_, a))
            x += d.textlength(h_, font=font(19, "b")) + 16
        d.text((760, 375), "모든 좌표 = 픽셀 ÷ 이미지 크기  (0 ~ 1)", font=font(20, "m"), fill=fade(TXT, a))
        d.text((760, 410), "빈 파일 = 객체 없는 배경 이미지", font=font(20, "m"), fill=fade(MUTED, a))
    a = prog(t, m[4], 0.6)
    if a > 0:
        bullet_list(d, 750, 490, ["박스는 객체에 딱 맞게 (타이트)", "보이는 객체는 빠짐없이 전부"],
                    t, [m[4], m[4] + 0.5], size=21, gap=40, icon="✓", icon_color=GREEN)
    a = prog(t, m[5], 0.6)
    if a > 0:
        rrect(d, (740, 488, 1220, 590), fill=fade(PANEL, a), outline=fade(YELLOW, a))
        d.text((760, 500), "자동 사전 라벨링 (선택)", font=font(22, "b"), fill=fade(YELLOW, a))
        draw_mono(d, 760, 545, "02b_auto_label.py --weights best.pt", 16, TXT, alpha=a)


# ---------------- 6. 3단계 라벨 점검
@scene("STEP 3", "라벨 품질 점검", step=3, chapter="3단계 라벨 점검")
@narr(S("3단계는 라벨 품질 점검입니다. 잘못된 라벨 하나가 좋은 라벨 여러 장의 효과를 깎아 먹기 때문입니다."),
      S("형식 오류, 이미지 밖으로 나간 좌표, 중복 박스를 찾고, 클래스별 개수를 막대로 보여 줍니다."),
      S("미리보기 이미지를 열어서 박스가 제자리에 있는지 눈으로도 꼭 확인하세요."))
def sc_check(img, d, t, m, T):
    lines = [("python scripts/03_check_labels.py", YELLOW, "cmd"),
             ("  전체 이미지 240 | 라벨 완료 240 | 미라벨 0 | 배경 20", TXT, "out"),
             ("", TXT, "out"),
             ("  클래스        박스수  이미지수   분포", MUTED, "out"),
             ("  0:car            82       70   █████", CLASS_COLORS["car"], "out"),
             ("  1:green          77       67   █████", CLASS_COLORS["green"], "out"),
             ("  2:oo            100       88   ██████", CLASS_COLORS["oo"], "out"),
             ("  3:red            94       85   ██████", CLASS_COLORS["red"], "out"),
             ("  4:xx             89       72   ██████", CLASS_COLORS["xx"], "out"),
             ("", TXT, "out"),
             ("  ERROR 0 건 | WARN 0 건", GREEN, "out"),
             ("  리포트: reports/label_check.md", MUTED, "out")]
    terminal(d, (60, 110, 700, 590), lines, t, start=m[0] + 1.0, size=17, line_gap=1.55)
    checks = ["값 5개 · 숫자 형식", "class_id 범위", "좌표 0~1 (이미지 안)", "너무 작은 / 중복 박스", "클래스 불균형"]
    bullet_list(d, 740, 120, checks, t, [m[1] + i * 0.35 for i in range(5)], size=21, gap=40, icon="✓",
                icon_color=GREEN)
    a = prog(t, m[2], 0.7)
    if a > 0 and A.preview is not None:
        paste_fit(img, A.preview, (740, 352, 1220, 592), alpha=a, border=CYAN)
        d.text((745, 322), "reports/label_preview/", font=font(18, "s"), fill=fade(CYAN, a))


# ---------------- 7. 4단계 데이터 분할
@scene("STEP 4", "데이터셋 분할 (train / val / test)", step=4, chapter="4단계 데이터 분할")
@narr(S("4단계는 데이터 분할입니다. 전체 데이터를 학습용 70, 검증용 20, 시험용 10 퍼센트로 나눕니다.",
        "4단계는 데이터 분할입니다. 전체 데이터를 학습용 칠십, 검증용 이십, 시험용 십 퍼센트로 나눕니다."),
      S("학습용으로 모델을 가르치고, 검증용으로 중간 점검을 하고, 시험용은 마지막에 딱 한 번만 씁니다."),
      S("같은 동영상에서 나온 프레임은 같은 묶음에 넣어야 점수가 부풀려지지 않습니다."),
      S("분할이 끝나면 학습 설정 파일인 data.yaml이 만들어집니다.", "분할이 끝나면 학습 설정 파일인 데이터 야믈이 만들어집니다."))
def sc_split(img, d, t, m, T):
    buckets = [("train", "70%", "169장", "모델 학습", BLUE, 28), ("val", "20%", "47장", "중간 점검 · best 선택", YELLOW, 8),
               ("test", "10%", "24장", "최종 시험 (1회)", RED, 4)]
    by = [120, 290, 440]
    bh = [150, 130, 120]
    for (name, pct, cnt, role, col, _), y, hh in zip(buckets, by, bh):
        a = prog(t, 0.4, 0.6)
        rrect(d, (760, y, 1220, y + hh), fill=fade(PANEL, a), outline=fade(col, a), w=3)
        d.text((780, y + 12), f"{name}  {pct}", font=font(30, "b"), fill=fade(col, a))
        d.text((1080, y + 18), cnt, font=font(24, "s"), fill=fade(TXT, a))
        ra = prog(t, m[1] + ["train", "val", "test"].index(name) * 0.6, 0.5)
        d.text((780, y + 56), role, font=font(20, "m"), fill=fade(TXT, ra))
    # 썸네일 40개 → 각 버킷으로 이동
    order = [0] * 28 + [1] * 8 + [2] * 4
    rng = np.random.default_rng(3)
    perm = rng.permutation(40)
    for n in range(40):
        i = perm[n]
        b = order[n]
        r, c = divmod(i, 8)
        sx, sy = 60 + c * 82, 130 + r * 82
        slot = sum(1 for q in range(n) if order[q] == b)
        cols = 14 if b == 0 else 8
        ex = 780 + (slot % cols) * 30
        ey = by[b] + 92 + (slot // cols) * 26 - (0 if b == 0 else 0)
        if b != 0:
            ey = by[b] + 88
        k = prog(t, m[0] + 1.0 + n * 0.05, 0.8)
        x, y = lerp(sx, ex, k), lerp(sy, ey, k)
        size = lerp(74, 24, k)
        th = A.thumbs[i % len(A.thumbs)]
        paste_fit(img, th, (x, y, x + size, y + size * 0.75), radius=4)
        if k > 0.95:
            d.rectangle((x, y, x + size, y + size * 0.75), outline=buckets[b][4], width=1)
    a = prog(t, m[2], 0.6)
    if a > 0:
        rrect(d, (60, 380, 700, 470), fill=fade(PANEL, a), outline=fade(ORANGE, a))
        d.text((80, 392), "drive1_000010.jpg · drive1_000020.jpg · ...", font=font(19, "m"), fill=fade(TXT, a))
        d.text((80, 428), "→ 같은 동영상(그룹) = 같은 split  (데이터 누수 방지)", font=font(20, "b"), fill=fade(ORANGE, a))
    if t >= m[3]:
        lines = [("path: datasets/raspbot", TXT, "out"), ("train: images/train", BLUE, "out"),
                 ("val: images/val", YELLOW, "out"), ("test: images/test", RED, "out"),
                 ("nc: 5", TXT, "out"), ("names: {0: car, 1: green, 2: oo, 3: red, 4: xx}", TXT, "out")]
        terminal(d, (60, 480, 700, 600), lines, t, start=m[3], size=14, title="data.yaml", line_gap=1.25)


# ---------------- 8. 5단계 학습
@scene("STEP 5", "YOLO11 학습 (전이학습)", step=5, chapter="5단계 학습")
@narr(S("5단계는 학습입니다. COCO 데이터로 미리 학습된 yolo11n 모델에서 출발하는 전이 학습을 합니다.",
        "5단계는 학습입니다. 코코 데이터로 미리 학습된 욜로 일레븐 엔 모델에서 출발하는 전이 학습을 합니다."),
      S("에폭이 진행될수록 손실은 내려가고, 정확도 지표인 mAP는 올라갑니다.",
        "에폭이 진행될수록 손실은 내려가고, 정확도 지표인 맵은 올라갑니다."),
      S("검증 점수가 가장 좋았던 가중치가 best.pt로 저장되고 models 폴더로 자동 복사됩니다.",
        "검증 점수가 가장 좋았던 가중치가 베스트 피티로 저장되고 모델스 폴더로 자동 복사됩니다."),
      S("학습 손실은 내려가는데 검증 손실만 다시 올라가면 과적합이니, 데이터를 늘리거나 일찍 멈춥니다."))
def sc_train(img, d, t, m, T):
    rows = A.results
    N = len(rows)
    p = clamp((t - (m[0] + 2.5)) / max(1.0, (m[2] - m[0] - 2.5)))
    ep = p * (N - 1)
    e_i = int(ep)
    lines = [("python scripts/05_train.py", YELLOW, "cmd"),
             ("모델: yolo11n.pt | epochs 15 | imgsz 320 | device cpu", MUTED, "out")]
    for r in rows[: e_i + 1 if t > m[0] + 2.5 else 0][-6:]:
        lines.append((f"Epoch {int(r['epoch']):>2}/{N}  box {r['train/box_loss']:.3f}  cls {r['train/cls_loss']:.3f}"
                      f"  mAP50 {r['metrics/mAP50(B)']:.3f}", TXT, "out"))
    if t >= m[2]:
        lines += [("✅ best.pt → models/best.pt", GREEN, "out")]
    terminal(d, (60, 110, 640, 470), lines, t, start=m[0] + 0.8, size=15)

    def chart(box, series, title, ymax=None, legend_bottom=False):
        x1, y1, x2, y2 = box
        rrect(d, box, fill=PANEL, outline=PANEL2)
        d.text((x1 + 14, y1 + 8), title, font=font(19, "b"), fill=TXT)
        gx1, gy1, gx2, gy2 = x1 + 50, y1 + 42, x2 - 16, y2 - 30
        vmax = ymax or max(max(r[k] for r in rows) for k, _, _ in series)
        for g in range(5):
            yy = gy2 - (gy2 - gy1) * g / 4
            d.line([(gx1, yy), (gx2, yy)], fill=PANEL2, width=1)
            d.text((x1 + 8, yy - 9), f"{vmax * g / 4:.2f}", font=font(13), fill=MUTED)
        d.text((gx2 - 40, gy2 + 6), "epoch", font=font(13), fill=MUTED)
        lx = gx1 + 10
        for key, col, label in series:
            pts = []
            for i in range(N):
                if i > ep + 1e-6:
                    break
                pts.append((gx1 + (gx2 - gx1) * i / (N - 1), gy2 - (gy2 - gy1) * rows[i][key] / vmax))
            if e_i + 1 < N and ep > e_i:
                fr = ep - e_i
                v = lerp(rows[e_i][key], rows[e_i + 1][key], fr)
                pts.append((gx1 + (gx2 - gx1) * ep / (N - 1), gy2 - (gy2 - gy1) * v / vmax))
            if len(pts) > 1:
                d.line(pts, fill=col, width=3)
            if pts:
                d.ellipse((pts[-1][0] - 4, pts[-1][1] - 4, pts[-1][0] + 4, pts[-1][1] + 4), fill=col)
            ly = (gy2 - 50 if legend_bottom else y1 + 12) + series.index((key, col, label)) * 20
            d.rectangle((x2 - 150, ly, x2 - 138, ly + 12), fill=col)
            d.text((x2 - 132, ly - 4), label, font=font(14, "m"), fill=TXT)

    chart((670, 110, 1220, 345), [("metrics/mAP50(B)", GREEN, "mAP50"), ("metrics/mAP50-95(B)", CYAN, "mAP50-95")],
          "정확도 (높을수록 좋음)", ymax=1.0, legend_bottom=True)
    chart((670, 360, 1220, 595), [("train/cls_loss", RED, "train cls_loss"), ("val/cls_loss", ORANGE, "val cls_loss")],
          "손실 (낮을수록 좋음)")
    text_c(d, 355, 485, f"epoch {min(N, e_i + 1) if t > m[0] + 2.5 else 0} / {N}", font(34, "b"), YELLOW)
    a = prog(t, m[3], 0.6)
    if a > 0:
        rrect(d, (60, 535, 640, 595), fill=fade(PANEL, a), outline=fade(RED, a))
        d.text((78, 550), "train loss ↓  +  val loss ↑  =  과적합", font=font(22, "b"), fill=fade(RED, a))


# ---------------- 9. 평가 지표
@scene("TIP", "평가 지표: IoU · 정밀도 · 재현율", chapter="평가 지표 이해")
@narr(S("결과를 보기 전에 평가 지표를 알아 둡시다."),
      S("IoU는 정답 박스와 예측 박스가 겹친 비율입니다. 0.5 이상이면 맞췄다고 판단합니다.",
        "아이오유는 정답 박스와 예측 박스가 겹친 비율입니다. 영점 오 이상이면 맞췄다고 판단합니다."),
      S("정밀도는 모델이 있다고 한 것 중 맞은 비율이고, 재현율은 실제 객체 중 찾아낸 비율입니다."),
      S("자율주행에서는 빨간불을 놓치지 않는 재현율이 특히 중요합니다."))
def sc_metrics(img, d, t, m, T):
    gx1, gy1, gx2, gy2 = 160, 200, 400, 420
    k = ease((t - m[1]) / 3.0) if t > m[1] else 0
    off = lerp(170, 25, k)
    px1, py1, px2, py2 = gx1 + off, gy1 + off * 0.5, gx2 + off, gy2 + off * 0.5
    ix1, iy1, ix2, iy2 = max(gx1, px1), max(gy1, py1), min(gx2, px2), min(gy2, py2)
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    area = (gx2 - gx1) * (gy2 - gy1)
    iou = inter / (2 * area - inter)
    a = prog(t, 0.3, 0.6)
    if inter > 0:
        d.rectangle((ix1, iy1, ix2, iy2), fill=fade((90, 80, 30), a))
    d.rectangle((gx1, gy1, gx2, gy2), outline=fade(GREEN, a), width=4)
    d.rectangle((px1, py1, px2, py2), outline=fade(RED, a), width=4)
    d.text((gx1, gy1 - 30), "정답 (GT)", font=font(20, "b"), fill=fade(GREEN, a))
    d.text((px1 + 40, py2 + 6), "예측", font=font(20, "b"), fill=fade(RED, a))
    d.text((80, 120), f"IoU = 겹친 면적 ÷ 합친 면적 = {iou:.2f}", font=font(28, "b"), fill=fade(TXT, a))
    ok = iou >= 0.5
    rrect(d, (80, 520, 560, 585), fill=fade(PANEL, a), outline=fade(GREEN if ok else RED, a))
    text_c(d, 320, 535, "IoU ≥ 0.5 → 맞춤 (TP)" if ok else "IoU < 0.5 → 틀림", font(26, "b"),
           fade(GREEN if ok else RED, a))
    a = prog(t, m[2], 0.6)
    if a > 0:
        rrect(d, (640, 110, 1220, 330), fill=fade(PANEL, a), outline=fade(BLUE, a))
        d.text((665, 125), "정밀도 Precision = TP ÷ (TP + FP)", font=font(25, "b"), fill=fade(BLUE, a))
        d.text((665, 165), "\"있다\"고 한 것 중 진짜 맞은 비율", font=font(21, "m"), fill=fade(TXT, a))
        d.text((665, 197), "낮으면 → 없는 신호에 멈춤 (오탐)", font=font(20), fill=fade(MUTED, a))
        d.text((665, 240), "재현율 Recall = TP ÷ (TP + FN)", font=font(25, "b"), fill=fade(PURPLE, a))
        d.text((665, 280), "실제 객체 중 찾아낸 비율", font=font(21, "m"), fill=fade(TXT, a))
    a = prog(t, m[3], 0.6)
    if a > 0:
        rrect(d, (640, 350, 1220, 585), fill=fade(PANEL, a), outline=fade(RED, a), w=3)
        paste_fit(img, A.icons[3], (665, 380, 815, 530), alpha=a)
        d.text((840, 390), "red 의 Recall 이 낮으면", font=font(24, "b"), fill=fade(TXT, a))
        d.text((840, 432), "빨간불을 못 보고 통과!", font=font(30, "b"), fill=fade(RED, a))
        d.text((840, 485), "→ 클래스별 위험도를 생각해", font=font(20, "m"), fill=fade(MUTED, a))
        d.text((840, 515), "   합격 기준을 정하세요", font=font(20, "m"), fill=fade(MUTED, a))


# ---------------- 10. 6단계 검증
@scene("STEP 6", "검증 — 합격 / 불합격 판정", step=6, chapter="6단계 검증")
@narr(S("6단계는 검증입니다. 검증 데이터로 클래스별 정밀도, 재현율, mAP를 계산합니다.",
        "6단계는 검증입니다. 검증 데이터로 클래스별 정밀도, 재현율, 맵을 계산합니다."),
      S("config에 정한 합격 기준과 비교해서 통과인지 실패인지 자동으로 판정합니다.",
        "컨피그에 정한 합격 기준과 비교해서 통과인지 실패인지 자동으로 판정합니다."),
      S("모든 결정이 끝나면 시험 데이터로 최종 시험을 딱 한 번 봅니다."))
def sc_validate(img, d, t, m, T):
    v = A.val
    d.text((60, 105), "python scripts/06_validate.py", font=font(20, "s"), fill=YELLOW)
    hdr = ["클래스", "Precision", "Recall", "mAP50", "mAP50-95"]
    xs = [70, 230, 380, 510, 630]
    rrect(d, (60, 140, 770, 470), fill=PANEL, outline=PANEL2)
    for x, h_ in zip(xs, hdr):
        d.text((x, 152), h_, font=font(19, "b"), fill=MUTED)
    rows = [(c["name"], c["precision"], c["recall"], c["map50"], c["map50_95"]) for c in v["per_class"]]
    o = v["overall"]
    rows.append(("전체", o["precision"], o["recall"], o["map50"], o["map50_95"]))
    for i, r in enumerate(rows):
        a = prog(t, m[0] + 1.2 + i * 0.35, 0.4)
        y = 192 + i * 44
        col = CLASS_COLORS.get(r[0], YELLOW)
        f = font(21, "b" if r[0] == "전체" else "m")
        if r[0] == "전체":
            d.line([(70, y - 6), (760, y - 6)], fill=fade(PANEL2, a), width=2)
        d.text((xs[0], y), r[0], font=f, fill=fade(col, a))
        for x, val in zip(xs[1:], r[1:]):
            d.text((x + 10, y), f"{val:.3f}", font=f, fill=fade(TXT, a))
    th = [(c["metric"], c["value"], c["threshold"], c["pass"]) for c in v["checks"]][:4]
    for i, (k, val, thr, okk) in enumerate(th):
        a = prog(t, m[1] + i * 0.35, 0.4)
        y = 130 + i * 46
        rrect(d, (810, y, 1220, y + 38), fill=fade(PANEL, a), outline=fade(GREEN if okk else RED, a), r=8)
        d.text((825, y + 6), ("✓ " if okk else "✗ ") + f"{k:<10}", font=font(20, "b"), fill=fade(GREEN if okk else RED, a))
        d.text((990, y + 7), f"{val:.3f} ≥ {thr}", font=font(19, "m"), fill=fade(TXT, a))
    a = prog(t, m[1] + 1.8, 0.5)
    if a > 0:
        sc = lerp(1.5, 1.0, a)
        f = font(int(60 * sc), "b")
        rrect(d, (870, 330, 1160, 420), outline=fade(GREEN, a), w=6, r=16)
        text_c(d, 1015, 340 + (1 - a) * 10, "PASS", f, fade(GREEN, a))
    a = prog(t, m[2], 0.6)
    if a > 0:
        rrect(d, (60, 495, 1220, 590), fill=fade(PANEL, a), outline=fade(RED, a))
        draw_mono(d, 85, 512, "python scripts/06_validate.py --split test", 18, YELLOW, alpha=a)
        d.text((85, 548), "test = 최종 시험지. 점수를 보고 다시 튜닝하면 test 에 과적합됩니다.", font=font(21, "m"),
               fill=fade(TXT, a))


# ---------------- 11. 7단계 테스트
@scene("STEP 7", "운영 조건 테스트 (오류 분석)", step=7, chapter="7단계 테스트")
@narr(S("7단계는 실제 운영 조건 테스트입니다. 로봇과 똑같이 신뢰도 0.5, 입력 크기 320으로 추론합니다.",
        "7단계는 실제 운영 조건 테스트입니다. 로봇과 똑같이 신뢰도 영점 오, 입력 크기 삼백이십으로 추론합니다."),
      S("정답과 하나씩 비교해서 정탐, 오탐, 미탐, 오분류를 셉니다."),
      S("틀린 이미지는 따로 저장되니, 초록색 정답과 빨간색 예측을 비교하며 원인을 찾아보세요."))
def sc_test(img, d, t, m, T):
    tr = A.test
    lines = [("python scripts/07_test.py", YELLOW, "cmd"),
             ("conf=0.5  imgsz=320  (로봇과 동일)", MUTED, "out"), ("", TXT, "out"),
             ("  클래스      정답   TP   FP   FN   정밀도  재현율", MUTED, "out")]
    for c in tr["per_class"]:
        lines.append((f"  {c['name']:<10}{c['gt']:>5}{c['tp']:>5}{c['fp']:>5}{c['fn']:>5}"
                      f"   {c['precision']:.3f}   {c['recall']:.3f}", CLASS_COLORS[c["name"]], "out"))
    lines += [("", TXT, "out"), (f"  완벽히 맞힌 이미지: 24/24 (100%)", GREEN, "out"),
              (f"  지연시간 평균 {tr['latency_ms']['mean']:.1f}ms ≈ {1000 / tr['latency_ms']['mean']:.0f} FPS", TXT, "out")]
    terminal(d, (60, 110, 680, 560), lines, t, start=m[0] + 1.0, size=16, line_gap=1.55)
    kinds = [("TP 정탐", "맞게 찾음", GREEN), ("FP 오탐", "없는 걸 찾음", RED), ("FN 미탐", "놓침", ORANGE),
             ("WRONG", "클래스 틀림 (red↔green)", PURPLE)]
    for i, (k, desc, col) in enumerate(kinds):
        a = prog(t, m[1] + i * 0.35, 0.4)
        y = 115 + i * 42
        d.text((720, y), k, font=font(21, "b"), fill=fade(col, a))
        d.text((850, y + 2), desc, font=font(20, "m"), fill=fade(TXT, a))
    a = prog(t, m[2], 0.6)
    if a > 0:
        src = A.label_img.copy()
        dd = ImageDraw.Draw(src)
        sw, sh = src.size
        for c, x1, y1, x2, y2 in A.label_boxes:
            dd.rectangle((x1 * sw, y1 * sh, x2 * sw, y2 * sh), outline=(0, 200, 0), width=4)
        c, x1, y1, x2, y2 = A.label_boxes[0]
        dd.rectangle((x1 * sw + 10, y1 * sh + 8, x2 * sw + 10, y2 * sh + 8), outline=(230, 0, 0), width=4)
        dd.rectangle((40, 330, 120, 400), outline=(230, 0, 0), width=4)
        paste_fit(img, src, (720, 305, 1220, 580), alpha=a, border=MUTED)
        d.text((725, 278), "test_failures/ 예시 그림  (초록=정답, 빨강=예측)", font=font(17, "s"), fill=fade(MUTED, a))


# ---------------- 12. 8단계 추론
@scene("STEP 8", "실제 영상 · 카메라 추론", step=8, chapter="8단계 추론")
@narr(S("8단계는 추론입니다. 학습에 쓰지 않은 새 영상이나 카메라로 모델을 직접 확인합니다."),
      S("화면이 없는 라즈베리파이에서도 결과를 파일로 저장하며 동작합니다."),
      S("벤치마크 옵션으로 초당 몇 장을 처리하는지 속도도 측정할 수 있습니다."))
def sc_predict(img, d, t, m, T):
    a = prog(t, 0.4, 0.7)
    if A.pred is not None:
        paste_fit(img, A.pred, (60, 110, 640, 590), alpha=a, border=GREEN)
    lines = [("python scripts/08_predict.py --source drive.mp4", YELLOW, "cmd"),
             ("  처리 프레임: 90 | 평균 추론 20.5ms (≈ 48.9 FPS)", TXT, "out"),
             ("python scripts/08_predict.py --source 0 --show", YELLOW, "cmd"),
             ("  USB 카메라 실시간 표시 (q: 종료)", MUTED, "out"),
             ("python scripts/08_predict.py --source 0 --max-frames 300", YELLOW, "cmd"),
             ("  헤드리스: runs/predict/<시각>/result.mp4 저장", MUTED, "out")]
    terminal(d, (670, 110, 1220, 420), lines, t, start=m[0] + 1.5, size=14, cps=45)
    a = prog(t, m[2], 0.5)
    if a > 0:
        rrect(d, (670, 440, 1220, 590), fill=fade(PANEL, a), outline=fade(YELLOW, a))
        draw_mono(d, 690, 458, "08_predict.py --benchmark 100", 17, YELLOW, alpha=a)
        fps = 76.2 * ease((t - m[2] - 0.5) / 1.5) if t > m[2] + 0.5 else 0
        text_c(d, 945, 495, f"{fps:5.1f} FPS", font(54, "b"), fade(GREEN, a))


# ---------------- 13. 9단계 배포
@scene("STEP 9", "배포용 변환 & 라즈베리파이 적용", step=9, chapter="9단계 배포")
@narr(S("9단계는 배포용 변환입니다. 라즈베리파이에서는 ONNX나 NCNN 형식이 더 빠릅니다.",
        "9단계는 배포용 변환입니다. 라즈베리파이에서는 오닉스나 엔씨엔엔 형식이 더 빠릅니다."),
      S("변환한 모델이 원래 모델과 같은 결과를 내는지 자동으로 비교합니다."),
      S("마지막으로 모델 파일을 라즈베리파이의 source/models/yolo 폴더에 복사하면 주행 코드가 새 모델을 사용합니다.",
        "마지막으로 모델 파일을 라즈베리파이의 소스, 모델스, 욜로 폴더에 복사하면 주행 코드가 새 모델을 사용합니다."))
def sc_export(img, d, t, m, T):
    rrect(d, (60, 110, 640, 400), fill=PANEL, outline=PANEL2)
    d.text((80, 122), "평균 추론 시간 (M2 Max CPU, 낮을수록 빠름)", font=font(20, "b"), fill=TXT)
    bars = [("PyTorch .pt", 13.6, MUTED), ("ONNX", 7.3, GREEN)]
    for i, (name, ms, col) in enumerate(bars):
        k = prog(t, m[0] + 1.0 + i * 0.6, 1.0)
        y = 185 + i * 90
        d.text((80, y + 8), name, font=font(21, "s"), fill=TXT)
        d.rounded_rectangle((240, y, 240 + 330 * ms / 14 * k, y + 50), radius=8, fill=col)
        d.text((250 + 330 * ms / 14 * k, y + 10), f"{ms * k:.1f} ms", font=font(22, "b"), fill=TXT)
    a = prog(t, m[1], 0.5)
    if a > 0:
        d.text((80, 355), "✓ .pt 와 탐지 결과 일치율 100%", font=font(22, "b"), fill=fade(GREEN, a))
    lines = [("python scripts/09_export.py", YELLOW, "cmd"), ("  ✅ onnx: models/best.onnx", GREEN, "out"),
             ("  ✅ ncnn: models/best_ncnn_model/", GREEN, "out")]
    terminal(d, (670, 110, 1220, 260), lines, t, start=m[0] + 0.8, size=16)
    nodes = [("PC / Colab", "학습 · 검증", BLUE), ("Raspberry Pi 5", "source/models/yolo/", ORANGE),
             ("주행 코드", "YoloEventDetector", GREEN)]
    for i, (n1, n2, col) in enumerate(nodes):
        a = prog(t, m[2] + i * 0.7, 0.5)
        x = 80 + i * 400
        if a <= 0:
            continue
        rrect(d, (x, 450, x + 320, 560), fill=fade(PANEL, a), outline=fade(col, a), w=3)
        text_c(d, x + 160, 465, n1, font(26, "b"), fade(col, a))
        text_c(d, x + 160, 510, n2, font(19, "m"), fade(TXT, a))
        if i > 0:
            arrow(d, (x - 75, 505), (x - 8, 505), fade(TXT, a), 4)
    a = prog(t, m[2] + 0.4, 0.5)
    if a > 0:
        draw_mono(d, 330, 418, "scp models/best.pt pi@raspberrypi.local:...", 15, MUTED, alpha=a)


# ---------------- 14. 개선 루프
@scene("TIP", "점수가 낮을 때 — 개선 루프", chapter="개선 방법")
@narr(S("점수가 낮다면 원인에 따라 처방이 다릅니다."),
      S("놓치는 게 많으면 그 상황의 데이터를 더 모으고, 오탐이 많으면 헷갈리는 배경 이미지를 추가합니다."),
      S("박스 위치가 부정확하면 라벨을 더 타이트하게 다시 그리고, 전체적으로 낮으면 학습을 더 길게, 모델을 더 크게 합니다."))
def sc_loop(img, d, t, m, T):
    rows = [("Recall ↓  (놓침)", "원거리 · 역광 · 흐린 장면 데이터 추가 수집", m[1], ORANGE),
            ("Precision ↓  (오탐)", "헷갈리는 배경을 빈 라벨로 추가 (hard negative)", m[1] + 1.8, RED),
            ("mAP50-95 만 ↓", "박스를 더 타이트하게 다시 라벨링", m[2], PURPLE),
            ("전체적으로 ↓", "epochs ↑ · yolo11s · imgsz ↑", m[2] + 2.5, BLUE)]
    for i, (p_, r_, st, col) in enumerate(rows):
        a = prog(t, st, 0.5)
        y = 130 + i * 105
        if a <= 0:
            continue
        rrect(d, (60, y, 470, y + 80), fill=fade(PANEL, a), outline=fade(col, a), w=3)
        text_c(d, 265, y + 22, p_, font(26, "b"), fade(col, a))
        arrow(d, (485, y + 40), (560, y + 40), fade(TXT, a), 4)
        rrect(d, (575, y, 1220, y + 80), fill=fade(PANEL, a), outline=fade(PANEL2, a))
        d.text((600, y + 24), r_, font=font(24, "m"), fill=fade(TXT, a))


# ---------------- 15. 한 번에 실행
@scene("RUN", "라벨링 후에는 명령 하나로", chapter="자동 실행")
@narr(S("라벨링이 끝났다면 run_pipeline 명령 하나로 3단계부터 9단계까지 자동으로 실행됩니다.",
        "라벨링이 끝났다면 런 파이프라인 명령 하나로 3단계부터 9단계까지 자동으로 실행됩니다."),
      S("실제 데이터가 없어도 데모 옵션으로 가상 데이터를 만들어 전체 과정을 체험할 수 있습니다."))
def sc_run(img, d, t, m, T):
    lines = [("python run_pipeline.py --demo", YELLOW, "cmd"), ("", TXT, "out"),
             ("================================================", MUTED, "out"),
             ("  파이프라인 요약", TXT, "out"),
             ("================================================", MUTED, "out"),
             ("  ✅ 3단계 라벨 점검          OK          0.6s", TXT, "out"),
             ("  ✅ 4단계 데이터셋 분할      OK          0.3s", TXT, "out"),
             ("  ✅ 5단계 학습              OK        115.9s", TXT, "out"),
             ("  ✅ 6단계 검증 (val)        OK          3.3s", TXT, "out"),
             ("  ✅ 6단계 최종 시험 (test)  OK          3.0s", TXT, "out"),
             ("  ✅ 7단계 운영조건 테스트   OK          2.1s", TXT, "out"),
             ("  ✅ 9단계 배포 변환         OK          4.9s", TXT, "out")]
    terminal(d, (140, 110, 1140, 590), lines, t, start=0.8, size=19, cps=22, line_gap=1.6)
    if t > m[1]:
        a = prog(t, m[1], 0.5)
        rrect(d, (760, 515, 1120, 570), fill=fade(PANEL2, a), outline=fade(CYAN, a), r=10)
        d.text((780, 527), "가상 데이터 240장 · 약 2분", font=font(22, "b"), fill=fade(CYAN, a))


# ---------------- 16. 마무리
@scene("SUMMARY", "정리", chapter="정리")
@narr(S("정리하면, 좋은 데이터와 정확한 라벨, 그리고 꼼꼼한 검증이 좋은 모델을 만듭니다."),
      S("자세한 내용은 README와 docs 폴더의 가이드를 참고하세요. 감사합니다.",
        "자세한 내용은 리드미와 닥스 폴더의 가이드를 참고하세요. 감사합니다."))
def sc_outro(img, d, t, m, T):
    items = ["다양한 조건의 데이터 수집", "타이트하고 빠짐없는 라벨", "라벨 점검 ERROR 0",
             "동영상 단위 train / val / test 분할", "검증 PASS → 운영 조건 테스트", "변환 후 일치율 확인 → 배포"]
    bullet_list(d, 140, 130, items, t, [0.4 + i * 0.5 for i in range(6)], size=28, gap=58, icon="✓",
                icon_color=GREEN)
    a = prog(t, m[1], 0.6)
    if a > 0:
        rrect(d, (140, 500, 1140, 580), fill=fade(PANEL, a), outline=fade(CYAN, a))
        text_c(d, 640, 520, "README.md  ·  docs/01_라벨링_가이드.md  ·  docs/02_검증_테스트_가이드.md",
               font(22, "m"), fade(CYAN, a))


# ------------------------------------------------------------------ 공통 프레임 요소
def base_frame(sc) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    if sc["title"]:
        col = STEP_COLORS[sc["step"]] if sc["step"] else CYAN
        tw = d.textlength(sc["chip"], font=font(18, "b"))
        rrect(d, (40, 30, 40 + tw + 28, 66), fill=col, r=18)
        d.text((54, 36), sc["chip"], font=font(18, "b"), fill=BG)
        d.text((40 + tw + 46, 28), sc["title"], font=font(32, "b"), fill=TXT)
    for i in range(9):   # 단계 진행 표시
        x = 1000 + i * 24
        cur = sc["step"] == i + 1
        doneish = sc["step"] and i + 1 < sc["step"]
        col = STEP_COLORS[i + 1] if (cur or doneish) else PANEL2
        r = 8 if cur else 5
        d.ellipse((x - r, 48 - r, x + r, 48 + r), fill=col)
    return img


def caption_img(text: str) -> Image.Image:
    f = font(27, "m")
    lines = wrap(text, f, W - 160)[:3]
    h = 30 + len(lines) * 38
    cap = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(cap)
    d.rectangle((0, 0, W, h), fill=(2, 6, 23, 225))
    for i, ln in enumerate(lines):
        x = (W - d.textlength(ln, font=f)) / 2
        d.text((x + 1, 15 + i * 38 + 1), ln, font=f, fill=(0, 0, 0, 255))
        d.text((x, 15 + i * 38), ln, font=f, fill=(255, 255, 255, 255))
    return cap


# ------------------------------------------------------------------ 오디오 (macOS say)
def synth(text: str, out: Path, voice: str, rate: int) -> float:
    aiff = out.with_suffix(".aiff")
    subprocess.run(["say", "-v", voice, "-r", str(rate), "-o", str(aiff), text], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(aiff), "-ar", "24000", "-ac", "1",
                    "-sample_fmt", "s16", str(out)], check=True)
    aiff.unlink()
    with wave.open(str(out)) as w:
        return w.getnframes() / w.getframerate()


def build_timeline(work: Path, voice: str, rate: int, use_tts: bool):
    timeline = []      # 장면별 {start, dur, marks[], clips[(path, t)]}
    cursor_t = 0.0
    for si, sc in enumerate(SCENES):
        marks, clips, t = [], [], 0.6
        for li, (cap, speech) in enumerate(sc["lines"]):
            marks.append(t)
            if use_tts:
                wav = work / f"s{si:02d}_{li:02d}.wav"
                dur = synth(speech, wav, voice, rate)
                clips.append((wav, cursor_t + t))
            else:
                dur = max(2.5, len(cap) * 0.11)
            t += dur + GAP
        total = t + TAIL
        timeline.append({"start": cursor_t, "dur": total, "marks": marks, "clips": clips})
        cursor_t += total
        print(f"  장면 {si:2d} {sc['chapter']:<14} {total:5.1f}s")
    return timeline, cursor_t


def mix_audio(timeline, total, out: Path, sr=24000):
    buf = np.zeros(int((total + 1) * sr), np.int16)
    for tl in timeline:
        for wav, start in tl["clips"]:
            with wave.open(str(wav)) as w:
                data = np.frombuffer(w.readframes(w.getnframes()), np.int16)
            s = int(start * sr)
            buf[s:s + len(data)] = data[: len(buf) - s]
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(buf.tobytes())


def srt_time(s):
    ms = int(round(s * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(timeline, path: Path):
    out, n = [], 1
    for sc, tl in zip(SCENES, timeline):
        ends = tl["marks"][1:] + [tl["dur"] - TAIL + 0.3]
        for (cap, _), st, en in zip(sc["lines"], tl["marks"], ends):
            out += [str(n), f"{srt_time(tl['start'] + st)} --> {srt_time(tl['start'] + en - 0.05)}", cap, ""]
            n += 1
    path.write_text("\n".join(out), encoding="utf-8")


def write_chapters(timeline, path: Path):
    lines = [";FFMETADATA1", "title=YOLO11 학습 튜토리얼 (라벨링부터 배포까지)"]
    for sc, tl in zip(SCENES, timeline):
        lines += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={int(tl['start'] * 1000)}",
                  f"END={int((tl['start'] + tl['dur']) * 1000)}", f"title={sc['chapter']}"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ------------------------------------------------------------------ 렌더링
def render_scene_frame(si, t, tl, base, caps):
    sc = SCENES[si]
    img = base.copy()
    d = ImageDraw.Draw(img)
    sc["draw"](img, d, t, tl["marks"], tl["dur"])
    idx = max([i for i, mk in enumerate(tl["marks"]) if mk <= t] or [-1])
    if idx >= 0:
        cap = caps[idx]
        img.paste(cap, (0, H - cap.height), cap)
    # 장면 전환 페이드
    k = min(1.0, t / 0.35, (tl["dur"] - t) / 0.35)
    if k < 1:
        img = Image.blend(Image.new("RGB", (W, H), BG), img, max(0.0, k))
    return img


def load_assets():
    req = [DEMO / "runs/train/demo_yolo11/results.csv", DEMO / "reports/validate_val.json",
           DEMO / "reports/test_test.json", DEMO / "labeled/images"]
    missing = [str(p) for p in req if not p.exists()]
    if missing:
        sys.exit("[ERROR] 데모 결과가 없습니다. 먼저 `python run_pipeline.py --demo` 를 실행하세요.\n  " + "\n  ".join(missing))
    A.icons = [class_icon(i) for i in range(5)]
    imgs = sorted((DEMO / "labeled/images").glob("*.jpg"))
    A.thumbs = [Image.open(p).convert("RGB").resize((160, 120), Image.LANCZOS) for p in imgs[1:41]]
    A.label_img = Image.open(DEMO / "labeled/images/demo_0011.jpg").convert("RGB")
    boxes = []
    for line in (DEMO / "labeled/labels/demo_0011.txt").read_text().split("\n"):
        if line.strip():
            c, xc, yc, w, h = line.split()
            c, xc, yc, w, h = int(c), float(xc), float(yc), float(w), float(h)
            boxes.append((c, xc - w / 2, yc - h / 2, xc + w / 2, yc + h / 2))
    A.label_boxes = boxes
    A.results = load_results_csv()
    A.val = load_json(DEMO / "reports/validate_val.json", {})
    A.test = load_json(DEMO / "reports/test_test.json", {})
    A.pred = load_img(DEMO / "runs/train/demo_yolo11/val_batch0_pred.jpg")
    pv = sorted((DEMO / "reports/label_preview").glob("*.jpg"))
    A.preview = load_img(pv[0]) if pv else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(ROOT / "docs/video/YOLO11_학습_튜토리얼.mp4"))
    ap.add_argument("--voice", default="Yuna")
    ap.add_argument("--rate", type=int, default=185, help="말하기 속도 (say -r)")
    ap.add_argument("--no-tts", action="store_true", help="나레이션 없이 자막만")
    ap.add_argument("--preview", type=int, nargs="*", help="장면 번호의 미리보기 PNG 만 저장")
    args = ap.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("[ERROR] ffmpeg 가 필요합니다 (brew install ffmpeg)")
    use_tts = not args.no_tts and shutil.which("say") is not None
    if not use_tts and not args.no_tts:
        print("  [WARN] macOS say 명령이 없어 자막만 있는 무음 영상으로 만듭니다.")
    load_assets()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    work = DEMO / "_video_build"
    work.mkdir(parents=True, exist_ok=True)

    if args.preview is not None:   # 빠른 미리보기 (각 장면의 문장 시작 + 2.5초 시점)
        ids = args.preview or range(len(SCENES))
        for si in ids:
            sc = SCENES[si]
            marks, t = [], 0.6
            for cap, _ in sc["lines"]:
                marks.append(t)
                t += max(2.5, len(cap) * 0.11) + GAP
            tl = {"marks": marks, "dur": t + TAIL}
            base = base_frame(sc)
            caps = [caption_img(c) for c, _ in sc["lines"]]
            render_scene_frame(si, min(t - 0.5, marks[-1] + 2.5), tl, base, caps).save(work / f"preview_{si:02d}.png")
        print(f"  미리보기 저장: {work}")
        return

    print("[1/3] 나레이션 합성")
    timeline, total = build_timeline(work, args.voice, args.rate, use_tts)
    audio = work / "narration.wav"
    if use_tts:
        mix_audio(timeline, total, audio)
    print(f"  총 길이: {total / 60:.1f} 분")

    print("[2/3] 프레임 렌더링 + 인코딩")
    meta = work / "chapters.txt"
    write_chapters(timeline, meta)
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-"]
    if use_tts:
        cmd += ["-i", str(audio)]
    cmd += ["-i", str(meta), "-map", "0:v"] + (["-map", "1:a"] if use_tts else []) + \
           ["-map_metadata", str(2 if use_tts else 1), "-map_chapters", str(2 if use_tts else 1),
            "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-pix_fmt", "yuv420p", "-tune", "animation"]
    if use_tts:
        cmd += ["-c:a", "aac", "-b:a", "128k"]
    cmd += ["-movflags", "+faststart", "-t", f"{total:.2f}", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for si, (sc, tl) in enumerate(zip(SCENES, timeline)):
        base = base_frame(sc)
        caps = [caption_img(c) for c, _ in sc["lines"]]
        nf = int(round(tl["dur"] * FPS))
        for f in range(nf):
            proc.stdin.write(render_scene_frame(si, f / FPS, tl, base, caps).tobytes())
        print(f"  장면 {si + 1}/{len(SCENES)} 완료", end="\r")
    proc.stdin.close()
    if proc.wait() != 0:
        sys.exit("[ERROR] ffmpeg 인코딩 실패")

    print("\n[3/3] 자막 파일")
    srt = out.with_suffix(".srt")
    write_srt(timeline, srt)
    print(f"  영상: {out}  ({out.stat().st_size / 1e6:.1f} MB, {total / 60:.1f} 분)")
    print(f"  자막: {srt}")


if __name__ == "__main__":
    main()
