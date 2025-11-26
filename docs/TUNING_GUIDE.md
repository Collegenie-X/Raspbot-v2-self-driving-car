# 🎛️ Raspbot 자율주행 튜닝 가이드

카메라 설정 및 라인 검출 파라미터를 조절하는 방법입니다.

---

## 🎯 문제별 해결 방법

### 문제 1: 화면이 너무 밝아요 (4_Processed Frame이 거의 흰색)

**증상**:
- 원본 이미지가 너무 밝음
- 4_Processed Frame에서 라인과 배경 구분 안됨
- 거의 모든 픽셀이 흰색으로 표시

**해결 방법**:

#### 1️⃣ **카메라 밝기 낮추기** (가장 중요!)
```python
# 코드 수정 (초기화 부분)
cap.set(cv2.CAP_PROP_BRIGHTNESS, -20)  # 밝기를 음수로 (어둡게)
cap.set(cv2.CAP_PROP_CONTRAST, 50)     # 대비 높임
cap.set(cv2.CAP_PROP_EXPOSURE, 50)     # 노출 낮춤
```

또는 **실행 중 트랙바 조절**:
- `Brightness`: 0 → -20 (낮춤)
- `Contrast`: 40 → 60 (높임)
- `Detect Value`: 35 → 100 (높임)

#### 2️⃣ **이진화 임계값 올리기**
밝은 환경에서는 `Detect Value`를 높여야 합니다:
- 트랙바: `Detect Value` → 80~120 사이로 조절
- 배경이 흰색으로 변하고 라인이 검은색으로 보여야 정상

#### 3️⃣ **RGB 가중치 조절**
밝은 환경에서는 파란색 채널 가중치를 높입니다:
- `R_weight`: 50 → 30 (낮춤)
- `G_weight`: 50 → 40 (중간)
- `B_weight`: 50 → 60 (높임)

---

### 문제 2: 화면이 너무 어두워요

**증상**:
- 원본 이미지가 너무 어두움
- 라인이 잘 안 보임

**해결 방법**:

#### 1️⃣ **카메라 밝기 올리기**
```python
cap.set(cv2.CAP_PROP_BRIGHTNESS, 40)   # 밝기 높임
cap.set(cv2.CAP_PROP_EXPOSURE, 200)    # 노출 높임
```

또는 트랙바:
- `Brightness`: 0 → 40
- `Detect Value`: 80 → 40 (낮춤)

---

### 문제 3: 라인 검출이 안 돼요

**증상**:
- 4_Processed Frame에서 라인이 안 보임
- 차가 길을 못 찾고 방황

**해결 방법**:

#### 1️⃣ **Y Value 조절** (관심 영역)
- 카메라 각도에 따라 라인이 보이는 위치가 다릅니다
- `Y Value`: 10 → 20~50 (위로 이동)
- 녹색 사각형이 라인을 포함하도록 조절

#### 2️⃣ **Detect Value 조절** (이진화)
- 너무 낮으면: 모든 게 흰색
- 너무 높으면: 모든 게 검은색
- **목표**: 라인은 검은색, 배경은 흰색

실시간 조절:
1. `Detect Value`를 0부터 시작
2. 천천히 올리면서 4_Processed Frame 관찰
3. 라인이 선명하게 보이는 값 찾기

#### 3️⃣ **RGB 가중치 조절**
라인 색상에 따라:
- **흰색 라인**: R=33, G=33, B=33 (균등)
- **노란색 라인**: R=40, G=40, B=20 (파랑 낮춤)
- **밝은 환경**: R=30, G=40, B=60 (파랑 높임)

---

### 문제 4: 해상도가 320x240이 아니에요

**증상**:
- 카메라 초기화 메시지에서 실제 해상도가 다름
- 예: 요청 320x240, 실제 640x480

**해결 방법**:

#### 1️⃣ **카메라 해상도 강제 설정**
```python
# 더 명확한 방법으로 설정
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

# 프레임 읽은 후 강제 리사이즈
ret, frame = cap.read()
frame = cv2.resize(frame, (320, 240))
```

#### 2️⃣ **Y Value 조절**
해상도가 다르면 관심 영역도 달라집니다:
- 640x480인 경우: `Y Value` → 20~60
- 320x240인 경우: `Y Value` → 10~30

---

## 🎛️ 트랙바 설정 가이드

### 기본 설정값 (일반 환경)

| 파라미터 | 권장값 | 범위 | 설명 |
|---------|-------|------|------|
| **Servo 1 Angle** | 90 | 0~180 | 카메라 좌우 각도 |
| **Servo 2 Angle** | 25 | 0~110 | 카메라 상하 각도 (낮을수록 아래) |
| **Y Value** | 10 | 0~160 | 관심 영역 위치 |
| **Direction Threshold** | 35000 | 0~500000 | 방향 전환 민감도 |
| **Up Threshold** | 220000 | 0~500000 | 막다른 길 감지 |
| **Brightness** | 0 | 0~100 | 카메라 밝기 |
| **Contrast** | 40 | 0~100 | 카메라 대비 |
| **Detect Value** | 80 | 0~150 | 이진화 임계값 ⭐ |
| **Motor Up Speed** | 20 | 0~255 | 전진 속도 |
| **Motor Down Speed** | 10 | 0~255 | 회전 속도 |
| **R_weight** | 30 | 0~100 | 빨강 가중치 |
| **G_weight** | 40 | 0~100 | 초록 가중치 |
| **B_weight** | 60 | 0~100 | 파랑 가중치 |

### 밝은 환경 (실내, 창가)

```
Brightness: -10~10
Contrast: 50~70
Detect Value: 80~120
R_weight: 20~30
G_weight: 30~40
B_weight: 50~70
```

### 어두운 환경 (저조도)

