#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspbot v2 Haar Cascade 멀티스레드 기반 자율주행 코드
카메라 캡처와 이미지 처리를 분리한 멀티스레드 버전

Copyright (C): 2015-2024, Shenzhen Yahboom Tech
Modified: 2025-11-25

═══════════════════════════════════════════════════════════
주요 특징:
═══════════════════════════════════════════════════════════
- 카메라 캡처와 이미지 처리를 별도 스레드로 분리
- Haar Cascade 분류기 기반 객체 검출
- 통행금지 표지판 하단/상단 검출
- 정지 표지판 검출
- 멀티스레드 병렬 처리로 성능 향상
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
9단계: 표지판 검출 함수 정의 (멀티스레드)
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
import time
import RPi.GPIO as GPIO
import random
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
no_drive_bottom_cascade_path = "./xml/obstacle.xml"
no_drive_top_cascade_path = "./xml/stop.xml"
stop_cascade_path = "./xml/no_drive.xml"

# Haar Cascade models 로드
no_drive_bottom_cascade = cv2.CascadeClassifier(no_drive_bottom_cascade_path)
no_drive_top_cascade = cv2.CascadeClassifier(no_drive_top_cascade_path)
stop_cascade = cv2.CascadeClassifier(stop_cascade_path)

if no_drive_bottom_cascade.empty():
    print("⚠️  경고: obstacle.xml을 찾을 수 없습니다.")
if no_drive_top_cascade.empty():
    print("⚠️  경고: stop.xml을 찾을 수 없습니다.")
if stop_cascade.empty():
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
    """
    가중 그레이스케일 변환

    처리 단계:
    1. RGB 채널별 가중치 정규화
    2. 가중 합산으로 그레이스케일 생성
    """
    sum_weight = r_weight + g_weight + b_weight
    r_weight /= sum_weight
    g_weight /= sum_weight
    b_weight /= sum_weight

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
    1. ROI 영역 정의
    2. 원본 프레임에 ROI 사각형 표시
    3. 원근 변환 적용
    4. 그레이스케일 변환
    5. 이진화
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
        frame.copy(), [pts], isClosed=True, color=(0, 0, 255), thickness=2
    )
    cv2.imshow("1_Frame", frame_with_rect)

    mat_affine = cv2.getPerspectiveTransform(pts_src, pts_dst)
    frame_transformed = cv2.warpPerspective(frame, mat_affine, (target_w, target_h))
    cv2.imshow("2_frame_transformed", frame_transformed)

    gray_frame = weighted_gray(frame_transformed, r_weight, g_weight, b_weight)
    cv2.imshow("3_gray_frame", gray_frame)

    _, binary_frame = cv2.threshold(gray_frame, detect_value, 255, cv2.THRESH_BINARY)

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


