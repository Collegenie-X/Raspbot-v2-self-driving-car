"""
20시간 교육과정 — 구조도 소개 영상 (짧은 버전, 1분 이내, 1920x1080 · 30fps)

- 상단: 구조 진행 체크 바 (목표 → 크로스 개발 → ROI 주행 → YOLO11 인식 → 6차시 단계도)
- 장면: 타이틀 · 목표 · 크로스 개발 · ROI(실제 처리) · YOLO11(검출 + 실제 학습 곡선) · 6차시 단계도 · 마무리
- 나레이션: Higgsfield MiniMax 'Hana' (assets/narration_short/NN.mp3), TEMPO 배속
- 그리기 도구 · 이미지 · ROI 처리는 make_session_video.py 를 재사용

사용 예:
  python3 make_overview_video.py            # 영상 생성
  python3 make_overview_video.py --stills   # 장면별 대표 PNG만 (stills/)
"""
from __future__ import annotations

import argparse
import math
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import make_session_video as mv
from make_session_video import (ASSETS, BG, BLUE, CUSTOM, CYAN, FPS, GREEN, H, LINE, MUTED, ORANGE, PANEL,
                                PANEL2, PURPLE, RED, REPO, TODO, WHITE, YEL, W, F, ap, back, base, check, clamp,
                                ctext, ease, frame_img, glow_rect, grow_arrow, kb, mix, packet, paste, rbox, rgba, tw)

HERE = Path(__file__).resolve().parent
NARR = ASSETS / "narration_short"
OUT = HERE / "20시간_교육과정_구조도_소개.mp4"
STILLS = HERE / "stills"

TEMPO, LEAD, TAIL, FADE = 1.12, 0.55, 1.0, 0.45


def cue(x):
    """나레이션 원본 시각(초) → 장면 시각(초)."""
    return LEAD + x / TEMPO


# ------------------------------------------------------------------ 상단: 구조 진행 체크
PARTS = [("목표", "무엇을 만드나", YEL), ("크로스 개발", "PC ↔ Raspbot", CYAN), ("ROI 주행", "OpenCV 도로선", RED),
         ("YOLO11 인식", "학습 · 검증 · 배포", ORANGE), ("6차시 단계도", "20시간 실습", GREEN)]


def tracker(cv, d, cur, prog, t, intro=None, finale=None):
    """cur: 진행 중 항목(1~5), 0=시작 전, 6=모두 완료."""
    x0, x1, y, h, gap = 70, 1850, 24, 78, 16
    pw = (x1 - x0 - gap * 4) / 5
    for i, (name, sub, col) in enumerate(PARTS):
        n = i + 1
        k = 1.0 if intro is None else back((t - intro - i * 0.15) / 0.5)
        if k <= 0:
            continue
        kc = clamp(k)
        x = x0 + i * (pw + gap)
        yy = y - (1 - kc) * 30
        done, now = n < cur or cur == 6, n == cur
        if finale is not None and cur == 6:
            done = t >= finale + i * 0.18
        if done:
            dk = (22, 70, 52)
            rbox(d, (x, yy, x + pw, yy + h), fill=mix(dk, kc), outline=mix(GREEN, kc), r=39, width=3)
            d.ellipse((x + 14, yy + 13, x + 66, yy + 65), fill=mix(GREEN, kc, dk))
            check(d, x + 40, yy + 39, 28, BG, 6, 1.0 if finale is None else ap(t, finale + i * 0.18, 0.4))
            tc, sc = mix(WHITE, kc, dk), mix((170, 230, 200), kc, dk)
        elif now:
            glow_rect(cv, (x, yy, x + pw, yy + h), col, 0.8 * (0.55 + 0.45 * math.sin(t * 4.2)), r=39, blur=10)
            d = ImageDraw.Draw(cv)
            rbox(d, (x, yy, x + pw, yy + h), fill=PANEL2, outline=col, r=39, width=4)
            bx1, bx2 = x + 80, x + pw - 30
            d.rounded_rectangle((bx1, yy + h - 11, bx2, yy + h - 6), radius=2, fill=(45, 60, 92))
            d.rounded_rectangle((bx1, yy + h - 11, bx1 + (bx2 - bx1) * clamp(prog), yy + h - 6), radius=2, fill=col)
            d.ellipse((x + 14, yy + 13, x + 66, yy + 65), fill=col)
            ctext(d, x + 40, yy + 17, str(n), F(32, "b"), BG)
            tc, sc = WHITE, col
        else:
            rbox(d, (x, yy, x + pw, yy + h), fill=mix(TODO, kc), outline=mix(LINE, kc), r=39, width=2)
            d.ellipse((x + 14, yy + 13, x + 66, yy + 65), outline=mix(LINE, kc), width=3)
            ctext(d, x + 40, yy + 17, str(n), F(32, "b"), mix(MUTED, kc))
            tc, sc = mix(MUTED, kc), mix((100, 115, 140), kc)
        d.text((x + 80, yy + 6), name, font=F(28, "b"), fill=tc)
        d.text((x + 80, yy + 40), sub, font=F(20, "m"), fill=sc)
    return d


