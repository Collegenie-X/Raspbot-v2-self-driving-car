"""PID 제어기 구현."""

from __future__ import annotations

from typing import Optional, Tuple


class PIDController:
    def __init__(
        self,
        kp: float,
        ki: float,
        kd: float,
        output_limits: Tuple[float, float] = (-255.0, 255.0),
    ) -> None:
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.min_output, self.max_output = output_limits

        self.integral = 0.0
        self.prev_error: Optional[float] = None

    def reset(self) -> None:
        self.integral = 0.0
        self.prev_error = None

    def update(self, error: float, dt: float) -> float:
        if dt <= 0:
            dt = 1e-3

        self.integral += error * dt

        derivative = 0.0
        if self.prev_error is not None:
            derivative = (error - self.prev_error) / dt
        self.prev_error = error

        output = self.kp * error + self.ki * self.integral + self.kd * derivative
        return float(max(self.min_output, min(self.max_output, output)))