def decide_direction(histogram, direction_threshold):
    """
    히스토그램 기반 방향 결정

    처리 단계:
    1. 히스토그램을 5개 구역으로 분할
    2. 좌우 영역 비교
    3. 좌우 차이가 크면 회전
    4. 그 외 직진
    """
    length = len(histogram)

    # 1. 구역 분할 (5등분)
    left = int(np.sum(histogram[: length // 5]))
    right = int(np.sum(histogram[4 * length // 5 :]))

    if DEBUG_MODE:
        print(f"left: {left}, right: {right}, right - left: {right - left}")

    # 2. 좌우 차이 확인
    if abs(right - left) > direction_threshold:
        return "LEFT" if right > left else "RIGHT"
    else:
        return "UP"


print("✅ 방향 결정 함수 정의 완료\n")

# ============================
# 9단계: 표지판 검출 함수 정의 (멀티스레드)
# ============================
print("=" * 50)
print("  🚦 9단계: 표지판 검출 함수 정의 (멀티스레드)")
print("=" * 50)


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


def draw_rectangles_and_text(frame, traffic_sign, sign_name):
    """
    검출된 표지판에 사각형 및 텍스트 그리기

    처리 단계:
    1. 각 표지판에 사각형 그리기
    2. 표지판 이름 및 크기 정보 표시
    """
    for x, y, w, h in traffic_sign:
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
    return frame


def detect_no_drive_bottom(frame, control_signals, r_weight, g_weight, b_weight):
    """
    통행금지 표지판 하단 검출 함수

    처리 단계:
    1. 그레이스케일 변환
    2. Haar Cascade로 하단 표지판 검출
    3. 검출 시 서보 모터 회전하여 상단 표지판 확인
    4. 검출 결과를 control_signals에 저장
    """
    if no_drive_bottom_cascade.empty():
        print("⚠️  통행금지 하단 분류기 로딩 실패")
        return

    gray = weighted_gray(frame, r_weight, g_weight, b_weight)
    no_drive_bottom = no_drive_bottom_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5
    )

    control_signals["no_drive_bottom"] = len(no_drive_bottom) > 0
    if control_signals["no_drive_bottom"]:
        draw_rectangles_and_text(frame, no_drive_bottom, "no_drive_bottom")
        # 서보 모터 2를 85도로 회전하여 카메라 각도 조절
        rotate_servo(2, 85)
        time.sleep(1)
        # 카메라로부터 새로운 프레임을 받아옴
        ret, new_frame = cap.read()
        if ret:
            no_drive_top(new_frame, control_signals, r_weight, g_weight, b_weight)
    else:
        control_signals["no_drive_bottom"] = False


def no_drive_top(frame, control_signals, r_weight, g_weight, b_weight):
    """
    통행금지 표지판 상단 검출 함수

    처리 단계:
    1. 그레이스케일 변환
    2. Haar Cascade로 상단 표지판 검출
    3. 검출 시 차량 정지 및 부저 알림
    4. 검출 결과를 control_signals에 저장
    """
    if no_drive_top_cascade.empty():
        print("⚠️  통행금지 상단 분류기 로딩 실패")
        return

    gray = weighted_gray(frame, r_weight, g_weight, b_weight)
    no_drive_top = no_drive_top_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5
    )

    control_signals["no_drive_top"] = len(no_drive_top) > 0
    if control_signals["no_drive_top"]:
        draw_rectangles_and_text(frame, no_drive_top, "no_drive_top")
        car_stop()
        beep_sound()
    else:
        control_signals["no_drive_bottom"] = False
        control_signals["no_drive_top"] = False


def detect_stop_sign(frame, control_signals, r_weight, g_weight, b_weight):
    """
    정지 표지판 검출 함수

    처리 단계:
    1. 그레이스케일 변환
    2. Haar Cascade로 정지 표지판 검출
    3. 검출 시 차량 정지
    4. 검출 결과를 control_signals에 저장
    """
    if stop_cascade.empty():
        print("⚠️  정지 표지판 분류기 로딩 실패")
        return

    gray = weighted_gray(frame, r_weight, g_weight, b_weight)
    stop_signs = stop_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    control_signals["stop"] = len(stop_signs) > 0
    if control_signals["stop"]:
        draw_rectangles_and_text(frame, stop_signs, "stop_signs")
        car_stop()
        time.sleep(0.5)
    else:
        control_signals["stop"] = False


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
control_signals = {"no_drive_bottom": False, "no_drive_top": False, "stop": False}

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

        direction = decide_direction(histogram, direction_threshold)

        if DEBUG_MODE:
            print(f"#### 결정된 방향 ####: {direction}")

        # 표지판 검출 (멀티스레드)
        detect_no_drive_bottom_thread = threading.Thread(
            target=detect_no_drive_bottom,
            args=(frame, control_signals, r_weight, g_weight, b_weight),
        )
        detect_stop_sign_thread = threading.Thread(
            target=detect_stop_sign,
            args=(frame, control_signals, r_weight, g_weight, b_weight),
        )

        detect_no_drive_bottom_thread.start()
        detect_stop_sign_thread.start()

        # 스레드 완료 대기
        detect_no_drive_bottom_thread.join()
        detect_stop_sign_thread.join()

        time.sleep(0.1)

        # 표지판에 따른 제어
        if (
            control_signals["no_drive_bottom"]
            or control_signals["no_drive_top"]
            or control_signals["stop"]
        ):
            if DEBUG_MODE:
                print("🚦 표지판 검출! 정지 중...")
        else:
            if DEBUG_MODE:
                print("✅ 표지판 없음. 자율주행 계속.")
            control_car(direction, motor_up_speed, motor_down_speed)

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
