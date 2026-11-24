"""
20시간 교육과정 — 차시별 소개 영상 (1920x1080, 30fps)

- 상단: 차시별 진행 상황 체크 바 (완료 ✓ · 진행 중 · 예정) + 누적 시간
- 장면: 인트로 → 1~6차시 → 마무리 (차시별 커스텀 일러스트 + 동적 구조도)
- 3차시: 커스텀 카메라 이미지에 실제 ROI 처리(HSV 마스크 · 좌/중/우 비율) 애니메이션
- 4차시: YOLO11 파이프라인 + 검출 박스 애니메이션 + best.pt 실제 학습 곡선(mAP50)
- 나레이션: Higgsfield MiniMax 'Hana' (assets/narration/NN.mp3), 속도 TEMPO 배

사용 예:
  python3 make_session_video.py            # 영상 생성
  python3 make_session_video.py --stills   # 장면별 대표 PNG만 (stills_v2/)
필요: Pillow, numpy, ffmpeg
"""
from __future__ import annotations

import argparse
import math
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
ASSETS = HERE / "assets"
CUSTOM = ASSETS / "custom"
NARR = ASSETS / "narration"
OUT = HERE / "20시간_교육과정_차시별_소개.mp4"
STILLS = HERE / "stills_v2"

W, H, FPS = 1920, 1080, 30
TEMPO = 1.12      # 나레이션 재생 속도 (음높이 유지)
LEAD = 0.55       # 장면 시작 → 나레이션 시작
TAIL = 1.0        # 나레이션 끝 → 장면 끝
FADE = 0.45       # 장면 간 크로스페이드

# ------------------------------------------------------------------ 색 · 폰트
BG = (10, 15, 30)
PANEL = (20, 30, 54)
PANEL2 = (28, 42, 72)
TODO = (17, 25, 44)
LINE = (56, 74, 110)
WHITE = (255, 255, 255)
MUTED = (148, 163, 188)
YEL = (255, 214, 10)
CYAN = (56, 220, 255)
GREEN = (74, 222, 128)
RED = (255, 92, 92)
ORANGE = (255, 159, 67)
PURPLE = (180, 140, 255)
BLUE = (96, 165, 250)

SD = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
MONO = "/System/Library/Fonts/Menlo.ttc"
_F: dict = {}


def F(size, w="b"):
    key = (size, w)
    if key not in _F:
        if w == "mono":
            _F[key] = ImageFont.truetype(MONO, size, index=1)
        else:
            _F[key] = ImageFont.truetype(SD, size, index={"r": 0, "m": 2, "s": 4, "b": 6}[w])
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


def ap(t, start, dur=0.45):
    return ease((t - start) / dur)


def cue(x):
    """나레이션 원본 시각(초) → 장면 시각(초)."""
    return LEAD + x / TEMPO


def mix(c, k, bg=BG):
    k = clamp(k)
    return tuple(int(bg[i] + (c[i] - bg[i]) * k) for i in range(3))


def rgba(c, a):
    return (*c, int(255 * clamp(a)))


# ------------------------------------------------------------------ 그리기 도우미
def tw(d, s, f):
    return d.textlength(s, font=f)


def ctext(d, cx, y, s, f, fill):
    d.text((cx - tw(d, s, f) / 2, y), s, font=f, fill=fill)


def rbox(d, xy, fill=PANEL, outline=LINE, r=20, width=3):
    d.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)


def arrow(d, p1, p2, color, width=6, head=18):
    (x1, y1), (x2, y2) = p1, p2
    d.line([p1, p2], fill=color, width=width)
    ang = math.atan2(y2 - y1, x2 - x1)
    a1, a2 = ang + math.radians(150), ang - math.radians(150)
    d.polygon([(x2, y2), (x2 + head * math.cos(a1), y2 + head * math.sin(a1)),
               (x2 + head * math.cos(a2), y2 + head * math.sin(a2))], fill=color)


def grow_arrow(d, p1, p2, k, color, width=6, head=18):
    if k <= 0.02:
        return
    (x1, y1), (x2, y2) = p1, p2
    arrow(d, p1, (x1 + (x2 - x1) * k, y1 + (y2 - y1) * k), color, width, head)


def packet(d, p1, p2, t, color, n=3, speed=0.8, r=9):
    (x1, y1), (x2, y2) = p1, p2
    for j in range(n):
        p = (t * speed + j / n) % 1
        x, y = x1 + (x2 - x1) * p, y1 + (y2 - y1) * p
        d.ellipse((x - r, y - r, x + r, y + r), fill=color)


def check(d, cx, cy, s, color, width=6, k=1.0):
    """체크 표시 (k: 그려지는 정도)."""
    pts = [(cx - s * .5, cy), (cx - s * .12, cy + s * .38), (cx + s * .55, cy - s * .4)]
    if k <= 0:
        return
    if k < 0.45:
        q = k / 0.45
        d.line([pts[0], (pts[0][0] + (pts[1][0] - pts[0][0]) * q, pts[0][1] + (pts[1][1] - pts[0][1]) * q)],
               fill=color, width=width)
    else:
        q = (k - 0.45) / 0.55
        d.line([pts[0], pts[1], (pts[1][0] + (pts[2][0] - pts[1][0]) * q, pts[1][1] + (pts[2][1] - pts[1][1]) * q)],
               fill=color, width=width, joint="curve")


def glow_rect(cv, xy, color, strength=1.0, r=24, blur=14):
    pad = blur * 3
    x1, y1, x2, y2 = [int(v) for v in xy]
    layer = Image.new("RGBA", (x2 - x1 + pad * 2, y2 - y1 + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle((pad, pad, pad + x2 - x1, pad + y2 - y1), radius=r,
                                            outline=rgba(color, 0.9 * strength), width=8)
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    cv.alpha_composite(layer, (x1 - pad, y1 - pad))


# ------------------------------------------------------------------ 이미지 (캐시)
_BASE: dict = {}


def base(path):
    p = str(path)
    if p not in _BASE:
        _BASE[p] = Image.open(path).convert("RGB")
    return _BASE[p]


def fit_cover(im, size):
    tw_, th_ = size
    s = max(tw_ / im.width, th_ / im.height)
    im = im.resize((max(1, int(im.width * s + 0.5)), max(1, int(im.height * s + 0.5))), Image.BILINEAR)
    x, y = (im.width - tw_) // 2, (im.height - th_) // 2
    return im.crop((x, y, x + tw_, y + th_))


def round_alpha(im, radius, alpha=1.0):
    im = im.convert("RGBA")
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, *im.size), radius=radius, fill=int(255 * clamp(alpha)))
    im.putalpha(m)
    return im


