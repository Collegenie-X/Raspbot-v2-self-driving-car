#!/usr/bin/env python3
# coding: utf-8
"""
05. 초음파 거리 측정 (trackbar)
  - Interval ms : 측정 간격
  - Warn mm     : 이 거리보다 가까우면 화면이 빨간색
  - Beep        : 1 이면 Warn 거리 안쪽일 때 부저도 울림
  키: q/ESC = 종료
실행: python3 05_ultrasonic.py
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

WIN = "05 Ultrasonic"


def nothing(_):
    pass


def read_distance(bot):
    """거리(mm). 상위 바이트 0x1B, 하위 바이트 0x1A. 실패 시 -1"""
    h = bot.read_data_array(0x1B, 1)
    l = bot.read_data_array(0x1A, 1)
    if not h or not l:
        return -1
    return (h[0] << 8) | l[0]


def main():
    bot = Raspbot()
    bot.Ctrl_Ulatist_Switch(1)   # 초음파 센서 ON
    time.sleep(0.1)

    cv2.namedWindow(WIN)
    cv2.createTrackbar("Interval ms", WIN, 50, 500, nothing)
    cv2.createTrackbar("Warn mm", WIN, 200, 1000, nothing)
    cv2.createTrackbar("Beep", WIN, 0, 1, nothing)

    beeping = False
    try:
        while True:
            interval = max(10, cv2.getTrackbarPos("Interval ms", WIN))
            warn = cv2.getTrackbarPos("Warn mm", WIN)
            beep_on = cv2.getTrackbarPos("Beep", WIN)

            dist = read_distance(bot)
            near = 0 <= dist < warn
            print(f"Ultrasonic Distance: {dist} mm" if dist >= 0 else "Failed to read distance.")

            # 부저: 상태가 바뀔 때만 명령 전송
            want_beep = bool(beep_on and near)
            if want_beep != beeping:
                bot.Ctrl_BEEP_Switch(1 if want_beep else 0)
                beeping = want_beep

            panel = np.zeros((160, 420, 3), np.uint8)
            if near:
                panel[:] = (0, 0, 160)
            cv2.putText(panel, f"{dist} mm" if dist >= 0 else "ERR", (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
            # 0~1000mm 막대
            bar = int(min(max(dist, 0), 1000) / 1000 * 380)
            cv2.rectangle(panel, (20, 110), (20 + bar, 130), (0, 255, 255), -1)
            wx = 20 + int(min(warn, 1000) / 1000 * 380)
            cv2.line(panel, (wx, 105), (wx, 135), (0, 0, 255), 2)
            cv2.putText(panel, "q: quit", (20, 152), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.imshow(WIN, panel)

            if (cv2.waitKey(interval) & 0xFF) in (ord("q"), 27):
                break
    except KeyboardInterrupt:
        pass
    finally:
        bot.Ctrl_BEEP_Switch(0)
        bot.Ctrl_Ulatist_Switch(0)   # 초음파 센서 OFF
        print("Ultrasonic sensor turned off.")
        cv2.destroyAllWindows()
        del bot


if __name__ == "__main__":
    main()
