#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
색상 추적 및 PTZ(Pan-Tilt-Zoom) 제어 시스템
Color Tracking with PTZ Control System

@Copyright (C): 2015-2024, Shenzhen Yahboom Tech
@Date: 2024/07/29 
@Author: clhchan 
@Contact: https://www.yahboom.com/about
"""

import os
import sys
import time
import math
import threading
import inspect
import ctypes

import numpy as np
import cv2
import traitlets
import ipywidgets.widgets as widgets
from IPython.display import display

# Raspbot 드라이버 라이브러리 임포트
from Raspbot_Lib import Raspbot

# OLED 디스플레이 라이브러리 임포트
sys.path.append('/home/pi/software/oled_yahboom/')
from yahboom_oled import *

# PID 제어 라이브러리 임포트
import PID


# ============================================================================
# 전역 변수 초기화
# Global Variables Initialization
# ============================================================================

# Raspbot 객체 생성
bot = Raspbot()

# OLED 객체 생성
oled = Yahboom_OLED(debug=False)

# 모드 및 색상 추적 변수
g_mode = 0
color_x = color_y = color_radius = 0

# 서보 모터 제어 변수
# 클라우드 팬은 9G 금속 디지털 서보 SG90M 사용
# 제어 펄스 폭 범위: 500~2500us
# 제어 각도 범위: 0~180°, 1500이 중앙 상태
target_valuex = 1500
target_valuey = 1500
target_servox = 90
target_servoy = 25

# 카메라 설정 변수
image_width = 640
image_height = 480

# HSV 색상 범위 설정 (초기값: 빨간색)
color_lower = np.array([0, 70, 72])
color_upper = np.array([7, 255, 255])


# ============================================================================
# 유틸리티 함수
# Utility Functions
# ============================================================================

def bgr8_to_jpeg(value, quality=75):
    """
    BGR8 이미지를 JPEG 포맷으로 변환
    Convert BGR8 image to JPEG format
    """
    return bytes(cv2.imencode('.jpg', value)[1])


def _async_raise(tid, exctype):
    """
    스레드에 예외를 발생시켜 종료
    Raises exception to terminate thread
    """
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # 1보다 큰 숫자를 반환하면 문제가 있으므로 exc=NULL로 다시 호출하여 효과를 되돌림
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)


def stop_thread(thread):
    """
    스레드 종료 함수
    Thread shutdown function
    """
    _async_raise(thread.ident, SystemExit)


def servo_reset():
    """
    서보 모터 초기 위치로 리셋
    Reset servo motors to initial position
    """
    bot.Ctrl_Servo(1, 90)
    bot.Ctrl_Servo(2, 25)


# ============================================================================
# 카메라 초기화
# Camera Initialization
# ============================================================================

def init_camera():
    """
    USB 카메라 초기화
    Initialize USB Camera
    """
    global image, image_width, image_height
    
    image = cv2.VideoCapture(0)
    image.set(3, image_width)
    image.set(4, image_height)
    image_width = image.get(cv2.CAP_PROP_FRAME_WIDTH)
    image_height = image.get(cv2.CAP_PROP_FRAME_HEIGHT)
    image.set(5, 30)  # 프레임 속도 설정
    
    # 옵션 설정 (필요시 주석 해제)
    # image.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))
    # image.set(cv2.CAP_PROP_BRIGHTNESS, 62)  # 밝기 설정 -64 ~ 64
    # image.set(cv2.CAP_PROP_CONTRAST, 63)    # 대비 설정 -64 ~ 64
    # image.set(cv2.CAP_PROP_EXPOSURE, 4800)  # 노출 설정 1.0 ~ 5000
    
    ret, frame = image.read()
    return ret, frame


# CSI 카메라 사용시 (주석 해제 필요)
# from picamera2 import Picamera2, Preview
# import libcamera
# def init_csi_camera():
#     picam2 = Picamera2()  
#     camera_config = picam2.create_preview_configuration(main={"format":'RGB888',"size":(320,240)})
#     camera_config["transform"] = libcamera.Transform(hflip=0, vflip=1)
#     picam2.configure(camera_config) 
#     picam2.start() 
#     return picam2


# ============================================================================
# 위젯 UI 설정
# Widget UI Setup
# ============================================================================

# 이미지 위젯 생성
image_widget = widgets.Image(format='jpeg', width=640, height=480)

# 색상 선택 버튼 생성
Redbutton = widgets.Button(
    value=False,
    description='red',
    disabled=False,
    button_style='danger',
    tooltip='Description',
    icon='uncheck'
)

Greenbutton = widgets.Button(
    value=False,
    description='green',
    disabled=False,
    button_style='success',
    tooltip='Description',
    icon='uncheck'
)

Bluebutton = widgets.Button(
    value=False,
    description='blue',
    disabled=False,
    button_style='info',
    tooltip='Description',
    icon='uncheck'
)

Yellowbutton = widgets.Button(
    value=False,
    description='yellow',
    disabled=False,
    button_style='warning',
    tooltip='Description',
    icon='uncheck'
)

Orangebutton = widgets.Button(
    value=False,
    description='orange',
    disabled=False,
    button_style='',
    tooltip='Description',
    icon='uncheck'
)

Closebutton = widgets.Button(
    value=False,
    description='close',
    disabled=False,
    button_style='',
    tooltip='Description',
    icon='uncheck'
)

output = widgets.Output()


# ============================================================================
# 버튼 콜백 함수
# Button Callback Functions
# ============================================================================

def ALL_Uncheck():
    """모든 버튼 체크 해제"""
    Redbutton.icon = 'uncheck'
    Greenbutton.icon = 'uncheck'
    Bluebutton.icon = 'uncheck'
    Yellowbutton.icon = 'uncheck'
    Orangebutton.icon = 'uncheck'


def on_Redbutton_clicked(b):
    """빨간색 선택"""
    global color_lower, color_upper, g_mode
    global target_valuex, target_valuey
    
    ALL_Uncheck()
    b.icon = 'check'
    color_lower = np.array([0, 43, 89])
    color_upper = np.array([7, 255, 255])
    g_mode = 1
    
    with output:
        bot.Ctrl_WQ2812_ALL(1, 0)  # 빨간색 LED
        oled.clear()
        oled.add_line("Color_Tracking", 1)
        oled.add_line("color: red", 3)
        oled.refresh()
        print("RedButton clicked.")


def on_Greenbutton_clicked(b):
    """초록색 선택"""
    global color_lower, color_upper, g_mode
    global target_valuex, target_valuey
    
    ALL_Uncheck()
    b.icon = 'check'
    color_lower = np.array([54, 104, 64])
    color_upper = np.array([78, 255, 255])
    g_mode = 1
    
    with output:
        bot.Ctrl_WQ2812_ALL(1, 1)  # 초록색 LED
        oled.clear()
        oled.add_line("Color_Tracking", 1)
        oled.add_line("color: green", 3)
        oled.refresh()
        print("GreenButton clicked.")


def on_Bluebutton_clicked(b):
    """파란색 선택"""
    global color_lower, color_upper, g_mode
    global target_valuex, target_valuey
    
    ALL_Uncheck()
    b.icon = 'check'
    color_lower = np.array([92, 100, 62])
    color_upper = np.array([121, 255, 255])
    g_mode = 1
    
    with output:
        bot.Ctrl_WQ2812_ALL(1, 2)  # 파란색 LED
        oled.clear()
        oled.add_line("Color_Tracking", 1)
        oled.add_line("color: blue", 3)
        oled.refresh()
        print("Bluebutton clicked.")


def on_Yellowbutton_clicked(b):
    """노란색 선택"""
    global color_lower, color_upper, g_mode
    global target_valuex, target_valuey
    
    ALL_Uncheck()
    b.icon = 'check'
    color_lower = np.array([26, 100, 91])
    color_upper = np.array([32, 255, 255])
    g_mode = 1
    
    with output:
        bot.Ctrl_WQ2812_ALL(1, 3)  # 노란색 LED
        oled.clear()
        oled.add_line("Color_Tracking", 1)
        oled.add_line("color: yellow", 3)
        oled.refresh()
        print("Yellowbutton clicked.")


def on_Orangebutton_clicked(b):
    """주황색 선택"""
    global color_lower, color_upper, g_mode
    global target_valuex, target_valuey
    
    ALL_Uncheck()
    b.icon = 'check'
    color_lower = np.array([11, 43, 46])
    color_upper = np.array([25, 255, 255])
    g_mode = 1
    
    with output:
        bot.Ctrl_WQ2812_brightness_ALL(255, 48, 0)  # 주황색 LED
        oled.clear()
        oled.add_line("Color_Tracking", 1)
        oled.add_line("color: orange", 3)
        oled.refresh()
        print("Orangebutton clicked.")


def on_Closebutton_clicked(b):
    """추적 종료"""
    global g_mode
    
    ALL_Uncheck()
    g_mode = 0
    RUNNING = False
    
    with output:
        bot.Ctrl_WQ2812_ALL(0, 0)  # LED 끄기
        oled.clear()
        oled.add_line("Color_Tracking", 1)
        oled.add_line("color: none", 3)
        oled.refresh()
        bot.Ctrl_Servo(1, 90)
        bot.Ctrl_Servo(2, 25)
        print("CloseButton clicked.")


# 버튼 이벤트 핸들러 등록
Redbutton.on_click(on_Redbutton_clicked)
Greenbutton.on_click(on_Greenbutton_clicked)
Bluebutton.on_click(on_Bluebutton_clicked)
Yellowbutton.on_click(on_Yellowbutton_clicked)
Orangebutton.on_click(on_Orangebutton_clicked)
Closebutton.on_click(on_Closebutton_clicked)


# ============================================================================
# PID 제어 초기화
# PID Control Initialization
# ============================================================================

# 위치식 PID를 사용하여 서보 모터 제어
# 초기화 파라미터는 서보 모터의 속도와 안정성에 영향
xservo_pid = PID.PositionalPID(0.8, 0.2, 0.02)  # P, I, D 파라미터
yservo_pid = PID.PositionalPID(0.8, 0.2, 0.01)


# ============================================================================
# 색상 인식 메인 함수 (버전 1 - 데드존 없음)
# Color Recognition Main Function (Version 1 - No Dead Zone)
# ============================================================================

def Color_Recongnize():
    """
    무데드존 제어: 실시간성이 높지만 서보가 계속 작동하여 떨림이 빈번함
    No dead zone control: High real-time performance, 
    but servo always works causing frequent jitter
    """
    oled.init_oled_process()  # OLED 프로세스 초기화
    
    global color_lower, color_upper, g_mode
    global target_valuex, target_valuey, color_x, color_y, target_servox
    
    t_start = time.time()
    fps = 0
    
    ret, frame = image.read()  # USB 카메라
    # frame = picam2.capture_array()  # CSI 카메라
    frame = cv2.GaussianBlur(frame, (5, 5), 0)
    
    first_read = 1
    while_cnt = 0
    target_servox_x = 0
    
    time.sleep(1)
    
    while True:
        ret, frame = image.read()
        # frame = picam2.capture_array()  # CSI 카메라
        
        # HSV 색공간으로 변환
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 색상 범위에 따른 마스크 생성
        mask = cv2.inRange(hsv, color_lower, color_upper)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        
        # 윤곽선 찾기
        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
        
        if g_mode == 1:  # 추적 모드 활성화
            if len(cnts) > 0:
                # 가장 큰 윤곽선 찾기
                cnt = max(cnts, key=cv2.contourArea)
                (color_x, color_y), color_radius = cv2.minEnclosingCircle(cnt)
                
                if color_radius > 10:
                    # 감지된 색상을 원으로 표시
                    cv2.circle(frame, (int(color_x), int(color_y)), 
                             int(color_radius), (255, 0, 255), 2)
                    
                    # X축 제어
                    if math.fabs(image_width - color_x) > 20:
                        xservo_pid.SystemOutput = color_x
                        xservo_pid.SetStepSignal(image_width / 2)
                        xservo_pid.SetInertiaTime(0.01, 0.05)
                        
                        target_valuex = int(1500 + xservo_pid.SystemOutput)
                        target_servox = int((target_valuex - 500) / 10)
                        
                        if target_servox > 180:
                            target_servox = 180
                        if target_servox < 0:
                            target_servox = 0
                        bot.Ctrl_Servo(1, target_servox)
                    
                    # Y축 제어
                    if math.fabs(image_height - color_y) > 75:
                        yservo_pid.SystemOutput = color_y
                        yservo_pid.SetStepSignal(image_height / 2)
                        yservo_pid.SetInertiaTime(0.01, 0.1)
                        
                        target_valuey = int(800 + yservo_pid.SystemOutput)
                        target_servoy = int((target_valuey - 500) / 10)
                        
                        if target_servoy > 110:
                            target_servoy = 110
                        if target_servoy < 0:
                            target_servoy = 0
                        bot.Ctrl_Servo(2, target_servoy)
        
        # FPS 계산 및 표시
        fps = fps + 1
        mfps = fps / (time.time() - t_start)
        
        # 실시간 이미지 전송
        image_widget.value = bgr8_to_jpeg(frame)


# ============================================================================
# 색상 인식 메인 함수 (버전 2 - 데드존 있음)
# Color Recognition Main Function (Version 2 - With Dead Zone)
# ============================================================================

def Color_Recongnize2():
    """
    데드존 제어: 추적 실시간성은 떨어지지만 데드존 범위 내에서 
    서보가 움직이지 않아 떨림이 안정적
    With dead zone control: Lower real-time performance, 
    but servo doesn't move within dead zone making it more stable
    """
    oled.init_oled_process()  # OLED 프로세스 초기화
    oled.clear(refresh=True)
    
    global color_lower, color_upper, g_mode
    global target_valuex, target_valuey, color_x, target_servox
    
    t_start = time.time()
    fps = 0
    
    ret, frame = image.read()
    # frame = picam2.capture_array()  # CSI 카메라
    frame = cv2.GaussianBlur(frame, (5, 5), 0)
    
    first_read = 1
    while_cnt = 0
    
    time.sleep(1)
    
    while True:
        ret, frame = image.read()
        # frame = picam2.capture_array()  # CSI 카메라
        
        # HSV 색공간으로 변환
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 색상 범위에 따른 마스크 생성
        mask = cv2.inRange(hsv, color_lower, color_upper)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        
        # 윤곽선 찾기
        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
        
        if g_mode == 1:  # 추적 모드 활성화
            if len(cnts) > 0:
                # 가장 큰 윤곽선 찾기
                cnt = max(cnts, key=cv2.contourArea)
                (color_x, color_y), color_radius = cv2.minEnclosingCircle(cnt)
                
                if color_radius > 10:
                    # 감지된 색상을 원으로 표시
                    cv2.circle(frame, (int(color_x), int(color_y)), 
                             int(color_radius), (255, 0, 255), 2)
                    
                    # X축 제어
                    if math.fabs(image_width - color_x) > 20:
                        xservo_pid.SystemOutput = color_x
                        xservo_pid.SetStepSignal(image_width / 2)
                        xservo_pid.SetInertiaTime(0.01, 0.05)
                        
                        target_valuex = int(1500 + xservo_pid.SystemOutput)
                        target_servox = int((target_valuex - 500) / 10)
                        
                        if target_servox > 180:
                            target_servox = 180
                        if target_servox < 0:
                            target_servox = 0
                        bot.Ctrl_Servo(1, target_servox)
                    
                    # Y축 제어
                    if math.fabs(image_height - color_y) > 75:
                        yservo_pid.SystemOutput = color_y
                        yservo_pid.SetStepSignal(image_height / 2)
                        yservo_pid.SetInertiaTime(0.01, 0.1)
                        
                        target_valuey = int(800 + yservo_pid.SystemOutput)
                        target_servoy = int((target_valuey - 500) / 10)
                        
                        if target_servoy > 110:
                            target_servoy = 110
                        if target_servoy < 0:
                            target_servoy = 0
                        bot.Ctrl_Servo(2, target_servoy)
        
        # FPS 계산 및 표시
        fps = fps + 1
        mfps = fps / (time.time() - t_start)
        cv2.putText(frame, "FPS " + str(int(mfps)), (40, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 3)
        
        # 실시간 이미지 전송
        image_widget.value = bgr8_to_jpeg(frame)


# ============================================================================
# 리소스 정리 함수
# Resource Cleanup Functions
# ============================================================================

def cleanup():
    """리소스 정리 및 해제"""
    image.release()
    # CSI 카메라 사용 시
    # picam2.stop_preview()
    # picam2.close()
    
    servo_reset()
    
    # 화면 기본 데이터 표시 복원
    os.system("python3 /home/pi/software/oled_yahboom/yahboom_oled.py &")


# ============================================================================
# 메인 실행 코드
# Main Execution Code
# ============================================================================

def main():
    """메인 실행 함수"""
    # 카메라 초기화
    ret, frame = init_camera()
    image_widget.value = bgr8_to_jpeg(frame)
    
    # 서보 모터 초기화
    servo_reset()
    
    # UI 위젯 표시
    display(image_widget)
    display(Redbutton, Greenbutton, Bluebutton, Yellowbutton, Orangebutton, Closebutton, output)
    
    # 색상 인식 스레드 시작 (버전 2 사용)
    thread1 = threading.Thread(target=Color_Recongnize2)
    thread1.daemon = True
    thread1.start()
    
    return thread1


if __name__ == "__main__":
    """
    프로그램 실행
    스레드를 시작하려면 main() 함수를 호출하세요
    종료하려면 stop_thread(thread1) 및 cleanup()을 호출하세요
    """
    # thread1 = main()
    # 
    # # 프로그램 종료 시:
    # # stop_thread(thread1)
    # # cleanup()
    pass