def kb(path_or_im, size, t, dur, zoom=0.06, pan=(0.0, 0.0)):
    """Ken Burns: 시간에 따라 천천히 확대·이동."""
    src = base(path_or_im) if not isinstance(path_or_im, Image.Image) else path_or_im
    k = clamp(t / max(dur, 0.1))
    z = 1 + zoom * k
    tw_, th_ = size
    s = max(tw_ / src.width, th_ / src.height) * z
    cw, ch = tw_ / s, th_ / s
    cx = (src.width - cw) / 2 + pan[0] * k * (src.width - cw) / 2
    cy = (src.height - ch) / 2 + pan[1] * k * (src.height - ch) / 2
    return src.resize(size, Image.BILINEAR, box=(cx, cy, cx + cw, cy + ch))


def paste(cv, im, xy, alpha=1.0, radius=18):
    if alpha <= 0:
        return
    cv.alpha_composite(round_alpha(im, radius, alpha), (int(xy[0]), int(xy[1])))


def frame_img(cv, d, im, xy, k, color=LINE, radius=18, label=None):
    """사진 + 테두리 + 아래 라벨 (등장 애니메이션 포함)."""
    if k <= 0:
        return
    x, y = xy[0], xy[1] + (1 - k) * 40
    paste(cv, im, (x, y), k, radius)
    d.rounded_rectangle((x, y, x + im.width, y + im.height), radius=radius, outline=mix(color, k), width=3)
    if label:
        d.text((x + 6, y + im.height + 12), label, font=F(26, "m"), fill=mix(MUTED, k))


# ------------------------------------------------------------------ 배경 (움직이는 격자)
_GRID = None


def background(cv, gt):
    global _GRID
    if _GRID is None:
        g = Image.new("RGBA", (W + 120, H + 120), (0, 0, 0, 0))
        gd = ImageDraw.Draw(g)
        for x in range(0, W + 120, 60):
            gd.line((x, 0, x, H + 120), fill=(40, 60, 100, 38), width=1)
        for y in range(0, H + 120, 60):
            gd.line((0, y, W + 120, y), fill=(40, 60, 100, 38), width=1)
        for x in range(0, W + 120, 60):
            for y in range(0, H + 120, 60):
                gd.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(70, 100, 160, 70))
        _GRID = g
    o = (gt * 12) % 60
    cv.alpha_composite(_GRID.crop((int(o), int(o), int(o) + W, int(o) + H)))


# ------------------------------------------------------------------ 상단: 차시별 진행 체크
SESS = [
    ("조립 · 앱 실행", "11/26 목", 4),
    ("개발환경 · 제어", "11/27 금", 3),
    ("ROI 자율주행", "12/2 수", 3),
    ("YOLO11 학습", "12/3 목", 4),
    ("통합 주행", "12/4 금", 3),
    ("최종 테스트", "12/7 월", 3),
]
SCOL = [WHITE, CYAN, RED, YEL, GREEN, ORANGE]


def tracker(cv, d, cur, prog, t, intro=None, finale=None):
    """cur: 진행 중 차시(1~6), 0=시작 전, 7=모두 완료. prog: 현재 차시 진행률."""
    x0, x1, y, h, gap = 70, 1850, 24, 78, 16
    pw = (x1 - x0 - gap * 5) / 6
    for i, (name, date, hrs) in enumerate(SESS):
        n = i + 1
        k = 1.0 if intro is None else back((t - intro - i * 0.16) / 0.5)
        if k <= 0:
            continue
        x = x0 + i * (pw + gap)
        yy = y + (1 - clamp(k)) * -30
        done = n < cur or cur == 7
        now = n == cur
        if finale is not None and cur == 7:
            done = t >= finale + i * 0.18
            now = False
        if done:
            rbox(d, (x, yy, x + pw, yy + h), fill=mix((22, 70, 52), k), outline=mix(GREEN, k), r=39, width=3)
            d.ellipse((x + 14, yy + 13, x + 66, yy + 65), fill=mix(GREEN, k, (22, 70, 52)))
            ck = 1.0 if finale is None else ap(t, finale + i * 0.18, 0.4)
            check(d, x + 40, yy + 39, 28, BG, 6, ck)
            tc, sc = mix(WHITE, k, (22, 70, 52)), mix((170, 230, 200), k, (22, 70, 52))
        elif now:
            pulse = 0.55 + 0.45 * math.sin(t * 4.2)
            glow_rect(cv, (x, yy, x + pw, yy + h), SCOL[i], 0.8 * pulse, r=39, blur=10)
            d = ImageDraw.Draw(cv)
            rbox(d, (x, yy, x + pw, yy + h), fill=PANEL2, outline=SCOL[i], r=39, width=4)
            # 진행률 바 (알약 내부 하단)
            bx1, bx2 = x + 80, x + pw - 30
            d.rounded_rectangle((bx1, yy + h - 11, bx2, yy + h - 6), radius=2, fill=(45, 60, 92))
            d.rounded_rectangle((bx1, yy + h - 11, bx1 + (bx2 - bx1) * clamp(prog), yy + h - 6), radius=2,
                                fill=SCOL[i])
            d.ellipse((x + 14, yy + 13, x + 66, yy + 65), fill=SCOL[i])
            ctext(d, x + 40, yy + 17, str(n), F(32, "b"), BG)
            tc, sc = WHITE, SCOL[i]
        else:
            rbox(d, (x, yy, x + pw, yy + h), fill=mix(TODO, k), outline=mix(LINE, k), r=39, width=2)
            d.ellipse((x + 14, yy + 13, x + 66, yy + 65), outline=mix(LINE, k), width=3)
            ctext(d, x + 40, yy + 17, str(n), F(32, "b"), mix(MUTED, k))
            tc, sc = mix(MUTED, k), mix((100, 115, 140), k)
        d.text((x + 80, yy + 6), name, font=F(27, "b"), fill=tc)
        d.text((x + 80, yy + 39), f"{n}차시 · {date} · {hrs}H", font=F(20, "m"), fill=sc)
    # 누적 시간
    hours = [s[2] for s in SESS]
    if cur == 0:
        acc = 0.0
    elif cur == 7:
        acc = 20.0
    else:
        acc = sum(hours[:cur - 1]) + hours[cur - 1] * clamp(prog)
    k = 1.0 if intro is None else ap(t, intro + 1.0)
    yb = 116
    d.rounded_rectangle((x0, yb, x1 - 230, yb + 6), radius=3, fill=mix((34, 46, 72), k))
    if acc > 0:
        d.rounded_rectangle((x0, yb, x0 + (x1 - 230 - x0) * acc / 20, yb + 6), radius=3, fill=mix(YEL, k))
    s = f"누적 {acc:4.1f}H / 20H"
    d.text((x1 - tw(d, s, F(24, "b")), yb - 12), s, font=F(24, "b"), fill=mix(YEL, k))


