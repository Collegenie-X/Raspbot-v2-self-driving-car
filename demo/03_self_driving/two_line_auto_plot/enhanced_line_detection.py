#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
선명도 개선 라인 검출 함수 모듈
다양한 이미지 처리 기법을 사용하여 라인 검출 정확도 향상

사용 방법:
    from enhanced_line_detection import enhanced_process_frame

    binary_frame = enhanced_process_frame(
        frame, detect_value, r_weight, g_weight, b_weight,
        roi_top_y, roi_bottom_y, enhancement_level=2
    )
"""

import cv2
import numpy as np


def enhance_contrast(frame_gray):
    """
    히스토그램 균등화로 대비 향상

    Args:
        frame_gray: 그레이스케일 이미지

    Returns:
        대비가 향상된 이미지
    """
    # CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(frame_gray)
    return enhanced


def unsharp_mask(frame_gray):
    """
    언샤프 마스킹으로 선명도 향상

    Args:
        frame_gray: 그레이스케일 이미지

    Returns:
        선명도가 향상된 이미지
    """
    # 가우시안 블러
    blurred = cv2.GaussianBlur(frame_gray, (9, 9), 2.0)

    # 언샤프 마스킹
    sharpened = cv2.addWeighted(frame_gray, 1.5, blurred, -0.5, 0)

    return sharpened


def adaptive_threshold(frame_gray):
    """
    적응형 임계값을 사용한 이진화

    Args:
        frame_gray: 그레이스케일 이미지

    Returns:
        이진화된 이미지
    """
    # 블록 크기: 11, C 상수: 2
    binary_adaptive = cv2.adaptiveThreshold(
        frame_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    return binary_adaptive


def enhanced_morphology(binary_frame):
    """
    모폴로지 연산으로 라인 선명화

    Args:
        binary_frame: 이진화된 이미지

    Returns:
        선명화된 이미지
    """
    # 닫힘 연산: 작은 구멍 채우기
    kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    binary_frame = cv2.morphologyEx(binary_frame, cv2.MORPH_CLOSE, kernel_close)

    # 열림 연산: 작은 노이즈 제거
    kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    binary_frame = cv2.morphologyEx(binary_frame, cv2.MORPH_OPEN, kernel_open)

    # 팽창 연산: 라인 두께 증가 (수평 방향)
    kernel_dilate = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 1))
    binary_frame = cv2.dilate(binary_frame, kernel_dilate, iterations=1)

    return binary_frame


def enhanced_binary(frame_gray, use_adaptive=False):
    """
    개선된 이진화 방법

    Args:
        frame_gray: 그레이스케일 이미지
        use_adaptive: 적응형 임계값 사용 여부

    Returns:
        이진화된 이미지
    """
    if use_adaptive:
        # 적응형 임계값
        binary = adaptive_threshold(frame_gray)
    else:
        # 기본 임계값 + Canny
        _, thresh = cv2.threshold(frame_gray, 200, 255, cv2.THRESH_BINARY)
        edge = cv2.Canny(frame_gray, 900, 900, apertureSize=3, L2gradient=False)
        binary = cv2.add(thresh, edge)

    return binary


def enhanced_process_frame(
    frame,
    detect_value,
    r_weight,
    g_weight,
    b_weight,
    roi_top_y,
    roi_bottom_y,
    enhancement_level=1,
):
    """
    개선된 프레임 처리 함수

    Args:
        frame: 원본 프레임
        detect_value: 이진화 임계값
        r_weight: R 채널 가중치
        g_weight: G 채널 가중치
        b_weight: B 채널 가중치
        roi_top_y: ROI 상단 Y 위치
        roi_bottom_y: ROI 하단 Y 위치
        enhancement_level: 개선 수준 (0=기본, 1=보통, 2=높음, 3=최대)

    Returns:
        이진화된 이미지
    """
    from two_line_lane_center import (
        calculate_roi_points,
        apply_perspective_transform,
        weighted_gray,
    )

    actual_h, actual_w = frame.shape[:2]

    # ROI 영역 계산
    pts_src, top_y, bottom_y = calculate_roi_points(
        actual_w, actual_h, roi_top_y, roi_bottom_y
    )

    # 원근 변환 적용
    frame_transformed = apply_perspective_transform(frame, pts_src)

    # 그레이스케일 변환
    gray_frame = weighted_gray(frame_transformed, r_weight, g_weight, b_weight)

    # 개선 수준에 따른 처리
    if enhancement_level >= 1:
        # 히스토그램 균등화
        gray_frame = enhance_contrast(gray_frame)

    if enhancement_level >= 2:
        # 언샤프 마스킹
        gray_frame = unsharp_mask(gray_frame)

    # 이진화
    use_adaptive = enhancement_level >= 3
    binary_frame = enhanced_binary(gray_frame, use_adaptive=use_adaptive)

    # 모폴로지 연산
    if enhancement_level >= 1:
        binary_frame = enhanced_morphology(binary_frame)

    return binary_frame


# 사용 예제
if __name__ == "__main__":
    # 테스트 코드
    import sys
    import os

    sys.path.append(
        os.path.join(os.path.dirname(__file__), "..", "..", "lib", "raspbot")
    )

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

    enhancement_level = 2  # 0=기본, 1=보통, 2=높음, 3=최대

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 개선된 처리
        binary = enhanced_process_frame(
            frame,
            detect_value=120,
            r_weight=30,
            g_weight=40,
            b_weight=60,
            roi_top_y=200,
            roi_bottom_y=800,
            enhancement_level=enhancement_level,
        )

        cv2.imshow("Enhanced Binary", binary)

        key = cv2.waitKey(30) & 0xFF
        if key == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()
