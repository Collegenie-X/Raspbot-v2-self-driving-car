# 🚦 신호등 제어 시스템 (Traffic Light Control System)

**파일명**: `4_traffic_light_control.py`  
**작성일**: 2025-12-09  
**버전**: v1.0

---

## 📋 목차

1. [개요](#개요)
2. [신호등 제어 로직](#신호등-제어-로직)
3. [주요 특징](#주요-특징)
4. [시스템 구조](#시스템-구조)
5. [신호등 감지 알고리즘](#신호등-감지-알고리즘)
6. [상태 기반 제어](#상태-기반-제어)
7. [실행 방법](#실행-방법)
8. [트러블슈팅](#트러블슈팅)
9. [Haar Cascade XML 파일](#haar-cascade-xml-파일)

---

## 개요

이 시스템은 **빨간불/초록불 신호등을 Haar Cascade로 감지**하여 자율주행 차량을 제어합니다.

### 핵심 기능

- 🔴 **빨간불 감지**: 모터 즉시 정지, 이미지 인식은 계속, 부저 1회
- 🟢 **초록불 감지**: 신호 해제, 부저 1회, 자율주행 재개
- 🚗 **자율주행 모드**: 라인 트레이싱으로 자동 주행
- 📷 **실시간 처리**: 정지 중에도 프레임 처리 계속 진행

---

## 신호등 제어 로직

### 1. 빨간불 감지 시 (🔴 RED SIGN)

```
RED sign 감지 → 부저 1회 (0.1초) → 정지 상태 진입 → 계속 유지 (GREEN sign까지)
```

**처리 흐름**:
1. 처음 감지: `red_light_active = True`, 부저 1회 울림
2. 정지 상태: `waiting_for_green = True` (GREEN sign 대기)
3. ⭐ **중요**: RED sign이 사라져도 정지 상태 **계속 유지**
4. 해제 조건: **GREEN sign 감지만** 가능
5. 이미지 인식: 계속 진행 (프레임 처리 멈추지 않음)

**코드**:
```python
elif red_detected:
    # 처음 감지된 경우
    if not red_light_active:
        red_light_active = True
        waiting_for_green = True  # 정지 상태 진입
        
        if USE_BEEP and not red_beep_played:
            bot.Ctrl_BEEP_Switch(1)  # 부저 ON
            time.sleep(0.1)
            bot.Ctrl_BEEP_Switch(0)  # 부저 OFF
            red_beep_played = True

# 정지 상태 유지 (RED sign 사라져도)
if waiting_for_green:
    car_stop()  # 모터 계속 정지
```

**핵심**: RED sign이 화면에서 사라져도 `waiting_for_green`이 True이므로 계속 정지!

### 2. 초록불 감지 시 (🟢 GREEN SIGN)

```
GREEN sign 감지 → 부저 1회 (0.1초) → 모든 상태 리셋 → 자율주행 재개
```

**처리 흐름**:
1. 조건: `waiting_for_green = True` (정지 상태)일 때만 유효
2. 부저 1회 울림
3. ⭐ **모든 상태 완전 리셋**:
   - `waiting_for_green = False`
   - `red_light_active = False`
   - `red_beep_played = False`
   - `green_light_active = False`
   - `green_beep_played = False`
4. 자율주행 모드 즉시 재개

**코드**:
```python
# 최우선 처리: GREEN sign이 정지 상태를 해제
if green_detected and waiting_for_green:
    if not green_beep_played:
        if USE_BEEP:
            bot.Ctrl_BEEP_Switch(1)
            time.sleep(0.1)
            bot.Ctrl_BEEP_Switch(0)
            green_beep_played = True
    
    # ⭐ 모든 상태 완전 리셋
    waiting_for_green = False
    red_light_active = False
    red_beep_played = False
    green_light_active = False
    green_beep_played = False
```

**핵심**: GREEN sign만이 정지 상태를 해제할 수 있음!

### 3. 신호등 없을 때 (⚪ NO SIGNAL)

```
신호등 없음 → 자율주행 모드 → 라인 트레이싱
```

**처리 흐름**:
1. 신호등 감지 안 됨
2. 정상 자율주행 진행
3. 히스토그램 기반 방향 결정
4. 모터 제어 (전진/좌회전/우회전)

---

## 주요 특징

### ✅ 1. 상태 기반 제어

신호등 상태를 플래그로 관리하여 안정적인 제어를 구현합니다.

| 상태 변수 | 설명 |
|---------|------|
| `red_light_active` | 현재 빨간불이 감지되고 있는지 |
| `green_light_active` | 현재 초록불이 감지되고 있는지 |
| `waiting_for_green` | 빨간불 후 초록불 대기 중인지 |
| `red_beep_played` | 빨간불 부저 울렸는지 (중복 방지) |
| `green_beep_played` | 초록불 부저 울렸는지 (중복 방지) |

### ✅ 2. 부저 1회만 울림

같은 신호등이 계속 감지되어도 **부저는 최초 1회만** 울립니다.

```python
if USE_BEEP and not red_beep_played:
    bot.Ctrl_BEEP_Switch(1)
    time.sleep(0.1)
    bot.Ctrl_BEEP_Switch(0)
    red_beep_played = True  # 플래그 설정으로 중복 방지
```

### ✅ 3. 프레임 처리 계속 진행

신호등 대기 중에도 **이미지 인식은 계속** 진행됩니다.

```python
if red_light_active or waiting_for_green:
    car_stop()  # 모터만 정지
    # 이미지 인식은 계속 (프레임 처리 중단 안 함)
    continue
```

### ✅ 4. 우선순위 제어

신호등 우선순위: **빨간불 > 초록불 > 자율주행**

```python
# 1. 빨간불 최우선 (감지 시 즉시 정지)
if red_detected:
    car_stop()

# 2. 초록불 (빨간불 후에만 유효)
elif green_detected and waiting_for_green:
    waiting_for_green = False  # 해제

# 3. 자율주행 (신호등 없을 때)
else:
    control_car(direction, up_speed, down_speed)
```

---

## 시스템 구조

### 파일 구조

```
04_cascade/
├── 4_traffic_light_control.py          # 메인 실행 파일
├── 4_TRAFFIC_LIGHT_가이드.md            # 가이드 문서 (이 파일)
└── xml/
    ├── red_light.xml                    # 빨간불 Haar Cascade
    └── green_light.xml                  # 초록불 Haar Cascade
```

### 함수 구조

#### 1. 초기화 함수
```python
initialize_raspbot()          # Raspbot 하드웨어 초기화
initialize_camera()           # 카메라 초기화
setup_initial_hardware_state() # 초기 하드웨어 상태 설정
```

#### 2. 이미지 처리 함수
```python
weighted_gray()               # RGB 가중치 기반 그레이스케일 변환
detect_road_lines()           # 도로선 감지 (빨간색 + 회색)
process_frame()               # 전체 프레임 처리 파이프라인
```

#### 3. 신호등 감지 함수
```python
detect_traffic_lights()       # 빨간불/초록불 감지 (Haar Cascade)
get_detection_frame()         # 감지용 프레임 소스 선택
```

#### 4. 차량 제어 함수
```python
car_run()                     # 전진
car_stop()                    # 정지
car_left()                    # 좌회전
car_right()                   # 우회전
control_car()                 # 방향에 따른 차량 제어
```

#### 5. 방향 결정 함수
```python
analyze_histogram()           # 히스토그램 3등분 분석
decide_direction()            # 방향 결정 (LEFT/UP/RIGHT)
```

---

## 신호등 감지 알고리즘

### Haar Cascade 기반 감지

#### 1. 프레임 전처리

```python
# RGB 가중치 기반 그레이스케일 변환
gray_frame = weighted_gray(detect_frame, r_weight, g_weight, b_weight)
```

#### 2. Haar Cascade 감지

```python
# 빨간불 감지
red_lights = red_light_cascade.detectMultiScale(
    gray_frame,
    scaleFactor=1.1,      # 이미지 피라미드 스케일
    minNeighbors=5,       # 최소 이웃 수 (노이즈 필터링)
    minSize=(30, 30)      # 최소 객체 크기
)

# 초록불 감지
green_lights = green_light_cascade.detectMultiScale(
    gray_frame,
    scaleFactor=1.1,
    minNeighbors=5,
    minSize=(30, 30)
)
```

#### 3. 감지 결과 시각화

```python
# 빨간불: 빨간색 윤곽선 (0, 0, 255)
for x, y, w, h in red_lights:
    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 3)
    cv2.putText(frame, "RED LIGHT", (x, y-10), ...)

# 초록불: 초록색 윤곽선 (0, 255, 0)
for x, y, w, h in green_lights:
    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
    cv2.putText(frame, "GREEN LIGHT", (x, y-10), ...)
```

---

## 상태 기반 제어

### 상태 다이어그램

```
시작
  ↓
[자율주행 모드]
  ↓
RED sign 감지? ──NO──> [자율주행 계속]
  │                           ↑
 YES                          │
  ↓                           │
[정지 상태 진입]              │
  - 모터 정지                 │
  - 부저 1회                  │
  - waiting_for_green = True  │
  ↓                           │
[정지 상태 유지] ←────────────┤
  - 모터 계속 정지             │
  - RED sign 사라져도 유지 ⭐  │
  - 이미지 인식은 계속         │
  ↓                           │
GREEN sign 감지? ──NO──> [대기 계속]
  │
 YES
  ↓
[정지 상태 해제]
  - 부저 1회
  - 모든 상태 리셋 ⭐
  - waiting_for_green = False
  └─────────────────────────┘
```

**핵심 포인트**:
- ⭐ RED sign 사라짐 ≠ 정지 해제
- ⭐ GREEN sign 감지 = 유일한 해제 조건

### 상태 전환 코드

```python
# 초기 상태
red_light_active = False
green_light_active = False
waiting_for_green = False

# === 빨간불 감지 ===
if red_detected:
    if not red_light_active:
        red_light_active = True      # 빨간불 상태 활성화
        waiting_for_green = True     # 초록불 대기 시작
        # 부저 1회
    car_stop()

# === 빨간불 사라짐 ===
else:
    if red_light_active:
        red_light_active = False     # 빨간불 상태 해제
        # waiting_for_green은 유지 (초록불 기다림)

# === 초록불 감지 (빨간불 후) ===
if green_detected and waiting_for_green:
    if not green_light_active:
        green_light_active = True
        # 부저 1회
    
    # 신호 완전 해제
    waiting_for_green = False
    green_light_active = False

# === 자율주행 ===
if not red_light_active and not waiting_for_green:
    control_car(direction, up_speed, down_speed)
```

---

## 실행 방법

### 1. 환경 준비

#### Haar Cascade XML 파일 준비

신호등 감지를 위한 Haar Cascade XML 파일이 필요합니다.

```bash
04_cascade/xml/
├── red_light.xml      # 빨간불 감지 모델
└── green_light.xml    # 초록불 감지 모델
```

**XML 파일이 없는 경우**:
- 경고 메시지가 표시되지만 프로그램은 실행됩니다
- 신호등 감지는 작동하지 않고 자율주행만 동작합니다

#### 필요한 라이브러리

```python
import cv2              # OpenCV
import numpy as np      # NumPy
import time             # 시간 제어
from Raspbot_Lib import Raspbot  # Raspbot 하드웨어 제어
```

### 2. 프로그램 실행

```bash
cd 04_cascade
python3 4_traffic_light_control.py
```

### 3. 실행 화면

프로그램 실행 시 다음 윈도우가 표시됩니다:

| 윈도우 이름 | 설명 |
|-----------|------|
| `Camera Settings` | 트랙바 설정 창 |
| `1_Frame` | 원본 프레임 + ROI 영역 |
| `2_frame_transformed` | 원근 변환된 프레임 |
| `3_gray_frame` | 그레이스케일 프레임 |
| `4_Processed Frame` | 도로선 감지 + 방향 정보 |
| `5_Traffic_Light_Detection` | 신호등 감지 결과 |

### 4. 키보드 제어

| 키 | 기능 |
|----|------|
| `ESC` | 프로그램 종료 |
| `SPACE` | 모터 ON/OFF 토글 |
| `l` | LED ON/OFF 토글 |
| `b` | 부저 ON/OFF 토글 |

---

## 트랙바 설정

### 서보 모터 (카메라 각도)

| 트랙바 | 범위 | 기본값 | 설명 |
|-------|------|--------|------|
| `Servo_1_Angle` | 0~180 | 95 | 좌우 회전 각도 |
| `Servo_2_Angle` | 0~110 | 0 | 상하 회전 각도 |

### 이미지 처리

| 트랙바 | 범위 | 기본값 | 설명 |
|-------|------|--------|------|
| `ROI_Top_Y` | 0~1000 | 695 | ROI 상단 Y 좌표 (‰) |
| `ROI_Bottom_Y` | 0~1000 | 812 | ROI 하단 Y 좌표 (‰) |
| `Detect_Value` | 0~150 | 120 | 도로선 감지 임계값 |
| `Brightness` | 0~100 | 32 | 카메라 밝기 |
| `Contrast` | 0~100 | 0 | 카메라 대비 |
| `Saturation` | 0~100 | 0 | 카메라 채도 |

### RGB 가중치 (빛 반사 필터링)

| 트랙바 | 범위 | 기본값 | 설명 |
|-------|------|--------|------|
| `R_weight` | 0~100 | 30 | 빨강 채널 가중치 |
| `G_weight` | 0~100 | 40 | 초록 채널 가중치 |
| `B_weight` | 0~100 | 60 | 파랑 채널 가중치 |

**조정 가이드**:
- 밝은 환경: R↓(30), G=중간(40), B↑(60-80)
- 어두운 환경: R↑(60), G=중간(40), B↓(30)

### 방향 판단

| 트랙바 | 범위 | 기본값 | 설명 |
|-------|------|--------|------|
| `Direction_Threshold` | 0~500000 | 35000 | 좌우 회전 임계값 |
| `Up_Threshold` | 0~500000 | 220000 | 막다른 골목 임계값 |

### 모터 속도

| 트랙바 | 범위 | 기본값 | 설명 |
|-------|------|--------|------|
| `Motor_Up_Speed` | 0~255 | 15 | 전진 속도 |
| `Motor_Down_Speed` | 0~255 | 8 | 회전/후진 속도 |

### 신호등 감지 프레임 선택

| 트랙바 | 값 | 설명 |
|-------|-----|------|
| `Detect_Frame_Source` | 0 | 원본 프레임 (컬러) |
|  | 1 | 원근 변환 프레임 |
|  | 2 | 그레이스케일 프레임 |

**권장**: `0` (원본 프레임) - 전체 화면에서 신호등 감지

---

## 트러블슈팅

### 1. 신호등이 감지되지 않음

**문제**: 빨간불/초록불이 화면에 나와도 감지 안 됨

**해결 방법**:

#### A. XML 파일 확인
```bash
ls -la 04_cascade/xml/
# red_light.xml, green_light.xml 파일 존재 확인
```

#### B. Haar Cascade 로드 확인
```python
if red_light_cascade.empty():
    print("⚠️ red_light.xml not found")
# → XML 파일 경로 확인
```

#### C. 프레임 소스 변경
- `Detect_Frame_Source` 트랙바를 0, 1, 2로 변경하며 테스트
- 원본 프레임(0)에서 가장 잘 감지됨

#### D. 감지 파라미터 조정
```python
# detectMultiScale 파라미터 조정
red_lights = red_light_cascade.detectMultiScale(
    gray_frame,
    scaleFactor=1.05,    # 1.1 → 1.05 (더 세밀하게)
    minNeighbors=3,      # 5 → 3 (더 민감하게)
    minSize=(20, 20)     # (30,30) → (20,20) (작은 객체도 감지)
)
```

### 2. 부저가 계속 울림

**문제**: 같은 신호등에서 부저가 여러 번 울림

**해결 방법**:

부저 플래그 확인:
```python
# 부저는 최초 1회만
if USE_BEEP and not red_beep_played:
    bot.Ctrl_BEEP_Switch(1)
    time.sleep(0.1)
    bot.Ctrl_BEEP_Switch(0)
    red_beep_played = True  # 플래그 설정
```

### 3. GREEN sign 감지 후에도 정지 상태

**문제**: GREEN sign 감지했는데 모터가 계속 정지

**해결 방법**:

상태 플래그 확인:
```python
if green_detected and waiting_for_green:
    # ⭐ 모든 상태 리셋 확인
    waiting_for_green = False  # ← 이 부분 확인
    red_light_active = False
    red_beep_played = False
    green_light_active = False
    green_beep_played = False
```

디버그 메시지 확인:
```bash
🟢 GREEN LIGHT DETECTED!
   ▶️  Releasing STOP state
   ▶️  Resuming AUTO DRIVING
✅ All traffic light states RESET
✅ AUTO DRIVING mode resumed
```

### 4. RED sign 없이 GREEN sign만 감지됨

**문제**: RED sign을 안 거치고 GREEN sign만 감지

**해결 방법**:

GREEN sign은 `waiting_for_green` 플래그가 있을 때만 유효:
```python
# GREEN sign은 정지 상태(waiting_for_green=True)일 때만 유효
if green_detected and waiting_for_green:
    # GREEN sign 처리
```

**정상 흐름**:
1. RED sign 감지 → `waiting_for_green = True` (정지 상태)
2. GREEN sign 감지 → 정지 해제
3. GREEN sign 단독 감지 → 무시 (정지 상태가 아니므로)

**설계 의도**:
- GREEN sign은 정지 상태를 해제하는 신호
- 정지 상태가 아니면 GREEN sign 무시

### 5. 모터가 움직이지 않음

**문제**: 신호등 없는데도 모터가 정지

**해결 방법**:

#### A. 모터 토글 확인
- `SPACE` 키를 눌러 모터 ON/OFF 확인
- 콘솔에 "Motor: ENABLED" 메시지 확인

#### B. 상태 플래그 확인
```python
# waiting_for_green이 True이면 무조건 정지
if waiting_for_green:
    car_stop()  # ← 이 조건 확인
```

#### C. 정지 상태 확인
```python
# 정지 상태를 해제하려면 GREEN sign 필요
if waiting_for_green:
    print("⏳ Waiting for GREEN sign")  # ← 이 메시지가 나오는지 확인
```

#### D. 디버그 메시지 확인
```bash
✅ Traffic Light: Normal - AUTO DRIVING
# → 자율주행 모드인지 확인

⏳ Traffic Light: Waiting for GREEN sign (RED disappeared)
# → 정지 상태인지 확인
```

#### E. 강제 리셋
정지 상태에서 벗어나려면:
1. GREEN sign을 보여주거나
2. 프로그램 재시작

---

## Haar Cascade XML 파일

### XML 파일 생성 방법

신호등 감지를 위한 Haar Cascade XML 파일은 별도로 학습해야 합니다.

#### 1. 학습 데이터 준비

```bash
positive_images/  # 빨간불/초록불 이미지
├── red_001.jpg
├── red_002.jpg
└── ...

negative_images/  # 배경 이미지 (신호등 없음)
├── bg_001.jpg
├── bg_002.jpg
└── ...
```

#### 2. OpenCV Cascade Trainer 사용

```bash
# Positive 샘플 생성
opencv_createsamples -info positive.txt -vec red_light.vec -w 24 -h 24

# Cascade 학습
opencv_traincascade \
  -data cascade_output/ \
  -vec red_light.vec \
  -bg negative.txt \
  -numPos 1000 \
  -numNeg 500 \
  -numStages 20 \
  -w 24 -h 24
```

#### 3. XML 파일 복사

```bash
cp cascade_output/cascade.xml ./xml/red_light.xml
```

### 대체 방법: YOLO 사용

Haar Cascade 대신 **YOLO** 객체 감지를 사용할 수도 있습니다.

```python
# YOLO 로드
net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")

# 신호등 감지
blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416))
net.setInput(blob)
outputs = net.forward()
```

→ **추천**: YOLO가 더 정확하지만, Haar Cascade가 더 빠름

---

## 디버그 메시지

### 정상 동작 메시지

#### RED sign 감지
```
==================================================
🔴 RED LIGHT DETECTED!
   ⏸️  Motor STOPPED
   ⏳ Waiting for GREEN light...
   ⭐ This state persists even if RED sign disappears
==================================================
🔊 Beep played for RED light (1 time only)
```

#### RED sign 사라짐 (정지 상태 유지)
```
⏸️  Motor STOPPED (waiting for GREEN sign)
   ⭐ RED sign disappeared, but STOP state persists
```

**중요**: RED sign이 사라져도 정지 상태는 계속 유지됨!

#### GREEN sign 감지 (정지 해제)
```
==================================================
🟢 GREEN LIGHT DETECTED!
   ▶️  Releasing STOP state
   ▶️  Resuming AUTO DRIVING
==================================================
🔊 Beep played for GREEN light (1 time only)
✅ All traffic light states RESET
✅ AUTO DRIVING mode resumed
```

**중요**: GREEN sign만이 정지 상태를 해제할 수 있음!

#### 자율주행 모드
```
--------------------------------------------------
Frame: 10 | Motor: ON
✅ Traffic Light: NONE or GREEN - AUTO DRIVING
--------------------------------------------------

--- Frame 10 ---
RGB Weights: R=30, G=40, B=60
Histogram Analysis:
  LEFT:    12345 (ratio: 0.123)
  CENTER:  23456 (ratio: 0.234)
  RIGHT:   13456 (ratio: 0.134)
Decision: Turn LEFT
TURN LEFT
FPS: 15.2
```

---

## 성능 최적화

### 1. FPS 향상

```python
# 프레임 처리 지연 최소화
time.sleep(0.01)  # 10ms (100 FPS 목표)
```

### 2. 감지 프레임 건너뛰기

```python
# 매 프레임마다 감지하지 않고 N 프레임마다 감지
if frame_count % 3 == 0:
    red_detected, green_detected, _, _ = detect_traffic_lights(...)
```

### 3. ROI 설정

신호등이 나타나는 영역만 감지하여 처리 속도 향상:

```python
# 신호등은 화면 상단에만 위치
traffic_roi = frame[0:120, :]  # 상단 120 픽셀만
red_detected, _, _, _ = detect_traffic_lights(traffic_roi, ...)
```

---

## 확장 아이디어

### 1. 좌회전/우회전 신호등

```python
# 좌회전 화살표 신호등
left_arrow_cascade = cv2.CascadeClassifier("./xml/left_arrow.xml")
left_arrows = left_arrow_cascade.detectMultiScale(...)
if len(left_arrows) > 0:
    # 좌회전 허용
```

### 2. 신호등 카운트다운

```python
# 빨간불 남은 시간 추정
red_light_start_time = time.time()
elapsed = time.time() - red_light_start_time
print(f"RED light duration: {elapsed:.1f}s")
```

### 3. 신호등 색상 확인

Haar Cascade + HSV 색상 검증:

```python
# Haar Cascade로 신호등 위치 감지
for x, y, w, h in detected_lights:
    roi = frame[y:y+h, x:x+w]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    
    # 빨간색 확인
    red_mask = cv2.inRange(hsv, lower_red, upper_red)
    if np.sum(red_mask) > threshold:
        # 빨간불 확정
```

### 4. 다중 신호등 처리

여러 신호등이 동시에 감지될 때:

```python
# 가장 큰 신호등 선택
if len(red_lights) > 1:
    largest = max(red_lights, key=lambda x: x[2] * x[3])
    # 가장 큰 것만 처리
```

---

## 요약

### 핵심 포인트

1. **RED sign 감지** → 정지 상태 진입, 부저 1회
2. ⭐ **정지 상태 유지** → RED sign 사라져도 계속 정지
3. ⭐ **GREEN sign 감지** → 유일한 해제 조건, 부저 1회, 모든 상태 리셋
4. **자율주행 재개** → GREEN sign 후 즉시 재개
5. **이미지 인식** → 정지 중에도 계속 진행
6. **부저 중복 방지** → 플래그로 1회만 울림
7. **상태 기반 제어** → 안정적인 신호등 처리

**가장 중요한 포인트**:
- 🔴 RED sign → 정지 상태 잠금 (LOCK)
- 🟢 GREEN sign → 정지 상태 해제 (UNLOCK)
- RED sign 사라짐 ≠ 정지 해제

### 장점

- ✅ 실제 신호등 시스템과 유사한 동작
- ✅ 안전한 정지 (빨간불에서 확실히 멈춤)
- ✅ 부저 소음 최소화 (1회만)
- ✅ 빠른 프레임 처리 (이미지 인식 계속)
- ✅ 확장 가능한 구조 (다른 신호 추가 용이)

### 한계

- ⚠️ Haar Cascade 정확도 제한 (조명, 각도에 민감)
- ⚠️ 신호등 학습 데이터 필요 (XML 파일)
- ⚠️ 실시간 처리 속도 (Raspberry Pi 성능)

---

## 참고 자료

### 관련 파일

- `3_object_autoplot___rgb_filter.py` - 표지판 감지 시스템 (기반 코드)
- `3_2_AUTOPLOT_HAARCASCADE_가이드.md` - Haar Cascade 가이드

### 외부 링크

- [OpenCV Cascade Classifier](https://docs.opencv.org/4.x/db/d28/tutorial_cascade_classifier.html)
- [Haar Cascade Training](https://docs.opencv.org/4.x/dc/d88/tutorial_traincascade.html)
- [Traffic Light Detection](https://github.com/topics/traffic-light-detection)

---

**문의사항이나 개선 제안은 이슈로 등록해 주세요!** 🚦
