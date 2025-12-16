"""
Haar Cascade 기반 객체 감지 카메라 프로그램
- Raspbot_Lib를 사용한 서보 모터 제어
- OpenCV Haar Cascade를 통한 객체 감지
- 부저음과 LED Bar를 통한 감지 알림
- RGB 가중치 조절을 통한 커스텀 그레이스케일 변환
- 실시간 트랙바를 통한 파라미터 조정
"""

import cv2
import time
import os
import sys
import numpy as np
from datetime import datetime

# Raspbot 라이브러리 임포트
from Raspbot_Lib import Raspbot

# ============================================================================
# 전역 상수 정의
# ============================================================================
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

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

# 감지 입력 소스 초기값 (0: frame 컬러, 1: gray 그레이스케일)
DETECT_SOURCE_INITIAL = 0

# Haar Cascade 설정
CASCADE_FILE = "cascade.xml"
SCALE_FACTOR = 1.1
MIN_NEIGHBORS = 5
MIN_SIZE = (30, 30)

# 저장 폴더 설정
SAVE_FOLDER_NAME = "detected_objects"
SAVE_PATH_PREFIX = "./save_images"

# 감지 객체 레이블
OBJECT_LABEL_NAME = "Object"  # 감지할 객체 이름

# LED 설정
LED_ON_VALUE = 1
LED_OFF_VALUE = 0

# 부저 설정
BUZZER_FREQUENCY = 2000  # Hz
BUZZER_DURATION = 100  # ms


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
# Haar Cascade 분류기 로드 함수
# ============================================================================
def load_cascade_classifier(cascade_file):
    """
    Haar Cascade 분류기를 로드합니다.

    Args:
        cascade_file (str): cascade XML 파일 경로

    Returns:
        cv2.CascadeClassifier: 로드된 분류기 객체
    """
    if not os.path.exists(cascade_file):
        print(f"Error: Cascade file not found: {cascade_file}")
        return None

    cascade = cv2.CascadeClassifier()

    if not cascade.load(cascade_file):
        print(f"Error: Failed to load cascade: {cascade_file}")
        return None

    print(f"Cascade classifier loaded: {cascade_file}")
    return cascade


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
    if car is None:
        return

    if not (0 <= angle <= 180):
        print(f"Warning: Servo angle out of range: {angle}")
        return

    if servo_id not in [1, 2]:
        print(f"Warning: Invalid servo ID: {servo_id}")
        return

    try:
        car.Ctrl_Servo(servo_id, angle)
    except Exception as e:
        print(f"Servo control error (ID:{servo_id}, Angle:{angle}): {e}")


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
    weighted_rg = cv2.addWeighted(image[:, :, 2], r_norm, image[:, :, 1], g_norm, 0)
    weighted_result = cv2.addWeighted(weighted_rg, 1.0, image[:, :, 0], b_norm, 0)

    return weighted_result


# ============================================================================
# 감지 프레임 선택 함수
# ============================================================================
def get_detection_frame(frame, gray_frame, gray_rgb_frame, frame_source):
    """
    트랙바로 선택된 프레임 소스 반환

    Args:
        frame (numpy.ndarray): 원본 BGR 프레임
        gray_frame (numpy.ndarray): 일반 그레이스케일 프레임
        gray_rgb_frame (numpy.ndarray): RGB 가중치 그레이스케일 프레임
        frame_source (int): 소스 선택 (0: 원본, 1: 그레이, 2: RGB 가중치)

    Returns:
        numpy.ndarray: 선택된 프레임
    """
    if frame_source == 0:
        return frame  # 원본 BGR
    elif frame_source == 1:
        return gray_frame  # 일반 그레이스케일
    elif frame_source == 2:
        return gray_rgb_frame  # RGB 가중치 그레이스케일
    else:
        return frame  # 기본값: 원본


