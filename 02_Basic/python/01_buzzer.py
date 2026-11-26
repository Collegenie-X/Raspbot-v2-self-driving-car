#!/usr/bin/env python3
# coding: utf-8
"""
01. 부저 제어 (trackbar)
  - BEEP 0/1      : 부저 ON/OFF 스위치
  - Duration x0.1s: SPACE 키로 울릴 비프 시간
  키: SPACE = Duration 만큼 비프, q/ESC = 종료
실행: python3 01_buzzer.py
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

WIN = "01 Buzzer"


def nothing(_):
    pass


def main():
    bot = Raspbot()
    cv2.namedWindow(WIN)
    cv2.createTrackbar("BEEP", WIN, 0, 1, nothing)
    cv2.createTrackbar("Duration x0.1s", WIN, 5, 20, nothing)

    last_state = None
    try:
        while True:
            state = cv2.getTrackbarPos("BEEP", WIN)
            duration = max(1, cv2.getTrackbarPos("Duration x0.1s", WIN)) * 0.1

            # 값이 바뀔 때만 I2C 명령 전송
            if state != last_state:
                bot.Ctrl_BEEP_Switch(state)
                print(f"Buzzer: {'ON' if state else 'OFF'}")
                last_state = state

            panel = np.zeros((120, 400, 3), np.uint8)
            color = (0, 0, 255) if state else (200, 200, 200)
            cv2.putText(panel, f"BEEP: {'ON' if state else 'OFF'}", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            cv2.putText(panel, f"SPACE: beep {duration:.1f}s   q: quit", (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.imshow(WIN, panel)

            key = cv2.waitKey(30) & 0xFF
            if key in (ord("q"), 27):
                break
            if key == ord(" "):
                bot.Ctrl_BEEP_Switch(1)
                time.sleep(duration)
                bot.Ctrl_BEEP_Switch(0)
                last_state = None  # 스위치 상태 다시 적용
                print(f"Buzzer: Beeped for {duration:.1f} seconds")
    except KeyboardInterrupt:
        pass
    finally:
        bot.Ctrl_BEEP_Switch(0)
        cv2.destroyAllWindows()
        del bot


if __name__ == "__main__":
    main()
