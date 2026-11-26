#!/usr/bin/env python3
# coding: utf-8
"""
06. 4방향 라인 추적 센서 상태 (trackbar)
  - Interval ms : 읽기 간격
  - Print       : 1 이면 터미널에도 출력 (값이 바뀔 때만)
  화면: x2 x1 x3 x4 순서로 원 4개 (채워진 원 = 1)
  키: q/ESC = 종료
실행: python3 06_line_tracker.py
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

WIN = "06 Line Tracker"
LABELS = ["x2", "x1", "x3", "x4"]


def nothing(_):
    pass


def read_tracker(bot):
    """(x2, x1, x3, x4) 튜플. 비트3=x1, 비트2=x2, 비트1=x3, 비트0=x4. 실패 시 None"""
    data = bot.read_data_array(0x0A, 1)
    if not data:
        return None
    t = int(data[0])
    x1, x2, x3, x4 = (t >> 3) & 1, (t >> 2) & 1, (t >> 1) & 1, t & 1
    return (x2, x1, x3, x4)


def main():
    bot = Raspbot()
    cv2.namedWindow(WIN)
    cv2.createTrackbar("Interval ms", WIN, 100, 500, nothing)
    cv2.createTrackbar("Print", WIN, 1, 1, nothing)

    last = None
    try:
        while True:
            interval = max(10, cv2.getTrackbarPos("Interval ms", WIN))
            status = read_tracker(bot)

            if status is not None and status != last and cv2.getTrackbarPos("Print", WIN):
                print("Line Tracker Status: {}, {}, {}, {}".format(*status))
            if status is not None:
                last = status

            panel = np.zeros((150, 400, 3), np.uint8)
            for i, label in enumerate(LABELS):
                cx = 60 + i * 95
                on = last is not None and last[i] == 1
                cv2.circle(panel, (cx, 60), 30, (0, 255, 0), -1 if on else 2)
                cv2.putText(panel, label, (cx - 15, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            if status is None:
                cv2.putText(panel, "I2C read error", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            cv2.putText(panel, "q: quit", (320, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
            cv2.imshow(WIN, panel)

            if (cv2.waitKey(interval) & 0xFF) in (ord("q"), 27):
                break
    except KeyboardInterrupt:
        pass
    finally:
        print("Line tracking stopped.")
        cv2.destroyAllWindows()
        del bot


if __name__ == "__main__":
    main()
