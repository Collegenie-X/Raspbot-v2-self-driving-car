#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspbot v2 YOLO + Haar Cascade 하이브리드 자율주행 시스템
신호등 제어(YOLO11) + 표지판 감지(Haar Cascade) + 자율주행 통합 버전

Created: 2025-12-15 (v3.0 - YOLO11 통합)

═══════════════════════════════════════════════════════════
주요 특징:
═══════════════════════════════════════════════════════════
- 서보 모터 제어 포함 (카메라 각도 조절)
- 라인 트레이싱 기본 기능 (빨간색/회색 도로선 감지)
- RGB 가중치 기반 그레이스케일 변환 (빛 반사 필터링)
- ⭐⭐ 신호등 감지: YOLO11 사용 (최우선 순위)
  - Class 0: traffic_red_light (빨간불)
  - Class 1: traffic_green_light (초록불)
  - Class 2: traffic_light (일반 신호등)
- ⭐ 표지판 감지: Haar Cascade 사용 (차순위)
  - Stop sign, No Drive sign
- ⭐ 자율주행: 히스토그램 3등분 분석 기반 방향 결정
- Frame 처리 계속: 정지 중에도 이미지 인식 계속 진행
- 부저 최적화: 각 신호별 최초 1회만 울림

하이브리드 아키텍처:
═══════════════════════════════════════════════════════════
┌─────────────────────────────────────────┐
│         신호등 감지 (YOLO11)            │
│  - traffic_red_light (Class 0)          │
│  - traffic_green_light (Class 1)        │
│  - traffic_light (Class 2)              │
│  - 실시간 객체 감지                     │
│  - Confidence threshold: 0.5            │
└─────────────────────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│      표지판 감지 (Haar Cascade)         │
│  - STOP sign                            │
│  - NO DRIVE sign                        │
│  - 전통적인 Cascade 방식                │
└─────────────────────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│         자율주행 (Line Tracing)         │
│  - 히스토그램 3등분 분석                │
│  - RGB 가중치 필터링                    │
│  - 방향 결정 알고리즘                   │
└─────────────────────────────────────────┘

