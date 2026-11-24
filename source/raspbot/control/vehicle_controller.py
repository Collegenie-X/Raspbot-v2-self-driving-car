"""차량 구동 제어기."""

from __future__ import annotations

from typing import Tuple

from raspbot.hardware.raspbot import RaspbotHardware


class VehicleController:
    def __init__(
        self,
        hardware: RaspbotHardware,
        base_speed: int,
        speed_limit: int,
        steer_scale: float,
        deadband: float = 0.0,
    ) -> None:
        self.hardware = hardware
        self.base_speed = base_speed
        self.speed_limit = speed_limit
        self.steer_scale = steer_scale
        self.deadband = deadband

    @staticmethod
    def _clamp(value: float, min_value: float, max_value: float) -> float:
        return max(min_value, min(max_value, value))

    def compute_speeds(self, steering_command: float) -> Tuple[int, int, str]:
        """조향 입력으로 좌/우 속도를 계산만 한다(하드웨어 출력 없음)."""
        steer = steering_command * self.steer_scale
        if abs(steer) < self.deadband:
            steer = 0.0

        # steer > 0: 오른쪽으로 돌기 위해 좌측 바퀴를 더 빠르게, 우측 바퀴를 더 느리게
        left_speed = self.base_speed + steer
        right_speed = self.base_speed - steer

        left_speed = self._clamp(left_speed, -self.speed_limit, self.speed_limit)
        right_speed = self._clamp(right_speed, -self.speed_limit, self.speed_limit)

        direction = "UP"
        if steer < -1e-3:
            direction = "LEFT"
        elif steer > 1e-3:
            direction = "RIGHT"

        return int(left_speed), int(right_speed), direction

    def drive(self, steering_command: float) -> Tuple[int, int, str]:
        left_speed, right_speed, direction = self.compute_speeds(steering_command)
        self.hardware.drive(int(left_speed), int(right_speed))
        return left_speed, right_speed, direction

    def stop(self) -> None:
        self.hardware.stop()
