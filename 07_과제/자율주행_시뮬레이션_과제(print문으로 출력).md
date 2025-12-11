# Raspbot v2 자율주행 시뮬레이션 과제

## 📋 과제 개요

**목표**: **Raspbot 자율주행 시스템의 가상 시뮬레이션(Print문 로그)**을 설계하여 단순하게 print문으로 출력하여, 실제 개발에 참고하기 위함입니다. 
         가상환경을 만들고, 여기에서 조건에 따른 제어를 print문으로 출력하면 됩니다. 

**💡 이 과제는 간단합니다!**
- 복잡한 계산이나 수학 공식 **없습니다**
- ** Python에서 random + 조건문 + print문**만 사용하면 됩니다
- 각 TODO는 10~20줄 정도로 짧게 작성하세요

**문제 정의**:
1. 1장의 카메라 이미지(1 Frame)에서 다양한 상황을 인식하고 즉시 제어 결정
2. random으로 무작위 상황 생성, 조건문으로 논리적 대응 알고리즘 설계
3. print문으로 전체 과정을 가상으로 시뮬레이션하여 로그(print) 출력

**핵심 방식**:
- 각 TODO에서 **인식 → 즉시 제어 결정** (제어 시스템 따로 분리 없음)
- 인식 결과에 따라 기어모터, 서보모터, 부저 제어를 바로 출력
- 20 Frames 반복하여 다양한 상황 시뮬레이션

**제출 방법 안내**

- **제출 파일**: Python 코드 파일 1개 (`.py` 형식)
- **파일명 예시**: `이름_학번_autoplot_simulation_학번.py`  
  (예: 홍길동_1234567_autoplot_simulation.py)
- **이메일 제출처**: jpdarrencompany@gmail.com
- **제출 마감일**: 다음주 월요일(15일) 18:00까지 반드시 제출  
  (기한 엄수, 늦은 제출 불가)
- **이메일 제목 양식**:  
  `[가천대학교-p학기제] - 자율주행시뮬레이션 과제 제출 (학번:XXXXXXX, 이름:XXXXXX)`

**유의사항**
- 반드시 위 파일명, 이메일 제목 형식을 지켜서 제출하세요.
- 주석/함수/코드 가독성 등 채점 기준표 확인 필수.

** 📊 실행 결과 예시 (print문으로 출력)** 

```
############################################################
🚗 Frame 1/20
############################################################

============================================================
📸 카메라 이미지 촬영 (1 Frame)
============================================================

[TODO 1] 차선 인식 & 제어
  📸 인식 결과: center
  ⚙️ 기어모터: 직진 전진

[TODO 2] 신호등 인식 & 제어
  📸 인식 결과: green
  ⚙️ 기어모터: 전진

[TODO 3] 표지판 인식 & 제어
  📸 인식 결과: stop
  ⚙️ 기어모터: 정지
  🔊 부저: 삐익-

[TODO 4] 주차공간 인식 & 제어
  📸 인식 결과 (위치): center
  📸 인식 결과 (크기): big
  ✅ 주차 가능! 가까움
  ⚙️ 기어모터: 후진 주차

[TODO 5] 장애물 인식 & 제어
  📸 인식 결과: far
  ✅ 안전거리
  ⚙️ 기어모터: 직진 전진

============================================================
✅ 1 Frame 처리 완료
============================================================


############################################################
🚗 Frame 2/20
############################################################
      :
      :
      :

```


---

## 🎯 1 Frame 처리 개념

| 단계 | 내용 | 설명 |
|------|------|------|
| 1️⃣ 이미지 촬영 | 카메라로 JPEG 1장 촬영 | 1 Frame = 1장의 이미지 |
| 2️⃣ 인식 + 제어 | 1장에서 모든 인식 & 즉시 제어 | TODO 1~5: 인식 → 바로 제어 명령 |
| 🔄 반복 | 다음 Frame으로 | 계속 반복 = 자율주행 |

---

## 📝 TODO 구현 항목 (총 5개)

### 각 TODO: 인식 → 즉시 제어 결정 & 출력