YOLO 모델 정보:
═══════════════════════════════════════════════════════════
- 모델 파일: ./models/traffic_light_yolo11.pt
- 입력 크기: 640x640 (자동 리사이징)
- 클래스 수: 3
- 프레임워크: Ultralytics YOLO11
- Confidence: 0.5 (트랙바로 조정 가능)
- IOU: 0.45 (NMS threshold)
"""

import sys
import os

# ============================
# Qt 플랫폼 플러그인 에러 방지 (Raspberry Pi)
# ============================
if not os.environ.get("QT_QPA_PLATFORM"):
    os.environ["QT_QPA_PLATFORM"] = "xcb"

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

# ⭐ YOLO11 import
try:
    # YOLO 오프라인 설정 (인터넷 연결 시도 비활성화)
    os.environ["YOLO_OFFLINE"] = "1"
    os.environ["YOLO_VERBOSE"] = "False"

    from ultralytics import YOLO
    from ultralytics import settings

    # Ultralytics 설정: 오프라인 모드
    settings.update(
        {
            "sync": False,  # 온라인 동기화 비활성화
            "datasets_dir": "./datasets",  # 로컬 데이터셋 경로
        }
    )

    print("✅ Ultralytics YOLO imported successfully (Offline mode)")
    YOLO_AVAILABLE = True
except ImportError:
    print("⚠️  Warning: Ultralytics YOLO not available")
    print("   Install with: pip install ultralytics")
    YOLO_AVAILABLE = False
except Exception as e:
    print(f"⚠️  Warning: YOLO configuration error: {e}")
    print("   Continuing with default settings")
    YOLO_AVAILABLE = True

print("Libraries loaded successfully\n")

# ============================
# 사용자 설정 영역
# ============================
print("=" * 50)
print("  STEP 2: Loading Configuration...")
print("=" * 50)

# 기본 속도 설정 (-255 ~ 255)
DEFAULT_SPEED_UP = 15
DEFAULT_SPEED_DOWN = 8

# 라인 검출 설정
DEFAULT_DETECT_VALUE = 120
DEFAULT_BRIGHTNESS = 32
DEFAULT_CONTRAST = 0

# RGB 가중치 설정 (빛 반사 필터링)
DEFAULT_R_WEIGHT = 30  # 빨강 채널 가중치 (0-100)
DEFAULT_G_WEIGHT = 40  # 초록 채널 가중치 (0-100)
DEFAULT_B_WEIGHT = 60  # 파랑 채널 가중치 (0-100)

# 방향 판단 임계값
DEFAULT_DIRECTION_THRESHOLD = 35000
DEFAULT_UP_THRESHOLD = 220000

# 중앙 윤곽선 체크 임계값
CENTER_CLEAR_THRESHOLD = 0.2

# 서보 모터 각도
DEFAULT_SERVO_1 = 95
DEFAULT_SERVO_2 = 0

# 디버그 모드
DEBUG_MODE = True

# LED 효과 사용
USE_LED_EFFECTS = True
LED_ON_START = True

# 부저 사용
USE_BEEP = True
BEEP_ON_START = True

# 모터 사용
mouse_use = True

# ⭐ YOLO 설정
DEFAULT_YOLO_CONFIDENCE = 50  # 0.5 (트랙바는 0~100)
DEFAULT_YOLO_IOU = 45  # 0.45 (트랙바는 0~100)

# ⭐ 모델 경로 설정
YOLO_MODEL_PATH = "./models/traffic_modeln.pt"  # 커스텀 모델만 사용

# YOLO 클래스 정의 (커스텀 모델 전용)
YOLO_CLASS_NAMES = {
    0: "traffic_red_light",
    1: "traffic_green_light",
    2: "traffic_light",
}

# 상태 변수
led_state = False
beep_state = False
frame_count = 0

# ⭐ 신호등 상태 관리 (최우선 순위)
red_light_active = False  # 현재 빨간불이 감지되고 있는지
green_light_active = False  # 현재 초록불이 감지되고 있는지
red_beep_played = False  # 빨간불 부저 울렸는지
green_beep_played = False  # 초록불 부저 울렸는지
waiting_for_green = False  # 빨간불 후 초록불 대기 중인지

# ⭐ 표지판 상태 관리 (차순위)
stop_sign_active = False  # 현재 Stop sign이 감지되고 있는지
no_drive_sign_active = False  # 현재 No Drive sign이 감지되고 있는지
stop_beep_played = False  # Stop sign 부저 울렸는지
no_drive_beep_played = False  # No Drive sign 부저 울렸는지

print("Configuration loaded successfully")
print(
    f"⭐ RGB Filter: R={DEFAULT_R_WEIGHT}, G={DEFAULT_G_WEIGHT}, B={DEFAULT_B_WEIGHT}"
)
print("⭐ YOLO11 + Haar Cascade Hybrid System")
print("   - Priority 1: Traffic Light (YOLO11)")
print("   - Priority 2: Traffic Sign (Haar Cascade)")
print("   - Priority 3: Auto Driving (Line Tracing)\n")

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


def find_available_camera():
    """
    사용 가능한 카메라 자동 검색

    Returns:
        int: 사용 가능한 카메라 인덱스, 없으면 None
    """
    camera_indices = [0, 1, 2, -1]

    for idx in camera_indices:
        try:
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                if ret and frame is not None:
                    return idx
        except Exception:
            continue

    return None


def initialize_camera(width=320, height=240, camera_index=None):
    """
    카메라 초기화 및 설정

    Args:
        width: 요청 해상도 너비
        height: 요청 해상도 높이
        camera_index: 카메라 인덱스 (None이면 자동 검색)
    """
    try:
        print("\nInitializing camera...")

        # 카메라 인덱스가 지정되지 않으면 자동 검색
        if camera_index is None:
            print("   - Searching for available camera...")
            camera_index = find_available_camera()

            if camera_index is None:
                raise Exception(
                    "No available camera found!\n"
                    "   Please check:\n"
                    "   1. Camera is connected (ls -la /dev/video*)\n"
                    "   2. Camera permissions (sudo usermod -aG video $USER)\n"
                    "   3. No other process is using camera (sudo lsof /dev/video0)\n"
                    "   4. Try running: python3 test_camera.py"
                )

            print(f"   - Found camera at index: {camera_index}")

        cap = cv2.VideoCapture(camera_index)

        if not cap.isOpened():
            raise Exception(f"Cannot open camera at index {camera_index}")

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_BRIGHTNESS, DEFAULT_BRIGHTNESS)
        cap.set(cv2.CAP_PROP_CONTRAST, DEFAULT_CONTRAST)
        cap.set(cv2.CAP_PROP_SATURATION, 50)
        cap.set(cv2.CAP_PROP_EXPOSURE, 100)

        ret, frame = cap.read()
        if not ret or frame is None:
            cap.release()
            raise Exception("Camera opened but cannot read frame")

        actual_height, actual_width = frame.shape[:2]
        print(f"✅ USB camera initialized successfully")
        print(f"   - Camera index: {camera_index}")
        print(f"   - Requested resolution: {width}x{height}")
        print(f"   - Actual resolution: {actual_width}x{actual_height}")

        return cap

    except Exception as e:
        print(f"\n❌ Failed to initialize camera: {e}\n")
        raise


def setup_initial_hardware_state(bot):
    """초기 하드웨어 상태 설정"""
    # LED 초기화
    bot.Ctrl_WQ2812_ALL(0, 0)
    print("LED initialized (OFF)")

    # 부저 초기화
    bot.Ctrl_BEEP_Switch(0)
    print("Beeper initialized (OFF)")

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
    print("Motors stopped and initialized")
    print("=" * 50 + "\n")


# Raspbot 및 카메라 초기화
bot = initialize_raspbot()

try:
    cap = initialize_camera()
except Exception as e:
    del bot
    sys.exit(1)

setup_initial_hardware_state(bot)

# ⭐ tmp 디렉토리 생성 (YOLO 임시 파일용)
if not os.path.exists("./tmp"):
    os.makedirs("./tmp")
    print("Created ./tmp directory for YOLO temporary files")

# ============================
# YOLO 모델 로드
# ============================
print("=" * 50)
print("  Loading YOLO11 Model...")
print("=" * 50)

yolo_model = None
yolo_model_type = None  # 'custom' 만 사용

if YOLO_AVAILABLE:
    try:
        # 커스텀 모델만 사용
        if os.path.exists(YOLO_MODEL_PATH):
            print(f"🔍 Found custom model: {YOLO_MODEL_PATH}")
            print(f"   Loading model (this may take 10-30 seconds)...")

            # YOLO 모델 로딩 (verbose=False로 출력 최소화)
            yolo_model = YOLO(YOLO_MODEL_PATH, verbose=False)
            yolo_model_type = "custom"

            print(f"✅ Custom YOLO model loaded successfully")
            print(f"   - Model path: {YOLO_MODEL_PATH}")
            print(f"   - Model type: Custom (Traffic Light)")
            print(f"   - Classes: {len(YOLO_CLASS_NAMES)}")
            print(f"   - Class names: {list(YOLO_CLASS_NAMES.values())}")
        else:
            print(f"❌ Custom model not found: {YOLO_MODEL_PATH}")
            print(f"   Please place your custom model file in: {YOLO_MODEL_PATH}")
            print(f"   Continuing WITHOUT traffic light detection...")
            print(f"   → Only Haar Cascade (signs) + Line Tracing will work")

    except KeyboardInterrupt:
        print("\n⚠️  YOLO loading interrupted by user")
        print("   Continuing without YOLO detection...")
        yolo_model = None
    except Exception as e:
        print(f"⚠️  Error loading YOLO model: {e}")
        print(f"   Error type: {type(e).__name__}")
        print("   Continuing without YOLO detection...")
        yolo_model = None
else:
    print("⚠️  YOLO not available, will skip traffic light detection")
    print("   Install with: pip install ultralytics")

print()

# ============================
# Haar Cascade 분류기 로드
# ============================
print("=" * 50)
print("  Loading Haar Cascade Classifiers...")
print("=" * 50)

# Haar Cascade models 경로 설정 (표지판용)
stop_cascade_path = "./xml/stop_sign.xml"
no_drive_cascade_path = "./xml/no_drive_sign.xml"

# Haar Cascade models 로드
stop_cascade = cv2.CascadeClassifier(stop_cascade_path)
no_drive_cascade = cv2.CascadeClassifier(no_drive_cascade_path)

# 표지판 모델 확인
if stop_cascade.empty():
    print("⚠️  Warning: stop_sign.xml not found")
else:
    print("✅ stop_sign.xml loaded successfully (STOP sign)")

if no_drive_cascade.empty():
    print("⚠️  Warning: no_drive_sign.xml not found")
else:
    print("✅ no_drive_sign.xml loaded successfully (NO DRIVE sign)")

print("Haar Cascade classifiers loaded\n")

# ============================
# 3단계: 트랙바 및 윈도우 설정
# ============================
print("=" * 50)
print("  STEP 4: Setting up Trackbars and Windows...")
print("=" * 50)


def nothing(x):
    """트랙바 콜백 함수"""
    pass


# 윈도우 생성
cv2.namedWindow("Camera Settings", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Camera Settings", 500, 1000)

cv2.namedWindow("1_Frame", cv2.WINDOW_NORMAL)
cv2.namedWindow("2_frame_transformed", cv2.WINDOW_NORMAL)
cv2.namedWindow("3_gray_frame", cv2.WINDOW_NORMAL)
cv2.namedWindow("4_Processed Frame", cv2.WINDOW_NORMAL)
cv2.namedWindow("5_YOLO_Traffic_Light", cv2.WINDOW_NORMAL)
cv2.namedWindow("6_Sign_Detection", cv2.WINDOW_NORMAL)

# 서보 모터 트랙바
cv2.createTrackbar("Servo_1_Angle", "Camera Settings", DEFAULT_SERVO_1, 180, nothing)
cv2.createTrackbar("Servo_2_Angle", "Camera Settings", DEFAULT_SERVO_2, 110, nothing)

# 이미지 처리 트랙바
cv2.createTrackbar("ROI_Top_Y", "Camera Settings", 695, 1000, nothing)
cv2.createTrackbar("ROI_Bottom_Y", "Camera Settings", 812, 1000, nothing)
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

# RGB 가중치 트랙바
cv2.createTrackbar("R_weight", "Camera Settings", DEFAULT_R_WEIGHT, 100, nothing)
cv2.createTrackbar("G_weight", "Camera Settings", DEFAULT_G_WEIGHT, 100, nothing)
cv2.createTrackbar("B_weight", "Camera Settings", DEFAULT_B_WEIGHT, 100, nothing)

# ⭐ YOLO 설정 트랙바
cv2.createTrackbar(
    "YOLO_Confidence", "Camera Settings", DEFAULT_YOLO_CONFIDENCE, 100, nothing
)
cv2.createTrackbar("YOLO_IOU", "Camera Settings", DEFAULT_YOLO_IOU, 100, nothing)

# 감지 프레임 선택 트랙바
cv2.createTrackbar("Detect_Frame_Source", "Camera Settings", 0, 2, nothing)

# 표지판 반응 모드 트랙바
cv2.createTrackbar("Sign_Reaction_Mode", "Camera Settings", 0, 3, nothing)

print("Trackbars and windows configured successfully")
print("⭐ YOLO Confidence/IOU trackbars added")
print("⭐ Detect_Frame_Source: 0=Original(BGR), 1=Gray, 2=Gray(RGB Weighted)")
print("⭐ Sign_Reaction_Mode: 0=Stop, 1=Reverse, 2=Avoid, 3=Ignore\n")

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
        그레이스케일 이미지
    """
    # 가중치를 0~1 범위로 정규화
    r_weight /= 100.0
    g_weight /= 100.0
    b_weight /= 100.0

    # OpenCV는 BGR 순서
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
    2. RGB 가중치 기반 그레이스케일로 엷은 회색 감지
    3. 두 마스크 결합
    4. 노이즈 제거
    """
    # HSV 변환 (빨간색 감지)
    hsv_frame = cv2.cvtColor(color_frame, cv2.COLOR_BGR2HSV)

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

    # 엷은 회색/흰색 감지
    threshold_gray = max(detect_value - 30, 80)
    _, mask_gray = cv2.threshold(gray_frame, threshold_gray, 255, cv2.THRESH_BINARY)

    # 어두운 부분 제외
    dark_threshold = 50
    _, mask_dark = cv2.threshold(gray_frame, dark_threshold, 255, cv2.THRESH_BINARY)
    mask_gray = cv2.bitwise_and(mask_gray, mask_dark)

    # 빨간색과 회색 마스크 결합
    mask_lines = cv2.bitwise_or(mask_red, mask_gray)

    # 노이즈 제거
    kernel = np.ones((3, 3), np.uint8)
    mask_lines = cv2.morphologyEx(mask_lines, cv2.MORPH_CLOSE, kernel)
    mask_lines = cv2.morphologyEx(mask_lines, cv2.MORPH_OPEN, kernel)

    return mask_lines


def visualize_direction_on_frame(
    binary_frame,
    direction,
    left_sum,
    center_sum,
    right_sum,
    rgb_weights,
    traffic_light_stop=False,
    sign_stop=False,
):
    """
    프레임에 방향 정보 시각화 (3등분 방식 + 신호등/표지판 상태)

    Args:
        binary_frame: 이진화된 프레임
        direction: 결정된 방향
        left_sum, center_sum, right_sum: 히스토그램 합
        rgb_weights: RGB 가중치 튜플
        traffic_light_stop: 신호등으로 인한 정지 상태
        sign_stop: 표지판으로 인한 정지 상태
    """
    # 컬러 이미지로 변환
    frame_color = cv2.cvtColor(binary_frame, cv2.COLOR_GRAY2BGR)
    h, w = frame_color.shape[:2]

    # 방향 텍스트 배경
    overlay = frame_color.copy()
    cv2.rectangle(overlay, (0, 0), (w, 110), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, frame_color, 0.3, 0, frame_color)

    # ⭐ 정지 상태 표시 (우선순위: 신호등 > 표지판)
    if traffic_light_stop:
        direction_text = "STOP (RED LIGHT)"
        direction_color = (0, 0, 255)  # 텍스트: 빨간색
        # 배경 강조 (노란색) - BGR 형식: (B=0, G=255, R=255) = 노란색
        cv2.rectangle(overlay, (0, 0), (w, 40), (0, 255, 255), -1)
        cv2.addWeighted(overlay, 0.8, frame_color, 0.2, 0, frame_color)
    elif sign_stop:
        direction_text = "STOP (SIGN)"
        direction_color = (0, 0, 255)  # 텍스트: 빨간색
        # 배경 강조 (노란색) - BGR 형식: (B=0, G=255, R=255) = 노란색
        cv2.rectangle(overlay, (0, 0), (w, 40), (0, 255, 255), -1)
        cv2.addWeighted(overlay, 0.8, frame_color, 0.2, 0, frame_color)
    else:
        # 정상 자율주행 상태
        direction_text = f"AUTO: {direction}"
        direction_color = (0, 255, 0) if direction == "UP" else (0, 255, 255)

    cv2.putText(
        frame_color,
        direction_text,
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
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

    # 비율 표시
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

    # 3등분 구분선 표시
    left_line = w // 3
    right_line = 2 * w // 3

    cv2.line(frame_color, (left_line, 0), (left_line, h), (255, 0, 0), 2)
    cv2.line(frame_color, (right_line, 0), (right_line, h), (255, 0, 0), 2)

    # 라벨
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
    프레임 처리 및 도로선 검출 (자율주행용)

    처리 단계:
    1. 실제 해상도 확인 및 ROI 계산
    2. ROI 영역 시각화
    3. 원근 변환 적용
    4. RGB 가중치 기반 그레이스케일 변환
    5. 도로선 감지
    """
    # 실제 해상도 확인 및 ROI 계산
    actual_h, actual_w = frame.shape[:2]
    pts_src, top_y, bottom_y = calculate_roi_points(
        actual_w, actual_h, roi_top_y, roi_bottom_y
    )

    # ROI 영역 시각화
    frame_with_rect = apply_roi_visualization(
        frame, pts_src, actual_w, actual_h, top_y, bottom_y
    )
    cv2.imshow("1_Frame", frame_with_rect)

    # 원근 변환
    frame_transformed = apply_perspective_transform(frame, pts_src)
    cv2.imshow("2_frame_transformed", frame_transformed)

    # RGB 가중치 기반 그레이스케일 변환
    gray_frame = weighted_gray(frame_transformed, r_weight, g_weight, b_weight)
    cv2.imshow("3_gray_frame", gray_frame)

    # 도로선 감지
    binary_frame = detect_road_lines(frame_transformed, gray_frame, detect_value)
    cv2.imshow("4_Processed Frame", binary_frame)

    return binary_frame


