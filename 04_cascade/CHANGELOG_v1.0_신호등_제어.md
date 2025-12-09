# CHANGELOG v1.0 - 신호등 제어 시스템

**파일**: `4_traffic_light_control.py`  
**작성일**: 2025-12-09  
**버전**: v1.0

---

## 📋 개요

신호등 제어 시스템을 구현했습니다. RED sign과 GREEN sign을 Haar Cascade로 감지하여 자율주행 차량을 제어합니다.

---

## 🎯 핵심 기능

### 1. RED Sign 감지 (🔴)

```
RED sign 감지 → 부저 1회 → 정지 상태 진입 → 계속 유지
```

**특징**:
- 처음 감지 시 부저 1회만 울림
- 모터 즉시 정지
- ⭐ **RED sign이 사라져도 정지 상태 계속 유지**
- 이미지 인식은 계속 진행 (프레임 처리 멈추지 않음)

**코드**:
```python
elif red_detected:
    if not red_light_active:
        red_light_active = True
        waiting_for_green = True  # 정지 상태 진입
        
        # 부저 1회
        if USE_BEEP and not red_beep_played:
            bot.Ctrl_BEEP_Switch(1)
            time.sleep(0.1)
            bot.Ctrl_BEEP_Switch(0)
            red_beep_played = True

# 정지 상태 유지
if waiting_for_green:
    car_stop()  # RED sign 사라져도 계속 정지
```

### 2. GREEN Sign 감지 (🟢)

```
GREEN sign 감지 → 부저 1회 → 모든 상태 리셋 → 자율주행 재개
```

**특징**:
- `waiting_for_green = True` (정지 상태)일 때만 유효
- 부저 1회 울림
- ⭐ **모든 상태 완전 리셋** (정지 해제)
- 자율주행 모드 즉시 재개

**코드**:
```python
# 최우선 처리
if green_detected and waiting_for_green:
    # 부저 1회
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

### 3. 정지 상태 유지 (⏸️)

```
정지 상태 = RED sign이 사라져도 계속 정지
```

**특징**:
- `waiting_for_green = True`이면 무조건 정지
- RED sign 화면에서 사라짐 ≠ 정지 해제
- ⭐ **GREEN sign만이 정지 상태를 해제할 수 있음**

**코드**:
```python
if waiting_for_green:
    car_stop()  # 계속 정지
    
    if DEBUG_MODE and frame_count % 30 == 0:
        if red_detected:
            print("⏸️  Motor STOPPED (RED sign visible)")
        else:
            print("⏸️  Motor STOPPED (waiting for GREEN sign)")
            print("   ⭐ RED sign disappeared, but STOP state persists")
```

---

## 🔄 상태 전환 다이어그램

```
[자율주행 모드]
       ↓
    RED sign 감지
       ↓
[정지 상태 진입]
 - waiting_for_green = True
 - 부저 1회
       ↓
[정지 상태 유지] ←─────┐
 - car_stop()          │
 - RED sign 사라져도   │ RED sign
   계속 정지 ⭐         │ 사라짐
       ↓                │
   GREEN sign 감지?  ──NO─┘
       │
      YES
       ↓
[정지 상태 해제]
 - 모든 상태 리셋 ⭐
 - 부저 1회
       ↓
[자율주행 모드 재개]
```

---

## 🚀 주요 변경사항

### 1. 정지 상태 우선순위 변경

**변경 전**:
```python
# RED sign이 사라지면 상태 리셋
if red_detected:
    red_light_active = True
else:
    red_light_active = False  # ← 문제: 너무 빨리 해제됨
```

**변경 후**:
```python
# GREEN sign 우선 처리 (정지 해제)
if green_detected and waiting_for_green:
    # 모든 상태 리셋 ⭐
    waiting_for_green = False
    red_light_active = False
    ...

# RED sign 처리 (정지 진입)
elif red_detected:
    if not red_light_active:
        waiting_for_green = True  # 정지 상태 진입

# 정지 상태 유지 (RED sign 사라져도)
if waiting_for_green:
    car_stop()  # 계속 정지 ⭐
```

### 2. 우선순위 순서

**우선순위**:
1. **GREEN sign** (정지 해제) - 최우선
2. **RED sign** (정지 진입) - 2순위
3. **정지 상태 유지** - 3순위
4. **자율주행** - 마지막

### 3. 상태 플래그 의미 명확화

| 플래그 | 의미 | 값 |
|--------|------|-----|
| `waiting_for_green` | 정지 상태 여부 | True = 정지, False = 주행 |
| `red_light_active` | RED sign 감지 여부 | True = 감지됨 |
| `red_beep_played` | 부저 울림 여부 | True = 울림 (중복 방지) |
| `green_beep_played` | 부저 울림 여부 | True = 울림 (중복 방지) |

**핵심**: `waiting_for_green`이 True이면 **무조건 정지**!

---

## 💡 설계 철학

### 1. LOCK-UNLOCK 메커니즘

```
🔴 RED sign   = LOCK   (정지 상태 잠금)
🟢 GREEN sign = UNLOCK (정지 상태 해제)
```

- RED sign은 "정지 상태를 켜는" 스위치
- GREEN sign은 "정지 상태를 끄는" 스위치
- RED sign이 사라져도 LOCK은 유지됨
- GREEN sign만이 UNLOCK 가능

### 2. 안전 우선 설계

```
안전 > 편의
```

- RED sign을 한 번 보면 확실히 멈춤
- GREEN sign을 확인할 때까지 절대 움직이지 않음
- 중간에 RED sign이 사라져도 안전하게 정지 유지

### 3. 명확한 상태 관리

```python
# 상태 확인이 명확함
if waiting_for_green:
    # 정지 상태
    car_stop()
