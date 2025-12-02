"""
카메라 가중치 기반 그레이스케일 변환 프로그램
- Raspbot_Lib를 사용한 서보 모터 제어
- OpenCV를 통한 카메라 설정 및 이미지 캡처
- RGB 가중치 조절을 통한 커스텀 그레이스케일 변환
- 실시간 트랙바를 통한 파라미터 조정
"""

import cv2
import time
import os
import sys
import numpy as np
from datetime import datetime


from Raspbot_Lib import Raspbot

# ============================================================================
# 전역 상수 정의
# ============================================================================
CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240

# 서보 모터 초기 각도
SERVO_1_INITIAL_ANGLE = 90  # 서보1 초기 각도 (좌우)
SERVO_2_INITIAL_ANGLE = 35  # 서보2 초기 각도 (상하)

# 카메라 파라미터 초기값
BRIGHTNESS_INITIAL = 70
CONTRAST_INITIAL = 70
SATURATION_INITIAL = 70
GAIN_INITIAL = 80

# RGB 가중치 초기값
R_WEIGHT_INITIAL = 33
G_WEIGHT_INITIAL = 33
B_WEIGHT_INITIAL = 33

# 저장 폴더 설정
SAVE_FOLDER_NAME = "rect"
SAVE_PATH_PREFIX = "./rectagle"


# ============================================================================
# 카메라 초기화 함수
# ============================================================================
def initialize_camera():
    """
    카메라를 초기화하고 기본 설정을 적용합니다.

    Returns:
        cv2.VideoCapture: 초기화된 카메라 객체
    """
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Cannot open camera.")
        return None

    # 카메라 해상도 설정
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

    print(f"Camera initialized: {CAMERA_WIDTH}x{CAMERA_HEIGHT}")
    return cap


# ============================================================================
# 서보 모터 제어 함수
# ============================================================================
def control_servo_motor(car, servo_id, angle):
    """
    서보 모터를 지정된 각도로 회전시킵니다.

    Args:
        car (Raspbot): Raspbot 객체
        servo_id (int): 서보 모터 ID (1 또는 2)
        angle (int): 회전 각도 (0-180)
    """
    if not (0 <= angle <= 180):
        print(f"Warning: Servo angle out of range: {angle}")
        return

    if servo_id not in [1, 2]:
        print(f"Warning: Invalid servo ID: {servo_id}")
        return

    car.Ctrl_Servo(servo_id, angle)


# ============================================================================
# 카메라 설정 적용 함수
# ============================================================================
def apply_camera_settings(cap, brightness, contrast, saturation, gain):
    """
    카메라 파라미터를 설정합니다.

    Args:
        cap (cv2.VideoCapture): 카메라 객체
        brightness (int): 밝기 (0-100)
        contrast (int): 대비 (0-100)
        saturation (int): 채도 (0-100)
        gain (int): 게인 (0-100)
    """
    cap.set(cv2.CAP_PROP_BRIGHTNESS, brightness)
    cap.set(cv2.CAP_PROP_CONTRAST, contrast)
    cap.set(cv2.CAP_PROP_SATURATION, saturation)
    cap.set(cv2.CAP_PROP_GAIN, gain)


# ============================================================================
# 가중치 기반 그레이스케일 변환 함수
# ============================================================================
def weighted_grayscale_conversion(image, r_weight, g_weight, b_weight):
    """
    RGB 가중치를 사용하여 그레이스케일 이미지로 변환합니다.

    Args:
        image (numpy.ndarray): 입력 컬러 이미지 (BGR)
        r_weight (int): Red 채널 가중치 (0-100)
        g_weight (int): Green 채널 가중치 (0-100)
        b_weight (int): Blue 채널 가중치 (0-100)

    Returns:
        numpy.ndarray: 가중치가 적용된 그레이스케일 이미지
    """
    sum_weight = r_weight + g_weight + b_weight

    # 가중치 합이 0이면 기본값 사용
    if sum_weight == 0:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 가중치를 0-1 범위로 정규화
    r_norm = r_weight / sum_weight
    g_norm = g_weight / sum_weight
    b_norm = b_weight / sum_weight

    # BGR 순서로 가중치 적용 (OpenCV는 BGR 사용)
    # image[:, :, 0] = B, image[:, :, 1] = G, image[:, :, 2] = R
    weighted_rg = cv2.addWeighted(image[:, :, 2], r_norm, image[:, :, 1], g_norm, 0)
    weighted_result = cv2.addWeighted(weighted_rg, 1.0, image[:, :, 0], b_norm, 0)

    return weighted_result