def head(d, t, n, title):
    k = ap(t, 0.05)
    col = PARTS[n - 1][2]
    x = 70 - (1 - k) * 40
    d.rounded_rectangle((x, 140, x + 10, 204), radius=5, fill=mix(col, k))
    d.text((x + 30, 134), title, font=F(56, "b"), fill=mix(WHITE, k))


# ------------------------------------------------------------------ 아이콘
def icon(d, kind, cx, cy, s, k, bgc=PANEL2):
    c = lambda col: mix(col, k, bgc)  # noqa: E731
    if kind == "lane":
        d.polygon([(cx - s * .15, cy - s * .5), (cx + s * .15, cy - s * .5), (cx + s * .5, cy + s * .5),
                   (cx - s * .5, cy + s * .5)], fill=c((70, 78, 96)))
        d.line([(cx - s * .1, cy - s * .5), (cx - s * .38, cy + s * .5)], fill=c(RED), width=6)
        d.line([(cx + s * .1, cy - s * .5), (cx + s * .38, cy + s * .5)], fill=c(WHITE), width=6)
    elif kind == "light":
        d.rounded_rectangle((cx - s * .22, cy - s * .5, cx + s * .22, cy + s * .5), radius=10, fill=c((40, 40, 48)))
        for i, col in enumerate([RED, YEL, GREEN]):
            yy = cy - s * .3 + i * s * .3
            d.ellipse((cx - s * .13, yy - s * .13, cx + s * .13, yy + s * .13), fill=c(col))
    elif kind == "car":
        d.rounded_rectangle((cx - s * .45, cy - s * .1, cx + s * .45, cy + s * .25), radius=8, fill=c(ORANGE))
        d.rounded_rectangle((cx - s * .25, cy - s * .35, cx + s * .2, cy - s * .05), radius=8, fill=c(ORANGE))
        for dx in (-.25, .25):
            d.ellipse((cx + s * dx - s * .12, cy + s * .15, cx + s * dx + s * .12, cy + s * .39), fill=c((20, 20, 20)))
    elif kind == "sign":
        for j, (ch, col) in enumerate([("O", BLUE), ("X", PURPLE)]):
            ox = cx - s * .27 + j * s * .54
            d.rounded_rectangle((ox - s * .24, cy - s * .3, ox + s * .24, cy + s * .2), radius=6, fill=c(WHITE))
            ctext(d, ox, cy - s * .32, ch, F(int(s * .42), "b"), c(col if ch == "X" else (20, 20, 20)))
    elif kind == "park":
        d.rounded_rectangle((cx - s * .45, cy - s * .45, cx + s * .45, cy + s * .45), radius=12, fill=c((40, 90, 200)))
        ctext(d, cx, cy - s * .4, "P", F(int(s * .62), "b"), c(WHITE))


# ================================================================== 장면
def sc_title(cv, d, t, dur):
    d = tracker(cv, d, 0, 0, t, intro=cue(1.6))
    k = ap(t, 0.0, 0.8)
    paste(cv, kb(REPO / "09_yolo11_pipeline/demo/shorts/illust/raspi.png", (620, 620), t, dur, 0.07), (130, 260 + (1 - k) * 30), k, 32)
    x = 860
    k1, k2, k3 = ap(t, 0.25), ap(t, 0.7), ap(t, 1.2)
    d.text((x - (1 - k1) * 40, 270), "Raspbot V2 자율주행", font=F(92, "b"), fill=mix(WHITE, k1))
    d.text((x - (1 - k2) * 40, 392), "20시간 과정 · 핵심 구조 1분 정리", font=F(52, "b"), fill=mix(CYAN, k2))
    chips = [("ROI 도로선", RED), ("YOLO11", YEL), ("크로스 개발", CYAN), ("실습 87%", GREEN)]
    xx = x
    for i, (s, col) in enumerate(chips):
        kk = clamp(back((t - 1.2 - i * 0.2) / 0.5))
        if kk <= 0:
            continue
        f = F(36, "b")
        w = tw(d, s, f) + 48
        rbox(d, (xx, 500, xx + w, 566), fill=mix(PANEL2, kk), outline=mix(col, kk), r=33, width=4)
        d.text((xx + 24, 511), s, font=f, fill=mix(col, kk))
        xx += w + 18
    d.text((x, 620), "11/26 ~ 12/7 · 6차시 · 이론은 차시당 1시간 이내", font=F(34, "m"), fill=mix(MUTED, k3))
    # 위쪽 체크 바 가리키기
    ka = ap(t, cue(1.6) + 0.8) * (1 - ap(t, dur - 0.6))
    if ka > 0:
        d.text((x, 700), "▲ 상단 바에서 5가지 구조를 차례로 체크합니다", font=F(30, "b"), fill=mix(YEL, ka))


