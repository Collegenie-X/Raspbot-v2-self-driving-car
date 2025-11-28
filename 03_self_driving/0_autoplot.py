#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspbot v2 자율주행 코드 (개선 버전 v2.1)
라인 트레이싱 기반 자율주행 시스템

Copyright (C): 2015-2024, Shenzhen Yahboom Tech
Modified: 2025-11-25

═══════════════════════════════════════════════════════════
주요 기능:
═══════════════════════════════════════════════════════════
1. 실시간 비전 처리 (OpenCV 기반)
   - 원근 변환 (Perspective Transform)
   - 가중 그레이스케일 변환
   - 이진화 및 노이즈 제거

2. 히스토그램 기반 방향 결정
   - 6구역 분할 분석
   - 좌우 회전 판단
   - 막다른 길 감지 및 대체 경로 탐색

3. 차량 제어
   - 직진, 좌회전, 우회전 (제자리 회전)
   - 속도 부스트 (직진 시)
   - LED 색상 피드백 (초록=직진, 노랑=회전)

4. 실시간 파라미터 조정
   - OpenCV 트랙바를 통한 실시간 튜닝
   - 서보 각도, 속도, 검출 임계값 등

═══════════════════════════════════════════════════════════
주요 변경사항 (v2.1):
═══════════════════════════════════════════════════════════
1. 실제 카메라 해상도 자동 감지 및 적용
2. 원근 변환 영역 동적 계산 (상단 영역 포함)
3. Y Value 트랙바 범위 확장 (0~200)
4. 한글 주석 및 상세 설명 추가
5. 에러 처리 강화

═══════════════════════════════════════════════════════════
동작 흐름:
═══════════════════════════════════════════════════════════
1. 카메라 프레임 캡처
2. 원근 변환 (ROI 영역 → 정면 뷰)
3. 그레이스케일 변환 (RGB 가중치 적용)
4. 이진화 (흰색 라인 검출)
5. 히스토그램 분석 (좌우 영역 비교)
6. 방향 결정 (직진/좌회전/우회전)
7. 모터 제어 실행
8. 1번으로 반복

═══════════════════════════════════════════════════════════
사용 방법:
═══════════════════════════════════════════════════════════
1. 트랙바 조정:
   - Y Value: ROI 영역의 세로 위치 (높을수록 상단)
   - Detect Value: 이진화 임계값 (환경에 따라 조정)
   - Motor Speed: 속도 조절
   - R/G/B Weight: 색상 가중치 (라인 색상에 맞게)

2. Keyboard shortcuts:
   - ESC: Exit
   - SPACE: Pause
   - 'm': Motor toggle (ON/OFF)
   - 'l': LED toggle
   - 'b': Buzzer test
