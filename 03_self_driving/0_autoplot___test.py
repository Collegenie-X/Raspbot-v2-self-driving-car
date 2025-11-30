#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspbot v2 자율주행 테스트 코드 (기본 기능)
서보 모터 포함 기본 라인 트레이싱 테스트

Copyright (C): 2015-2024, Shenzhen Yahboom Tech
Modified: 2025-11-30

═══════════════════════════════════════════════════════════
주요 특징:
═══════════════════════════════════════════════════════════
- 서보 모터 제어 포함 (카메라 각도 조절)
- 라인 트레이싱 기본 기능 (빨간색/회색 도로선 감지)
- 히스토그램 3등분 분석 기반 방향 결정
- 단계별 주석으로 실행 흐름 명확화

═══════════════════════════════════════════════════════════
교육생 실습 과제:
═══════════════════════════════════════════════════════════
- 막다른 길 감지 알고리즘 구현
- 서보 모터를 활용한 대체 경로 탐색 기능 추가

═══════════════════════════════════════════════════════════
실행 단계:
═══════════════════════════════════════════════════════════
1단계: 라이브러리 및 모듈 import
2단계: 하드웨어 초기화 (Raspbot, 카메라, 서보)
3단계: 트랙바 및 윈도우 설정
4단계: 이미지 처리 함수 정의
5단계: 차량 제어 함수 정의
6단계: 서보 모터 제어 함수 정의
7단계: 방향 결정 함수 정의
8단계: 메인 루프 실행
9단계: 정리 및 종료
"""

import sys
import os

# ============================
# 1단계: 라이브러리 및 모듈 import
# ============================
print("=" * 50)
print("  STEP 1: Loading Libraries...")
print("=" * 50)

# Raspbot 라이브러리 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib", "raspbot"))

import cv2
import numpy as np
import random
import time
from Raspbot_Lib import Raspbot

print("Libraries loaded successfully\n")

# ============================
# 사용자 설정 영역
# ============================
print("=" * 50)
print("  STEP 2: Loading Configuration...")
print("=" * 50)

# 기본 속도 설정 (-255 ~ 255)
DEFAULT_SPEED_UP = 40
DEFAULT_SPEED_DOWN = 30

# 라인 검출 설정
DEFAULT_DETECT_VALUE = 120
DEFAULT_BRIGHTNESS = 0
DEFAULT_CONTRAST = 0

# 방향 판단 임계값
DEFAULT_DIRECTION_THRESHOLD = 35000
DEFAULT_UP_THRESHOLD = 220000

# 서보 모터 각도
DEFAULT_SERVO_1 = 70  # 좌우 각도 (0~180)
DEFAULT_SERVO_2 = 10  # 상하 각도 (0~110)

# 디버그 모드
DEBUG_MODE = True

# LED 효과 사용
USE_LED_EFFECTS = True
LED_ON_START = True

# 부저 사용
USE_BEEP = True
BEEP_ON_START = True
BEEP_ON_TURN = False

print("Configuration loaded successfully\n")

# ============================
# 2단계: 하드웨어 초기화
# ============================
print("=" * 50)
print("  STEP 3: Initializing Hardware...")
print("=" * 50)


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
        print("\nInitializing camera...")

        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_BRIGHTNESS, DEFAULT_BRIGHTNESS)
        cap.set(cv2.CAP_PROP_CONTRAST, DEFAULT_CONTRAST)
        cap.set(cv2.CAP_PROP_SATURATION, 50)
        cap.set(cv2.CAP_PROP_EXPOSURE, 100)

        ret, frame = cap.read()
        if not ret or frame is None:
            raise Exception("Cannot read frame from camera")

        actual_height, actual_width = frame.shape[:2]
        print(f"USB camera initialized successfully")
        print(f"   - Requested resolution: {width}x{height}")
        print(f"   - Actual resolution: {actual_width}x{actual_height}")

        return cap
    except Exception as e:
        print(f"\nFailed to initialize camera: {e}\n")
        raise


def setup_initial_hardware_state(bot):
    """초기 하드웨어 상태 설정"""
    # LED 초기화
    if LED_ON_START and USE_LED_EFFECTS:
        bot.Ctrl_WQ2812_ALL(1, 2)
        print("LED initialized")

    # 부저 테스트
    if BEEP_ON_START and USE_BEEP:
        bot.Ctrl_BEEP_Switch(1)
        time.sleep(0.2)
        bot.Ctrl_BEEP_Switch(0)
        print("Beeper test completed")

    # 서보 모터 초기 위치
    bot.Ctrl_Servo(1, DEFAULT_SERVO_1)
    bot.Ctrl_Servo(2, DEFAULT_SERVO_2)
    print(
        f"Servo motors initialized (S1:{DEFAULT_SERVO_1}deg, S2:{DEFAULT_SERVO_2}deg)"
    )

    # 모터 정지
    for i in range(4):
        bot.Ctrl_Muto(i, 0)
    print("Motors stopped and initialized\n")


# Raspbot 및 카메라 초기화
bot = initialize_raspbot()

try:
    cap = initialize_camera()
except Exception as e:
    del bot
    sys.exit(1)

setup_initial_hardware_state(bot)

# ============================
# 3단계: 트랙바 및 윈도우 설정
# ============================
print("=" * 50)
print("  STEP 4: Setting up Trackbars and Windows...")
print("=" * 50)


def nothing(x):
    """트랙바 콜백 함수"""
    pass


# 윈도우 생성 (크기 조절 가능)
# Camera Settings 윈도우를 먼저 생성하고 크기 설정
cv2.namedWindow("Camera Settings", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Camera Settings", 500, 800)

cv2.namedWindow("1_Frame", cv2.WINDOW_NORMAL)
cv2.namedWindow("2_frame_transformed", cv2.WINDOW_NORMAL)
cv2.namedWindow("3_gray_frame", cv2.WINDOW_NORMAL)
cv2.namedWindow("4_Processed Frame", cv2.WINDOW_NORMAL)

# 4_Processed Frame 창을 더 크게 설정
cv2.resizeWindow("4_Processed Frame", 640, 480)
cv2.resizeWindow("1_Frame", 640, 480)

# 서보 모터 트랙바
cv2.createTrackbar("Servo_1_Angle", "Camera Settings", DEFAULT_SERVO_1, 180, nothing)
cv2.createTrackbar("Servo_2_Angle", "Camera Settings", DEFAULT_SERVO_2, 110, nothing)

# 이미지 처리 트랙바 (공백 제거하여 안정성 향상)
cv2.createTrackbar("ROI_Top_Y", "Camera Settings", 871, 1000, nothing)
cv2.createTrackbar("ROI_Bottom_Y", "Camera Settings", 946, 1000, nothing)
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
cv2.createTrackbar("Brightness", "Camera Settings", DEFAULT_BRIGHTNESS, 100, nothing)
cv2.createTrackbar("Contrast", "Camera Settings", DEFAULT_CONTRAST, 100, nothing)
cv2.createTrackbar(
    "Detect_Value", "Camera Settings", DEFAULT_DETECT_VALUE, 150, nothing
)
cv2.createTrackbar("Motor_Up_Speed", "Camera Settings", DEFAULT_SPEED_UP, 255, nothing)
cv2.createTrackbar(
    "Motor_Down_Speed", "Camera Settings", DEFAULT_SPEED_DOWN, 255, nothing
)
cv2.createTrackbar("Saturation", "Camera Settings", 0, 100, nothing)
cv2.createTrackbar("Gain", "Camera Settings", 0, 100, nothing)

print("Trackbars and windows configured successfully\n")

# ============================
# 4단계: 이미지 처리 함수 정의
# ============================
print("=" * 50)
print("  STEP 5: Defining Image Processing Functions")
print("=" * 50)


def apply_roi_visualization(frame, pts_src, actual_w, actual_h, top_y, bottom_y):
    """ROI 영역 시각화"""
    pts = pts_src.reshape((-1, 1, 2)).astype(np.int32)
    frame_with_rect = cv2.polylines(
        frame.copy(), [pts], isClosed=True, color=(0, 255, 0), thickness=2
    )

    cv2.putText(
        frame_with_rect,
        f"Resolution: {actual_w}x{actual_h}",
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


def calculate_roi_points(actual_w, actual_h, roi_top_y, roi_bottom_y):
    """ROI 포인트 계산"""
    top_y = int(roi_top_y * actual_h / 1000)
    bottom_y = int(roi_bottom_y * actual_h / 1000)
    top_y = max(0, min(top_y, actual_h - 1))
    bottom_y = max(0, min(bottom_y, actual_h - 1))

    if top_y >= bottom_y:
        top_y = max(0, bottom_y - 50)

    margin = 10
    pts_src = np.float32(
        [
            [margin, bottom_y],
            [actual_w - margin, bottom_y],
            [actual_w - margin, top_y],
            [margin, top_y],
        ]
    )

    return pts_src, top_y, bottom_y


def apply_perspective_transform(frame, pts_src, target_w=320, target_h=240):
    """원근 변환 적용"""
    pts_dst = np.float32([[0, target_h], [target_w, target_h], [target_w, 0], [0, 0]])
    mat_affine = cv2.getPerspectiveTransform(pts_src, pts_dst)
    frame_transformed = cv2.warpPerspective(frame, mat_affine, (target_w, target_h))
    return frame_transformed


def detect_road_lines(color_frame, gray_frame, detect_value):
    """
    도로선 감지 (빨간색 + 엷은 회색)

    처리 방식:
    1. HSV 변환하여 빨간색 범위 감지
    2. 밝기로 엷은 회색(흰색 계열) 감지
    3. 두 마스크 결합
    4. 노이즈 제거

    결과:
    - 빨간색/회색 도로선: 255 (흰색)
    - 검정색 도로/장애물: 0 (검정)

    히스토그램 해석:
    - 합이 클수록 = 도로선이 많음 = 막힘 또는 경계
    - 합이 작을수록 = 검정 도로가 많음 = 주행 가능
    """
    # HSV 변환 (빨간색 감지를 위해)
    hsv_frame = cv2.cvtColor(color_frame, cv2.COLOR_BGR2HSV)

    # 빨간색 범위 감지 (HSV에서 빨간색은 0도 근처와 180도 근처 두 영역)
    # 빨간색 범위 1: 0-10도
    lower_red1 = np.array([0, 70, 50])
    upper_red1 = np.array([10, 255, 255])
    mask_red1 = cv2.inRange(hsv_frame, lower_red1, upper_red1)

    # 빨간색 범위 2: 170-180도
    lower_red2 = np.array([170, 70, 50])
    upper_red2 = np.array([180, 255, 255])
    mask_red2 = cv2.inRange(hsv_frame, lower_red2, upper_red2)

    # 두 빨간색 마스크 결합
    mask_red = cv2.bitwise_or(mask_red1, mask_red2)

    # 엷은 회색/흰색 감지 (밝기 기준)
    # detect_value를 기준으로 밝은 영역 감지 (범위를 더 넓게)
    # 검정색 반사 부분도 포함하기 위해 임계값을 낮춤
    threshold_gray = max(detect_value - 30, 80)  # 범위 확장
    _, mask_gray = cv2.threshold(gray_frame, threshold_gray, 255, cv2.THRESH_BINARY)

    # 너무 어두운 부분(검정 도로)은 제외
    dark_threshold = 50  # 50 이하는 확실한 검정 도로
    _, mask_dark = cv2.threshold(gray_frame, dark_threshold, 255, cv2.THRESH_BINARY)
    mask_gray = cv2.bitwise_and(mask_gray, mask_dark)

    # 빨간색과 회색 마스크 결합
    mask_lines = cv2.bitwise_or(mask_red, mask_gray)

    # 노이즈 제거
    kernel = np.ones((3, 3), np.uint8)
    mask_lines = cv2.morphologyEx(mask_lines, cv2.MORPH_CLOSE, kernel)
    mask_lines = cv2.morphologyEx(mask_lines, cv2.MORPH_OPEN, kernel)

    return mask_lines


def apply_binary_threshold(gray_frame, detect_value):
    """
    기본 이진화 (호환성을 위해 유지)
    실제로는 detect_road_lines 사용 권장
    """
    _, binary_frame = cv2.threshold(gray_frame, detect_value, 255, cv2.THRESH_BINARY)

    kernel = np.ones((5, 5), np.uint8)
    binary_frame = cv2.morphologyEx(binary_frame, cv2.MORPH_CLOSE, kernel)
    binary_frame = cv2.morphologyEx(binary_frame, cv2.MORPH_OPEN, kernel)

    return binary_frame


def visualize_direction_on_frame(
    binary_frame, direction, left_sum, center_sum, right_sum
):
    """
    프레임에 방향 정보 시각화 (3등분 방식)

    Args:
        binary_frame: 이진화된 프레임
        direction: 결정된 방향 (LEFT/UP/RIGHT)
        left_sum: 좌측 영역 히스토그램 합
        center_sum: 중앙 영역 히스토그램 합
        right_sum: 우측 영역 히스토그램 합

    시각화 요소:
    - 방향 표시 (DIR: LEFT/UP/RIGHT)
    - 히스토그램 합계 (작을수록 도로 많음)
    - 3등분 영역 구분선 및 라벨
    """
    # 컬러 이미지로 변환 (텍스트 표시를 위해)
    frame_color = cv2.cvtColor(binary_frame, cv2.COLOR_GRAY2BGR)
    h, w = frame_color.shape[:2]

    # 방향 텍스트 배경
    overlay = frame_color.copy()
    cv2.rectangle(overlay, (0, 0), (w, 90), (0, 0, 0), -1)
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

    # 비율 표시 (작을수록 주행 가능)
    height_in_frame = binary_frame.shape[0]
    max_possible = height_in_frame * 255
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

    # 도로선 감지 설명
    cv2.putText(
        frame_color,
        "White=RoadLine(Red/Gray) Black=Road",
        (10, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.35,
        (150, 150, 150),
        1,
    )

    # 3등분 구분선 표시
    left_line = w // 3
    right_line = 2 * w // 3

    # 왼쪽 구분선 (파란색)
    cv2.line(frame_color, (left_line, 0), (left_line, h), (255, 0, 0), 2)
    # 오른쪽 구분선 (파란색)
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


def process_frame(frame, detect_value, roi_top_y, roi_bottom_y):
    """
    프레임 처리 및 도로선 검출

    처리 단계:
    1. 실제 해상도 확인 및 ROI 계산
    2. ROI 영역 시각화
    3. 원근 변환 적용
    4. 그레이스케일 변환
    5. 도로선 감지 (빨간색 + 엷은 회색)
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

    # 4. 그레이스케일 변환 (참고용)
    gray_frame = cv2.cvtColor(frame_transformed, cv2.COLOR_BGR2GRAY)
    cv2.imshow("3_gray_frame", gray_frame)

    # 5. 도로선 감지 (빨간색 + 엷은 회색)
    binary_frame = detect_road_lines(frame_transformed, gray_frame, detect_value)
    cv2.imshow("4_Processed Frame", binary_frame)

    return binary_frame