GOALS = [("lane", "도로선 따라 주행", "OpenCV · ROI", RED, 2.28), ("light", "신호등 인식", "red / green → 정지 · 출발", GREEN, 4.2),
         ("car", "장애물 인식", "car → 정지 · 경고", ORANGE, 5.36), ("sign", "주차 표지 인식", "oo 목표 · xx 금지", BLUE, 6.38),
         ("park", "자동 주차", "oo 표지 접근 → 정지", PURPLE, 8.23)]


def sc_goal(cv, d, t, dur):
    d = tracker(cv, d, 1, t / dur, t)
    head(d, t, 1, "목표 — 카메라 하나로 보고, 판단하고, 달린다")
    frame_img(cv, d, kb(CUSTOM / "s5_parking.png", (900, 504), t, dur, 0.1, (0.4, -0.2)), (70, 250), ap(t, 0.2, 0.6),
              YEL, label="커스텀 일러스트 — 빨간불 · 앞차 · oo 주차 표지")
    d = ImageDraw.Draw(cv)
    for i, (ic, a, b, col, c) in enumerate(GOALS):
        st = cue(c)
        k = ap(t, st - 0.35, 0.45)
        if k <= 0:
            continue
        y = 250 + i * 126
        x = 1010 + (1 - k) * 50
        latest = st <= t < (cue(GOALS[i + 1][4]) if i < 4 else 1e9)
        if latest:
            glow_rect(cv, (x, y, x + 840, y + 108), col, 0.55 + 0.45 * math.sin(t * 5), r=20, blur=9)
            d = ImageDraw.Draw(cv)
        rbox(d, (x, y, x + 840, y + 108), fill=mix(mix(col, 0.18, PANEL2) if latest else PANEL2, k),
             outline=mix(col, k), r=20, width=3)
        icon(d, ic, x + 64, y + 54, 72, k)
        d.text((x + 130, y + 12), a, font=F(42, "b"), fill=mix(WHITE, k, PANEL2))
        d.text((x + 130, y + 64), b, font=F(28, "m"), fill=mix(col, k, PANEL2))
        if t >= st + 0.3:
            check(d, x + 790, y + 54, 28, GREEN, 6, ap(t, st + 0.3, 0.35))


def sc_cross(cv, d, t, dur):
    d = tracker(cv, d, 2, t / dur, t)
    head(d, t, 2, "크로스 개발 — PC에서 만들고, 라즈봇에서 실행")
    # PC 패널
    kp = ap(t, 0.15)
    rbox(d, (70, 250, 690, 930), fill=mix(PANEL, kp), outline=mix(CYAN, kp), r=22, width=4)
    d.text((104, 268), "PC  · 개발 · 학습", font=F(44, "b"), fill=mix(CYAN, kp))
    pc = [("코드 작성", "VS Code · Python"), ("이미지 데이터 생성", "수집 · 라벨링"), ("YOLO11 학습", "GPU · Colab"),
          ("모델 검증", "mAP50 ≥ 0.80 통과만")]
    for i, (a, b) in enumerate(pc):
        st = cue(0.2 + i * 0.5)
        k = ap(t, st, 0.4)
        y = 350 + i * 140
        lit = ap(t, st + 0.2, 0.3)
        rbox(d, (104, y, 656, y + 118), fill=mix(mix(CYAN, 0.15 * lit, PANEL2), k), outline=mix(CYAN if lit else LINE, k), r=16)
        d.text((134, y + 16), a, font=F(38, "b"), fill=mix(WHITE, k, PANEL2))
        d.text((134, y + 68), b, font=F(26, "m"), fill=mix(MUTED, k, PANEL2))
    # Raspbot 패널
    kr = ap(t, cue(2.92) - 0.3)
    rbox(d, (1230, 250, 1850, 930), fill=mix(PANEL, kr), outline=mix(GREEN, kr), r=22, width=4)
    d.text((1264, 268), "Raspbot V2 · 실행", font=F(44, "b"), fill=mix(GREEN, kr))
    chain = ["카메라 영상", "OpenCV ROI · YOLO11", "판단 (우선순위 FSM)", "I2C → 모터 · 서보"]
    flow = ((t - cue(3.4)) * 1.2) % 5 if t > cue(3.4) else -1
    for i, s in enumerate(chain):
        st = cue(2.92) + i * 0.3
        k = ap(t, st, 0.4)
        y = 350 + i * 140
        on = int(flow) == i
        rbox(d, (1264, y, 1816, y + 100), fill=mix(mix(GREEN, 0.28, PANEL2) if on else PANEL2, k),
             outline=mix(GREEN if on else LINE, k), r=16, width=4 if on else 2)
        ctext(d, 1540, y + 26, s, F(38, "b"), mix(WHITE, k, PANEL2))
        if i < 3:
            grow_arrow(d, (1540, y + 102), (1540, y + 136), ap(t, st + 0.3), mix(GREEN, k), 5, 14)
    # 가운데: 일러스트 + 배포/확인 화살표
    ki = ap(t, 0.4, 0.6)
    frame_img(cv, d, kb(CUSTOM / "s2_crossdev.png", (480, 270), t, dur, 0.08), (720, 290), ki, LINE, 16)
    d = ImageDraw.Draw(cv)
    ka = ap(t, cue(4.5), 0.7)
    grow_arrow(d, (712, 650), (1214, 650), ka, YEL, 8, 22)
    ctext(d, 963, 592, "배포  SSH · FTP · best.pt", F(30, "b"), mix(YEL, ka))
    if ka >= 1:
        packet(d, (722, 650), (1196, 650), t, YEL, 4, 0.7, 9)
    kb_ = ap(t, cue(5.6), 0.7)
    grow_arrow(d, (1214, 800), (712, 800), kb_, ORANGE, 8, 22)
    ctext(d, 963, 742, "확인  VNC 화면 · 로그", F(30, "b"), mix(ORANGE, kb_))
    if kb_ >= 1:
        packet(d, (1196, 800), (722, 800), t, ORANGE, 3, 0.6, 8)


