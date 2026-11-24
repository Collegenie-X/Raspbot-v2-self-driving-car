"""라인 검출 및 에러 계산."""

from __future__ import annotations

from typing import List, Optional, Tuple

import cv2
import numpy as np


def detect_road_lines(color_frame, gray_frame, detect_value: int) -> np.ndarray:
    """빨간색/엷은 회색 차선을 검출한 이진 이미지를 반환."""
    hsv_frame = cv2.cvtColor(color_frame, cv2.COLOR_BGR2HSV)

    lower_red1 = np.array([0, 70, 50])
    upper_red1 = np.array([10, 255, 255])
    mask_red1 = cv2.inRange(hsv_frame, lower_red1, upper_red1)

    lower_red2 = np.array([170, 70, 50])
    upper_red2 = np.array([180, 255, 255])
    mask_red2 = cv2.inRange(hsv_frame, lower_red2, upper_red2)
    mask_red = cv2.bitwise_or(mask_red1, mask_red2)

    threshold_gray = max(detect_value - 30, 80)
    _, mask_gray = cv2.threshold(gray_frame, threshold_gray, 255, cv2.THRESH_BINARY)

    dark_threshold = 50
    _, mask_dark = cv2.threshold(gray_frame, dark_threshold, 255, cv2.THRESH_BINARY)
    mask_gray = cv2.bitwise_and(mask_gray, mask_dark)

    mask_lines = cv2.bitwise_or(mask_red, mask_gray)

    kernel = np.ones((5, 5), np.uint8)
    mask_lines = cv2.morphologyEx(mask_lines, cv2.MORPH_CLOSE, kernel)
    mask_lines = cv2.morphologyEx(mask_lines, cv2.MORPH_OPEN, kernel)
    return mask_lines


