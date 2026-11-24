"""YOLO 인식 결과를 안정화해 FSM 이벤트로 변환하는 모듈.

quest.md 요구사항:
- 연속 N프레임 Confirm
- bbox 최소 면적 비율(min_area_ratio)
- 쿨다운(cooldown)으로 원샷 처리
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Tuple


@dataclass
class YoloDetection:
    name: str
    conf: float
    bbox_xyxy: Tuple[float, float, float, float]
    area_ratio: float
    center_x_norm: float
    center_y_norm: float


class StableTrigger:
    """연속 프레임 확인 + 쿨다운 + 원샷 처리를 담당."""

    def __init__(self, confirm_frames: int = 3, cooldown_s: float = 0.0, release_frames: int = 2) -> None:
        self.confirm_frames = max(1, int(confirm_frames))
        self.cooldown_s = float(cooldown_s)
        self.release_frames = max(1, int(release_frames))
        self._present_count = 0
        self._absent_count = 0
        self._armed = True
        self._cooldown_until = 0.0

    def update(self, present: bool, now: float) -> bool:
        if present:
            self._present_count += 1
            self._absent_count = 0
        else:
            self._present_count = 0
            self._absent_count += 1
            if self._absent_count >= self.release_frames:
                self._armed = True
        if not present:
            return False
        if self._present_count >= self.confirm_frames and self._armed and now >= self._cooldown_until:
            self._armed = False
            if self.cooldown_s > 0:
                self._cooldown_until = now + self.cooldown_s
            return True
        return False


class YoloEventDetector:
    """YOLO 추론을 수행하고, 대상 클래스별 안정화 이벤트를 제공."""

    def __init__(
        self,
        model: Any,
        target_names: Iterable[str],
        imgsz: int = 320,
        conf: float = 0.5,
        device: Optional[str] = None,
        confirm_frames: int = 3,
        cooldown_s: Optional[Dict[str, float]] = None,
        min_area_ratio: Optional[Dict[str, float]] = None,
        release_frames: int = 2,
    ) -> None:
        self.model = model
        self.target_names = [str(n).lower() for n in target_names]
        self.imgsz = int(imgsz)
        self.conf = float(conf)
        self.cooldown_s = {str(k).lower(): float(v) for k, v in (cooldown_s or {}).items()}
        self.min_area_ratio = {str(k).lower(): float(v) for k, v in (min_area_ratio or {}).items()}
        self.stables: Dict[str, StableTrigger] = {
            name: StableTrigger(confirm_frames, self.cooldown_s.get(name, 0.0), release_frames)
            for name in self.target_names
        }
        # 시각화를 위해 마지막 raw 결과를 저장
        self.last_results = None
        if device:
            try:
                self.model.to(device)
            except Exception:
                pass

    def update_thresholds(self, min_area_ratio: Dict[str, float]) -> None:
        self.min_area_ratio = {str(k).lower(): float(v) for k, v in min_area_ratio.items()}

    def step(self, frame, now: float) -> Tuple[Dict[str, YoloDetection], Dict[str, bool]]:
        """한 프레임 처리 후 (detections, triggers) 반환."""
        results = self.model(frame, imgsz=self.imgsz, conf=self.conf, verbose=False)
        self.last_results = results
        if not results:
            detections: Dict[str, YoloDetection] = {}
            triggers = {name: self.stables[name].update(False, now) for name in self.target_names}
            triggers = {k: v for k, v in triggers.items() if v}
            return detections, triggers

        r0 = results[0]
        frame_h, frame_w = r0.orig_shape[:2]
        frame_area = float(frame_h * frame_w) if frame_h and frame_w else 0.0

        names_lc = {k: str(v).lower() for k, v in getattr(self.model, "names", {}).items()}
        detections = {}

        boxes = getattr(r0, "boxes", None)
        if boxes is None:
            boxes = []

        for box in boxes:
            cls_id = int(box.cls.item()) if hasattr(box.cls, "item") else int(box.cls)
            cls_name = names_lc.get(cls_id, "")
            if cls_name not in self.target_names:
                continue

            x1, y1, x2, y2 = box.xyxy[0].tolist()
            area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
            ratio = (area / frame_area) if frame_area > 0 else 0.0
            if ratio < self.min_area_ratio.get(cls_name, 0.0):
                continue

            conf_val = float(box.conf.item()) if hasattr(box.conf, "item") else float(box.conf)
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0
            center_x_norm = (cx - (frame_w / 2.0)) / (frame_w / 2.0) if frame_w > 0 else 0.0
            center_y_norm = (cy - (frame_h / 2.0)) / (frame_h / 2.0) if frame_h > 0 else 0.0

            det = YoloDetection(
                name=cls_name,
                conf=conf_val,
                bbox_xyxy=(float(x1), float(y1), float(x2), float(y2)),
                area_ratio=ratio,
                center_x_norm=center_x_norm,
                center_y_norm=center_y_norm,
            )

            prev = detections.get(cls_name)
            if prev is None or det.area_ratio > prev.area_ratio:
                detections[cls_name] = det

        present = set(detections.keys())
        triggers: Dict[str, bool] = {}
        for name, stable in self.stables.items():
            if stable.update(name in present, now):
                triggers[name] = True
        return detections, triggers
