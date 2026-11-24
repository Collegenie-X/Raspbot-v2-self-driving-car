"""YOLO 이벤트 기반 미션 FSM + 논블로킹 비프 시퀀서."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, List, Optional, Tuple

from raspbot.hardware.raspbot import RaspbotHardware
from raspbot.perception.yolo_events import YoloDetection


@dataclass
class MissionCommand:
    base_speed: int
    steering: float
    force_stop: bool
    state: str


class BeepSequencer:
    """sleep 없이 루프 틱마다 진행되는 비프 시퀀서."""

    def __init__(self, hardware: RaspbotHardware) -> None:
        self.hardware = hardware
        self._queue: Deque[Tuple[bool, float]] = deque()
        self._playing = False
        self._step_end_time = 0.0

    def enqueue(self, pattern: List[Tuple[bool, float]], now: float) -> None:
        self._queue.extend(pattern)
        if not self._playing:
            self._start_next(now)

    def is_idle(self) -> bool:
        return (not self._playing) and (not self._queue)

    def tick(self, now: float) -> None:
        if not self._playing:
            return
        if now >= self._step_end_time:
            self._start_next(now)

    def _start_next(self, now: float) -> None:
        if not self._queue:
            self.hardware.set_beep(False)
            self._playing = False
            self._step_end_time = now
            return
        on, duration = self._queue.popleft()
        self.hardware.set_beep(on)
        self._playing = True
        self._step_end_time = now + float(duration)


def repeat_beeps(on_s: float, off_s: float, count: int) -> List[Tuple[bool, float]]:
    pattern: List[Tuple[bool, float]] = []
    for _ in range(int(count)):
        pattern.append((True, float(on_s)))
        pattern.append((False, float(off_s)))
    return pattern


class MissionFSM:
    """Layer B 미션 FSM. DRIVE 위에서 미션 행동을 override 한다."""

    DRIVE = "DRIVE"
    WAIT_TRAFFIC_LIGHT = "WAIT_TRAFFIC_LIGHT"
    HAZARD_ACTION = "HAZARD_ACTION"
    PARKING_APPROACH = "PARKING_APPROACH"
    PARKING_HOLD = "PARKING_HOLD"

    def __init__(
        self,
        beep_seq: BeepSequencer,
        steer_limit: float,
        parking_cfg: Optional[dict] = None,
        hazard_cfg: Optional[dict] = None,
    ) -> None:
        self.beep_seq = beep_seq
        self.state = self.DRIVE

        parking_cfg = parking_cfg or {}
        hazard_cfg = hazard_cfg or {}

        self.steer_limit = float(steer_limit)

        self.parking_approach_speed = int(parking_cfg.get("approach_speed", 20))
        self.parking_missing_frames = int(parking_cfg.get("missing_frames", 3))
        self.parking_steer_kp = float(parking_cfg.get("steer_kp", 0.8))
        self._parking_missing_count = 0
        self._last_oo_center_x_norm = 0.0

        self.hazard_beep_delay = float(hazard_cfg.get("beep_delay", 0.2))

        self._hazard_entry_time = 0.0
        self._hazard_beep_started = False

        # 비프 패턴(traffic: 동일음 3회, hazard: 다른 패턴 3회)
        self.traffic_beep_pattern = repeat_beeps(0.06, 0.06, 3)
        self.hazard_beep_pattern = repeat_beeps(0.3, 0.08, 3)

    def update(
        self,
        lane_steering: float,
        lane_speed: int,
        detections: Dict[str, YoloDetection],
        triggers: Dict[str, bool],
        now: float,
    ) -> MissionCommand:
        # 상태 전이
        if self.state == self.DRIVE:
            if triggers.get("red"):
                self.state = self.WAIT_TRAFFIC_LIGHT
                self.beep_seq.enqueue(self.traffic_beep_pattern, now)
            elif triggers.get("car"):
                self.state = self.HAZARD_ACTION
                self._hazard_entry_time = now
                self._hazard_beep_started = False
            elif triggers.get("oo"):
                self.state = self.PARKING_APPROACH
                self._parking_missing_count = 0

        elif self.state == self.WAIT_TRAFFIC_LIGHT:
            # red가 동시에 보이면 green 트리거 무시(깜빡임 안정화)
            if "red" not in detections:
                self.state = self.DRIVE

        elif self.state == self.HAZARD_ACTION:
            if (not self._hazard_beep_started) and (now - self._hazard_entry_time >= self.hazard_beep_delay):
                self.beep_seq.enqueue(self.hazard_beep_pattern, now)
                self._hazard_beep_started = True
            if self._hazard_beep_started and self.beep_seq.is_idle():
                self.state = self.DRIVE

        elif self.state == self.PARKING_APPROACH:
            det = detections.get("oo")
            if det is None:
                self._parking_missing_count += 1
                # O가 연속으로 안 보이면(발밑/시야 밖) 정지
                if self._parking_missing_count >= self.parking_missing_frames:
                    self.state = self.PARKING_HOLD
            else:
                self._parking_missing_count = 0
                self._last_oo_center_x_norm = det.center_x_norm

        elif self.state == self.PARKING_HOLD:
            pass

        # 출력 생성(override)
        force_stop = self.state in (self.WAIT_TRAFFIC_LIGHT, self.HAZARD_ACTION, self.PARKING_HOLD)
        base_speed = int(lane_speed)
        steering = float(lane_steering)

        if self.state == self.PARKING_APPROACH:
            base_speed = min(base_speed, self.parking_approach_speed)
            det = detections.get("oo")
            if det is not None:
                steering = self.parking_steer_kp * det.center_x_norm * self.steer_limit
                self._last_oo_center_x_norm = det.center_x_norm
            else:
                steering = 0.0

        if force_stop:
            base_speed = 0
            steering = 0.0

        return MissionCommand(base_speed=base_speed, steering=steering, force_stop=force_stop, state=self.state)
