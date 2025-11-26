# Raspbot 소스 코드 가이드

## 📂 프로젝트 구조 요약

이 프로젝트는 Raspberry Pi 기반 자율주행 로봇 카의 소스 코드입니다.

---

## 🔧 주요 수정 가능한 소스 코드

### 1. **로봇 하드웨어 제어 라이브러리**

#### `lib/raspbot/Raspbot_Lib.py` (최신 버전)
- **기능**: 로봇의 모든 하드웨어 제어
- **주요 클래스**:
  - `Raspbot()`: 메인 로봇 제어 클래스
  - `LightShow()`: LED 특수 효과 제어

**주요 메서드**:
```python
# 모터 제어
car.Ctrl_Car(motor_id, motor_dir, motor_speed)
car.Ctrl_Muto(motor_id, motor_speed)  # -255 ~ 255

# 서보 모터
car.Ctrl_Servo(id, angle)  # 0~180도

# LED 제어
car.Ctrl_WQ2812_ALL(state, color)  # 모든 LED
car.Ctrl_WQ2812_Alone(number, state, color)  # 개별 LED
car.Ctrl_WQ2812_brightness_ALL(R, G, B)  # 밝기

# 센서
car.Ctrl_Ulatist_Switch(state)  # 초음파 센서
car.Ctrl_BEEP_Switch(state)  # 부저
car.Ctrl_IR_Switch(state)  # 적외선 리모컨

# 센서 읽기
track = car.read_data_array(0x0a, 1)  # 라인 트래킹
distance = car.read_data_array(0x1b, 1)  # 초음파 거리
```

#### `04_cascade/YB_Pcb_Car.py` (구 버전)
- **기능**: 기본 차량 제어 (I2C 통신)
- **사용처**: 자율주행 테스트 코드들

**주요 메서드**:
```python
car.Car_Run(speed1, speed2)      # 전진
car.Car_Back(speed1, speed2)     # 후진
car.Car_Left(speed1, speed2)     # 좌회전
car.Car_Right(speed1, speed2)    # 우회전
car.Car_Stop()                   # 정지
car.Ctrl_Servo(id, angle)        # 서보 모터
```

---

### 2. **자율주행 애플리케이션 (수정 권장)**

#### 📍 `03_self_driving/` 폴더

가장 **수정하기 쉽고** 실용적인 자율주행 코드들입니다!

##### **2_autoplot___test.py** (기본 자율주행)
- **기능**: 라인 트래킹 기반 자율주행
- **주요 파라미터**:
  - 카메라 설정: `brightness`, `contrast`, `saturation`
  - 라인 검출: `detect_value`, `R_weight`, `G_weight`, `B_weight`
  - 모터 속도: `motor_up_speed`, `motor_down_speed`
  - 서보 각도: `servo_1_angle`, `servo_2_angle`
  - 방향 판단: `direction_threshold`, `up_threshold`

**수정 포인트**:
```python
# 속도 조절 (54줄)
cv2.createTrackbar('Motor Up Speed', 'Camera Settings', 90, 125, nothing)
cv2.createTrackbar('Motor Down Speed', 'Camera Settings', 50, 125, nothing)

# 라인 검출 민감도 (52줄)
cv2.createTrackbar('Detect Value', 'Camera Settings', 29, 150, nothing)

# 방향 결정 로직 (105~137줄)
def decide_direction(histogram, direction_threshold, car, detect_value):
    # 여기를 수정하면 주행 알고리즘 변경 가능
```

##### **5_autoplot_harr_cascade_thread.py** (표지판 인식)
- **기능**: 자율주행 + 교통 표지판 인식
- **인식 표지판**:
  - 진입금지 (하단): `obstacle.xml`
  - 정지 표지판 (상단): `stop.xml`
  - 일반 정지: `no_drive.xml`

**수정 포인트**:
```python
# XML 모델 경로 (42~44줄)
no_drive_bottom_cascade_path = './xml/obstacle.xml'
no_drive_top_cascade_path = './xml/stop.xml'
stop_cascade_path = './xml/no_drive.xml'

# 표지판 감지 시 동작 (69~98줄)
def detect_no_drive_bottom(frame, control_signals):
    # 표지판 감지 로직
    
# 정지 신호 처리 (100~112줄)
def detect_stop_sign(frame, control_signals):
    # 정지 신호 처리
```