print("Image processing functions defined successfully\n")

# ============================
# YOLO 신호등 및 Haar 표지판 감지 함수
# ============================
print("=" * 50)
print("  Defining YOLO Traffic Light and Haar Sign Detection Functions")
print("=" * 50)


def detect_traffic_lights_yolo(frame, confidence_threshold=0.5, iou_threshold=0.45):
    """
    YOLO11로 신호등 감지

    Args:
        frame: 입력 프레임 (BGR)
        confidence_threshold: 신뢰도 임계값 (0~1)
        iou_threshold: NMS IOU 임계값 (0~1)

    Returns:
        tuple: (red_detected, green_detected, annotated_frame, detection_info)
    """
    red_detected = False
    green_detected = False
    annotated_frame = frame.copy()
    h, w = annotated_frame.shape[:2]

    detection_info = {
        "red_count": 0,
        "green_count": 0,
        "traffic_light_count": 0,
        "red_positions": [],
        "green_positions": [],
        "traffic_light_positions": [],
    }

    # YOLO 모델이 없으면 빈 결과 반환
    if yolo_model is None:
        cv2.putText(
            annotated_frame,
            "YOLO MODEL NOT LOADED",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2,
        )
        return red_detected, green_detected, annotated_frame, detection_info

    try:
        # ⭐ frame을 JPEG 이미지로 저장 후 YOLO 추론 실행
        # (cv2와 YOLO 호환성 문제 해결)
        temp_path = "./tmp/yolo_temp.jpg"
        cv2.imwrite(temp_path, frame)

        # YOLO 추론 실행 (JPEG 파일 경로 전달)
        results = yolo_model(
            temp_path, conf=confidence_threshold, iou=iou_threshold, verbose=False
        )

        # 결과 처리
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # 바운딩 박스 좌표
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])

                # ⭐ 커스텀 모델 전용: 빨간불/초록불 구분
                if class_id == 0:  # traffic_red_light
                    red_detected = True
                    detection_info["red_count"] += 1
                    detection_info["red_positions"].append(
                        {
                            "x": x1,
                            "y": y1,
                            "w": x2 - x1,
                            "h": y2 - y1,
                            "center_x": (x1 + x2) // 2,
                            "confidence": confidence,
                        }
                    )
                    # 빨간색 박스
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                    label = f"RED {confidence:.2f}"
                    cv2.putText(
                        annotated_frame,
                        label,
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 0, 255),
                        2,
                    )

                elif class_id == 1:  # traffic_green_light
                    green_detected = True
                    detection_info["green_count"] += 1
                    detection_info["green_positions"].append(
                        {
                            "x": x1,
                            "y": y1,
                            "w": x2 - x1,
                            "h": y2 - y1,
                            "center_x": (x1 + x2) // 2,
                            "confidence": confidence,
                        }
                    )
                    # 초록색 박스
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
                    label = f"GREEN {confidence:.2f}"
                    cv2.putText(
                        annotated_frame,
                        label,
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2,
                    )

                elif class_id == 2:  # traffic_light (일반)
                    detection_info["traffic_light_count"] += 1
                    detection_info["traffic_light_positions"].append(
                        {
                            "x": x1,
                            "y": y1,
                            "w": x2 - x1,
                            "h": y2 - y1,
                            "center_x": (x1 + x2) // 2,
                            "confidence": confidence,
                        }
                    )
                    # 회색 박스
                    cv2.rectangle(
                        annotated_frame, (x1, y1), (x2, y2), (128, 128, 128), 2
                    )
                    label = f"LIGHT {confidence:.2f}"
                    cv2.putText(
                        annotated_frame,
                        label,
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (128, 128, 128),
                        2,
                    )

    except Exception as e:
        print(f"YOLO detection error: {e}")

    # 상태 텍스트 표시 (커스텀 모델 전용)
    if red_detected:
        status_text = "TRAFFIC LIGHT: RED - STOP (YOLO Custom)"
        status_color = (0, 0, 255)
    elif green_detected:
        status_text = "TRAFFIC LIGHT: GREEN - GO (YOLO Custom)"
        status_color = (0, 255, 0)
    else:
        status_text = "TRAFFIC LIGHT: NONE (YOLO Custom)"
        status_color = (255, 255, 255)

    cv2.putText(
        annotated_frame,
        status_text,
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        status_color,
        2,
    )

    # 감지 개수 표시
    info_text = f"Detections: R={detection_info['red_count']} G={detection_info['green_count']} T={detection_info['traffic_light_count']}"

    cv2.putText(
        annotated_frame,
        info_text,
        (10, h - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 0),
        1,
    )

    return red_detected, green_detected, annotated_frame, detection_info


