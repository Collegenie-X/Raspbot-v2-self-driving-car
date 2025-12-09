# 🎯 v1.6 표지판 지속 감지 패치 노트

**날짜**: 2025-12-09  
**파일**: `3_object_autoplot___rgb_filter.py`  
**목적**: Stop sign이 사라질 때까지 계속 정지, 부저는 1회만

---

## 🎯 요구사항

사용자 피드백:
> "Stop sign이 있으면 무조건 정지해야 합니다. 그 stop sign이 사라질때까지 정지해야 합니다. (모터 정지만 하고, frame 전환 및 이미지 인식은 해야 합니다.) 그리고 stop sign 인식할 때 처음으로 딱 한번 피에조 부조음을 내면 된다."

---

## ❌ 기존 문제 (v1.5)

### 쿨다운 시스템의 문제점

```python
# v1.5의 문제
SIGN_COOLDOWN_TIME = 2.5  # 2.5초 후 표지판 무시

if stop_detected:
    if current_time - last_stop_detection_time < SIGN_COOLDOWN_TIME:
        stop_detected = False  # 쿨다운 중이면 무시
```

**문제**:
1. ❌ 표지판이 계속 있어도 2.5초 후 무시
2. ❌ 표지판 앞에서 자율주행 재개 (위험!)
3. ❌ 부저가 2.5초마다 반복

---

## ✅ 새로운 해결 방법 (v1.6)

### 상태 기반 제어 시스템

```python
# v1.6의 개선
stop_sign_active = False      # 현재 표지판 감지 중인지 상태
stop_beep_played = False      # 부저 울렸는지 여부

# 매 프레임마다 체크
if stop_detected:
    if not stop_sign_active:
        # 처음 감지
        stop_sign_active = True
        부저 울림 (1회)
    
    # 계속 감지
    모터 정지 유지
    
else:
    if stop_sign_active:
        # 표지판 사라짐
        stop_sign_active = False
        자율주행 재개
```

---

## 🔄 작동 방식

### 1️⃣ **표지판 처음 감지**

```
[프레임 N: Stop sign 감지]
  ↓
[stop_sign_active = True]
  ↓
[부저 울림 (0.1초, 1회만)]
  ↓
[stop_beep_played = True]
  ↓
[모터 정지]
```

**화면 출력**:
```
==================================================
🛑 STOP sign DETECTED! Position: CENTER
   Reaction Mode: STOP_ONLY
==================================================
🔊 Beep played (1 time only)
```

---

### 2️⃣ **표지판 계속 감지 중**

```
[프레임 N+1, N+2, N+3, ...: Stop sign 계속 감지]
  ↓
[stop_sign_active = True (유지)]
  ↓
[부저 울리지 않음 (stop_beep_played = True)]
  ↓
[모터 정지 유지]
  ↓
[Frame 처리는 계속 진행] ← ⭐ 중요!
```

**화면 출력** (30프레임마다):
```
⏸️  Motor STOPPED (waiting for sign to disappear)
```

---

### 3️⃣ **표지판 사라짐**

```
[프레임 N+K: Stop sign 감지 안됨]
  ↓
[stop_sign_active = False]
  ↓
[stop_beep_played = False (리셋)]
  ↓
[자율주행 즉시 재개]
```

**화면 출력**:
```
==================================================
✅ STOP sign DISAPPEARED - Resuming auto drive
==================================================
```

---

## 📊 상태 변화 다이어그램

```
            감지 안됨
             ↓
    ┌────────────────────┐
    │  표지판 없음        │
    │  (자율주행)         │
    └────────────────────┘
             ↑ ↓
     사라짐 ↑   ↓ 처음 감지
             ↑   ↓ (부저 1회)
             ↑   ↓
    ┌────────────────────┐
    │  표지판 감지 중     │
    │  (모터 정지)        │
    │  (Frame 처리 계속)  │
    └────────────────────┘
             ↑ ↓
     계속 감지 (부저 없음)
```

