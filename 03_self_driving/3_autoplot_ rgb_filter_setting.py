#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspbot v2 자율주행 코드 (개선 버전 v3.0)
RGB 필터링 기반 라인 트레이싱 자율주행 시스템

Copyright (C): 2015-2024, Shenzhen Yahboom Tech
Modified: 2025-12-08

═══════════════════════════════════════════════════════════
버전 히스토리:
═══════════════════════════════════════════════════════════
v2.1: 기본 라인 트레이싱, 6구역 분할
v3.0: RGB 필터링 + 3등분 분석 + 모듈화 구조 (현재)

═══════════════════════════════════════════════════════════
주요 기능:
═══════════════════════════════════════════════════════════
1. 실시간 비전 처리 (OpenCV 기반)
   - 원근 변환 (Perspective Transform)
   - RGB 가중 그레이스케일 변환 (빛 반사 필터링)
   - HSV 기반 빨간색 + 밝기 기반 회색 도로선 검출

2. 히스토그램 기반 방향 결정 (3등분 분석)
   - 좌/중앙/우 영역 분할 분석
   - 좌우 차이 기반 회전 판단 (최우선)
   - 중앙 클리어 체크 (직진 판단)
   - 막다른 길 감지 및 랜덤 탈출

3. 차량 제어
   - 직진, 좌회전, 우회전 (제자리 회전)
   - LED 색상 피드백 (초록=직진, 노랑=회전)
   - 모터 ON/OFF 토글 (SPACE 키)

4. 실시간 파라미터 조정
   - OpenCV 트랙바를 통한 실시간 튜닝
   - RGB 가중치, ROI 영역, 임계값 등

═══════════════════════════════════════════════════════════
도로 환경 특성:
═══════════════════════════════════════════════════════════
- 검정색 바탕: 주행 가능 영역 (이진화 결과 0)
- 회색/흰색 선: 직선 경계선 (이진화 결과 255)
- 빨간색 선: 곡선 구간 표시 (이진화 결과 255)

핵심 원리:
- 히스토그램 합이 작을수록 = 검정 도로 많음 = 주행 가능
- 히스토그램 합이 클수록 = 도로선 많음 = 경계/막힘

═══════════════════════════════════════════════════════════
실행 단계:
═══════════════════════════════════════════════════════════
1단계: 라이브러리 및 모듈 import
2단계: 설정값 로딩
3단계: 하드웨어 초기화 (Raspbot, 카메라, 서보)
4단계: 트랙바 및 윈도우 설정
5단계: 이미지 처리 함수 정의
6단계: 차량 제어 함수 정의
7단계: 서보 모터 제어 함수 정의
8단계: 방향 결정 함수 정의
9단계: 메인 루프 실행
10단계: 정리 및 종료

═══════════════════════════════════════════════════════════
사용 방법:
═══════════════════════════════════════════════════════════
키보드 단축키:
- ESC: 종료
- SPACE: 모터 ON/OFF 토글 (카메라는 계속 작동)
- 'l': LED 토글
- 'b': 부저 토글

트랙바 조정:
- ROI_Top_Y / ROI_Bottom_Y: ROI 영역 조절
- Direction_Threshold: 회전 민감도 (높으면 덜 회전)
- R/G/B_weight: RGB 가중치 (빛 반사 필터링)
- Detect_Value: 이진화 임계값