def detect_traffic_signs(
    detect_frame, display_frame, r_weight, g_weight, b_weight, frame_source=0
):
    """
    Haar Cascade로 표지판 감지 (Stop, No Drive)

    처리 과정:
    1. 선택된 프레임 소스에서 그레이스케일 변환
    2. Haar Cascade로 정지 표지판 감지
    3. Haar Cascade로 통행금지 표지판 감지
    4. 감지된 표지판에 윤곽선 + 텍스트 표시

    Args:
        detect_frame: 감지에 사용할 프레임
        display_frame: 결과 표시용 프레임
        r_weight, g_weight, b_weight: RGB 가중치
        frame_source: 프레임 소스 (0~2)

    Returns:
        tuple: (stop_detected, no_drive_detected, annotated_frame, detection_info)
    """
    # 감지용 그레이스케일 준비
    if len(detect_frame.shape) == 2:
        gray_frame = detect_frame
    else:
        gray_frame = cv2.cvtColor(detect_frame, cv2.COLOR_BGR2GRAY)

    # 정지 표지판 감지
    stop_signs = stop_cascade.detectMultiScale(
        gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
    )

    # 통행금지 표지판 감지
    no_drive_signs = no_drive_cascade.detectMultiScale(
        gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
    )

    stop_detected = len(stop_signs) > 0
    no_drive_detected = len(no_drive_signs) > 0

    # 프레임에 감지 결과 그리기
    if len(display_frame.shape) == 2:
        annotated_frame = cv2.cvtColor(display_frame, cv2.COLOR_GRAY2BGR)
    else:
        annotated_frame = display_frame.copy()

    h, w = annotated_frame.shape[:2]

    # 프레임 소스 정보 표시
    source_names = {0: "Original(BGR->GRAY)", 1: "Gray", 2: "Gray(RGB Weighted)"}
    source_text = f"Detect Source: {source_names.get(frame_source, 'Unknown')}"
    cv2.putText(
        annotated_frame,
        source_text,
        (10, h - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 0),
        1,
    )

    # 감지 정보 저장
    detection_info = {
        "stop_count": len(stop_signs),
        "no_drive_count": len(no_drive_signs),
        "stop_positions": [],
        "no_drive_positions": [],
        "largest_object": None,
        "object_position": "NONE",
    }

    # 정지 표지판 표시 (빨간색 윤곽선)
    for x, y, obj_w, obj_h in stop_signs:
        cv2.rectangle(annotated_frame, (x, y), (x + obj_w, y + obj_h), (0, 0, 255), 3)
        cv2.putText(
            annotated_frame,
            f"STOP ({obj_w}x{obj_h})",
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2,
        )
        detection_info["stop_positions"].append(
            {
                "x": x,
                "y": y,
                "w": obj_w,
                "h": obj_h,
                "center_x": x + obj_w // 2,
                "size": obj_w * obj_h,
            }
        )

    # 통행금지 표지판 표시 (파란색 윤곽선)
    for x, y, obj_w, obj_h in no_drive_signs:
        cv2.rectangle(annotated_frame, (x, y), (x + obj_w, y + obj_h), (255, 0, 0), 3)
        cv2.putText(
            annotated_frame,
            f"NO DRIVE ({obj_w}x{obj_h})",
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 0, 0),
            2,
        )
        detection_info["no_drive_positions"].append(
            {
                "x": x,
                "y": y,
                "w": obj_w,
                "h": obj_h,
                "center_x": x + obj_w // 2,
                "size": obj_w * obj_h,
            }
        )

    # 가장 큰 객체 찾기 및 위치 판단
    all_objects = (
        detection_info["stop_positions"] + detection_info["no_drive_positions"]
    )
    if all_objects:
        largest = max(all_objects, key=lambda obj: obj["size"])
        detection_info["largest_object"] = largest

        # 좌/중앙/우 위치 판단
        center_x = largest["center_x"]
        if center_x < w // 3:
            detection_info["object_position"] = "LEFT"
        elif center_x > 2 * w // 3:
            detection_info["object_position"] = "RIGHT"
        else:
            detection_info["object_position"] = "CENTER"

        # 위치 정보 표시
        pos_text = f"Position: {detection_info['object_position']}"
        cv2.putText(
            annotated_frame,
            pos_text,
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2,
        )

    # 표지판 상태 표시 (상단)
    if stop_detected:
        status_text = "SIGN: STOP (Haar Cascade)"
        status_color = (0, 0, 255)
    elif no_drive_detected:
        status_text = "SIGN: NO DRIVE (Haar Cascade)"
        status_color = (255, 0, 0)
    else:
        status_text = "SIGN: NONE"
        status_color = (255, 255, 255)

    cv2.putText(
        annotated_frame,
        status_text,
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        status_color,
        2,
    )

    return stop_detected, no_drive_detected, annotated_frame, detection_info