print("Image processing functions defined successfully\n")

# ============================
# 5단계: 차량 제어 함수 정의
# ============================
print("=" * 50)
print("  STEP 6: Defining Car Control Functions")
print("=" * 50)


def set_motor_speeds(motor_0, motor_1, motor_2, motor_3):
    """모터 속도 설정"""
    bot.Ctrl_Muto(0, motor_0)
    bot.Ctrl_Muto(1, motor_1)
    bot.Ctrl_Muto(2, motor_2)
    bot.Ctrl_Muto(3, motor_3)


def car_run(speed_left, speed_right):
    """전진"""
    set_motor_speeds(speed_left, speed_left, speed_right, speed_right)


def car_stop():
    """정지"""
    set_motor_speeds(0, 0, 0, 0)


def car_left(speed_left, speed_right):
    """좌회전 (제자리 회전)"""
    set_motor_speeds(-speed_left, -speed_left, speed_right, speed_right)


def car_right(speed_left, speed_right):
    """우회전 (제자리 회전)"""
    set_motor_speeds(speed_left, speed_left, -speed_right, -speed_right)


def set_led_effect(mode):
    """LED 효과 설정"""
    if not USE_LED_EFFECTS:
        return
    bot.Ctrl_WQ2812_ALL(1, mode)


def log_car_action(action_name, speed=None):
    """차량 동작 로그 출력"""
    if not DEBUG_MODE:
        return
    if speed:
        print(f"{action_name} - Speed: {speed}")
    else:
        print(action_name)


