"""YOLO 추론을 메인 제어 루프에서 분리하기 위한 비동기 러너.

메인 루프가 매 프레임 YOLO 추론을 기다리면 조향/속도 업데이트가 지연될 수 있다.
이 모듈은 최신 프레임만 유지하는 큐를 사용해 YOLO를 별도 스레드에서 돌리고,
메인 루프는 가장 최근 결과를 폴링(poll)해서 사용하도록 한다.
"""

from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass
from typing import Dict, List, Tuple

from raspbot.perception.yolo_events import YoloDetection, YoloEventDetector


@dataclass(frozen=True)
class YoloRawBox:
    cls_id: int
    name: str
    conf: float
    bbox_xyxy: Tuple[float, float, float, float]
    area_ratio: float


@dataclass(frozen=True)
class YoloAsyncResult:
    timestamp: float
    detections: Dict[str, YoloDetection]
    triggers: Dict[str, bool]
    raw_boxes: List[YoloRawBox]


class YoloAsyncRunner:
    """YOLO 추론을 별도 스레드에서 수행하고 결과를 큐로 전달한다."""

    def __init__(self, detector: YoloEventDetector, infer_interval_s: float = 0.0) -> None:
        self.detector = detector

        self._settings_lock = threading.Lock()
        self._infer_interval_s = max(0.0, float(infer_interval_s))
        self._min_area_ratio = dict(detector.min_area_ratio)

        self._frame_queue: "queue.Queue" = queue.Queue(maxsize=1)
        self._result_queue: "queue.Queue[YoloAsyncResult]" = queue.Queue(maxsize=5)

        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._worker_loop, name="yolo_async_runner", daemon=True)
        self._thread.start()

        # 메인 스레드에서만 갱신/참조
        self._last_detections: Dict[str, YoloDetection] = {}
        self._last_raw_boxes: List[YoloRawBox] = []
        self._last_timestamp: float = 0.0

    def set_infer_interval_s(self, infer_interval_s: float) -> None:
        with self._settings_lock:
            self._infer_interval_s = max(0.0, float(infer_interval_s))

    def set_min_area_ratio(self, min_area_ratio: Dict[str, float]) -> None:
        with self._settings_lock:
            self._min_area_ratio = {str(k).lower(): float(v) for k, v in (min_area_ratio or {}).items()}

    def update_settings(self, infer_interval_s: float, min_area_ratio: Dict[str, float]) -> None:
        with self._settings_lock:
            self._infer_interval_s = max(0.0, float(infer_interval_s))
            self._min_area_ratio = {str(k).lower(): float(v) for k, v in (min_area_ratio or {}).items()}

    def submit_frame(self, frame) -> None:
        """최신 프레임을 큐에 넣는다(가득 차면 이전 프레임을 버리고 최신으로 교체)."""
        try:
            self._frame_queue.put_nowait(frame)
        except queue.Full:
            try:
                _ = self._frame_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self._frame_queue.put_nowait(frame)
            except queue.Full:
                pass

    def poll(self) -> Tuple[Dict[str, YoloDetection], Dict[str, bool], List[YoloRawBox], float]:
        """현재까지 완료된 결과를 모두 소비하고 (최근 detections, 누적 triggers, 최근 raw_boxes, timestamp) 반환."""
        merged_triggers: Dict[str, bool] = {}
        last_result: YoloAsyncResult | None = None
        while True:
            try:
                result = self._result_queue.get_nowait()
            except queue.Empty:
                break
            last_result = result
            for name in result.triggers.keys():
                merged_triggers[name] = True

        if last_result is not None:
            self._last_detections = last_result.detections
            self._last_raw_boxes = last_result.raw_boxes
            self._last_timestamp = last_result.timestamp

        return self._last_detections, merged_triggers, self._last_raw_boxes, self._last_timestamp

    def stop(self, timeout_s: float = 1.0) -> None:
        self._stop_event.set()
        try:
            self._frame_queue.put_nowait(None)
        except queue.Full:
            pass
        self._thread.join(timeout=timeout_s)

    def _put_result(self, result: YoloAsyncResult) -> None:
        try:
            self._result_queue.put_nowait(result)
        except queue.Full:
            try:
                _ = self._result_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self._result_queue.put_nowait(result)
            except queue.Full:
                pass

    def _extract_raw_boxes(self) -> List[YoloRawBox]:
        results = getattr(self.detector, "last_results", None)
        if not results:
            return []

        r0 = results[0]
        frame_h, frame_w = r0.orig_shape[:2]
        frame_area = float(frame_h * frame_w) if frame_h and frame_w else 0.0

        names_lc = {k: str(v).lower() for k, v in getattr(self.detector.model, "names", {}).items()}
        boxes = getattr(r0, "boxes", None) or []

        raw_boxes: List[YoloRawBox] = []
        for box in boxes:
            cls_id = int(box.cls.item()) if hasattr(box.cls, "item") else int(box.cls)
            cls_name = names_lc.get(cls_id, "")

            x1, y1, x2, y2 = box.xyxy[0].tolist()
            area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
            ratio = (area / frame_area) if frame_area > 0 else 0.0

            conf_val = float(box.conf.item()) if hasattr(box.conf, "item") else float(box.conf)
            raw_boxes.append(
                YoloRawBox(
                    cls_id=cls_id,
                    name=cls_name,
                    conf=conf_val,
                    bbox_xyxy=(float(x1), float(y1), float(x2), float(y2)),
                    area_ratio=float(ratio),
                )
            )
        return raw_boxes

    def _worker_loop(self) -> None:
        last_infer_time = 0.0
        pending_frame = None
        has_new_frame = False

        while not self._stop_event.is_set():
            try:
                frame = self._frame_queue.get(timeout=0.05)
                if frame is None:
                    continue
                pending_frame = frame
                has_new_frame = True
            except queue.Empty:
                pass

            if not has_new_frame:
                continue

            now = time.perf_counter()
            with self._settings_lock:
                infer_interval_s = self._infer_interval_s
                min_area_ratio = dict(self._min_area_ratio)

            if infer_interval_s > 0 and (now - last_infer_time) < infer_interval_s:
                continue

            try:
                self.detector.update_thresholds(min_area_ratio)
                detections, triggers = self.detector.step(pending_frame, now)
                raw_boxes = self._extract_raw_boxes()
                self._put_result(
                    YoloAsyncResult(
                        timestamp=now,
                        detections=detections,
                        triggers=triggers,
                        raw_boxes=raw_boxes,
                    )
                )
            except Exception:
                # 추론 오류가 나도 메인 루프를 멈추지 않도록 무시(다음 프레임에서 재시도)
                pass

            last_infer_time = now
            has_new_frame = False
