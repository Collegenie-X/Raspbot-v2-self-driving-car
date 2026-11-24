"""전처리 및 ROI/IPM 관련 유틸리티."""

from __future__ import annotations

from typing import Tuple

import cv2
import numpy as np


def calculate_roi_points(
    width: int, height: int, roi_top_y: int, roi_bottom_y: int, margin: int = 10
) -> Tuple[np.ndarray, int, int]:
    top_y = int(roi_top_y * height / 1000)
    bottom_y = int(roi_bottom_y * height / 1000)
    top_y = max(0, min(top_y, height - 1))
    bottom_y = max(0, min(bottom_y, height - 1))

    if top_y >= bottom_y:
        top_y = max(0, bottom_y - 50)

    pts_src = np.float32(
        [
            [margin, bottom_y],
            [width - margin, bottom_y],
            [width - margin, top_y],
            [margin, top_y],
        ]
    )
    return pts_src, top_y, bottom_y


def apply_roi_overlay(frame, pts_src: np.ndarray, width: int, height: int, top_y: int, bottom_y: int):
    """ROI를 시각화한 프레임을 반환."""
    pts = pts_src.reshape((-1, 1, 2)).astype(np.int32)
    frame_with_rect = cv2.polylines(
        frame.copy(), [pts], isClosed=True, color=(0, 255, 0), thickness=2
    )
    cv2.putText(
        frame_with_rect,
        f"Resolution: {width}x{height}",
        (10, 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 255),
        1,
    )
    cv2.putText(
        frame_with_rect,
        f"ROI Top: {top_y} / Bottom: {bottom_y}",
        (10, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 255),
        1,
    )
    return frame_with_rect


def warp_perspective(frame, pts_src: np.ndarray, target_size: Tuple[int, int]) -> Tuple[np.ndarray, np.ndarray]:
    """버드아이뷰 변환."""
    target_w, target_h = target_size
    pts_dst = np.float32([[0, target_h], [target_w, target_h], [target_w, 0], [0, 0]])
    mat_affine = cv2.getPerspectiveTransform(pts_src, pts_dst)
    frame_transformed = cv2.warpPerspective(frame, mat_affine, (target_w, target_h))
    return frame_transformed, mat_affine
