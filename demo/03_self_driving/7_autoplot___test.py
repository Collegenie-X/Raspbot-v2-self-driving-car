import cv2
import numpy as np
import random
import time
import sys
import os

# Raspbot 라이브러리 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib", "raspbot"))
from Raspbot_Lib import Raspbot

# Camera and bot initialization
print("=" * 50)
print("  Initializing Hardware")
print("=" * 50)

print("Initializing Raspbot...")
bot = Raspbot()  # Raspbot으로 변경
print("Raspbot initialized successfully")

# LED 초기화
bot.Ctrl_WQ2812_ALL(0, 0)
print("LED initialized (OFF)")

# 부저 초기화
bot.Ctrl_BEEP_Switch(0)
print("Beeper initialized (OFF)")

# 서보 초기 위치
bot.Ctrl_Servo(1, 0)
bot.Ctrl_Servo(2, 92)
print("Servo motors initialized")

print("\nInitializing camera...")
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)  # set Width
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)  # set Height
cap.set(cv2.CAP_PROP_SATURATION, 50)
cap.set(cv2.CAP_PROP_EXPOSURE, 100)
print("Camera initialized successfully")
print("=" * 50 + "\n")


# 트랙바 콜백 함수 (사용되지 않음)
def nothing(x):
    pass


brightness = 0
contrast = 0
saturation = 0
gain = 0
detect_value = 0
motor_up_speed = 0
motor_down_speed = 0
r_weight = 0
g_weight = 0
b_weight = 0
servo_1_angle = 0
servo_2_angle = 0
y_value = 0


direction_threshold = 0
up_threshold = 0

# 상태 변수 추가
led_state = False  # LED 상태
beep_state = False  # 부저 상태
motor_enabled = True  # 모터 활성화 상태
frame_count = 0  # 프레임 카운터

# 윈도우 생성 (값을 조절하는 부분)
cv2.namedWindow("Camera Settings")

# # 트랙바 생성
cv2.createTrackbar("Servo 1 Angle", "Camera Settings", 90, 180, nothing)
cv2.createTrackbar("Servo 2 Angle", "Camera Settings", 119, 180, nothing)

cv2.createTrackbar("Y Value", "Camera Settings", 10, 160, nothing)

cv2.createTrackbar("Direction Threshold", "Camera Settings", 30000, 500000, nothing)
cv2.createTrackbar("Up Threshold", "Camera Settings", 210000, 500000, nothing)

cv2.createTrackbar("Brightness", "Camera Settings", 71, 100, nothing)
cv2.createTrackbar("Contrast", "Camera Settings", 78, 100, nothing)

cv2.createTrackbar("Detect Value", "Camera Settings", 29, 150, nothing)

cv2.createTrackbar("Motor Up Speed", "Camera Settings", 90, 125, nothing)
cv2.createTrackbar("Motor Down Speed", "Camera Settings", 50, 125, nothing)

cv2.createTrackbar("R_weight", "Camera Settings", 46, 100, nothing)
cv2.createTrackbar("G_weight", "Camera Settings", 47, 100, nothing)
cv2.createTrackbar("B_weight", "Camera Settings", 49, 100, nothing)

cv2.createTrackbar("Saturation", "Camera Settings", 20, 100, nothing)
cv2.createTrackbar("Gain", "Camera Settings", 20, 100, nothing)


def weighted_gray(image, r_weight, g_weight, b_weight):
    # 가중치를 0-1 범위로 변환
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