def sc_roi(cv, d, t, dur):
    d = tracker(cv, d, 3, t / dur, t)
    head(d, t, 3, "ROI 도로선 인식 — 관심 영역만 보고 방향 결정")
    t_roi, t_mask, t_split, t_dec = cue(1.02), cue(2.34), cue(5.04), cue(7.0)
    src = base(CUSTOM / "s3_lane_cam.png")
    sw, sh = 1040, 582
    sy = sh / src.height
    cam = src.resize((sw, sh), Image.BILINEAR).convert("RGBA")
    y0, y1 = int(mv.ROI_Y[0] * sy), int(mv.ROI_Y[1] * sy)
    k_roi = ap(t, t_roi, 0.7)
    if k_roi > 0:
        dim = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        dd = ImageDraw.Draw(dim)
        dd.rectangle((0, 0, sw, y0), fill=(0, 0, 0, int(150 * k_roi)))
        dd.rectangle((0, y1, sw, sh), fill=(0, 0, 0, int(150 * k_roi)))
        cam = Image.alpha_composite(cam, dim)
    k_mask = ap(t, t_mask, 1.0)
    if k_mask > 0:
        m = mv.ROI_MASK.resize((sw, sh), Image.NEAREST).convert("RGBA")
        scan = int(y0 + (y1 - y0) * k_mask)
        cam.paste(m.crop((0, y0, sw, scan)), (0, y0))
        if k_mask < 1:
            ImageDraw.Draw(cam).line((0, scan, sw, scan), fill=(56, 220, 255, 255), width=4)
    IX, IY = 70, 250
    k_in = ap(t, 0.15, 0.5)
    frame_img(cv, d, cam, (IX, IY), k_in, RED)
    d = ImageDraw.Draw(cv)
    oy = IY + (1 - k_in) * 40
    if k_roi > 0:
        ry1, ry2 = oy + y0, oy + y1
        d.rectangle((IX, ry1, IX + sw * k_roi, ry2), outline=YEL, width=5)
        d.rounded_rectangle((IX + 12, ry1 - 52, IX + 230, ry1 - 8), radius=10, fill=YEL)
        d.text((IX + 24, ry1 - 47), "ROI 관심 영역", font=F(28, "b"), fill=BG)
    k_sp = ap(t, t_split, 0.6)
    if k_sp > 0:
        for i in (1, 2):
            x = IX + sw * i / 3
            d.line((x, oy + y0, x, oy + y0 + (y1 - y0) * k_sp), fill=GREEN, width=4)
        for i, lb in enumerate("LCR"):
            v = mv.ROI_RATIO[i] * ap(t, t_split + 0.3, 1.0)
            cx = IX + sw * (i + 0.5) / 3
            d.rounded_rectangle((cx - 80, oy + y1 - 64, cx + 80, oy + y1 - 12), radius=10, fill=(0, 0, 0))
            ctext(d, cx, oy + y1 - 60, f"{lb} {v * 100:3.0f}%", F(32, "b"), mix(GREEN, k_sp))
    k_dec = back((t - t_dec) / 0.5)
    if k_dec > 0:
        s = f"조향: {mv.ROI_DEC}"
        f = F(46, "b")
        w = tw(d, s, f) + 60
        cx, cy = IX + sw / 2, oy + 90
        sc_ = clamp(k_dec, 0, 1.2)
        d.rounded_rectangle((cx - w / 2 * sc_, cy - 40 * sc_, cx + w / 2 * sc_, cy + 40 * sc_), radius=40, fill=ORANGE)
        if sc_ > 0.7:
            ctext(d, cx, cy - 30, s, f, BG)
            grow_arrow(d, (cx + w / 2 + 30, cy), (cx + w / 2 + 120, cy - 40), ap(t, t_dec + 0.3, 0.4), ORANGE, 8, 22)
    d.text((IX + 6, oy + sh + 12), "커스텀 카메라 이미지에 실제 ROI 처리 적용 (HSV 마스크 · 좌/중/우 픽셀 비율)",
           font=F(24, "m"), fill=mix(MUTED, k_in))
    steps = [("카메라 프레임", WHITE, 0.0), ("ROI 설정", YEL, t_roi), ("색상 필터 · 이진화", CYAN, t_mask),
             ("좌 · 중 · 우 픽셀 비율", GREEN, t_split), ("조향 LEFT / UP / RIGHT", ORANGE, t_dec)]
    x = 1150
    for i, (s, col, st) in enumerate(steps):
        k = ap(t, 0.3 + i * 0.1, 0.4)
        y = IY + i * 118
        active = st <= t < (steps[i + 1][2] if i < 4 else 1e9)
        if active:
            glow_rect(cv, (x, y, x + 700, y + 96), col, 0.6 + 0.4 * math.sin(t * 5), r=16, blur=8)
            d = ImageDraw.Draw(cv)
        fill = mix(mix(col, 0.22, PANEL2), k) if active else mix(PANEL2, k)
        rbox(d, (x, y, x + 700, y + 96), fill=fill, outline=mix(col if t >= st else LINE, k), r=16, width=3)
        d.text((x + 26, y + 22), f"{i + 1}", font=F(38, "b"), fill=mix(col, k, PANEL2))
        d.text((x + 80, y + 22), s, font=F(38, "b"), fill=mix(WHITE if t >= st else MUTED, k, PANEL2))
        if t >= st + 0.4 and not active:
            check(d, x + 656, y + 48, 24, GREEN, 5, ap(t, st + 0.4, 0.3))