def compute_lane_error(
    binary_frame: np.ndarray,
) -> Tuple[Optional[float], Optional[int]]:
    """
    도로(검정 영역)를 기준으로 중심 오차를 계산.

    Returns:
        error_norm: (-1~1) 정규화된 중심 오차. 좌측이 음수, 우측이 양수.
        centroid_x: 도로 영역 무게중심 x 좌표
    """
    height, width = binary_frame.shape[:2]
    road_mask = cv2.bitwise_not(binary_frame)
    moments = cv2.moments(road_mask)

    if moments["m00"] < 1e-3:
        return None, None

    centroid_x = int(moments["m10"] / moments["m00"])
    error_px = centroid_x - (width // 2)
    error_norm = error_px / (width / 2)
    return error_norm, centroid_x


def estimate_heading(
    binary_frame: np.ndarray,
    bands: Tuple[Tuple[float, float], ...] = ((0.15, 0.3), (0.45, 0.6), (0.75, 0.9)),
    weights: Optional[Tuple[float, ...]] = None,
    connect_close_px: int = 1,
    merge_gap_px: int = 1,
    p1_margin_px: int = 1,
) -> Tuple[Optional[float], List[Tuple[int, int]], Optional[float], np.ndarray]:
    """
    여러 높이 구간에서 도로 중심을 추정해 진행 방향 기울기를 계산.
    p3가 포함된 컴포넌트(필요시 p2와 병합)만 남겨 p1이 튀는 것을 막는다.

    Returns:
        slope_norm: 하단 대비 상단 중심 이동량을 (-1~1)로 정규화한 값. 음수=좌, 양수=우.
        centers: 각 구간에서 구한 (x, y) 중심 좌표 리스트
        top_offset_norm: 가중 상단 중심이 화면 중앙에서 얼마나 치우쳤는지 (-1~1)
        target_mask: p3(필요시 p2 병합)과 연결된 도로 영역 마스크(전경=255)
    """
    h, w = binary_frame.shape[:2]
    road_mask = cv2.bitwise_not(binary_frame)

    close_ksize = max(1, 2 * connect_close_px + 1)
    close_kernel = np.ones((close_ksize, close_ksize), np.uint8)
    road_mask = cv2.morphologyEx(road_mask, cv2.MORPH_CLOSE, close_kernel)

    band_ranges: List[Tuple[int, int]] = []
    for band in bands:
        y0 = int(band[0] * h)
        y1 = int(band[1] * h)
        y0 = max(0, min(h - 1, y0))
        y1 = max(0, min(h, y1))
        if y1 <= y0:
            continue
        band_ranges.append((y0, y1))

    def calc_centers(mask: np.ndarray) -> Tuple[List[Tuple[int, int]], List[Tuple[int, Tuple[int, int]]]]:
        pts: List[Tuple[int, int]] = []
        meta: List[Tuple[int, Tuple[int, int]]] = []
        for idx, (y0, y1) in enumerate(band_ranges):
            band_mask = mask[y0:y1, :]
            m = cv2.moments(band_mask)
            if m["m00"] < 1e-3:
                continue
            cx = int(m["m10"] / m["m00"])
            cy = (y0 + y1) // 2
            pts.append((cx, cy))
            meta.append((idx, (cx, cy)))
        return pts, meta

    _, centers_meta = calc_centers(road_mask)

    labels = None
    try:
        _, labels, _, _ = cv2.connectedComponentsWithStats(road_mask, connectivity=8)
    except cv2.error:
        labels = None

    merge_ksize = max(3, 2 * merge_gap_px + 1)
    merge_kernel = np.ones((merge_ksize, merge_ksize), np.uint8)

    def get_label(pt: Tuple[int, int]) -> Optional[int]:
        if labels is None:
            return None
        x, y = pt
        if x < 0 or x >= w or y < 0 or y >= h:
            return None
        return int(labels[y, x])

    def find_band_meta(band_idx: int) -> Optional[Tuple[int, Tuple[int, int]]]:
        for idx, pt in centers_meta:
            if idx == band_idx:
                return idx, pt
        return None

    p2_meta = find_band_meta(1)
    p3_meta = find_band_meta(2)

    target_mask = road_mask
    if labels is not None and p3_meta:
        # p3가 포함된 컴포넌트만 남기고, p2가 인접하면 병합한다.
        _, p3_pt = p3_meta
        p3_label = get_label(p3_pt)
        selected_mask = None
        if p3_label and p3_label > 0:
            selected_mask = (labels == p3_label).astype(np.uint8) * 255

            if p2_meta:
                _, p2_pt = p2_meta
                p2_label = get_label(p2_pt)
                if p2_label and p2_label > 0 and p2_label != p3_label:
                    p2_mask = (labels == p2_label).astype(np.uint8) * 255
                    p3_mask = selected_mask.copy()
                    overlap = cv2.bitwise_and(
                        cv2.dilate(p2_mask, merge_kernel, iterations=1),
                        cv2.dilate(p3_mask, merge_kernel, iterations=1),
                    )
                    if np.any(overlap):
                        merged_mask = cv2.bitwise_or(p2_mask, p3_mask)
                        merged_mask = cv2.morphologyEx(merged_mask, cv2.MORPH_CLOSE, merge_kernel)
                        selected_mask = merged_mask

        if selected_mask is not None:
            target_mask = selected_mask

    if p1_margin_px > 0:
        margin_ksize = max(1, 2 * p1_margin_px + 1)
        margin_kernel = np.ones((margin_ksize, margin_ksize), np.uint8)
        target_mask = cv2.dilate(target_mask, margin_kernel, iterations=1)

    centers, _ = calc_centers(target_mask)

    if len(centers) < 2:
        top_offset_norm = (
            (centers[0][0] - (w / 2)) / (w / 2) if centers else None
        )
        return None, centers, top_offset_norm, target_mask

    default_weights = (1.5, 1.0, 0.7)
    use_weights = list(weights) if weights else list(default_weights[: len(centers)])
    if len(use_weights) < len(centers):
        use_weights += [use_weights[-1]] * (len(centers) - len(use_weights))

    bottom_x, _ = centers[-1]
    weighted_top = sum(cx * w for (cx, _), w in zip(centers, use_weights)) / sum(
        use_weights
    )

    slope_px = weighted_top - bottom_x
    slope_norm = slope_px / (w / 2)
    slope_norm = float(max(-1.0, min(1.0, slope_norm)))
    top_offset_norm = (weighted_top - (w / 2)) / (w / 2)
    top_offset_norm = float(max(-1.0, min(1.0, top_offset_norm)))
    return slope_norm, centers, top_offset_norm, target_mask