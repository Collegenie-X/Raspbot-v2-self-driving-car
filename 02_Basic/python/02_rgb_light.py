#!/usr/bin/env python3
# coding: utf-8
"""
02. RGB 라이트 바 (trackbar)
  - Preset : 0=R/G/B 슬라이더 사용, 1~7=Red/Green/Blue/Yellow/Purple/Cyan/White, 8=OFF
  - R, G, B: Preset=0 일 때 적용되는 사용자 색상 (0~255)
  - Effect : 0=Gradient 1=River 2=Running 3=Starlight 4=Breathing
  - Speed x0.01s / Duration s : 효과 속도/지속 시간
  키: e = 선택한 효과 실행(지속 시간 동안), q/ESC = 종료
  차량의 KEY1 버튼을 누르면 Preset 이 다음 색으로 넘어갑니다.
실행: python3 02_rgb_light.py
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

WIN = "02 RGB Light"
COLOR_NAMES = ["Red", "Green", "Blue", "Yellow", "Purple", "Cyan", "White"]
# 미리보기용 BGR 색상
PREVIEW_BGR = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (0, 255, 255),
               (255, 0, 255), (255, 255, 0), (255, 255, 255)]
EFFECTS = ["gradient", "river", "random_running", "starlight", "breathing"]
KEY1_REG = 0x0D


def nothing(_):
    pass


def read_key1(bot):
    """KEY1 상태(0/1). I2C 읽기 실패 시 None (원본 노트북의 TypeError 방지)"""
    data = bot.read_data_array(KEY1_REG, 1)
    return None if not data else data[0]


def main():
    bot = Raspbot()
    lights = LightShow()

    cv2.namedWindow(WIN)
    cv2.createTrackbar("Preset", WIN, 0, 8, nothing)
    cv2.createTrackbar("R", WIN, 0, 255, nothing)
    cv2.createTrackbar("G", WIN, 0, 255, nothing)
    cv2.createTrackbar("B", WIN, 0, 255, nothing)
    cv2.createTrackbar("Effect", WIN, 0, len(EFFECTS) - 1, nothing)
    cv2.createTrackbar("Speed x0.01s", WIN, 1, 20, nothing)
    cv2.createTrackbar("Duration s", WIN, 5, 20, nothing)

    last = None
    key_down = False
    try:
        while True:
            preset = cv2.getTrackbarPos("Preset", WIN)
            r = cv2.getTrackbarPos("R", WIN)
            g = cv2.getTrackbarPos("G", WIN)
            b = cv2.getTrackbarPos("B", WIN)

            # 1) KEY1 버튼 → 다음 Preset (눌리는 순간에만)
            state = read_key1(bot)
            if state == 1 and not key_down:
                preset = preset % 8 + 1  # 1..8 순환
                cv2.setTrackbarPos("Preset", WIN, preset)
                key_down = True
            elif state == 0:
                key_down = False

            # 2) 값이 바뀌었을 때만 LED 갱신
            current = (preset, r, g, b)
            if current != last:
                if preset == 0:
                    bot.Ctrl_WQ2812_brightness_ALL(r, g, b)
                    label, bgr = f"RGB({r},{g},{b})", (b, g, r)
                elif preset == 8:
                    bot.Ctrl_WQ2812_ALL(0, 0)
                    label, bgr = "OFF", (40, 40, 40)
                else:
                    bot.Ctrl_WQ2812_ALL(1, preset - 1)
                    label, bgr = COLOR_NAMES[preset - 1], PREVIEW_BGR[preset - 1]
                print(f"LED: {label}")
                last = current

            effect = EFFECTS[cv2.getTrackbarPos("Effect", WIN)]
            speed = max(1, cv2.getTrackbarPos("Speed x0.01s", WIN)) * 0.01
            duration = max(1, cv2.getTrackbarPos("Duration s", WIN))

            panel = np.zeros((160, 460, 3), np.uint8)
            cv2.rectangle(panel, (10, 10), (110, 110), bgr, -1)
            cv2.putText(panel, label, (125, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(panel, f"Effect: {effect} {duration}s @{speed:.2f}", (125, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            cv2.putText(panel, "e: run effect   q: quit   KEY1: next color", (10, 145),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.imshow(WIN, panel)

            key = cv2.waitKey(30) & 0xFF
            if key in (ord("q"), 27):
                break
            if key == ord("e"):
                print(f"Effect: {effect} ({duration}s, speed {speed:.2f}) ... 실행 중")
                # breathing 은 Preset 색(없으면 빨강)을 사용
                color_id = preset - 1 if 1 <= preset <= 7 else 0
                lights.execute_effect(effect, duration, speed, color_id)
                print("finished")
                last = None  # 효과 종료 후 현재 색 다시 적용
    except KeyboardInterrupt:
        pass
    finally:
        bot.Ctrl_WQ2812_ALL(0, 0)
        cv2.destroyAllWindows()
        del bot


if __name__ == "__main__":
    main()