def sc_yolo(cv, d, t, dur):
    d = tracker(cv, d, 4, t / dur, t)
    head(d, t, 4, "YOLO11 인식 — PC에서 학습 · 검증, 통과 모델만 배포")
    steps = [("수집", cue(2.8)), ("라벨링", cue(3.9)), ("학습", cue(5.0)), ("검증", cue(6.52)), ("배포", cue(8.7))]
    x0, y0, bw, gap = 120, 236, 300, 34
    d.text((70, y0 + 16), "PC", font=F(26, "b"), fill=mix(CYAN, ap(t, 0.2)))
    for i, (s, st) in enumerate(steps):
        x = x0 + i * (bw + gap)
        k = ap(t, 0.2 + i * 0.08)
        lit = t >= st
        active = lit and (i == 4 or t < steps[i + 1][1])
        col = GREEN if i == 4 else (YEL if i == 3 else CYAN)
        if active:
            glow_rect(cv, (x, y0, x + bw, y0 + 64), col, 0.5 + 0.5 * math.sin(t * 5), r=32, blur=8)
            d = ImageDraw.Draw(cv)
        rbox(d, (x, y0, x + bw, y0 + 64), fill=mix(mix(col, 0.3, PANEL2) if lit else PANEL2, k),
             outline=mix(col if lit else LINE, k), r=32, width=3)
        ctext(d, x + bw / 2, y0 + 12, s, F(32, "b"), mix(WHITE if lit else MUTED, k, PANEL2))
        if lit and i < 4:
            check(d, x + bw - 36, y0 + 32, 18, GREEN, 4, ap(t, st + 0.3, 0.3)) if t >= steps[i + 1][1] else None
        if i < 4:
            grow_arrow(d, (x + bw + 4, y0 + 32), (x + bw + gap - 4, y0 + 32), k, mix(LINE, k), 3, 10)
    # 검출 장면
    sw, sh, IX, iy = 1000, 560, 70, 330
    src = base(CUSTOM / "s4_yolo_scene.png")
    sx, sy = sw / src.width, sh / src.height
    ki = ap(t, 0.2, 0.5)
    frame_img(cv, d, src.resize((sw, sh), Image.BILINEAR), (IX, iy), ki, YEL)
    d = ImageDraw.Draw(cv)
    oy = iy + (1 - ki) * 40
    if 0.3 < t < 1.6:
        p = clamp((t - 0.3) / 1.2)
        d.line((IX, oy + sh * p, IX + sw, oy + sh * p), fill=CYAN, width=3)
        d.text((IX + 16, oy + 14), "YOLO11n 추론 · 320×320", font=F(26, "b"), fill=CYAN)
    for j, (bx, cls, conf, col, _) in enumerate(mv.YOLO_BOXES):
        st = 1.2 + j * 0.3
        k = ap(t, st, 0.4)
        if k <= 0:
            continue
        x1, y1, x2, y2 = IX + bx[0] * sx, oy + bx[1] * sy, IX + bx[2] * sx, oy + bx[3] * sy
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        s = 1.5 - 0.5 * k
        bx1, by1, bx2, by2 = cx - (cx - x1) * s, cy - (cy - y1) * s, cx + (x2 - cx) * s, cy + (y2 - cy) * s
        d.rectangle((bx1, by1, bx2, by2), outline=rgba(col, k), width=5)
        lab = f"{cls} {conf * ap(t, st, 0.7):.2f}"
        f = F(26, "b")
        lw = tw(d, lab, f) + 20
        d.rectangle((bx1 - 2, by1 - 38, bx1 + lw, by1), fill=rgba(col, k))
        d.text((bx1 + 8, by1 - 35), lab, font=f, fill=rgba(BG, k))
    d.text((IX + 6, oy + sh + 10), "검출 예시 (커스텀 일러스트) · 클래스 car · green · red · oo · xx", font=F(24, "m"),
           fill=mix(MUTED, ki))
    # 오른쪽: 실제 학습 곡선
    px, py, pw, ph = 1110, 330, 740, 560
    kc = ap(t, cue(5.8), 0.5)
    if kc <= 0:
        return
    rbox(d, (px, py, px + pw, py + ph), fill=mix(PANEL, kc), outline=mix(LINE, kc), r=18)
    d.text((px + 24, py + 16), "검증 — 실제 학습 곡선 (best.pt)", font=F(30, "b"), fill=mix(WHITE, kc))
    gx1, gy1, gx2, gy2 = px + 70, py + 80, px + pw - 30, py + 360

    def X(e):
        return gx1 + (gx2 - gx1) * (e - 1) / 99

    def Y(v):
        return gy2 - (gy2 - gy1) * (v - 0.6) / 0.4
    for v in (0.6, 0.7, 0.8, 0.9, 1.0):
        d.line((gx1, Y(v), gx2, Y(v)), fill=mix((40, 55, 85), kc), width=1)
        d.text((gx1 - 58, Y(v) - 14), f"{v:.1f}", font=F(22, "m"), fill=mix(MUTED, kc))
    d.line((gx1, Y(0.8), gx2, Y(0.8)), fill=mix(RED, kc), width=3)
    d.text((gx2 - 200, Y(0.8) + 6), "합격선 mAP50 0.80", font=F(22, "b"), fill=mix(RED, kc))
    kl = ap(t, cue(6.3), 1.4)
    pts = [(X(e), Y(v)) for e, v in mv.EPOCHS]
    drawn = kl * (len(pts) - 1)
    line = [pts[0]]
    for i in range(len(pts) - 1):
        if drawn >= i + 1:
            line.append(pts[i + 1])
        elif drawn > i:
            q = drawn - i
            line.append((pts[i][0] + (pts[i + 1][0] - pts[i][0]) * q, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * q))
            break
    if len(line) > 1:
        d.line(line, fill=YEL, width=5, joint="curve")
    for p in pts:
        if p[0] <= line[-1][0] + 1:
            d.ellipse((p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6), fill=YEL)
    d.text((gx1, gy2 + 2), "epoch 1", font=F(20, "m"), fill=mix(MUTED, kc))
    d.text((gx2 - 90, gy2 + 2), "epoch 100", font=F(20, "m"), fill=mix(MUTED, kc))
    km = ap(t, cue(7.3), 0.8)
    for i, (n, v, col) in enumerate([("mAP50", 0.988, YEL), ("Precision", 0.957, CYAN), ("Recall", 0.986, GREEN)]):
        x = px + 30 + i * 235
        d.text((x, gy2 + 40), n, font=F(24, "m"), fill=mix(MUTED, km))
        d.text((x, gy2 + 70), f"{v * km:.3f}", font=F(44, "b"), fill=mix(col, km))
    kp = clamp(back((t - cue(8.7)) / 0.5))
    if kp > 0:
        s = "PASS → 라즈봇 배포 (NCNN)"
        f = F(30, "b")
        w = tw(d, s, f) + 40
        d.rounded_rectangle((px + pw - w - 24, py + ph - 64, px + pw - 24, py + ph - 18), radius=23, fill=mix(GREEN, kp))
        d.text((px + pw - w - 4, py + ph - 59), s, font=f, fill=BG)


