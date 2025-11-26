#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspbot v2 Haar Cascade 기반 자율주행 코드
Haar Cascade 분류기를 사용한 표지판 및 장애물 검출

Copyright (C): 2015-2024, Shenzhen Yahboom Tech
Modified: 2025-11-25

═══════════════════════════════════════════════════════════
주요 특징:
═══════════════════════════════════════════════════════════
- Haar Cascade 분류기 기반 객체 검출
- 장애물, 정지 표지판, 통행금지 표지판 검출
- 표지판 검출 시 자동 정지 및 부저 알림
- 스레드를 사용한 병렬 검출 처리
- 단계별 주석으로 실행 흐름 명확화

═══════════════════════════════════════════════════════════
실행 단계:
═══════════════════════════════════════════════════════════
1단계: 라이브러리 및 모듈 import
2단계: 하드웨어 초기화 (Raspbot, 카메라, 서보)
3단계: Haar Cascade 분류기 로딩
4단계: 트랙바 및 윈도우 설정
5단계: 이미지 처리 함수 정의
6단계: 차량 제어 함수 정의
7단계: 서보 모터 제어 함수 정의
8단계: 방향 결정 함수 정의
9단계: 표지판 검출 함수 정의
10단계: 메인 루프 실행
11단계: 정리 및 종료
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
import threading
import random
import time
import RPi.GPIO as GPIO
from Raspbot_Lib import Raspbot

print("✅ 라이브러리 로딩 완료\n")

# ============================
# 사용자 설정 영역
# ============================
print("=" * 50)
print("  ⚙️  설정 값 로딩 중...")
print("=" * 50)

# 기본 속도 설정
DEFAULT_SPEED_UP = 20
DEFAULT_SPEED_DOWN = 10
SPEED_BOOST = 15

# 라인 검출 설정
DEFAULT_DETECT_VALUE = 120
DEFAULT_BRIGHTNESS = 0
DEFAULT_CONTRAST = 40

# RGB 가중치
DEFAULT_R_WEIGHT = 30
DEFAULT_G_WEIGHT = 40
DEFAULT_B_WEIGHT = 60

# 방향 판단 임계값
DEFAULT_DIRECTION_THRESHOLD = 35000
DEFAULT_UP_THRESHOLD = 220000

# 서보 모터 각도
DEFAULT_SERVO_1 = 90
DEFAULT_SERVO_2 = 25

# 디버그 모드
DEBUG_MODE = True

# LED 효과 사용
USE_LED_EFFECTS = True
LED_ON_START = True

# 부저 사용
USE_BEEP = True
BEEP_ON_START = True

print("✅ 설정 값 로딩 완료\n")

# ============================
# 2단계: 하드웨어 초기화
# ============================
print("=" * 50)
print("  🔧 2단계: 하드웨어 초기화 중...")
print("=" * 50)

try:
    bot = Raspbot()
    print("✅ Raspbot 하드웨어 초기화 완료")
except Exception as e:
    print(f"❌ Raspbot 초기화 실패: {e}")
    sys.exit(1)

try:
    print("\n📹 카메라 초기화 중...")
    cap = cv2.VideoCapture(0)

    width = 320
    height = 240
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_BRIGHTNESS, DEFAULT_BRIGHTNESS)
    cap.set(cv2.CAP_PROP_CONTRAST, DEFAULT_CONTRAST)
    cap.set(cv2.CAP_PROP_SATURATION, 50)
    cap.set(cv2.CAP_PROP_EXPOSURE, 100)

    ret, frame = cap.read()
    if not ret or frame is None:
        raise Exception("카메라에서 프레임을 읽을 수 없습니다")

    actual_height, actual_width = frame.shape[:2]
    print(f"✅ USB 카메라 초기화 완료")
    print(f"   - 요청 해상도: {width}x{height}")
    print(f"   - 실제 해상도: {actual_width}x{actual_height}")

except Exception as e:
    print(f"\n❌ 카메라 초기화 실패: {e}\n")
    del bot
    sys.exit(1)

if LED_ON_START and USE_LED_EFFECTS:
    bot.Ctrl_WQ2812_ALL(1, 2)
    print("💡 LED 초기화 완료")

if BEEP_ON_START and USE_BEEP:
    bot.Ctrl_BEEP_Switch(1)
    time.sleep(0.2)
    bot.Ctrl_BEEP_Switch(0)
    print("🔊 부저 테스트 완료")

