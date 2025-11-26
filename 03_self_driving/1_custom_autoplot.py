#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspbot v2 자율주행 코드 (최신 버전)
02_Basic 예제를 기반으로 올바른 하드웨어 제어 방식 적용

Copyright (C): 2015-2024, Shenzhen Yahboom Tech
Modified: 2025-11-25

주요 변경사항:
1. Raspbot_Lib 라이브러리 사용 (YB_Pcb_Car 대신)
2. 올바른 모터 제어 방식 (Ctrl_Muto)
3. 서보 모터 각도 범위 수정 (Servo 2: 0~110)
4. 부저, LED 기능 통합
5. 향상된 에러 처리
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
SPEED_BOOST = 15  # 직진 시 추가 속도

# 라인 검출 설정
DEFAULT_DETECT_VALUE = 80  # 기본값: 80 (밝은 환경용 - 높게 설정)
DEFAULT_BRIGHTNESS = 0  # 기본값: 0 (카메라 밝기 - 낮게)
DEFAULT_CONTRAST = 40  # 기본값: 40 (카메라 대비 - 중간)

# RGB 가중치 (흰색 라인 검출 최적화 - 밝은 환경용)
DEFAULT_R_WEIGHT = 30  # 기본값: 30 (빨강 가중치 낮춤)
DEFAULT_G_WEIGHT = 40  # 기본값: 40 (초록 중간)
DEFAULT_B_WEIGHT = 60  # 기본값: 60 (파랑 가중치 높임)

# 방향 판단 임계값
DEFAULT_DIRECTION_THRESHOLD = 35000  # 기본값: 35000
DEFAULT_UP_THRESHOLD = 220000  # 기본값: 220000

# 서보 모터 각도
DEFAULT_SERVO_1 = 90  # 좌우 각도 (0~180)
DEFAULT_SERVO_2 = 25  # 상하 각도 (0~110, 기본값 25)

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
    print("✅ Raspbot 하드웨어 초기화 완료")
except Exception as e:
    print(f"❌ Raspbot 초기화 실패: {e}")
    sys.exit(1)

# 카메라 초기화 (07_Camera_Driving.ipynb 방식)
try:
    print("🔍 USB 카메라 초기화 중...")

    # 카메라 열기 (Open the camera /dev/video0)
    cap = cv2.VideoCapture(0)

    # 해상도 설정 (Set the image width and height)
    width = 320
    height = 240
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)  # 명확한 속성 사용
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    # ⚠️ 밝기 조절 (화면이 너무 밝은 경우 - 낮은 값으로 시작)
    cap.set(cv2.CAP_PROP_BRIGHTNESS, 0)  # 밝기: -64 ~ 64 (기본: 0, 낮게 시작)
    cap.set(cv2.CAP_PROP_CONTRAST, 40)  # 대비: -64 ~ 64 (대비 높임)
    cap.set(cv2.CAP_PROP_SATURATION, 50)  # 채도: 0 ~ 100
    cap.set(cv2.CAP_PROP_EXPOSURE, 100)  # 노출: 1.0 ~ 5000 (낮게 설정)

    print(f"📹 카메라 설정:")
    print(f"   - 해상도: {width}x{height}")
    print(f"   - 밝기: 0 (어두운 환경용)")
    print(f"   - 대비: 40")
    print(f"   - 노출: 100 (낮음)")

    # 추가 설정 (필요시 활성화)
    # cap.set(cv2.CAP_PROP_FPS, 30)  # 프레임레이트 설정
    # cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))

    # 카메라 정상 동작 확인 (Reading camera data)
    ret, frame = cap.read()
    if not ret or frame is None:
        raise Exception("카메라에서 프레임을 읽을 수 없습니다")

    # 실제 해상도 확인
    actual_height, actual_width = frame.shape[:2]
    print(f"✅ USB 카메라 초기화 완료")
    print(f"   - 요청 해상도: {width}x{height}")
    print(f"   - 실제 해상도: {actual_width}x{actual_height}")

    # 실제 카메라 설정 값 확인
    print(f"   - 실제 밝기: {int(cap.get(cv2.CAP_PROP_BRIGHTNESS))}")
    print(f"   - 실제 대비: {int(cap.get(cv2.CAP_PROP_CONTRAST))}")
    print(f"   - 실제 노출: {int(cap.get(cv2.CAP_PROP_EXPOSURE))}")

    if actual_width != width or actual_height != height:
        print(f"⚠️  경고: 해상도가 다릅니다. 트랙바에서 'Y Value'를 조절하세요.")