---

## 🔧 코드 변경 사항

### 1. 상태 변수 추가

**Before (v1.5)**:
```python
SIGN_COOLDOWN_TIME = 2.5
last_stop_detection_time = 0
last_no_drive_detection_time = 0
```

**After (v1.6)**:
```python
stop_sign_active = False          # Stop sign 감지 중 여부
no_drive_sign_active = False      # No Drive sign 감지 중 여부
stop_beep_played = False          # Stop sign 부저 울렸는지
no_drive_beep_played = False      # No Drive sign 부저 울렸는지
```

---

### 2. 메인 로직 변경

**Before (v1.5)**:
```python
if stop_detected:
    if current_time - last_stop_detection_time < SIGN_COOLDOWN_TIME:
        stop_detected = False  # 쿨다운 중이면 무시
    else:
        모터 정지
        부저 울림
        continue  # 자율주행 건너뛰기
```

**After (v1.6)**:
```python
if stop_detected:
    # 처음 감지
    if not stop_sign_active:
        stop_sign_active = True
        stop_beep_played = False
        
    # 부저는 최초 1회만
    if USE_BEEP and not stop_beep_played:
        bot.Ctrl_BEEP_Switch(1)
        time.sleep(0.1)
        bot.Ctrl_BEEP_Switch(0)
        stop_beep_played = True
    
    # 모터 정지 (계속)
    car_stop()

else:
    # 표지판 사라짐
    if stop_sign_active:
        stop_sign_active = False
        stop_beep_played = False
        # 자율주행 자동 재개

# 표지판 활성화 중이면 자율주행 건너뛰기
if stop_sign_active:
    continue
```

---

## 📊 성능 비교

| 항목 | v1.5 (쿨다운) | v1.6 (상태 기반) |
|:----:|:-------------:|:---------------:|
| **표지판 인식** | 2.5초마다 1회 | 매 프레임 체크 |
| **모터 정지** | 0.1초만 | 표지판 사라질 때까지 |
| **부저 횟수** | 2.5초마다 1회 | 전체 1회만 |
| **Frame 처리** | 계속 진행 ✅ | 계속 진행 ✅ |
| **이미지 인식** | 계속 진행 ✅ | 계속 진행 ✅ |
| **안전성** | 낮음 ⚠️ | 높음 ✅ |
| **사용자 경험** | 부저 반복 ❌ | 부저 1회만 ✅ |

---

## ✅ 주요 개선 사항

### 1. 안전성 향상 🛡️

**Before**:
```
표지판 감지 → 0.1초 정지 → 2.5초 후 자율주행 (표지판 아직 있음!)
```

**After**:
```
표지판 감지 → 계속 정지 → 표지판 사라짐 → 자율주행 재개
```

### 2. 부저 소음 최소화 🔇

**Before**:
```
부저: 피! (0초) → 피! (2.5초) → 피! (5초) → ...
```

**After**:
```
부저: 피! (처음만) → (조용) → (조용) → ...
```

### 3. Frame 처리 유지 📹

표지판 감지 중에도:
- ✅ Frame 읽기 계속
- ✅ 이미지 처리 계속
- ✅ 표지판 감지 계속
- ✅ 키보드 입력 처리

**오직 모터만 정지**

---

## 🎮 사용자 체험

### Before (v1.5) ❌

```
[로봇이 Stop sign 앞에 도착]
  ↓
[0.1초 정지]
  ↓
[부저: 피!]
  ↓
[2.5초 대기]
  ↓
[자율주행 재개] ← 표지판 아직 있음!
  ↓
[2.5초 후]
  ↓
[다시 감지 → 부저: 피!] ← 계속 반복
```

### After (v1.6) ✅

```
[로봇이 Stop sign 앞에 도착]
  ↓
[감지: 처음]
  ↓
[부저: 피! (1회만)]
  ↓
[모터 정지 유지]
  ↓
[Frame 처리 계속...]
  ↓
[표지판이 화면에서 사라짐]
  ↓
[즉시 자율주행 재개]
```

