"""카메라 초기화 및 설정 래퍼."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import cv2


@dataclass
class CameraConfig:
    index: int = 0
    resolution: Tuple[int, int] = (320, 240)
    brightness: int = 0
    contrast: int = 0
    saturation: int = 50
    exposure: int = 100
    gain: int = 0


class Camera:
    def __init__(self, config: CameraConfig) -> None:
        self.config = config
        self.cap = cv2.VideoCapture(config.index, cv2.CAP_V4L2)
        self.apply_settings(
            brightness=config.brightness,
            contrast=config.contrast,
            saturation=config.saturation,
            exposure=config.exposure,
            gain=config.gain,
        )
        w, h = config.resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

    def apply_settings(
        self,
        brightness: int,
        contrast: int,
        saturation: int,
        exposure: int,
        gain: int,
    ) -> None:
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, brightness)
        self.cap.set(cv2.CAP_PROP_CONTRAST, contrast)
        self.cap.set(cv2.CAP_PROP_SATURATION, saturation)
        self.cap.set(cv2.CAP_PROP_EXPOSURE, exposure)
        self.cap.set(cv2.CAP_PROP_GAIN, gain)

    def read(self):
        ret, frame = self.cap.read()
        if not ret:
            raise RuntimeError("카메라에서 프레임을 읽지 못했습니다.")
        return frame

    def release(self) -> None:
        self.cap.release()