def get_detection_frame(frame, gray_frame, gray_rgb_frame, frame_source):
    """
    트랙바로 선택된 프레임 소스 반환

    Args:
        frame: 원본 프레임 (컬러)
        gray_frame: 일반 그레이 프레임
        gray_rgb_frame: RGB 강조(가중치) 그레이 프레임
        frame_source: 선택된 소스 (0, 1, 2)

    Returns:
        선택된 프레임
    """
    if frame_source == 0:
        return frame
    elif frame_source == 1:
        return gray_frame
    elif frame_source == 2:
        return gray_rgb_frame
    else:
        return frame


print("YOLO Traffic Light and Haar Sign detection functions defined successfully\n")

# ============================
# 5단계: 차량 제어 함수 정의
# ============================
print("=" * 50)
print("  STEP 6: Defining Car Control Functions")
print("=" * 50)


def set_motor_speeds(motor_0, motor_1, motor_2, motor_3):
    """
    기어 모터 속도 설정

    Args:
        motor_0, motor_1: 왼쪽 바퀴 (0, 1번)
        motor_2, motor_3: 오른쪽 바퀴 (2, 3번)
    """
    if not mouse_use:
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
    """전진"""
    set_motor_speeds(speed_left, speed_left, speed_right, speed_right)


def car_stop():
    """정지"""
    set_motor_speeds(0, 0, 0, 0)


