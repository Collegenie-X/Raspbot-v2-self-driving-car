import cv2
import time
import os
import YB_Pcb_Car
import numpy as np
from datetime import datetime

# Init camera 
cap = cv2.VideoCapture(0)
cap.set(3, 320)  # set Width
cap.set(4, 240)  # set Height

car = YB_Pcb_Car.YB_Pcb_Car()

# 트랙바 콜백 함수 (사용되지 않음)
def nothing(x):
    pass

# 윈도우 생성
cv2.namedWindow('Camera Settings')

# # 트랙바 생성
cv2.createTrackbar('Servo 1 Angle', 'Camera Settings',90, 180, nothing)
cv2.createTrackbar('Servo 2 Angle', 'Camera Settings', 113, 180, nothing)

# 트랙바 생성
cv2.createTrackbar('Brightness', 'Camera Settings', 70, 100, nothing)
cv2.createTrackbar('Contrast', 'Camera Settings', 70, 100, nothing)
cv2.createTrackbar('Saturation', 'Camera Settings', 70, 100, nothing)
cv2.createTrackbar('Gain', 'Camera Settings', 80, 100, nothing)

t_start = time.time()
fps = 0

def rotate_servo(car, servo_id, angle):
    car.Ctrl_Servo(servo_id, angle)

while True:
    # 트랙바 값 읽기
    servo_1_angle = cv2.getTrackbarPos('Servo 1 Angle', 'Camera Settings')
    servo_2_angle = cv2.getTrackbarPos('Servo 2 Angle', 'Camera Settings')
    
    brightness = cv2.getTrackbarPos('Brightness', 'Camera Settings')
    contrast = cv2.getTrackbarPos('Contrast', 'Camera Settings')
    saturation = cv2.getTrackbarPos('Saturation', 'Camera Settings')
    gain = cv2.getTrackbarPos('Gain', 'Camera Settings')

    # 카메라 속성 설정
    cap.set(cv2.CAP_PROP_BRIGHTNESS, brightness)
    cap.set(cv2.CAP_PROP_CONTRAST, contrast)
    cap.set(cv2.CAP_PROP_SATURATION, saturation)
    cap.set(cv2.CAP_PROP_GAIN, gain)

     # 서보 모터 각도 조절
    rotate_servo(car, 1, servo_1_angle)
    rotate_servo(car, 2, servo_2_angle)

    ret, frame = cap.read()
    

    # Calculate FPS
    fps += 1
    mfps = fps / (time.time() - t_start)

    # Show the frame
    cv2.imshow('1___frame', frame)
    
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    
    cv2.imshow('2___gray', gray)

 
    # Check for key presses
    
    k = cv2.waitKey(30) & 0xff
    if k == 27:  # press 'ESC' to quit
        break
    
    folder_name = "rect"

    if k == 32:  # press 'SPACE' to take a photo
        path = f"./positive/{folder_name}"
        if not os.path.exists(path):
            os.makedirs(path)
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        filename = f"{path}/{folder_name}_{timestamp}.jpg"
        print(f"image:{filename} saved")
        cv2.imwrite(filename, gray)

    time.sleep(0.2)

cap.release()
cv2.destroyAllWindows()
