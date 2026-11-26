#!/usr/bin/env python3
# coding: utf-8
"""
04. 모터 제어 (trackbar)
  - M1~M4: 각 모터 속도. trackbar 는 음수가 안 되므로 0~510 범위를 쓰고
           실제 속도 = 값 - 255  (가운데 255 = 정지, 0 = -255 후진, 510 = +255 전진)
           M1=왼쪽 앞, M2=왼쪽 뒤, M3=오른쪽 앞, M4=오른쪽 뒤
  - Speed: 키보드 주행(w/a/s/d) 에 쓸 속도 0~255
  키: w=전진 s=후진 a=좌회전 d=우회전 SPACE=정지(슬라이더 가운데로), q/ESC=종료
  ⚠️ 바퀴를 띄우거나 넓은 곳에서 테스트하세요.
실행: python3 04_motor.py
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

WIN = "04 Motor"
OFFSET = 255
NAMES = ["M1", "M2", "M3", "M4"]


def nothing(_):
    pass


def set_sliders(left, right):
    """왼쪽(M1,M2)/오른쪽(M3,M4) 속도를 슬라이더에 반영 → 메인 루프가 모터에 적용"""
    for name, v in zip(NAMES, (left, left, right, right)):
        cv2.setTrackbarPos(name, WIN, v + OFFSET)


def main():
    bot = Raspbot()
    cv2.namedWindow(WIN)
    for name in NAMES:
        cv2.createTrackbar(name, WIN, OFFSET, OFFSET * 2, nothing)
    cv2.createTrackbar("Speed", WIN, 100, 255, nothing)

    last = None
    try:
        while True:
            speeds = [cv2.getTrackbarPos(n, WIN) - OFFSET for n in NAMES]
            if speeds != last:
                for motor_id, sp in enumerate(speeds):
                    bot.Ctrl_Muto(motor_id, sp)
                print("Motor:", dict(zip(NAMES, speeds)))
                last = speeds

            panel = np.zeros((150, 460, 3), np.uint8)
            for i, (n, sp) in enumerate(zip(NAMES, speeds)):
                color = (0, 255, 0) if sp > 0 else (0, 0, 255) if sp < 0 else (200, 200, 200)
                cv2.putText(panel, f"{n}: {sp:+4d}", (10 + (i % 2) * 220, 35 + (i // 2) * 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            cv2.putText(panel, "w/s/a/d: drive  SPACE: stop  q: quit", (10, 130),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
            cv2.imshow(WIN, panel)

            key = cv2.waitKey(30) & 0xFF
            sp = cv2.getTrackbarPos("Speed", WIN)
            if key in (ord("q"), 27):
                break
            elif key == ord("w"):
                set_sliders(sp, sp)        # 전진
            elif key == ord("s"):
                set_sliders(-sp, -sp)      # 후진
            elif key == ord("a"):
                set_sliders(-sp, sp)       # 좌회전(제자리)
            elif key == ord("d"):
                set_sliders(sp, -sp)       # 우회전(제자리)
            elif key == ord(" "):
                set_sliders(0, 0)          # 정지
    except KeyboardInterrupt:
        pass
    finally:
        for motor_id in range(4):
            bot.Ctrl_Muto(motor_id, 0)
        print("Stop")
        cv2.destroyAllWindows()
        del bot


if __name__ == "__main__":
    main()