else:
    # 자율주행 상태
    control_car(...)
```

---

## 📊 비교표

| 항목 | 이전 방식 | 현재 방식 (v1.0) |
|------|----------|-----------------|
| RED sign 사라짐 | 바로 해제 ❌ | 계속 유지 ✅ |
| GREEN sign 역할 | 선택 사항 | 필수 (유일한 해제) ✅ |
| 안전성 | 중간 | 높음 ✅ |
| 상태 명확성 | 애매함 | 명확함 ✅ |
| 부저 중복 | 방지 ✅ | 방지 ✅ |
| 이미지 인식 | 계속 ✅ | 계속 ✅ |

---

## 🎮 사용 예시

### 시나리오 1: 정상 작동

```
1. 자율주행 중
2. RED sign 감지 → 부저 1회, 정지
3. RED sign 사라짐 → 계속 정지 ⭐
4. GREEN sign 감지 → 부저 1회, 자율주행 재개 ✅
```

### 시나리오 2: RED sign만 감지

```
1. 자율주행 중
2. RED sign 감지 → 부저 1회, 정지
3. RED sign 사라짐 → 계속 정지 ⭐
4. GREEN sign 감지 안 됨 → 계속 정지 (안전) ✅
```

### 시나리오 3: GREEN sign 단독 감지

```
1. 자율주행 중
2. GREEN sign 감지 → 무시 (정지 상태가 아니므로)
3. 계속 자율주행 ✅
```

---

## 🔧 디버그 메시지

### RED sign 감지 시

```
==================================================
🔴 RED LIGHT DETECTED!
   ⏸️  Motor STOPPED
   ⏳ Waiting for GREEN light...
   ⭐ This state persists even if RED sign disappears
==================================================
🔊 Beep played for RED light (1 time only)
```

### RED sign 사라진 후

```
⏸️  Motor STOPPED (waiting for GREEN sign)
   ⭐ RED sign disappeared, but STOP state persists
```

### GREEN sign 감지 시

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

---

## ⚠️ 주의사항

### 1. Haar Cascade XML 파일

신호등 감지를 위한 XML 파일이 필요합니다:

```bash
04_cascade/xml/
├── stop.xml       # RED sign (빨간 정지 표지판)
└── no_drive.xml   # GREEN sign (초록 통행 가능 표지판)
```

**참고**: 현재 코드는 `stop.xml`과 `no_drive.xml`을 사용하도록 설정됨

### 2. 테스트 시나리오

반드시 다음 시나리오로 테스트:

1. ✅ RED sign → 정지 → GREEN sign → 재개
2. ✅ RED sign → 사라짐 → 계속 정지 → GREEN sign → 재개
3. ✅ GREEN sign 단독 → 무시 → 계속 주행

### 3. 강제 해제

정지 상태에서 벗어나는 방법:
- **방법 1**: GREEN sign 보여주기 ✅
- **방법 2**: 프로그램 재시작
- **방법 3**: 코드 수정 (비추천)

---

## 📈 성능 지표

| 항목 | 값 |
|------|-----|
| FPS | 10~20 (Raspberry Pi 기준) |
| 부저 시간 | 0.1초 (최소화) |
| 프레임 지연 | 0.01초 (10ms) |
| 감지 정확도 | Haar Cascade 의존 |
| 반응 시간 | 즉시 (1프레임 내) |

---

## 🎯 향후 개선 사항

### 1. 타이머 추가

RED sign 후 일정 시간 지나면 자동 해제:

```python
red_light_start_time = time.time()

if waiting_for_green:
    elapsed = time.time() - red_light_start_time
    if elapsed > 30:  # 30초 후 자동 해제
        waiting_for_green = False
```

### 2. 카운트다운 표시

```python
remaining = 30 - elapsed
cv2.putText(frame, f"Wait: {remaining:.0f}s", ...)
```

### 3. 수동 해제 키

```python
# 'r' 키로 강제 리셋
if key == ord('r'):
    waiting_for_green = False
    print("Manual reset")
```

---

## 📝 요약

### 가장 중요한 변경사항

1. ⭐ **RED sign 사라짐 ≠ 정지 해제**
2. ⭐ **GREEN sign만이 정지 해제 가능**
3. ⭐ **안전 우선: 확실히 멈추고, 확실히 출발**

### 핵심 원칙

```
🔴 RED sign   → 정지 상태 LOCK
🟢 GREEN sign → 정지 상태 UNLOCK
```

### 설계 철학

```
안전 > 편의
명확성 > 복잡성
```

---

**이 변경으로 더 안전하고 명확한 신호등 제어 시스템이 완성되었습니다!** 🚦✨