except Exception as e:
    print(f"\n❌ 카메라 초기화 실패: {e}\n")
    print("=" * 50)
    print("가능한 해결 방법:")
    print("1. USB 카메라 연결 확인")
    print("   ls /dev/video*")
    print("\n2. 권한 확인")
    print("   sudo usermod -aG video $USER")
    print("   sudo reboot")
    print("\n3. 다른 프로그램에서 카메라 사용 중인지 확인")
    print("   sudo lsof | grep video")
    print("\n4. 카메라 테스트")
    print(
        "   python3 -c \"import cv2; cap=cv2.VideoCapture(0); print('OK' if cap.read()[0] else 'FAIL'); cap.release()\""
    )
    print("=" * 50)
    del bot
    sys.exit(1)

# 초기 하드웨어 설정
if LED_ON_START and USE_LED_EFFECTS:
    bot.Ctrl_WQ2812_ALL(1, 2)  # 파란색 LED 켜기
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

# 모터 정지 상태로 초기화
for i in range(4):
    bot.Ctrl_Muto(i, 0)
print("🛑 모터 정지 상태로 초기화 완료")


# ============================
# OpenCV 트랙바 설정
# ============================


def nothing(x):
    """트랙바 콜백 함수"""
    pass


# 윈도우 생성
cv2.namedWindow("Camera Settings")

# 서보 모터 트랙바
cv2.createTrackbar("Servo 1 Angle", "Camera Settings", DEFAULT_SERVO_1, 180, nothing)
cv2.createTrackbar(
    "Servo 2 Angle", "Camera Settings", DEFAULT_SERVO_2, 110, nothing
)  # 최대 110

# 이미지 처리 트랙바
cv2.createTrackbar("Y Value", "Camera Settings", 10, 160, nothing)
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

print("🎛️  OpenCV 트랙바 설정 완료")


# ============================
# 이미지 처리 함수
# ============================


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


def process_frame(frame, detect_value, r_weight, g_weight, b_weight, y_value):
    """프레임 처리 및 엣지 검출"""
    # 원근 변환 영역 정의
    pts_src = np.float32(
        [
            [10, 70 + y_value],
            [310, 70 + y_value],
            [310, 10 + y_value],
            [10, 10 + y_value],
        ]
    )
    pts_dst = np.float32([[0, 240], [320, 240], [320, 0], [0, 0]])

    # 원본 프레임에 사각형 그리기
    pts = pts_src.reshape((-1, 1, 2)).astype(np.int32)
    frame_with_rect = cv2.polylines(
        frame.copy(), [pts], isClosed=True, color=(0, 255, 0), thickness=2
    )
    cv2.imshow("1_Frame", frame_with_rect)

    # 원근 변환 적용
    mat_affine = cv2.getPerspectiveTransform(pts_src, pts_dst)
    frame_transformed = cv2.warpPerspective(frame, mat_affine, (320, 240))
    cv2.imshow("2_frame_transformed", frame_transformed)

    # 그레이스케일 변환
    gray_frame = weighted_gray(frame_transformed, r_weight, g_weight, b_weight)
    cv2.imshow("3_gray_frame", gray_frame)

    # 이진화
    _, binary_frame = cv2.threshold(gray_frame, detect_value, 255, cv2.THRESH_BINARY)

    # 노이즈 제거 (모폴로지 연산)
    kernel = np.ones((5, 5), np.uint8)
    binary_frame = cv2.morphologyEx(binary_frame, cv2.MORPH_CLOSE, kernel)
    binary_frame = cv2.morphologyEx(binary_frame, cv2.MORPH_OPEN, kernel)

    cv2.imshow("4_Processed Frame", binary_frame)
    return binary_frame


# ============================
# 차량 제어 함수 (Raspbot_Lib 사용)
# ============================