def control_car(direction, up_speed, down_speed):
    """차량 제어 메인 함수"""
    if direction == "UP":
        car_run(up_speed, up_speed)
        log_car_action("FORWARD", up_speed)
        set_led_effect(1)
    elif direction == "LEFT":
        car_left(down_speed, up_speed)
        log_car_action("TURN LEFT")
        set_led_effect(3)
    elif direction == "RIGHT":
        car_right(up_speed, down_speed)
        log_car_action("TURN RIGHT")
        set_led_effect(3)


print("Car control functions defined successfully\n")

# ============================
# 6단계: 서보 모터 제어 함수 정의
# ============================
print("=" * 50)
print("  STEP 7: Defining Servo Motor Control Functions")
print("=" * 50)


def rotate_servo(servo_id, angle):
    """
    서보 모터 회전

    단계:
    1. Servo 2 각도 제한 확인 (최대 110도)
    2. 서보 모터 제어
    """
    if servo_id == 2 and angle > 110:
        angle = 110
    bot.Ctrl_Servo(servo_id, angle)


print("Servo motor control functions defined successfully\n")

# ============================
# 7단계: 방향 결정 함수 정의
# ============================
print("=" * 50)
print("  STEP 8: Defining Direction Decision Functions")
print("=" * 50)


def analyze_histogram(histogram):
    """
    히스토그램 3등분 분석

    분할 방식:
    - LEFT:   0% ~ 33% (왼쪽 1/3)
    - CENTER: 33% ~ 66% (중앙 1/3)
    - RIGHT:  66% ~ 100% (오른쪽 1/3)

    이진화 값 (도로선 감지):
    - 검정색 도로 = 0 (주행 가능 영역)
    - 빨간색/회색 도로선 = 255 (경계/막힘)

    히스토그램 합산 해석:
    - 합이 작을수록 = 검정 도로가 많음 = 주행 가능 영역
    - 합이 클수록 = 도로선이 많음 = 경계/막힘

    반비례 관계:
    - ratio가 낮을수록 = 주행 가능
    - ratio가 높을수록 = 막힘
    """
    length = len(histogram)

    # 3등분 경계
    left_end = length // 3
    right_start = 2 * length // 3

    # 각 영역의 히스토그램 합계
    left_sum = int(np.sum(histogram[:left_end]))
    center_sum = int(np.sum(histogram[left_end:right_start]))
    right_sum = int(np.sum(histogram[right_start:]))

    # 정규화 (0~1 범위로 변환하여 비율 계산)
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
    히스토그램 기반 방향 결정 (3등분 분석 - 도로선 감지)

    처리 단계:
    1. 히스토그램 3등분 분석 (LEFT, CENTER, RIGHT)
    2. 좌우 영역 비교하여 도로 방향 판단
    3. 좌우 차이가 크면 해당 방향으로 회전
    4. 막다른 길 감지 시 랜덤 방향 선택
    5. 그 외 직진

    로직 (도로선 감지 모드):
    - 합이 작음 = 검정 도로 많음 = 주행 가능 (도로선 적음)
    - 합이 큼 = 도로선 많음 = 경계/막힘 (빨간색/회색선)
    - left_sum < right_sum → 왼쪽에 도로선 적음 → LEFT 회전 가능
    - right_sum < left_sum → 오른쪽에 도로선 적음 → RIGHT 회전 가능
    - center_ratio > 0.7 → 중앙에 도로선 많음 → 막다른 길 → 랜덤 선택

    Returns:
        tuple: (direction, left_sum, center_sum, right_sum) - 방향과 히스토그램 분석값
    
    NOTE: 서보 모터를 활용한 대체 경로 탐색 기능은 교육생들이 직접 구현해야 합니다.
    """
    # 1. 히스토그램 3등분 분석
    left_sum, center_sum, right_sum, left_ratio, center_ratio, right_ratio = (
        analyze_histogram(histogram)
    )

    if DEBUG_MODE:
        print(f"Histogram Analysis (Road Line Detection):")
        print(
            f"  LEFT:   {left_sum:7d} (ratio: {left_ratio:.3f}) - Lower = More drivable"
        )
        print(
            f"  CENTER: {center_sum:7d} (ratio: {center_ratio:.3f}) - Lower = More drivable"
        )
        print(
            f"  RIGHT:  {right_sum:7d} (ratio: {right_ratio:.3f}) - Lower = More drivable"
        )
        print(
            f"  L-R Diff: {right_sum - left_sum:7d} | Threshold: {direction_threshold}"
        )

    # 2. 좌우 차이가 크면 회전
    # right_sum이 크면 = 오른쪽에 도로선 많음 = 왼쪽으로 회전
    # left_sum이 크면 = 왼쪽에 도로선 많음 = 오른쪽으로 회전
    if abs(right_sum - left_sum) > direction_threshold:
        if right_sum > left_sum:
            # 오른쪽에 도로선이 많음 = 왼쪽이 더 주행 가능
            direction = "LEFT"
        else:
            # 왼쪽에 도로선이 많음 = 오른쪽이 더 주행 가능
            direction = "RIGHT"

        if DEBUG_MODE:
            print(f"Decision: Turn {direction} (less road lines on that side)")
        if USE_BEEP and BEEP_ON_TURN:
            bot.Ctrl_BEEP_Switch(1)
            time.sleep(0.05)
            bot.Ctrl_BEEP_Switch(0)
        return direction, left_sum, center_sum, right_sum

    # 3. 막다른 길 감지 (center_ratio가 높으면 중앙에 도로선이 많음 = 막힘)
    if center_ratio > 0.7:  # 70% 이상이 도로선이면 막다른 길
        if DEBUG_MODE:
            print("Dead end detected! Center has too many road lines.")
            print("Choosing random direction (LEFT or RIGHT)...")
        
        # 차량 잠시 정지
        car_stop()
        time.sleep(0.3)
        
        # 랜덤으로 LEFT 또는 RIGHT 선택
        random_direction = random.choice(["LEFT", "RIGHT"])
        
        if DEBUG_MODE:
            print(f"Random direction selected: {random_direction}")
        
        # 부저로 막다른 길 알림
        if USE_BEEP:
            bot.Ctrl_BEEP_Switch(1)
            time.sleep(0.1)
            bot.Ctrl_BEEP_Switch(0)
            time.sleep(0.1)
            bot.Ctrl_BEEP_Switch(1)
            time.sleep(0.1)
            bot.Ctrl_BEEP_Switch(0)
        
        return random_direction, left_sum, center_sum, right_sum

    # 4. 직진 (중앙에 검정 도로가 있음)
    if DEBUG_MODE:
        print("Decision: Go straight (CENTER path has black road)")
    return "UP", left_sum, center_sum, right_sum


print("Direction decision functions defined successfully\n")

# ============================
# 보조 함수 정의
# ============================
print("=" * 50)
print("  Defining Helper Functions")
print("=" * 50)


def handle_keyboard_input(led_state):
    """
    키보드 입력 처리

    Returns:
        led_state: 현재 LED 상태 (None이면 종료)
    """
    key = cv2.waitKey(30) & 0xFF

    # ESC: 종료
    if key == 27:
        print("\nExiting...")
        return None

    # SPACE: 일시정지
    elif key == 32:
        print("\nPaused. Press any key to continue.")
        car_stop()
        cv2.waitKey()

    # 'l': LED 토글
    elif key == ord("l"):
        led_state = not led_state
        if led_state:
            bot.Ctrl_WQ2812_ALL(1, 2)
            print("LED ON")
        else:
            bot.Ctrl_WQ2812_ALL(0, 0)
            print("LED OFF")

    # 'b': 부저 테스트
    elif key == ord("b"):
        print("Beep!")
        bot.Ctrl_BEEP_Switch(1)
        time.sleep(0.1)
        bot.Ctrl_BEEP_Switch(0)

    return led_state


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
    print("\n" + "=" * 50)
    print("  STEP 10: Cleaning up and Exiting")
    print("=" * 50)

    car_stop()
    print("Motors stopped")

    if USE_LED_EFFECTS:
        bot.Ctrl_WQ2812_ALL(0, 0)
        print("LED turned off")

    bot.Ctrl_BEEP_Switch(0)

    bot.Ctrl_Servo(1, 90)
    bot.Ctrl_Servo(2, 25)
    print("Servo motors returned to initial position")

    cap.release()
    cv2.destroyAllWindows()
    print("Camera released")

    del bot
    print("Raspbot object deleted")

    print("\nCleanup completed successfully!")


print("Helper functions defined successfully\n")

# ============================
# 8단계: 메인 루프 실행
# ============================
print("=" * 50)
print("  STEP 9: Starting Main Loop")
print("=" * 50)
print("Controls:")
print("  ESC   : Exit")
print("  SPACE : Pause")
print("  'l'   : Toggle LED")
print("  'b'   : Test Beeper")
print("=" * 50)

frame_count = 0
start_time = time.time()
led_state = LED_ON_START

try:
    while True:
        frame_count += 1

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

        # 프레임 처리
        processed_frame = process_frame(
            frame, params["detect_value"], params["roi_top_y"], params["roi_bottom_y"]
        )
        histogram = np.sum(processed_frame, axis=0)

        # 방향 결정 및 제어
        if DEBUG_MODE:
            print(f"\n--- Frame {frame_count} ---")

        direction, hist_left, hist_center, hist_right = decide_direction(
            histogram,
            params["direction_threshold"],
            params["up_threshold"],
            params["detect_value"],
            params["roi_top_y"],
            params["roi_bottom_y"],
        )

        # 방향 정보 시각화
        processed_frame_visual = visualize_direction_on_frame(
            processed_frame, direction, hist_left, hist_center, hist_right
        )
        cv2.imshow("4_Processed Frame", processed_frame_visual)

        control_car(direction, params["motor_up_speed"], params["motor_down_speed"])

        # FPS 계산
        if frame_count % 10 == 0:
            elapsed = time.time() - start_time
            fps = 10 / elapsed
            if DEBUG_MODE:
                print(f"FPS: {fps:.1f}")
            start_time = time.time()

        # 키 입력 처리
        led_state = handle_keyboard_input(led_state)
        if led_state is None:
            break

        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nInterrupted by user")
except Exception as e:
    print(f"\nError occurred: {e}")
    import traceback

    traceback.print_exc()

# ============================
# 9단계: 정리 및 종료
# ============================
finally:
    cleanup_and_exit(bot, cap)