| TODO | 기능 | random 생성 | 조건문 | 출력 내용 |
|------|------|------------|--------|-----------|
| **1** | 차선 인식 & 제어 | "left", "center", "right", "fail" | 위치별 조향 결정 | 차선 위치 → 기어모터 방향 제어 |
| **2** | 신호등 인식 & 제어 | "red", "yellow", "green", "fail" | 신호별 행동 결정 | 신호등 색상 → 기어모터 속도 + 부저음 |
| **3** | 표지판 인식 & 제어 | "stop", "fail" | 표지판별 행동 | 표지판 종류 → 기어모터 제어 + 부저음 |
| **4** | 주차공간 인식 & 제어 | "left", "center", "right", "fail" | 위치/크기별 주차 동작 | 주차 위치 → 기어모터 주차 제어 (간단!) |
| **5** | 장애물 인식 & 제어 | "near", "far", "fail" | 거리별 회피 결정 | 장애물 거리 → 기어모터 회피 + 부저 경고 |

---

## 💻 전체 코드 구조 형식 

```python
import random

# ===== TODO 1: 차선 인식 & 제어 =====
def lane_detection_and_control():
    """차선 인식 → 즉시 기어모터 제어"""
    print("\n[TODO 1] 차선 인식 & 제어")
    
    # 1. 차선 인식 (random으로 시뮬레이션)
    lane_positions = ["left", "center", "right", "fail"]
    detected = random.choice(lane_positions)
    print(f"  📸 인식 결과: {detected}")
    
    # 2. 조건문으로 제어 결정
    if detected == "left":
        print(f"  ⚙️ 기어모터: 우회전 전진")
    elif detected == "center":
        print(f"  ⚙️ 기어모터: 직진 전진")
    elif detected == "right":
        print(f"  ⚙️ 기어모터: 좌회전 전진")
    else:  # fail
        print(f"  ⚠️ 인식 실패")
        print(f"  ⚙️ 기어모터: 감속")




# ===== TODO 2: 신호등 인식 & 제어 =====
def traffic_light_detection_and_control():
    """신호등 인식 → 즉시 기어모터 제어"""
    print("\n[TODO 2] 신호등 인식 & 제어")
    
    # 1. 신호등 인식 (random으로 시뮬레이션)
    traffic_lights = ["red", "yellow", "green", "fail"]
    detected = random.choice(traffic_lights)
    print(f"  📸 인식 결과: {detected}")
    
    # 2. 조건문으로 제어 결정
    if detected == "red":
        print(f"  ⚙️ 기어모터: 정지")
        print(f"  🔊 부저: 삐-")
            :
            :

# ======= TODO 3: 표지판 인식 & 제어 
def traffic_sign_detection_and_control() :
  pass


# ===== TODO 4: 주차공간 인식 & 제어 =====
def parking_detection_and_control():
    """주차공간(O 표시) 인식 → 즉시 주차 제어"""
    print("\n[TODO 4] 주차공간 인식 & 제어")
    
    # 1. O 표시 위치 인식 (random으로 시뮬레이션)
    parking_positions = ["left", "center", "right", "fail"]
    detected_position = random.choice(parking_positions)
    print(f"  📸 인식 결과 (위치): {detected_position}")
    
    # 2. 조건문으로 제어 결정
    if detected_position == "left":
        print(f"  ⚙️ 기어모터: 좌회전")
    elif detected_position == "center":
        # 중앙에 있으면 크기(거리) 확인
        parking_sizes = ["big", "small"]
        detected_size = random.choice(parking_sizes)
        print(f"  📸 인식 결과 (크기): {detected_size}")
        
        if detected_size == "big":
            print(f"  ✅ 주차 가능! 가까움")
            print(f"  ⚙️ 기어모터: 후진 주차")
        else:  # small
            print(f"  🚗 더 접근 필요")
            print(f"  ⚙️ 기어모터: 직진 전진")
    elif detected_position == "right":
        print(f"  ⚙️ 기어모터: 우회전")
    else:  # fail
        print(f"  ⚠️ 인식 실패")
        print(f"  ⚙️ 기어모터: 전진 탐색")



# ===== TODO 5: 장애물 인식 & 제어 =====
def obstacle_detection_and_control():
    """장애물 인식 → 즉시 회피 제어"""
    print("\n[TODO 5] 장애물 인식 & 제어")
    
    # 1. 장애물 거리 인식 (random으로 시뮬레이션)
    obstacle_distances = ["near", "far", "fail"]
    detected = random.choice(obstacle_distances)
    print(f"  📸 인식 결과: {detected}")
    
    # 2. 조건문으로 제어 결정
    if detected == "near":
        print(f"  ⚠️ 위험! 회피 필요")
        print(f"  ⚙️ 기어모터: 좌회전 회피")
        print(f"  🔊 부저: 삐삐- (경고)")
          :
          :
          :
      
# ===== 1 Frame 처리 =====
def process_one_frame():
    """1장의 이미지 처리: 5개 TODO 순차 실행"""
    print("\n" + "="*60)
    print("📸 카메라 이미지 촬영 (1 Frame)")
    print("="*60)
    
    # 각 TODO 실행: 인식 → 즉시 제어
    lane_detection_and_control()
    traffic_light_detection_and_control()
    traffic_sign_detection_and_control()
    parking_detection_and_control()
    obstacle_detection_and_control()
    
    print("\n" + "="*60)
    print("✅ 1 Frame 처리 완료")
    print("="*60)

# ===== 20 Frames 반복 실행 =====
def run_autonomous_driving():
    """20 Frames 자동 반복"""
    frame = 0
    while frame < 20:
        print(f"\n\n{'#'*60}")
        print(f"🚗 Frame {frame + 1}/20")
        print(f"{'#'*60}")
        process_one_frame()
        frame += 1
    
    print(f"\n\n{'🎉'*20}")
    print("✅ 자율주행 시뮬레이션 완료! (총 20 Frames)")
    print(f"{'🎉'*20}")

if __name__ == "__main__":
    run_autonomous_driving()

---



---

## ✅ 평가 기준

| 항목 | 배점 | 세부 내역 |
|------|------|-----------|
| TODO 1~5 구현 | 50점 | 각 TODO 10점 (인식+제어+random+조건문+print) |
| 인식→제어 즉시 처리 | 20점 | 각 TODO에서 인식 후 바로 제어 출력 |
| 20 Frames 반복 | 15점 | while/for문, Frame 번호 표시 |
| 1 Frame 개념 이해 | 10점 | 1장 이미지에서 TODO 1~5 모두 처리 |
| 코드 가독성 | 5점 | 함수 분리, 주석, 변수명 명확성 |

**총점**: 100점

---

## 📤 제출 방법

| 항목 | 내용 |
|------|------|
| 파일명 | `학번_이름_자율주행시뮬레이션.py` |
| 실행 조건 | 20 Frames 자동 반복 실행 |
| 제출처 | jpdarrencompany@gmail.com |
| 제출 기한 | 12월 15일 월요일 18:00 까지 |

---

## ❓ FAQ

| 질문 | 답변 |
|------|------|
| 1 Frame이 뭔가요? | 카메라가 촬영한 1장의 이미지 |
| TODO 개수는? | 총 5개 (차선, 신호등, 표지판, 주차, 장애물) |
| 제어를 따로 구현하나요? | 아니요! 각 TODO에서 인식 후 바로 제어 출력 |
| 복잡한 계산이 필요한가요? | 아니요! random + 조건문만 사용하면 됩니다 |
| random은 어디에 사용? | 인식 결과 생성 (다양한 상황 시뮬레이션) |
| 실제 카메라가 필요한가요? | 아니요. random + print문으로 시뮬레이션만 |
| 왜 20 Frames인가? | 다양한 상황 시뮬레이션 + 알고리즘 검증 |

---

## 🎯 핵심 요약

```
1 Frame = 1장 이미지 처리
  ├─ TODO 1: 차선 인식 → 기어모터 제어
  ├─ TODO 2: 신호등 인식 → 기어모터/부저 제어
  ├─ TODO 3: 표지판 인식 → 기어모터/부저 제어
  ├─ TODO 4: 주차공간 인식 → 기어모터 주차 제어
  └─ TODO 5: 장애물 인식 → 기어모터/부저 제어
      ↓
  (위 과정을 20회 반복)
```

**이 과제의 핵심**:
1. **random**으로 상황 생성 → **조건문**으로 제어 결정 → **print**로 출력
2. 복잡한 계산 없이 **간단한 if문**만 사용하면 됩니다!
3. 각 TODO는 10~20줄 정도로 짧게 작성하세요

---

**행운을 빕니다! 🚗💨**