---

### 3. **컴퓨터 비전 & OpenCV 예제**

#### 📍 `04_cascade/` 폴더

객체 인식 관련 코드:
- `3_object_camera_haarcascade.py`: Haar Cascade 기본 예제
- `4_auto_plot_park_test.py`: 주차 표지판 인식
- `5_multi_thread_cascade.py`: 멀티스레드 객체 인식

#### 📍 `opencv/` 폴더

다양한 OpenCV 활용 예제:
- `03.Speech_Car_line_patrol/`: 음성 제어 + 라인 트래킹
- `04.Face_tracking/`: 얼굴 추적
- `05.Face_follow/`: 얼굴 따라가기
- `08.Autopilot_map_sandbox/`: 맵 기반 자율주행

---

### 4. **유틸리티 파일**

#### `lib/raspbot/PID.py`
- **기능**: PID 제어 알고리즘
- **사용처**: 정밀한 모터 제어, 카메라 트래킹

#### `lib/raspbot/HSV_Config.py`
- **기능**: 색상 기반 객체 추적 설정
- **사용처**: 컬러 라인 트래킹

#### `lib/raspbot/color_detection.py`
- **기능**: 색상 감지

#### `lib/raspbot/face_tracking.py`
- **기능**: 얼굴 추적

---

## ⚠️ 수정 불가능한 파일

### `lib/raspbot/raspbot.pyc` (컴파일된 메인 서버)

- **문제**: 원본 `raspbot.py` 파일이 **존재하지 않음**
- **역할**: 웹 서버 (Flask 기반으로 추정)
  - 카메라 스트리밍
  - 웹 인터페이스 제공
  - REST API 제공 (추정)
- **해결책**:
  1. 원본 `.py` 파일을 찾아야 함
  2. 또는 자율주행 코드를 직접 실행 (웹 서버 없이)

**웹 서버 관련 파일**:
- `lib/raspbot/templates/index.html`: 웹 UI
- `lib/raspbot/yb-discover.py`: UDP 디스커버리 서비스 (수정 가능)

---

## 🚀 추천 수정 워크플로우

### 시나리오 1: 자율주행 알고리즘 개선

1. **파일**: `03_self_driving/2_autoplot___test.py`
2. **수정 예시**:
```python
# 속도를 더 빠르게
cv2.createTrackbar('Motor Up Speed', 'Camera Settings', 110, 125, nothing)  # 90 → 110

# 라인 검출 민감도 조절
cv2.createTrackbar('Detect Value', 'Camera Settings', 35, 150, nothing)  # 29 → 35

# 방향 판단 임계값
cv2.createTrackbar('Direction Threshold', 'Camera Settings', 40000, 500000, nothing)  # 30000 → 40000
```

3. **실행**:
```bash
cd /home/pi/project_demo/03_self_driving
python3 2_autoplot___test.py
```

---

### 시나리오 2: 표지판 인식 추가

1. **파일**: `03_self_driving/5_autoplot_harr_cascade_thread.py`
2. **수정 예시**: 새로운 표지판 추가
```python
# 새로운 cascade 모델 추가 (50줄 아래)
speed_limit_cascade_path = './xml/speed_limit.xml'
speed_limit_cascade = cv2.CascadeClassifier(speed_limit_cascade_path)

# 감지 함수 추가
def detect_speed_limit(frame, control_signals):
    gray = weighted_gray(frame, r_weight, g_weight, b_weight)
    speed_limits = speed_limit_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    control_signals['speed_limit'] = len(speed_limits) > 0
    if control_signals['speed_limit']:
        draw_rectangles_and_text(frame, speed_limits, "speed_limit")
        # 속도 제한 로직
        motor_up_speed = 60  # 속도 줄이기
```

---

### 시나리오 3: LED 효과 변경