권장 RGB 설정:
- 밝은 환경 (빛 반사): R=30, G=40, B=60~80
- 어두운 환경: R=60, G=40, B=30
"""

import sys
import os

# ════════════════════════════════════════════════════════
# STEP 1: Import Libraries and Modules
# ════════════════════════════════════════════════════════
print("=" * 60)
print("  STEP 1: Loading Libraries...")
print("=" * 60)

# Raspbot 라이브러리 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib", "raspbot"))

import cv2
import numpy as np
import random
import time
from Raspbot_Lib import Raspbot

print("Libraries loaded successfully\n")

# ════════════════════════════════════════════════════════
# STEP 2: Load Configuration
# ════════════════════════════════════════════════════════
print("=" * 60)
print("  STEP 2: Loading Configuration...")
print("=" * 60)

# ────────────────────────────────────────────────────────
# 기본 속도 설정 (-255 ~ 255)
# ────────────────────────────────────────────────────────
DEFAULT_SPEED_UP = 15  # 전진/주 속도
DEFAULT_SPEED_DOWN = 8  # 회전 시 감속 측 속도

# ────────────────────────────────────────────────────────
# 라인 검출 설정
# ────────────────────────────────────────────────────────
DEFAULT_DETECT_VALUE = 120  # 이진화 임계값 (80~150)
DEFAULT_BRIGHTNESS = 32  # 카메라 밝기 (0~100)
DEFAULT_CONTRAST = 0  # 카메라 대비 (0~100)

# ────────────────────────────────────────────────────────
# RGB 가중치 설정 (빛 반사 필터링)
# ────────────────────────────────────────────────────────
# 파랑 채널(B)을 강조하면 빛 반사 억제에 효과적
DEFAULT_R_WEIGHT = 30  # 빨강 채널 가중치 (0~100)
DEFAULT_G_WEIGHT = 40  # 초록 채널 가중치 (0~100)
DEFAULT_B_WEIGHT = 60  # 파랑 채널 가중치 (0~100)

# ────────────────────────────────────────────────────────
# 방향 판단 임계값
# ────────────────────────────────────────────────────────
DEFAULT_DIRECTION_THRESHOLD = 35000  # 좌우 차이 임계값 (회전 민감도)
DEFAULT_UP_THRESHOLD = 220000  # 막다른 골목 감지 임계값

# ────────────────────────────────────────────────────────
# 중앙 클리어 임계값 (0.0 ~ 1.0)
# ────────────────────────────────────────────────────────
# center_ratio < CENTER_CLEAR_THRESHOLD → 중앙에 도로선 적음 → 직진 가능
CENTER_CLEAR_THRESHOLD = 0.2  # 20% 미만이면 중앙이 클리어

# ────────────────────────────────────────────────────────
# 서보 모터 각도
# ────────────────────────────────────────────────────────
DEFAULT_SERVO_1 = 95  # 좌우 각도 (0~180)
DEFAULT_SERVO_2 = 0  # 상하 각도 (0~110)

# ────────────────────────────────────────────────────────
# 디버그 및 효과 설정
# ────────────────────────────────────────────────────────
DEBUG_MODE = True  # True: 상세 정보 출력

USE_LED_EFFECTS = True  # LED 효과 사용 여부
LED_ON_START = True  # 시작 시 LED 켜기

USE_BEEP = True  # 부저 사용 여부
BEEP_ON_START = True  # 시작 시 부저 울리기
BEEP_ON_TURN = False  # 회전 시 부저 울리기

# ────────────────────────────────────────────────────────
# 상태 변수 (전역)
# ────────────────────────────────────────────────────────
motor_enabled = True  # 모터 ON/OFF 상태 (SPACE 키로 토글)
led_state = False  # LED 상태
beep_state = False  # 부저 상태
frame_count = 0  # 프레임 카운터

print("Configuration loaded successfully")
print(
    f"   RGB Weights: R={DEFAULT_R_WEIGHT}, G={DEFAULT_G_WEIGHT}, B={DEFAULT_B_WEIGHT}"
)
print(f"   Direction Threshold: {DEFAULT_DIRECTION_THRESHOLD}")
print(f"   Up Threshold: {DEFAULT_UP_THRESHOLD}\n")

# ════════════════════════════════════════════════════════
# STEP 3: Initialize Hardware
# ════════════════════════════════════════════════════════
print("=" * 60)
print("  STEP 3: Initializing Hardware...")
print("=" * 60)


def initialize_raspbot():
    """Raspbot 하드웨어 초기화"""
    try:
        bot = Raspbot()
        print("Raspbot hardware initialized successfully")
        return bot
    except Exception as e:
        print(f"Failed to initialize Raspbot: {e}")
        sys.exit(1)


def initialize_camera(width=320, height=240):
    """카메라 초기화 및 설정"""
    try:
        print("\nInitializing USB camera...")

        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_BRIGHTNESS, DEFAULT_BRIGHTNESS)
        cap.set(cv2.CAP_PROP_CONTRAST, DEFAULT_CONTRAST)
        cap.set(cv2.CAP_PROP_SATURATION, 50)
        cap.set(cv2.CAP_PROP_EXPOSURE, 100)

        # 카메라 테스트
        ret, frame = cap.read()
        if not ret or frame is None:
            raise Exception("Cannot read frame from camera")

        actual_height, actual_width = frame.shape[:2]
        print("USB camera initialized successfully")
        print(f"   Requested resolution: {width}x{height}")
        print(f"   Actual resolution: {actual_width}x{actual_height}")

        return cap
    except Exception as e:
        print(f"\nFailed to initialize camera: {e}\n")
        raise


def setup_initial_hardware_state(bot):
    """초기 하드웨어 상태 설정"""
    # LED 초기화
    bot.Ctrl_WQ2812_ALL(0, 0)
    print("   LED initialized (OFF)")

    # 부저 초기화
    bot.Ctrl_BEEP_Switch(0)
    print("   Beeper initialized (OFF)")

    # 부저 테스트 (옵션)
    if BEEP_ON_START and USE_BEEP:
        bot.Ctrl_BEEP_Switch(1)
        time.sleep(0.2)
        bot.Ctrl_BEEP_Switch(0)
        print("   Beeper test completed")

    # 서보 모터 초기 위치
    bot.Ctrl_Servo(1, DEFAULT_SERVO_1)
    bot.Ctrl_Servo(2, DEFAULT_SERVO_2)
    print(
        f"   Servo motors initialized (S1:{DEFAULT_SERVO_1}deg, S2:{DEFAULT_SERVO_2}deg)"
    )

    # 모터 정지
    for i in range(4):
        bot.Ctrl_Muto(i, 0)
    print("   Motors stopped and initialized")
    print("=" * 60 + "\n")


# Raspbot 및 카메라 초기화 실행
bot = initialize_raspbot()

try:
    cap = initialize_camera()
except Exception as e:
    del bot
    sys.exit(1)

setup_initial_hardware_state(bot)

# ════════════════════════════════════════════════════════
# STEP 4: Setup Trackbars and Windows
# ════════════════════════════════════════════════════════
print("=" * 60)
print("  STEP 4: Setting up Trackbars and Windows...")
print("=" * 60)


def nothing(x):
    """트랙바 콜백 함수 (비어있음)"""
    pass


# 윈도우 생성 (크기 조절 가능)
cv2.namedWindow("Camera Settings", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Camera Settings", 500, 950)

cv2.namedWindow("1_Frame", cv2.WINDOW_NORMAL)
cv2.namedWindow("2_frame_transformed", cv2.WINDOW_NORMAL)
cv2.namedWindow("3_gray_frame", cv2.WINDOW_NORMAL)
cv2.namedWindow("4_Processed Frame", cv2.WINDOW_NORMAL)

# ────────────────────────────────────────────────────────
# 서보 모터 트랙바
# ────────────────────────────────────────────────────────
cv2.createTrackbar("Servo_1_Angle", "Camera Settings", DEFAULT_SERVO_1, 180, nothing)
cv2.createTrackbar("Servo_2_Angle", "Camera Settings", DEFAULT_SERVO_2, 110, nothing)

# ────────────────────────────────────────────────────────
# ROI 영역 트랙바 (0~1000 비율 → 실제 픽셀로 변환)
# ────────────────────────────────────────────────────────
cv2.createTrackbar("ROI_Top_Y", "Camera Settings", 695, 1000, nothing)
cv2.createTrackbar("ROI_Bottom_Y", "Camera Settings", 812, 1000, nothing)

# ────────────────────────────────────────────────────────
# 방향 결정 임계값 트랙바
# ────────────────────────────────────────────────────────
cv2.createTrackbar(
    "Direction_Threshold",
    "Camera Settings",
    DEFAULT_DIRECTION_THRESHOLD,
    500000,
    nothing,
)
cv2.createTrackbar(
    "Up_Threshold", "Camera Settings", DEFAULT_UP_THRESHOLD, 500000, nothing
)

# ────────────────────────────────────────────────────────
# 카메라 설정 트랙바
# ────────────────────────────────────────────────────────
cv2.createTrackbar("Brightness", "Camera Settings", DEFAULT_BRIGHTNESS, 100, nothing)
cv2.createTrackbar("Contrast", "Camera Settings", DEFAULT_CONTRAST, 100, nothing)
cv2.createTrackbar(
    "Detect_Value", "Camera Settings", DEFAULT_DETECT_VALUE, 150, nothing
)

# ────────────────────────────────────────────────────────
# 속도 설정 트랙바
# ────────────────────────────────────────────────────────
cv2.createTrackbar("Motor_Up_Speed", "Camera Settings", DEFAULT_SPEED_UP, 255, nothing)
cv2.createTrackbar(
    "Motor_Down_Speed", "Camera Settings", DEFAULT_SPEED_DOWN, 255, nothing
)

# ────────────────────────────────────────────────────────
# RGB 가중치 트랙바 (빛 반사 필터링)
# ────────────────────────────────────────────────────────
cv2.createTrackbar("R_weight", "Camera Settings", DEFAULT_R_WEIGHT, 100, nothing)
cv2.createTrackbar("G_weight", "Camera Settings", DEFAULT_G_WEIGHT, 100, nothing)
cv2.createTrackbar("B_weight", "Camera Settings", DEFAULT_B_WEIGHT, 100, nothing)

# ────────────────────────────────────────────────────────
# 추가 카메라 설정 트랙바
# ────────────────────────────────────────────────────────
cv2.createTrackbar("Saturation", "Camera Settings", 50, 100, nothing)
cv2.createTrackbar("Gain", "Camera Settings", 0, 100, nothing)

print("Trackbars and windows configured successfully")
print("   RGB weight trackbars added for light reflection filtering\n")

# ════════════════════════════════════════════════════════
# STEP 5: Define Image Processing Functions
# ════════════════════════════════════════════════════════
print("=" * 60)
print("  STEP 5: Defining Image Processing Functions...")
print("=" * 60)


def calculate_roi_points(actual_w, actual_h, roi_top_y, roi_bottom_y):
    """
    ROI (관심 영역) 포인트 계산

    트랙바 값(0~1000)을 실제 픽셀 좌표로 변환

    Args:
        actual_w, actual_h: 실제 해상도
        roi_top_y: ROI 상단 Y (0~1000 비율)
        roi_bottom_y: ROI 하단 Y (0~1000 비율)

    Returns:
        pts_src: 원근 변환용 소스 포인트
        top_y, bottom_y: 실제 픽셀 좌표
    """
    # 비율 → 픽셀 변환
    top_y = int(roi_top_y * actual_h / 1000)
    bottom_y = int(roi_bottom_y * actual_h / 1000)

    # 범위 제한
    top_y = max(0, min(top_y, actual_h - 1))
    bottom_y = max(0, min(bottom_y, actual_h - 1))

    # 최소 50픽셀 높이 보장
    if top_y >= bottom_y:
        top_y = max(0, bottom_y - 50)

    margin = 10  # 좌우 여백

    # 사다리꼴 영역: [좌하, 우하, 우상, 좌상]
    pts_src = np.float32(
        [
            [margin, bottom_y],  # 좌하
            [actual_w - margin, bottom_y],  # 우하
            [actual_w - margin, top_y],  # 우상
            [margin, top_y],  # 좌상
        ]
    )

    return pts_src, top_y, bottom_y


def apply_roi_visualization(frame, pts_src, actual_w, actual_h, top_y, bottom_y):
    """ROI 영역 시각화 (원본 프레임에 녹색 사각형 표시)"""
    pts = pts_src.reshape((-1, 1, 2)).astype(np.int32)
    frame_with_rect = cv2.polylines(
        frame.copy(), [pts], isClosed=True, color=(0, 255, 0), thickness=2
    )

    # 해상도 및 ROI 정보 표시
    cv2.putText(
        frame_with_rect,
        f"Resolution: {actual_w}x{actual_h}",
        (10, 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 255),
        2,
    )
    cv2.putText(
        frame_with_rect,
        f"ROI Top: {top_y} / Bottom: {bottom_y}",
        (10, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 255),
        2,
    )

    return frame_with_rect


def apply_perspective_transform(frame, pts_src, target_w=320, target_h=240):
    """
    원근 변환 적용 (Bird's Eye View)

    사다리꼴 ROI 영역 → 직사각형 변환
    """
    pts_dst = np.float32([[0, target_h], [target_w, target_h], [target_w, 0], [0, 0]])
    mat_affine = cv2.getPerspectiveTransform(pts_src, pts_dst)
    frame_transformed = cv2.warpPerspective(frame, mat_affine, (target_w, target_h))

    return frame_transformed


def weighted_gray(image, r_weight, g_weight, b_weight):
    """
    RGB 가중치 기반 그레이스케일 변환 (빛 반사 필터링)

    목적:
        도로 검정색 표면의 빛 반사로 인한 오검출 방지
        RGB 채널별 가중치를 조정하여 최적의 도로선 감지

    Args:
        image: BGR 컬러 이미지
        r_weight: 빨강 채널 가중치 (0~100)
        g_weight: 초록 채널 가중치 (0~100)
        b_weight: 파랑 채널 가중치 (0~100)

    Returns:
        그레이스케일 이미지 (단일 채널)

    권장 설정:
        밝은 환경 (빛 반사): R↓(30), G=중간(40), B↑(60-80)
        어두운 환경: R↑(60), G=중간(40), B↓(30)

    원리:
        - 파랑 채널(B)은 빛 반사에 덜 민감
        - 빨강 채널(R)은 빛 반사에 민감
        - B 가중치↑ → 빛 반사 영역이 상대적으로 어둡게 처리
    """
    # 가중치 정규화 (0~100 → 0~1)
    r_weight /= 100.0
    g_weight /= 100.0
    b_weight /= 100.0

    # OpenCV BGR 순서: [:,:,0]=B, [:,:,1]=G, [:,:,2]=R
    weighted_gray_frame = cv2.addWeighted(
        cv2.addWeighted(image[:, :, 2], r_weight, image[:, :, 1], g_weight, 0),
        1.0,
        image[:, :, 0],
        b_weight,
        0,
    )

    return weighted_gray_frame


def detect_road_lines(color_frame, gray_frame, detect_value):
    """
    도로선 감지 (빨간색 + 엷은 회색)

    처리 방식:
    1. HSV 변환하여 빨간색 범위 감지
    2. RGB 가중치 기반 그레이스케일로 회색/흰색 감지
    3. 두 마스크 결합
    4. 노이즈 제거 (모폴로지 연산)

    결과 해석:
    - 빨간색/회색 도로선: 255 (흰색)
    - 검정색 도로/장애물: 0 (검정)

    히스토그램 해석:
    - 합이 작을수록 = 검정 도로가 많음 = 주행 가능
    - 합이 클수록 = 도로선이 많음 = 경계/막힘
    """
    # 1. HSV 변환 (빨간색 감지를 위해)
    hsv_frame = cv2.cvtColor(color_frame, cv2.COLOR_BGR2HSV)

    # 빨간색 범위 1: Hue 0~10 (주황색 방향)
    lower_red1 = np.array([0, 70, 50])
    upper_red1 = np.array([10, 255, 255])
    mask_red1 = cv2.inRange(hsv_frame, lower_red1, upper_red1)

    # 빨간색 범위 2: Hue 170~180 (보라색 방향)
    lower_red2 = np.array([170, 70, 50])
    upper_red2 = np.array([180, 255, 255])
    mask_red2 = cv2.inRange(hsv_frame, lower_red2, upper_red2)

    # 두 빨간색 마스크 결합
    mask_red = cv2.bitwise_or(mask_red1, mask_red2)

    # 2. 엷은 회색/흰색 감지 (RGB 가중치 기반 그레이스케일 사용)
    threshold_gray = max(detect_value - 30, 80)
    _, mask_gray = cv2.threshold(gray_frame, threshold_gray, 255, cv2.THRESH_BINARY)

    # 너무 어두운 부분(검정 도로)은 제외 (50 이하는 확실한 검정 도로)
    dark_threshold = 50
    _, mask_dark = cv2.threshold(gray_frame, dark_threshold, 255, cv2.THRESH_BINARY)
    mask_gray = cv2.bitwise_and(mask_gray, mask_dark)

    # 3. 빨간색과 회색 마스크 결합
    mask_lines = cv2.bitwise_or(mask_red, mask_gray)

    # 4. 노이즈 제거 (모폴로지 연산)
    kernel = np.ones((3, 3), np.uint8)
    mask_lines = cv2.morphologyEx(
        mask_lines, cv2.MORPH_CLOSE, kernel
    )  # 작은 구멍 메우기
    mask_lines = cv2.morphologyEx(
        mask_lines, cv2.MORPH_OPEN, kernel
    )  # 작은 노이즈 제거

    return mask_lines


def visualize_direction_on_frame(
    binary_frame, direction, left_sum, center_sum, right_sum, rgb_weights
):
    """
    프레임에 방향 정보 시각화 (3등분 방식 + RGB 가중치 표시)

    시각화 요소:
    - 방향 표시 (DIR: LEFT/UP/RIGHT)
    - 히스토그램 합계 (작을수록 도로 많음)
    - 3등분 영역 구분선 및 라벨
    - RGB 가중치 표시
    """
    # 컬러 이미지로 변환
    frame_color = cv2.cvtColor(binary_frame, cv2.COLOR_GRAY2BGR)
    h, w = frame_color.shape[:2]

    # 방향 텍스트 배경 (반투명 검정)
    overlay = frame_color.copy()
    cv2.rectangle(overlay, (0, 0), (w, 110), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, frame_color, 0.3, 0, frame_color)

    # 방향 텍스트 표시
    direction_text = f"DIR: {direction}"
    direction_color = (0, 255, 0) if direction == "UP" else (0, 255, 255)
    cv2.putText(
        frame_color,
        direction_text,
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        direction_color,
        2,
    )

    # 히스토그램 값 표시
    hist_text = f"L:{left_sum:7d} C:{center_sum:7d} R:{right_sum:7d}"
    cv2.putText(
        frame_color,
        hist_text,
        (10, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (255, 255, 255),
        1,
    )

    # 비율 표시 (낮을수록 주행 가능)
    max_possible = h * 255
    left_ratio = left_sum / (max_possible / 3)
    center_ratio = center_sum / (max_possible / 3)
    right_ratio = right_sum / (max_possible / 3)

    ratio_text = (
        f"Ratio(Low=OK) - L:{left_ratio:.2f} C:{center_ratio:.2f} R:{right_ratio:.2f}"
    )
    cv2.putText(
        frame_color,
        ratio_text,
        (10, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.4,
        (200, 200, 200),
        1,
    )

    # RGB 가중치 표시
    r_w, g_w, b_w = rgb_weights
    rgb_text = f"RGB Filter: R:{r_w} G:{g_w} B:{b_w}"
    cv2.putText(
        frame_color,
        rgb_text,
        (10, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.35,
        (150, 255, 255),
        1,
    )

    # 3등분 구분선 표시 (파란색)
    left_line = w // 3
    right_line = 2 * w // 3
    cv2.line(frame_color, (left_line, 0), (left_line, h), (255, 0, 0), 2)
    cv2.line(frame_color, (right_line, 0), (right_line, h), (255, 0, 0), 2)

    # LEFT/CENTER/RIGHT 라벨 (하단)
    label_y = h - 10
    cv2.putText(
        frame_color,
        "LEFT",
        (w // 6 - 20, label_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 0),
        2,
    )
    cv2.putText(
        frame_color,
        "CENTER",
        (w // 2 - 35, label_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 0),
        2,
    )
    cv2.putText(
        frame_color,
        "RIGHT",
        (5 * w // 6 - 25, label_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 0),
        2,
    )

    return frame_color


def process_frame(
    frame, detect_value, roi_top_y, roi_bottom_y, r_weight, g_weight, b_weight
):
    """
    프레임 처리 및 도로선 검출 메인 함수

    처리 단계:
    1. 실제 해상도 확인 및 ROI 계산
    2. ROI 영역 시각화
    3. 원근 변환 적용 (Bird's Eye View)
    4. RGB 가중치 기반 그레이스케일 변환
    5. 도로선 감지 (빨간색 + 엷은 회색)

    Returns:
        binary_frame: 이진화된 도로선 마스크
    """
    # 1. 실제 해상도 확인 및 ROI 계산
    actual_h, actual_w = frame.shape[:2]
    pts_src, top_y, bottom_y = calculate_roi_points(
        actual_w, actual_h, roi_top_y, roi_bottom_y
    )

    # 2. ROI 영역 시각화
    frame_with_rect = apply_roi_visualization(
        frame, pts_src, actual_w, actual_h, top_y, bottom_y
    )
    cv2.imshow("1_Frame", frame_with_rect)

    # 3. 원근 변환 적용
    frame_transformed = apply_perspective_transform(frame, pts_src)
    cv2.imshow("2_frame_transformed", frame_transformed)

    # 4. RGB 가중치 기반 그레이스케일 변환
    gray_frame = weighted_gray(frame_transformed, r_weight, g_weight, b_weight)
    cv2.imshow("3_gray_frame", gray_frame)

    # 5. 도로선 감지 (빨간색 + 엷은 회색)
    binary_frame = detect_road_lines(frame_transformed, gray_frame, detect_value)
    cv2.imshow("4_Processed Frame", binary_frame)

    return binary_frame


print("Image processing functions defined successfully")
print("   RGB weighted grayscale conversion added\n")

# ════════════════════════════════════════════════════════
# STEP 6: Define Car Control Functions
# ════════════════════════════════════════════════════════
print("=" * 60)
print("  STEP 6: Defining Car Control Functions...")
print("=" * 60)


def set_motor_speeds(motor_0, motor_1, motor_2, motor_3):
    """
    모터 속도 개별 설정

    모터 배치:
        M0: 왼쪽 앞바퀴
        M1: 왼쪽 뒷바퀴
        M2: 오른쪽 앞바퀴
        M3: 오른쪽 뒷바퀴

    motor_enabled가 False이면 모든 모터 정지 (SPACE 키로 토글)
    """
    if not motor_enabled:
        bot.Ctrl_Muto(0, 0)
        bot.Ctrl_Muto(1, 0)
        bot.Ctrl_Muto(2, 0)
        bot.Ctrl_Muto(3, 0)
        return

    bot.Ctrl_Muto(0, motor_0)
    bot.Ctrl_Muto(1, motor_1)
    bot.Ctrl_Muto(2, motor_2)
    bot.Ctrl_Muto(3, motor_3)


def car_run(speed_left, speed_right):
    """전진: 4개 모터 모두 같은 방향으로 회전"""
    set_motor_speeds(speed_left, speed_left, speed_right, speed_right)


def car_stop():
    """정지: 모든 모터 속도 0"""
    set_motor_speeds(0, 0, 0, 0)


def car_left(speed_left, speed_right):
    """
    좌회전 (제자리 회전)

    동작: 왼쪽 모터 후진, 오른쪽 모터 전진
    결과: 제자리에서 왼쪽으로 회전
    """
    set_motor_speeds(-speed_left, -speed_left, speed_right, speed_right)


def car_right(speed_left, speed_right):
    """
    우회전 (제자리 회전)

    동작: 왼쪽 모터 전진, 오른쪽 모터 후진
    결과: 제자리에서 오른쪽으로 회전
    """
    set_motor_speeds(speed_left, speed_left, -speed_right, -speed_right)


def set_led_effect(mode):
    """LED 효과 설정 (mode: 1=초록, 2=파랑, 3=노랑, ...)"""
    if not USE_LED_EFFECTS:
        return
    bot.Ctrl_WQ2812_ALL(1, mode)


def log_car_action(action_name, speed=None):
    """차량 동작 로그 출력"""
    if not DEBUG_MODE:
        return
    if speed:
        print(f"   {action_name} - Speed: {speed}")
    else:
        print(f"   {action_name}")


def control_car(direction, up_speed, down_speed):
    """
    차량 제어 메인 함수

    방향에 따른 모터 및 LED 제어

    Args:
        direction: "UP", "LEFT", "RIGHT"
        up_speed: 주 속도
        down_speed: 감속 측 속도
    """
    if direction == "UP":
        car_run(up_speed, up_speed)
        log_car_action("FORWARD", up_speed)
        set_led_effect(1)  # 초록색

    elif direction == "LEFT":
        car_left(down_speed, up_speed)
        log_car_action("TURN LEFT")
        set_led_effect(3)  # 노란색

    elif direction == "RIGHT":
        car_right(up_speed, down_speed)
        log_car_action("TURN RIGHT")
        set_led_effect(3)  # 노란색


print("Car control functions defined successfully\n")

# ════════════════════════════════════════════════════════
# STEP 7: Define Servo Motor Control Functions
# ════════════════════════════════════════════════════════
print("=" * 60)
print("  STEP 7: Defining Servo Motor Control Functions...")
print("=" * 60)


def rotate_servo(servo_id, angle):
    """
    서보 모터 회전

    Args:
        servo_id: 1 (좌우), 2 (상하)
        angle: 각도 (Servo 1: 0~180, Servo 2: 0~110)

    ⚠️ Servo 2는 하드웨어 제한으로 최대 110도
    """
    if servo_id == 2 and angle > 110:
        angle = 110
    bot.Ctrl_Servo(servo_id, angle)


print("Servo motor control functions defined successfully\n")

# ════════════════════════════════════════════════════════
# STEP 8: Define Direction Decision Functions
# ════════════════════════════════════════════════════════
print("=" * 60)
print("  STEP 8: Defining Direction Decision Functions...")
print("=" * 60)


def analyze_histogram(histogram):
    """
    히스토그램 3등분 분석

    분할 방식:
    - LEFT:   0% ~ 33% (왼쪽 1/3)
    - CENTER: 33% ~ 66% (중앙 1/3)
    - RIGHT:  66% ~ 100% (오른쪽 1/3)

    이진화 값 해석:
    - 검정색 도로 = 0 (주행 가능 영역)
    - 빨간색/회색 도로선 = 255 (경계/막힘)

    히스토그램 합산 해석:
    - 합이 작을수록 = 검정 도로가 많음 = 주행 가능 영역
    - 합이 클수록 = 도로선이 많음 = 경계/막힘

    Returns:
        left_sum, center_sum, right_sum: 각 영역의 히스토그램 합
        left_ratio, center_ratio, right_ratio: 각 영역의 비율 (0~1)
    """
    length = len(histogram)

    # 3등분 경계
    left_end = length // 3
    right_start = 2 * length // 3

    # 각 영역의 히스토그램 합계
    left_sum = int(np.sum(histogram[:left_end]))
    center_sum = int(np.sum(histogram[left_end:right_start]))
    right_sum = int(np.sum(histogram[right_start:]))

    # 정규화 (0~1 범위로 비율 계산)
    left_ratio = left_sum / (left_end * 255) if left_end > 0 else 0
    center_ratio = (
        center_sum / ((right_start - left_end) * 255)
        if (right_start - left_end) > 0
        else 0
    )
    right_ratio = (
        right_sum / ((length - right_start) * 255) if (length - right_start) > 0 else 0
    )

    return left_sum, center_sum, right_sum, left_ratio, center_ratio, right_ratio


def decide_direction(
    histogram, direction_threshold, up_threshold, detect_value, roi_top_y, roi_bottom_y
):
    """
    히스토그램 기반 방향 결정 (3등분 분석)

    ═══════════════════════════════════════════════════════
    처리 단계 (우선순위 순):
    ═══════════════════════════════════════════════════════
    1. 히스토그램 3등분 분석 (LEFT, CENTER, RIGHT)
    2. 좌우 차이 체크 (최우선) ⭐
       - abs(right - left) > direction_threshold → 회전
    3. 중앙 클리어 체크
       - center_ratio < CENTER_CLEAR_THRESHOLD → 직진
    4. 막다른 골목 감지
       - (left + right) / 2 < up_threshold → 랜덤 선택
    5. 기본 동작 → 직진

    ═══════════════════════════════════════════════════════
    핵심 원리 (도로선 감지 모드):
    ═══════════════════════════════════════════════════════
    - 합이 작음 = 검정 도로 많음 = 주행 가능 (도로선 적음)
    - 합이 큼 = 도로선 많음 = 경계/막힘 (빨간색/회색선)

    로직:
    - right_sum > left_sum → 오른쪽에 도로선 → 왼쪽이 주행 가능 → LEFT 회전
    - left_sum > right_sum → 왼쪽에 도로선 → 오른쪽이 주행 가능 → RIGHT 회전

    Returns:
        tuple: (direction, left_sum, center_sum, right_sum)
    """
    # 1. 히스토그램 3등분 분석
    left_sum, center_sum, right_sum, left_ratio, center_ratio, right_ratio = (
        analyze_histogram(histogram)
    )

    if DEBUG_MODE:
        print(f"\n   Histogram Analysis (Road Line Detection Mode):")
        print(
            f"      LEFT:   {left_sum:7d} (ratio: {left_ratio:.3f}) - Lower = More drivable"
        )
        print(
            f"      CENTER: {center_sum:7d} (ratio: {center_ratio:.3f}) - Lower = More drivable"
        )
        print(
            f"      RIGHT:  {right_sum:7d} (ratio: {right_ratio:.3f}) - Lower = More drivable"
        )
        print(
            f"      L-R Diff: {right_sum - left_sum:7d} | Threshold: {direction_threshold}"
        )

    # 2. 좌우 차이 체크 (최우선) ⭐
    # right_sum이 크면 = 오른쪽에 도로선 많음 = 왼쪽으로 회전
    # left_sum이 크면 = 왼쪽에 도로선 많음 = 오른쪽으로 회전
    if abs(right_sum - left_sum) > direction_threshold:
        if right_sum > left_sum:
            direction = "LEFT"  # 오른쪽에 도로선 → 왼쪽이 주행 가능
        else:
            direction = "RIGHT"  # 왼쪽에 도로선 → 오른쪽이 주행 가능

        if DEBUG_MODE:
            print(f"   Decision: Turn {direction} (less road lines on that side)")

        return direction, left_sum, center_sum, right_sum

    # 3. 중앙 클리어 체크
    # center_ratio가 낮으면 = 중앙에 검정 도로 많음 = 직진 가능
    if center_ratio < CENTER_CLEAR_THRESHOLD:
        if DEBUG_MODE:
            print(
                f"   Center is CLEAR (ratio: {center_ratio:.3f} < {CENTER_CLEAR_THRESHOLD})"
            )
            print("   Decision: Go STRAIGHT (center has minimal road lines)")

        return "UP", left_sum, center_sum, right_sum

    # 4. 막다른 골목 감지
    # 조건: 좌우 영역의 평균 합이 up_threshold보다 작으면 막힘
    left_right_avg = (left_sum + right_sum) // 2

    if DEBUG_MODE:
        print(f"      L-R Average: {left_right_avg:7d} | Up Threshold: {up_threshold}")

    if left_right_avg < up_threshold:
        if DEBUG_MODE:
            print("\n   " + "=" * 50)
            print("   WARNING: Dead End Detected!")
            print("   " + "=" * 50)
            print(f"   L-R Average: {left_right_avg} < Threshold: {up_threshold}")
            print("   Action: Random direction selection")

        # 부저 알림 (3회: 삐-삐-삐)
        if USE_BEEP:
            for _ in range(3):
                bot.Ctrl_BEEP_Switch(1)
                time.sleep(0.15)
                bot.Ctrl_BEEP_Switch(0)
                time.sleep(0.1)

        # 랜덤 방향 선택
        random_direction = random.choice(["LEFT", "RIGHT"])

        if DEBUG_MODE:
            print(f"   Random Direction Selected: {random_direction}")
            print("   " + "=" * 50 + "\n")

        return random_direction, left_sum, center_sum, right_sum

    # 5. 기본: 직진
    if DEBUG_MODE:
        print("   Decision: Go straight (default)")

    return "UP", left_sum, center_sum, right_sum


print("Direction decision functions defined successfully\n")

# ════════════════════════════════════════════════════════
# Define Helper Functions
# ════════════════════════════════════════════════════════
print("=" * 60)
print("  Defining Helper Functions...")
print("=" * 60)


def handle_keyboard_input():
    """
    키보드 입력 처리

    Returns:
        str: "EXIT" (종료), "CONTINUE" (계속)

    키 매핑:
        ESC: 종료
        SPACE: 모터 ON/OFF 토글
        'l': LED 토글
        'b': 부저 토글
    """
    global motor_enabled, led_state, beep_state

    key = cv2.waitKey(30) & 0xFF

    # ESC: 종료
    if key == 27:
        print("\nExiting...")
        return "EXIT"

    # SPACE: 모터 토글
    elif key == 32:
        motor_enabled = not motor_enabled
        if motor_enabled:
            print("\n" + "=" * 50)
            print("   Motor: ENABLED")
            print("=" * 50)
        else:
            print("\n" + "=" * 50)
            print("   Motor: DISABLED (Camera continues)")
            print("=" * 50)
            car_stop()  # 즉시 모터 정지

    # 'l': LED 토글
    elif key == ord("l"):
        led_state = not led_state
        if led_state:
            bot.Ctrl_WQ2812_ALL(1, 2)  # 파란색
            print("   LED: ON")
        else:
            bot.Ctrl_WQ2812_ALL(0, 0)
            print("   LED: OFF")

    # 'b': 부저 토글
    elif key == ord("b"):
        beep_state = not beep_state
        bot.Ctrl_BEEP_Switch(1 if beep_state else 0)
        print(f"   Beeper: {'ON' if beep_state else 'OFF'}")

    return "CONTINUE"


def read_trackbar_values():
    """트랙바 값 일괄 읽기"""
    values = {
        "brightness": cv2.getTrackbarPos("Brightness", "Camera Settings"),
        "contrast": cv2.getTrackbarPos("Contrast", "Camera Settings"),
        "saturation": cv2.getTrackbarPos("Saturation", "Camera Settings"),
        "gain": cv2.getTrackbarPos("Gain", "Camera Settings"),
        "detect_value": cv2.getTrackbarPos("Detect_Value", "Camera Settings"),
        "motor_up_speed": cv2.getTrackbarPos("Motor_Up_Speed", "Camera Settings"),
        "motor_down_speed": cv2.getTrackbarPos("Motor_Down_Speed", "Camera Settings"),
        "servo_1_angle": cv2.getTrackbarPos("Servo_1_Angle", "Camera Settings"),
        "servo_2_angle": cv2.getTrackbarPos("Servo_2_Angle", "Camera Settings"),
        "roi_top_y": cv2.getTrackbarPos("ROI_Top_Y", "Camera Settings"),
        "roi_bottom_y": cv2.getTrackbarPos("ROI_Bottom_Y", "Camera Settings"),
        "direction_threshold": cv2.getTrackbarPos(
            "Direction_Threshold", "Camera Settings"
        ),
        "up_threshold": cv2.getTrackbarPos("Up_Threshold", "Camera Settings"),
        # RGB 가중치
        "r_weight": cv2.getTrackbarPos("R_weight", "Camera Settings"),
        "g_weight": cv2.getTrackbarPos("G_weight", "Camera Settings"),
        "b_weight": cv2.getTrackbarPos("B_weight", "Camera Settings"),
    }
    return values


def apply_camera_settings(cap, brightness, contrast, saturation, gain):
    """카메라 속성 설정"""
    cap.set(cv2.CAP_PROP_BRIGHTNESS, brightness)
    cap.set(cv2.CAP_PROP_CONTRAST, contrast)
    cap.set(cv2.CAP_PROP_SATURATION, saturation)
    cap.set(cv2.CAP_PROP_GAIN, gain)


def cleanup_and_exit(bot, cap):
    """정리 및 종료"""
    print("\n" + "=" * 60)
    print("  STEP 10: Cleaning up and Exiting...")
    print("=" * 60)

    car_stop()
    print("   Motors stopped")

    # LED 끄기
    bot.Ctrl_WQ2812_ALL(0, 0)
    print("   LED turned off")

    # 부저 끄기
    bot.Ctrl_BEEP_Switch(0)
    print("   Beeper turned off")

    # 서보 초기 위치
    bot.Ctrl_Servo(1, 90)
    bot.Ctrl_Servo(2, 25)
    print("   Servo motors returned to initial position")

    cap.release()
    cv2.destroyAllWindows()
    print("   Camera released")

    del bot
    print("   Raspbot object deleted")

    print("\nCleanup completed successfully!")
    print("=" * 60)


print("Helper functions defined successfully\n")

# ════════════════════════════════════════════════════════
# STEP 9: Start Main Loop
# ════════════════════════════════════════════════════════
print("=" * 60)
print("  STEP 9: Starting Main Loop")
print("=" * 60)
print("\nRaspbot v2 Autopilot Started!")
print("\n" + "=" * 60)
print("  Keyboard Controls:")
print("=" * 60)
print("  ESC   : Exit")
print("  SPACE : Motor ON/OFF toggle (Camera continues)")
print("  'l'   : Toggle LED")
print("  'b'   : Toggle Beeper")
print("=" * 60)
print("\n  RGB Filter Feature:")
print("  Bright environment: R down(30), G mid(40), B up(60-80)")
print("  Dark environment: R up(60), G mid(40), B down(30)")
print("=" * 60 + "\n")

start_time = time.time()
led_state = LED_ON_START
beep_state = False

try:
    while True:
        frame_count += 1

        # 프레임 상태 표시 (10프레임마다)
        if frame_count % 10 == 0:
            print("\n" + "-" * 50)
            motor_status = "ON" if motor_enabled else "OFF"
            led_status = "ON" if led_state else "OFF"
            beep_status = "ON" if beep_state else "OFF"
            print(
                f"Frame: {frame_count} | Motor: {motor_status} | LED: {led_status} | Beep: {beep_status}"
            )
            print("-" * 50)

        # 트랙바 값 읽기
        params = read_trackbar_values()

        # 카메라 속성 설정
        apply_camera_settings(
            cap,
            params["brightness"],
            params["contrast"],
            params["saturation"],
            params["gain"],
        )

        # 프레임 읽기
        ret, frame = cap.read()
        if not ret:
            print("Cannot read frame from camera.")
            break

        # 서보 모터 각도 조절
        rotate_servo(1, params["servo_1_angle"])
        rotate_servo(2, params["servo_2_angle"])

        # RGB 가중치 적용하여 프레임 처리
        processed_frame = process_frame(
            frame,
            params["detect_value"],
            params["roi_top_y"],
            params["roi_bottom_y"],
            params["r_weight"],
            params["g_weight"],
            params["b_weight"],
        )
        histogram = np.sum(processed_frame, axis=0)

        # 방향 결정 및 제어
        if DEBUG_MODE and frame_count % 10 == 0:
            print(f"\n--- Frame {frame_count} ---")
            print(
                f"RGB Weights: R={params['r_weight']}, G={params['g_weight']}, B={params['b_weight']}"
            )

        direction, hist_left, hist_center, hist_right = decide_direction(
            histogram,
            params["direction_threshold"],
            params["up_threshold"],
            params["detect_value"],
            params["roi_top_y"],
            params["roi_bottom_y"],
        )

        # 방향 정보 시각화 (RGB 가중치 포함)
        rgb_weights = (params["r_weight"], params["g_weight"], params["b_weight"])
        processed_frame_visual = visualize_direction_on_frame(
            processed_frame, direction, hist_left, hist_center, hist_right, rgb_weights
        )
        cv2.imshow("4_Processed Frame", processed_frame_visual)

        # 차량 제어
        control_car(direction, params["motor_up_speed"], params["motor_down_speed"])

        # FPS 계산 (10프레임마다)
        if frame_count % 10 == 0:
            elapsed = time.time() - start_time
            fps = 10 / elapsed
            if DEBUG_MODE:
                print(f"   FPS: {fps:.1f}")
            start_time = time.time()

        # 키보드 입력 처리
        result = handle_keyboard_input()
        if result == "EXIT":
            break

        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nInterrupted by user")
except Exception as e:
    print(f"\nError occurred: {e}")
    import traceback

    traceback.print_exc()

# ════════════════════════════════════════════════════════
# STEP 10: Cleanup and Exit
# ════════════════════════════════════════════════════════
finally:
    cleanup_and_exit(bot, cap)