def process_frame(frame, detect_value, r_weight, g_weight, b_weight, y_value):
    """
    Process the frame to detect edges and transform perspective.
    """
    # Define region for perspective transformation
    pts_src = np.float32(
        [
            [10, 70 + y_value],
            [310, 70 + y_value],
            [310, 10 + y_value],
            [10, 10 + y_value],
        ]
    )
    pts_dst = np.float32([[0, 240], [320, 240], [320, 0], [0, 0]])

    # 사각형 그리기
    pts = pts_src.reshape((-1, 1, 2)).astype(np.int32)  # np.float32에서 np.int32로 변경
    frame = cv2.polylines(frame, [pts], isClosed=True, color=(0, 0, 255), thickness=2)
    cv2.imshow("1_Frame", frame)

    # Apply perspective transformation
    mat_affine = cv2.getPerspectiveTransform(pts_src, pts_dst)
    frame_transformed = cv2.warpPerspective(frame, mat_affine, (320, 240))
    cv2.imshow("2_frame_transformed", frame_transformed)

    # Convert to grayscale using weighted gray
    gray_frame = weighted_gray(frame_transformed, r_weight, g_weight, b_weight)
    cv2.imshow("3_gray_frame", gray_frame)
    _, binary_frame = cv2.threshold(gray_frame, detect_value, 255, cv2.THRESH_BINARY)

    # 노이즈 제거
    kernel = np.ones((5, 5), np.uint8)
    binary_frame = cv2.morphologyEx(binary_frame, cv2.MORPH_CLOSE, kernel)
    binary_frame = cv2.morphologyEx(binary_frame, cv2.MORPH_OPEN, kernel)

    # Display the processed frame (for debugging)
    cv2.imshow("4_Processed Frame", binary_frame)
    return binary_frame