def scene_head(d, t, n, title):
    k = ap(t, 0.05)
    col = SCOL[n - 1]
    name, date, hrs = SESS[n - 1]
    tag = f"{n}차시 · {date} · {hrs}H"
    f = F(28, "b")
    w = tw(d, tag, f) + 40
    x = 70 - (1 - k) * 40
    d.rounded_rectangle((x, 156, x + w, 204), radius=24, fill=mix(col, k))
    d.text((x + 20, 163), tag, font=f, fill=BG)
    d.text((x + w + 24, 146), title, font=F(52, "b"), fill=mix(WHITE, k))


def caption(cv, d, text, k):
    if k <= 0:
        return
    f = F(38, "s")
    w = tw(d, text, f)
    pad = 32
    x1, y1 = (W - w) / 2 - pad, 972
    ov = Image.new("RGBA", (int(w + pad * 2), 68), (0, 0, 0, 0))
    ImageDraw.Draw(ov).rounded_rectangle((0, 0, w + pad * 2, 67), radius=16, fill=(0, 0, 0, int(175 * k)))
    cv.alpha_composite(ov, (int(x1), y1))
    d.text(((W - w) / 2, y1 + 11), text, font=f, fill=(255, 255, 255, int(255 * k)))


def check_list(cv, d, items, x, y, t, starts, col, w=720, h=88, gap=18):
    for i, (a, b) in enumerate(items):
        k = ap(t, starts[i] - 0.5, 0.5)
        if k <= 0:
            continue
        yy = y + i * (h + gap)
        xx = x + (1 - k) * 60
        done = ap(t, starts[i], 0.5)
        rbox(d, (xx, yy, xx + w, yy + h), fill=mix(PANEL2, k), outline=mix(col if done > 0.5 else LINE, k), r=18)
        d.ellipse((xx + 20, yy + 20, xx + 68, yy + 68), outline=mix(col, k, PANEL2), width=3,
                  fill=mix(col, done, PANEL2) if done > 0 else None)
        check(d, xx + 44, yy + 44, 26, BG, 5, done)
        d.text((xx + 90, yy + 12), a, font=F(36, "b"), fill=mix(WHITE, k, PANEL2))
        d.text((xx + 90, yy + 54), b, font=F(24, "m"), fill=mix(MUTED, k, PANEL2))


# ================================================================== 3차시용 실제 ROI 처리
ROI_Y = (330, 600)


