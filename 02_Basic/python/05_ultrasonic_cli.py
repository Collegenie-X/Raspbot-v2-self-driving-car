#!/usr/bin/env python3
# coding: utf-8
"""
05. 초음파 거리 측정 (터미널 버전 — 화면/창 없이 SSH 에서 실행 가능)
  옵션:
    --interval 0.05   측정 간격(초)
    --warn 200        이 거리(mm)보다 가까우면 WARN 표시
    --beep            WARN 일 때 부저도 울림
  Ctrl+C 로 종료
실행: python3 05_ultrasonic_cli.py --warn 200 --beep
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


def read_distance(bot):
    """거리(mm). 상위 바이트 0x1B, 하위 바이트 0x1A. 실패 시 -1"""
    h = bot.read_data_array(0x1B, 1)
    l = bot.read_data_array(0x1A, 1)
    if not h or not l:
        return -1
    return (h[0] << 8) | l[0]


def main():
    parser = argparse.ArgumentParser(description="초음파 거리 측정")
    parser.add_argument("--interval", type=float, default=0.05)
    parser.add_argument("--warn", type=int, default=200)
    parser.add_argument("--beep", action="store_true")
    args = parser.parse_args()

    bot = Raspbot()
    bot.Ctrl_Ulatist_Switch(1)   # 초음파 센서 ON
    time.sleep(0.1)
    beeping = False
    print("Ctrl+C 로 종료")
    try:
        while True:
            dist = read_distance(bot)
            if dist < 0:
                print("Failed to read distance.")
            else:
                near = dist < args.warn
                bar = "#" * int(min(dist, 1000) / 1000 * 40)  # 0~1000mm → 막대 40칸
                print(f"{dist:5d} mm |{bar:<40}| {'WARN' if near else ''}")
                want_beep = args.beep and near
                if want_beep != beeping:
                    bot.Ctrl_BEEP_Switch(1 if want_beep else 0)
                    beeping = want_beep
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print()
    finally:
        bot.Ctrl_BEEP_Switch(0)
        bot.Ctrl_Ulatist_Switch(0)   # 초음파 센서 OFF
        print("Ultrasonic sensor turned off.")
        del bot


if __name__ == "__main__":
    main()
