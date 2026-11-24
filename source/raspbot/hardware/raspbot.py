"""Raspbot V2 하드웨어 제어 래퍼."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Optional, Tuple


class MockRaspbot:
    """실기 없이 로직만 점검할 때 사용하는 더미 구현."""

    def __init__(self) -> None:
        self.last_motors = [0, 0, 0, 0]

    def Ctrl_Muto(self, index: int, speed: int) -> None:
        self.last_motors[index] = speed
        print(f"[MOCK] Motor {index}: {speed}")

    def Ctrl_WQ2812_ALL(self, state: int, mode: int) -> None:
        print(f"[MOCK] LED state={state}, mode={mode}")

    def Ctrl_BEEP_Switch(self, state: int) -> None:
        print(f"[MOCK] Beep state={state}")

    def Ctrl_Servo(self, channel: int, angle: int) -> None:
        print(f"[MOCK] Servo {channel}: {angle}")


class RaspbotHardware:
    """Raspbot 하드웨어를 제어하기 위한 고수준 래퍼."""

    SERVO_PITCH_LIMIT = 110

    def __init__(
        self,
        use_led: bool = True,
        use_beep: bool = True,
        led_on_start: bool = True,
        beep_on_start: bool = True,
        servo_defaults: Tuple[int, int] = (70, 10),
        servo_neutral: Tuple[int, int] = (90, 25),
        led_mode: int = 2,
        enable_mock: bool = False,
    ) -> None:
        self.use_led = use_led
        self.use_beep = use_beep
        self.led_on_start = led_on_start
        self.beep_on_start = beep_on_start
        self.servo_defaults = servo_defaults
        self.servo_neutral = servo_neutral
        self.led_mode = led_mode

        self.bot = self._init_bot(enable_mock)
        self._initialize_state()

    def _init_bot(self, enable_mock: bool):
        lib_path = Path(__file__).resolve().parents[2] / "lib" / "raspbot"
        sys.path.append(str(lib_path))
        try:
            from Raspbot_Lib import Raspbot  # type: ignore

            return Raspbot()
        except Exception:
            if enable_mock:
                return MockRaspbot()
            raise

    def _initialize_state(self) -> None:
        if self.use_led and self.led_on_start:
            self.set_led(True)
        if self.use_beep and self.beep_on_start:
            self.beep(0.2)

        yaw, pitch = self.servo_defaults
        self.set_servo(1, yaw)
        self.set_servo(2, pitch)
        self.stop()

    def set_servo(self, channel: int, angle: int) -> None:
        if channel == 2:
            angle = min(angle, self.SERVO_PITCH_LIMIT)
        self.bot.Ctrl_Servo(channel, int(angle))

    def set_led(self, on: bool) -> None:
        if not self.use_led:
            return
        state = 1 if on else 0
        self.bot.Ctrl_WQ2812_ALL(state, self.led_mode if on else 0)

    def set_led_mode(self, mode: int) -> None:
        self.led_mode = int(mode)
        self.set_led(True)

    def set_beep(self, on: bool) -> None:
        """비프 스위치를 즉시 ON/OFF한다(논블로킹)."""
        if not self.use_beep:
            return
        self.bot.Ctrl_BEEP_Switch(1 if on else 0)

    def beep(self, duration: float = 0.1) -> None:
        if not self.use_beep:
            return
        self.set_beep(True)
        time.sleep(duration)
        self.set_beep(False)

    def set_motor_speeds(self, front_left: int, rear_left: int, front_right: int, rear_right: int) -> None:
        self.bot.Ctrl_Muto(0, int(front_left))
        self.bot.Ctrl_Muto(1, int(rear_left))
        self.bot.Ctrl_Muto(2, int(front_right))
        self.bot.Ctrl_Muto(3, int(rear_right))

    def drive(self, left: int, right: int) -> None:
        """좌우 속도로 주행 (메카넘 직진 기준 동일 방향 회전)."""
        self.set_motor_speeds(left, left, right, right)

    def stop(self) -> None:
        self.drive(0, 0)

    def cleanup(self) -> None:
        self.stop()
        self.set_led(False)
        self.bot.Ctrl_BEEP_Switch(0)

        yaw, pitch = self.servo_neutral
        self.set_servo(1, yaw)
        self.set_servo(2, pitch)
