#!/usr/bin/env python3
# coding: utf-8
"""
03. 서보 제어 (trackbar)
  - S1: 서보 1 (좌우) 0~180도
  - S2: 서보 2 (상하) 0~110도  ⚠️ 110도 초과 금지 (trackbar 최대값으로 제한)
  키: r = 기본 위치(S1=90, S2=25), q/ESC = 종료(기본 위치로 복귀)
실행: python3 03_servo.py
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

WIN = "03 Servo"
S1_DEFAULT, S2_DEFAULT = 90, 25
S2_MAX = 110


def nothing(_):
    pass


def main():
    bot = Raspbot()
    cv2.namedWindow(WIN)
    cv2.createTrackbar("S1", WIN, S1_DEFAULT, 180, nothing)
    cv2.createTrackbar("S2", WIN, S2_DEFAULT, S2_MAX, nothing)

    last = None
    try:
        while True:
            s1 = cv2.getTrackbarPos("S1", WIN)
            s2 = min(cv2.getTrackbarPos("S2", WIN), S2_MAX)

            if (s1, s2) != last:
                bot.Ctrl_Servo(1, s1)
                bot.Ctrl_Servo(2, s2)
                print(f"Servo 1: {s1}°, Servo 2: {s2}°")
                last = (s1, s2)

            panel = np.zeros((120, 400, 3), np.uint8)
            cv2.putText(panel, f"S1: {s1:3d} deg   S2: {s2:3d} deg", (10, 45),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            cv2.putText(panel, "r: reset   q: quit", (10, 95),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.imshow(WIN, panel)

            key = cv2.waitKey(30) & 0xFF
            if key in (ord("q"), 27):
                break
            if key == ord("r"):
                cv2.setTrackbarPos("S1", WIN, S1_DEFAULT)
                cv2.setTrackbarPos("S2", WIN, S2_DEFAULT)
    except KeyboardInterrupt:
        pass
    finally:
        bot.Ctrl_Servo(1, S1_DEFAULT)
        bot.Ctrl_Servo(2, S2_DEFAULT)
        print(f"Servos reset: Servo 1={S1_DEFAULT}°, Servo 2={S2_DEFAULT}°")
        cv2.destroyAllWindows()
        del bot


if __name__ == "__main__":
    main()