def sc_stages(cv, d, t, dur):
    d = tracker(cv, d, 5, t / dur, t)
    head(d, t, 5, "6차시 단계도 — 20시간, 실습 중심")
    cols = mv.SCOL
    topics = [["조립", "앱 실행"], ["동작 원리", "개발환경"], ["ROI", "기본 자율주행"], ["Haar 개요", "YOLO11 학습"],
              ["자율주행", "+ YOLO11"], ["최종 테스트", "코칭"]]
    gates = ["앱으로 주행", "코드로 제어", "트랙 완주", "best.pt 검증", "신호 · 장애물 · 주차", "평가 · 회고"]
    bw, gap, y = 272, 26, 250
    t_chk = cue(4.44)
    for i in range(6):
        name, date, hrs = mv.SESS[i]
        col = cols[i]
        k = ap(t, 0.2 + i * 0.3, 0.5)
        if k <= 0:
            continue
        x = 70 + i * (bw + gap)
        yy = y + (1 - k) * 40
        done = ap(t, t_chk + i * 0.22, 0.35)
        if 0 < done < 1:
            glow_rect(cv, (x, yy, x + bw, yy + 420), col, 1 - done, r=20, blur=10)
            d = ImageDraw.Draw(cv)
        rbox(d, (x, yy, x + bw, yy + 420), fill=mix(PANEL2, k), outline=mix(col, k), r=20, width=4)
        d.ellipse((x + bw / 2 - 40, yy + 24, x + bw / 2 + 40, yy + 104), fill=mix(GREEN if done >= 1 else col, k, PANEL2))
        if done > 0:
            check(d, x + bw / 2, yy + 64, 34, BG, 7, done)
        else:
            ctext(d, x + bw / 2, yy + 34, str(i + 1), F(48, "b"), mix(BG, k, PANEL2))
        ctext(d, x + bw / 2, yy + 128, f"{date} · {hrs}H", F(28, "m"), mix(MUTED, k, PANEL2))
        for j, ln in enumerate(topics[i]):
            ctext(d, x + bw / 2, yy + 180 + j * 46, ln, F(36, "b"), mix(WHITE, k, PANEL2))
        d.line((x + 30, yy + 300, x + bw - 30, yy + 300), fill=mix(LINE, k, PANEL2), width=2)
        ctext(d, x + bw / 2, yy + 320, "통과 조건", F(24, "m"), mix(MUTED, k, PANEL2))
        ctext(d, x + bw / 2, yy + 352, gates[i], F(28, "b"), mix(col, k, PANEL2))
        if i < 5:
            grow_arrow(d, (x + bw + 3, y + 210), (x + bw + gap - 3, y + 210), ap(t, 0.4 + i * 0.3), mix(MUTED, k), 4, 10)
    # 이론 / 실습 비율
    kb_ = ap(t, cue(2.94), 0.9)
    x0, x1, yb = 70, 1850, 760
    d.text((x0, yb - 54), "시간 배분", font=F(32, "b"), fill=mix(WHITE, kb_))
    th = (x1 - x0) * 0.133
    if kb_ > 0:
        d.rounded_rectangle((x0, yb, x0 + th * kb_, yb + 72), radius=12, fill=PURPLE)
        d.rounded_rectangle((x0 + th + 8, yb, x0 + th + 8 + (x1 - x0 - th - 8) * kb_, yb + 72), radius=12, fill=GREEN)
    if kb_ > 0.6:
        d.text((x0 + 20, yb + 15), "이론 2h40m", font=F(32, "b"), fill=BG)
        d.text((x0 + th + 30, yb + 15), "실습 17h20m (87%) — 이론은 차시당 1시간 이내", font=F(32, "b"), fill=BG)