def decide_direction(histogram, direction_threshold, detect_value):
    """
    Decide the driving direction based on histogram.
    """
    # 히스토그램의 길이
    length = len(histogram)

    # 히스토그램을 세 구역으로 나눔
    DIVIDE_DIRECTION = 6

    left = int(np.sum(histogram[: length // DIVIDE_DIRECTION]))
    right = int(np.sum(histogram[DIVIDE_DIRECTION - 1 * length // DIVIDE_DIRECTION :]))
    center_left = int(
        np.sum(
            histogram[1 * length // DIVIDE_DIRECTION : 3 * length // DIVIDE_DIRECTION]
        )
    )
    center_right = int(
        np.sum(
            histogram[3 * length // DIVIDE_DIRECTION : 5 * length // DIVIDE_DIRECTION]
        )
    )

    print("left:", left)
    print("right:", right)
    print("right - left:", right - left)

    # 방향 결정
    if abs(right - left) > direction_threshold:
        return "LEFT" if right > left else "RIGHT"

    center = abs(center_left - center_right)

    ### 라인 바가 직진으로 LEFT/RIGHT가 구별되지 않는 경우
    if center < up_threshold:

        # 차량 정지 (Raspbot용)
        bot.Ctrl_Muto(0, 0)
        bot.Ctrl_Muto(1, 0)
        bot.Ctrl_Muto(2, 0)
        bot.Ctrl_Muto(3, 0)
        time.sleep(0.5)
        return rotate_servo_and_check_direction()

    return "UP"


def rotate_servo_and_check_direction():
    """
    Rotate the servo to check directions and return the best direction.
    (Raspbot용으로 수정)
    """

    # 180도 서보모터 동작 (Raspbot용)
    bot.Ctrl_Servo(1, 180)
    bot.Ctrl_Servo(2, 100)
    time.sleep(0.5)

    # 이미지 송출
    ret, frame = cap.read()
    if not ret:
        print("############### Failed to read frame from camera.############")
        return "STOP"

    # 이미지 rect
    processed_frame = process_frame(
        frame, detect_value, r_weight, g_weight, b_weight, y_value
    )

    histogram_180 = np.sum(processed_frame, axis=0)
    length = len(histogram_180)

    left = int(np.sum(histogram[: length // 3]))
    center = int(np.sum(histogram[length // 3 : 2 * length // 3]))
    right = int(np.sum(histogram[2 * length // 3 :]))

    bot.Ctrl_Servo(1, servo_1_angle)
    bot.Ctrl_Servo(2, servo_2_angle)
    print(histogram_180)
    print("length: ", len(histogram_180))
    print(
        "################## histogram_180:",
        center,
        "--- up:",
        up_threshold,
        "is LEFT:",
        center > up_threshold,
    )
    time.sleep(0.5)

    #### center 부분만 체크함 center 부분이 1의 분포도가 가장 적다는 것은 길이 막혀 있지 않다는 부분입니다.

    if left > center and right > center:
        print("########### LEFT #############")
        return "RIGHT"

    print("########### RIGHT #############")
    return "LEFT"


def control_car(direction, up_speed, down_speed):
    """
    Control the car based on the decided direction.
    """
    global motor_enabled

    # 모터가 비활성화 상태면 정지
    if not motor_enabled:
        stop_car()
        return

    print(f"Controlling car: {direction}")
    if direction == "UP":
        # 직진: 모든 모터를 같은 속도로
        bot.Ctrl_Muto(0, up_speed)
        bot.Ctrl_Muto(1, up_speed)
        bot.Ctrl_Muto(2, up_speed)
        bot.Ctrl_Muto(3, up_speed)
    elif direction == "LEFT":
        # 좌회전: 왼쪽 모터 역회전, 오른쪽 모터 정회전
        bot.Ctrl_Muto(0, -(down_speed - 10))
        bot.Ctrl_Muto(1, -(down_speed - 10))
        bot.Ctrl_Muto(2, up_speed + 10)
        bot.Ctrl_Muto(3, up_speed + 10)
    elif direction == "RIGHT":
        # 우회전: 왼쪽 모터 정회전, 오른쪽 모터 역회전
        bot.Ctrl_Muto(0, up_speed + 10)
        bot.Ctrl_Muto(1, up_speed + 10)
        bot.Ctrl_Muto(2, -(down_speed - 10))
        bot.Ctrl_Muto(3, -(down_speed - 10))
    elif direction == "RANDOM":
        random_direction = random.choice(["LEFT", "RIGHT"])
        control_car(random_direction, up_speed, down_speed)


def rotate_servo(servo_id, angle):
    """서보 모터 회전 (Raspbot용)"""
    bot.Ctrl_Servo(servo_id, angle)


def stop_car():
    """차량 정지"""
    bot.Ctrl_Muto(0, 0)
    bot.Ctrl_Muto(1, 0)
    bot.Ctrl_Muto(2, 0)
    bot.Ctrl_Muto(3, 0)


def handle_keyboard_input():
    """키보드 입력 처리"""
    global led_state, beep_state, motor_enabled

    key = cv2.waitKey(30) & 0xFF

    if key == 27:  # ESC: 종료
        return "EXIT"

    elif key == 32:  # SPACE: 모터 토글
        motor_enabled = not motor_enabled
        if motor_enabled:
            print("\n" + "=" * 50)
            print("Motor: ENABLED")
            print("=" * 50)
        else:
            print("\n" + "=" * 50)
            print("Motor: DISABLED (Camera and display continue)")
            print("=" * 50)
            stop_car()  # 즉시 모터 정지

    elif key == ord("b"):  # b: 부저 토글
        beep_state = not beep_state
        bot.Ctrl_BEEP_Switch(1 if beep_state else 0)
        print(f"Beep: {'ON' if beep_state else 'OFF'}")

    elif key == ord("l"):  # l: LED 토글
        led_state = not led_state
        if led_state:
            bot.Ctrl_WQ2812_ALL(1, 2)  # LED ON
        else:
            bot.Ctrl_WQ2812_ALL(0, 0)  # LED OFF
        print(f"LED: {'ON' if led_state else 'OFF'}")

    return "CONTINUE"


print("\n" + "=" * 50)
print("  Controls:")
print("=" * 50)
print("  ESC   : Exit")
print("  SPACE : Pause/Resume (Motor Stop)")
print("  'b'   : Toggle Beeper")
print("  'l'   : Toggle LED")
print("=" * 50 + "\n")

try:
    while True:
        frame_count += 1

        # 프레임 상태 표시
        if frame_count % 10 == 0:  # 10프레임마다 상태 표시
            print("\n" + "-" * 50)
            print(
                f"Frame: {frame_count} | Motor: {'ON' if motor_enabled else 'OFF'} | LED: {'ON' if led_state else 'OFF'} | Beep: {'ON' if beep_state else 'OFF'}"
            )
            print("-" * 50)

        # 트랙바 값 읽기
        brightness = cv2.getTrackbarPos("Brightness", "Camera Settings")
        contrast = cv2.getTrackbarPos("Contrast", "Camera Settings")
        saturation = cv2.getTrackbarPos("Saturation", "Camera Settings")
        gain = cv2.getTrackbarPos("Gain", "Camera Settings")
        detect_value = cv2.getTrackbarPos("Detect Value", "Camera Settings")
        motor_up_speed = cv2.getTrackbarPos("Motor Up Speed", "Camera Settings")
        motor_down_speed = cv2.getTrackbarPos("Motor Down Speed", "Camera Settings")
        r_weight = cv2.getTrackbarPos("R_weight", "Camera Settings")
        g_weight = cv2.getTrackbarPos("G_weight", "Camera Settings")
        b_weight = cv2.getTrackbarPos("B_weight", "Camera Settings")
        servo_1_angle = cv2.getTrackbarPos("Servo 1 Angle", "Camera Settings")
        servo_2_angle = cv2.getTrackbarPos("Servo 2 Angle", "Camera Settings")
        y_value = cv2.getTrackbarPos("Y Value", "Camera Settings")
        direction_threshold = cv2.getTrackbarPos(
            "Direction Threshold", "Camera Settings"
        )
        up_threshold = cv2.getTrackbarPos("Up Threshold", "Camera Settings")

        # 카메라 속성 설정
        cap.set(cv2.CAP_PROP_BRIGHTNESS, brightness)
        cap.set(cv2.CAP_PROP_CONTRAST, contrast)
        cap.set(cv2.CAP_PROP_SATURATION, saturation)
        cap.set(cv2.CAP_PROP_GAIN, gain)

        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame from camera.")
            break

        # 서보 모터 각도 조절 (Raspbot용)
        rotate_servo(1, servo_1_angle)
        rotate_servo(2, servo_2_angle)

        processed_frame = process_frame(
            frame, detect_value, r_weight, g_weight, b_weight, y_value
        )
        histogram = np.sum(processed_frame, axis=0)

        print(f"Histogram: {histogram}")
        direction = decide_direction(histogram, direction_threshold, detect_value)
        print(f"#### Decided direction ####: {direction}")
        control_car(direction, motor_up_speed, motor_down_speed)

        # 키보드 입력 처리
        result = handle_keyboard_input()
        if result == "EXIT":
            break

        time.sleep(0.1)

except Exception as e:
    print(f"\nError occurred: {e}")
    import traceback

    traceback.print_exc()

finally:
    print("\n" + "=" * 50)
    print("  Cleaning up and Exiting")
    print("=" * 50)

    # 모터 정지 (Raspbot용)
    bot.Ctrl_Muto(0, 0)
    bot.Ctrl_Muto(1, 0)
    bot.Ctrl_Muto(2, 0)
    bot.Ctrl_Muto(3, 0)
    print("Motors stopped")

    # LED 끄기
    bot.Ctrl_WQ2812_ALL(0, 0)
    print("LED turned off")

    # 부저 끄기
    bot.Ctrl_BEEP_Switch(0)
    print("Beeper turned off")

    # 서보 초기 위치
    bot.Ctrl_Servo(1, 90)
    bot.Ctrl_Servo(2, 25)
    print("Servo motors returned to initial position")

    # 카메라 해제
    cap.release()
    cv2.destroyAllWindows()
    print("Camera released")

    # Raspbot 객체 삭제
    del bot
    print("Raspbot object deleted")

    print("\nCleanup completed successfully!")
    print("=" * 50)