def roi_process():
    im = base(CUSTOM / "s3_lane_cam.png")
    hsv = np.asarray(im.convert("HSV")).astype(int)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    red = ((h < 14) | (h > 235)) & (s > 110) & (v > 90)
    gray = (s < 38) & (v > 140)
    mask = red | gray
    y0, y1 = ROI_Y
    roi = mask[y0:y1]
    wdt = roi.shape[1]
    cnt = [int(roi[:, i * wdt // 3:(i + 1) * wdt // 3].sum()) for i in range(3)]
    tot = max(1, sum(cnt))
    ratio = [c / tot for c in cnt]
    m = np.zeros((*mask.shape, 3), np.uint8)
    m[y0:y1][roi[...]] = (255, 255, 255)
    # 좌측 차선이 많으면 오른쪽으로 조향 (실제 디버깅 화면: L 99% → Dir: RIGHT)
    if ratio[0] - ratio[2] > 0.3:
        dec = "RIGHT"
    elif ratio[2] - ratio[0] > 0.3:
        dec = "LEFT"
    else:
        dec = "UP"
    return Image.fromarray(m), ratio, dec


ROI_MASK, ROI_RATIO, ROI_DEC = None, None, None

# ================================================================== 장면
IMG_W, IMG_H = 1040, 582   # 16:9 이미지 슬롯
IX, IY = 70, 250


def sc_intro(cv, d, t, dur):
    tracker(cv, d, 0, 0, t, intro=cue(6.0))
    d = ImageDraw.Draw(cv)
    k = ap(t, 0.0, 0.8)
    paste(cv, kb(REPO / "09_yolo11_pipeline/demo/shorts/illust/raspi.png", (640, 640), t, dur, 0.06), (120, 250 + (1 - k) * 30), k, 32)
    x = 860
    k1, k2, k3 = ap(t, 0.3), ap(t, 0.8), ap(t, 1.4)
    d.text((x - (1 - k1) * 40, 270), "Raspbot V2 자율주행", font=F(92, "b"), fill=mix(WHITE, k1))
    d.text((x - (1 - k2) * 40, 390), "컴퓨터 비전 개발 프로세스 20시간", font=F(54, "b"), fill=mix(CYAN, k2))
    flow = [("ROI 도로선", RED), ("YOLO11 인식", YEL), ("통합 주행", GREEN)]
    xx = x
    for i, (s, col) in enumerate(flow):
        kk = back((t - 1.4 - i * 0.25) / 0.5)
        if kk <= 0:
            continue
        f = F(38, "b")
        w = tw(d, s, f) + 48
        rbox(d, (xx, 500, xx + w, 570), fill=mix(PANEL2, clamp(kk)), outline=mix(col, clamp(kk)), r=35, width=4)
        d.text((xx + 24, 511), s, font=f, fill=mix(col, clamp(kk)))
        if i < 2:
            grow_arrow(d, (xx + w + 8, 535), (xx + w + 50, 535), ap(t, 1.7 + i * 0.25), MUTED, 4, 12)
        xx += w + 60
    # 크로스 개발 한 줄
    k4 = ap(t, 2.4)
    rbox(d, (x, 620, x + 900, 740), fill=mix(PANEL, k4), outline=mix(LINE, k4), r=20)
    d.text((x + 30, 638), "PC", font=F(40, "b"), fill=mix(CYAN, k4))
    d.text((x + 30, 690), "코드 · 데이터 · 학습 · 검증", font=F(24, "m"), fill=mix(MUTED, k4))
    d.text((x + 640, 638), "Raspbot V2", font=F(40, "b"), fill=mix(GREEN, k4))
    d.text((x + 640, 690), "실행 · 주행", font=F(24, "m"), fill=mix(MUTED, k4))
    grow_arrow(d, (x + 400, 680), (x + 610, 680), ap(t, 2.7, 0.6), YEL, 6, 16)
    if k4 >= 1:
        packet(d, (x + 410, 680), (x + 600, 680), t, YEL, 3, 0.9, 7)
    d.text((x + 420, 630), "크로스 개발", font=F(26, "b"), fill=mix(YEL, k4))
    d.text((x, 790), "아래에서 차시별로 무엇을 하는지 살펴봅니다  ▼", font=F(30, "m"), fill=mix(MUTED, ap(t, cue(6.0))))


def sc_s1(cv, d, t, dur):
    tracker(cv, d, 1, t / dur, t)
    d = ImageDraw.Draw(cv)
    scene_head(d, t, 1, "간단 조립 · 앱으로 실행")
    frame_img(cv, d, kb(CUSTOM / "s1_assembly.png", (IMG_W, IMG_H), t, dur, 0.08, (-0.3, 0.2)), (IX, IY),
              ap(t, 0.2, 0.6), WHITE, label="부품 확인 → 조립 → 전원 → 앱 주행")
    items = [("부품 확인", "모터 · 보드 · 카메라 · 배터리"), ("차체 · 모터 · 보드 조립", "매뉴얼 순서대로"),
             ("전원 ON · 부팅", "배선 점검 후 전원 인가"), ("앱으로 첫 주행", "전/후/좌/우 · 카메라 화면")]
    check_list(cv, d, items, 1150, IY, t, [cue(3.5), cue(4.8), cue(6.0), cue(6.9)], WHITE, w=700)
    k = ap(t, cue(7.5))
    d.text((1150, IY + 4 * 106 + 10), "통과 조건: 앱으로 트랙 1바퀴", font=F(30, "b"), fill=mix(YEL, k))


def sc_s2(cv, d, t, dur):
    tracker(cv, d, 2, t / dur, t)
    d = ImageDraw.Draw(cv)
    scene_head(d, t, 2, "동작 원리 · 개발환경 · 제어 테스트")
    frame_img(cv, d, kb(CUSTOM / "s2_crossdev.png", (820, 459), t, dur, 0.07), (IX, IY), ap(t, 0.2, 0.6), CYAN,
              label="PC에서 작성 → 라즈봇에서 실행 (크로스 개발)")
    # 구조도: PC → Pi → I2C → 쉴드 → 모터/서보/센서
    x0 = 950
    nodes = [("PC", "VS Code · SSH · VNC · FTP", CYAN, cue(4.1)),
             ("Raspberry Pi", "Python 코드 실행", GREEN, cue(5.6)),
             ("Raspbot 쉴드 MCU", "I2C 명령 수신", YEL, cue(7.4))]
    for i, (a, b, col, st) in enumerate(nodes):
        k = ap(t, st - 0.4, 0.5)
        if k <= 0:
            continue
        y = IY + i * 160
        rbox(d, (x0, y, x0 + 480, y + 110), fill=mix(PANEL2, k), outline=mix(col, k), r=18, width=3)
        d.text((x0 + 28, y + 14), a, font=F(38, "b"), fill=mix(col, k, PANEL2))
        d.text((x0 + 28, y + 64), b, font=F(24, "m"), fill=mix(MUTED, k, PANEL2))
        if i < 2:
            ka = ap(t, nodes[i + 1][3] - 0.5, 0.5)
            grow_arrow(d, (x0 + 240, y + 112), (x0 + 240, y + 156), ka, col, 5, 14)
            lab = "Wi-Fi · SSH" if i == 0 else "I2C"
            d.text((x0 + 260, y + 116), lab, font=F(22, "b"), fill=mix(col, ka))
            if ka >= 1:
                packet(d, (x0 + 240, y + 114), (x0 + 240, y + 150), t, col, 2, 1.2, 6)
    # 출력 장치
    outs = [("모터", ORANGE, cue(9.3)), ("서보", ORANGE, cue(9.9)), ("센서", PURPLE, cue(10.9))]
    for i, (s, col, st) in enumerate(outs):
        k = back((t - st) / 0.45)
        if k <= 0:
            continue
        bx = 1610
        yy = IY + 300 + (i - 1) * 110
        rbox(d, (bx, yy, bx + 240, yy + 84), fill=mix(PANEL2, clamp(k)), outline=mix(col, clamp(k)), r=42, width=3)
        ctext(d, bx + 120, yy + 18, s, F(38, "b"), mix(WHITE, clamp(k), PANEL2))
        grow_arrow(d, (x0 + 484, IY + 375), (bx - 8, yy + 42), ap(t, st, 0.4), mix(col, 0.9), 4, 14)
        if ap(t, st, 0.4) >= 1:
            packet(d, (x0 + 490, IY + 375), (bx - 14, yy + 42), t + i * 0.3, col, 2, 1.0, 6)
    # 02_Basic 테스트 칩
    chips = ["부저", "RGB", "서보", "모터", "초음파", "라인센서", "카메라"]
    k0 = ap(t, cue(10.9) + 0.3)
    d.text((IX, 790), "02_Basic 동작 테스트", font=F(28, "b"), fill=mix(WHITE, k0))
    xx = IX
    for i, s in enumerate(chips):
        st = cue(10.9) + 0.4 + i * 0.22
        k = back((t - st) / 0.4)
        if k <= 0:
            continue
        f = F(28, "b")
        w = tw(d, s, f) + 64
        on = ap(t, st + 0.3, 0.3)
        rbox(d, (xx, 840, xx + w, 900), fill=mix(mix(GREEN, on * 0.35, PANEL2), clamp(k)), outline=mix(GREEN if on else LINE, clamp(k)), r=30)
        check(d, xx + 26, 870, 18, mix(GREEN, on), 4, on)
        d.text((xx + 44, 851), s, font=f, fill=mix(WHITE, clamp(k)))
        xx += w + 14


def sc_s3(cv, d, t, dur):
    tracker(cv, d, 3, t / dur, t)
    d = ImageDraw.Draw(cv)
    scene_head(d, t, 3, "ROI 도로선 인식 자율주행")
    t_roi, t_mask, t_split, t_dec, t_tune = cue(3.1), cue(6.4), cue(8.7), cue(11.0), cue(13.0)
    src = base(CUSTOM / "s3_lane_cam.png")
    sw, sh = IMG_W, IMG_H
    sx, sy = sw / src.width, sh / src.height
    cam = src.resize((sw, sh), Image.BILINEAR).convert("RGBA")
    y0, y1 = int(ROI_Y[0] * sy), int(ROI_Y[1] * sy)
    k_in = ap(t, 0.2, 0.6)
    # ROI 밖 어둡게
    k_roi = ap(t, t_roi, 0.8)
    if k_roi > 0:
        dim = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        dd = ImageDraw.Draw(dim)
        dd.rectangle((0, 0, sw, y0), fill=(0, 0, 0, int(150 * k_roi)))
        dd.rectangle((0, y1, sw, sh), fill=(0, 0, 0, int(150 * k_roi)))
        cam = Image.alpha_composite(cam, dim)
    # ROI 영역 → 이진 마스크 (위에서 아래로 스캔)
    k_mask = ap(t, t_mask, 1.0)
    if k_mask > 0:
        m = ROI_MASK.resize((sw, sh), Image.NEAREST).convert("RGBA")
        scan = int(y0 + (y1 - y0) * k_mask)
        part = m.crop((0, y0, sw, scan))
        cam.paste(part, (0, y0))
        if k_mask < 1:
            ImageDraw.Draw(cam).line((0, scan, sw, scan), fill=(56, 220, 255, 255), width=4)
    frame_img(cv, d, cam, (IX, IY), k_in, RED)
    d = ImageDraw.Draw(cv)
    oy = IY + (1 - k_in) * 40
    # ROI 사각형 그리기
    if k_roi > 0:
        rx1, ry1, rx2, ry2 = IX, oy + y0, IX + sw * k_roi, oy + y1
        d.rectangle((rx1, ry1, rx2, ry2), outline=YEL, width=5)
        d.rounded_rectangle((IX + 12, ry1 - 52, IX + 230, ry1 - 8), radius=10, fill=YEL)
        d.text((IX + 24, ry1 - 47), "ROI 관심 영역", font=F(28, "b"), fill=BG)
    # 3등분 선 + 비율
    k_sp = ap(t, t_split, 0.6)
    labels = ["L", "C", "R"]
    if k_sp > 0:
        for i in (1, 2):
            x = IX + sw * i / 3
            d.line((x, oy + y0, x, oy + y0 + (y1 - y0) * k_sp), fill=GREEN, width=4)
        for i in range(3):
            v = ROI_RATIO[i] * ap(t, t_split + 0.3, 1.2)
            cx = IX + sw * (i + 0.5) / 3
            s = f"{labels[i]} {v * 100:3.0f}%"
            d.rounded_rectangle((cx - 80, oy + y1 - 64, cx + 80, oy + y1 - 12), radius=10, fill=(0, 0, 0))
            ctext(d, cx, oy + y1 - 60, s, F(32, "b"), mix(GREEN, k_sp))
    # 결정 배지
    k_dec = back((t - t_dec) / 0.5)
    if k_dec > 0:
        s = f"조향: {ROI_DEC}"
        f = F(46, "b")
        w = tw(d, s, f) + 60
        cx, cy = IX + sw / 2, oy + 90
        sc_ = clamp(k_dec, 0, 1.2)
        d.rounded_rectangle((cx - w / 2 * sc_, cy - 40 * sc_, cx + w / 2 * sc_, cy + 40 * sc_), radius=40, fill=ORANGE)
        if sc_ > 0.7:
            ctext(d, cx, cy - 30, s, f, BG)
            # 조향 화살표
            ax = cx + w / 2 + 30
            grow_arrow(d, (ax, cy), (ax + 90, cy - 40 if ROI_DEC == "RIGHT" else cy), ap(t, t_dec + 0.3, 0.4), ORANGE, 8, 22)
    d.text((IX + 6, oy + sh + 12), "커스텀 카메라 이미지에 실제 ROI 처리 적용 (HSV 마스크 · 좌/중/우 비율)", font=F(24, "m"), fill=mix(MUTED, k_in))
    # 오른쪽 단계 목록 (진행에 맞춰 하이라이트)
    steps = [("카메라 프레임", WHITE, 0.0), ("ROI 설정", YEL, t_roi), ("색상 필터 · 이진화", CYAN, t_mask),
             ("좌 · 중 · 우 픽셀 비율", GREEN, t_split), ("조향 결정", ORANGE, t_dec), ("트랙바 튜닝 → 완주", PURPLE, t_tune)]
    x = 1150
    for i, (s, col, st) in enumerate(steps):
        k = ap(t, max(0.3, st - 0.6) + 0.0, 0.5) if i else ap(t, 0.4)
        y = IY + i * 84
        active = st <= t < (steps[i + 1][2] if i < 5 else 1e9)
        if active:
            glow_rect(cv, (x, y, x + 700, y + 70), col, 0.6 + 0.4 * math.sin(t * 5), r=16, blur=8)
            d = ImageDraw.Draw(cv)
        fill = mix(mix(col, 0.22, PANEL2), k) if active else mix(PANEL2, k)
        rbox(d, (x, y, x + 700, y + 70), fill=fill, outline=mix(col if t >= st else LINE, k), r=16, width=3)
        d.text((x + 26, y + 13), f"{i + 1}", font=F(34, "b"), fill=mix(col, k, PANEL2))
        d.text((x + 76, y + 13), s, font=F(34, "b"), fill=mix(WHITE if t >= st else MUTED, k, PANEL2))
        if t >= st + 0.4 and not active:
            check(d, x + 660, y + 35, 22, GREEN, 5, ap(t, st + 0.4, 0.3))
    # 실제 디버깅 화면 썸네일
    k_th = ap(t, t_tune, 0.6)
    if k_th > 0:
        th = kb(REPO / "01_Movies/실전_자율주행_테스트_화면_캡쳐/주행-모니터닝-1.png", (520, 284), t - t_tune, dur - t_tune, 0.05)
        frame_img(cv, d, th, (1150 + 180, IY + 512), k_th, PURPLE, 12)
        d = ImageDraw.Draw(cv)
        d.text((1150, IY + 530), "실제\n트랙바\n디버깅\n화면", font=F(28, "b"), fill=mix(PURPLE, k_th), spacing=8)


YOLO_BOXES = [  # (x1,y1,x2,y2) in 1344x752 이미지 좌표, class, conf, color, 등장 cue
    ((150, 46, 255, 228), "red", 0.94, RED, 8.3),
    ((550, 238, 745, 384), "car", 0.92, ORANGE, 9.0),
    ((858, 160, 1010, 305), "oo", 0.90, BLUE, 9.9),
    ((1118, 160, 1262, 305), "xx", 0.89, PURPLE, 10.6),
]
EPOCHS = [(1, 0.731), (10, 0.985), (25, 0.982), (50, 0.986), (75, 0.990), (95, 0.988), (100, 0.992)]


def sc_s4(cv, d, t, dur):
    tracker(cv, d, 4, t / dur, t)
    d = ImageDraw.Draw(cv)
    scene_head(d, t, 4, "Haar 개요 → YOLO11 학습 · 검증")
    # 파이프라인 (PC)
    steps = [("수집", cue(3.5)), ("라벨링", cue(5.0)), ("학습", cue(6.9)), ("검증", cue(12.2)), ("테스트", cue(13.2)),
             ("배포", cue(14.9))]
    x0, y0, bw, gap = 70, 236, 236, 22
    kp = ap(t, 0.3)
    d.text((x0, y0 - 2), "PC", font=F(24, "b"), fill=mix(CYAN, kp))
    for i, (s, st) in enumerate(steps):
        x = x0 + 50 + i * (bw + gap) - (0 if i < 5 else 0)
        k = ap(t, 0.3 + i * 0.08)
        lit = t >= st
        active = lit and (i == 5 or t < steps[i + 1][1])
        col = GREEN if i == 5 else (YEL if i in (3, 4) else CYAN)
        if active:
            glow_rect(cv, (x, y0, x + bw, y0 + 64), col, 0.5 + 0.5 * math.sin(t * 5), r=32, blur=8)
            d = ImageDraw.Draw(cv)
        rbox(d, (x, y0, x + bw, y0 + 64), fill=mix(mix(col, 0.3, PANEL2) if lit else PANEL2, k),
             outline=mix(col if lit else LINE, k), r=32, width=3)
        ctext(d, x + bw / 2, y0 + 12, s, F(32, "b"), mix(WHITE if lit else MUTED, k, PANEL2))
        if i < 5:
            grow_arrow(d, (x + bw + 2, y0 + 32), (x + bw + gap - 2, y0 + 32), k, mix(LINE, k), 3, 10)
    # Haar 한 줄 (처음 3초)
    kh = ap(t, 0.4) * (1 - ap(t, cue(3.3)))
    if kh > 0:
        d.text((70, 322), "먼저 Haar Cascade로 정지 표지판 검출을 체험하고, 조명 · 거리 한계를 확인합니다",
               font=F(28, "m"), fill=mix(MUTED, kh))
    # 검출 장면
    sw, sh = 1000, 560
    src = base(CUSTOM / "s4_yolo_scene.png")
    sx, sy = sw / src.width, sh / src.height
    img = kb(CUSTOM / "s4_yolo_scene.png", (sw, sh), 0, 1, 0)
    ki = ap(t, 0.3, 0.6)
    iy = 340
    frame_img(cv, d, img, (IX, iy), ki, YEL)
    d = ImageDraw.Draw(cv)
    oy = iy + (1 - ki) * 40
    # 스캔 라인 (추론 중)
    t_det = cue(8.0)
    if t_det - 0.8 < t < t_det + 0.6:
        p = clamp((t - (t_det - 0.8)) / 1.4)
        y = oy + sh * p
        d.line((IX, y, IX + sw, y), fill=CYAN, width=3)
        d.text((IX + 16, oy + 14), "YOLO11n 추론 중 · 320×320", font=F(26, "b"), fill=CYAN)
    for (bx, cls, conf, col, c) in YOLO_BOXES:
        st = cue(c)
        k = ap(t, st, 0.45)
        if k <= 0:
            continue
        x1, y1, x2, y2 = IX + bx[0] * sx, oy + bx[1] * sy, IX + bx[2] * sx, oy + bx[3] * sy
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        s = 1.5 - 0.5 * k
        bx1, by1, bx2, by2 = cx - (cx - x1) * s, cy - (cy - y1) * s, cx + (x2 - cx) * s, cy + (y2 - cy) * s
        d.rectangle((bx1, by1, bx2, by2), outline=rgba(col, k), width=5)
        lab = f"{cls} {conf * ap(t, st, 0.8):.2f}"
        f = F(26, "b")
        lw = tw(d, lab, f) + 20
        d.rectangle((bx1 - 2, by1 - 38, bx1 + lw, by1), fill=rgba(col, k))
        d.text((bx1 + 8, by1 - 35), lab, font=f, fill=rgba(BG, k))
    d.text((IX + 6, oy + sh + 10), "검출 예시 — 커스텀 일러스트 이미지 (클래스: car · green · red · oo · xx)",
           font=F(24, "m"), fill=mix(MUTED, ki))
    # 오른쪽: 실제 학습 곡선 (best.pt)
    px, py, pw, ph = 1120, 340, 730, 400
    kc = ap(t, cue(12.0), 0.5)
    if kc > 0:
        rbox(d, (px, py, px + pw, py + ph + 150), fill=mix(PANEL, kc), outline=mix(LINE, kc), r=18)
        d.text((px + 24, py + 16), "검증 · 실제 학습 곡선 (best.pt)", font=F(30, "b"), fill=mix(WHITE, kc))
        gx1, gy1, gx2, gy2 = px + 70, py + 80, px + pw - 30, py + ph - 20

        def X(e):
            return gx1 + (gx2 - gx1) * (e - 1) / 99

        def Y(v):
            return gy2 - (gy2 - gy1) * (v - 0.6) / 0.4
        for v in (0.6, 0.7, 0.8, 0.9, 1.0):
            d.line((gx1, Y(v), gx2, Y(v)), fill=mix((40, 55, 85), kc), width=1)
            d.text((gx1 - 60, Y(v) - 14), f"{v:.1f}", font=F(22, "m"), fill=mix(MUTED, kc))
        # 합격선 0.80
        d.line((gx1, Y(0.8), gx2, Y(0.8)), fill=mix(RED, kc), width=3)
        d.text((gx2 - 190, Y(0.8) + 6), "합격선 mAP50 0.80", font=F(22, "b"), fill=mix(RED, kc))
        # 곡선 그리기
        kl = ap(t, cue(12.4), 1.6)
        pts = [(X(e), Y(v)) for e, v in EPOCHS]
        segs = len(pts) - 1
        drawn = kl * segs
        line = [pts[0]]
        for i in range(segs):
            if drawn >= i + 1:
                line.append(pts[i + 1])
            elif drawn > i:
                q = drawn - i
                line.append((pts[i][0] + (pts[i + 1][0] - pts[i][0]) * q, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * q))
                break
        if len(line) > 1:
            d.line(line, fill=YEL, width=5, joint="curve")
        for (e, v), p in zip(EPOCHS, pts):
            if p[0] <= line[-1][0] + 1:
                d.ellipse((p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6), fill=YEL)
        d.text((gx1, gy2 + 0), "epoch 1", font=F(20, "m"), fill=mix(MUTED, kc))
        d.text((gx2 - 90, gy2 + 0), "epoch 100", font=F(20, "m"), fill=mix(MUTED, kc))
        # 지표
        km = ap(t, cue(13.6), 0.8)
        mets = [("mAP50", 0.988, YEL), ("Precision", 0.957, CYAN), ("Recall", 0.986, GREEN)]
        for i, (n, v, col) in enumerate(mets):
            x = px + 24 + i * 235
            d.text((x, py + ph + 10), n, font=F(24, "m"), fill=mix(MUTED, km))
            d.text((x, py + ph + 40), f"{v * km:.3f}", font=F(44, "b"), fill=mix(col, km))
        kpass = back((t - cue(14.8)) / 0.5)
        if kpass > 0:
            s = "PASS → 라즈봇 배포 (NCNN)"
            f = F(30, "b")
            w = tw(d, s, f) + 40
            d.rounded_rectangle((px + pw - w - 20, py + ph + 98, px + pw - 20, py + ph + 142), radius=22,
                                fill=mix(GREEN, clamp(kpass)))
            d.text((px + pw - w, py + ph + 103), s, font=f, fill=BG)


FSM = [("DRIVE", "차선 주행", WHITE), ("WAIT", "빨간불 정지", RED), ("HAZARD", "앞차 정지 · 경고", ORANGE),
       ("APPROACH", "oo 표지 접근", BLUE), ("HOLD", "주차 완료", GREEN)]
FSM_SEQ = [(0.0, 0), (4.75, 1), (6.3, 0), (6.7, 2), (9.2, 0), (10.8, 3), (12.6, 4)]


def sc_s5(cv, d, t, dur):
    tracker(cv, d, 5, t / dur, t)
    d = ImageDraw.Draw(cv)
    scene_head(d, t, 5, "기본 자율주행 + YOLO11 통합 주행")
    frame_img(cv, d, kb(CUSTOM / "s5_parking.png", (900, 504), t, dur, 0.1, (0.4, -0.2)), (IX, IY),
              ap(t, 0.2, 0.6), GREEN, label="빨간불 정지 · 앞차 경고 · oo 표지 자동 주차")
    # 현재 상태
    cur = 0
    for c, s in FSM_SEQ:
        if t >= cue(c):
            cur = s
    x0 = 1020
    d.text((x0, IY - 4), "미션 FSM (우선순위 red > car > oo)", font=F(28, "b"), fill=mix(WHITE, ap(t, 0.4)))
    for i, (n, desc, col) in enumerate(FSM):
        k = ap(t, 0.5 + i * 0.12)
        y = IY + 50 + i * 118
        active = i == cur
        if active:
            glow_rect(cv, (x0, y, x0 + 830, y + 96), col, 0.6 + 0.4 * math.sin(t * 5), r=18, blur=9)
            d = ImageDraw.Draw(cv)
        rbox(d, (x0, y, x0 + 830, y + 96), fill=mix(mix(col, 0.25, PANEL2) if active else PANEL2, k),
             outline=mix(col if active else LINE, k), r=18, width=4 if active else 2)
        d.text((x0 + 28, y + 22), n, font=F(40, "b"), fill=mix(col if active else MUTED, k, PANEL2))
        d.text((x0 + 300, y + 28), desc, font=F(34, "b"), fill=mix(WHITE if active else MUTED, k, PANEL2))
        if active:
            d.ellipse((x0 + 780, y + 36, x0 + 804, y + 60), fill=col)
    # 이벤트 토스트
    ev = None
    for c, s in FSM_SEQ[1:]:
        if cue(c) <= t < cue(c) + 1.4:
            ev = {1: ("red 인식 → 정지", RED), 0: ("신호 해제 → 주행 재개", WHITE), 2: ("car 인식 → 정지 + 경고음", ORANGE),
                  3: ("oo 인식 → 주차 접근", BLUE), 4: ("oo 사라짐 → 주차 정지", GREEN)}[s]
            ke = ap(t, cue(c), 0.3) * (1 - ap(t, cue(c) + 1.1, 0.3))
    if ev:
        s, col = ev
        f = F(34, "b")
        w = tw(d, s, f) + 50
        x, y = IX + 450 - w / 2, IY + 504 + 70
        d.rounded_rectangle((x, y, x + w, y + 64), radius=32, fill=mix(col, ke))
        d.text((x + 25, y + 11), s, font=f, fill=mix(BG, ke, col) if ke > 0 else BG)


def sc_s6(cv, d, t, dur):
    tracker(cv, d, 6, t / dur, t)
    d = ImageDraw.Draw(cv)
    scene_head(d, t, 6, "최종 테스트 · 코칭")
    frame_img(cv, d, kb(CUSTOM / "s6_final.png", (900, 504), t, dur, 0.08, (0.3, 0.3)), (IX, IY),
              ap(t, 0.2, 0.6), ORANGE, label="최종 코스 주행 → 점수 확인 → 즉석 코칭")
    x0 = 1020
    k0 = ap(t, cue(3.2))
    d.text((x0, IY - 4), "평가 배점 (예시, 100점)", font=F(28, "b"), fill=mix(WHITE, k0))
    items = [("차선 주행", 30, RED), ("신호등 준수", 25, YEL), ("자동 주차", 20, BLUE), ("앞차 대응", 15, ORANGE),
             ("완주 시간", 10, GREEN)]
    for i, (n, v, col) in enumerate(items):
        st = cue(3.4) + i * 0.3
        k = ap(t, st, 0.7)
        y = IY + 50 + i * 74
        d.text((x0, y + 6), n, font=F(30, "b"), fill=mix(WHITE, ap(t, st - 0.2)))
        bx = x0 + 200
        d.rounded_rectangle((bx, y + 10, bx + 560, y + 46), radius=18, fill=mix((34, 46, 72), ap(t, st - 0.2)))
        if k > 0:
            d.rounded_rectangle((bx, y + 10, bx + 560 * v / 30 * k, y + 46), radius=18, fill=col)
        d.text((bx + 575, y + 6), f"{int(v * k)}", font=F(30, "b"), fill=mix(col, k))
    # 코칭 루프 (회전)
    kc = ap(t, cue(6.4), 0.6)
    if kc > 0:
        cx, cy, r = x0 + 400, IY + 575, 86
        labels = [("주행", 0), ("진단", 1), ("수정", 2), ("재주행", 3)]
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=mix(LINE, kc), width=4)
        a0 = t * 2.2
        d.arc((cx - r, cy - r, cx + r, cy + r), math.degrees(a0), math.degrees(a0) + 80, fill=YEL, width=8)
        for s, i in labels:
            ang = -math.pi / 2 + i * math.pi / 2
            px, py = cx + (r + 75) * math.cos(ang), cy + (r + 34) * math.sin(ang)
            ctext(d, px, py - 18, s, F(30, "b"), mix(WHITE, kc))
        ctext(d, cx, cy - 22, "코칭", F(36, "b"), mix(YEL, kc))


def sc_outro(cv, d, t, dur):
    tracker(cv, d, 7, 1, t, finale=0.2)
    d = ImageDraw.Draw(cv)
    bg = kb(ASSETS / "track_top_2.jpg", (W, 800), t, dur, 0.08).filter(ImageFilter.GaussianBlur(5))
    paste(cv, bg, (0, 170), 0.5 * ap(t, 0.0, 0.8), 0)
    d = ImageDraw.Draw(cv)
    k = ap(t, 1.4)
    ctext(d, W / 2, 300, "20시간 · 6차시 완료", F(44, "b"), mix(GREEN, k))
    flow = [("단계도", YEL), ("실습", GREEN), ("검증", CYAN)]
    bw, gap = 360, 120
    x0 = (W - (bw * 3 + gap * 2)) / 2
    for i, (s, col) in enumerate(flow):
        kk = back((t - 1.6 - i * 0.3) / 0.5)
        if kk <= 0:
            continue
        x = x0 + i * (bw + gap)
        rbox(d, (x, 400, x + bw, 550), fill=mix(PANEL2, clamp(kk)), outline=mix(col, clamp(kk)), r=26, width=5)
        ctext(d, x + bw / 2, 438, s, F(62, "b"), mix(col, clamp(kk), PANEL2))
        if i < 2:
            grow_arrow(d, (x + bw + 14, 475), (x + bw + gap - 14, 475), ap(t, 1.8 + i * 0.3), WHITE, 7)
    k2 = ap(t, 2.6)
    ctext(d, W / 2, 640, "PC에서 만들고 검증하고, 라즈봇에서 달린다", F(56, "b"), mix(WHITE, k2))
    ctext(d, W / 2, 730, "Raspbot V2 · 컴퓨터 비전 자율주행 20시간 과정", F(32, "m"), mix(MUTED, k2))


# ------------------------------------------------------------------ 대본
SCENES = [
    dict(fn=sc_intro, narr="00", cap="라즈봇 V2로 배우는 컴퓨터 비전 자율주행 20시간 — 여섯 차시를 차례로"),
    dict(fn=sc_s1, narr="01", cap="1차시: 부품 확인 → 조립 → 스마트폰 앱으로 첫 주행"),
    dict(fn=sc_s2, narr="02", cap="2차시: PC에서 코드 작성 → 원격 전송 → I2C로 모터 · 서보 · 센서 제어"),
    dict(fn=sc_s3, narr="03", cap="3차시: ROI만 잘라 이진화 → 좌 · 중 · 우 비율로 조향 → 트랙바 튜닝 · 완주"),
    dict(fn=sc_s4, narr="04", cap="4차시: PC에서 수집 · 라벨링 · 학습 → 검증 mAP50 0.80 통과 모델만 배포"),
    dict(fn=sc_s5, narr="05", cap="5차시: 차선 주행 + YOLO11 — 빨간불 정지 · 앞차 경고 · oo 표지 자동 주차"),
    dict(fn=sc_s6, narr="06", cap="6차시: 최종 코스 주행으로 점수 확인, 부족한 부분은 바로 코칭"),
    dict(fn=sc_outro, narr="07", cap="단계마다 만들고 검증하며 컴퓨터 비전 개발 프로세스를 익힙니다"),
]


def prep_audio(tmp: Path):
    """나레이션 앞뒤 무음 제거 + 속도 조정 → 길이 측정."""
    for sc in SCENES:
        src = NARR / f"{sc['narr']}.mp3"
        dst = tmp / f"{sc['narr']}.wav"
        af = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
              "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
              f"atempo={TEMPO},aresample=48000")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", af, "-ac", "1", str(dst)], check=True)
        dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                             "-of", "csv=p=0", str(dst)]).decode())
        sc["wav"], sc["ndur"] = dst, dur
        sc["dur"] = LEAD + dur + TAIL