# 서보 모터 초기 위치
bot.Ctrl_Servo(1, DEFAULT_SERVO_1)
bot.Ctrl_Servo(2, DEFAULT_SERVO_2)
print(f"📷 서보 모터 초기화 완료 (S1:{DEFAULT_SERVO_1}°, S2:{DEFAULT_SERVO_2}°)")

for i in range(4):
    bot.Ctrl_Muto(i, 0)
print("🛑 모터 정지 상태로 초기화 완료\n")

# ============================
# 3단계: Haar Cascade 분류기 로딩
# ============================
print("=" * 50)
print("  🔍 3단계: Haar Cascade 분류기 로딩 중...")
print("=" * 50)

# Haar Cascade models 경로 설정
obstacle_cascade_path = "./xml/obstacle.xml"
stop_cascade_path = "./xml/stop.xml"
no_drive_cascade_path = "./xml/no_drive.xml"

# Haar Cascade models 로드
obstacle_cascade = cv2.CascadeClassifier(obstacle_cascade_path)
stop_cascade = cv2.CascadeClassifier(stop_cascade_path)
no_drive_cascade = cv2.CascadeClassifier(no_drive_cascade_path)

if obstacle_cascade.empty():
    print("⚠️  경고: obstacle.xml을 찾을 수 없습니다.")
if stop_cascade.empty():
    print("⚠️  경고: stop.xml을 찾을 수 없습니다.")
if no_drive_cascade.empty():
    print("⚠️  경고: no_drive.xml을 찾을 수 없습니다.")

print("✅ Haar Cascade 분류기 로딩 완료\n")

# ============================
# 4단계: 트랙바 및 윈도우 설정
# ============================
print("=" * 50)
print("  🎛️  4단계: 트랙바 및 윈도우 설정 중...")
print("=" * 50)


def nothing(x):
    """트랙바 콜백 함수"""
    pass


# 윈도우 생성 (크기 조절 가능)
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

# 이미지 처리 트랙바
cv2.createTrackbar("ROI Top Y", "Camera Settings", 0, 1000, nothing)
cv2.createTrackbar("ROI Bottom Y", "Camera Settings", 800, 1000, nothing)
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
cv2.createTrackbar("Brightness", "Camera Settings", DEFAULT_BRIGHTNESS, 100, nothing)
cv2.createTrackbar("Contrast", "Camera Settings", DEFAULT_CONTRAST, 100, nothing)
cv2.createTrackbar(
    "Detect Value", "Camera Settings", DEFAULT_DETECT_VALUE, 150, nothing
)
cv2.createTrackbar("Motor Up Speed", "Camera Settings", DEFAULT_SPEED_UP, 255, nothing)
cv2.createTrackbar(
    "Motor Down Speed", "Camera Settings", DEFAULT_SPEED_DOWN, 255, nothing
)
cv2.createTrackbar("R_weight", "Camera Settings", DEFAULT_R_WEIGHT, 100, nothing)
cv2.createTrackbar("G_weight", "Camera Settings", DEFAULT_G_WEIGHT, 100, nothing)
cv2.createTrackbar("B_weight", "Camera Settings", DEFAULT_B_WEIGHT, 100, nothing)
cv2.createTrackbar("Saturation", "Camera Settings", 20, 100, nothing)
cv2.createTrackbar("Gain", "Camera Settings", 20, 100, nothing)

print("✅ 트랙바 및 윈도우 설정 완료\n")

# ============================
# 5단계: 이미지 처리 함수 정의
# ============================
print("=" * 50)
print("  🖼️  5단계: 이미지 처리 함수 정의")
print("=" * 50)


def weighted_gray(image, r_weight, g_weight, b_weight):
    """가중 그레이스케일 변환"""
    r_weight /= 100.0
    g_weight /= 100.0
    b_weight /= 100.0
    return cv2.addWeighted(
        cv2.addWeighted(image[:, :, 2], r_weight, image[:, :, 1], g_weight, 0),
        1.0,
        image[:, :, 0],
        b_weight,
        0,
    )


