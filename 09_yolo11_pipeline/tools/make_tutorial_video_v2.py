"""
YOLO11 학습 튜토리얼 영상 v2 — 원본(make_tutorial_video.py)과 같은 내용을
  ① 자연스러운 한국어 나레이션 (Higgsfield MiniMax 'Hana', 캐시: demo/tutorial_v2/audio/NN.mp3)
  ② 장면마다 일러스트 (demo/tutorial_v2/illust/sNN.png): 전체 화면 인트로 카드 + 흐린 움직이는 배경
  ③ 움직임: 인트로 카드 줌/슬라이드 전환, 자막 팝업 + 키워드 노란 강조, 진행 바
로 다시 렌더링합니다. 장면 내용(그림·표·애니메이션)은 원본 스크립트의 것을 그대로 씁니다.

사용 예:
  python tools/make_tutorial_video_v2.py
  python tools/make_tutorial_video_v2.py --preview 5 8      # 장면 미리보기 PNG
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import make_tutorial_video as v1  # noqa: E402  (장면 정의·그리기 함수 재사용)

W, H, FPS = 1280, 720, 30
WORK = ROOT / "demo/tutorial_v2"
HERO = 2.3            # 장면 시작 인트로 카드 길이(초)
REVEAL = 0.55         # 인트로 → 본문 전환 시간
GAP, TAIL = 0.35, 0.8
TEMPO = 1.12
YEL = (255, 214, 10)


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def back(x):
    x = max(0.0, min(1.0, x))
    c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


# ------------------------------------------------------------------ 이미지 준비
def cover(img, w, h):
    s = max(w / img.width, h / img.height)
    im = img.resize((int(img.width * s) + 1, int(img.height * s) + 1), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def make_bg(ill):
    """흐리고 어둡게 만든 배경 (1.15배 크기 → 프레임마다 천천히 이동)."""
    big = cover(ill, int(W * 1.15), int(H * 1.15)).filter(ImageFilter.GaussianBlur(18))
    arr = np.asarray(big).astype(np.float32) * 0.28
    tint = np.array(v1.BG, np.float32)
    arr = arr * 0.75 + tint * 0.6
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def header_layer(sc):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    if sc["title"]:
        col = v1.STEP_COLORS[sc["step"]] if sc["step"] else v1.CYAN
        f = v1.font(18, "b")
        tw = d.textlength(sc["chip"], font=f)
        d.rounded_rectangle((40, 30, 40 + tw + 28, 66), radius=18, fill=col)
        d.text((54, 36), sc["chip"], font=f, fill=v1.BG)
        d.text((40 + tw + 46, 28), sc["title"], font=v1.font(32, "b"), fill=v1.TXT)
    for i in range(9):
        x = 1000 + i * 24
        cur = sc["step"] == i + 1
        done = sc["step"] and i + 1 < sc["step"]
        col = v1.STEP_COLORS[i + 1] if (cur or done) else v1.PANEL2
        r = 8 if cur else 5
        d.ellipse((x - r, 48 - r, x + r, 48 + r), fill=col)
    return layer


KEY_RE = re.compile(r"([A-Za-z0-9][A-Za-z0-9._%/\-+]*)")


def caption_layer(text):
    """자막: 영문·숫자 토큰을 노란색으로 강조."""
    f = v1.font(29, "b")
    lines = v1.wrap(text, f, W - 180)[:3]
    h = 34 + len(lines) * 42
    cap = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(cap)
    d.rounded_rectangle((60, 4, W - 60, h - 4), radius=22, fill=(2, 6, 23, 215))
    for i, ln in enumerate(lines):
        parts = [(p, bool(KEY_RE.fullmatch(p))) for p in KEY_RE.split(ln) if p]
        x = (W - d.textlength(ln, font=f)) / 2
        y = 18 + i * 42
        for p, hl in parts:
            d.text((x, y), p, font=f, fill=YEL if hl else (255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
            x += d.textlength(p, font=f)
    return cap


def hero_frame(sc, ill, k_zoom, idx, total_scenes):
    """장면 인트로 카드: 일러스트 + 큰 제목."""
    z = 1.0 + 0.07 * k_zoom
    im = cover(ill, int(W * z), int(H * z))
    x, y = (im.width - W) // 2, (im.height - H) // 2
    im = im.crop((x, y, x + W, y + H)).convert("RGBA")
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for i in range(380):
        a = int(235 * (i / 380) ** 1.3)
        gd.line([(0, H - 380 + i), (W, H - 380 + i)], fill=(4, 8, 22, a))
    im.alpha_composite(grad)
    return im


def draw_hero_text(img, sc, t):
    d = ImageDraw.Draw(img)
    col = v1.STEP_COLORS[sc["step"]] if sc["step"] else v1.CYAN
    title = sc["title"] or "YOLO11 객체 인식 모델 만들기"
    chip = sc["chip"] if sc["title"] else "TUTORIAL"
    k1, k2 = back((t - 0.15) / 0.45), ease((t - 0.35) / 0.5)
    f = v1.font(26, "b")
    tw = d.textlength(chip, font=f)
    x0 = 70 - (1 - k1) * 200
    d.rounded_rectangle((x0, H - 320, x0 + tw + 40, H - 275), radius=22, fill=col)
    d.text((x0 + 20, H - 315), chip, font=f, fill=v1.BG)
    ft = v1.font(60, "b")
    d.text((70 + (1 - k2) * 80, H - 262), title, font=ft, fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))


# ------------------------------------------------------------------ 오디오
def build_timeline(lines_audio):
    timeline, cur, gi = [], 0.0, 0
    for sc in v1.SCENES:
        marks, clips, t = [], [], 0.6
        for _ in sc["lines"]:
            wav, dur = lines_audio[gi]
            gi += 1
            marks.append(t)
            clips.append((wav, cur + t))
            t += dur + GAP
        total = max(t + TAIL, HERO + 2.0)
        timeline.append({"start": cur, "dur": total, "marks": marks, "clips": clips})
        cur += total
    return timeline, cur


def prepare_audio(use_hf):
    out = []
    (WORK / "wav").mkdir(parents=True, exist_ok=True)
    gi = 0
    for sc in v1.SCENES:
        for cap, say in sc["lines"]:
            mp3 = WORK / "audio" / f"{gi:02d}.mp3"
            wav = WORK / "wav" / f"{gi:02d}.wav"
            if use_hf and mp3.exists():
                src = mp3
            else:
                src = WORK / "wav" / f"{gi:02d}.aiff"
                subprocess.run(["say", "-v", "Yuna", "-r", "185", "-o", str(src), say], check=True)
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af", f"atempo={TEMPO}", "-ar", "44100",
                            "-ac", "1", "-sample_fmt", "s16", str(wav)], check=True)
            with wave.open(str(wav)) as w:
                out.append((wav, w.getnframes() / w.getframerate()))
            gi += 1
    return out


def mix(timeline, total, path, sr=44100):
    buf = np.zeros(int((total + 1) * sr), np.int32)
    for tl in timeline:
        for wav, st in tl["clips"]:
            with wave.open(str(wav)) as w:
                data = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.int32)
            s = int(st * sr)
            buf[s:s + len(data)] += data[: len(buf) - s]
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(np.clip(buf, -32768, 32767).astype(np.int16).tobytes())


# ------------------------------------------------------------------ 렌더링
class SceneCache:
    def __init__(self, si):
        sc = v1.SCENES[si]
        self.sc = sc
        self.ill = Image.open(WORK / "illust" / f"s{si:02d}.png").convert("RGB")
        self.bg = make_bg(self.ill)
        self.header = header_layer(sc)
        self.caps = [caption_layer(c) for c, _ in sc["lines"]]


def render(si, cache, t, tl, g_t, g_total):
    sc = cache.sc
    T = tl["dur"]
    # 배경: 흐린 일러스트가 천천히 이동
    k = t / T
    bx = int((cache.bg.width - W) * (0.15 + 0.7 * k))
    by = int((cache.bg.height - H) * (0.5 + 0.3 * np.sin(k * 3.0)) * 0.9)
    img = cache.bg.crop((bx, by, bx + W, by + H)).copy()
    # 본문 (원본 장면 그리기 함수 그대로) — 인트로 동안은 시간을 늦춰 시작
    tc = max(0.0, t - (HERO - REVEAL))
    m = tl["marks"]
    mm = [m[0]] + [max(m[i] - (HERO - REVEAL), m[0] + 0.4 * i) for i in range(1, len(m))]
    content = img.copy()
    v1.BG_SAVE = v1.BG
    sc["draw"](content, ImageDraw.Draw(content), tc, mm, T - (HERO - REVEAL))
    content = content.convert("RGBA")
    content.alpha_composite(cache.header)
    idx = max([i for i, mk in enumerate(m) if mk <= t] or [-1])
    # 인트로 카드
    if t < HERO:
        hero = hero_frame(sc, cache.ill, t / HERO, si, len(v1.SCENES))
        draw_hero_text(hero, sc, t)
        r = (t - (HERO - REVEAL)) / REVEAL
        if r > 0:      # 인트로 카드가 커지며 사라짐
            e = ease(r)
            s = 1 + 0.18 * e
            hero = hero.resize((int(W * s), int(H * s)), Image.BILINEAR)
            x, y = (hero.width - W) // 2, (hero.height - H) // 2
            hero = hero.crop((x, y, x + W, y + H))
            hero.putalpha(hero.getchannel("A").point(lambda v: int(v * (1 - e))))
        if t < 0.4:    # 새 장면 인트로가 오른쪽에서 밀려 들어옴
            e = ease(t / 0.4)
            off = int((1 - e) * W * 0.35)
            hero.putalpha(hero.getchannel("A").point(lambda v: int(v * e)))
            content = Image.new("RGBA", (W, H), (*v1.BG, 255))
            content.alpha_composite(hero, (off, 0))
        else:
            content.alpha_composite(hero)
    # 자막 (항상 맨 위, 새 문장마다 팝업)
    if idx >= 0:
        cap = cache.caps[idx]
        ck = back((t - m[idx]) / 0.3)
        if ck < 0.999:
            s = 0.88 + 0.12 * ck
            cap = cap.resize((int(cap.width * s), max(1, int(cap.height * s))), Image.BILINEAR)
        content.alpha_composite(cap, ((W - cap.width) // 2, H - cap.height - 14))
    # 장면 끝: 살짝 어두워짐
    end = (T - t) / 0.3
    if end < 1:
        dark = Image.new("RGBA", (W, H), (*v1.BG, int(255 * (1 - max(0, end)))))
        content.alpha_composite(dark)
    d = ImageDraw.Draw(content)
    d.rectangle((0, H - 5, W, H), fill=(30, 41, 59))
    d.rectangle((0, H - 5, int(W * g_t / g_total), H), fill=YEL)
    return content.convert("RGB")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(ROOT / "docs/video/YOLO11_학습_튜토리얼.mp4"))
    ap.add_argument("--srt", default=str(ROOT / "docs/video/자막/YOLO11_학습_튜토리얼.srt"))
    ap.add_argument("--no-hf", action="store_true")
    ap.add_argument("--preview", type=int, nargs="*")
    args = ap.parse_args()
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg 필요")
    v1.load_assets()
    audio = prepare_audio(not args.no_hf)
    timeline, total = build_timeline(audio)
    print(f"총 길이 {total / 60:.1f}분, 장면 {len(timeline)}")

    if args.preview is not None:
        pd = WORK / "preview"
        pd.mkdir(exist_ok=True)
        for si in (args.preview or range(len(v1.SCENES))):
            cache, tl = SceneCache(si), timeline[si]
            for tag, t in (("hero", 1.0), ("rev", HERO - 0.25), ("mid", tl["dur"] * 0.7)):
                render(si, cache, t, tl, tl["start"] + t, total).save(pd / f"s{si:02d}_{tag}.png")
        print(f"미리보기: {pd}")
        return

    wavp = WORK / "narration.wav"
    mix(timeline, total, wavp)
    meta = WORK / "chapters.txt"
    v1.write_chapters(timeline, meta)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", str(wavp), "-i", str(meta), "-map", "0:v", "-map", "1:a", "-map_metadata", "2",
           "-map_chapters", "2", "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-af", "loudnorm=I=-16:TP=-1.5", "-movflags", "+faststart",
           "-t", f"{total:.2f}", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for si, tl in enumerate(timeline):
        cache = SceneCache(si)
        nf = int(round(tl["dur"] * FPS))
        for f in range(nf):
            t = f / FPS
            p.stdin.write(render(si, cache, t, tl, tl["start"] + t, total).tobytes())
        print(f"  장면 {si + 1}/{len(timeline)}", end="\r")
    p.stdin.close()
    if p.wait() != 0:
        sys.exit("인코딩 실패")
    srt = Path(args.srt)
    srt.parent.mkdir(parents=True, exist_ok=True)
    v1.write_srt(timeline, srt)
    print(f"\n영상: {out} ({out.stat().st_size / 1e6:.1f} MB, {total / 60:.1f}분)\n자막: {srt}")


if __name__ == "__main__":
    main()
