# Raspbot v2 자율주행 시스템 설명서

## 📚 목차
1. [시스템 개요](#시스템-개요)
2. [해상도 문제 해결](#해상도-문제-해결)
3. [단계별 동작 설명](#단계별-동작-설명)
4. [트랙바 설정 가이드](#트랙바-설정-가이드)
5. [문제 해결](#문제-해결)

---

## 🎯 시스템 개요

### 주요 기능
- **라인 트레이싱**: 흰색(또는 검은색) 라인을 따라 자율 주행
- **실시간 비전 처리**: OpenCV를 사용한 이미지 처리
- **히스토그램 분석**: 좌우 영역 분석으로 방향 결정
- **제자리 회전**: 정밀한 좌우 회전 가능
- **막다른 길 감지**: 대체 경로 자동 탐색

### 하드웨어 구성
- **카메라**: USB 웹캠 (해상도 자동 감지)
- **모터**: 4개 (M1~M4, 좌우 독립 제어)
- **서보**: 2개 (카메라 좌우/상하 각도 조절)
- **LED**: RGB LED (상태 표시)
- **부저**: 소리 피드백

---

## 🔧 해상도 문제 해결

### 문제 상황
```
요청 해상도: 320x240
실제 해상도: 640x480 (또는 다른 해상도)
```

### 해결 방법 (v2.1에서 자동 처리)

#### 1. **실제 해상도 자동 감지** (123-126번 라인)
```python
actual_height, actual_width = frame.shape[:2]
ACTUAL_WIDTH = actual_width
ACTUAL_HEIGHT = actual_height
```
- 카메라에서 첫 프레임을 읽어 실제 해상도를 확인
- 전역 변수에 저장하여 전체 코드에서 사용

#### 2. **원근 변환 좌표 동적 계산** (267-279번 라인)
```python
# 실제 해상도 가져오기
actual_h, actual_w = frame.shape[:2]

# 원근 변환 영역 정의 (실제 해상도 기반)
pts_src = np.float32([
    [margin, actual_h - y_value],  # 좌하
    [actual_w - margin, actual_h - y_value],  # 우하
    [actual_w - margin, y_value],  # 우상
    [margin, y_value],  # 좌상
])
```

**이전 코드 (고정 좌표):**
```python
pts_src = np.float32([
    [10, 70 + y_value],   # 320x240 기준 (고정)
    [310, 70 + y_value],
    [310, 10 + y_value],
    [10, 10 + y_value],
])
```

**개선된 코드 (동적 좌표):**
- `actual_w`, `actual_h`: 실제 카메라 해상도 사용
- `y_value`: 트랙바로 ROI 영역의 세로 위치 조절
- **결과**: 어떤 해상도에서도 자동으로 적용됨

#### 3. **Y Value 트랙바 개선** (199번 라인)
```python
# 이전: cv2.createTrackbar("Y Value", "Camera Settings", 10, 160, nothing)
# 개선: 범위 확장 및 기본값 조정
cv2.createTrackbar("Y Value", "Camera Settings", 50, 200, nothing)
```
- **기본값**: 10 → 50 (상단 영역 포함)
- **최대값**: 160 → 200 (더 넓은 조절 범위)

---

## 📊 단계별 동작 설명

### 전체 흐름도
```
┌─────────────────────────────────────────────────┐
│ 1. 초기화                                        │
│    - 하드웨어 초기화                             │
│    - 카메라 설정                                 │
│    - 트랙바 생성                                 │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│ 2. 메인 루프 (무한 반복)                         │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│ 3. 프레임 캡처                                   │
│    ret, frame = cap.read()                      │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│ 4. 이미지 처리 (process_frame)                   │
│    ├─ 원근 변환 (ROI 영역 추출)                  │
│    ├─ 그레이스케일 변환 (RGB 가중치)             │
│    ├─ 이진화 (흰색 라인 검출)                    │
│    └─ 노이즈 제거 (모폴로지)                     │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│ 5. 히스토그램 분석                               │
│    histogram = np.sum(processed_frame, axis=0)  │
│    (세로 방향으로 합산 → 가로 분포 계산)          │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│ 6. 방향 결정 (decide_direction)                 │
│    ├─ 좌우 영역 비교                             │
│    ├─ 중앙 영역 분석                             │
│    └─ 방향 출력 (UP/LEFT/RIGHT)                  │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│ 7. 차량 제어 (control_car)                      │
│    ├─ UP: 직진 (속도 부스트)                     │
│    ├─ LEFT: 좌회전 (제자리 회전)                 │
│    └─ RIGHT: 우회전 (제자리 회전)                │
└────────────┬────────────────────────────────────┘
             │
             ▼
        2번으로 돌아감
```

---

### 단계별 상세 설명

#### **1단계: 초기화** (73-227번 라인)

##### 1-1. 하드웨어 초기화
```python
bot = Raspbot()  # Raspbot 객체 생성
```
- 모터, 서보, LED, 부저 등 초기화

##### 1-2. 카메라 설정
```python
cap = cv2.VideoCapture(0)  # USB 카메라 열기
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
cap.set(cv2.CAP_PROP_BRIGHTNESS, 0)
cap.set(cv2.CAP_PROP_CONTRAST, 40)
```

**중요**: 실제 해상도 확인
```python
actual_height, actual_width = frame.shape[:2]
print(f"실제 해상도: {actual_width}x{actual_height}")
```

##### 1-3. 트랙바 생성
```python
cv2.createTrackbar("Y Value", "Camera Settings", 50, 200, nothing)
cv2.createTrackbar("Detect Value", "Camera Settings", 120, 150, nothing)
cv2.createTrackbar("Motor Up Speed", "Camera Settings", 20, 255, nothing)
# ... 기타 트랙바
```

---

#### **2단계: 프레임 캡처** (540-543번 라인)

```python
ret, frame = cap.read()
if not ret:
    print("❌ 카메라에서 프레임을 읽을 수 없습니다.")
    break
```

- 카메라에서 실시간으로 프레임 읽기
- `ret`: 성공 여부 (True/False)
- `frame`: BGR 이미지 (실제 해상도)

---

#### **3단계: 이미지 처리** (process_frame 함수, 261-315번 라인)

##### 3-1. 원근 변환 (Perspective Transform)

**목적**: 카메라 각도로 인한 왜곡을 보정하여 정면 뷰로 변환

```python
# ROI 영역 정의 (실제 해상도 기반)
pts_src = np.float32([
    [margin, actual_h - y_value],  # 좌하
    [actual_w - margin, actual_h - y_value],  # 우하
    [actual_w - margin, y_value],  # 우상 (상단 포함!)
    [margin, y_value],  # 좌상
])

# 목표 해상도 (320x240 고정)
pts_dst = np.float32([[0, 240], [320, 240], [320, 0], [0, 0]])

# 변환 행렬 계산 및 적용
mat_affine = cv2.getPerspectiveTransform(pts_src, pts_dst)
frame_transformed = cv2.warpPerspective(frame, mat_affine, (320, 240))
```

**시각적 이해:**
```
원본 프레임 (실제 해상도: 640x480)
┌────────────────────────┐
│                        │  ← 카메라 시야
│   ┌──────────┐         │
│   │   ROI    │         │  ← 녹색 사각형 (관심 영역)
│   │  (상단   │         │     y_value로 위치 조절
│   │   포함)  │         │
│   └──────────┘         │
│                        │
└────────────────────────┘
        ↓ 원근 변환
변환된 프레임 (320x240)
┌──────────────┐
│              │
│   정면 뷰    │  ← 위에서 내려다본 것처럼 보임
│              │
│              │
└──────────────┘
```

##### 3-2. 그레이스케일 변환 (weighted_gray 함수)

```python
gray_frame = weighted_gray(frame_transformed, r_weight, g_weight, b_weight)
```

**RGB 가중치 적용 방식:**
```python
result = R채널 × r_weight + G채널 × g_weight + B채널 × b_weight
```

**사용 예시:**
- **밝은 환경 (흰색 라인)**: R=30, G=40, B=60 (파랑 강조)
- **어두운 환경**: R=60, G=40, B=30 (빨강 강조)

##### 3-3. 이진화 (Binarization)

```python
_, binary_frame = cv2.threshold(gray_frame, detect_value, 255, cv2.THRESH_BINARY)
```

**동작:**
- `detect_value`보다 밝은 픽셀 → 255 (흰색)
- `detect_value`보다 어두운 픽셀 → 0 (검은색)

**시각적 예시:**
```
그레이스케일                이진화 (detect_value=120)
┌────────────┐             ┌────────────┐
│ 150 130 80 │             │ 255 255  0 │
│ 200 180 90 │  ────────▶  │ 255 255  0 │
│  70  60 50 │             │   0   0  0 │
└────────────┘             └────────────┘
```

##### 3-4. 노이즈 제거 (Morphology)

```python
kernel = np.ones((5, 5), np.uint8)
binary_frame = cv2.morphologyEx(binary_frame, cv2.MORPH_CLOSE, kernel)
binary_frame = cv2.morphologyEx(binary_frame, cv2.MORPH_OPEN, kernel)
```

- **MORPH_CLOSE**: 작은 구멍 메우기
- **MORPH_OPEN**: 작은 노이즈 제거

---

#### **4단계: 히스토그램 분석** (553번 라인)

```python
histogram = np.sum(processed_frame, axis=0)
```

**의미:**
- 세로 방향(axis=0)으로 픽셀 값을 모두 합산
- 결과: 가로 방향의 흰색 픽셀 분포

**시각적 예시:**
```
이진화된 이미지 (320x240)
┌─────────────────────────┐
│        255              │  ▲
│    255  255  255        │  │ 세로 방향으로
│  255    255    255      │  │ 합산
│    255  255  255        │  │
│        255              │  ▼
└─────────────────────────┘
           ↓
히스토그램 (320개 값)
  값
   │     ████
   │   ██████████
   │ ████████████████
   └────────────────▶ 위치 (0~320)
   왼쪽    중앙    오른쪽
```

---

#### **5단계: 방향 결정** (decide_direction 함수, 373-436번 라인)

##### 5-1. 히스토그램 6구역 분할

```python
DIVIDE = 6
left = int(np.sum(histogram[: length // DIVIDE]))  # 0 ~ 1/6
right = int(np.sum(histogram[(DIVIDE - 1) * length // DIVIDE :]))  # 5/6 ~ 1
center_left = int(np.sum(histogram[1 * length // DIVIDE : 3 * length // DIVIDE]))  # 1/6 ~ 3/6
center_right = int(np.sum(histogram[3 * length // DIVIDE : 5 * length // DIVIDE]))  # 3/6 ~ 5/6
```

**구역 분할:**
```
┌────┬────┬────┬────┬────┬────┐
│    │    │    │    │    │    │
│ L  │ CL │ CL │ CR │ CR │ R  │
│    │    │    │    │    │    │
└────┴────┴────┴────┴────┴────┘
  0   1/6  2/6  3/6  4/6  5/6  1
  
L: left (왼쪽 끝)
CL: center_left (중앙 좌측)
CR: center_right (중앙 우측)
R: right (오른쪽 끝)
```

##### 5-2. 좌우 회전 판단

```python
if abs(right - left) > direction_threshold:
    direction = "LEFT" if right > left else "RIGHT"
    return direction
```

**판단 로직:**
```
상황 1: 오른쪽에 라인이 많음
  left=10000, right=50000
  → right > left
  → 왼쪽으로 회전 (LEFT)

상황 2: 왼쪽에 라인이 많음
  left=50000, right=10000
  → left > right
  → 오른쪽으로 회전 (RIGHT)

상황 3: 좌우 균형
  left=30000, right=32000
  → abs(right - left) < threshold
  → 직진 (UP)
```

##### 5-3. 막다른 길 감지

```python
center_diff = abs(center_left - center_right)

if center_diff < up_threshold:
    # 중앙 영역에 라인이 거의 없음 → 막다른 길
    return rotate_servo_and_check_direction(...)
```

**동작:**
1. 차량 정지
2. 서보 모터를 180도로 회전
3. 뒤쪽 카메라 뷰 확인
4. 좌/우/중앙 영역 분석
5. 최적 방향 반환
6. 서보 모터 원위치

---

#### **6단계: 차량 제어** (control_car 함수, 494-534번 라인)

##### 6-1. 직진 (UP)

```python
if direction == "UP":
    boosted_speed = min(up_speed + SPEED_BOOST, 255)
    car_run(boosted_speed, boosted_speed)
```

**모터 동작:**
```
M1 (왼쪽 앞): +boosted_speed (전진)
M2 (왼쪽 뒤): +boosted_speed (전진)
M3 (오른쪽 앞): +boosted_speed (전진)
M4 (오른쪽 뒤): +boosted_speed (전진)

결과: ↑ 직진
```

##### 6-2. 좌회전 (LEFT)

```python
elif direction == "LEFT":
    car_left(down_speed - 10, up_speed + 10)
```

**모터 동작 (제자리 회전):**
```
M1 (왼쪽 앞): -speed (후진)
M2 (왼쪽 뒤): -speed (후진)
M3 (오른쪽 앞): +speed (전진)
M4 (오른쪽 뒤): +speed (전진)

상단 뷰:
    앞
  ←─┴─→
왼 │   │ 우
  ←─┬─→
    뒤
    
왼쪽 후진 ← │ → 오른쪽 전진
결과: ↺ 반시계 방향 회전
```

##### 6-3. 우회전 (RIGHT)

```python
elif direction == "RIGHT":
    car_right(up_speed + 10, down_speed - 10)
```

**모터 동작:**
```
M1 (왼쪽 앞): +speed (전진)
M2 (왼쪽 뒤): +speed (전진)
M3 (오른쪽 앞): -speed (후진)
M4 (오른쪽 뒤): -speed (후진)

왼쪽 전진 → │ ← 오른쪽 후진
결과: ↻ 시계 방향 회전
```

---

## 🎛️ 트랙바 설정 가이드

### 핵심 설정

#### 1. **Y Value** (ROI 영역 위치)
- **범위**: 0~200
- **기본값**: 50
- **효과**: 
  - 낮음 (0~50): 화면 하단 중심 (가까운 곳)
  - 중간 (50~100): 화면 중앙 (권장)
  - 높음 (100~200): 화면 상단 포함 (먼 곳까지 인식)

**조절 방법:**
1. 프로그램 실행
2. `1_Frame` 창에서 녹색 사각형 확인
3. Y Value를 조절하여 사각형이 라인을 포함하도록 설정
4. **목표**: 라인이 사각형 안에 들어오도록

**이미지 예시:**
```
Y Value = 50 (낮음)
┌────────────────┐
│                │
│                │  ← 상단 영역 제외
│   ┌──────┐     │
│   │ ROI  │     │  ← 하단만 인식
└───┴──────┴─────┘

Y Value = 150 (높음)
┌────────────────┐
│   ┌──────┐     │  ← 상단 영역 포함
│   │      │     │
│   │ ROI  │     │  ← 넓은 영역 인식
│   │      │     │
└───┴──────┴─────┘
```

#### 2. **Detect Value** (이진화 임계값)
- **범위**: 0~150
- **기본값**: 120
- **효과**:
  - 낮음 (50~80): 어두운 환경용
  - 중간 (80~120): 일반 환경
  - 높음 (120~150): 밝은 환경용

**조절 방법:**
1. `4_Processed Frame` 창 확인
2. 라인이 흰색(255)으로 표시되고, 배경이 검은색(0)이 되도록 조절
3. **목표**: 라인만 선명하게 흰색으로 추출

#### 3. **Motor Up Speed / Down Speed**
- **Up Speed**: 직진 및 회전 시 기본 속도
- **Down Speed**: 회전 시 감속
- **권장값**: Up=20~50, Down=10~30

#### 4. **Direction Threshold / Up Threshold**
- **Direction Threshold**: 좌우 회전 민감도
  - 높음: 큰 차이에만 회전 (안정적)
  - 낮음: 작은 차이에도 회전 (민감)
  
- **Up Threshold**: 막다른 길 감지 민감도
  - 높음: 라인이 많이 사라져야 감지
  - 낮음: 라인이 조금만 사라져도 감지

#### 5. **R/G/B Weight** (색상 가중치)
- **흰색 라인 (밝은 환경)**: R=30, G=40, B=60
- **검은색 라인 (어두운 환경)**: R=60, G=40, B=30
- **노란색 라인**: R=50, G=50, B=20

---

## 🛠️ 문제 해결

### 문제 1: "왼쪽 상단 부분을 인식하지 못해요"

**원인:**
- Y Value가 너무 낮아서 상단 영역이 ROI에 포함되지 않음

**해결:**
1. **Y Value를 높임**: 50 → 100 ~ 150
2. `1_Frame` 창에서 녹색 사각형이 상단까지 포함하는지 확인
3. 사각형이 라인 전체를 감싸도록 조절

**시각적 확인:**
```
✗ 잘못된 설정 (Y Value = 10)
┌────────────────┐
│   라인 (보이지 않음)
│                │
│   ┌──────┐     │  ← 라인이 ROI 밖에 있음
│   │ ROI  │     │
└───┴──────┴─────┘

✓ 올바른 설정 (Y Value = 100)
┌────────────────┐
│   ┌──────┐     │
│   │ 라인 │     │  ← 라인이 ROI 안에 있음
│   │ (포함)│    │
│   └──────┘     │
└────────────────┘
```

### 문제 2: "해상도가 320x240이 아니에요"

**원인:**
- 카메라가 320x240을 지원하지 않음
- 실제로는 640x480 등 다른 해상도로 동작

**해결 (v2.1에서 자동):**
1. 코드가 실제 해상도를 자동으로 감지
2. 원근 변환 좌표를 실제 해상도에 맞게 동적 계산
3. 사용자는 Y Value만 조절하면 됨

**확인 방법:**
```
프로그램 시작 시 콘솔 출력:
✅ USB 카메라 초기화 완료
   - 요청 해상도: 320x240
   - 실제 해상도: 640x480  ← 여기 확인
```

`1_Frame` 창 왼쪽 상단에도 표시:
```
Resolution: 640x480
Y-offset: 50
```

### 문제 3: "차량이 라인을 따라가지 않아요"

**체크리스트:**

1. **이진화 확인** (`4_Processed Frame` 창)
   - 라인이 흰색으로 선명하게 보이나요?
   - 아니면 → Detect Value 조절

2. **ROI 확인** (`1_Frame` 창)
   - 녹색 사각형이 라인을 포함하나요?
   - 아니면 → Y Value 조절

3. **히스토그램 확인** (콘솔 출력)
   - 좌우 값이 합리적인가요?
   - 예: `Left: 10000 | Right: 50000` (오른쪽에 라인 많음)

4. **속도 확인**
   - 너무 빠르면 → Motor Up Speed 낮춤
   - 너무 느리면 → Motor Up Speed 높임

5. **임계값 확인**
   - 반응이 너무 느리면 → Direction Threshold 낮춤
   - 너무 민감하면 → Direction Threshold 높임

### 문제 4: "막다른 길에서 멈춰요"

**원인:**
- Up Threshold가 너무 높거나 낮음
- 대체 경로 탐색이 제대로 작동하지 않음

**해결:**
1. Up Threshold 조절 (기본값 220000)
   - 낮춤 → 더 빨리 감지
   - 높임 → 더 늦게 감지

2. 서보 각도 확인
   - Servo 1, 2가 정상 범위인지 확인

3. DEBUG_MODE 활성화하여 로그 확인
   ```python
   DEBUG_MODE = True
   ```

---

## 📝 추가 팁

### 1. 환경별 최적 설정

#### 밝은 실내 (형광등)
```python
DEFAULT_BRIGHTNESS = 0
DEFAULT_CONTRAST = 40
DEFAULT_DETECT_VALUE = 120
DEFAULT_R_WEIGHT = 30
DEFAULT_G_WEIGHT = 40
DEFAULT_B_WEIGHT = 60
```

#### 어두운 실내
```python
DEFAULT_BRIGHTNESS = 30
DEFAULT_CONTRAST = 50
DEFAULT_DETECT_VALUE = 80
DEFAULT_R_WEIGHT = 60
DEFAULT_G_WEIGHT = 40
DEFAULT_B_WEIGHT = 30
```

#### 실외 (자연광)
```python
DEFAULT_BRIGHTNESS = -20
DEFAULT_CONTRAST = 60
DEFAULT_DETECT_VALUE = 100
# RGB 가중치는 현장에서 조절
```

### 2. 디버깅 팁

#### 콘솔 로그 활성화
```python
DEBUG_MODE = True
```

출력 예시:
```
--- Frame 123 ---
Left: 15234 | Right: 42156 | Diff: 26922 | Threshold: 35000
⬆️  직진
⚡ 속도: 35
📊 FPS: 28.5
```

#### 창 배치 최적화
- `1_Frame`: 원본 + ROI (녹색 사각형)
- `2_frame_transformed`: 원근 변환 결과
- `3_gray_frame`: 그레이스케일
- `4_Processed Frame`: 최종 이진화 (가장 중요!)

**권장**: `1_Frame`과 `4_Processed Frame`을 크게 띄우고, 나머지는 최소화

### 3. 성능 최적화

#### FPS 향상
```python
# time.sleep(0.05) 제거 또는 감소
time.sleep(0.01)  # 더 빠른 주기
```

#### 해상도 낮추기 (속도 ↑, 정확도 ↓)
```python
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 160)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 120)
```

---

## 🎓 요약

### 핵심 개념 3가지

1. **원근 변환**: 카메라 각도 보정 → 정면 뷰
2. **히스토그램 분석**: 좌우 영역 비교 → 방향 결정
3. **제자리 회전**: 한쪽 전진 + 한쪽 후진 → 정밀 회전

### 가장 중요한 설정 3가지

1. **Y Value**: ROI 영역 위치 (상단 포함 여부)
2. **Detect Value**: 이진화 임계값 (라인 검출)
3. **Motor Speed**: 속도 조절 (안정성)

### 문제 발생 시 순서

1. `4_Processed Frame` 확인 → 라인이 흰색인가?
2. `1_Frame` 확인 → 녹색 사각형이 라인 포함?
3. 콘솔 로그 확인 → 히스토그램 값이 합리적인가?
4. 트랙바 조절 → Y Value, Detect Value 우선

---

## 📞 문의

문제가 계속되면:
1. 콘솔 로그 전체 캡처
2. `1_Frame`, `4_Processed Frame` 스크린샷
3. 트랙바 설정 값 기록

---

**버전**: v2.1  
**작성일**: 2025-11-25  
**작성자**: AI Assistant  
**라이선스**: Shenzhen Yahboom Tech

