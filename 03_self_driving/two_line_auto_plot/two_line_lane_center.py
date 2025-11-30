#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspbot v2 두 라인 인식 기반 중앙 유지 자율주행 코드
카메라로 두 개의 라인을 인식하여 가운데 위치로 이동하며 자율주행

Copyright (C): 2015-2024, Shenzhen Yahboom Tech
Modified: 2025-11-28

═══════════════════════════════════════════════════════════
주요 특징:
═══════════════════════════════════════════════════════════
- 두 개의 라인(좌우)을 인식하여 가운데 위치 계산
- 프레임 중앙과 라인 중앙의 편차를 계산하여 차량 제어
- 원근 변환을 통한 버드아이 뷰 생성
- 히스토그램 기반 라인 위치 검출
- PID 제어 또는 간단한 비례 제어로 부드러운 주행

═══════════════════════════════════════════════════════════
실행 단계:
═══════════════════════════════════════════════════════════
1단계: 라이브러리 및 모듈 import
2단계: 하드웨어 초기화 (Raspbot, 카메라, 서보)
3단계: 트랙바 및 윈도우 설정
4단계: 이미지 처리 함수 정의
5단계: 라인 검출 함수 정의
6단계: 차량 제어 함수 정의
7단계: 중앙 유지 제어 로직 정의
8단계: 메인 루프 실행
9단계: 정리 및 종료
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
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "lib", "raspbot"))

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
DEFAULT_BASE_SPEED = 30  # 기본 전진 속도
DEFAULT_TURN_SPEED = 20  # 회전 시 속도
SPEED_BOOST = 10  # 직진 시 속도 부스트

# 라인 검출 설정
DEFAULT_DETECT_VALUE = 120  # 이진화 임계값
DEFAULT_BRIGHTNESS = 0
DEFAULT_CONTRAST = 40

# RGB 가중치
DEFAULT_R_WEIGHT = 30
DEFAULT_G_WEIGHT = 40
DEFAULT_B_WEIGHT = 60

# 라인 검출 파라미터
# 640x480 해상도 기준 (320x240의 2배)
DEFAULT_MIN_LANE_WIDTH = 100  # 최소 라인 간격 (픽셀) - 320 기준 50의 2배
DEFAULT_MAX_LANE_WIDTH = 600  # 최대 라인 간격 (픽셀) - 320 기준 300의 2배
DEFAULT_ROI_START_Y = 280  # 히스토그램 계산 ROI 시작 Y 위치 (240 기준 140의 2배)
DEFAULT_ROI_HEIGHT = 200  # 히스토그램 계산 ROI 높이 (240 기준 100의 2배)

# 제어 파라미터
DEFAULT_BIAS_THRESHOLD = 10  # 편차 임계값 (픽셀)
DEFAULT_P_GAIN = 0.5  # 비례 제어 게인
DEFAULT_MAX_BIAS = 160  # 최대 편차 (픽셀)

# 서보 모터 각도
DEFAULT_SERVO_1 = 90  # 좌우 각도 (0~180)
DEFAULT_SERVO_2 = 25  # 상하 각도 (0~110)

# ROI 설정 (퍼센트)
DEFAULT_ROI_TOP_Y = 200  # 상단 Y 위치 (0~1000)
DEFAULT_ROI_BOTTOM_Y = 800  # 하단 Y 위치 (0~1000)

# 디버그 모드
DEBUG_MODE = True

# LED 효과 사용
USE_LED_EFFECTS = True
LED_ON_START = True

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

    # 기본 해상도: 640x480
    width = 640
    height = 480
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

    # 실제 해상도에 맞게 기본값 조정
    if actual_width == 640 and actual_height == 480:
        print("   - 640x480 해상도로 동작합니다")

except Exception as e:
    print(f"\n❌ 카메라 초기화 실패: {e}\n")
    del bot
    sys.exit(1)

