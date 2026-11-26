#!/usr/bin/env python3
# coding: utf-8
"""
01. 부저 제어 (터미널 버전 — 화면/창 없이 SSH 에서 실행 가능)
  명령:
    [Enter]   기본 시간(0.5초) 비프
    1.2       1.2초 비프 (숫자 입력)
    on / off  부저 켜기 / 끄기
    d 0.3     기본 비프 시간을 0.3초로 변경
    q         종료
실행: python3 01_buzzer_cli.py
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


def buzzer_beep(bot, duration):
    bot.Ctrl_BEEP_Switch(1)
    time.sleep(duration)
    bot.Ctrl_BEEP_Switch(0)
    print(f"Buzzer: Beeped for {duration:.1f} seconds")


def main():
    bot = Raspbot()
    duration = 0.5
    print(__doc__)
    try:
        while True:
            cmd = input(f"[beep {duration:.1f}s] > ").strip().lower()
            if cmd in ("q", "quit", "exit"):
                break
            elif cmd == "":
                buzzer_beep(bot, duration)
            elif cmd == "on":
                bot.Ctrl_BEEP_Switch(1)
                print("Buzzer: ON")
            elif cmd == "off":
                bot.Ctrl_BEEP_Switch(0)
                print("Buzzer: OFF")
            elif cmd.startswith("d "):
                try:
                    duration = min(max(float(cmd[2:]), 0.1), 5.0)
                except ValueError:
                    print("예: d 0.3")
            else:
                try:
                    buzzer_beep(bot, min(max(float(cmd), 0.1), 5.0))
                except ValueError:
                    print("알 수 없는 명령입니다.")
    except (KeyboardInterrupt, EOFError):
        print()
    finally:
        bot.Ctrl_BEEP_Switch(0)
        print("Buzzer: OFF")
        del bot


if __name__ == "__main__":
    main()
