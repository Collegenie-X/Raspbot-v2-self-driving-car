# 🚗 Raspbot v2 자율주행 시스템 가이드 (v3.0)

## 📋 목차

1. [개요](#-개요)
2. [시스템 아키텍처](#-시스템-아키텍처)
3. [실행 단계별 흐름](#-실행-단계별-흐름)
4. [핵심 알고리즘 상세](#-핵심-알고리즘-상세)
5. [이미지 처리 파이프라인](#-이미지-처리-파이프라인)
6. [방향 결정 알고리즘](#-방향-결정-알고리즘)
7. [RGB 가중치 필터링](#-rgb-가중치-필터링)
8. [파라미터 튜닝 가이드](#-파라미터-튜닝-가이드)
9. [함수 레퍼런스](#-함수-레퍼런스)
10. [트러블슈팅](#-트러블슈팅)

---

## 📌 개요

### 버전 정보

| 항목 | 내용 |
|------|------|
| **버전** | v3.0 (RGB 필터링 + 3등분 분석 + 모듈화) |
| **파일** | `autoplot.py` |
| **기반** | `1_autoplot___rgb_filter.py` 통합 |
| **작성일** | 2025-12-08 |

### 주요 특징

```mermaid
flowchart LR
    subgraph v3_특징["v3.0 주요 특징"]
        A["🎨 RGB 가중치 필터링<br/>(빛 반사 억제)"]
        B["📊 히스토그램 3등분 분석<br/>(좌/중앙/우)"]
        C["🔧 모듈화 구조<br/>(10단계 실행)"]
        D["⌨️ 모터 토글 기능<br/>(SPACE 키)"]
        E["📈 실시간 시각화<br/>(방향/RGB/비율)"]
    end
```

### 도로 환경 특성

```mermaid
flowchart TB
    subgraph 도로_환경["도로 환경"]
        direction LR
        A["검정색 바탕<br/>(주행 가능)"]
        B["회색/흰색 선<br/>(경계선)"]
        C["빨간색 선<br/>(곡선 표시)"]
    end

    subgraph 이진화_결과["이진화 결과"]
        D["0 (검정)<br/>= 주행 가능"]
        E["255 (흰색)<br/>= 경계/막힘"]
    end

    A -->|"이진화"| D
    B -->|"이진화"| E
    C -->|"이진화"| E
```

| 요소 | 색상 | 의미 | 이진화 결과 | 히스토그램 합 |
|------|------|------|-------------|--------------|
| **도로 바닥** | 검정색 | 주행 가능 영역 | 0 (검정) | 낮음 (좋음) |
| **직선 경계** | 회색/흰색 | 도로 경계선 | 255 (흰색) | 높음 (막힘) |
| **곡선 구간** | 빨간색 | 회전 필요 구간 | 255 (흰색) | 높음 (막힘) |

---

## 🏗️ 시스템 아키텍처

### 전체 시스템 구조

```mermaid
flowchart TB
    subgraph 입력["📥 입력 계층"]
        CAM["🎥 카메라<br/>(320x240)"]
        TRACK["🎛️ 트랙바<br/>(파라미터)"]
        KEY["⌨️ 키보드<br/>(제어)"]
    end

    subgraph 처리["⚙️ 처리 계층"]
        ROI["ROI 계산<br/>calculate_roi_points()"]
        PERSP["원근 변환<br/>apply_perspective_transform()"]
        GRAY["그레이스케일 변환<br/>weighted_gray()"]
        DETECT["도로선 검출<br/>detect_road_lines()"]
        HIST["히스토그램 분석<br/>analyze_histogram()"]
        DECIDE["방향 결정<br/>decide_direction()"]
    end

    subgraph 출력["📤 출력 계층"]
        MOTOR["🔧 모터 제어<br/>(M0~M3)"]
        SERVO["📷 서보 모터<br/>(S1, S2)"]
        LED["💡 LED 효과"]
        BEEP["🔊 부저"]
        DISP["🖥️ 화면 표시"]
    end

    CAM --> ROI
    TRACK --> ROI
    TRACK --> GRAY
    TRACK --> DECIDE
    
    ROI --> PERSP --> GRAY --> DETECT --> HIST --> DECIDE
    
    DECIDE --> MOTOR
    DECIDE --> LED
    
    KEY --> SERVO
    KEY --> LED
    KEY --> MOTOR
    
    DETECT --> DISP
```

### 하드웨어 연결 구조

```mermaid
flowchart LR
    subgraph Raspberry_Pi["🍓 Raspberry Pi"]
        I2C["I2C Bus"]
        USB["USB Port"]
    end

    subgraph Raspbot["🤖 Raspbot PCB"]
        MCU["MCU (0x2B)"]
    end

    subgraph 모터["🔧 4륜 모터"]
        M0["M0 (왼쪽 앞)"]
        M1["M1 (왼쪽 뒤)"]
        M2["M2 (오른쪽 앞)"]
        M3["M3 (오른쪽 뒤)"]
    end

    subgraph 서보["📷 서보 모터"]
        S1["S1 (좌우 0~180°)"]
        S2["S2 (상하 0~110°)"]
    end

    I2C <--> MCU
    USB --> CAM2["🎥 USB 카메라"]
    MCU --> M0 & M1 & M2 & M3
    MCU --> S1 & S2
```

---

## 📈 실행 단계별 흐름

### 10단계 실행 순서

```mermaid
sequenceDiagram
    participant Main as 🚀 메인
    participant Init as ⚙️ 초기화
    participant Loop as 🔄 메인 루프
    participant Proc as 🖼️ 이미지 처리
    participant Ctrl as 🚗 차량 제어

    Main->>Init: STEP 1: 라이브러리 Import
    Init->>Init: STEP 2: 설정값 로딩
    Init->>Init: STEP 3: 하드웨어 초기화
    Init->>Init: STEP 4: 트랙바 설정
    Init->>Init: STEP 5~8: 함수 정의
    
    rect rgb(200, 230, 200)
        note over Loop: STEP 9: 메인 루프
        loop 프레임 반복
            Loop->>Proc: 프레임 캡처
            Proc->>Proc: ROI 계산
            Proc->>Proc: 원근 변환
            Proc->>Proc: 그레이스케일 (RGB 가중치)
            Proc->>Proc: 도로선 검출
            Proc->>Proc: 히스토그램 분석
            Proc->>Loop: 방향 결정
            Loop->>Ctrl: 차량 제어
            Loop->>Loop: 키보드 입력 확인
        end
    end
    
    Main->>Init: STEP 10: 정리 및 종료
```

### 단계별 상세 설명

| 단계 | 함수/로직 | 설명 |
|------|----------|------|
| **STEP 1** | `import` | cv2, numpy, Raspbot_Lib 로딩 |
| **STEP 2** | 설정값 | 속도, RGB 가중치, 임계값 등 설정 |
| **STEP 3** | `initialize_raspbot()`, `initialize_camera()` | 하드웨어 초기화 |
| **STEP 4** | `cv2.createTrackbar()` | 16개 트랙바 생성 |
| **STEP 5** | 이미지 처리 함수 | ROI, 원근 변환, 도로선 검출 |
| **STEP 6** | 차량 제어 함수 | car_run, car_left, car_right |
| **STEP 7** | 서보 제어 함수 | rotate_servo |
| **STEP 8** | 방향 결정 함수 | analyze_histogram, decide_direction |
| **STEP 9** | 메인 루프 | 프레임 처리 및 제어 반복 |
| **STEP 10** | `cleanup_and_exit()` | 리소스 해제 |

---

## 🧮 핵심 알고리즘 상세

### 알고리즘 전체 흐름

```mermaid
flowchart TB
    subgraph 1_입력["1️⃣ 입력"]
        A["원본 프레임<br/>(320x240 BGR)"]
    end

    subgraph 2_ROI["2️⃣ ROI 계산"]
        B["ROI Top Y (695/1000)"]
        C["ROI Bottom Y (812/1000)"]
        D["pts_src 사다리꼴"]
    end

    subgraph 3_변환["3️⃣ 원근 변환"]
        E["Bird's Eye View<br/>(320x240)"]
    end

    subgraph 4_그레이["4️⃣ RGB 그레이스케일"]
        F["R×r_weight<br/>+ G×g_weight<br/>+ B×b_weight"]
    end

    subgraph 5_검출["5️⃣ 도로선 검출"]
        G1["HSV 빨간색<br/>H=0~10, 170~180"]
        G2["밝기 회색<br/>threshold"]
        G3["마스크 결합"]
    end

    subgraph 6_분석["6️⃣ 히스토그램 분석"]
        H["열 방향 합산"]
        I["3등분 분할<br/>LEFT/CENTER/RIGHT"]
    end

    subgraph 7_결정["7️⃣ 방향 결정"]
        J["우선순위 판단<br/>1. 좌우차이<br/>2. 중앙클리어<br/>3. 막다른골목"]
    end

    subgraph 8_제어["8️⃣ 차량 제어"]
        K["모터 속도 설정<br/>LED 효과"]
    end

    A --> B & C --> D --> E --> F --> G1 & G2 --> G3 --> H --> I --> J --> K
```

---

## 🖼️ 이미지 처리 파이프라인

### ROI (Region of Interest) 계산

```mermaid
flowchart LR
    subgraph 원본["원본 이미지"]
        direction TB
        TOP["상단 (배경)"]
        ROI["ROI 영역<br/>(도로)"]
        BOT["하단 (차체)"]
    end

    subgraph 설정["ROI 설정"]
        T1["ROI Top Y<br/>695/1000<br/>= 167px"]
        T2["ROI Bottom Y<br/>812/1000<br/>= 195px"]
    end

    ROI -->|"관심 영역"| T1 & T2

    style ROI fill:#90EE90
```

### ROI 좌표 계산 공식

```python
def calculate_roi_points(actual_w, actual_h, roi_top_y, roi_bottom_y):
    """
    ROI 포인트 계산
    
    트랙바 값(0~1000) → 실제 픽셀 좌표로 변환
    
    예시 (해상도 320x240):
    - roi_top_y = 695 → top_y = 695 × 240 / 1000 = 166.8px
    - roi_bottom_y = 812 → bottom_y = 812 × 240 / 1000 = 194.9px
    """
    top_y = int(roi_top_y * actual_h / 1000)
    bottom_y = int(roi_bottom_y * actual_h / 1000)
    
    # 범위 제한 및 최소 높이 보장
    top_y = max(0, min(top_y, actual_h - 1))
    bottom_y = max(0, min(bottom_y, actual_h - 1))
    if top_y >= bottom_y:
        top_y = max(0, bottom_y - 50)
    
    margin = 10  # 좌우 여백
    
    # 사다리꼴: [좌하, 우하, 우상, 좌상]
    pts_src = np.float32([
        [margin, bottom_y],
        [actual_w - margin, bottom_y],
        [actual_w - margin, top_y],
        [margin, top_y],
    ])
    
    return pts_src, top_y, bottom_y
```

### 원근 변환 (Perspective Transform)

```mermaid
flowchart LR
    subgraph 변환전["변환 전"]
        A["사다리꼴 ROI<br/>(원근 시점)"]
    end

    subgraph 변환후["변환 후"]
        B["직사각형<br/>(Bird's Eye View)"]
    end

    A -->|"warpPerspective()"| B
```

### 도로선 검출 알고리즘

```mermaid
flowchart TB
    subgraph 입력["입력"]
        A["BGR 컬러 이미지"]
    end

    subgraph 빨간색["🔴 빨간색 검출 (HSV)"]
        B1["BGR → HSV"]
        B2["빨강1: H=0~10<br/>S=70~255, V=50~255"]
        B3["빨강2: H=170~180<br/>S=70~255, V=50~255"]
        B4["OR 결합"]
    end

    subgraph 회색["⬜ 회색 검출"]
        C1["RGB 가중 그레이스케일"]
        C2["threshold_gray<br/>= detect_value - 30"]
        C3["dark_threshold = 50<br/>(검정 도로 보호)"]
    end

    subgraph 결합["결합 & 노이즈 제거"]
        D1["빨강 OR 회색"]
        D2["MORPH_CLOSE<br/>(구멍 메우기)"]
        D3["MORPH_OPEN<br/>(노이즈 제거)"]
    end

    A --> B1 --> B2 & B3 --> B4
    A --> C1 --> C2 --> C3
    B4 --> D1
    C3 --> D1 --> D2 --> D3
```

### 빨간색 HSV 범위 상세

| 범위 | Hue (색조) | Saturation | Value | 설명 |
|------|-----------|------------|-------|------|
| **빨강 1** | 0~10 | 70~255 | 50~255 | 주황색 방향 빨강 |
| **빨강 2** | 170~180 | 70~255 | 50~255 | 보라색 방향 빨강 |

---

## 🧭 방향 결정 알고리즘

### 히스토그램 3등분 분석

```mermaid
flowchart TB
    subgraph 이진화["이진화 이미지 (320px 폭)"]
        direction LR
        L["LEFT<br/>(0~106px)"]
        C["CENTER<br/>(107~213px)"]
        R["RIGHT<br/>(214~320px)"]
    end

    subgraph 분석["분석"]
        H["histogram = np.sum(binary, axis=0)"]
        LS["left_sum = Σ histogram[0:106]"]
        CS["center_sum = Σ histogram[107:213]"]
        RS["right_sum = Σ histogram[214:320]"]
    end

    이진화 --> H --> LS & CS & RS
```

### 방향 결정 우선순위 (핵심 로직)

```mermaid
flowchart TD
    A["📊 히스토그램 3등분 분석"] --> B{"|right - left| > threshold?<br/>(좌우 차이 큼?)"}
    
    B -->|"예 ⭐최우선"| C{right > left?}
    C -->|"예"| D["◀️ LEFT 회전<br/>(오른쪽에 도로선 많음)"]
    C -->|"아니오"| E["▶️ RIGHT 회전<br/>(왼쪽에 도로선 많음)"]
    
    B -->|"아니오"| F{center_ratio < 0.2?<br/>(중앙 클리어?)}
    F -->|"예"| G["⬆️ 직진<br/>(중앙에 도로선 없음)"]
    
    F -->|"아니오"| H{"(left + right) / 2 < up_threshold?<br/>(막다른 골목?)"}
    H -->|"예"| I["🎲 랜덤 방향<br/>(부저 3회 알림)"]
    H -->|"아니오"| J["⬆️ 직진<br/>(기본값)"]

    style D fill:#FFD700
    style E fill:#FFD700
    style G fill:#90EE90
    style I fill:#FF6B6B
    style J fill:#90EE90
```

### 방향 결정 핵심 원리

```
┌─────────────────────────────────────────────────────────────┐
│  핵심 원리: 히스토그램 합과 주행 가능성의 반비례 관계       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  • 합이 작음 = 검정 도로 많음 = 주행 가능 영역              │
│  • 합이 큼   = 도로선 많음   = 경계/막힘                    │
│                                                             │
│  로직:                                                      │
│  • right_sum > left_sum → 오른쪽에 도로선 → LEFT 회전      │
│  • left_sum > right_sum → 왼쪽에 도로선  → RIGHT 회전      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 임계값 설명

| 임계값 | 기본값 | 범위 | 역할 |
|--------|--------|------|------|
| **direction_threshold** | 35,000 | 0~500,000 | 좌우 차이 판단 (높으면 덜 회전) |
| **up_threshold** | 220,000 | 0~500,000 | 막다른 골목 감지 |
| **CENTER_CLEAR_THRESHOLD** | 0.2 (20%) | 0.0~1.0 | 중앙 클리어 판단 |

---

## 🎨 RGB 가중치 필터링

### 빛 반사 문제와 해결

```mermaid
flowchart LR
    subgraph 문제["❌ 문제 상황"]
        A["검정 도로 표면"]
        B["빛 반사 발생"]
        C["회색/흰색으로<br/>오검출"]
    end

    subgraph 해결["✅ 해결: RGB 가중치"]
        D["파랑(B) 채널 강조"]
        E["빛 반사 영역<br/>상대적 어둡게"]
        F["검정 도로 보존"]
    end

    A --> B --> C
    D --> E --> F
```

### RGB 가중치 공식

```python
def weighted_gray(image, r_weight, g_weight, b_weight):
    """
    RGB 가중치 기반 그레이스케일 변환
    
    표준 그레이스케일:
    Y = 0.299 × R + 0.587 × G + 0.114 × B
    
    가중 그레이스케일 (v3.0):
    Y = R × r_weight + G × g_weight + B × b_weight
    
    원리:
    - 파랑(B)은 빛 반사에 덜 민감
    - 빨강(R)은 빛 반사에 민감
    - B 가중치↑ → 빛 반사 억제
    """
    r_weight /= 100.0  # 0~100 → 0~1
    g_weight /= 100.0
    b_weight /= 100.0
    
    # OpenCV BGR 순서
    # [:,:,0] = B, [:,:,1] = G, [:,:,2] = R
    weighted = cv2.addWeighted(
        cv2.addWeighted(image[:,:,2], r_weight,
                       image[:,:,1], g_weight, 0),
        1.0,
        image[:,:,0], b_weight, 0
    )
    return weighted
```

### 환경별 권장 RGB 설정

```mermaid
flowchart TB
    subgraph 밝은환경["☀️ 밝은 환경 (빛 반사 있음)"]
        A1["R: 30 (낮춤)"]
        A2["G: 40 (중간)"]
        A3["B: 60~80 (높임)"]
    end

    subgraph 어두운환경["🌙 어두운 환경"]
        B1["R: 60 (높임)"]
        B2["G: 40 (중간)"]
        B3["B: 30 (낮춤)"]
    end

    subgraph 직사광선["🔆 직사광선"]
        C1["R: 10~20 (최저)"]
        C2["G: 30 (낮춤)"]
        C3["B: 70~80 (최고)"]
    end
```

| 환경 | R | G | B | 효과 |
|------|---|---|---|------|
| **표준** | 30 | 40 | 60 | 균형있는 처리 |
| **밝은 실내** | 20 | 40 | 70 | 빛 반사 억제 |
| **어두운 환경** | 60 | 40 | 30 | 명암 강조 |
| **직사광선** | 10 | 30 | 80 | 최대 빛 반사 억제 |

---

## ⚙️ 파라미터 튜닝 가이드

### 전체 트랙바 목록

| 카테고리 | 파라미터 | 기본값 | 범위 | 설명 |
|----------|----------|--------|------|------|
| **서보** | Servo_1_Angle | 95 | 0~180 | 카메라 좌우 |
| | Servo_2_Angle | 0 | 0~110 | 카메라 상하 |
| **ROI** | ROI_Top_Y | 695 | 0~1000 | ROI 상단 (작을수록 멀리) |
| | ROI_Bottom_Y | 812 | 0~1000 | ROI 하단 (클수록 가까이) |
| **임계값** | Direction_Threshold | 35,000 | 0~500,000 | 회전 민감도 |
| | Up_Threshold | 220,000 | 0~500,000 | 막다른 골목 감지 |
| **카메라** | Brightness | 32 | 0~100 | 밝기 |
| | Contrast | 0 | 0~100 | 대비 |
| | Detect_Value | 120 | 0~150 | 이진화 임계값 |
| **속도** | Motor_Up_Speed | 15 | 0~255 | 주 속도 |
| | Motor_Down_Speed | 8 | 0~255 | 감속 측 속도 |
| **RGB** | R_weight | 30 | 0~100 | 빨강 가중치 |
| | G_weight | 40 | 0~100 | 초록 가중치 |
| | B_weight | 60 | 0~100 | 파랑 가중치 |

### 상황별 권장 설정

```mermaid
flowchart TB
    subgraph 직선["📏 직선 구간"]
        A1["Direction_Threshold ↑<br/>(높게, 덜 회전)"]
        A2["Motor_Up_Speed ↑<br/>(빠르게)"]
        A3["ROI_Top_Y ↓<br/>(멀리 보기)"]
    end

    subgraph 곡선["🔄 곡선 구간"]
        B1["Direction_Threshold ↓<br/>(낮게, 민감)"]
        B2["Motor_Up_Speed ↓<br/>(느리게)"]
        B3["ROI_Top_Y ↑<br/>(가까이 보기)"]
    end

    subgraph 빛반사["☀️ 빛 반사 심한 환경"]
        C1["B_weight ↑↑<br/>(70~80)"]
        C2["R_weight ↓<br/>(20~30)"]
        C3["Detect_Value ↑<br/>(130~150)"]
    end
```

---

## 📚 함수 레퍼런스

### 이미지 처리 함수

| 함수명 | 입력 | 출력 | 설명 |
|--------|------|------|------|
| `calculate_roi_points()` | actual_w, actual_h, roi_top_y, roi_bottom_y | pts_src, top_y, bottom_y | ROI 좌표 계산 |
| `apply_roi_visualization()` | frame, pts_src, ... | frame_with_rect | ROI 시각화 |
| `apply_perspective_transform()` | frame, pts_src | frame_transformed | 원근 변환 |
| `weighted_gray()` | image, r/g/b_weight | gray_frame | RGB 그레이스케일 |
| `detect_road_lines()` | color_frame, gray_frame, detect_value | mask_lines | 도로선 검출 |
| `process_frame()` | frame, params... | binary_frame | 전체 처리 파이프라인 |

### 방향 결정 함수

| 함수명 | 입력 | 출력 | 설명 |
|--------|------|------|------|
| `analyze_histogram()` | histogram | left/center/right_sum, ratios | 3등분 분석 |
| `decide_direction()` | histogram, thresholds... | direction, sums | 방향 결정 |
| `visualize_direction_on_frame()` | binary_frame, direction, sums, rgb_weights | frame_color | 시각화 |

### 차량 제어 함수

| 함수명 | 입력 | 동작 |
|--------|------|------|
| `car_run(speed_l, speed_r)` | 좌/우 속도 | 직진 (4륜 전진) |
| `car_left(speed_l, speed_r)` | 좌/우 속도 | 좌회전 (제자리) |
| `car_right(speed_l, speed_r)` | 좌/우 속도 | 우회전 (제자리) |
| `car_stop()` | - | 정지 |
| `control_car(direction, up_speed, down_speed)` | 방향, 속도 | 방향별 제어 |

### 보조 함수

| 함수명 | 설명 |
|--------|------|
| `handle_keyboard_input()` | 키보드 입력 처리 (ESC/SPACE/l/b) |
| `read_trackbar_values()` | 트랙바 값 일괄 읽기 |
| `apply_camera_settings()` | 카메라 속성 설정 |
| `cleanup_and_exit()` | 정리 및 종료 |

---

## 🔧 트러블슈팅

### 일반적인 문제 해결

| 문제 | 원인 | 해결 방법 |
|------|------|----------|
| **빛 반사로 오검출** | R 가중치 높음 | B_weight ↑ (60~80), R_weight ↓ (20~30) |
| **회전 너무 민감** | threshold 낮음 | Direction_Threshold ↑ |
| **회전 안 함** | threshold 높음 | Direction_Threshold ↓ |
| **막다른 골목 미감지** | up_threshold 높음 | Up_Threshold ↓ |
| **직진 불안정** | 중앙 클리어 판단 실패 | CENTER_CLEAR_THRESHOLD 조정 |
| **ROI 영역 부적절** | 해상도 미스매치 | ROI_Top_Y, ROI_Bottom_Y 조정 |

### 키보드 조작

| 키 | 동작 |
|----|------|
| **ESC** | 프로그램 종료 |
| **SPACE** | 모터 ON/OFF 토글 (카메라 계속 작동) |
| **l** | LED ON/OFF 토글 |
| **b** | 부저 ON/OFF 토글 |

### 디버그 정보 해석

```
--- Frame 100 ---
RGB Weights: R=30, G=40, B=60

   📊 히스토그램 분석 (도로선 검출 모드):
      LEFT:   12345 (ratio: 0.150) - 낮을수록 주행 가능
      CENTER: 23456 (ratio: 0.280) - 낮을수록 주행 가능
      RIGHT:  56789 (ratio: 0.680) - 낮을수록 주행 가능
      L-R 차이:  44444 | 임계값: 35000
   🔄 결정: LEFT 회전 (도로선 적은 쪽으로)
```

**해석:**
- LEFT (12,345) < RIGHT (56,789) → 왼쪽이 더 주행 가능
- L-R 차이 (44,444) > 임계값 (35,000) → 회전 필요
- 결론: LEFT 회전

---

## 📊 성능 최적화

### 최적화 팁

| 최적화 | 방법 | 효과 |
|--------|------|------|
| **해상도** | 320x240 유지 | FPS 유지 |
| **프레임 스킵** | `time.sleep(0.05)` | CPU 부하 감소 |
| **ROI 최소화** | 필요 영역만 처리 | 연산량 감소 |
| **디버그 출력** | 10프레임마다 | I/O 감소 |

---

**작성일**: 2025-12-08  
**버전**: v3.0  
**파일 위치**: `03_self_driving/AUTOPLOT_v3_가이드.md`