def sc_end(cv, d, t, dur):
    bg = kb(ASSETS / "track_top_2.jpg", (W, 800), t, dur, 0.08).filter(ImageFilter.GaussianBlur(5))
    paste(cv, bg, (0, 170), 0.5 * ap(t, 0.0, 0.8), 0)
    d = ImageDraw.Draw(cv)
    d = tracker(cv, d, 6, 1, t, finale=0.2)
    k = ap(t, 1.2)
    ctext(d, W / 2, 300, "구조 5가지 체크 완료", F(44, "b"), mix(GREEN, k))
    flow = [("단계도", YEL), ("실습", GREEN), ("검증", CYAN)]
    bw, gap = 360, 120
    x0 = (W - (bw * 3 + gap * 2)) / 2
    for i, (s, col) in enumerate(flow):
        kk = clamp(back((t - 1.4 - i * 0.3) / 0.5))
        if kk <= 0:
            continue
        x = x0 + i * (bw + gap)
        rbox(d, (x, 400, x + bw, 550), fill=mix(PANEL2, kk), outline=mix(col, kk), r=26, width=5)
        ctext(d, x + bw / 2, 438, s, F(62, "b"), mix(col, kk, PANEL2))
        if i < 2:
            grow_arrow(d, (x + bw + 14, 475), (x + bw + gap - 14, 475), ap(t, 1.6 + i * 0.3), WHITE, 7)
    k2 = ap(t, 2.4)
    ctext(d, W / 2, 640, "PC에서 만들고 검증하고, 라즈봇에서 달린다", F(56, "b"), mix(WHITE, k2))
    ctext(d, W / 2, 730, "Raspbot V2 · 컴퓨터 비전 자율주행 20시간 과정", F(32, "m"), mix(MUTED, k2))


