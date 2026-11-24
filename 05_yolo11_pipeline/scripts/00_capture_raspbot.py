#!/usr/bin/env python3
"""
[0단계] 라즈봇 V2 카메라로 YOLO 학습용 사진 수집  (라즈봇에서 실행)

라즈봇 카메라로 사진을 찍어 세션(촬영 조건)별 폴더에 저장합니다.
화면이 없는 SSH 접속에서도 일정 간격 자동 저장으로 동작합니다.

  세션 이름 : 촬영 조건 하나 = 세션 하나 (예: t1-red-near, t1-xx-dark)
              → 1단계에서 '<세션>_<번호>.jpg' 로 바뀌고, 4단계에서 같은 세션은 같은 split 으로 묶임
                (거의 같은 연속 사진이 train/test 에 나뉘는 데이터 누수 방지)
              → 세션 이름에 '_' 는 쓰지 않음 (그룹 구분자). 넣으면 자동으로 '-' 로 바꿈

출력:
  ~/captures/<세션이름>/000001.jpg, 000002.jpg ...   (같은 세션으로 다시 실행하면 번호 이어서 저장)

다음 단계 (PC 의 05_yolo11_pipeline/ 에서):
  scp -r pi@<라즈봇IP>:~/captures data/raw/
  python scripts/01_prepare_images.py

사용 예 (라즈봇의 05_yolo11_pipeline/ 에서):
  python3 scripts/00_capture_raspbot.py --session t1-red-near               # 0.5초마다 자동 저장, 40장
  python3 scripts/00_capture_raspbot.py --session t1-red-far --interval 1   # 1초마다
  python3 scripts/00_capture_raspbot.py --session t1-oo-mid --show --interval 0   # 화면 보며 's' 로 한 장씩 (VNC/모니터)
  python3 scripts/00_capture_raspbot.py --session t1-bg --tilt 35           # 카메라 상하 각도(서보2) 35도로 맞추고 시작

종료: 최대 장수(--max) 도달, 또는 Ctrl+C (화면 모드는 q / ESC)

※ 이 스크립트는 config.yaml 을 읽지 않습니다. 라즈봇에 저장소 없이 이 파일만 복사해서 써도 됩니다.
"""
import argparse
import time
from pathlib import Path

import cv2


def set_camera_angle(tilt: int, pan: int = 90) -> None:
    """서보로 카메라 각도를 맞춘다. Raspbot_Lib 가 없으면(PC 등) 건너뛴다."""
    try:
        from Raspbot_Lib import Raspbot
        car = Raspbot()
        car.Ctrl_Servo(1, pan)    # 서보1: 좌우 (90 = 정면)
        car.Ctrl_Servo(2, tilt)   # 서보2: 상하 (주행 코드 기본 35)
        time.sleep(0.5)
        print(f"  카메라 각도: 좌우 {pan}° / 상하 {tilt}°")
    except Exception as e:        # 라이브러리 없음, I2C 오류 등 — 촬영은 계속 진행
        print(f"  [WARN] 서보 제어 생략: {e}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--session", required=True, help="촬영 세션 이름 (예: t1-red-near)")
    ap.add_argument("--out", default="~/captures", help="저장 폴더 (기본 ~/captures)")
    ap.add_argument("--interval", type=float, default=0.5, help="자동 저장 간격(초), 0 = 자동 저장 끔")
    ap.add_argument("--max", type=int, default=40, help="이번 실행에서 저장할 최대 장수")
    ap.add_argument("--width", type=int, default=640)
    ap.add_argument("--height", type=int, default=480)
    ap.add_argument("--tilt", type=int, help="카메라 상하 각도 (서보2, 0~110)")
    ap.add_argument("--show", action="store_true", help="화면 표시 + 's' 키 저장 (모니터/VNC 필요)")
    args = ap.parse_args()

    # '_' 는 파이프라인에서 '그룹_번호' 구분자로 쓰이므로 세션 이름에는 '-' 만 사용
    session = args.session.replace("_", "-")
    out = Path(args.out).expanduser() / session
    out.mkdir(parents=True, exist_ok=True)
    n = len(list(out.glob("*.jpg")))          # 같은 세션으로 다시 실행하면 번호를 이어서 저장

    if args.tilt is not None:
        set_camera_angle(args.tilt)

    cap = cv2.VideoCapture(0)                 # /dev/video0 (라즈봇 카메라)
    if not cap.isOpened():
        raise SystemExit("[ERROR] 카메라를 열 수 없습니다. 다른 프로그램이 카메라를 쓰고 있지 않은지 확인하세요.")
    # 640x480: 주행 코드(320x240)와 화면 비율이 같고, 라벨링할 때 작은 객체가 잘 보임
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    for _ in range(10):                       # 처음 몇 프레임은 노출이 불안정 → 버림
        cap.read()

    mode = "자동" if args.interval > 0 else "수동('s')"
    print(f"  세션: {session} | 저장: {out} | {mode} | 최대 {args.max}장")
    print("  종료: Ctrl+C" + (" / 화면에서 q" if args.show else ""))

    saved, last = 0, 0.0
    try:
        while saved < args.max:
            ok, frame = cap.read()
            if not ok:
                print("  [WARN] 프레임 읽기 실패 — 다시 시도")
                time.sleep(0.1)
                continue

            now = time.time()
            save_now = args.interval > 0 and now - last >= args.interval

            if args.show:
                view = frame.copy()           # 글자는 화면용 사본에만 (저장 사진에는 넣지 않음)
                cv2.putText(view, f"{session}  {saved}/{args.max}", (10, 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.imshow("capture", view)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27):
                    break
                if key == ord("s"):
                    save_now = True

            if save_now:
                n += 1
                cv2.imwrite(str(out / f"{n:06d}.jpg"), frame)
                saved += 1
                last = now
                print(f"  📸 {saved:3d}/{args.max}  {session}/{n:06d}.jpg")
    except KeyboardInterrupt:                 # Ctrl+C 로 멈춰도 카메라를 정상 해제
        pass
    finally:
        cap.release()
        if args.show:
            cv2.destroyAllWindows()

    print(f"\n  이번에 {saved}장 저장 (세션 누적 {n}장) → {out}")
    print("  다음 단계 (PC): scp -r pi@<라즈봇IP>:~/captures data/raw/  →  python scripts/01_prepare_images.py")
    print("                  (입문 수업은 simple/raw/ 로 복사하고 --config config.simple.yaml)")


if __name__ == "__main__":
    main()