def process_frame(
    frame, detect_value, r_weight, g_weight, b_weight, roi_top_y, roi_bottom_y
):
    """
    프레임 처리 및 엣지 검출

    처리 단계:
    1. 실제 해상도 확인
    2. ROI 영역 정의
    3. 원본 프레임에 ROI 사각형 표시
    4. 원근 변환 적용
    5. 그레이스케일 변환
    6. 이진화
    7. 노이즈 제거
    """
    actual_h, actual_w = frame.shape[:2]

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

    target_w, target_h = 320, 240
    pts_dst = np.float32([[0, target_h], [target_w, target_h], [target_w, 0], [0, 0]])

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
    cv2.imshow("1_Frame", frame_with_rect)

    mat_affine = cv2.getPerspectiveTransform(pts_src, pts_dst)
    frame_transformed = cv2.warpPerspective(frame, mat_affine, (target_w, target_h))
    cv2.imshow("2_frame_transformed", frame_transformed)

    gray_frame = weighted_gray(frame_transformed, r_weight, g_weight, b_weight)
    cv2.imshow("3_gray_frame", gray_frame)

    _, binary_frame = cv2.threshold(gray_frame, detect_value, 255, cv2.THRESH_BINARY)

    kernel = np.ones((5, 5), np.uint8)
    binary_frame = cv2.morphologyEx(binary_frame, cv2.MORPH_CLOSE, kernel)
    binary_frame = cv2.morphologyEx(binary_frame, cv2.MORPH_OPEN, kernel)

    cv2.imshow("4_Processed Frame", binary_frame)
    return binary_frame


print("✅ 이미지 처리 함수 정의 완료\n")

# ============================
# 6단계: 차량 제어 함수 정의
# ============================
print("=" * 50)
print("  🚗 6단계: 차량 제어 함수 정의")
print("=" * 50)


def car_run(speed_left, speed_right):
    """전진"""
    bot.Ctrl_Muto(0, speed_left)
    bot.Ctrl_Muto(1, speed_left)
    bot.Ctrl_Muto(2, speed_right)
    bot.Ctrl_Muto(3, speed_right)


def car_stop():
    """정지"""
    for i in range(4):
        bot.Ctrl_Muto(i, 0)


def car_left(speed_left, speed_right):
    """좌회전"""
    bot.Ctrl_Muto(0, -speed_left)
    bot.Ctrl_Muto(1, -speed_left)
    bot.Ctrl_Muto(2, speed_right)
    bot.Ctrl_Muto(3, speed_right)


def car_right(speed_left, speed_right):
    """우회전"""
    bot.Ctrl_Muto(0, speed_left)
    bot.Ctrl_Muto(1, speed_left)
    bot.Ctrl_Muto(2, -speed_right)
    bot.Ctrl_Muto(3, -speed_right)


def control_car(direction, up_speed, down_speed):
    """차량 제어"""
    if direction == "UP":
        boosted_speed = min(up_speed + SPEED_BOOST, 255)
        car_run(boosted_speed, boosted_speed)
        if DEBUG_MODE:
            print(f"⚡ 직진 - 속도: {boosted_speed}")
        if USE_LED_EFFECTS:
            bot.Ctrl_WQ2812_ALL(1, 1)
    elif direction == "LEFT":
        car_left(down_speed, up_speed)
        if DEBUG_MODE:
            print(f"◀️  좌회전")
        if USE_LED_EFFECTS:
            bot.Ctrl_WQ2812_ALL(1, 3)
    elif direction == "RIGHT":
        car_right(up_speed, down_speed)
        if DEBUG_MODE:
            print(f"▶️  우회전")
        if USE_LED_EFFECTS:
            bot.Ctrl_WQ2812_ALL(1, 3)
    elif direction == "RANDOM":
        random_direction = random.choice(["LEFT", "RIGHT"])
        control_car(random_direction, up_speed, down_speed)


print("✅ 차량 제어 함수 정의 완료\n")

# ============================
# 7단계: 서보 모터 제어 함수 정의
# ============================
print("=" * 50)
print("  📷 7단계: 서보 모터 제어 함수 정의")
print("=" * 50)


def rotate_servo(servo_id, angle):
    """서보 모터 회전"""
    if servo_id == 2 and angle > 110:
        angle = 110
    bot.Ctrl_Servo(servo_id, angle)


print("✅ 서보 모터 제어 함수 정의 완료\n")

# ============================
# 8단계: 방향 결정 함수 정의
# ============================
print("=" * 50)
print("  🧭 8단계: 방향 결정 함수 정의")
print("=" * 50)


