"""
Raspberry Pi Wi-Fi 연결 가이드 영상 (1920x1080, 30fps)

- 화면: 레포 루트의 「Raspberry Pi Wi-Fi 연결하기.pptx」 슬라이드 5장
- 나레이션: macOS 내장 한국어 음성 'Yuna' (say 명령, 무료·오프라인)
- 자막: 문장마다 하단에 반투명 자막 (make_session_video.py 와 같은 스타일)

사용 예:
  python3 make_wifi_guide_video.py            # 영상 생성
  python3 make_wifi_guide_video.py --stills   # 자막 입힌 PNG만 확인 (_wifi_build/)
필요: Pillow, LibreOffice, pdftoppm(poppler), ffmpeg, macOS say
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
PPTX = REPO / "Raspberry Pi Wi-Fi 연결하기.pptx"
OUT = HERE / "Raspberry_Pi_WiFi_연결_가이드.mp4"
BUILD = HERE / "_wifi_build"
SOFFICE = "/Applications/LibreOffice.app/Contents/MacOS/soffice"

W, H, FPS = 1920, 1080, 30
VOICE, RATE = "Yuna", 190   # say 음성 · 분당 단어 수
LEAD_MS = 250               # 문장 시작 전 무음
GAP = 0.45                  # 문장 끝 뒤 여백(초)
SLIDE_TAIL = 0.6            # 슬라이드 마지막 문장 뒤 추가 여백(초)

SD = "/System/Library/Fonts/AppleSDGothicNeo.ttc"

# (자막, 읽는 문장) — 영어·명령어는 읽는 문장에서 한글 발음으로 바꿈. 읽는 문장이 None 이면 자막 그대로 읽음
SCRIPT: list[list[tuple[str, str | None]]] = [
    [  # 1. 표지
        ("라즈베리 파이를 Wi-Fi 에 연결하는 방법을 알아보겠습니다.",
         "라즈베리 파이를 와이파이에 연결하는 방법을 알아보겠습니다."),
        ("Bookworm 부터는 wpa_supplicant.conf 를 고쳐도 반영되지 않습니다.",
         "북웜 버전부터는, 더블유피에이 서플리컨트 설정 파일을 고쳐도 반영되지 않습니다."),
        ("그래서 wifi_setup.sh 스크립트로, 4단계만에 연결합니다.",
         "그래서 와이파이 셋업 스크립트로, 네 단계만에 연결합니다."),
        ("1·2단계는 Mac 터미널, 3·4단계는 Pi 터미널에서 진행합니다.",
         "일, 이 단계는 맥 터미널, 삼, 사 단계는 파이 터미널에서 진행합니다."),
    ],
    [  # 2. 복사 · 접속
        ("먼저 Mac 터미널에서 scp 로 스크립트를 Pi 에 복사합니다.",
         "먼저 맥 터미널에서, 에스씨피 명령으로 스크립트를 파이에 복사합니다."),
        ("이 단계를 빼먹으면 No such file or directory 오류가 납니다.",
         "이 단계를 빼먹으면, 노 서치 파일 오류가 납니다."),
        ("다음으로 ssh pi@pi.local 로 접속합니다.",
         "다음으로, 에스에스에이치 파이 골뱅이 파이 닷 로컬로 접속합니다."),
        ("프롬프트가 초록색 pi@pi 로 바뀌었는지 꼭 확인하세요.",
         "프롬프트가 초록색 파이 골뱅이 파이로 바뀌었는지 꼭 확인하세요."),
        ("pi.local 이 안 되면 IP 주소로 접속하면 됩니다.",
         "파이 닷 로컬이 안 되면, 아이피 주소로 접속하면 됩니다."),
    ],
    [  # 3. 실행
        ("Pi 터미널에서 sudo bash ~/wifi_setup.sh 를 실행합니다.",
         "파이 터미널에서, 수도 배시 명령으로 스크립트를 실행합니다."),
        ("맨 위에 연결 상태, IP 주소, 인터넷 여부가 표시됩니다.",
         "맨 위에 현재 연결 상태와 아이피 주소, 인터넷 여부가 표시됩니다."),
        ("처음 설정할 때는 1번, 주변 Wi-Fi 검색을 고릅니다.",
         "처음 설정할 때는 일번, 주변 와이파이 검색을 고릅니다."),
    ],
    [  # 4. 선택 · 연결
        ("주변 Wi-Fi 가 신호가 센 순서로 나타납니다.",
         "주변 와이파이가 신호가 센 순서로 나타납니다."),
        ("연결할 Wi-Fi 번호를 입력합니다. 예) edu → 3",
         "연결할 와이파이의 번호를 입력합니다. 예를 들어 에듀는 삼번입니다."),
        ("비밀번호를 두 번 입력합니다. 화면에 안 보이는 것이 정상입니다.",
         "비밀번호를 두 번 입력합니다. 화면에 보이지 않는 것이 정상입니다."),
        ("우선순위는 Enter 를 누르면 기본값 10 이 들어갑니다.",
         "우선순위는 엔터를 누르면 기본값 십이 들어갑니다."),
        ("지금 연결할지 물으면 y. SSH 창이 끊기는 것은 정상입니다.",
         "지금 연결할지 물으면 와이를 누릅니다. 이때 에스에스에이치 창이 끊기는 것은 정상입니다."),
    ],
    [  # 5. 연결 확인
        ("Pi 의 IP 주소가 바뀌어서 이전 SSH 창은 멈춥니다.",
         "파이의 아이피 주소가 바뀌었기 때문에, 이전 에스에스에이치 창은 멈춥니다."),
        ("Mac 도 같은 공유기에 연결한 뒤 ssh pi@pi.local 로 다시 접속합니다.",
         "맥도 같은 공유기에 연결한 뒤, 파이 닷 로컬로 다시 접속합니다."),
        ("status 에서 ✔ 인터넷 연결 정상 이 보이면 완료입니다.",
         "스테이터스 명령에서, 인터넷 연결 정상이 보이면 완료입니다."),
    ],
]


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def render_slides(work: Path) -> list[Path]:
    """pptx → pdf → 1920x1080 png"""
    prof = work / "lo_profile"
    run([SOFFICE, f"-env:UserInstallation=file://{prof}", "--headless",
         "--convert-to", "pdf", "--outdir", str(work), str(PPTX)])
    pdf = work / (PPTX.stem + ".pdf")
    run(["pdftoppm", "-png", "-scale-to-x", str(W), "-scale-to-y", str(H), str(pdf), str(work / "slide")])
    slides = sorted(work.glob("slide-*.png"))
    if len(slides) != len(SCRIPT):
        raise SystemExit(f"슬라이드 {len(slides)}장 ≠ 나레이션 {len(SCRIPT)}개")
    return slides


def with_caption(slide: Path, text: str, out: Path) -> None:
    cv = Image.open(slide).convert("RGBA").resize((W, H))
    d = ImageDraw.Draw(cv)
    f = ImageFont.truetype(SD, 38, index=4)  # SemiBold
    w = d.textlength(text, font=f)
    pad = 32
    x1, y1 = (W - w) / 2 - pad, 972
    ov = Image.new("RGBA", (int(w + pad * 2), 68), (0, 0, 0, 0))
    ImageDraw.Draw(ov).rounded_rectangle((0, 0, w + pad * 2, 67), radius=16, fill=(0, 0, 0, 185))
    cv.alpha_composite(ov, (int(x1), y1))
    d.text(((W - w) / 2, y1 + 11), text, font=f, fill=(255, 255, 255, 255))
    cv.convert("RGB").save(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", action="store_true", help="자막 입힌 PNG만 _wifi_build/ 에 저장")
    args = ap.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        slides = render_slides(work)

        if args.stills:
            BUILD.mkdir(exist_ok=True)
            for si, (slide, lines) in enumerate(zip(slides, SCRIPT), 1):
                with_caption(slide, lines[0][0], BUILD / f"still_{si}.png")
            print("saved stills →", BUILD)
            return

        segs: list[Path] = []
        for si, (slide, lines) in enumerate(zip(slides, SCRIPT), 1):
            for li, (cap, speech) in enumerate(lines, 1):
                tag = f"{si:02d}_{li:02d}"
                img, wav, seg = work / f"{tag}.png", work / f"{tag}.aiff", work / f"{tag}.mp4"
                with_caption(slide, cap, img)
                run(["say", "-v", VOICE, "-r", str(RATE), "-o", str(wav), speech or cap])
                pad = GAP + (SLIDE_TAIL if li == len(lines) else 0)
                run(["ffmpeg", "-y", "-loop", "1", "-framerate", str(FPS), "-i", str(img), "-i", str(wav),
                     "-af", f"adelay={LEAD_MS}:all=1,apad=pad_dur={pad}",
                     "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-r", str(FPS),
                     "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2", "-shortest", str(seg)])
                segs.append(seg)
                print("  ✔", tag, cap)

        lst = work / "list.txt"
        lst.write_text("".join(f"file '{p}'\n" for p in segs))
        joined = work / "joined.mp4"
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined)])

        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                    "-of", "csv=p=0", str(joined)], capture_output=True, text=True).stdout)
        run(["ffmpeg", "-y", "-i", str(joined),
             "-vf", f"fade=in:st=0:d=0.5,fade=out:st={dur - 0.6:.2f}:d=0.6",
             "-af", f"afade=in:st=0:d=0.3,afade=out:st={dur - 0.6:.2f}:d=0.6",
             "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
             "-movflags", "+faststart", str(OUT)])
        print(f"완료 → {OUT}  ({dur:.1f}초)")


if __name__ == "__main__":
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg 가 필요합니다: brew install ffmpeg")
    main()