# ============================================================================
# 이미지 저장 함수
# ============================================================================
def save_image(image, folder_name):
    """
    이미지를 지정된 폴더에 타임스탬프와 함께 저장합니다.

    Args:
        image (numpy.ndarray): 저장할 이미지
        folder_name (str): 저장 폴더 이름

    Returns:
        bool: 저장 성공 여부
    """
    path = f"{SAVE_PATH_PREFIX}/{folder_name}"

    # 폴더가 없으면 생성
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Folder created: {path}")

    # 타임스탬프 생성
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    filename = f"{path}/{folder_name}_{timestamp}.jpg"

    # 이미지 저장
    success = cv2.imwrite(filename, image)

    if success:
        print(f"Image saved: {filename}")
    else:
        print(f"Image save failed: {filename}")

    return success


# ============================================================================
# 트랙바 콜백 함수
# ============================================================================
def trackbar_callback(x):
    """트랙바 콜백 함수 (사용되지 않음)"""
    pass


# ============================================================================
# UI 초기화 함수
# ============================================================================
def initialize_ui():
    """
    OpenCV 윈도우와 트랙바를 초기화합니다.
    """
    window_name = "Camera Settings"
    cv2.namedWindow(window_name)

    # 서보 모터 제어 트랙바
    cv2.createTrackbar(
        "Servo 1 Angle", window_name, SERVO_1_INITIAL_ANGLE, 180, trackbar_callback
    )
    cv2.createTrackbar(
        "Servo 2 Angle", window_name, SERVO_2_INITIAL_ANGLE, 180, trackbar_callback
    )

    # 카메라 설정 트랙바
    cv2.createTrackbar(
        "Brightness", window_name, BRIGHTNESS_INITIAL, 100, trackbar_callback
    )
    cv2.createTrackbar(
        "Contrast", window_name, CONTRAST_INITIAL, 100, trackbar_callback
    )
    cv2.createTrackbar(
        "Saturation", window_name, SATURATION_INITIAL, 100, trackbar_callback
    )
    cv2.createTrackbar("Gain", window_name, GAIN_INITIAL, 100, trackbar_callback)

    # RGB 가중치 트랙바
    cv2.createTrackbar(
        "R_weight", window_name, R_WEIGHT_INITIAL, 100, trackbar_callback
    )
    cv2.createTrackbar(
        "G_weight", window_name, G_WEIGHT_INITIAL, 100, trackbar_callback
    )
    cv2.createTrackbar(
        "B_weight", window_name, B_WEIGHT_INITIAL, 100, trackbar_callback
    )

    print("UI initialized")
    return window_name


# ============================================================================
# 트랙바에서 값 읽기 함수
# ============================================================================
def get_trackbar_values(window_name):
    """
    트랙바에서 현재 값을 읽어옵니다.

    Args:
        window_name (str): 윈도우 이름

    Returns:
        dict: 트랙바 값들의 딕셔너리
    """
    return {
        "servo_1_angle": cv2.getTrackbarPos("Servo 1 Angle", window_name),
        "servo_2_angle": cv2.getTrackbarPos("Servo 2 Angle", window_name),
        "brightness": cv2.getTrackbarPos("Brightness", window_name),
        "contrast": cv2.getTrackbarPos("Contrast", window_name),
        "saturation": cv2.getTrackbarPos("Saturation", window_name),
        "gain": cv2.getTrackbarPos("Gain", window_name),
        "r_weight": cv2.getTrackbarPos("R_weight", window_name),
        "g_weight": cv2.getTrackbarPos("G_weight", window_name),
        "b_weight": cv2.getTrackbarPos("B_weight", window_name),
    }


# ============================================================================
# FPS 계산 함수
# ============================================================================
def calculate_fps(frame_count, start_time):
    """
    현재 FPS를 계산합니다.

    Args:
        frame_count (int): 프레임 카운트
        start_time (float): 시작 시간

    Returns:
        float: 계산된 FPS
    """
    elapsed_time = time.time() - start_time

    if elapsed_time == 0:
        return 0

    return frame_count / elapsed_time


