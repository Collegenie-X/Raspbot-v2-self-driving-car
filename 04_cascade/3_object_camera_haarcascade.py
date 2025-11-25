import cv2
import numpy as np
import time
import os

import YB_Pcb_Car


folder_name = "rect"

cap = cv2.VideoCapture(0)
cap.set(3, 320)  # Set Width
cap.set(4, 240)  # Set Height

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

cv2.createTrackbar('R_weight', 'Camera Settings', 33, 100, nothing)
cv2.createTrackbar('G_weight', 'Camera Settings', 33, 100, nothing)
cv2.createTrackbar('B_weight', 'Camera Settings', 33, 100, nothing)

def initialize_camera(brightness,contrast,saturation,gain):

    cap.set(cv2.CAP_PROP_BRIGHTNESS, brightness)
    cap.set(cv2.CAP_PROP_CONTRAST, contrast)
    cap.set(cv2.CAP_PROP_SATURATION, saturation)
    cap.set(cv2.CAP_PROP_GAIN, gain)
    return cap

def load_cascade(file_name):
    cascade = cv2.CascadeClassifier()
    if not cascade.load(cv2.samples.findFile(file_name)):
        print('--(!)Error loading cascade:', file_name)
        exit(0)
    return cascade

def capture_frame(cap):
    ret, frame = cap.read()
    if not ret:
        print('--(!)Error capturing frame')
        return None
    return frame

def weighted_gray(image, r_weight, g_weight, b_weight):
    sum_weight = r_weight + g_weight + b_weight

    # 가중치를 0-1 범위로 변환
    r_weight /= sum_weight
    g_weight /= sum_weight
    b_weight /= sum_weight
    return cv2.addWeighted(cv2.addWeighted(image[:, :, 2], r_weight, image[:, :, 1], g_weight, 0), 1.0, image[:, :, 0], b_weight, 0)


def detect_object_sign(cascade, frame,r_weight,g_weight,b_weight):
    gray = weighted_gray(image=frame, r_weight=r_weight, g_weight=g_weight, b_weight=b_weight)
    cv2.imshow("1_Gray Image", gray)
    object_sign = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    return object_sign


def draw_rectangles_and_text(frame, traffic_sign):
    for (x, y, w, h) in traffic_sign:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
        cv2.putText(frame, f"{folder_name}_({w}X{h})", (x - 30, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    return frame


def save_image(frame, count):
    os.makedirs("./save_images", exist_ok=True)
    file_name = f"./save_images/{folder_name}_{count}.jpg"
    cv2.imwrite(file_name, frame)
    print(f"Image saved: {file_name}")


def rotate_servo(car, servo_id, angle):
    car.Ctrl_Servo(servo_id, angle)   

def main():
 
    object_cascade = load_cascade('cascade.xml')
    count = 0
    

    while True:
        
        # 트랙바 값 읽기
        servo_1_angle = cv2.getTrackbarPos('Servo 1 Angle', 'Camera Settings')
        servo_2_angle = cv2.getTrackbarPos('Servo 2 Angle', 'Camera Settings')    
        
        # 트랙바 값 읽기
        brightness = cv2.getTrackbarPos('Brightness', 'Camera Settings')
        contrast = cv2.getTrackbarPos('Contrast', 'Camera Settings')
        saturation = cv2.getTrackbarPos('Saturation', 'Camera Settings')
        gain = cv2.getTrackbarPos('Gain', 'Camera Settings')
        
        
        r_weight = cv2.getTrackbarPos('R_weight', 'Camera Settings')
        g_weight = cv2.getTrackbarPos('G_weight', 'Camera Settings')
        b_weight = cv2.getTrackbarPos('B_weight', 'Camera Settings')

        cap = initialize_camera(brightness,contrast,saturation,gain)
        
            # 서보 모터 각도 조절
        rotate_servo(car, 1, servo_1_angle)
        rotate_servo(car, 2, servo_2_angle)
        
        frame = capture_frame(cap)
        if frame is None:
            continue
        
        object_sign = detect_object_sign(object_cascade, frame,r_weight,g_weight,b_weight)

        if len(object_sign) > 0:
            frame = draw_rectangles_and_text(frame, object_sign)
            cv2.imshow("2_Image Frame(rectagles,text)", frame)

        k = cv2.waitKey(30) & 0xff
        if k == 27:  # press 'ESC' to quit
            break
        if k == 32:  # press 'SPACE' to save image
            save_image(frame, count)
            count += 1

        time.sleep(0.1)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
