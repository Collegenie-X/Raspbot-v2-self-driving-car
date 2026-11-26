#!/usr/bin/env python3
# coding: utf-8
"""
04. 모터 제어 (터미널 버전 — 화면/창 없이 SSH 에서 실행 가능)
  키 (Enter 없이 바로 동작):
    w / s      전진 / 후진
    a / d      좌회전 / 우회전 (제자리)
    SPACE, x   정지
    + / -      속도 20 씩 증가 / 감소 (0~255)
    1 2 3 4    M1(왼앞) M2(왼뒤) M3(오앞) M4(오뒤) 하나만 1초 회전 (배선 확인용)
    q          종료
  ⚠️ 바퀴를 띄우거나 넓은 곳에서 테스트하세요.
실행: python3 04_motor_cli.py
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

import select
import termios
import tty


def drive(bot, left, right, label):
    """M1,M2 = 왼쪽 / M3,M4 = 오른쪽"""
    for motor_id, sp in enumerate((left, left, right, right)):
        bot.Ctrl_Muto(motor_id, sp)
    print(f"\r{label:<12} Left={left:+4d}  Right={right:+4d}")


def stop(bot):
    for motor_id in range(4):
        bot.Ctrl_Muto(motor_id, 0)


def read_key(timeout=0.1):
    """키 하나를 읽습니다(Enter 불필요). 입력이 없으면 None"""
    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    return sys.stdin.read(1) if ready else None


def main():
    bot = Raspbot()
    speed = 100
    print(__doc__.replace("\n", "\r\n"))
    old = termios.tcgetattr(sys.stdin)
    try:
        tty.setcbreak(sys.stdin.fileno())  # 키를 누르는 즉시 읽기
        while True:
            key = read_key()
            if key is None:
                continue
            key = key.lower()
            if key == "q":
                break
            elif key == "w":
                drive(bot, speed, speed, "Forward")
            elif key == "s":
                drive(bot, -speed, -speed, "Backward")
            elif key == "a":
                drive(bot, -speed, speed, "Turn Left")
            elif key == "d":
                drive(bot, speed, -speed, "Turn Right")
            elif key in (" ", "x"):
                stop(bot)
                print("\rStop")
            elif key in ("+", "="):
                speed = min(speed + 20, 255)
                print(f"\rSpeed: {speed}")
            elif key in ("-", "_"):
                speed = max(speed - 20, 0)
                print(f"\rSpeed: {speed}")
            elif key in "1234":
                stop(bot)
                motor_id = int(key) - 1
                print(f"\rM{key} only, speed {speed} (1s)")
                bot.Ctrl_Muto(motor_id, speed)
                time.sleep(1)
                bot.Ctrl_Muto(motor_id, 0)
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old)  # 터미널 원래대로
        stop(bot)
        print("\nStop")
        del bot


if __name__ == "__main__":
    main()