if LED_ON_START and USE_LED_EFFECTS:
    bot.Ctrl_WQ2812_ALL(1, 2)
    print("💡 LED 초기화 완료")

# 서보 모터 초기 위치
bot.Ctrl_Servo(1, DEFAULT_SERVO_1)
bot.Ctrl_Servo(2, DEFAULT_SERVO_2)
print(f"📷 서보 모터 초기화 완료 (S1:{DEFAULT_SERVO_1}°, S2:{DEFAULT_SERVO_2}°)")

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
    """트랙바 콜백 함수"""
    pass


# 윈도우 생성
cv2.namedWindow("Camera Settings")
cv2.namedWindow("1_Original", cv2.WINDOW_NORMAL)
cv2.namedWindow("2_Perspective", cv2.WINDOW_NORMAL)
cv2.namedWindow("3_Gray", cv2.WINDOW_NORMAL)
cv2.namedWindow("4_Binary", cv2.WINDOW_NORMAL)
cv2.namedWindow("5_Final", cv2.WINDOW_NORMAL)

cv2.resizeWindow("1_Original", 640, 480)
cv2.resizeWindow("2_Perspective", 640, 480)
cv2.resizeWindow("5_Final", 640, 480)

# 서보 모터 트랙바
cv2.createTrackbar("Servo 1 Angle", "Camera Settings", DEFAULT_SERVO_1, 180, nothing)
cv2.createTrackbar("Servo 2 Angle", "Camera Settings", DEFAULT_SERVO_2, 110, nothing)

# 이미지 처리 트랙바
cv2.createTrackbar("ROI Top Y", "Camera Settings", DEFAULT_ROI_TOP_Y, 1000, nothing)
cv2.createTrackbar(
    "ROI Bottom Y", "Camera Settings", DEFAULT_ROI_BOTTOM_Y, 1000, nothing
)
cv2.createTrackbar("Brightness", "Camera Settings", DEFAULT_BRIGHTNESS, 100, nothing)
cv2.createTrackbar("Contrast", "Camera Settings", DEFAULT_CONTRAST, 100, nothing)
cv2.createTrackbar(
    "Detect Value", "Camera Settings", DEFAULT_DETECT_VALUE, 255, nothing
)
cv2.createTrackbar("R_weight", "Camera Settings", DEFAULT_R_WEIGHT, 100, nothing)
cv2.createTrackbar("G_weight", "Camera Settings", DEFAULT_G_WEIGHT, 100, nothing)
cv2.createTrackbar("B_weight", "Camera Settings", DEFAULT_B_WEIGHT, 100, nothing)

# 제어 파라미터 트랙바
cv2.createTrackbar("Base Speed", "Camera Settings", DEFAULT_BASE_SPEED, 255, nothing)
cv2.createTrackbar("P Gain", "Camera Settings", int(DEFAULT_P_GAIN * 100), 200, nothing)
cv2.createTrackbar(
    "Bias Threshold", "Camera Settings", DEFAULT_BIAS_THRESHOLD, 100, nothing
)

# 라인 검출 파라미터 트랙바 (640x480 해상도 기준)
cv2.createTrackbar("ROI Start Y", "Camera Settings", DEFAULT_ROI_START_Y, 480, nothing)
cv2.createTrackbar("ROI Height", "Camera Settings", DEFAULT_ROI_HEIGHT, 480, nothing)

print("✅ 트랙바 및 윈도우 설정 완료\n")

# ============================
# 4단계: 이미지 처리 함수 정의
# ============================
print("=" * 50)
print("  🖼️  4단계: 이미지 처리 함수 정의")
print("=" * 50)


def weighted_gray(image, r_weight, g_weight, b_weight):
    """
    가중 그레이스케일 변환

    Args:
        image: BGR 이미지
        r_weight: R 채널 가중치 (0~100)
        g_weight: G 채널 가중치 (0~100)
        b_weight: B 채널 가중치 (0~100)

    Returns:
        가중치가 적용된 그레이스케일 이미지
    """
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


