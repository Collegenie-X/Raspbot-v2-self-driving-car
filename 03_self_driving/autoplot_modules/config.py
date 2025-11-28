# -*- coding: utf-8 -*-
"""
설정 파일 (Configuration)
"""

# 기본 속도 설정
DEFAULT_SPEED_UP = 20  # 기본 전진 속도
DEFAULT_SPEED_DOWN = 10  # 회전 시 감속 속도
SPEED_BOOST = 15  # 직진 시 추가 속도

# 라인 검출 기본 설정
DEFAULT_DETECT_VALUE = 120  # 이진화 임계값
DEFAULT_BRIGHTNESS = 0  # 카메라 밝기
DEFAULT_CONTRAST = 0  # 카메라 대비

# RGB 가중치 (흰색 라인 검출 최적화)
DEFAULT_R_WEIGHT = 30
DEFAULT_G_WEIGHT = 40
DEFAULT_B_WEIGHT = 60

# 방향 판단 임계값
DEFAULT_DIRECTION_THRESHOLD = 35000
DEFAULT_UP_THRESHOLD = 220000

# 서보 모터 초기 각도
DEFAULT_SERVO_1 = 90  # 좌우 (Pan)
DEFAULT_SERVO_2 = 25  # 상하 (Tilt)

# 기능 활성화 여부
DEBUG_MODE = True
USE_LED_EFFECTS = True
USE_BEEP = True

# ROI 기본 좌표 (트랙바 초기값)
ROI_TOP_DEFAULT = 0
ROI_BOTTOM_DEFAULT = 130
