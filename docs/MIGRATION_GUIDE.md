# 🔄 Raspbot v2 마이그레이션 가이드

## YB_Pcb_Car → Raspbot_Lib 전환 가이드

이 문서는 구 버전 `YB_Pcb_Car`를 사용하는 코드를 최신 `Raspbot_Lib`로 전환하는 방법을 설명합니다.

---

## 📋 목차

1. [주요 변경사항](#주요-변경사항)
2. [라이브러리 Import 변경](#라이브러리-import-변경)
3. [객체 생성 변경](#객체-생성-변경)
4. [모터 제어 변경](#모터-제어-변경)
5. [서보 모터 변경](#서보-모터-변경)
6. [추가 기능](#추가-기능)
7. [전체 예제 비교](#전체-예제-비교)
8. [체크리스트](#체크리스트)

---

## 🎯 주요 변경사항

| 구분 | 구 버전 (YB_Pcb_Car) | 신 버전 (Raspbot_Lib) |
|------|---------------------|----------------------|
| 라이브러리 | `import YB_Pcb_Car` | `from Raspbot_Lib import Raspbot` |
| 객체 생성 | `car = YB_Pcb_Car.YB_Pcb_Car()` | `bot = Raspbot()` |
| 모터 제어 | `car.Car_Run(speed1, speed2)` | `bot.Ctrl_Muto(id, speed)` |
| 속도 범위 | 0~255 (방향 별도) | -255~255 (음수=후진) |
| 서보 2 최대각도 | 180도 | 110도 |
| 추가 기능 | 없음 | LED, 부저, 센서 등 |

---

## 📦 라이브러리 Import 변경

### ❌ 구 버전
```python
import YB_Pcb_Car

car = YB_Pcb_Car.YB_Pcb_Car()
```

### ✅ 신 버전
```python
import sys
import os

# Raspbot 라이브러리 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib', 'raspbot'))

from Raspbot_Lib import Raspbot

bot = Raspbot()
```

---

## 🚗 모터 제어 변경

### 기본 이동

#### ❌ 구 버전
```python
# 전진
car.Car_Run(speed1, speed2)

# 후진
car.Car_Back(speed1, speed2)

# 좌회전
car.Car_Left(speed1, speed2)

# 우회전
car.Car_Right(speed1, speed2)

# 정지
car.Car_Stop()
```

#### ✅ 신 버전 (방법 1: 개별 모터 제어)
```python
# 전진
bot.Ctrl_Muto(0, 100)   # M1 (Left Front)
bot.Ctrl_Muto(1, 100)   # M2 (Left Rear)
bot.Ctrl_Muto(2, 100)   # M3 (Right Front)
bot.Ctrl_Muto(3, 100)   # M4 (Right Rear)

# 후진 (음수 사용)
bot.Ctrl_Muto(0, -100)
bot.Ctrl_Muto(1, -100)
bot.Ctrl_Muto(2, -100)
bot.Ctrl_Muto(3, -100)

# 좌회전 (왼쪽 후진, 오른쪽 전진)
bot.Ctrl_Muto(0, -80)
bot.Ctrl_Muto(1, -80)
bot.Ctrl_Muto(2, 100)
bot.Ctrl_Muto(3, 100)

# 우회전 (왼쪽 전진, 오른쪽 후진)
bot.Ctrl_Muto(0, 100)
bot.Ctrl_Muto(1, 100)
bot.Ctrl_Muto(2, -80)
bot.Ctrl_Muto(3, -80)

# 정지
for i in range(4):
    bot.Ctrl_Muto(i, 0)
```

#### ✅ 신 버전 (방법 2: 함수로 래핑)
```python
def car_run(speed_left, speed_right):
    """전진"""
    bot.Ctrl_Muto(0, speed_left)
    bot.Ctrl_Muto(1, speed_left)
    bot.Ctrl_Muto(2, speed_right)
    bot.Ctrl_Muto(3, speed_right)

def car_stop():
    """정지"""
    for i in range(4):
        bot.Ctrl_Muto(i, 0)

def car_left(speed_left, speed_right):
    """좌회전"""
    bot.Ctrl_Muto(0, -speed_left)
    bot.Ctrl_Muto(1, -speed_left)
    bot.Ctrl_Muto(2, speed_right)
    bot.Ctrl_Muto(3, speed_right)

def car_right(speed_left, speed_right):
    """우회전"""
    bot.Ctrl_Muto(0, speed_left)
    bot.Ctrl_Muto(1, speed_left)
    bot.Ctrl_Muto(2, -speed_right)
    bot.Ctrl_Muto(3, -speed_right)

# 사용 예
car_run(100, 100)    # 전진
car_left(50, 100)    # 좌회전
car_right(100, 50)   # 우회전
car_stop()           # 정지
```

### 속도 범위 비교

| 동작 | 구 버전 | 신 버전 |
|------|--------|---------|
| 전진 최대 | `Car_Run(255, 255)` | `Ctrl_Muto(0, 255)` |
| 후진 최대 | `Car_Back(255, 255)` | `Ctrl_Muto(0, -255)` |
| 정지 | `Car_Stop()` | `Ctrl_Muto(0, 0)` |

---

## 🎮 서보 모터 변경

### ❌ 구 버전
```python
# 서보 1: 0~180도
car.Ctrl_Servo(1, 90)

# 서보 2: 0~180도
car.Ctrl_Servo(2, 119)
```

### ✅ 신 버전
```python
# 서보 1: 0~180도 (변경 없음)
bot.Ctrl_Servo(1, 90)

# 서보 2: 0~110도 (최대각도 제한!)
bot.Ctrl_Servo(2, 25)  # 기본값 25도

# ⚠️ 주의: 서보 2는 110도 이상 설정 금지!
if servo_2_angle > 110:
    servo_2_angle = 110
bot.Ctrl_Servo(2, servo_2_angle)
```

---

## 🎨 추가 기능

신 버전에서는 추가 하드웨어 제어 기능이 있습니다!

### LED 제어

```python
# 모든 LED 켜기
bot.Ctrl_WQ2812_ALL(1, color)
# color: 0=빨강, 1=초록, 2=파랑, 3=노랑, 4=보라, 5=청록, 6=흰색

# 모든 LED 끄기
bot.Ctrl_WQ2812_ALL(0, 0)

# 개별 LED 제어 (1~14번)
bot.Ctrl_WQ2812_Alone(1, 1, 0)  # 1번 LED를 빨간색으로

# LED 밝기 제어 (RGB)
bot.Ctrl_WQ2812_brightness_ALL(255, 0, 0)  # 빨간색 최대 밝기
```

### 부저 제어

```python
# 부저 켜기
bot.Ctrl_BEEP_Switch(1)
time.sleep(0.5)

# 부저 끄기
bot.Ctrl_BEEP_Switch(0)
```

### 센서 읽기

```python
# 초음파 센서 활성화 및 읽기
bot.Ctrl_Ulatist_Switch(1)  # 센서 켜기
time.sleep(0.1)
diss_H = bot.read_data_array(0x1b, 1)[0]
diss_L = bot.read_data_array(0x1a, 1)[0]
distance = (diss_H << 8) | diss_L
print(f"Distance: {distance}mm")
bot.Ctrl_Ulatist_Switch(0)  # 센서 끄기

# 라인 트래킹 센서 읽기
track = bot.read_data_array(0x0a, 1)
track_value = int(track[0])
x1 = (track_value >> 3) & 0x01
x2 = (track_value >> 2) & 0x01
x3 = (track_value >> 1) & 0x01
x4 = track_value & 0x01
print(f"Track sensors: {x1} {x2} {x3} {x4}")

# 적외선 리모컨 읽기
bot.Ctrl_IR_Switch(1)  # IR 켜기
time.sleep(0.1)
ir_data = bot.read_data_array(0x0c, 1)
print(f"IR data: {ir_data}")
bot.Ctrl_IR_Switch(0)  # IR 끄기
```

---

## 📝 전체 예제 비교

### 구 버전 (YB_Pcb_Car)

```python
import cv2
import YB_Pcb_Car
import time

# 초기화
cap = cv2.VideoCapture(0)
car = YB_Pcb_Car.YB_Pcb_Car()

# 서보 모터 설정
car.Ctrl_Servo(1, 90)
car.Ctrl_Servo(2, 119)

try:
    while True:
        ret, frame = cap.read()
        
        # ... 이미지 처리 ...
        
        # 전진
        car.Car_Run(100, 100)
        time.sleep(1)
        
        # 좌회전
        car.Car_Left(50, 100)
        time.sleep(1)
        
        # 정지
        car.Car_Stop()
        
except KeyboardInterrupt:
    pass

finally:
    car.Car_Stop()
    cap.release()
    cv2.destroyAllWindows()
```

### 신 버전 (Raspbot_Lib)

```python
import cv2
import sys
import os
import time

# 라이브러리 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib', 'raspbot'))
from Raspbot_Lib import Raspbot

# 초기화
cap = cv2.VideoCapture(0)
bot = Raspbot()

# 서보 모터 설정
bot.Ctrl_Servo(1, 90)
bot.Ctrl_Servo(2, 25)  # ⚠️ 최대 110도

# LED 켜기 (시작 신호)
bot.Ctrl_WQ2812_ALL(1, 2)  # 파란색

# 부저 (시작 신호)
bot.Ctrl_BEEP_Switch(1)
time.sleep(0.2)
bot.Ctrl_BEEP_Switch(0)

try:
    while True:
        ret, frame = cap.read()
        
        # ... 이미지 처리 ...
        
        # 전진 (LED: 초록색)
        bot.Ctrl_Muto(0, 100)
        bot.Ctrl_Muto(1, 100)
        bot.Ctrl_Muto(2, 100)
        bot.Ctrl_Muto(3, 100)
        bot.Ctrl_WQ2812_ALL(1, 1)  # 초록색
        time.sleep(1)
        
        # 좌회전 (LED: 노란색)
        bot.Ctrl_Muto(0, -50)
        bot.Ctrl_Muto(1, -50)
        bot.Ctrl_Muto(2, 100)
        bot.Ctrl_Muto(3, 100)
        bot.Ctrl_WQ2812_ALL(1, 3)  # 노란색
        time.sleep(1)
        
        # 정지
        for i in range(4):
            bot.Ctrl_Muto(i, 0)
        
except KeyboardInterrupt:
    pass

finally:
    # 정지
    for i in range(4):
        bot.Ctrl_Muto(i, 0)
    
    # LED 끄기
    bot.Ctrl_WQ2812_ALL(0, 0)
    
    # 부저 끄기
    bot.Ctrl_BEEP_Switch(0)
    
    # 카메라 해제
    cap.release()
    cv2.destroyAllWindows()
    
    # 객체 삭제 (중요!)
    del bot
```

---

## ✅ 체크리스트

기존 코드를 신 버전으로 전환할 때 확인할 사항:

### 필수 변경
- [ ] `import YB_Pcb_Car` → `from Raspbot_Lib import Raspbot`
- [ ] 라이브러리 경로 `sys.path.append()` 추가
- [ ] `car = YB_Pcb_Car.YB_Pcb_Car()` → `bot = Raspbot()`
- [ ] `car.Car_Run()` → `bot.Ctrl_Muto()` (4개 모터 각각)
- [ ] `car.Car_Stop()` → 4개 모터 각각 0으로
- [ ] 서보 2 각도 110도 이하로 제한
- [ ] 모터 속도 음수 사용 (후진)
- [ ] 종료 시 `del bot` 추가

### 선택 변경
- [ ] LED 효과 추가
- [ ] 부저 효과 추가
- [ ] 센서 읽기 기능 추가
- [ ] 에러 처리 강화

---

## 🔧 자주 묻는 질문

### Q1: 왜 전환해야 하나요?
**A:** 신 버전은 더 많은 기능(LED, 부저, 센서)과 더 유연한 모터 제어를 제공합니다.

### Q2: 기존 코드가 작동 안 하나요?
**A:** `YB_Pcb_Car`는 여전히 작동하지만, 새로운 하드웨어 기능을 사용할 수 없습니다.

### Q3: 모든 파일을 수정해야 하나요?
**A:** 아니요. 새 프로젝트나 중요한 파일만 우선 전환하세요.

### Q4: 서보 2가 110도까지만 되는 이유는?
**A:** 하드웨어 제한사항입니다. `02_Basic` 예제를 참고하세요.

### Q5: 속도 범위가 달라진 이유는?
**A:** 음수로 후진을 표현하여 더 직관적입니다.

---

## 📚 참고 문서

- [QUICK_START.md](./QUICK_START.md) - 빠른 시작 가이드
- [SOURCE_CODE_GUIDE.md](./SOURCE_CODE_GUIDE.md) - 소스 코드 상세 가이드
- `02_Basic/` - 공식 예제 코드
- `lib/raspbot/Raspbot_Lib.py` - 라이브러리 소스

---

## 🎓 마이그레이션 예제

실제 파일 마이그레이션 예제:
- ❌ 구 버전: `03_self_driving/6_custom_autoplot_old.py`
- ✅ 신 버전: `03_self_driving/6_custom_autoplot.py`

두 파일을 비교하여 변경 사항을 확인하세요!

---

**업데이트 날짜**: 2025-11-25  
**버전**: v2.0