def calculate_roi_points(actual_w, actual_h, roi_top_y, roi_bottom_y):
    """
    ROI 영역 계산 (사다리꼴)

    Args:
        actual_w: 실제 이미지 너비
        actual_h: 실제 이미지 높이
        roi_top_y: 상단 Y 위치 (0~1000)
        roi_bottom_y: 하단 Y 위치 (0~1000)

    Returns:
        pts_src: 원본 이미지의 4개 점 좌표
        top_y: 상단 Y 좌표
        bottom_y: 하단 Y 좌표
    """
    # 퍼센트를 픽셀 좌표로 변환
    top_y = int(roi_top_y * actual_h / 1000)
    bottom_y = int(roi_bottom_y * actual_h / 1000)

    # 범위 제한
    top_y = max(0, min(top_y, actual_h - 1))
    bottom_y = max(0, min(bottom_y, actual_h - 1))

    # 상단이 하단보다 아래에 있으면 조정
    if top_y >= bottom_y:
        top_y = max(0, bottom_y - 50)

    # 마진 설정 (좌우 여백)
    margin = 10

    # 사다리꼴 ROI 정의 (하단이 넓고 상단이 좁음)
    pts_src = np.float32(
        [
            [margin, bottom_y],  # 좌하단
            [actual_w - margin, bottom_y],  # 우하단
            [actual_w - margin, top_y],  # 우상단
            [margin, top_y],  # 좌상단
        ]
    )

    return pts_src, top_y, bottom_y


def apply_perspective_transform(frame, pts_src):
    """
    원근 변환 적용 (버드아이 뷰)

    원본 해상도에 맞게 목표 해상도 자동 조정
    - 640x480 원본 → 640x480 변환 (정확도 우선)
    - 또는 320x240 변환 (속도 우선, 선택 가능)

    Args:
        frame: 원본 이미지
        pts_src: 원본 이미지의 4개 점 좌표

    Returns:
        원근 변환된 이미지
    """
    h, w = frame.shape[:2]

    # 원본 해상도에 맞게 목표 해상도 설정
    # 640x480 원본이면 640x480으로 유지 (정확도 우선)
    # 또는 처리 속도를 위해 320x240으로 축소 가능
    USE_FULL_RESOLUTION = True  # True: 640x480, False: 320x240

    if USE_FULL_RESOLUTION and w >= 640:
        target_w, target_h = 640, 480
    else:
        target_w, target_h = 320, 240

    # 목표 사각형 좌표
    pts_dst = np.float32(
        [
            [0, target_h],  # 좌하단
            [target_w, target_h],  # 우하단
            [target_w, 0],  # 우상단
            [0, 0],  # 좌상단
        ]
    )

    # 원근 변환 행렬 계산
    mat_affine = cv2.getPerspectiveTransform(pts_src, pts_dst)

    # 원근 변환 적용
    frame_transformed = cv2.warpPerspective(frame, mat_affine, (target_w, target_h))

    return frame_transformed


