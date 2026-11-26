#!/usr/bin/env python3
# coding: utf-8
"""
02. RGB 라이트 바 (터미널 버전 — 화면/창 없이 SSH 에서 실행 가능)
  명령:
    0~6 또는 red/green/blue/yellow/purple/cyan/white   기본 색
    rgb 255 100 0                                     사용자 색 (R G B, 0~255)
    off                                               끄기
    effect gradient [지속초=5] [속도=0.01]             효과 실행
           (gradient / river / running / starlight / breathing)
    key                                               KEY1 버튼으로 색 순환 (Ctrl+C 로 메뉴 복귀)
    q                                                 종료
실행: python3 02_rgb_light_cli.py
"""
import os
import sys

# Raspbot 라이브러리 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib", "raspbot"))

import cv2
import numpy as np
import random
import time
from Raspbot_Lib import Raspbot, LightShow

COLOR_NAMES = ["red", "green", "blue", "yellow", "purple", "cyan", "white"]
EFFECTS = {"gradient": "gradient", "river": "river", "running": "random_running",
           "starlight": "starlight", "breathing": "breathing"}
KEY1_REG = 0x0D


def set_color(bot, color_id):
    bot.Ctrl_WQ2812_ALL(1, color_id)
    print(f"LED: {COLOR_NAMES[color_id]}")


def key_mode(bot):
    """KEY1 을 누를 때마다 7색 → OFF 순으로 바뀝니다."""
    print("KEY1 버튼을 눌러 보세요. (Ctrl+C: 메뉴로)")
    index = -1
    key_down = False
    try:
        while True:
            data = bot.read_data_array(KEY1_REG, 1)
            if data:  # I2C 읽기 실패(None)면 이번 회차는 건너뜀
                if data[0] == 1 and not key_down:
                    index = (index + 1) % 8
                    if index == 7:
                        bot.Ctrl_WQ2812_ALL(0, 0)
                        print("LED: OFF")
                    else:
                        set_color(bot, index)
                    key_down = True
                elif data[0] == 0:
                    key_down = False
            time.sleep(0.02)
    except KeyboardInterrupt:
        print()


def main():
    bot = Raspbot()
    lights = LightShow()
    last_color = 0
    print(__doc__)
    try:
        while True:
            parts = input("> ").strip().lower().split()
            if not parts:
                continue
            cmd = parts[0]
            if cmd in ("q", "quit", "exit"):
                break
            elif cmd == "off":
                bot.Ctrl_WQ2812_ALL(0, 0)
                print("LED: OFF")
            elif cmd.isdigit() and 0 <= int(cmd) <= 6:
                last_color = int(cmd)
                set_color(bot, last_color)
            elif cmd in COLOR_NAMES:
                last_color = COLOR_NAMES.index(cmd)
                set_color(bot, last_color)
            elif cmd == "rgb" and len(parts) == 4:
                try:
                    r, g, b = (min(max(int(v), 0), 255) for v in parts[1:])
                except ValueError:
                    print("예: rgb 255 100 0")
                    continue
                bot.Ctrl_WQ2812_brightness_ALL(r, g, b)
                print(f"LED: RGB({r}, {g}, {b})")
            elif cmd == "effect" and len(parts) >= 2 and parts[1] in EFFECTS:
                try:
                    duration = int(parts[2]) if len(parts) > 2 else 5
                    speed = float(parts[3]) if len(parts) > 3 else 0.01
                except ValueError:
                    print("예: effect river 5 0.01")
                    continue
                print(f"Effect: {parts[1]} ({duration}s, speed {speed}) ... 실행 중")
                lights.execute_effect(EFFECTS[parts[1]], duration, speed, last_color)
                print("finished")
            elif cmd == "key":
                key_mode(bot)
            else:
                print("알 수 없는 명령입니다.")
    except (KeyboardInterrupt, EOFError):
        print()
    finally:
        bot.Ctrl_WQ2812_ALL(0, 0)
        print("LED: OFF")
        del bot


if __name__ == "__main__":
    main()