def mix_audio(tmp: Path, starts, total):
    inputs, filt = [], []
    for i, sc in enumerate(SCENES):
        inputs += ["-i", str(sc["wav"])]
        ms = int((starts[i] + LEAD) * 1000)
        filt.append(f"[{i}]adelay={ms}|{ms}[a{i}]")
    filt.append("".join(f"[a{i}]" for i in range(len(SCENES))) +
                f"amix=inputs={len(SCENES)}:normalize=0,loudnorm=I=-16:TP=-1.5,apad,atrim=0:{total:.3f}[out]")
    wav = tmp / "narration.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filt),
                    "-map", "[out]", "-ac", "2", "-ar", "48000", str(wav)], check=True)
    return wav


def render(sc, t, gt, cap=True):
    cv = Image.new("RGBA", (W, H), BG + (255,))
    background(cv, gt)
    d = ImageDraw.Draw(cv)
    sc["fn"](cv, d, t, sc["dur"])
    d = ImageDraw.Draw(cv)
    if cap:
        caption(cv, d, sc["cap"], ap(t, LEAD - 0.2, 0.3) * (1 - ap(t, sc["dur"] - 0.35, 0.3)))
    return cv


def main():
    global ROI_MASK, ROI_RATIO, ROI_DEC
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("--stills", action="store_true")
    args = ap_.parse_args()
    ROI_MASK, ROI_RATIO, ROI_DEC = roi_process()
    print("ROI 비율 L/C/R =", [f"{r:.2f}" for r in ROI_RATIO], "→", ROI_DEC)

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        prep_audio(tmp)
        starts, acc = [], 0.0
        for sc in SCENES:
            starts.append(acc)
            acc += sc["dur"] - FADE
        total = acc + FADE
        print("장면 길이:", [round(sc["dur"], 1) for sc in SCENES], f"총 {total:.1f}s")

        STILLS.mkdir(exist_ok=True)
        for i, sc in enumerate(SCENES):
            render(sc, sc["dur"] - 0.6, starts[i] + sc["dur"] - 0.6, cap=False).convert("RGB").save(
                STILLS / f"{i:02d}_{sc['fn'].__name__}.png")
        print(f"stills → {STILLS}")
        if args.stills:
            return

        wav = mix_audio(tmp, starts, total)
        n = int(round(total * FPS))
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-i", str(wav), "-map", "0:v", "-map", "1:a",
               "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "160k", "-t", f"{n / FPS:.3f}", "-movflags", "+faststart", str(OUT)]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for fi in range(n):
            gt = fi / FPS
            idx = max(i for i, s in enumerate(starts) if s <= gt)
            frame = render(SCENES[idx], gt - starts[idx], gt)
            if idx > 0 and gt - starts[idx] < FADE:
                old = render(SCENES[idx - 1], gt - starts[idx - 1], gt)
                frame = Image.blend(old, frame, ease((gt - starts[idx]) / FADE))
            fd = ImageDraw.Draw(frame)
            fd.rectangle((0, H - 6, W * gt / total, H), fill=YEL)
            proc.stdin.write(np.asarray(frame.convert("RGB")).tobytes())
            if fi % 300 == 0:
                print(f"  frame {fi}/{n}")
        proc.stdin.close()
        proc.wait()
    print(f"video → {OUT}  ({total:.1f}s)")


if __name__ == "__main__":
    main()