# ------------------------------------------------------------------ 대본
SCENES = [
    dict(fn=sc_title, narr="00", cap="라즈봇 V2 자율주행 20시간 — 핵심 구조 1분 정리"),
    dict(fn=sc_goal, narr="01", cap="목표: 도로선 주행 + 신호등 · 장애물 · 주차 표지 인식 → 자동 주차"),
    dict(fn=sc_cross, narr="02", cap="크로스 개발: 코드 · 모델은 PC에서, 라즈봇은 실행에 집중"),
    dict(fn=sc_roi, narr="03", cap="ROI에서 도로선 검출 → 좌 · 우 비율로 조향 결정"),
    dict(fn=sc_yolo, narr="04", cap="YOLO11: PC에서 수집 · 라벨링 · 학습 → 검증 통과 모델만 배포"),
    dict(fn=sc_stages, narr="05", cap="6차시 · 20시간, 실습 중심으로 하나씩 완성"),
    dict(fn=sc_end, narr="06", cap="단계마다 만들고 검증하며 컴퓨터 비전 개발 프로세스를 익힙니다"),
]


def prep_audio(tmp: Path):
    for sc in SCENES:
        dst = tmp / f"{sc['narr']}.wav"
        af = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
              "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
              f"atempo={TEMPO},aresample=48000")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(NARR / f"{sc['narr']}.mp3"), "-af", af, "-ac", "1",
                        str(dst)], check=True)
        dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                             "-of", "csv=p=0", str(dst)]).decode())
        sc["wav"], sc["dur"] = dst, LEAD + dur + TAIL


def mix_audio(tmp: Path, starts, total):
    inputs, filt = [], []
    for i, sc in enumerate(SCENES):
        inputs += ["-i", str(sc["wav"])]
        ms = int((starts[i] + LEAD) * 1000)
        filt.append(f"[{i}]adelay={ms}|{ms}[a{i}]")
    filt.append("".join(f"[a{i}]" for i in range(len(SCENES))) +
                f"amix=inputs={len(SCENES)}:normalize=0,loudnorm=I=-16:TP=-1.5,apad,atrim=0:{total:.3f}[out]")
    wav = tmp / "narration.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filt), "-map", "[out]",
                    "-ac", "2", "-ar", "48000", str(wav)], check=True)
    return wav


def render(sc, t, gt, cap=True):
    cv = Image.new("RGBA", (W, H), BG + (255,))
    mv.background(cv, gt)
    d = ImageDraw.Draw(cv)
    sc["fn"](cv, d, t, sc["dur"])
    d = ImageDraw.Draw(cv)
    if cap:
        mv.caption(cv, d, sc["cap"], ap(t, LEAD - 0.2, 0.3) * (1 - ap(t, sc["dur"] - 0.35, 0.3)))
    return cv


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stills", action="store_true")
    args = p.parse_args()
    mv.ROI_MASK, mv.ROI_RATIO, mv.ROI_DEC = mv.roi_process()
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
        for old in STILLS.glob("*.png"):
            old.unlink()
        for i, sc in enumerate(SCENES):
            render(sc, sc["dur"] - 0.6, starts[i] + sc["dur"] - 0.6, cap=False).convert("RGB").save(
                STILLS / f"{i + 1:02d}_{sc['fn'].__name__[3:]}.png")
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
                frame = Image.blend(render(SCENES[idx - 1], gt - starts[idx - 1], gt), frame,
                                    ease((gt - starts[idx]) / FADE))
            ImageDraw.Draw(frame).rectangle((0, H - 6, W * gt / total, H), fill=YEL)
            proc.stdin.write(np.asarray(frame.convert("RGB")).tobytes())
            if fi % 300 == 0:
                print(f"  frame {fi}/{n}")
        proc.stdin.close()
        proc.wait()
    print(f"video → {OUT}  ({total:.1f}s)")


if __name__ == "__main__":
    main()