def car_run(speed_left, speed_right):
    """
    전진
    speed: -255 ~ 255 (음수=후진, 양수=전진)
    """
    bot.Ctrl_Muto(0, speed_left)  # M1 (Left Front)
    bot.Ctrl_Muto(1, speed_left)  # M2 (Left Rear)
    bot.Ctrl_Muto(2, speed_right)  # M3 (Right Front)
    bot.Ctrl_Muto(3, speed_right)  # M4 (Right Rear)


def car_stop():
    """정지"""
    for i in range(4):
        bot.Ctrl_Muto(i, 0)


def car_left(speed_left, speed_right):
    """
    좌회전 (왼쪽 바퀴 느리게, 오른쪽 바퀴 빠르게)
    """
    bot.Ctrl_Muto(0, -speed_left)  # M1 후진
    bot.Ctrl_Muto(1, -speed_left)  # M2 후진
    bot.Ctrl_Muto(2, speed_right)  # M3 전진
    bot.Ctrl_Muto(3, speed_right)  # M4 전진


def car_right(speed_left, speed_right):
    """
    우회전 (왼쪽 바퀴 빠르게, 오른쪽 바퀴 느리게)
    """
    bot.Ctrl_Muto(0, speed_left)  # M1 전진
    bot.Ctrl_Muto(1, speed_left)  # M2 전진
    bot.Ctrl_Muto(2, -speed_right)  # M3 후진
    bot.Ctrl_Muto(3, -speed_right)  # M4 후진