1. **파일**: `lib/raspbot/Raspbot_Lib.py`
2. **수정 예시**: 새로운 LED 효과 추가
```python
# LightShow 클래스에 새로운 효과 추가 (300줄 이후)
def my_custom_effect(self, effect_duration, speed):
    """사용자 정의 LED 효과"""
    colors = [0, 1, 2, 3, 4, 5, 6]
    end_time = time.time()
    
    while self.running and time.time() - end_time < effect_duration:
        # 여기에 커스텀 로직 작성
        for i in range(self.num_lights):
            color = random.choice(colors)
            self.bot.Ctrl_WQ2812_Alone(i, 1, color)
        time.sleep(speed)
    
    self.turn_off_all_lights()

# execute_effect에 추가 (212줄 이후)
def execute_effect(self, effect_name, effect_duration, speed, current_color):
    if effect_name == 'my_custom':
        self.my_custom_effect(effect_duration, speed)
    # ... 기존 코드
```

---

### 시나리오 4: 하드웨어 제어 파라미터 변경

1. **파일**: `lib/raspbot/Raspbot_Lib.py`
2. **수정 예시**:
```python
# 서보 모터 범위 변경 (91~102줄)
def Ctrl_Servo(self, id, angle):
    reg = 0x02
    data = [id, angle]
    if angle < 0:
        angle = 0
    elif angle > 180:
        angle = 180
    if (id == 2 and angle > 120):  # 100 → 120 (더 높은 각도 허용)
        angle = 120
    self.write_array(reg, data)
```

---

## 📝 파일 수정 후 적용 방법

### 방법 1: Python 파일 직접 실행
```bash
# 수정한 자율주행 코드 실행
python3 /home/pi/project_demo/03_self_driving/2_autoplot___test.py
```

### 방법 2: 라이브러리 수정 후 재시작
```bash
# Raspbot_Lib.py 수정 후
sudo systemctl restart raspbot.service
```

### 방법 3: 새로운 .pyc 컴파일 (raspbot.py가 있는 경우)
```bash
cd /home/pi/project_demo/raspbot
python3 compile.py
sudo systemctl restart raspbot.service
```

---

## 🔍 소스 코드 찾기 팁

### 특정 기능 찾기
```bash
# 예: "Car_Run" 함수가 어디에 있는지 찾기
grep -r "def Car_Run" /home/pi/project_demo/

# 예: Flask 서버 코드 찾기
grep -r "Flask\|@app.route" /home/pi/project_demo/

# 예: 카메라 관련 코드 찾기
grep -r "VideoCapture\|cv2.imread" /home/pi/project_demo/
```

---

## 💡 주요 수정 포인트 요약

| 목적 | 파일 | 라인 |
|------|------|------|
| 주행 속도 변경 | `03_self_driving/2_autoplot___test.py` | 54-55 |
| 라인 검출 민감도 | `03_self_driving/2_autoplot___test.py` | 52 |
| 방향 판단 알고리즘 | `03_self_driving/2_autoplot___test.py` | 105-137 |
| 서보 모터 각도 범위 | `lib/raspbot/Raspbot_Lib.py` | 91-102 |
| LED 효과 | `lib/raspbot/Raspbot_Lib.py` | 203-394 |
| 표지판 인식 | `03_self_driving/5_autoplot_harr_cascade_thread.py` | 42-112 |
| 모터 제어 | `04_cascade/YB_Pcb_Car.py` | 62-103 |
| PID 파라미터 | `lib/raspbot/PID.py` | 전체 |

---

## 🐛 디버깅 팁

### 1. 실시간 디버깅
자율주행 코드에는 트랙바가 내장되어 있어 **실시간으로 파라미터 조절 가능**합니다!

```python
# ESC 키: 프로그램 종료
# Space 키: 일시정지 및 디버깅
```

### 2. 로그 출력
```python
# 중요한 값 출력
print(f"Direction: {direction}, Speed: {motor_up_speed}")
print(f"Histogram: {histogram}")
```

### 3. OpenCV 디버깅 창
```python
# 중간 처리 결과 시각화
cv2.imshow('Debug Window', processed_frame)
```

---

## 📚 참고 자료

- **OpenCV 문서**: https://docs.opencv.org/
- **Raspberry Pi GPIO**: https://www.raspberrypi.org/documentation/usage/gpio/
- **Haar Cascade 학습**: https://docs.opencv.org/3.4/dc/d88/tutorial_traincascade.html

---

## ✅ 다음 단계

1. 원하는 기능 선택
2. 해당 파일 열기
3. 수정
4. 테스트 실행
5. 결과 확인 및 조정

**가장 쉬운 시작점**: `03_self_driving/2_autoplot___test.py`의 트랙바 기본값 변경!

