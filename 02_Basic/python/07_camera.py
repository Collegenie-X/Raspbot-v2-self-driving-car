#!/usr/bin/env python3
# coding: utf-8
"""
07. 카메라 영상 (trackbar)
  - Brightness : 밝기 보정 (가운데 100 = 원본, 0~200 → -100~+100)
  - Contrast x0.1: 대비 배율 (10 = 원본)
  - Flip       : 0=원본 1=좌우 2=상하 3=180도 회전
  - Gray       : 1 이면 흑백
  키: s = 현재 화면 저장(snapshot_*.jpg), q/ESC = 종료
실행: python3 07_camera.py [카메라번호, 기본 0]
"""
import os
import sys

# Raspbot 라이브러리 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib", "raspbot"))

import cv2
import numpy as np
import random
import time
from Raspbot_Lib import Raspbot

WIN = "07 Camera"
FLIP_CODES = [None, 1, 0, -1]


def nothing(_):
    pass


def main():
    index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        print(f"Error: Cannot open camera {index}.")
        return
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    cv2.namedWindow(WIN)
    cv2.createTrackbar("Brightness", WIN, 100, 200, nothing)
    cv2.createTrackbar("Contrast x0.1", WIN, 10, 30, nothing)
    cv2.createTrackbar("Flip", WIN, 0, 3, nothing)
    cv2.createTrackbar("Gray", WIN, 0, 1, nothing)

    prev = time.time()
    fps = 0.0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Failed to read frame.")
                break

            beta = cv2.getTrackbarPos("Brightness", WIN) - 100
            alpha = cv2.getTrackbarPos("Contrast x0.1", WIN) / 10.0
            flip = FLIP_CODES[cv2.getTrackbarPos("Flip", WIN)]
            gray = cv2.getTrackbarPos("Gray", WIN)

            # 밝기/대비: out = frame * alpha + beta
            frame = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)
            if flip is not None:
                frame = cv2.flip(frame, flip)
            if gray:
                frame = cv2.cvtColor(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)

            now = time.time()
            fps = 0.9 * fps + 0.1 * (1.0 / max(now - prev, 1e-6))
            prev = now
            cv2.putText(frame, f"FPS {fps:4.1f}  s: save  q: quit", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.imshow(WIN, frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key == ord("s"):
                name = time.strftime("snapshot_%Y%m%d_%H%M%S.jpg")
                cv2.imwrite(name, frame)
                print(f"Saved {name}")
    except KeyboardInterrupt:
        pass
    finally:
        # 카메라를 해제해야 다른 프로그램에서 사용 가능
        cap.release()
        cv2.destroyAllWindows()
        print("Camera released.")


if __name__ == "__main__":
    main()