def process_frame(
    frame, detect_value, r_weight, g_weight, b_weight, roi_top_y, roi_bottom_y
):
    """
    C++ 코드 방식의 프레임 처리 및 이진화

    처리 단계:
    1. ROI 영역 계산
    2. 원본 프레임에 ROI 표시
    3. 원근 변환 적용
    4. 그레이스케일 변환
    5. 이진화 (inRange + Canny 엣지 검출)
    6. 두 결과 합산

    Args:
        frame: 원본 프레임
        detect_value: 이진화 임계값 (사용 안 함, inRange 사용)
        r_weight: R 채널 가중치
        g_weight: G 채널 가중치
        b_weight: B 채널 가중치
        roi_top_y: ROI 상단 Y 위치
        roi_bottom_y: ROI 하단 Y 위치

    Returns:
        이진화된 이미지
    """
    actual_h, actual_w = frame.shape[:2]

    # ROI 영역 계산
    pts_src, top_y, bottom_y = calculate_roi_points(
        actual_w, actual_h, roi_top_y, roi_bottom_y
    )

    # ROI 영역 시각화
    pts = pts_src.reshape((-1, 1, 2)).astype(np.int32)
    frame_with_rect = cv2.polylines(
        frame.copy(), [pts], isClosed=True, color=(0, 0, 255), thickness=2
    )

    # 해상도 정보 표시
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
    cv2.imshow("1_Original", frame_with_rect)

    # 원근 변환 적용
    frame_transformed = apply_perspective_transform(frame, pts_src)
    cv2.imshow("2_Perspective", frame_transformed)

    # 그레이스케일 변환
    gray_frame = weighted_gray(frame_transformed, r_weight, g_weight, b_weight)
    cv2.imshow("3_Gray", gray_frame)

    # C++ 코드 방식: inRange + Canny 엣지 검출
    # inRange: 밝은 영역만 추출 (200~255)
    _, frame_thresh = cv2.threshold(gray_frame, 200, 255, cv2.THRESH_BINARY)

    # Canny 엣지 검출 (C++ 코드: 900, 900)
    frame_edge = cv2.Canny(gray_frame, 900, 900, apertureSize=3, L2gradient=False)

    # 두 결과 합산
    binary_frame = cv2.add(frame_thresh, frame_edge)

    cv2.imshow("4_Binary", binary_frame)

    return binary_frame


print("✅ 이미지 처리 함수 정의 완료\n")

# ============================
# 5단계: 라인 검출 함수 정의
# ============================
print("=" * 50)
print("  🔍 5단계: 라인 검출 함수 정의")
print("=" * 50)


def calculate_histogram(binary_frame, roi_start_y=140, roi_height=100):
    """
    C++ 코드 방식의 히스토그램 계산
    각 열마다 지정된 ROI 영역(1xheight)의 합을 계산

    Args:
        binary_frame: 이진화된 이미지
        roi_start_y: ROI 시작 Y 위치 (기본값: 140)
        roi_height: ROI 높이 (기본값: 100)

    Returns:
        histogram: 각 열의 픽셀 합계 배열
    """
    h, w = binary_frame.shape[:2]

    # ROI 영역 제한
    roi_start_y = max(0, min(roi_start_y, h - 1))
    roi_end_y = min(roi_start_y + roi_height, h)

    # 각 열마다 ROI 영역의 합 계산
    histogram = np.zeros(w, dtype=np.int32)

    for i in range(w):
        # 각 열(i)에서 y=roi_start_y부터 roi_height만큼의 영역
        roi_region = binary_frame[roi_start_y:roi_end_y, i]
        histogram[i] = int(np.sum(roi_region))

    return histogram


