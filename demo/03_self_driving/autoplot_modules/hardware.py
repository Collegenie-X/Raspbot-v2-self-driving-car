# -*- coding: utf-8 -*-
import sys
import os
import time

# 라이브러리 경로 추가 (현재 파일 기준 상대 경로)
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, "..", "..", "lib", "raspbot")
if os.path.exists(lib_path):
    sys.path.append(lib_path)

try:
    from Raspbot_Lib import Raspbot
except ImportError:
    # 경로가 안 맞을 경우를 대비해 예외 처리 또는 상위에서 추가했다고 가정
    pass


class RobotController:
    """
    로봇 하드웨어 제어 클래스 (모터, 서보, LED, 부저)
    """

    def __init__(self):
        try:
            self.bot = Raspbot()
            self.stop()
            print("✅ 로봇 하드웨어 초기화 완료")
        except Exception as e:
            print(f"❌ 로봇 초기화 실패: {e}")
            raise e

    def set_motor(self, left_speed, right_speed):
        """
        좌우 모터 속도 설정 (-255 ~ 255)
        """
        # M1, M2: 왼쪽 / M3, M4: 오른쪽
        # 모터 방향에 따라 부호 조정이 필요할 수 있음 (기존 코드 참조)
        # 기존 코드:
        # car_run: all positive
        # car_left: left negative, right positive
        # car_right: left positive, right negative

        # Raspbot_Lib가 직접 제어하므로 그대로 전달
        self.bot.Ctrl_Muto(0, left_speed)  # M1
        self.bot.Ctrl_Muto(1, left_speed)  # M2
        self.bot.Ctrl_Muto(2, right_speed)  # M3
        self.bot.Ctrl_Muto(3, right_speed)  # M4

    def stop(self):
        """모든 모터 정지"""
        for i in range(4):
            self.bot.Ctrl_Muto(i, 0)

    def set_servo(self, servo_id, angle):
        """
        서보 모터 제어
        servo_id: 1(좌우), 2(상하)
        """
        if servo_id == 2 and angle > 110:
            angle = 110
        self.bot.Ctrl_Servo(servo_id, angle)

    def set_led(self, mode):
        """
        LED 제어
        mode: 0=OFF, 1=GREEN(직진), 2=BLUE(대기), 3=YELLOW(회전)
        """
        if mode == 0:
            self.bot.Ctrl_WQ2812_ALL(0, 0)
        elif mode == 1:  # Green
            self.bot.Ctrl_WQ2812_ALL(1, 1)
        elif mode == 2:  # Blue
            self.bot.Ctrl_WQ2812_ALL(1, 2)
        elif mode == 3:  # Yellow
            self.bot.Ctrl_WQ2812_ALL(1, 3)

    def beep(self, duration=0.1):
        """부저 울림"""
        self.bot.Ctrl_BEEP_Switch(1)
        time.sleep(duration)
        self.bot.Ctrl_BEEP_Switch(0)

    def __del__(self):
        self.stop()
        self.set_led(0)
        self.bot.Ctrl_BEEP_Switch(0)