def car_left(speed_left, speed_right):
    """좌회전"""
    set_motor_speeds(-speed_left, -speed_left, speed_right, speed_right)


def car_right(speed_left, speed_right):
    """우회전"""
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
# 6단계: 서보 모터 제어 함수
# ============================
print("=" * 50)
print("  STEP 7: Defining Servo Motor Control Functions")
print("=" * 50)


def rotate_servo(servo_id, angle):
    """
    서보 모터 회전 제어

    Args:
        servo_id: 서보 모터 ID (1: 좌우, 2: 상하)
        angle: 회전 각도
    """
    if servo_id == 2 and angle > 110:
        angle = 110
    bot.Ctrl_Servo(servo_id, angle)


print("Servo motor control functions defined successfully\n")

# ============================
# 7단계: 방향 결정 함수
# ============================
print("=" * 50)
print("  STEP 8: Defining Direction Decision Functions")
print("=" * 50)


def analyze_histogram(histogram):
    """
    히스토그램 3등분 분석

    분할 방식:
    - LEFT: 0% ~ 33%
    - CENTER: 33% ~ 66%
    - RIGHT: 66% ~ 100%
    """
    length = len(histogram)

    left_end = length // 3
    right_start = 2 * length // 3

    left_sum = int(np.sum(histogram[:left_end]))
    center_sum = int(np.sum(histogram[left_end:right_start]))
    right_sum = int(np.sum(histogram[right_start:]))

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

    우선순위:
    1. abs(right - left) > threshold → 회전
    2. center_ratio < 0.2 → 직진
    3. 좌우 평균 < up_threshold → 막다른 골목 → 랜덤
    4. 기본 → 직진
    """
    # 히스토그램 3등분 분석
    left_sum, center_sum, right_sum, left_ratio, center_ratio, right_ratio = (
        analyze_histogram(histogram)
    )

    if DEBUG_MODE:
        print(f"Histogram Analysis:")
        print(f"  LEFT: {left_sum:7d} (ratio: {left_ratio:.3f})")
        print(f"  CENTER: {center_sum:7d} (ratio: {center_ratio:.3f})")
        print(f"  RIGHT: {right_sum:7d} (ratio: {right_ratio:.3f})")
        print(
            f"  L-R Diff: {right_sum - left_sum:7d} | Threshold: {direction_threshold}"
        )

    # 좌우 차이 체크
    if abs(right_sum - left_sum) > direction_threshold:
        if right_sum > left_sum:
            direction = "LEFT"
        else:
            direction = "RIGHT"

        if DEBUG_MODE:
            print(f"Decision: Turn {direction}")

        return direction, left_sum, center_sum, right_sum

    # 중앙 윤곽선 체크
    if center_ratio < CENTER_CLEAR_THRESHOLD:
        if DEBUG_MODE:
            print(f"  Center is CLEAR (ratio: {center_ratio:.3f})")
            print("Decision: Go STRAIGHT (AUTO DRIVE)")

        return "UP", left_sum, center_sum, right_sum

    # 막다른 골목 감지
    left_right_avg = (left_sum + right_sum) // 2

    if DEBUG_MODE:
        print(f"  L-R Average: {left_right_avg:7d} | Up Threshold: {up_threshold}")

    if left_right_avg < up_threshold:
        if DEBUG_MODE:
            print("\n" + "=" * 60)
            print("WARNING: Dead End Detected!")
            print("=" * 60)

        # 부저 알림
        if USE_BEEP:
            for _ in range(3):
                bot.Ctrl_BEEP_Switch(1)
                time.sleep(0.15)
                bot.Ctrl_BEEP_Switch(0)
                time.sleep(0.1)

        # 랜덤 방향 선택
        random_direction = random.choice(["LEFT", "RIGHT"])

        if DEBUG_MODE:
            print(f"Random Direction Selected: {random_direction}")
            print("=" * 60 + "\n")

        return random_direction, left_sum, center_sum, right_sum

    # 직진 (기본값)
    if DEBUG_MODE:
        print("Decision: Go straight (AUTO DRIVE)")

    return "UP", left_sum, center_sum, right_sum


print("Direction decision functions defined successfully\n")

# ============================
# 보조 함수 정의
# ============================
print("=" * 50)
print("  Defining Helper Functions")
print("=" * 50)


def handle_keyboard_input():
    """
    키보드 입력 처리

    Returns:
        str: "EXIT" (종료), "CONTINUE" (계속)
    """
    global mouse_use, led_state, beep_state

    key = cv2.waitKey(30) & 0xFF

    # ESC: 종료
    if key == 27:
        print("\nExiting...")
        return "EXIT"

    # SPACE: 모터 토글
    elif key == 32:
        mouse_use = not mouse_use
        if mouse_use:
            print("\n" + "=" * 50)
            print("Motor: ENABLED")
            print("=" * 50)
        else:
            print("\n" + "=" * 50)
            print("Motor: DISABLED")
            print("=" * 50)
            car_stop()

    # 'l': LED 토글
    elif key == ord("l"):
        led_state = not led_state
        if led_state:
            bot.Ctrl_WQ2812_ALL(1, 2)
            print(f"LED: ON")
        else:
            bot.Ctrl_WQ2812_ALL(0, 0)
            print(f"LED: OFF")

    # 'b': 부저 토글
    elif key == ord("b"):
        beep_state = not beep_state
        bot.Ctrl_BEEP_Switch(1 if beep_state else 0)
        print(f"Beep: {'ON' if beep_state else 'OFF'}")

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
        "r_weight": cv2.getTrackbarPos("R_weight", "Camera Settings"),
        "g_weight": cv2.getTrackbarPos("G_weight", "Camera Settings"),
        "b_weight": cv2.getTrackbarPos("B_weight", "Camera Settings"),
        "detect_frame_source": cv2.getTrackbarPos(
            "Detect_Frame_Source", "Camera Settings"
        ),
        "sign_reaction_mode": cv2.getTrackbarPos(
            "Sign_Reaction_Mode", "Camera Settings"
        ),
        "yolo_confidence": cv2.getTrackbarPos("YOLO_Confidence", "Camera Settings")
        / 100.0,
        "yolo_iou": cv2.getTrackbarPos("YOLO_IOU", "Camera Settings") / 100.0,
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

    bot.Ctrl_WQ2812_ALL(0, 0)
    print("LED turned off")

    bot.Ctrl_BEEP_Switch(0)
    print("Beeper turned off")

    bot.Ctrl_Servo(1, 90)
    bot.Ctrl_Servo(2, 25)
    print("Servo motors returned to initial position")

    cap.release()
    cv2.destroyAllWindows()
    print("Camera released")

    # ⭐ YOLO 임시 파일 정리
    temp_path = "./tmp/yolo_temp.jpg"
    if os.path.exists(temp_path):
        os.remove(temp_path)
        print("YOLO temporary file removed")

    del bot
    print("Raspbot object deleted")

    print("\nCleanup completed successfully!")
    print("=" * 50)


print("Helper functions defined successfully\n")

# ============================
# 8단계: 메인 루프 실행
# ============================
print("=" * 50)
print("  STEP 9: Starting Main Loop")
print("=" * 50)
print("Controls:")
print("  ESC   : Exit")
print("  SPACE : Motor toggle (ON/OFF)")
print("  'l'   : Toggle LED")
print("  'b'   : Toggle Beeper")
print("=" * 50)
print("⭐ YOLO11 Custom + Haar Cascade Hybrid System:")

# 모델 상태 표시
if yolo_model_type == "custom":
    print("  📦 YOLO Model: CUSTOM (Traffic Light with R/G distinction)")
    print("  🔴 RED Light (YOLO) → Motor STOP (wait for GREEN)")
    print("  🟢 GREEN Light (YOLO) → Release STOP state, Resume AUTO DRIVE")
else:
    print("  ⚠️  YOLO Model: NOT LOADED")
    print("  ⚠️  Traffic Light detection DISABLED")
    print("  💡 Place custom model at: ./models/traffic_modeln.pt")

print("  🛑 STOP Sign (Haar) → Motor STOP (until sign disappears)")
print("  🚫 NO DRIVE Sign (Haar) → Motor STOP (until sign disappears)")
print("  ✅ No Signal → Auto Driving (Line Tracing)")
print("=" * 50)
print("⭐ Priority:")
print("  1. Traffic Light (YOLO11) - Highest")
print("  2. Traffic Sign (Haar Cascade) - Middle")
print("  3. Auto Driving (Line Tracing) - Default")
print("=" * 50)

start_time = time.time()
led_state = LED_ON_START
beep_state = False

try:
    while True:

        frame_count += 1

        # 프레임 상태 표시 (10프레임마다)
        if frame_count % 10 == 0:
            print("\n" + "-" * 50)
            print(f"Frame: {frame_count} | Motor: {'ON' if mouse_use else 'OFF'}")

            # 상태 표시
            if waiting_for_green:
                if red_light_active:
                    print("🔴 State: RED LIGHT detected (YOLO) - MOTOR STOPPED")
                else:
                    print("⏳ State: Waiting for GREEN light (RED disappeared)")
            elif stop_sign_active or no_drive_sign_active:
                sign_type = "STOP" if stop_sign_active else "NO DRIVE"
                print(f"🛑 State: {sign_type} sign detected (Haar) - MOTOR STOPPED")
            else:
                print("✅ State: Normal AUTO DRIVING")

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

        # ✅ 감지용 3가지 프레임 생성
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_rgb_frame = weighted_gray(
            frame, params["r_weight"], params["g_weight"], params["b_weight"]
        )

        # 트랙바에서 선택된 프레임 소스 가져오기
        detect_frame = get_detection_frame(
            frame, gray_frame, gray_rgb_frame, params["detect_frame_source"]
        )

        # ═══════════════════════════════════════════════════════════
        # 우선순위 1: 신호등 감지 (YOLO11 - 최우선)
        # ═══════════════════════════════════════════════════════════
        red_detected, green_detected, traffic_frame, traffic_info = (
            detect_traffic_lights_yolo(
                frame, params["yolo_confidence"], params["yolo_iou"]
            )
        )

        # 신호등 감지 화면 표시
        cv2.imshow("5_YOLO_Traffic_Light", traffic_frame)

        # ═══════════════════════════════════════════════════════════
        # 신호등 제어 로직 (상태 기반)
        # ═══════════════════════════════════════════════════════════

        # === 우선순위 1-1: 초록불 처리 (정지 상태 해제) ===
        if green_detected and waiting_for_green:
            # 처음 감지된 경우에만 부저
            if not green_beep_played:
                if USE_BEEP:
                    bot.Ctrl_BEEP_Switch(1)
                    time.sleep(0.1)
                    bot.Ctrl_BEEP_Switch(0)
                    green_beep_played = True

                if DEBUG_MODE:
                    print(f"\n{'='*50}")
                    print("🟢 GREEN LIGHT DETECTED (YOLO)!")
                    print("   ▶️  Releasing ALL STOP states")
                    print("   ▶️  Resuming AUTO DRIVING")
                    print(f"{'='*50}")

            # ⭐ 모든 상태 완전 리셋
            waiting_for_green = False
            red_light_active = False
            red_beep_played = False
            green_light_active = False
            green_beep_played = False
            stop_sign_active = False
            stop_beep_played = False
            no_drive_sign_active = False
            no_drive_beep_played = False

            if DEBUG_MODE:
                print("✅ All states RESET (traffic light + signs)")
                print("✅ AUTO DRIVING mode resumed\n")

        # === 우선순위 1-2: 빨간불 처리 (정지 상태 진입) ===
        elif red_detected:
            # 처음 감지된 경우
            if not red_light_active:
                red_light_active = True
                waiting_for_green = True

                if DEBUG_MODE:
                    print(f"\n{'='*50}")
                    print("🔴 RED LIGHT DETECTED (YOLO)!")
                    print("   ⏸️  Motor STOPPED")
                    print("   ⏳ Waiting for GREEN light...")
                    print(f"{'='*50}")

            # 부저는 최초 1회만
            if USE_BEEP and not red_beep_played:
                bot.Ctrl_BEEP_Switch(1)
                time.sleep(0.1)
                bot.Ctrl_BEEP_Switch(0)
                red_beep_played = True
                if DEBUG_MODE:
                    print("🔊 Beep for RED light (1 time only)")

        # ═══════════════════════════════════════════════════════════
        # 우선순위 2: 표지판 감지 (Haar Cascade - 신호등이 없을 때만)
        # ═══════════════════════════════════════════════════════════
        if not waiting_for_green:
            stop_detected, no_drive_detected, sign_frame, sign_info = (
                detect_traffic_signs(
                    detect_frame,
                    detect_frame,
                    params["r_weight"],
                    params["g_weight"],
                    params["b_weight"],
                    params["detect_frame_source"],
                )
            )

            # 표지판 감지 화면 표시
            cv2.imshow("6_Sign_Detection", sign_frame)

            # === STOP 표지판 처리 ===
            if stop_detected:
                if not stop_sign_active:
                    stop_sign_active = True
                    stop_beep_played = False

                    if DEBUG_MODE:
                        print(f"\n{'='*50}")
                        print(
                            f"🛑 STOP sign DETECTED (Haar)! Position: {sign_info['object_position']}"
                        )
                        print(f"{'='*50}")

                if USE_BEEP and not stop_beep_played:
                    bot.Ctrl_BEEP_Switch(1)
                    time.sleep(0.1)
                    bot.Ctrl_BEEP_Switch(0)
                    stop_beep_played = True
                    if DEBUG_MODE:
                        print("🔊 Beep for STOP sign (1 time only)")

                car_stop()

                if DEBUG_MODE and frame_count % 30 == 0:
                    print("⏸️  Motor STOPPED (STOP sign active)")

            else:
                if stop_sign_active:
                    stop_sign_active = False
                    stop_beep_played = False
                    if DEBUG_MODE:
                        print(f"\n{'='*50}")
                        print("✅ STOP sign DISAPPEARED - Resuming auto drive")
                        print(f"{'='*50}\n")

            # === NO DRIVE 표지판 처리 ===
            if no_drive_detected:
                if not no_drive_sign_active:
                    no_drive_sign_active = True
                    no_drive_beep_played = False

                    if DEBUG_MODE:
                        print(f"\n{'='*50}")
                        print(
                            f"🚫 NO DRIVE sign DETECTED (Haar)! Position: {sign_info['object_position']}"
                        )
                        print(f"{'='*50}")

                if USE_BEEP and not no_drive_beep_played:
                    bot.Ctrl_BEEP_Switch(1)
                    time.sleep(0.1)
                    bot.Ctrl_BEEP_Switch(0)
                    no_drive_beep_played = True
                    if DEBUG_MODE:
                        print("🔊 Beep for NO DRIVE sign (1 time only)")

                car_stop()

                if DEBUG_MODE and frame_count % 30 == 0:
                    print("⏸️  Motor STOPPED (NO DRIVE sign active)")

            else:
                if no_drive_sign_active:
                    no_drive_sign_active = False
                    no_drive_beep_played = False
                    if DEBUG_MODE:
                        print(f"\n{'='*50}")
                        print("✅ NO DRIVE sign DISAPPEARED - Resuming auto drive")
                        print(f"{'='*50}\n")

        else:
            # 신호등 대기 중이면 표지판 감지 화면만 표시
            empty_frame = detect_frame.copy()
            if len(empty_frame.shape) == 2:
                empty_frame = cv2.cvtColor(empty_frame, cv2.COLOR_GRAY2BGR)
            cv2.putText(
                empty_frame,
                "WAITING FOR GREEN LIGHT (YOLO)",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2,
            )
            cv2.imshow("6_Sign_Detection", empty_frame)

        # ═══════════════════════════════════════════════════════════
        # 우선순위 3: 자율주행 제어
        # ═══════════════════════════════════════════════════════════

        # ⭐⭐⭐ 프레임 처리는 항상 실행
        binary_frame = process_frame(
            frame,
            params["detect_value"],
            params["roi_top_y"],
            params["roi_bottom_y"],
            params["r_weight"],
            params["g_weight"],
            params["b_weight"],
        )
        histogram = np.sum(binary_frame, axis=0)

        # 방향 결정
        if DEBUG_MODE and frame_count % 10 == 0:
            print(f"\n--- Frame {frame_count} ---")
            print(
                f"RGB Weights: R={params['r_weight']}, G={params['g_weight']}, B={params['b_weight']}"
            )
            print(
                f"YOLO: Conf={params['yolo_confidence']:.2f}, IOU={params['yolo_iou']:.2f}"
            )

        direction, hist_left, hist_center, hist_right = decide_direction(
            histogram,
            params["direction_threshold"],
            params["up_threshold"],
            params["detect_value"],
            params["roi_top_y"],
            params["roi_bottom_y"],
        )

        # 방향 정보 시각화
        rgb_weights = (params["r_weight"], params["g_weight"], params["b_weight"])
        any_sign_stop = stop_sign_active or no_drive_sign_active
        processed_frame_visual = visualize_direction_on_frame(
            binary_frame,
            direction,
            hist_left,
            hist_center,
            hist_right,
            rgb_weights,
            traffic_light_stop=waiting_for_green,
            sign_stop=any_sign_stop,
        )
        cv2.imshow("4_Processed Frame", processed_frame_visual)

        # ⭐⭐⭐ 차량 제어
        if waiting_for_green:
            car_stop()
            if DEBUG_MODE and frame_count % 30 == 0:
                print("⏸️  Motor control SKIPPED (waiting for GREEN)")
        elif stop_sign_active or no_drive_sign_active:
            car_stop()
            if DEBUG_MODE and frame_count % 30 == 0:
                print("⏸️  Motor control SKIPPED (sign active)")
        else:
            control_car(direction, params["motor_up_speed"], params["motor_down_speed"])

        # FPS 계산
        if frame_count % 10 == 0:
            elapsed = time.time() - start_time
            fps = 10 / elapsed
            if DEBUG_MODE:
                print(f"FPS: {fps:.1f}")
            start_time = time.time()

        # 키 입력 처리
        result = handle_keyboard_input()
        if result == "EXIT":
            break

        # 프레임 처리 지연 최소화
        time.sleep(0.01)

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