def detect_lane_lines(
    binary_frame, min_lane_width=50, max_lane_width=300, roi_start_y=140, roi_height=100
):
    """
    C++ 코드 방식의 히스토그램을 사용하여 좌우 라인 위치 검출

    Args:
        binary_frame: 이진화된 이미지
        min_lane_width: 최소 라인 간격 (픽셀)
        max_lane_width: 최대 라인 간격 (픽셀)
        roi_start_y: 히스토그램 계산 ROI 시작 Y 위치
        roi_height: 히스토그램 계산 ROI 높이

    Returns:
        left_lane_pos: 왼쪽 라인 X 위치 (검출 실패 시 None)
        right_lane_pos: 오른쪽 라인 X 위치 (검출 실패 시 None)
        lane_center: 라인 중앙 X 위치 (검출 실패 시 None)
    """
    h, w = binary_frame.shape[:2]

    # C++ 코드 방식: 하단 영역 사용 (기본값: y=140부터 100픽셀)
    histogram = calculate_histogram(
        binary_frame, roi_start_y=roi_start_y, roi_height=roi_height
    )

    # C++ 코드 방식: 명확한 영역 구분
    # 원본 해상도에 따라 비례 조정
    # 320x240 기준: 왼쪽 0~150, 오른쪽 250~320
    # 640x480 기준: 왼쪽 0~300, 오른쪽 500~640
    if w >= 600:  # 640x480 해상도
        left_search_end = min(300, w)  # 150 * 2
        right_search_start = max(500, 0)  # 250 * 2
    else:  # 320x240 해상도
        left_search_end = min(150, w)
        right_search_start = max(250, 0)

    # 왼쪽 영역에서 최대값 위치 찾기
    left_region = histogram[:left_search_end]
    if len(left_region) > 0:
        left_max_idx = np.argmax(left_region)
        left_max_value = left_region[left_max_idx]

        # 임계값 이상인 경우만 라인으로 인식
        # 해상도에 따라 임계값 조정 (640x480은 2배)
        threshold = 2000 if w >= 600 else 1000
        if left_max_value > threshold:
            left_lane_pos = left_max_idx
        else:
            left_lane_pos = None
    else:
        left_lane_pos = None

    # 오른쪽 영역에서 최대값 위치 찾기
    right_region = histogram[right_search_start:]
    if len(right_region) > 0:
        right_max_idx = np.argmax(right_region)
        right_max_value = right_region[right_max_idx]

        # 임계값 이상인 경우만 라인으로 인식
        # 해상도에 따라 임계값 조정 (640x480은 2배)
        threshold = 2000 if w >= 600 else 1000
        if right_max_value > threshold:
            right_lane_pos = right_search_start + right_max_idx
        else:
            right_lane_pos = None
    else:
        right_lane_pos = None

    # 두 라인 모두 검출된 경우
    if left_lane_pos is not None and right_lane_pos is not None:
        lane_width = right_lane_pos - left_lane_pos

        # 라인 간격이 유효한 범위인지 확인
        if min_lane_width <= lane_width <= max_lane_width:
            # C++ 코드 방식: (RightLanePos-LeftLanePos)/2 + LeftLanePos
            lane_center = (right_lane_pos - left_lane_pos) // 2 + left_lane_pos
            return left_lane_pos, right_lane_pos, lane_center

    # 한쪽 라인만 검출된 경우 (대체 방법)
    if left_lane_pos is not None:
        # 왼쪽 라인 기준으로 오른쪽 라인 추정
        estimated_right = left_lane_pos + (w // 3)  # 대략적인 라인 간격
        if estimated_right < w:
            lane_center = (left_lane_pos + estimated_right) // 2
            return left_lane_pos, estimated_right, lane_center

    if right_lane_pos is not None:
        # 오른쪽 라인 기준으로 왼쪽 라인 추정
        estimated_left = right_lane_pos - (w // 3)  # 대략적인 라인 간격
        if estimated_left >= 0:
            lane_center = (estimated_left + right_lane_pos) // 2
            return estimated_left, right_lane_pos, lane_center

    # 라인 검출 실패
    return None, None, None


def draw_lane_lines(
    frame, left_lane_pos, right_lane_pos, lane_center, frame_center, bias
):
    """
    검출된 라인과 중앙선을 프레임에 그리기

    Args:
        frame: 원본 프레임 (BGR 또는 그레이스케일)
        left_lane_pos: 왼쪽 라인 X 위치
        right_lane_pos: 오른쪽 라인 X 위치
        lane_center: 라인 중앙 X 위치
        frame_center: 프레임 중앙 X 위치
        bias: 편차 값

    Returns:
        라인이 그려진 프레임
    """
    # 컬러 이미지로 변환 (그레이스케일인 경우)
    if len(frame.shape) == 2:
        frame_color = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    else:
        frame_color = frame.copy()

    h, w = frame_color.shape[:2]

    # 왼쪽 라인 그리기 (녹색)
    if left_lane_pos is not None:
        cv2.line(
            frame_color,
            (int(left_lane_pos), 0),
            (int(left_lane_pos), h),
            (0, 255, 0),
            2,
        )
        cv2.putText(
            frame_color,
            "L",
            (int(left_lane_pos) - 10, 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2,
        )

    # 오른쪽 라인 그리기 (녹색)
    if right_lane_pos is not None:
        cv2.line(
            frame_color,
            (int(right_lane_pos), 0),
            (int(right_lane_pos), h),
            (0, 255, 0),
            2,
        )
        cv2.putText(
            frame_color,
            "R",
            (int(right_lane_pos) + 5, 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2,
        )

    # 라인 중앙 그리기 (파란색)
    if lane_center is not None:
        cv2.line(
            frame_color,
            (int(lane_center), 0),
            (int(lane_center), h),
            (255, 0, 0),
            3,
        )
        cv2.putText(
            frame_color,
            "Lane Center",
            (int(lane_center) - 50, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (255, 0, 0),
            1,
        )

    # 프레임 중앙 그리기 (보라색)
    cv2.line(
        frame_color,
        (int(frame_center), 0),
        (int(frame_center), h),
        (255, 0, 255),
        3,
    )
    cv2.putText(
        frame_color,
        "Frame Center",
        (int(frame_center) - 50, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.4,
        (255, 0, 255),
        1,
    )

    # 편차 정보 표시
    if bias is not None:
        bias_text = f"Bias: {bias:.1f}px"
        bias_color = (0, 255, 255) if abs(bias) < 10 else (0, 165, 255)
        cv2.putText(
            frame_color,
            bias_text,
            (10, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            bias_color,
            2,
        )

    # 라인 위치 정보 표시
    if left_lane_pos is not None and right_lane_pos is not None:
        info_text = f"Left: {int(left_lane_pos)} | Right: {int(right_lane_pos)}"
        cv2.putText(
            frame_color,
            info_text,
            (10, h - 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )

    return frame_color


print("✅ 라인 검출 함수 정의 완료\n")

# ============================
# 6단계: 차량 제어 함수 정의
# ============================
print("=" * 50)
print("  🚗 6단계: 차량 제어 함수 정의")
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
    """좌회전 (왼쪽 속도 감소, 오른쪽 속도 증가)"""
    set_motor_speeds(speed_left, speed_left, speed_right, speed_right)


def car_right(speed_left, speed_right):
    """우회전 (왼쪽 속도 증가, 오른쪽 속도 감소)"""
    set_motor_speeds(speed_left, speed_left, speed_right, speed_right)


print("✅ 차량 제어 함수 정의 완료\n")

# ============================
# 7단계: 중앙 유지 제어 로직 정의
# ============================
print("=" * 50)
print("  🧭 7단계: 중앙 유지 제어 로직 정의")
print("=" * 50)


def calculate_bias(lane_center, frame_center):
    """
    C++ 코드 방식의 편차 계산

    Args:
        lane_center: 라인 중앙 X 위치
        frame_center: 프레임 중앙 X 위치

    Returns:
        bias: 편차 값 (C++ 코드 방식: laneCenter - frameCenter)
              양수: 라인 중앙이 프레임 중앙보다 오른쪽에 있음 -> 오른쪽으로 조정 필요
              음수: 라인 중앙이 프레임 중앙보다 왼쪽에 있음 -> 왼쪽으로 조정 필요
    """
    if lane_center is None:
        return None

    # C++ 코드 방식: Result = laneCenter - frameCenter
    # 양수: 라인 중앙이 프레임 중앙보다 오른쪽 -> 차량이 왼쪽으로 편향 -> 오른쪽으로 조정
    # 음수: 라인 중앙이 프레임 중앙보다 왼쪽 -> 차량이 오른쪽으로 편향 -> 왼쪽으로 조정
    bias = lane_center - frame_center

    return bias


def control_car_by_bias(bias, base_speed, p_gain, bias_threshold):
    """
    편차를 기반으로 차량 제어

    Args:
        bias: 편차 값 (픽셀)
        base_speed: 기본 속도
        p_gain: 비례 제어 게인
        bias_threshold: 편차 임계값 (이 값 이하면 직진)

    Returns:
        left_speed: 왼쪽 모터 속도
        right_speed: 오른쪽 모터 속도
        direction: 방향 문자열
    """
    if bias is None:
        # 라인 검출 실패 시 정지 또는 느린 직진
        if DEBUG_MODE:
            print("⚠️  라인 검출 실패 - 정지")
        car_stop()
        return 0, 0, "STOP"

    # 편차가 임계값 이하면 직진
    if abs(bias) <= bias_threshold:
        boosted_speed = min(base_speed + SPEED_BOOST, 255)
        car_run(boosted_speed, boosted_speed)
        if DEBUG_MODE:
            print(f"⚡ 직진 - 속도: {boosted_speed}, 편차: {bias:.1f}px")
        return boosted_speed, boosted_speed, "UP"

    # 비례 제어로 속도 차이 계산
    speed_diff = int(bias * p_gain)
    speed_diff = max(-base_speed, min(base_speed, speed_diff))  # 제한

    # C++ 코드 방식: Result = laneCenter - frameCenter
    # 양수: 라인 중앙이 프레임 중앙보다 오른쪽 -> 차량이 왼쪽으로 편향 -> 오른쪽으로 조정
    # 음수: 라인 중앙이 프레임 중앙보다 왼쪽 -> 차량이 오른쪽으로 편향 -> 왼쪽으로 조정
    if bias > 0:
        # 라인 중앙이 오른쪽에 있음 -> 오른쪽으로 조정 (오른쪽 속도 증가)
        left_speed = max(0, base_speed - abs(speed_diff))
        right_speed = min(255, base_speed + abs(speed_diff))
        car_right(left_speed, right_speed)
        if DEBUG_MODE:
            print(f"▶️  우회전 - L:{left_speed}, R:{right_speed}, 편차: {bias:.1f}px")
        return left_speed, right_speed, "RIGHT"

    # 편차가 음수: 라인 중앙이 왼쪽에 있음 -> 왼쪽으로 조정 (왼쪽 속도 증가)
    else:
        left_speed = min(255, base_speed + abs(speed_diff))
        right_speed = max(0, base_speed - abs(speed_diff))
        car_left(left_speed, right_speed)
        if DEBUG_MODE:
            print(f"◀️  좌회전 - L:{left_speed}, R:{right_speed}, 편차: {bias:.1f}px")
        return left_speed, right_speed, "LEFT"


print("✅ 중앙 유지 제어 로직 정의 완료\n")

# ============================
# 8단계: 메인 루프 실행
# ============================
print("=" * 50)
print("  🚀 8단계: 메인 루프 시작")
print("=" * 50)
print("Controls:")
print("  ESC   : 종료")
print("  SPACE : 일시정지")
print("  'l'   : LED 토글")
print("=" * 50)

frame_count = 0
start_time = time.time()
led_state = LED_ON_START

# 이전 라인 위치 저장 (라인 검출 실패 시 사용)
prev_left_lane = None
prev_right_lane = None

try:
    while True:
        frame_count += 1

        # 트랙바 값 읽기
        brightness = cv2.getTrackbarPos("Brightness", "Camera Settings")
        contrast = cv2.getTrackbarPos("Contrast", "Camera Settings")
        detect_value = cv2.getTrackbarPos("Detect Value", "Camera Settings")
        r_weight = cv2.getTrackbarPos("R_weight", "Camera Settings")
        g_weight = cv2.getTrackbarPos("G_weight", "Camera Settings")
        b_weight = cv2.getTrackbarPos("B_weight", "Camera Settings")
        servo_1_angle = cv2.getTrackbarPos("Servo 1 Angle", "Camera Settings")
        servo_2_angle = cv2.getTrackbarPos("Servo 2 Angle", "Camera Settings")
        roi_top_y = cv2.getTrackbarPos("ROI Top Y", "Camera Settings")
        roi_bottom_y = cv2.getTrackbarPos("ROI Bottom Y", "Camera Settings")
        roi_start_y = cv2.getTrackbarPos("ROI Start Y", "Camera Settings")
        roi_height = cv2.getTrackbarPos("ROI Height", "Camera Settings")
        base_speed = cv2.getTrackbarPos("Base Speed", "Camera Settings")
        p_gain = cv2.getTrackbarPos("P Gain", "Camera Settings") / 100.0
        bias_threshold = cv2.getTrackbarPos("Bias Threshold", "Camera Settings")

        # 카메라 속성 설정
        cap.set(cv2.CAP_PROP_BRIGHTNESS, brightness)
        cap.set(cv2.CAP_PROP_CONTRAST, contrast)

        # 프레임 읽기
        ret, frame = cap.read()
        if not ret:
            print("❌ 카메라에서 프레임을 읽을 수 없습니다.")
            break

        # 서보 모터 각도 조절
        bot.Ctrl_Servo(1, servo_1_angle)
        bot.Ctrl_Servo(2, servo_2_angle)

        # 프레임 처리
        binary_frame = process_frame(
            frame, detect_value, r_weight, g_weight, b_weight, roi_top_y, roi_bottom_y
        )

        # 라인 검출 (C++ 코드 방식)
        left_lane_pos, right_lane_pos, lane_center = detect_lane_lines(
            binary_frame,
            DEFAULT_MIN_LANE_WIDTH,
            DEFAULT_MAX_LANE_WIDTH,
            roi_start_y,
            roi_height,
        )

        # 라인 위치 저장 (다음 프레임에서 사용)
        if left_lane_pos is not None:
            prev_left_lane = left_lane_pos
        if right_lane_pos is not None:
            prev_right_lane = right_lane_pos

        # 프레임 중앙 계산
        # C++ 코드: frameCenter = 188 (400x240 기준)
        # 해상도에 따라 비례 계산
        w = binary_frame.shape[1]
        if w >= 600:  # 640x480 해상도
            frame_center = 320  # 640 / 2
        elif w >= 300:  # 320x240 해상도
            frame_center = 160  # 320 / 2
        else:
            frame_center = w // 2  # 일반적인 경우

        # 편차 계산
        bias = calculate_bias(lane_center, frame_center)

        # 차량 제어
        left_speed, right_speed, direction = control_car_by_bias(
            bias, base_speed, p_gain, bias_threshold
        )

        # 최종 프레임에 라인 그리기
        final_frame = draw_lane_lines(
            binary_frame, left_lane_pos, right_lane_pos, lane_center, frame_center, bias
        )

        # 방향 정보 추가
        if direction:
            cv2.putText(
                final_frame,
                f"Direction: {direction}",
                (10, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2,
            )

        # 속도 정보 추가
        cv2.putText(
            final_frame,
            f"Speed L:{left_speed} R:{right_speed}",
            (10, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )

        cv2.imshow("5_Final", final_frame)

        # FPS 계산
        if frame_count % 10 == 0:
            elapsed = time.time() - start_time
            fps = 10 / elapsed if elapsed > 0 else 0
            if DEBUG_MODE:
                print(f"📊 FPS: {fps:.1f}")
            start_time = time.time()

        # 키 입력 처리
        key = cv2.waitKey(30) & 0xFF
        if key == 27:  # ESC
            print("\n🛑 종료 중...")
            break
        elif key == 32:  # SPACE
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
# 9단계: 정리 및 종료
# ============================
finally:
    print("\n" + "=" * 50)
    print("  🧹 9단계: 정리 및 종료")
    print("=" * 50)

    car_stop()
    print("✅ 모터 정지")

    if USE_LED_EFFECTS:
        bot.Ctrl_WQ2812_ALL(0, 0)
        print("✅ LED 끄기")

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
