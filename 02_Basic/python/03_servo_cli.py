#!/usr/bin/env python3
# coding: utf-8
"""
03. 서보 제어 (터미널 버전 — 화면/창 없이 SSH 에서 실행 가능)
  명령:
    90 40      S1=90도, S2=40도 동시에
    s1 120     서보 1 (좌우, 0~180도)
    s2 60      서보 2 (상하, 0~110도)  ⚠️ 110도 초과는 자동으로 110 으로 제한
    sweep      S1 0→180→90, S2 0→110→25 왕복 테스트
    r          기본 위치 (S1=90, S2=25)
    q          종료 (기본 위치로 복귀)
실행: python3 03_servo_cli.py
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

S1_DEFAULT, S2_DEFAULT = 90, 25
LIMITS = {1: 180, 2: 110}


def set_servo(bot, servo_id, angle):
    angle = min(max(int(angle), 0), LIMITS[servo_id])
    bot.Ctrl_Servo(servo_id, angle)
    print(f"Servo {servo_id}: {angle}°")


def sweep(bot):
    for servo_id, path in ((1, (0, 180, S1_DEFAULT)), (2, (0, 110, S2_DEFAULT))):
        for angle in path:
            set_servo(bot, servo_id, angle)
            time.sleep(0.7)


def main():
    bot = Raspbot()
    set_servo(bot, 1, S1_DEFAULT)
    set_servo(bot, 2, S2_DEFAULT)
    print(__doc__)
    try:
        while True:
            parts = input("> ").strip().lower().split()
            if not parts:
                continue
            try:
                if parts[0] in ("q", "quit", "exit"):
                    break
                elif parts[0] == "r":
                    set_servo(bot, 1, S1_DEFAULT)
                    set_servo(bot, 2, S2_DEFAULT)
                elif parts[0] == "sweep":
                    sweep(bot)
                elif parts[0] in ("s1", "s2") and len(parts) == 2:
                    set_servo(bot, int(parts[0][1]), parts[1])
                elif len(parts) == 2:
                    set_servo(bot, 1, parts[0])
                    set_servo(bot, 2, parts[1])
                else:
                    print("알 수 없는 명령입니다.")
            except ValueError:
                print("각도는 숫자로 입력하세요. 예: 90 40")
    except (KeyboardInterrupt, EOFError):
        print()
    finally:
        bot.Ctrl_Servo(1, S1_DEFAULT)
        bot.Ctrl_Servo(2, S2_DEFAULT)
        print(f"Servos reset: Servo 1={S1_DEFAULT}°, Servo 2={S2_DEFAULT}°")
        del bot


if __name__ == "__main__":
    main()