def decide_direction(histogram, direction_threshold, up_threshold):
    """
    히스토그램 기반 방향 결정

    처리 단계:
    1. 히스토그램을 6개 구역으로 분할
    2. 좌우 영역 비교
    3. 좌우 차이가 크면 회전
    4. 중앙 막힘 시 무작위 방향 선택
    5. 그 외 직진
    """
    length = len(histogram)
    DIVIDE = 6

    left = int(np.sum(histogram[: length // DIVIDE]))
    right = int(np.sum(histogram[(DIVIDE - 1) * length // DIVIDE :]))
    center_left = int(np.sum(histogram[1 * length // DIVIDE : 3 * length // DIVIDE]))
    center_right = int(np.sum(histogram[3 * length // DIVIDE : 5 * length // DIVIDE]))

    if DEBUG_MODE:
        print(f"left: {left}, right: {right}, right - left: {right - left}")

    if abs(right - left) > direction_threshold:
        return "LEFT" if right > left else "RIGHT"

    center = abs(center_left - center_right)

    if DEBUG_MODE:
        print(
            f"center: {center} --- up_threshold: {up_threshold} RANDOM: {center < up_threshold}"
        )

    if center > up_threshold:
        return "UP"

    return "RANDOM"


print("✅ 방향 결정 함수 정의 완료\n")

# ============================
# 9단계: 표지판 검출 함수 정의
# ============================
print("=" * 50)
print("  🚦 9단계: 표지판 검출 함수 정의")
print("=" * 50)


def draw_rectangles_and_text(frame, rect_sign, sign_name):
    """
    검출된 표지판에 사각형 및 텍스트 그리기

    처리 단계:
    1. 각 표지판에 사각형 그리기
    2. 표지판 이름 및 크기 정보 표시
    3. 별도 윈도우에 표시
    """
    for x, y, w, h in rect_sign:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
        cv2.putText(
            frame,
            f"{sign_name}_({w}X{h})",
            (x - 30, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2,
        )
        cv2.imshow(f"{sign_name}:", frame)


def detect_obstacle(frame, control_signals, event, r_weight, g_weight, b_weight):
    """
    장애물 검출 함수

    처리 단계:
    1. 그레이스케일 변환
    2. Haar Cascade로 장애물 검출
    3. 검출 결과를 control_signals에 저장
    4. 장애물 검출 시 서보 모터 회전하여 통행금지 표지판 확인
    5. 이벤트 신호 전송
    """
    if obstacle_cascade.empty():
        print("⚠️  장애물 분류기 로딩 실패")
        event.set()
        return

    gray = weighted_gray(frame, r_weight, g_weight, b_weight)
    obstacles = obstacle_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    for x, y, w, h in obstacles:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    control_signals["obstacle"] = len(obstacles) > 0
    if control_signals["obstacle"]:
        draw_rectangles_and_text(frame, obstacles, "obstacles")
        # 서보 모터 2를 85도로 회전하여 카메라 각도 조절
        rotate_servo(2, 85)
        time.sleep(1)
        # 카메라로부터 새로운 프레임을 받아옴
        ret, new_frame = cap.read()
        if ret:
            no_drive_sign(new_frame, control_signals, r_weight, g_weight, b_weight)

    event.set()


def no_drive_sign(frame, control_signals, r_weight, g_weight, b_weight):
    """
    통행금지 표지판 검출 함수

    처리 단계:
    1. 그레이스케일 변환
    2. Haar Cascade로 통행금지 표지판 검출
    3. 검출 결과를 control_signals에 저장
    """
    if no_drive_cascade.empty():
        print("⚠️  통행금지 분류기 로딩 실패")
        return

    gray = weighted_gray(frame, r_weight, g_weight, b_weight)
    no_drive_signs = no_drive_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5
    )
    control_signals["no_drive"] = len(no_drive_signs) > 0
    if control_signals["no_drive"]:
        draw_rectangles_and_text(frame, no_drive_signs, "no_drive_cascade")


def stop_sign(frame, control_signals, event, r_weight, g_weight, b_weight):
    """
    정지 표지판 검출 함수

    처리 단계:
    1. 그레이스케일 변환
    2. Haar Cascade로 정지 표지판 검출
    3. 검출 결과를 control_signals에 저장
    4. 이벤트 신호 전송
    """
    if stop_cascade.empty():
        print("⚠️  정지 표지판 분류기 로딩 실패")
        event.set()
        return

    gray = weighted_gray(frame, r_weight, g_weight, b_weight)
    stop_signs = stop_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    control_signals["stop"] = len(stop_signs) > 0
    if control_signals["stop"]:
        draw_rectangles_and_text(frame, stop_signs, "stop_signs")

    event.set()


def beep_sound():
    """
    부저 소리 출력 함수

    처리 단계:
    1. GPIO 설정
    2. PWM으로 부저 제어
    3. GPIO 정리
    """
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(32, GPIO.OUT)
    p = GPIO.PWM(32, 440)
    p.start(50)
    time.sleep(0.5)
    p.stop()
    GPIO.cleanup()


print("✅ 표지판 검출 함수 정의 완료\n")

# ============================
# 10단계: 메인 루프 실행
# ============================
print("=" * 50)
print("  🚀 10단계: 메인 루프 시작")
print("=" * 50)
print("Controls:")
print("  ESC   : 종료")
print("  SPACE : 일시정지")
print("  'l'   : LED 토글")
print("=" * 50)

frame_count = 0
start_time = time.time()
led_state = LED_ON_START
control_signals = {"obstacle": False, "no_drive": False, "stop": False}

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

        # 프레임 읽기
        ret, frame = cap.read()
        if not ret:
            print("❌ 카메라에서 프레임을 읽을 수 없습니다.")
            break

        # 서보 모터 각도 조절
        rotate_servo(1, servo_1_angle)
        rotate_servo(2, servo_2_angle)

        # 프레임 처리
        processed_frame = process_frame(
            frame, detect_value, r_weight, g_weight, b_weight, roi_top_y, roi_bottom_y
        )
        histogram = np.sum(processed_frame, axis=0)

        # 방향 결정 및 제어
        if DEBUG_MODE:
            print(f"\n--- Frame {frame_count} ---")

        direction = decide_direction(histogram, direction_threshold, up_threshold)

        if DEBUG_MODE:
            print(f"#### 결정된 방향 ####: {direction}")

        control_car(direction, motor_up_speed, motor_down_speed)

        # 표지판 검출 (스레드 사용)
        obstacle_event = threading.Event()
        stop_sign_event = threading.Event()

        detect_obstacle_thread = threading.Thread(
            target=detect_obstacle,
            args=(frame, control_signals, obstacle_event, r_weight, g_weight, b_weight),
        )
        stop_sign_thread = threading.Thread(
            target=stop_sign,
            args=(
                frame,
                control_signals,
                stop_sign_event,
                r_weight,
                g_weight,
                b_weight,
            ),
        )

        detect_obstacle_thread.start()
        stop_sign_thread.start()

        # 스레드 완료 대기
        obstacle_event.wait()
        stop_sign_event.wait()

        # 표지판에 따른 제어
        if control_signals["obstacle"]:
            if DEBUG_MODE:
                print("🚧 장애물 검출! 회피 중...")
        elif control_signals["no_drive"]:
            if DEBUG_MODE:
                print("🚫 통행금지 표지판 검출! 정지 중...")
            rotate_servo(2, 75)
            time.sleep(0.8)
            beep_sound()
            car_stop()
        elif control_signals["stop"]:
            if DEBUG_MODE:
                print("🛑 정지 표지판 검출! 정지 중...")
            car_stop()

        # FPS 계산
        if frame_count % 10 == 0:
            elapsed = time.time() - start_time
            fps = 10 / elapsed
            if DEBUG_MODE:
                print(f"📊 FPS: {fps:.1f}")
            start_time = time.time()

        # 키 입력 처리
        key = cv2.waitKey(30) & 0xFF
        if key == 27:
            print("\n🛑 종료 중...")
            break
        elif key == 32:
            print("\n⏸️  일시정지. 아무 키나 누르세요.")
            car_stop()
            cv2.waitKey()
        elif key == ord("l"):
            led_state = not led_state
            if led_state:
                bot.Ctrl_WQ2812_ALL(1, 2)
                print("💡 LED ON")
            else:
                bot.Ctrl_WQ2812_ALL(0, 0)
                print("💡 LED OFF")

        time.sleep(0.05)

except KeyboardInterrupt:
    print("\n⚠️  사용자에 의해 중단됨")
except Exception as e:
    print(f"\n❌ 오류 발생: {e}")
    import traceback

    traceback.print_exc()

# ============================
# 11단계: 정리 및 종료
# ============================
finally:
    print("\n" + "=" * 50)
    print("  🧹 11단계: 정리 및 종료")
    print("=" * 50)

    car_stop()
    print("✅ 모터 정지")

    if USE_LED_EFFECTS:
        bot.Ctrl_WQ2812_ALL(0, 0)
        print("✅ LED 끄기")

    bot.Ctrl_BEEP_Switch(0)

    # 서보 모터 초기 위치
    bot.Ctrl_Servo(1, 90)
    bot.Ctrl_Servo(2, 25)
    print("✅ 서보 모터 초기 위치로 복귀")

    cap.release()
    cv2.destroyAllWindows()
    print("✅ 카메라 해제")

    del bot
    print("✅ Raspbot 객체 삭제")

    print("\n✅ 모든 정리 완료!")