def rotate_servo(servo_id, angle):
    """서보 모터 회전"""
    if servo_id == 2 and angle > 110:
        angle = 110  # Servo 2는 최대 110도
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
    y_value,
):
    """히스토그램 기반 방향 결정"""
    length = len(histogram)

    # 히스토그램을 6개 구역으로 나눔
    DIVIDE = 6

    left = int(np.sum(histogram[: length // DIVIDE]))
    right = int(np.sum(histogram[(DIVIDE - 1) * length // DIVIDE :]))
    center_left = int(np.sum(histogram[1 * length // DIVIDE : 3 * length // DIVIDE]))
    center_right = int(np.sum(histogram[3 * length // DIVIDE : 5 * length // DIVIDE]))

    if DEBUG_MODE:
        print(
            f"Left: {left:6d} | Right: {right:6d} | Diff: {right - left:6d} | Threshold: {direction_threshold}"
        )

    # 좌우 차이가 큰 경우 방향 전환
    if abs(right - left) > direction_threshold:
        direction = "LEFT" if right > left else "RIGHT"
        if DEBUG_MODE:
            print(f"🔄 Turn {direction}")

        # 회전 시 부저 (옵션)
        if USE_BEEP and BEEP_ON_TURN:
            bot.Ctrl_BEEP_Switch(1)
            time.sleep(0.05)
            bot.Ctrl_BEEP_Switch(0)

        return direction

    # 중앙 영역 분석
    center_diff = abs(center_left - center_right)

    # 앞이 막힌 경우 (라인이 거의 없음)
    if center_diff < up_threshold:
        if DEBUG_MODE:
            print("🚫 Dead end detected! Checking alternative routes...")
        car_stop()
        time.sleep(0.3)
        return rotate_servo_and_check_direction(
            detect_value, r_weight, g_weight, b_weight, y_value
        )

    # 직진
    if DEBUG_MODE:
        print("⬆️  Going straight")
    return "UP"


def rotate_servo_and_check_direction(
    detect_value, r_weight, g_weight, b_weight, y_value
):
    """서보 모터 회전으로 대체 경로 확인"""
    global cap

    if DEBUG_MODE:
        print("🔍 Scanning for alternative routes...")

    # 서보 모터를 180도로 회전하여 위쪽 확인
    bot.Ctrl_Servo(1, 180)
    bot.Ctrl_Servo(2, 100)
    time.sleep(0.5)

    # 새 프레임 캡처 (opencv_camera.py 방식)
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to read frame from camera.")
        return "STOP"

    # 프레임 처리
    processed_frame = process_frame(
        frame, detect_value, r_weight, g_weight, b_weight, y_value
    )
    histogram_180 = np.sum(processed_frame, axis=0)
    length = len(histogram_180)

    # 3구역 분석
    left = int(np.sum(histogram_180[: length // 3]))
    center = int(np.sum(histogram_180[length // 3 : 2 * length // 3]))
    right = int(np.sum(histogram_180[2 * length // 3 :]))

    if DEBUG_MODE:
        print(f"Alternative scan - Left: {left}, Center: {center}, Right: {right}")

    # 서보 모터 원위치
    servo_1_angle = cv2.getTrackbarPos("Servo 1 Angle", "Camera Settings")
    servo_2_angle = cv2.getTrackbarPos("Servo 2 Angle", "Camera Settings")
    bot.Ctrl_Servo(1, servo_1_angle)
    bot.Ctrl_Servo(2, servo_2_angle)
    time.sleep(0.3)

    # 중앙이 가장 비어있으면 (값이 작으면) 직진 가능
    if left > center and right > center:
        if DEBUG_MODE:
            print("✅ Center path clear -> Turn RIGHT")
        return "RIGHT"

    if DEBUG_MODE:
        print("✅ Turn LEFT")
    return "LEFT"


def control_car(direction, up_speed, down_speed):
    """차량 제어 (개선된 버전)"""
    if direction == "UP":
        # 직진 시 속도 부스트
        boosted_speed = min(up_speed + SPEED_BOOST, 255)
        car_run(boosted_speed, boosted_speed)
        if DEBUG_MODE:
            print(f"⚡ Speed: {boosted_speed}")

        # LED: 초록색
        if USE_LED_EFFECTS:
            bot.Ctrl_WQ2812_ALL(1, 1)

    elif direction == "LEFT":
        car_left(down_speed - 10, up_speed + 10)
        if DEBUG_MODE:
            print(f"◀️  Left Turn")

        # LED: 노란색
        if USE_LED_EFFECTS:
            bot.Ctrl_WQ2812_ALL(1, 3)

    elif direction == "RIGHT":
        car_right(up_speed + 10, down_speed - 10)
        if DEBUG_MODE:
            print(f"▶️  Right Turn")

        # LED: 노란색
        if USE_LED_EFFECTS:
            bot.Ctrl_WQ2812_ALL(1, 3)

    elif direction == "RANDOM":
        random_direction = random.choice(["LEFT", "RIGHT"])
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
print("  'l'   : Toggle LED")
print("  'b'   : Test Beep")
print("=" * 50)

frame_count = 0
start_time = time.time()
led_state = LED_ON_START

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
        y_value = cv2.getTrackbarPos("Y Value", "Camera Settings")
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
        processed_frame = process_frame(
            frame, detect_value, r_weight, g_weight, b_weight, y_value
        )
        histogram = np.sum(processed_frame, axis=0)

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
            y_value,
        )
        control_car(direction, motor_up_speed, motor_down_speed)

        # FPS 계산 (10프레임마다)
        if frame_count % 10 == 0:
            elapsed = time.time() - start_time
            fps = 10 / elapsed
            if DEBUG_MODE:
                print(f"📊 FPS: {fps:.1f}")
            start_time = time.time()

        # 키 입력 처리
        key = cv2.waitKey(30) & 0xFF
        if key == 27:  # ESC
            print("\n🛑 Stopping...")
            break
        elif key == 32:  # SPACE
            print("\n⏸️  Paused. Press any key to continue.")
            car_stop()
            cv2.waitKey()
        elif key == ord("l"):  # LED 토글
            led_state = not led_state
            if led_state:
                bot.Ctrl_WQ2812_ALL(1, 2)  # 파란색
                print("💡 LED ON")
            else:
                bot.Ctrl_WQ2812_ALL(0, 0)  # OFF
                print("💡 LED OFF")
        elif key == ord("b"):  # 부저 테스트
            print("🔊 Beep!")
            bot.Ctrl_BEEP_Switch(1)
            time.sleep(0.1)
            bot.Ctrl_BEEP_Switch(0)

        time.sleep(0.05)

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

    # LED 끄기
    if USE_LED_EFFECTS:
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