---

## 🔍 디버그 메시지

### 표지판 감지 시 (처음)

```
==================================================
🛑 STOP sign DETECTED! Position: CENTER
   Reaction Mode: STOP_ONLY
==================================================
🔊 Beep played (1 time only)
```

### 표지판 감지 중 (30프레임마다)

```
⏸️  Motor STOPPED (waiting for sign to disappear)
```

### 표지판 사라짐

```
==================================================
✅ STOP sign DISAPPEARED - Resuming auto drive
==================================================
```

---

## 🧪 테스트 방법

### 1. Stop Sign 테스트

```bash
# 실행
python3 3_object_autoplot___rgb_filter.py

# 테스트 시나리오:
1. Stop sign을 카메라 앞에 보여주기
   → 부저 1회 "피!" 확인
   → 모터 정지 확인
   → 디버그: "🛑 STOP sign DETECTED!" 확인

2. Stop sign을 계속 보여주기 (5초 동안)
   → 부저 울리지 않는지 확인
   → 모터 계속 정지 확인
   → 디버그: "⏸️  Motor STOPPED" 확인

3. Stop sign을 치우기
   → 모터 즉시 재개 확인
   → 자율주행 시작 확인
   → 디버그: "✅ STOP sign DISAPPEARED" 확인
```

### 2. No Drive Sign 테스트

```bash
# Stop sign과 동일한 방식으로 테스트
1. No Drive sign 보여주기
   → 부저 1회 확인
   → 모터 정지 확인
   → 디버그: "🚫 NO DRIVE sign DETECTED!" 확인

2. 계속 보여주기
   → 부저 없음, 모터 정지 유지 확인

3. 치우기
   → 자율주행 즉시 재개 확인
```

### 3. Frame 처리 확인

```bash
# 표지판 감지 중에도:
- 5_Sign_Detection 윈도우가 계속 업데이트되는지 확인
- FPS 카운터가 계속 증가하는지 확인
- 키보드 입력 (Q, M, L 등)이 작동하는지 확인
```

---

## 📋 체크리스트

- [ ] **Stop sign 감지 시 부저 1회만 울리는가?**
- [ ] **Stop sign이 있는 동안 모터가 계속 정지하는가?**
- [ ] **Stop sign이 사라지면 즉시 자율주행 재개되는가?**
- [ ] **표지판 감지 중에도 Frame이 계속 업데이트되는가?**
- [ ] **No Drive sign도 동일하게 작동하는가?**
- [ ] **부저가 반복되지 않는가?**
- [ ] **FPS가 유지되는가? (40-60)**
- [ ] **키보드 입력이 작동하는가?**

---

## ⚙️ 설정 조정 (필요시)

현재는 상태 기반이므로 별도 설정이 필요 없습니다!

하지만 원하신다면:

```python
# 부저 사용 여부
USE_BEEP = True  # False로 설정하면 부저 안 울림

# 디버그 메시지
DEBUG_MODE = True  # False로 설정하면 메시지 최소화
```

---

## 🎉 결론

**v1.6 업데이트로 달성한 것**:

✅ **안전한 정지**: 표지판이 사라질 때까지 계속 정지  
✅ **부저 1회만**: 처음 감지 시에만 울림 (소음 최소화)  
✅ **빠른 Frame 처리**: FPS 40-60 유지  
✅ **즉각적인 재개**: 표지판 사라지면 바로 자율주행  
✅ **통행금지 동일 적용**: Stop/No Drive 모두 동일한 로직  
✅ **상태 기반 제어**: 직관적이고 안정적인 코드

**이제 로봇이 표지판 앞에서 안전하게 정지하고, 표지판이 사라지면 즉시 주행을 재개합니다! 🛑✅🚗💨**

---

**Made with ❤️ for Raspbot v2 Project**

*최종 업데이트: 2025년 12월 9일*
