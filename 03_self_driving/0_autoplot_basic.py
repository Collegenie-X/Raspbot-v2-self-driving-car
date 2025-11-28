#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspbot v2 자율주행 수업용 코드 - Step 1: 기본 영상 처리
RGB 필터 없이 기본적인 그레이스케일 변환을 사용하여 라인을 인식합니다.

목적:
- 색상 필터링 없이 명도(밝기) 차이만으로 라인을 인식해봅니다.
- 카메라 설정(밝기, 대비)이 인식률에 미치는 영향을 학습합니다.
- RGB 가중치 필터가 왜 필요한지 이해하기 위한 기초 단계입니다.

Copyright (C): 2015-2024, Shenzhen Yahboom Tech
Modified: 2025-11-28
"""

import sys
import os

# ============================
# 1단계: 라이브러리 및 모듈 import
# ============================
print("=" * 50)
print("  📚 1단계: 라이브러리 로딩 중...")
print("=" * 50)

# Raspbot 라이브러리 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib", "raspbot"))

import cv2
import numpy as np
import time
from Raspbot_Lib import Raspbot

print("✅ 라이브러리 로딩 완료\n")

# ============================
# 사용자 설정 영역
# ============================
print("=" * 50)
print("  ⚙️  설정 값 로딩 중...")
print("=" * 50)

# 기본 속도 설정 (-255 ~ 255)
DEFAULT_SPEED_UP = 20
DEFAULT_SPEED_DOWN = 10
SPEED_BOOST = 15

# 라인 검출 설정
DEFAULT_DETECT_VALUE = 120
DEFAULT_BRIGHTNESS = 0
DEFAULT_CONTRAST = 40

# 방향 판단 임계값
DEFAULT_DIRECTION_THRESHOLD = 35000
DEFAULT_UP_THRESHOLD = 220000

# 서보 모터 각도
DEFAULT_SERVO_1 = 90  # 좌우 각도 (0~180)
DEFAULT_SERVO_2 = 25  # 상하 각도 (0~110)

# 디버그 모드
DEBUG_MODE = True

# LED 효과 사용
USE_LED_EFFECTS = True
LED_ON_START = True

# 부저 사용
USE_BEEP = True
BEEP_ON_START = True
BEEP_ON_TURN = False

print("✅ 설정 값 로딩 완료\n")

# ============================
# 2단계: 하드웨어 초기화
# ============================
print("=" * 50)
print("  🔧 2단계: 하드웨어 초기화 중...")
print("=" * 50)

# Raspbot 객체 생성
try:
    bot = Raspbot()
    print("✅ Raspbot 하드웨어 초기화 완료")
except Exception as e:
    print(f"❌ Raspbot 초기화 실패: {e}")
    sys.exit(1)

# 카메라 초기화
try:
    print("\n📹 카메라 초기화 중...")
    cap = cv2.VideoCapture(0)
    width = 320
    height = 240
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    
    # 카메라 기본 속성 설정
    cap.set(cv2.CAP_PROP_BRIGHTNESS, DEFAULT_BRIGHTNESS)
    cap.set(cv2.CAP_PROP_CONTRAST, DEFAULT_CONTRAST)
    cap.set(cv2.CAP_PROP_SATURATION, 50)
    cap.set(cv2.CAP_PROP_EXPOSURE, 100)

    ret, frame = cap.read()
    if not ret or frame is None:
        raise Exception("카메라에서 프레임을 읽을 수 없습니다")

    actual_height, actual_width = frame.shape[:2]
    print(f"✅ USB 카메라 초기화 완료 ({actual_width}x{actual_height})")

except Exception as e:
    print(f"\n❌ 카메라 초기화 실패: {e}\n")
    del bot
    sys.exit(1)

# 초기 하드웨어 설정
if LED_ON_START and USE_LED_EFFECTS:
    bot.Ctrl_WQ2812_ALL(1, 2)  # 파란색 LED
    print("💡 LED 초기화 완료")

if BEEP_ON_START and USE_BEEP:
    bot.Ctrl_BEEP_Switch(1)
    time.sleep(0.2)
    bot.Ctrl_BEEP_Switch(0)
    print("🔊 부저 테스트 완료")

# 서보 모터 및 주행 모터 초기화
bot.Ctrl_Servo(1, DEFAULT_SERVO_1)
bot.Ctrl_Servo(2, DEFAULT_SERVO_2)
for i in range(4):
    bot.Ctrl_Muto(i, 0)
print("🛑 모터 정지 상태로 초기화 완료\n")

# ============================
# 3단계: 트랙바 및 윈도우 설정
# ============================
print("=" * 50)
print("  🎛️  3단계: 트랙바 및 윈도우 설정 중...")
print("=" * 50)

def nothing(x):
    pass

# 윈도우 생성
cv2.namedWindow("Camera Settings")
cv2.namedWindow("1_Frame", cv2.WINDOW_NORMAL)
cv2.namedWindow("2_frame_transformed", cv2.WINDOW_NORMAL)
cv2.namedWindow("3_gray_frame", cv2.WINDOW_NORMAL)
cv2.namedWindow("4_Processed Frame", cv2.WINDOW_NORMAL)

cv2.resizeWindow("4_Processed Frame", 640, 480)
cv2.resizeWindow("1_Frame", 640, 480)

# 서보 모터 트랙바
cv2.createTrackbar("Servo 1 Angle", "Camera Settings", DEFAULT_SERVO_1, 180, nothing)
cv2.createTrackbar("Servo 2 Angle", "Camera Settings", DEFAULT_SERVO_2, 110, nothing)

# 이미지 처리 트랙바 (RGB Weight 제거됨)
cv2.createTrackbar("ROI Top Y", "Camera Settings", 0, 1000, nothing)
cv2.createTrackbar("ROI Bottom Y", "Camera Settings", 800, 1000, nothing)
cv2.createTrackbar("Detect Value", "Camera Settings", DEFAULT_DETECT_VALUE, 255, nothing)

# 주행 설정 트랙바
cv2.createTrackbar("Direction Threshold", "Camera Settings", DEFAULT_DIRECTION_THRESHOLD, 500000, nothing)
cv2.createTrackbar("Up Threshold", "Camera Settings", DEFAULT_UP_THRESHOLD, 500000, nothing)
cv2.createTrackbar("Motor Up Speed", "Camera Settings", DEFAULT_SPEED_UP, 255, nothing)
cv2.createTrackbar("Motor Down Speed", "Camera Settings", DEFAULT_SPEED_DOWN, 255, nothing)

# 카메라 설정 트랙바
cv2.createTrackbar("Brightness", "Camera Settings", DEFAULT_BRIGHTNESS, 100, nothing)
cv2.createTrackbar("Contrast", "Camera Settings", DEFAULT_CONTRAST, 100, nothing)

print("✅ 트랙바 및 윈도우 설정 완료\n")

# ============================
# 4단계: 이미지 처리 함수 정의
# ============================
print("=" * 50)
print("  🖼️  4단계: 이미지 처리 함수 정의")
print("=" * 50)

def process_frame(frame, detect_value, roi_top_y, roi_bottom_y):
    """
    프레임 처리 및 엣지 검출 (RGB 필터 없음)
    """
    actual_h, actual_w = frame.shape[:2]

    # ROI 영역 계산
    top_y = int(roi_top_y * actual_h / 1000)
    bottom_y = int(roi_bottom_y * actual_h / 1000)
    top_y = max(0, min(top_y, actual_h - 1))
    bottom_y = max(0, min(bottom_y, actual_h - 1))
    if top_y >= bottom_y: top_y = max(0, bottom_y - 50)

    # 원근 변환 좌표 설정
    margin = 10
    pts_src = np.float32([
        [margin, bottom_y],
        [actual_w - margin, bottom_y],
        [actual_w - margin, top_y],
        [margin, top_y],
    ])
    target_w, target_h = 320, 240
    pts_dst = np.float32([[0, target_h], [target_w, target_h], [target_w, 0], [0, 0]])

    # 원본 프레임에 ROI 표시
    pts = pts_src.reshape((-1, 1, 2)).astype(np.int32)
    frame_with_rect = cv2.polylines(frame.copy(), [pts], isClosed=True, color=(0, 255, 0), thickness=2)
    cv2.imshow("1_Frame", frame_with_rect)

    # 원근 변환
    mat_affine = cv2.getPerspectiveTransform(pts_src, pts_dst)
    frame_transformed = cv2.warpPerspective(frame, mat_affine, (target_w, target_h))
    cv2.imshow("2_frame_transformed", frame_transformed)

    # -------------------------------------------------------
    # [학습 포인트] Step 1: 단순 그레이스케일 변환
    # RGB 가중치 없이 단순히 색상을 흑백으로 변환합니다.
    # BGR2GRAY는 보통 0.114*B + 0.587*G + 0.299*R 공식을 사용합니다.
    # -------------------------------------------------------
    gray_frame = cv2.cvtColor(frame_transformed, cv2.COLOR_BGR2GRAY)
    cv2.imshow("3_gray_frame", gray_frame)

    # 이진화
    _, binary_frame = cv2.threshold(gray_frame, detect_value, 255, cv2.THRESH_BINARY)

    # 노이즈 제거
    kernel = np.ones((5, 5), np.uint8)
    binary_frame = cv2.morphologyEx(binary_frame, cv2.MORPH_CLOSE, kernel)
    binary_frame = cv2.morphologyEx(binary_frame, cv2.MORPH_OPEN, kernel)

    cv2.imshow("4_Processed Frame", binary_frame)
    return binary_frame

print("✅ 이미지 처리 함수 정의 완료\n")

# ============================
# 5단계: 차량 제어 함수 정의
# ============================
def car_run(speed_left, speed_right):
    bot.Ctrl_Muto(0, speed_left)
    bot.Ctrl_Muto(1, speed_left)
    bot.Ctrl_Muto(2, speed_right)
    bot.Ctrl_Muto(3, speed_right)

def car_stop():
    for i in range(4): bot.Ctrl_Muto(i, 0)

def car_left(speed_left, speed_right):
    bot.Ctrl_Muto(0, -speed_left)
    bot.Ctrl_Muto(1, -speed_left)
    bot.Ctrl_Muto(2, speed_right)
    bot.Ctrl_Muto(3, speed_right)

def car_right(speed_left, speed_right):
    bot.Ctrl_Muto(0, speed_left)
    bot.Ctrl_Muto(1, speed_left)
    bot.Ctrl_Muto(2, -speed_right)
    bot.Ctrl_Muto(3, -speed_right)

def control_car(direction, up_speed, down_speed):
    if direction == "UP":
        boosted_speed = min(up_speed + SPEED_BOOST, 255)
        car_run(boosted_speed, boosted_speed)
        if DEBUG_MODE: print(f"⚡ 직진 - 속도: {boosted_speed}")
        if USE_LED_EFFECTS: bot.Ctrl_WQ2812_ALL(1, 1) # 초록
    elif direction == "LEFT":
        car_left(down_speed - 10, up_speed + 10)
        if DEBUG_MODE: print(f"◀️  좌회전")
        if USE_LED_EFFECTS: bot.Ctrl_WQ2812_ALL(1, 3) # 노랑
    elif direction == "RIGHT":
        car_right(up_speed + 10, down_speed - 10)
        if DEBUG_MODE: print(f"▶️  우회전")
        if USE_LED_EFFECTS: bot.Ctrl_WQ2812_ALL(1, 3) # 노랑

print("✅ 차량 제어 함수 정의 완료\n")

# ============================
# 6단계: 서보 및 대체 경로 탐색
# ============================
def rotate_servo(servo_id, angle):
    if servo_id == 2 and angle > 110: angle = 110
    bot.Ctrl_Servo(servo_id, angle)

def rotate_servo_and_check_direction(detect_value, roi_top_y, roi_bottom_y):
    """대체 경로 탐색 (RGB 인자 제거됨)"""
    global cap
    if DEBUG_MODE: print("🔍 막다른 길 감지! 대체 경로 탐색 중...")

    bot.Ctrl_Servo(1, 180)
    bot.Ctrl_Servo(2, 100)
    time.sleep(0.5)

    ret, frame = cap.read()
    if not ret: return "STOP"

    processed_frame = process_frame(frame, detect_value, roi_top_y, roi_bottom_y)
    histogram_180 = np.sum(processed_frame, axis=0)
    length = len(histogram_180)

    left = int(np.sum(histogram_180[: length // 3]))
    center = int(np.sum(histogram_180[length // 3 : 2 * length // 3]))
    right = int(np.sum(histogram_180[2 * length // 3 :]))

    # 서보 원위치
    servo_1_angle = cv2.getTrackbarPos("Servo 1 Angle", "Camera Settings")
    servo_2_angle = cv2.getTrackbarPos("Servo 2 Angle", "Camera Settings")
    bot.Ctrl_Servo(1, servo_1_angle)
    bot.Ctrl_Servo(2, servo_2_angle)
    time.sleep(0.3)

    if left > center and right > center:
        return "RIGHT"
    return "LEFT"

# ============================
# 7단계: 방향 결정 함수
# ============================
def decide_direction(histogram, direction_threshold, up_threshold, detect_value, roi_top_y, roi_bottom_y):
    """방향 결정 (RGB 인자 제거됨)"""
    length = len(histogram)
    DIVIDE = 6
    
    left = int(np.sum(histogram[: length // DIVIDE]))
    right = int(np.sum(histogram[(DIVIDE - 1) * length // DIVIDE :]))
    center_left = int(np.sum(histogram[1 * length // DIVIDE : 3 * length // DIVIDE]))
    center_right = int(np.sum(histogram[3 * length // DIVIDE : 5 * length // DIVIDE]))

    if DEBUG_MODE:
        print(f"L: {left} | R: {right} | Diff: {abs(right-left)}")

    if abs(right - left) > direction_threshold:
        return "LEFT" if right > left else "RIGHT"

    center_diff = abs(center_left - center_right)
    if center_diff < up_threshold:
        car_stop()
        time.sleep(0.3)
        return rotate_servo_and_check_direction(detect_value, roi_top_y, roi_bottom_y)

    return "UP"

# ============================
# 8단계: 메인 루프
# ============================
print("=" * 50)
print("  🚀 수업용 Basic Mode 시작")
print("  (RGB 필터가 비활성화된 상태입니다)")
print("=" * 50)

frame_count = 0
start_time = time.time()
led_state = LED_ON_START

try:
    while True:
        frame_count += 1

        # 트랙바 값 읽기 (RGB Weight 제거됨)
        brightness = cv2.getTrackbarPos("Brightness", "Camera Settings")
        contrast = cv2.getTrackbarPos("Contrast", "Camera Settings")
        detect_value = cv2.getTrackbarPos("Detect Value", "Camera Settings")
        motor_up_speed = cv2.getTrackbarPos("Motor Up Speed", "Camera Settings")
        motor_down_speed = cv2.getTrackbarPos("Motor Down Speed", "Camera Settings")
        servo_1_angle = cv2.getTrackbarPos("Servo 1 Angle", "Camera Settings")
        servo_2_angle = cv2.getTrackbarPos("Servo 2 Angle", "Camera Settings")
        roi_top_y = cv2.getTrackbarPos("ROI Top Y", "Camera Settings")
        roi_bottom_y = cv2.getTrackbarPos("ROI Bottom Y", "Camera Settings")
        direction_threshold = cv2.getTrackbarPos("Direction Threshold", "Camera Settings")
        up_threshold = cv2.getTrackbarPos("Up Threshold", "Camera Settings")

        # 카메라 설정 적용
        cap.set(cv2.CAP_PROP_BRIGHTNESS, brightness)
        cap.set(cv2.CAP_PROP_CONTRAST, contrast)

        ret, frame = cap.read()
        if not ret: break

        rotate_servo(1, servo_1_angle)
        rotate_servo(2, servo_2_angle)

        # 이미지 처리 (RGB 인자 전달하지 않음)
        processed_frame = process_frame(frame, detect_value, roi_top_y, roi_bottom_y)
        histogram = np.sum(processed_frame, axis=0)

        direction = decide_direction(
            histogram, direction_threshold, up_threshold, 
            detect_value, roi_top_y, roi_bottom_y
        )
        control_car(direction, motor_up_speed, motor_down_speed)

        # 키 입력
        key = cv2.waitKey(30) & 0xFF
        if key == 27: break
        elif key == 32:
            car_stop()
            cv2.waitKey()
        elif key == ord("l"):
            led_state = not led_state
            bot.Ctrl_WQ2812_ALL(1, 2) if led_state else bot.Ctrl_WQ2812_ALL(0, 0)
        elif key == ord("b"):
            bot.Ctrl_BEEP_Switch(1)
            time.sleep(0.1)
            bot.Ctrl_BEEP_Switch(0)

except KeyboardInterrupt:
    print("\n⚠️  중단됨")
finally:
    car_stop()
    bot.Ctrl_WQ2812_ALL(0, 0)
    bot.Ctrl_BEEP_Switch(0)
    bot.Ctrl_Servo(1, 90)
    bot.Ctrl_Servo(2, 25)
    cap.release()
    cv2.destroyAllWindows()
    del bot
    print("\n✅ 종료 완료")

