#!/usr/bin/env python3
# coding: utf-8
"""
06. 4방향 라인 추적 센서 상태 (터미널 버전 — 화면/창 없이 SSH 에서 실행 가능)
  옵션:
    --interval 0.1   읽기 간격(초)
    --all            값이 같아도 매번 출력 (기본: 바뀔 때만 출력)
  출력: x2 x1 x3 x4 순서, ● = 1, ○ = 0
  Ctrl+C 로 종료
실행: python3 06_line_tracker_cli.py
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

import argparse


def read_tracker(bot):
    """(x2, x1, x3, x4) 튜플. 비트3=x1, 비트2=x2, 비트1=x3, 비트0=x4. 실패 시 None"""
    data = bot.read_data_array(0x0A, 1)
    if not data:
        return None
    t = int(data[0])
    x1, x2, x3, x4 = (t >> 3) & 1, (t >> 2) & 1, (t >> 1) & 1, t & 1
    return (x2, x1, x3, x4)


def main():
    parser = argparse.ArgumentParser(description="라인 추적 센서 상태")
    parser.add_argument("--interval", type=float, default=0.1)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    bot = Raspbot()
    last = None
    print("        x2 x1 x3 x4   (Ctrl+C 로 종료)")
    try:
        while True:
            status = read_tracker(bot)
            if status is None:
                print("I2C read error")
            elif args.all or status != last:
                dots = "  ".join("●" if v else "○" for v in status)
                print(f"Status: {dots}    ({', '.join(map(str, status))})")
                last = status
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print()
    finally:
        print("Line tracking stopped.")
        del bot


if __name__ == "__main__":
    main()
