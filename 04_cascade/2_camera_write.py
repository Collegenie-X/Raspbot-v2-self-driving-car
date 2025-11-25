import cv2
import time
import os
import numpy as np
from datetime import datetime

# Init camera 
cap = cv2.VideoCapture(0)
cap.set(3, 320)  # set Width
cap.set(4, 240)  # set Height

# 트랙바 콜백 함수 (사용되지 않음)
def nothing(x):
    pass

# 윈도우 생성
cv2.namedWindow('Camera Settings')

# 트랙바 생성
cv2.createTrackbar('Brightness', 'Camera Settings', 70, 100, nothing)
cv2.createTrackbar('Contrast', 'Camera Settings', 70, 100, nothing)
cv2.createTrackbar('Saturation', 'Camera Settings', 70, 100, nothing)
cv2.createTrackbar('Gain', 'Camera Settings', 80, 100, nothing)
cv2.createTrackbar('R_weight', 'Camera Settings', 33, 100, nothing)
cv2.createTrackbar('G_weight', 'Camera Settings', 33, 100, nothing)
cv2.createTrackbar('B_weight', 'Camera Settings', 33, 100, nothing)

t_start = time.time()
fps = 0

def weighted_gray(image, r_weight, g_weight, b_weight):
    sum_weight = r_weight + g_weight + b_weight

    # 가중치를 0-1 범위로 변환
    r_weight /= sum_weight
    g_weight /= sum_weight
    b_weight /= sum_weight
    return cv2.addWeighted(cv2.addWeighted(image[:, :, 2], r_weight, image[:, :, 1], g_weight, 0), 1.0, image[:, :, 0], b_weight, 0)

def channel_frame (frame) : 
    lab_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2Lab)
    l_channel, a_channel, b_channel = cv2.split(lab_frame)
    return l_channel, a_channel, b_channel


while True:
    # 트랙바 값 읽기
    brightness = cv2.getTrackbarPos('Brightness', 'Camera Settings')
    contrast = cv2.getTrackbarPos('Contrast', 'Camera Settings')
    saturation = cv2.getTrackbarPos('Saturation', 'Camera Settings')
    gain = cv2.getTrackbarPos('Gain', 'Camera Settings')
    r_weight = cv2.getTrackbarPos('R_weight', 'Camera Settings')
    g_weight = cv2.getTrackbarPos('G_weight', 'Camera Settings')
    b_weight = cv2.getTrackbarPos('B_weight', 'Camera Settings')

    # 카메라 속성 설정
    cap.set(cv2.CAP_PROP_BRIGHTNESS, brightness)
    cap.set(cv2.CAP_PROP_CONTRAST, contrast)
    cap.set(cv2.CAP_PROP_SATURATION, saturation)
    cap.set(cv2.CAP_PROP_GAIN, gain)

    ret, frame = cap.read()

    # Calculate FPS
    fps += 1
    mfps = fps / (time.time() - t_start)

    
    cv2.imshow('1 Step frame', frame)

    gray_frame = weighted_gray(frame, r_weight, g_weight, b_weight)
    cv2.imshow('2 Step weighted_gray_frame', gray_frame)

        
    # l_channel, a_channel, b_channel = channel_frame(frame)
    # cv2.imshow('l_channel lab_frame', l_channel)
    # cv2.imshow('a_channel lab_frame', a_channel)
    # cv2.imshow('b_channel lab_frame', b_channel)

    # Check for key presses
    k = cv2.waitKey(30) & 0xff
    if k == 27:  # press 'ESC' to quit
        break

    if k == 32:  # press 'SPACE' to take a photo
        path = "./positive/rect_color_weight"
        if not os.path.exists(path):
            os.makedirs(path)
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        filename_gray = f"{path}/rect_gray_{timestamp}.jpg"
        filename_lab = f"{path}/rect_lab_{timestamp}.jpg"
        print(f"images: {filename_gray} and {filename_lab} saved")
        cv2.imwrite(filename_gray, gray_frame)
        # cv2.imwrite(filename_lab, l_channel)

    time.sleep(0.2)

cap.release()
cv2.destroyAllWindows()