# ============================================================================
# 이미지 처리 및 표시 함수
# ============================================================================
def process_and_display_frames(frame, fps, r_weight, g_weight, b_weight):
    """
    프레임을 처리하고 화면에 표시합니다.

    Args:
        frame (numpy.ndarray): 원본 프레임
        fps (float): 현재 FPS
        r_weight (int): Red 채널 가중치
        g_weight (int): Green 채널 가중치
        b_weight (int): Blue 채널 가중치

    Returns:
        numpy.ndarray: 가중치가 적용된 그레이스케일 프레임
    """
    # FPS 정보를 프레임에 추가
    fps_text = f"FPS: {fps:.1f}"
    cv2.putText(frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # 원본 프레임 표시
    cv2.imshow("1__origin_frame", frame)

    # 가중치 기반 그레이스케일 변환
    weighted_gray = weighted_grayscale_conversion(frame, r_weight, g_weight, b_weight)

    # 가중치 정보를 그레이스케일 프레임에 추가
    weight_text = f"R:{r_weight} G:{g_weight} B:{b_weight}"
    cv2.putText(
        weighted_gray,
        weight_text,
        (10, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        255,
        1,
    )

    # 그레이스케일 프레임 표시
    cv2.imshow("2__weighted_gray_frame", weighted_gray)

    return weighted_gray


# ============================================================================
# 키 입력 처리 함수
# ============================================================================
def handle_key_input(key, weighted_gray_frame):
    """
    키 입력을 처리합니다.

    Args:
        key (int): 입력된 키 코드
        weighted_gray_frame (numpy.ndarray): 가중치 그레이스케일 프레임

    Returns:
        bool: 프로그램 종료 여부
    """
    # ESC 키 (종료)
    if key == 27:
        print("Exiting program.")
        return True

    # SPACE 키 (이미지 저장)
    if key == 32:
        save_image(weighted_gray_frame, SAVE_FOLDER_NAME)

    return False


# ============================================================================
# 메인 실행 함수
# ============================================================================
def main():
    """
    메인 실행 함수
    """
    # 초기화
    print("=" * 60)
    print("Camera Weighted Grayscale Conversion Program Started")
    print("=" * 60)
    print("Controls:")
    print("  - ESC: Exit program")
    print("  - SPACE: Capture image (weighted grayscale)")
    print("  - Use trackbars to adjust:")
    print("    * Servo angles")
    print("    * Camera settings")
    print("    * RGB weights for grayscale conversion")
    print("=" * 60)

    # 카메라 초기화
    cap = initialize_camera()
    if cap is None:
        return

    # Raspbot 초기화
    try:
        car = Raspbot()
        print("Raspbot initialized")

        # 서보모터 초기 위치 설정
        control_servo_motor(car, 1, SERVO_1_INITIAL_ANGLE)
        control_servo_motor(car, 2, SERVO_2_INITIAL_ANGLE)
        print(
            f"Servo motors set to initial position: Servo1={SERVO_1_INITIAL_ANGLE}, Servo2={SERVO_2_INITIAL_ANGLE}"
        )
        time.sleep(0.5)  # 서보모터가 초기 위치로 이동할 시간 제공

    except Exception as e:
        print(f"Raspbot initialization failed: {e}")
        print("Running camera test only without servo motor control.")
        car = None

    # UI 초기화
    window_name = initialize_ui()

    # FPS 카운터 초기화
    frame_count = 0
    start_time = time.time()

    # 메인 루프
    try:
        while True:
            # 트랙바 값 읽기
            params = get_trackbar_values(window_name)

            # 카메라 설정 적용
            apply_camera_settings(
                cap,
                params["brightness"],
                params["contrast"],
                params["saturation"],
                params["gain"],
            )

            # 서보 모터 제어
            if car is not None:
                control_servo_motor(car, 1, params["servo_1_angle"])
                control_servo_motor(car, 2, params["servo_2_angle"])

            # 프레임 읽기
            ret, frame = cap.read()

            if not ret:
                print("Warning: Cannot read frame.")
                continue

            # FPS 계산
            frame_count += 1
            fps = calculate_fps(frame_count, start_time)

            # 프레임 처리 및 표시
            weighted_gray = process_and_display_frames(
                frame,
                fps,
                params["r_weight"],
                params["g_weight"],
                params["b_weight"],
            )

            # 키 입력 처리
            key = cv2.waitKey(30) & 0xFF
            should_exit = handle_key_input(key, weighted_gray)

            if should_exit:
                break

            # 프레임 레이트 제어
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected - exiting program.")

    except Exception as e:
        print(f"Error occurred: {e}")

    finally:
        # 리소스 정리
        print("Cleaning up resources...")
        cap.release()
        cv2.destroyAllWindows()
        print("Program terminated successfully")


# ============================================================================
# 프로그램 시작점
# ============================================================================
if __name__ == "__main__":
    main()