# ============================================================================
# 객체 감지 함수
# ============================================================================
def detect_objects(cascade, input_image):
    """
    Haar Cascade를 사용하여 객체를 감지합니다.

    Args:
        cascade (cv2.CascadeClassifier): 분류기 객체
        input_image (numpy.ndarray): 입력 이미지 (컬러 또는 그레이스케일)

    Returns:
        numpy.ndarray: 감지된 객체의 좌표 배열 [(x, y, w, h), ...]
    """
    # ⭐ 컬러 이미지면 그레이스케일로 변환
    if len(input_image.shape) == 3:
        gray_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)
    else:
        gray_image = input_image

    objects = cascade.detectMultiScale(
        gray_image,
        scaleFactor=SCALE_FACTOR,
        minNeighbors=MIN_NEIGHBORS,
        minSize=MIN_SIZE,
    )
    return objects


# ============================================================================
# 감지된 객체에 사각형과 텍스트 그리기
# ============================================================================
def draw_detection_results(display_frame, detected_objects, label, frame_source):
    """
    감지된 객체 주위에 사각형과 레이블을 그립니다.

    Args:
        display_frame (numpy.ndarray): 표시할 프레임 (선택된 소스)
        detected_objects (numpy.ndarray): 감지된 객체 좌표
        label (str): 객체 레이블
        frame_source (int): 프레임 소스 (0: 원본, 1: 그레이, 2: RGB 가중치)

    Returns:
        numpy.ndarray: 주석이 추가된 프레임
    """
    # ⭐ 그레이스케일이면 컬러로 변환 (박스와 텍스트를 컬러로 그리기 위해)
    if len(display_frame.shape) == 2:
        frame = cv2.cvtColor(display_frame, cv2.COLOR_GRAY2BGR)
    else:
        frame = display_frame.copy()

    # 왼쪽 상단에 객체 이름 표시
    if len(detected_objects) > 0:
        object_name_text = f"{OBJECT_LABEL_NAME} Detected!"
        cv2.putText(
            frame,
            object_name_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),  # 빨간색
            2,
        )

        # 감지된 객체 수 표시
        count_text = f"Count: {len(detected_objects)}"
        cv2.putText(
            frame,
            count_text,
            (10, 65),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),  # 노란색
            2,
        )

    for idx, (x, y, w, h) in enumerate(detected_objects, 1):
        # 사각형 그리기 (녹색, 두께 3)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 5)

        # 객체 위에 텍스트 그리기 (크기 정보)
        size_text = f"Size: {w}x{h}"
        cv2.putText(
            frame,
            size_text,
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 0),
            2,
        )

        # 객체 번호 표시
        number_text = f"#{idx}"
        cv2.putText(
            frame,
            number_text,
            (x, y - 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 0, 0),
            2,
        )

        # Rect 좌표 정보 표시 (객체 내부 왼쪽 상단)
        rect_text = f"({x},{y})"
        cv2.putText(
            frame,
            rect_text,
            (x + 5, y + 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            1,
        )

    return frame


# ============================================================================
# LED Bar 제어 함수
# ============================================================================
def control_led_bar(car, detected_count):
    """
    감지된 객체 수에 따라 LED Bar를 제어합니다.

    Args:
        car (Raspbot): Raspbot 객체
        detected_count (int): 감지된 객체 수
    """
    if car is None or not hasattr(car, "Ctrl_LED"):
        return

    try:
        if detected_count == 0:
            # 객체가 없으면 LED 모두 끄기
            car.Ctrl_LED(1, LED_OFF_VALUE)
            car.Ctrl_LED(2, LED_OFF_VALUE)
            car.Ctrl_LED(3, LED_OFF_VALUE)
        elif detected_count == 1:
            # 1개 감지: LED 1개 켜기
            car.Ctrl_LED(1, LED_ON_VALUE)
            car.Ctrl_LED(2, LED_OFF_VALUE)
            car.Ctrl_LED(3, LED_OFF_VALUE)
        elif detected_count == 2:
            # 2개 감지: LED 2개 켜기
            car.Ctrl_LED(1, LED_ON_VALUE)
            car.Ctrl_LED(2, LED_ON_VALUE)
            car.Ctrl_LED(3, LED_OFF_VALUE)
        else:
            # 3개 이상 감지: LED 모두 켜기
            car.Ctrl_LED(1, LED_ON_VALUE)
            car.Ctrl_LED(2, LED_ON_VALUE)
            car.Ctrl_LED(3, LED_ON_VALUE)
    except Exception as e:
        pass  # 조용히 무시


# ============================================================================
# 부저 제어 함수
# ============================================================================
def control_buzzer_beep(car, detected_count, frame_counter):
    """
    객체 감지 시 부저를 삐익삐익 울립니다.

    Args:
        car (Raspbot): Raspbot 객체
        detected_count (int): 감지된 객체 수
        frame_counter (int): 프레임 카운터 (부저 패턴용)

    Returns:
        int: 부저 상태 (1: ON, 0: OFF)
    """
    if car is None or not hasattr(car, "Ctrl_Buzzer"):
        return 0

    try:
        if detected_count > 0:
            # 15프레임마다 부저 토글 (삐익삐익 효과)
            beep_cycle = (frame_counter // 15) % 2
            if beep_cycle == 0:
                car.Ctrl_Buzzer(1)
                return 1
            else:
                car.Ctrl_Buzzer(0)
                return 0
        else:
            car.Ctrl_Buzzer(0)
            return 0
    except Exception as e:
        return 0  # 조용히 무시


# ============================================================================
# 이미지 저장 함수
# ============================================================================
def save_detected_image(image, folder_name, count):
    """
    감지된 이미지를 저장합니다.

    Args:
        image (numpy.ndarray): 저장할 이미지
        folder_name (str): 저장 폴더 이름
        count (int): 이미지 카운트

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
    filename = f"{path}/{folder_name}_{timestamp}_{count}.jpg"

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
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

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

    # 감지 입력 소스 트랙바 (0: frame 컬러, 1: gray 그레이스케일)
    cv2.createTrackbar(
        "Detect_Source", window_name, DETECT_SOURCE_INITIAL, 2, trackbar_callback
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
        "detect_source": cv2.getTrackbarPos("Detect_Source", window_name),
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
# 키 입력 처리 함수
# ============================================================================
def handle_key_input(key, frame, save_count):
    """
    키 입력을 처리합니다.

    Args:
        key (int): 입력된 키 코드
        frame (numpy.ndarray): 현재 프레임
        save_count (int): 현재 저장 카운트

    Returns:
        tuple: (종료 여부, 업데이트된 저장 카운트)
    """
    # ESC 키 (종료)
    if key == 27:
        print("Exiting program.")
        return True, save_count

    # SPACE 키 (이미지 저장)
    if key == 32:
        save_detected_image(frame, SAVE_FOLDER_NAME, save_count)
        save_count += 1

    return False, save_count


# ============================================================================
# 메인 실행 함수
# ============================================================================
def main():
    """
    메인 실행 함수
    """
    # 초기화
    print("=" * 60)
    print("Haar Cascade Object Detection Program Started")
    print("=" * 60)
    print("Controls:")
    print("  - ESC: Exit program")
    print("  - SPACE: Save detected image")
    print("  - Use trackbars to adjust:")
    print("    * Servo angles")
    print("    * Camera settings")
    print("    * RGB weights for grayscale conversion")
    print("    * Detect_Source: 0=Frame(Color), 1=Gray, 2=Gray(RGB Weighted)")
    print("=" * 60)

    # 카메라 초기화
    cap = initialize_camera()
    if cap is None:
        return

    # Haar Cascade 분류기 로드
    cascade = load_cascade_classifier(CASCADE_FILE)
    if cascade is None:
        cap.release()
        return

    # Raspbot 초기화
    car = None
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

    # LED와 부저 초기화 (선택적)
    if car is not None:
        try:
            # LED 초기화 (모두 끄기) - Ctrl_LED 메서드가 있는 경우만
            if hasattr(car, "Ctrl_LED"):
                control_led_bar(car, 0)
                print("LED Bar initialized (all off)")
            else:
                print("LED Bar not available (method not found)")
        except Exception as e:
            print(f"LED initialization warning: {e}")

        try:
            # 부저 초기화 (끄기) - Ctrl_Buzzer 메서드가 있는 경우만
            if hasattr(car, "Ctrl_Buzzer"):
                car.Ctrl_Buzzer(0)
                print("Buzzer initialized (off)")
            else:
                print("Buzzer not available (method not found)")
        except Exception as e:
            print(f"Buzzer initialization warning: {e}")

    # UI 초기화
    window_name = initialize_ui()

    # 이미지 표시 윈도우 생성 (크기 조절 가능)
    cv2.namedWindow("1__Origin_Frame", cv2.WINDOW_NORMAL)
    cv2.namedWindow("2__Detection_Result", cv2.WINDOW_NORMAL)

    # 저장 카운터 초기화
    save_count = 0

    # 프레임 카운터 및 FPS 계산 초기화
    frame_counter = 0
    start_time = time.time()

    # 메인 루프
    try:
        while True:
            frame_counter += 1

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

                # 첫 10 프레임만 서보 각도 디버그 출력
                if frame_counter <= 10:
                    print(
                        f"Frame {frame_counter}: Servo1={params['servo_1_angle']}, Servo2={params['servo_2_angle']}"
                    )

            # 프레임 읽기
            ret, frame = cap.read()

            if not ret:
                print("Warning: Cannot read frame.")
                continue

            # FPS 계산
            fps = calculate_fps(frame_counter, start_time)

            # ⭐ 3가지 프레임 준비
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # 일반 그레이스케일
            gray_rgb_frame = weighted_grayscale_conversion(
                frame, params["r_weight"], params["g_weight"], params["b_weight"]
            )  # RGB 가중치 그레이스케일

            # ⭐ 감지 입력 소스 선택 (0: frame, 1: gray, 2: gray_rgb)
            detect_frame = get_detection_frame(
                frame, gray_frame, gray_rgb_frame, params["detect_source"]
            )

            # 소스 이름 설정
            source_names = {0: "Frame (Color)", 1: "Gray", 2: "Gray (RGB Weighted)"}
            source_name = source_names.get(params["detect_source"], "Unknown")

            # 객체 감지
            detected_objects = detect_objects(cascade, detect_frame)
            detected_count = len(detected_objects)

            # ⭐ 원본 프레임 표시 (항상 원본 유지)
            cv2.imshow("1__Origin_Frame", frame)

            # ⭐ 감지 결과 그리기 (선택된 프레임 사용)
            result_frame = draw_detection_results(
                detect_frame,
                detected_objects,
                OBJECT_LABEL_NAME,
                params["detect_source"],
            )

            # FPS 정보 표시 (오른쪽 하단)
            fps_text = f"FPS: {fps:.1f}"
            cv2.putText(
                result_frame,
                fps_text,
                (CAMERA_WIDTH - 120, CAMERA_HEIGHT - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )

            # 감지 소스 정보 표시 (왼쪽 하단, 폰트 굵기 증가)
            source_text = f"Source: {source_name}"
            cv2.putText(
                result_frame,
                source_text,
                (10, CAMERA_HEIGHT - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 0, 255),  # 마젠타 색상
                2,
            )

            # ⭐ 결과 프레임 표시
            cv2.imshow("2__Detection_Result", result_frame)

            # LED Bar 및 부저 제어
            if car is not None:
                # LED Bar 제어 (메서드가 있는 경우만)
                if hasattr(car, "Ctrl_LED"):
                    control_led_bar(car, detected_count)

                # 부저 제어 (삐익삐익 소리) (메서드가 있는 경우만)
                if hasattr(car, "Ctrl_Buzzer"):
                    control_buzzer_beep(car, detected_count, frame_counter)

            # 키 입력 처리
            key = cv2.waitKey(30) & 0xFF
            should_exit, save_count = handle_key_input(key, frame, save_count)

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

        # LED와 부저 끄기
        if car is not None:
            try:
                if hasattr(car, "Ctrl_LED"):
                    control_led_bar(car, 0)
                if hasattr(car, "Ctrl_Buzzer"):
                    car.Ctrl_Buzzer(0)
            except Exception as e:
                print(f"Cleanup warning: {e}")

        cap.release()
        cv2.destroyAllWindows()
        print("Program terminated successfully")


# ============================================================================
# 프로그램 시작점
# ============================================================================
if __name__ == "__main__":
    main()
