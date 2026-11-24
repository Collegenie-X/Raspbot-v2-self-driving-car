"""디버그용 시각화 유틸리티."""

from __future__ import annotations

from typing import Optional, Tuple

import cv2
import numpy as np


def visualize_binary_debug(
    binary_frame: np.ndarray,
    direction: str,
    centroid_x: Optional[int],
    steering: Optional[float] = None,
    fps: Optional[float] = None,
    heading: Optional[float] = None,
    heading_offset: Optional[float] = None,
    turn_thresholds: Optional[Tuple[float, float]] = None,
    centers=None,
):
    frame_color = cv2.cvtColor(binary_frame, cv2.COLOR_GRAY2BGR)
    h, w = frame_color.shape[:2]

    overlay = frame_color.copy()
    cv2.rectangle(overlay, (0, 0), (w, 110), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, frame_color, 0.3, 0, frame_color)

    cv2.putText(
        frame_color,
        f"DIR: {direction}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 255, 255),
        2,
    )

    if steering is not None:
        cv2.putText(
            frame_color,
            f"steer: {steering:.2f}",
            (10, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (180, 255, 180),
            1,
        )

    if heading is not None:
        cv2.putText(
            frame_color,
            f"heading: {heading:.2f}",
            (10, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (180, 180, 255),
            1,
        )
    if heading_offset is not None:
        cv2.putText(
            frame_color,
            f"heading_off: {heading_offset:.2f}",
            (10, 140),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (180, 220, 255),
            1,
        )

    if turn_thresholds:
        slope_thr, offset_thr = turn_thresholds
        cv2.putText(
            frame_color,
            f"turn thr slope:{slope_thr:.2f} off:{offset_thr:.2f}",
            (10, 160),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (150, 255, 150),
            1,
        )

    if fps is not None:
        cv2.putText(
            frame_color,
            f"FPS: {fps:.1f}",
            (w - 140, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            1,
        )

    left_line = w // 3
    right_line = 2 * w // 3
    cv2.line(frame_color, (left_line, 0), (left_line, h), (255, 0, 0), 2)
    cv2.line(frame_color, (right_line, 0), (right_line, h), (255, 0, 0), 2)

    cv2.putText(
        frame_color,
        "LEFT",
        (w // 6 - 20, h - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 0),
        2,
    )
    cv2.putText(
        frame_color,
        "CENTER",
        (w // 2 - 35, h - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 0),
        2,
    )
    cv2.putText(
        frame_color,
        "RIGHT",
        (5 * w // 6 - 25, h - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 0),
        2,
    )

    if centroid_x is not None:
        cv2.line(frame_color, (centroid_x, 0), (centroid_x, h), (0, 255, 255), 2)
        cv2.circle(frame_color, (centroid_x, h // 2), 6, (0, 255, 255), -1)

    if centers:
        for idx, (cx, cy) in enumerate(centers):
            cv2.circle(frame_color, (cx, cy), 5, (0, 165, 255), -1)
            cv2.putText(
                frame_color,
                f"P{idx+1}",
                (cx + 5, cy - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (0, 165, 255),
                1,
            )
        if len(centers) >= 2:
            for i in range(len(centers) - 1):
                cv2.line(frame_color, centers[i], centers[i + 1], (0, 165, 255), 2)

    return frame_color