"""

import sys
import os

# Raspbot 라이브러리 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib", "raspbot"))

import cv2
import numpy as np
import random
import time
from Raspbot_Lib import Raspbot

# ============================
# 사용자 설정 영역 (여기를 수정하세요!)
# ============================

# 기본 속도 설정 (-255 ~ 255)
DEFAULT_SPEED_UP = 20  # 기본값: 100 (전진 속도)
DEFAULT_SPEED_DOWN = 10  # 기본값: 55 (회전 시 감속)
SPEED_BOOST = 10  # 직진 시 추가 속도

# 라인 검출 설정
DEFAULT_DETECT_VALUE = 120  # 기본값: 80 (밝은 환경용 - 높게 설정)
DEFAULT_BRIGHTNESS = 0  # 기본값: 0 (카메라 밝기 - 낮게)
DEFAULT_CONTRAST = 0  # 기본값: 40 (카메라 대비 - 중간)

# RGB 가중치 (흰색 라인 검출 최적화 - 밝은 환경용)
DEFAULT_R_WEIGHT = 30  # 기본값: 30 (빨강 가중치 낮춤)
DEFAULT_G_WEIGHT = 40  # 기본값: 40 (초록 중간)
DEFAULT_B_WEIGHT = 60  # 기본값: 60 (파랑 가중치 높임)

# 방향 판단 임계값
DEFAULT_DIRECTION_THRESHOLD = 35000  # 기본값: 35000
DEFAULT_UP_THRESHOLD = 220000  # 기본값: 220000

# 서보 모터 각도
DEFAULT_SERVO_1 = 90  # 좌우 각도 (0~180)
DEFAULT_SERVO_2 = 0  # 상하 각도 (0~110, 기본값 25)

# 디버그 모드
DEBUG_MODE = True  # True: 상세 정보 출력, False: 최소 정보만

# LED 효과 사용
USE_LED_EFFECTS = True  # LED 효과 사용 여부
LED_ON_START = True  # 시작 시 LED 켜기

# 부저 사용
USE_BEEP = True  # 부저 사용 여부
BEEP_ON_START = True  # 시작 시 부저 울리기
BEEP_ON_TURN = False  # 회전 시 부저 울리기

# ============================
# 시스템 초기화
# ============================

print("=" * 50)
print("  🚗 Raspbot v2 Autopilot Initializing...")
print("=" * 50)

# Raspbot 객체 생성
try:
    bot = Raspbot()
    print("✅ Raspbot hardware initialized")
except Exception as e:
    print(f"❌ Raspbot initialization failed: {e}")
    sys.exit(1)

# 카메라 초기화 (07_Camera_Driving.ipynb 방식)
try:
    print("🔍 Initializing USB camera...")

    # 카메라 열기 (Open the camera /dev/video0)
    cap = cv2.VideoCapture(0)

    # 해상도 설정 (Set the image width and height)
    width = 320
    height = 240
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)  # 명확한 속성 사용
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    # ⚠️ 밝기 조절 (화면이 너무 밝은 경우 - 낮은 값으로 시작)
    cap.set(cv2.CAP_PROP_BRIGHTNESS, 0)  # 밝기: -64 ~ 64 (기본: 0, 낮게 시작)
    cap.set(cv2.CAP_PROP_CONTRAST, 0)  # 대비: -64 ~ 64 (대비 높임)
    cap.set(cv2.CAP_PROP_SATURATION, 0)  # 채도: 0 ~ 100
    cap.set(cv2.CAP_PROP_EXPOSURE, 50)  # 노출: 1.0 ~ 5000 (낮게 설정)

    print(f"📹 Camera settings:")
    print(f"   - Resolution: {width}x{height}")
    print(f"   - Brightness: 0 (for dark environment)")
    print(f"   - Contrast: 40")
    print(f"   - Exposure: 100 (low)")

    # 추가 설정 (필요시 활성화)
    # cap.set(cv2.CAP_PROP_FPS, 30)  # 프레임레이트 설정
    # cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))

    # 카메라 정상 동작 확인 (Reading camera data)
    ret, frame = cap.read()
    if not ret or frame is None:
        raise Exception("Cannot read frame from camera")

    # 실제 해상도 확인 및 전역 변수 업데이트
    actual_height, actual_width = frame.shape[:2]
    ACTUAL_WIDTH = actual_width
    ACTUAL_HEIGHT = actual_height

    print(f"✅ USB camera initialized")
    print(f"   - Requested: {width}x{height}")
    print(f"   - Actual: {actual_width}x{actual_height}")

    # 실제 카메라 설정 값 확인
    print(f"   - Actual brightness: {int(cap.get(cv2.CAP_PROP_BRIGHTNESS))}")
    print(f"   - Actual contrast: {int(cap.get(cv2.CAP_PROP_CONTRAST))}")
    print(f"   - Actual exposure: {int(cap.get(cv2.CAP_PROP_EXPOSURE))}")

    if actual_width != width or actual_height != height:
        print(f"⚠️  Warning: Resolution mismatch. Adjusting perspective transform.")
        print(f"   → Adjust 'Y Value' trackbar to set ROI area.")

except Exception as e:
    print(f"\n❌ Camera initialization failed: {e}\n")
    print("=" * 50)
    print("Possible solutions:")
    print("1. Check USB camera connection")
    print("   ls /dev/video*")
    print("\n2. Check permissions")
    print("   sudo usermod -aG video $USER")
    print("   sudo reboot")
    print("\n3. Check if camera is used by another program")
    print("   sudo lsof | grep video")
    print("\n4. Test camera")
    print(
        "   python3 -c \"import cv2; cap=cv2.VideoCapture(0); print('OK' if cap.read()[0] else 'FAIL'); cap.release()\""
    )
    print("=" * 50)
    del bot
    sys.exit(1)

# 초기 하드웨어 설정
if LED_ON_START and USE_LED_EFFECTS:
    bot.Ctrl_WQ2812_ALL(1, 2)  # 파란색 LED 켜기
    print("💡 LED initialized")

if BEEP_ON_START and USE_BEEP:
    bot.Ctrl_BEEP_Switch(1)
    time.sleep(0.2)
    bot.Ctrl_BEEP_Switch(0)
    print("🔊 Buzzer tested")

# 서보 모터 초기 위치
bot.Ctrl_Servo(1, DEFAULT_SERVO_1)
bot.Ctrl_Servo(2, DEFAULT_SERVO_2)
print(f"📷 Servo motors initialized (S1:{DEFAULT_SERVO_1}°, S2:{DEFAULT_SERVO_2}°)")

# 모터 정지 상태로 초기화
for i in range(4):
    bot.Ctrl_Muto(i, 0)
print("🛑 Motors stopped (initial state)")


# ============================
# OpenCV 트랙바 설정
# ============================


def nothing(x):
    """트랙바 콜백 함수"""
    pass


# 전역 변수: 실제 카메라 해상도 저장
ACTUAL_WIDTH = 320
ACTUAL_HEIGHT = 240


# 윈도우 생성 (크기 조절 가능하도록 설정)
cv2.namedWindow("Camera Settings")
cv2.namedWindow("1_Frame", cv2.WINDOW_NORMAL)
cv2.namedWindow("2_frame_transformed", cv2.WINDOW_NORMAL)
cv2.namedWindow("3_gray_frame", cv2.WINDOW_NORMAL)
cv2.namedWindow("4_Processed Frame", cv2.WINDOW_NORMAL)

# 창 크기 설정
cv2.resizeWindow(
    "4_Processed Frame", ACTUAL_WIDTH, ACTUAL_HEIGHT
)  # 2배 확대 (320xACTUAL_HEIGHT → ACTUAL_WIDTHxACTUAL_HEIGHT)
cv2.resizeWindow("1_Frame", ACTUAL_WIDTH, ACTUAL_HEIGHT)  # 원본도 크게
cv2.resizeWindow(
    "2_frame_transformed", ACTUAL_WIDTH, ACTUAL_HEIGHT
)  # 변환된 이미지도 크게
cv2.resizeWindow("3_gray_frame", ACTUAL_WIDTH, ACTUAL_HEIGHT)  # 그레이스케일도 크게

# 서보 모터 트랙바
cv2.createTrackbar("Servo 1 Angle", "Camera Settings", DEFAULT_SERVO_1, 180, nothing)
cv2.createTrackbar(
    "Servo 2 Angle", "Camera Settings", DEFAULT_SERVO_2, 110, nothing
)  # 최대 110

# 이미지 처리 트랙바 (ROI 상단/하단 위치 개별 조절)
# ROI Top Y: 상단 Y 좌표 (0=화면 최상단, 높을수록 아래로)
# 범위: 0~1000 (실제 해상도에 맞게 자동 조정됨)
# 기본값: 0 (화면 최상단부터 시작)
cv2.createTrackbar("ROI Top Y", "Camera Settings", 688, 1000, nothing)
# ROI Bottom Y: 하단 Y 좌표 (0=화면 최상단, 높을수록 아래로)
# 범위: 0~1000 (실제 해상도에 맞게 자동 조정됨)
# 기본값: 800 (1000의 80%, 480 해상도 기준 약 384픽셀)
cv2.createTrackbar("ROI Bottom Y", "Camera Settings", 883, 1000, nothing)
cv2.createTrackbar(
    "Direction Threshold",
    "Camera Settings",
    DEFAULT_DIRECTION_THRESHOLD,
    500000,
    nothing,
)
cv2.createTrackbar(
    "Up Threshold", "Camera Settings", DEFAULT_UP_THRESHOLD, 500000, nothing
)

# 카메라 설정 트랙바
cv2.createTrackbar("Brightness", "Camera Settings", DEFAULT_BRIGHTNESS, 100, nothing)
cv2.createTrackbar("Contrast", "Camera Settings", DEFAULT_CONTRAST, 100, nothing)
cv2.createTrackbar(
    "Detect Value", "Camera Settings", DEFAULT_DETECT_VALUE, 150, nothing
)

# 속도 설정 트랙바
cv2.createTrackbar("Motor Up Speed", "Camera Settings", DEFAULT_SPEED_UP, 255, nothing)
cv2.createTrackbar(
    "Motor Down Speed", "Camera Settings", DEFAULT_SPEED_DOWN, 255, nothing
)

# 색상 가중치 트랙바
cv2.createTrackbar("R_weight", "Camera Settings", DEFAULT_R_WEIGHT, 100, nothing)
cv2.createTrackbar("G_weight", "Camera Settings", DEFAULT_G_WEIGHT, 100, nothing)
cv2.createTrackbar("B_weight", "Camera Settings", DEFAULT_B_WEIGHT, 100, nothing)

cv2.createTrackbar("Saturation", "Camera Settings", 20, 100, nothing)
cv2.createTrackbar("Gain", "Camera Settings", 20, 100, nothing)

print("🎛️  OpenCV trackbars configured")


# ============================
# 이미지 처리 함수
# ============================


def weighted_gray(image, r_weight, g_weight, b_weight):
    """
    가중 그레이스케일 변환

    RGB 채널별 가중치를 적용하여 그레이스케일로 변환합니다.
    흰색 라인 검출을 위해 각 색상의 기여도를 조절할 수 있습니다.

    Args:
        image: BGR 컬러 이미지
        r_weight: 빨강 채널 가중치 (0~100)
        g_weight: 초록 채널 가중치 (0~100)
        b_weight: 파랑 채널 가중치 (0~100)

    Returns:
        그레이스케일 이미지 (단일 채널)

    사용 예시:
        밝은 환경: R↓, G=중간, B↑ (파랑 채널 강조)
        어두운 환경: R↑, G=중간, B↓ (빨강 채널 강조)
    """
    # 가중치를 0~1 범위로 정규화
    r_weight /= 100.0
    g_weight /= 100.0
    b_weight /= 100.0

    # OpenCV는 BGR 순서: image[:,:,0]=B, image[:,:,1]=G, image[:,:,2]=R
    return cv2.addWeighted(
        cv2.addWeighted(image[:, :, 2], r_weight, image[:, :, 1], g_weight, 0),
        1.0,
        image[:, :, 0],
        b_weight,
        0,
    )


def draw_info_on_binary_frame(binary_frame, direction, histogram):
    """
    이진화 프레임에 방향 및 히스토그램 정보 표시 (개선된 버전)

    Args:
        binary_frame: 이진화된 프레임 (0=검정색 도로, 255=테두리/장애물)
        direction: 주행 방향 ("UP", "LEFT", "RIGHT", "BLOCKED")
        histogram: 히스토그램 배열

    Returns:
        정보가 표시된 컬러 프레임
    """
    # Convert binary image to color (for displaying information)
    color_frame = cv2.cvtColor(binary_frame, cv2.COLOR_GRAY2BGR)

    # Histogram analysis (divided into 3 sections)
    length = len(histogram)
    divide = 3  # Divide into 3 equal sections
    section_len = length // divide

    # Calculate left/center/right area sums (equal division)
    left_sum = int(np.sum(histogram[:section_len]))  # 0 ~ 1/3
    center_sum = int(np.sum(histogram[section_len : 2 * section_len]))  # 1/3 ~ 2/3
    right_sum = int(np.sum(histogram[2 * section_len :]))  # 2/3 ~ 3/3

    # Total sum
    total = left_sum + center_sum + right_sum

    # Calculate percentages
    if total > 0:
        left_pct = (left_sum / total) * 100
        center_pct = (center_sum / total) * 100
        right_pct = (right_sum / total) * 100
    else:
        left_pct = center_pct = right_pct = 0.0

    # Status panel background (compact and simple)
    panel_height = 60
    overlay = color_frame.copy()
    cv2.rectangle(overlay, (0, 0), (color_frame.shape[1], panel_height), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.75, color_frame, 0.25, 0, color_frame)

    # Text settings
    font = cv2.FONT_HERSHEY_SIMPLEX
    w = color_frame.shape[1]

    # Direction display (English)
    direction_map = {
        "UP": "FWD",
        "LEFT": "LEFT",
        "RIGHT": "RIGHT",
        "BLOCKED": "BLOCK",
        "STOP": "STOP",
    }
    direction_text = direction_map.get(direction, direction)

    # Direction colors
    direction_color = {
        "UP": (0, 255, 0),  # Green
        "LEFT": (0, 255, 255),  # Yellow
        "RIGHT": (0, 255, 255),  # Yellow
        "BLOCKED": (0, 0, 255),  # Red
        "STOP": (128, 128, 128),  # Gray
    }.get(direction, (255, 255, 255))

    # Simple one-line display
    # Direction (굵게)
    cv2.putText(
        color_frame, f"Dir:{direction_text}", (10, 25), font, 0.5, direction_color, 2
    )

    # LEFT (굵게)
    left_color = (100, 100, 255) if left_pct > 30 else (255, 255, 255)
    left_thickness = 2 if left_pct > 30 else 2
    cv2.putText(
        color_frame,
        f"L:{left_pct:.0f}%",
        (10, 45),
        font,
        0.5,
        left_color,
        left_thickness,
    )

    # CENTER (굵게)
    center_color = (100, 255, 100) if center_pct > 40 else (255, 255, 255)
    cv2.putText(
        color_frame,
        f"C:{center_pct:.0f}%",
        (w // 2 - 25, 45),
        font,
        0.5,
        center_color,
        2,
    )

    # RIGHT (굵게)
    right_color = (100, 100, 255) if right_pct > 30 else (255, 255, 255)
    right_thickness = 2 if right_pct > 30 else 2
    cv2.putText(
        color_frame,
        f"R:{right_pct:.0f}%",
        (w - 70, 45),
        font,
        0.5,
        right_color,
        right_thickness,
    )

    # Yellow dividing lines (2 lines for 3 equal sections)
    h = color_frame.shape[0]
    line_start_y = panel_height

    # Left boundary (1/3)
    cv2.line(
        color_frame, (section_len, line_start_y), (section_len, h), (0, 255, 255), 2
    )
    # Right boundary (2/3)
    cv2.line(
        color_frame,
        (2 * section_len, line_start_y),
        (2 * section_len, h),
        (0, 255, 255),
        2,
    )

    return color_frame


def draw_info_on_frame(frame, info_dict):
    """
    프레임에 실시간 정보 표시

    ⚠️ 주의: 이 함수는 더 이상 사용되지 않습니다.
    대신 draw_info_on_binary_frame()을 사용합니다.

    Args:
        frame: 표시할 프레임
        info_dict: 표시할 정보 딕셔너리
    """
    # 반투명 배경 그리기 (상단)
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (frame.shape[1], 120), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    # 텍스트 설정
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    thickness = 1
    y_offset = 20
    line_height = 20

    # 방향 표시 (크게)
    direction = info_dict.get("direction", "UNKNOWN")
    direction_color = {
        "UP": (0, 255, 0),  # 초록 (직진)
        "LEFT": (0, 255, 255),  # 노란 (좌회전)
        "RIGHT": (0, 255, 255),  # 노란 (우회전)
        "BLOCKED": (0, 0, 255),  # 빨강 (막힘)
        "STOP": (128, 128, 128),  # 회색 (정지)
    }.get(direction, (255, 255, 255))

    direction_text = {
        "UP": "⬆️ 직진",
        "LEFT": "◀️ 좌회전",
        "RIGHT": "▶️ 우회전",
        "BLOCKED": "🚫 막힘",
        "STOP": "⏸️ 정지",
    }.get(direction, direction)

    cv2.putText(
        frame, f"방향: {direction_text}", (10, y_offset), font, 0.7, direction_color, 2
    )

    # 속도 정보
    y_offset += line_height + 10
    speed_left = info_dict.get("speed_left", 0)
    speed_right = info_dict.get("speed_right", 0)
    cv2.putText(
        frame,
        f"속도: L={speed_left:3d} | R={speed_right:3d}",
        (10, y_offset),
        font,
        font_scale,
        (255, 255, 255),
        thickness,
    )

    # 프레임 카운터 및 FPS
    y_offset += line_height
    frame_count = info_dict.get("frame_count", 0)
    fps = info_dict.get("fps", 0.0)
    cv2.putText(
        frame,
        f"Frame: {frame_count:04d} | FPS: {fps:.1f}",
        (10, y_offset),
        font,
        font_scale,
        (255, 255, 255),
        thickness,
    )

    # 주요 변수 상태
    y_offset += line_height
    detect_val = info_dict.get("detect_value", 0)
    threshold = info_dict.get("direction_threshold", 0)
    cv2.putText(
        frame,
        f"Detect: {detect_val} | Threshold: {threshold//1000}k",
        (10, y_offset),
        font,
        font_scale,
        (255, 255, 255),
        thickness,
    )

    # LED 상태
    y_offset += line_height
    led_status = "ON" if info_dict.get("led_enabled", True) else "OFF"
    led_color = (0, 255, 0) if info_dict.get("led_enabled", True) else (128, 128, 128)
    cv2.putText(
        frame,
        f"LED: {led_status}",
        (10, y_offset),
        font,
        font_scale,
        led_color,
        thickness,
    )

    return frame


def process_frame(
    frame, detect_value, r_weight, g_weight, b_weight, roi_top_y, roi_bottom_y
):
    """
    프레임 처리 및 엣지 검출

    단계:
    1. 원근 변환 영역 정의 (실제 해상도 기반)
    2. 원본 프레임에 ROI 사각형 표시
    3. 원근 변환 적용
    4. 그레이스케일 변환 (RGB 가중치 적용)
    5. 이진화 및 노이즈 제거

    Args:
        frame: 입력 프레임 (BGR)
        detect_value: 이진화 임계값
        r_weight, g_weight, b_weight: RGB 가중치
        roi_top_y: ROI 상단 Y 좌표 (0=화면 최상단)
        roi_bottom_y: ROI 하단 Y 좌표 (0=화면 최상단)
    """
    # 실제 해상도 가져오기
    actual_h, actual_w = frame.shape[:2]

    # ROI 좌표를 실제 해상도에 맞게 조정
    # 트랙바 범위는 0~1000이지만, 실제 해상도에 맞게 스케일링
    # 예: 트랙바 값 500, 실제 높이 480 → 500 * 480 / 1000 = 240
    top_y = int(roi_top_y * actual_h / 1000)
    bottom_y = int(roi_bottom_y * actual_h / 1000)

    # 값이 실제 해상도 범위를 벗어나지 않도록 제한
    top_y = max(0, min(top_y, actual_h - 1))
    bottom_y = max(0, min(bottom_y, actual_h - 1))

    # 상단이 하단보다 아래에 있으면 교정 (최소 50픽셀 높이 보장)
    if top_y >= bottom_y:
        top_y = max(0, bottom_y - 50)

    margin = 10  # 좌우 여백

    # ROI 영역: [좌하, 우하, 우상, 좌상] 순서
    pts_src = np.float32(
        [
            [margin, bottom_y],  # 좌하
            [actual_w - margin, bottom_y],  # 우하
            [actual_w - margin, top_y],  # 우상
            [margin, top_y],  # 좌상
        ]
    )

    # 목표 해상도 (고정: 320x240)
    target_w, target_h = 320, 240
    pts_dst = np.float32([[0, target_h], [target_w, target_h], [target_w, 0], [0, 0]])

    # 원본 프레임에 ROI 사각형 그리기 (녹색)
    pts = pts_src.reshape((-1, 1, 2)).astype(np.int32)
    frame_with_rect = cv2.polylines(
        frame.copy(), [pts], isClosed=True, color=(0, 255, 0), thickness=2
    )

    # 해상도 및 ROI 정보 표시 (크고 굵게)
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.8  # 크기 증가
    thickness = 2  # 굵기 증가
    color = (0, 255, 255)  # 노란색

    cv2.putText(
        frame_with_rect,
        f"Resolution: {actual_w}x{actual_h}",
        (10, 25),
        font,
        font_scale,
        color,
        thickness,
    )
    cv2.putText(
        frame_with_rect,
        f"ROI Top: {top_y} / Bottom: {bottom_y}",
        (10, 55),
        font,
        font_scale,
        color,
        thickness,
    )
    cv2.putText(
        frame_with_rect,
        f"ROI Height: {bottom_y - top_y}px",
        (10, 85),
        font,
        font_scale,
        color,
        thickness,
    )
    cv2.imshow("1_Frame", frame_with_rect)

    # 원근 변환 적용
    mat_affine = cv2.getPerspectiveTransform(pts_src, pts_dst)
    frame_transformed = cv2.warpPerspective(frame, mat_affine, (target_w, target_h))
    cv2.imshow("2_frame_transformed", frame_transformed)

    # 그레이스케일 변환
    gray_frame = weighted_gray(frame_transformed, r_weight, g_weight, b_weight)
    cv2.imshow("3_gray_frame", gray_frame)

    # 이진화 (검정색=0, 나머지=1)
    # detect_value보다 낮으면 0(검정색 도로), 높으면 255(테두리/장애물)
    _, binary_frame = cv2.threshold(gray_frame, detect_value, 255, cv2.THRESH_BINARY)

    # 노이즈 제거 (모폴로지 연산)
    kernel = np.ones((5, 5), np.uint8)
    binary_frame = cv2.morphologyEx(binary_frame, cv2.MORPH_CLOSE, kernel)
    binary_frame = cv2.morphologyEx(binary_frame, cv2.MORPH_OPEN, kernel)

    # 히스토그램 계산 (반환용)
    # 각 열의 흰색(테두리/장애물) 픽셀 수를 합산
    histogram = np.sum(binary_frame, axis=0)

    return binary_frame, histogram


# ============================
# 차량 제어 함수 (Raspbot_Lib 사용)
# ============================


def car_run(speed_left, speed_right):
    """
    전진 (양쪽 모터 동일 속도)

    Args:
        speed_left: 왼쪽 모터 속도 (-255 ~ 255, 음수=후진, 양수=전진)
        speed_right: 오른쪽 모터 속도 (-255 ~ 255)

    모터 배치:
        M1 (0): 왼쪽 앞바퀴
        M2 (1): 왼쪽 뒷바퀴
        M3 (2): 오른쪽 앞바퀴
        M4 (3): 오른쪽 뒷바퀴
    """
    bot.Ctrl_Muto(0, speed_left)  # M1 (왼쪽 앞)
    bot.Ctrl_Muto(1, speed_left)  # M2 (왼쪽 뒤)
    bot.Ctrl_Muto(2, speed_right)  # M3 (오른쪽 앞)
    bot.Ctrl_Muto(3, speed_right)  # M4 (오른쪽 뒤)


def car_stop():
    """
    정지 (모든 모터 속도 0)

    긴급 정지 또는 일시 정지 시 사용
    """
    for i in range(4):
        bot.Ctrl_Muto(i, 0)


def car_left(speed_left, speed_right):
    """
    좌회전 (제자리 회전 방식)

    동작:
        - 왼쪽 바퀴: 후진 (음수 속도)
        - 오른쪽 바퀴: 전진 (양수 속도)

    결과: 제자리에서 왼쪽으로 회전
    """
    bot.Ctrl_Muto(0, -speed_left)  # M1 후진
    bot.Ctrl_Muto(1, -speed_left)  # M2 후진
    bot.Ctrl_Muto(2, speed_right)  # M3 전진
    bot.Ctrl_Muto(3, speed_right)  # M4 전진


def car_right(speed_left, speed_right):
    """
    우회전 (제자리 회전 방식)

    동작:
        - 왼쪽 바퀴: 전진 (양수 속도)
        - 오른쪽 바퀴: 후진 (음수 속도)

    결과: 제자리에서 오른쪽으로 회전
    """
    bot.Ctrl_Muto(0, speed_left)  # M1 전진
    bot.Ctrl_Muto(1, speed_left)  # M2 전진
    bot.Ctrl_Muto(2, -speed_right)  # M3 후진
    bot.Ctrl_Muto(3, -speed_right)  # M4 후진


def rotate_servo(servo_id, angle):
    """
    서보 모터 회전

    Args:
        servo_id: 서보 ID (1=좌우, 2=상하)
        angle: 각도 (Servo 1: 0~180, Servo 2: 0~110)

    용도:
        - Servo 1: 카메라 좌우 회전
        - Servo 2: 카메라 상하 각도 조절
    """
    if servo_id == 2 and angle > 110:
        angle = 110  # Servo 2는 최대 110도로 제한
    bot.Ctrl_Servo(servo_id, angle)


# ============================
# 방향 결정 및 제어 함수
# ============================


def decide_direction(
    histogram,
    direction_threshold,
    up_threshold,
    detect_value,
    r_weight,
    g_weight,
    b_weight,
    roi_top_y,
    roi_bottom_y,
):
    """
    히스토그램 기반 방향 결정 (3등분 방식)

    동작 방식:
    1. 히스토그램을 3개 구역으로 균등 분할 (LEFT, CENTER, RIGHT)
    2. 좌우 영역의 테두리 검출량 비교
    3. 좌우 차이가 임계값보다 크면 회전
    4. 중앙 영역이 막혀있으면 대체 경로 탐색
    5. 그 외의 경우 직진

    Args:
        histogram: 이진화된 이미지의 가로 히스토그램 (테두리/장애물 검출)
        direction_threshold: 좌우 회전 판단 임계값
        up_threshold: 직진 가능 여부 판단 임계값

    Returns:
        방향 문자열 ("UP", "LEFT", "RIGHT", "BLOCKED")
    """
    length = len(histogram)

    # 히스토그램을 3개 구역으로 균등 분할
    DIVIDE = 3
    section_len = length // DIVIDE

    # 좌/중/우 영역 (각 1/3씩)
    left = int(np.sum(histogram[:section_len]))  # 0 ~ 1/3
    center = int(np.sum(histogram[section_len : 2 * section_len]))  # 1/3 ~ 2/3
    right = int(np.sum(histogram[2 * section_len :]))  # 2/3 ~ 3/3

    if DEBUG_MODE:
        print(
            f"Left: {left:6d} | Center: {center:6d} | Right: {right:6d} | Diff(R-L): {right - left:6d}"
        )

    # 좌우 차이가 큰 경우 방향 전환
    # 우측에 테두리가 많으면 좌회전, 좌측에 테두리가 많으면 우회전
    if abs(right - left) > direction_threshold:
        direction = "LEFT" if right > left else "RIGHT"
        if DEBUG_MODE:
            print(f"🔄 Turn {direction} (edge avoidance)")

        # 회전 시 부저 (옵션)
        if USE_BEEP and BEEP_ON_TURN:
            bot.Ctrl_BEEP_Switch(1)
            time.sleep(0.05)
            bot.Ctrl_BEEP_Switch(0)

        return direction

    # 중앙 영역 체크 (테두리/장애물이 너무 많으면 막힌 것)
    total = left + center + right
    if total > 0:
        center_ratio = center / total
    else:
        center_ratio = 0

    # 중앙에 테두리/장애물이 너무 많으면 막힌 것으로 판단
    if center > up_threshold:
        if DEBUG_MODE:
            print(f"🚫 CENTER BLOCKED! (center={center}, threshold={up_threshold})")
        car_stop()
        time.sleep(0.3)
        return rotate_servo_and_check_direction(
            detect_value, r_weight, g_weight, b_weight, roi_top_y, roi_bottom_y
        )

    # 직진 (중앙이 비교적 깨끗함)
    if DEBUG_MODE:
        print(f"⬆️  Going straight (center clear: {center_ratio*100:.1f}%)")
    return "UP"


def rotate_servo_and_check_direction(
    detect_value, r_weight, g_weight, b_weight, roi_top_y, roi_bottom_y
):
    """
    서보 모터 회전으로 대체 경로 확인

    막다른 길에 도달했을 때 호출되어:
    1. 서보 모터를 회전시켜 주변 탐색
    2. 좌/우/중앙 영역 분석
    3. 가장 적합한 방향 반환
    """
    global cap

    if DEBUG_MODE:
        print("🔍 Dead end detected! Searching alternative route...")

    # 서보 모터를 180도로 회전하여 뒤쪽 확인
    bot.Ctrl_Servo(1, 180)
    bot.Ctrl_Servo(2, 100)
    time.sleep(0.5)

    # 새 프레임 캡처
    ret, frame = cap.read()
    if not ret:
        print("❌ Cannot read frame from camera.")
        return "STOP"

    # 프레임 처리
    processed_frame, histogram_180 = process_frame(
        frame, detect_value, r_weight, g_weight, b_weight, roi_top_y, roi_bottom_y
    )
    length = len(histogram_180)

    # 3등분 분석
    section_len = length // 3
    left = int(np.sum(histogram_180[:section_len]))
    center = int(np.sum(histogram_180[section_len : 2 * section_len]))
    right = int(np.sum(histogram_180[2 * section_len :]))

    if DEBUG_MODE:
        print(f"Alternative scan - Left: {left}, Center: {center}, Right: {right}")

    # 서보 모터 원위치
    servo_1_angle = cv2.getTrackbarPos("Servo 1 Angle", "Camera Settings")
    servo_2_angle = cv2.getTrackbarPos("Servo 2 Angle", "Camera Settings")
    bot.Ctrl_Servo(1, servo_1_angle)
    bot.Ctrl_Servo(2, servo_2_angle)
    time.sleep(0.3)

    # 중앙이 가장 비어있으면 (테두리가 적으면) 직진 가능
    # 테두리가 적다 = 안전하다
    if center < left and center < right:
        if DEBUG_MODE:
            print("✅ Center clear -> Go FORWARD")
        return "UP"

    # 좌우 비교하여 테두리가 적은 쪽으로 회전
    if left < right:
        if DEBUG_MODE:
            print("✅ Left clearer -> Turn LEFT")
        return "LEFT"
    else:
        if DEBUG_MODE:
            print("✅ Right clearer -> Turn RIGHT")
        return "RIGHT"


def control_car(direction, up_speed, down_speed):
    """
    차량 제어 (방향에 따른 모터 제어)

    ⚠️ 주의: 이 함수는 더 이상 메인 루프에서 사용되지 않습니다.
    차량 제어 로직이 메인 루프에 직접 통합되어 LED 토글 기능과
    실시간 정보 표시를 지원합니다.

    동작:
    1. "UP": 직진 (양쪽 모터 동일 속도 + 부스트)
    2. "LEFT": 좌회전 (왼쪽 후진, 오른쪽 전진)
    3. "RIGHT": 우회전 (왼쪽 전진, 오른쪽 후진)
    4. "RANDOM": 무작위 방향 선택 (막다른 길용)

    Args:
        direction: 방향 문자열 ("UP", "LEFT", "RIGHT", "RANDOM")
        up_speed: 기본 전진 속도 (0~255)
        down_speed: 회전 시 감속 속도 (0~255)
    """
    if direction == "UP":
        # Forward: apply speed boost
        boosted_speed = min(up_speed + SPEED_BOOST, 255)
        car_run(boosted_speed, boosted_speed)
        if DEBUG_MODE:
            print(f"Forward - Speed: {boosted_speed}")

        # LED: Green (normal driving)
        if USE_LED_EFFECTS:
            bot.Ctrl_WQ2812_ALL(1, 1)

    elif direction == "LEFT":
        # Left turn: left slow, right fast
        car_left(down_speed - 10, up_speed + 10)
        if DEBUG_MODE:
            print(f"Turn LEFT - L:{down_speed-10}, R:{up_speed+10}")

        # LED: Yellow (turning)
        if USE_LED_EFFECTS:
            bot.Ctrl_WQ2812_ALL(1, 3)

    elif direction == "RIGHT":
        # Right turn: left fast, right slow
        car_right(up_speed + 10, down_speed - 10)
        if DEBUG_MODE:
            print(f"Turn RIGHT - L:{up_speed+10}, R:{down_speed-10}")

        # LED: 노란색 (회전 중)
        if USE_LED_EFFECTS:
            bot.Ctrl_WQ2812_ALL(1, 3)

    elif direction == "RANDOM":
        # 무작위 방향 (막다른 길 탈출용)
        random_direction = random.choice(["LEFT", "RIGHT"])
        if DEBUG_MODE:
            print(f"Random direction: {random_direction}")
        control_car(random_direction, up_speed, down_speed)


# ============================
# 메인 루프
# ============================

print("=" * 50)
print("  🚗 Raspbot v2 Autopilot Started!")
print("=" * 50)
print("Controls:")
print("  ESC   : Quit")
print("  SPACE : Pause/Debug")
print("  'l'   : Toggle LED Bar")
print("  'b'   : Test Beep")
print("=" * 50)
print("\n📺 Display Info:")
print("  - 1_Frame: Original video + ROI")
print("  - 4_Processed Frame: Binary + Status panel")
print("    * Binary: 0=Road(black), 1=Edge/Obstacle(white)")
print("    * Direction: FORWARD/LEFT TURN/RIGHT TURN/BLOCKED")
print("    * L/C/R: Edge detection distribution %")
print("    * Division lines: Yellow")
print("=" * 50)
print("\n💡 LED Bar Toggle:")
print("  - 'l' key: Toggle LED Bar on/off")
print("  - Enabled: Auto color change by driving state")
print("  - Disabled: Always off")
print("=" * 50)

frame_count = 0
start_time = time.time()
led_state = LED_ON_START
led_enabled = True  # LED enabled state (toggle)
motor_enabled = True  # Motor enabled state (toggle) - START ENABLED
current_direction = "STOP"
current_speed_left = 0
current_speed_right = 0
fps = 0.0

print("\n" + "=" * 50)
print("  🚗 Raspbot Autopilot Starting...")
print("=" * 50)
print("✅ MOTOR ENABLED (Press 'm' to stop)")
print("\nKeyboard Controls:")
print("  ESC   : Exit")
print("  SPACE : Pause")
print("  'm'   : Motor toggle (ON/OFF)")
print("  'l'   : LED toggle")
print("  'b'   : Buzzer test")
print("=" * 50 + "\n")

try:
    while True:
        frame_count += 1

        # 트랙바 값 읽기
        brightness = cv2.getTrackbarPos("Brightness", "Camera Settings")
        contrast = cv2.getTrackbarPos("Contrast", "Camera Settings")
        saturation = cv2.getTrackbarPos("Saturation", "Camera Settings")
        gain = cv2.getTrackbarPos("Gain", "Camera Settings")
        detect_value = cv2.getTrackbarPos("Detect Value", "Camera Settings")
        motor_up_speed = cv2.getTrackbarPos("Motor Up Speed", "Camera Settings")
        motor_down_speed = cv2.getTrackbarPos("Motor Down Speed", "Camera Settings")
        r_weight = cv2.getTrackbarPos("R_weight", "Camera Settings")
        g_weight = cv2.getTrackbarPos("G_weight", "Camera Settings")
        b_weight = cv2.getTrackbarPos("B_weight", "Camera Settings")
        servo_1_angle = cv2.getTrackbarPos("Servo 1 Angle", "Camera Settings")
        servo_2_angle = cv2.getTrackbarPos("Servo 2 Angle", "Camera Settings")
        roi_top_y = cv2.getTrackbarPos("ROI Top Y", "Camera Settings")
        roi_bottom_y = cv2.getTrackbarPos("ROI Bottom Y", "Camera Settings")
        direction_threshold = cv2.getTrackbarPos(
            "Direction Threshold", "Camera Settings"
        )
        up_threshold = cv2.getTrackbarPos("Up Threshold", "Camera Settings")

        # 카메라 속성 설정
        cap.set(cv2.CAP_PROP_BRIGHTNESS, brightness)
        cap.set(cv2.CAP_PROP_CONTRAST, contrast)
        cap.set(cv2.CAP_PROP_SATURATION, saturation)
        cap.set(cv2.CAP_PROP_GAIN, gain)

        # 프레임 읽기 (opencv_camera.py 방식)
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to read frame from camera.")
            break

        # 서보 모터 각도 조절
        rotate_servo(1, servo_1_angle)
        rotate_servo(2, servo_2_angle)

        # 프레임 처리
        processed_frame, histogram = process_frame(
            frame, detect_value, r_weight, g_weight, b_weight, roi_top_y, roi_bottom_y
        )

        # 방향 결정 및 제어
        if DEBUG_MODE:
            print(f"\n--- Frame {frame_count} ---")

        direction = decide_direction(
            histogram,
            direction_threshold,
            up_threshold,
            detect_value,
            r_weight,
            g_weight,
            b_weight,
            roi_top_y,
            roi_bottom_y,
        )
        current_direction = direction

        # Motor control (check if motor enabled)
        if not motor_enabled:
            # Motor disabled - stop
            car_stop()
            current_speed_left = 0
            current_speed_right = 0

        elif direction == "UP":
            # Forward
            boosted_speed = min(motor_up_speed + SPEED_BOOST, 255)
            car_run(boosted_speed, boosted_speed)
            current_speed_left = boosted_speed
            current_speed_right = boosted_speed

            # LED: Green (normal driving) - only if LED enabled
            if USE_LED_EFFECTS and led_enabled:
                bot.Ctrl_WQ2812_ALL(1, 1)
            if DEBUG_MODE:
                print(f"Forward - Speed: {boosted_speed}")

        elif direction == "LEFT":
            # Turn left
            left_speed = motor_down_speed - 10
            right_speed = motor_up_speed + 10
            car_left(left_speed, right_speed)
            current_speed_left = -left_speed
            current_speed_right = right_speed

            # LED: Yellow (turning) - only if LED enabled
            if USE_LED_EFFECTS and led_enabled:
                bot.Ctrl_WQ2812_ALL(1, 3)
            if DEBUG_MODE:
                print(f"Turn LEFT - L:{left_speed}, R:{right_speed}")

        elif direction == "RIGHT":
            # Turn right
            left_speed = motor_up_speed + 10
            right_speed = motor_down_speed - 10
            car_right(left_speed, right_speed)
            current_speed_left = left_speed
            current_speed_right = -right_speed

            # LED: Yellow (turning) - only if LED enabled
            if USE_LED_EFFECTS and led_enabled:
                bot.Ctrl_WQ2812_ALL(1, 3)
            if DEBUG_MODE:
                print(f"Turn RIGHT - L:{left_speed}, R:{right_speed}")

        elif direction == "RANDOM":
            # Random direction
            random_direction = random.choice(["LEFT", "RIGHT"])
            if DEBUG_MODE:
                print(f"Random direction: {random_direction}")

            if random_direction == "LEFT":
                left_speed = motor_down_speed - 10
                right_speed = motor_up_speed + 10
                car_left(left_speed, right_speed)
                current_speed_left = -left_speed
                current_speed_right = right_speed
            else:
                left_speed = motor_up_speed + 10
                right_speed = motor_down_speed - 10
                car_right(left_speed, right_speed)
                current_speed_left = left_speed
                current_speed_right = -right_speed

        # FPS 계산 (10프레임마다)
        if frame_count % 10 == 0:
            elapsed = time.time() - start_time
            fps = 10 / elapsed if elapsed > 0 else 0.0
            if DEBUG_MODE:
                print(f"📊 FPS: {fps:.1f}")
            start_time = time.time()

        # 4_Processed Frame에 정보 표시
        processed_with_info = draw_info_on_binary_frame(
            processed_frame, current_direction, histogram
        )
        cv2.imshow("4_Processed Frame", processed_with_info)

        # 키 입력 처리 (대기 시간 증가)
        key = cv2.waitKey(1) & 0xFF

        if key == 27:  # ESC
            print("\n🛑 Stopping...")
            break
        elif key == 32:  # SPACE
            print("\n⏸️  Paused. Press any key to continue.")
            car_stop()
            current_direction = "STOP"
            current_speed_left = 0
            current_speed_right = 0
            cv2.waitKey()
        elif key == ord("m") or key == ord("M"):  # Motor toggle
            motor_enabled = not motor_enabled
            if motor_enabled:
                print("🚗 MOTOR ENABLED")
            else:
                car_stop()
                current_speed_left = 0
                current_speed_right = 0
                print("🛑 MOTOR DISABLED (stopped)")
        elif key == ord("l") or key == ord("L"):  # LED Bar toggle
            led_enabled = not led_enabled
            if led_enabled:
                print("💡 LED Bar ENABLED")
            else:
                bot.Ctrl_WQ2812_ALL(0, 0)  # Turn off LED
                print("💡 LED Bar DISABLED")
        elif key == ord("b") or key == ord("B"):  # Buzzer test
            print("🔊 Beep!")
            bot.Ctrl_BEEP_Switch(1)
            time.sleep(0.1)
            bot.Ctrl_BEEP_Switch(0)

except KeyboardInterrupt:
    print("\n⚠️  Interrupted by user")
except Exception as e:
    print(f"\n❌ Error occurred: {e}")
    import traceback

    traceback.print_exc()

finally:
    print("\n🧹 Cleaning up...")

    # 모터 정지
    car_stop()
    print("✅ Motors stopped")

    # LED 끄기 (항상 끄기)
    bot.Ctrl_WQ2812_ALL(0, 0)
    print("✅ LEDs off")

    # 부저 끄기
    bot.Ctrl_BEEP_Switch(0)

    # 서보 모터 초기 위치
    bot.Ctrl_Servo(1, 90)
    bot.Ctrl_Servo(2, 25)
    print("✅ Servos reset")

    # 카메라 해제
    cap.release()
    cv2.destroyAllWindows()
    print("✅ Camera released")

    # Raspbot 객체 삭제
    del bot
    print("✅ Raspbot object deleted")

    print("✅ Done!")