```
Brightness: 40~60
Contrast: 30~40
Detect Value: 30~50
R_weight: 40~50
G_weight: 40~50
B_weight: 40~50
```

---

## 📊 단계별 튜닝 방법

### Step 1: 카메라 각도 조절

1. `Servo 1 Angle`: 90° (정면)
2. `Servo 2 Angle`: 20~30° (약간 아래 향하게)
3. 1_Frame 창에서 라인이 보이는지 확인

### Step 2: 밝기/대비 조절

1. **1_Frame 창 확인**
   - 너무 밝으면: `Brightness` 낮춤 (0 → -20)
   - 너무 어두우면: `Brightness` 높임 (0 → 40)

2. **대비 조절**
   - `Contrast`: 40~60 사이로 설정
   - 라인과 배경 구분이 명확해야 함

### Step 3: 관심 영역 설정

1. **Y Value 조절**
   - 녹색 사각형이 라인을 포함하도록
   - 너무 위: 라인이 안 보임
   - 너무 아래: 불필요한 영역 포함

2. **2_frame_transformed 확인**
   - 원근 변환 후 라인이 수직으로 보여야 함

### Step 4: 이진화 임계값 (가장 중요!)

1. **Detect Value 조절**
   - 시작: 0부터
   - 천천히 올리면서 4_Processed Frame 관찰
   - **목표**: 라인은 검은색, 배경은 흰색

2. **RGB 가중치 조절**
   - 라인이 흐릿하면: 가중치 조절
   - 밝은 환경: B_weight 높임
   - 어두운 환경: 균등하게 (33, 33, 33)

### Step 5: 속도 조절

1. **안전 속도로 시작**
   - `Motor Up Speed`: 20
   - `Motor Down Speed`: 10

2. **점진적으로 증가**
   - 라인 추종이 안정되면
   - 속도를 10씩 증가

---

## 🔍 디버깅 팁

### 각 창의 의미

1. **1_Frame**: 원본 카메라 영상
   - 녹색 사각형: 관심 영역 (Y Value로 조절)

2. **2_frame_transformed**: 원근 변환 후
   - 라인이 수직으로 보여야 함

3. **3_gray_frame**: 그레이스케일
   - RGB 가중치 적용 결과

4. **4_Processed Frame**: 이진화 결과
   - **라인: 검은색 / 배경: 흰색** 이어야 함
   - 이게 잘못되면 자율주행 불가능!

### 좋은 설정의 예

```
1_Frame: 라인이 선명하게 보임
2_frame_transformed: 라인이 수직으로 변환됨
3_gray_frame: 라인과 배경이 구분됨
4_Processed Frame: 라인은 검은색, 배경은 흰색으로 명확히 구분
```

### 나쁜 설정의 예

```
❌ 4_Processed Frame이 거의 흰색
   → Detect Value가 너무 낮음 (높여야 함)
   → 또는 Brightness가 너무 높음 (낮춰야 함)

❌ 4_Processed Frame이 거의 검은색
   → Detect Value가 너무 높음 (낮춰야 함)
   → 또는 Brightness가 너무 낮음 (높여야 함)

❌ 라인이 흐릿함
   → Contrast 높이기
   → RGB 가중치 조절
```

---

## ⚡ 빠른 설정 레시피

### 레시피 1: 밝은 실내 (가장 흔한 경우)

```python
# 코드에서 초기값 설정
DEFAULT_BRIGHTNESS = 0
DEFAULT_CONTRAST = 50
DEFAULT_DETECT_VALUE = 100
DEFAULT_R_WEIGHT = 30
DEFAULT_G_WEIGHT = 40
DEFAULT_B_WEIGHT = 60
```

### 레시피 2: 어두운 실내

```python
DEFAULT_BRIGHTNESS = 40
DEFAULT_CONTRAST = 40
DEFAULT_DETECT_VALUE = 40
DEFAULT_R_WEIGHT = 40
DEFAULT_G_WEIGHT = 40
DEFAULT_B_WEIGHT = 40
```

### 레시피 3: 야외 (햇빛)

```python
DEFAULT_BRIGHTNESS = -20
DEFAULT_CONTRAST = 70
DEFAULT_DETECT_VALUE = 120
DEFAULT_R_WEIGHT = 20
DEFAULT_G_WEIGHT = 30
DEFAULT_B_WEIGHT = 70
```

---

## 💾 설정 저장하기

최적 값을 찾았다면 코드에 저장:

1. `6_custom_autoplot.py` 열기
2. 사용자 설정 영역 수정:

```python
# ============================
# 사용자 설정 영역 (여기를 수정하세요!)
# ============================

# 라인 검출 설정
DEFAULT_DETECT_VALUE = 100  # 찾은 최적값 입력
DEFAULT_BRIGHTNESS = 0
DEFAULT_CONTRAST = 50

# RGB 가중치
DEFAULT_R_WEIGHT = 30
DEFAULT_G_WEIGHT = 40
DEFAULT_B_WEIGHT = 60
```

---

## 🎮 키보드 단축키

- `ESC`: 종료
- `SPACE`: 일시정지 (디버깅용)
- `l`: LED 토글
- `b`: 부저 테스트

---

## 📞 여전히 안 되나요?

1. **카메라 위치 확인**
   - 카메라가 라인을 향하고 있는지
   - Servo 2 Angle을 조절해서 각도 맞추기

2. **조명 확인**
   - 너무 밝거나 어둡지 않은지
   - 라인과 배경의 대비가 충분한지

3. **라인 상태 확인**
   - 라인이 선명한지
   - 너무 좁거나 넓지 않은지

4. **코드 로그 확인**
   - 터미널 출력 확인
   - Left/Right 값이 출력되는지

---

**업데이트**: 2025-11-25

