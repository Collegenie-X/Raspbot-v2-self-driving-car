"""
@Copyright (C): 2015-2024, Shenzhen Yahboom Tech
@Author: clhchan
@Date: 2024-07-25
@Modified: 2025-11-28 (한글 주석 적용)
"""

import cv2
import ipywidgets.widgets as widgets
import threading
import time
import enum

# 주피터 노트북용 이미지 위젯 생성
image_widget = widgets.Image(format="jpeg", width=640, height=480)


def bgr8_to_jpeg(value, quality=75):
    """OpenCV 이미지(BGR)를 JPEG 포맷으로 변환"""
    return bytes(cv2.imencode(".jpg", value)[1])


# 카메라 초기화 (디바이스 번호 0번: /dev/video0)
image = cv2.VideoCapture(0)

# 해상도 설정
width = 640
height = 480
image.set(cv2.CAP_PROP_FRAME_WIDTH, width)  # 이미지 너비 설정
image.set(cv2.CAP_PROP_FRAME_HEIGHT, height)  # 이미지 높이 설정

# 추가 설정 (주석 처리됨 - 필요시 활성화)
# image.set(3, 600)       # 너비 설정 (숫자 코드 사용)
# image.set(4, 500)       # 높이 설정
# image.set(5, 30)        # 프레임 레이트(FPS) 설정
# image.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G')) # 코덱 설정
# image.set(cv2.CAP_PROP_BRIGHTNESS, 40) # 밝기 설정 (-64 ~ 64, 기본값 0.0)
# image.set(cv2.CAP_PROP_CONTRAST, 50)   # 대비 설정 (-64 ~ 64, 기본값 2.0)
# image.set(cv2.CAP_PROP_EXPOSURE, 156)  # 노출 설정 (1.0 ~ 5000, 기본값 156.0)

# 첫 번째 프레임 읽기 및 테스트
ret, frame = image.read()  # 카메라 데이터 읽기
if ret:
    image_widget.value = bgr8_to_jpeg(frame)

try:
    # 주피터 노트북 환경에서만 동작하는 함수입니다.
    # 일반 파이썬 스크립트 실행 시에는 NameError(display not defined)가 발생할 수 있습니다.
    if "display" in globals():
        display(image_widget)  # 카메라 컴포넌트 화면에 표시
    else:
        print("⚠️ Note: This code is designed for Jupyter Notebook environment.")
        print("For terminal execution, use cv2.imshow() instead.")

    while True:
        ret, frame = image.read()
        if ret:
            image_widget.value = bgr8_to_jpeg(frame)
        time.sleep(0.010)

except KeyboardInterrupt:
    print(" Program terminated! ")
    pass

finally:
    image.release()  # 카메라 자원 해제
