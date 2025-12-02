# Raspbot v2 자율주행 시스템 분석 문서

## 📋 목차
1. [시스템 개요](#시스템-개요)
2. [전체 유저 플로우](#전체-유저-플로우)
3. [주요 실행 단계](#주요-실행-단계)
4. [시스템 아키텍처](#시스템-아키텍처)
5. [이미지 처리 파이프라인](#이미지-처리-파이프라인)
6. [방향 결정 알고리즘](#방향-결정-알고리즘)
7. [주요 기능 상세](#주요-기능-상세)
8. [하드웨어 구성](#하드웨어-구성)
9. [설정 파라미터](#설정-파라미터)

---

## 시스템 개요

### 프로젝트 정보
- **파일명**: `0_autoplot___test.py`
- **목적**: Raspbot v2 자율주행 라인 트레이싱 테스트
- **주요 특징**:
  - 서보 모터 제어를 통한 카메라 각도 조절
  - 빨간색/회색 도로선 기반 라인 트레이싱
  - 히스토그램 3등분 분석 기반 방향 결정
  - 실시간 이미지 처리 및 차량 제어

### 현재 구현된 기능
- **막다른 길 감지**: 중앙 영역의 도로선 비율(70% 이상) 분석
- **랜덤 방향 선택**: 막다른 길 감지 시 LEFT/RIGHT 랜덤 선택

### 교육생 실습 과제
- **서보 모터 활용 대체 경로 탐색**: 서보를 180도 회전하여 뒤쪽 확인
- **최적 경로 선택 알고리즘**: 히스토그램 분석으로 가장 주행 가능한 경로 결정
- **랜덤 대신 지능형 선택**: 현재 랜덤 선택을 서보 기반 분석으로 개선

### 핵심 기술
- **비전 처리**: OpenCV 기반 이미지 처리
- **도로선 감지**: HSV 색상 공간 + 그레이스케일 임계값
- **방향 결정**: 히스토그램 3등분 분석
- **하드웨어 제어**: Raspbot 라이브러리 활용

---

## 전체 유저 플로우

```mermaid
graph TD
    A[프로그램 시작] --> B[라이브러리 로드]
    B --> C[하드웨어 초기화]
    C --> D{초기화 성공?}
    D -->|실패| E[에러 메시지 출력 및 종료]
    D -->|성공| F[카메라 초기화]
    F --> G{카메라 성공?}
    G -->|실패| E
    G -->|성공| H[서보/LED/부저 초기 설정]
    H --> I[트랙바 및 윈도우 생성]
    I --> J[메인 루프 시작]
    
    J --> K[프레임 캡처]
    K --> L[이미지 처리]
    L --> M[히스토그램 분석]
    M --> N[방향 결정<br/>LEFT/UP/RIGHT]
    N --> Q[방향 결정 완료]
    Q --> R[차량 제어 명령]
    R --> S[LED 효과 적용]
    S --> T{키 입력 확인}
    T -->|ESC| U[종료 프로세스]
    T -->|SPACE| V[일시정지]
    T -->|L| W[LED 토글]
    T -->|B| X[부저 테스트]
    T -->|없음| J
    V --> J
    W --> J
    X --> J
    
    U --> Y[모터 정지]
    Y --> Z[LED 끄기]
    Z --> AA[서보 원위치]
    AA --> AB[카메라 해제]
    AB --> AC[프로그램 종료]
    
    style A fill:#e1f5e1
    style AC fill:#ffe1e1
    style O fill:#fff4e1
    style P fill:#e1f0ff
```

---

## 주요 실행 단계

### 9단계 실행 프로세스

```mermaid
flowchart TB
    subgraph Step1[1단계: 초기화]
        A1[라이브러리 Import]
        A2[경로 설정]
    end
    
    subgraph Step2[2단계: 설정 로드]
        B1[속도 설정]
        B2[검출 설정]
        B3[서보 각도 설정]
    end
    
    subgraph Step3[3단계: 하드웨어]
        C1[Raspbot 초기화]
        C2[카메라 초기화]
        C3[서보/LED 설정]
    end
    
    subgraph Step4[4단계: UI 설정]
        D1[윈도우 생성]
        D2[트랙바 생성]
    end
    
    subgraph Step5[5단계: 함수 정의]
        E1[이미지 처리]
        E2[차량 제어]
        E3[서보 제어]
        E4[방향 결정]
    end
    
    subgraph Step6[6단계: 메인 루프]
        F1[실시간 처리]
        F2[방향 결정]
        F3[차량 제어]
    end
    
    subgraph Step7[7단계: 종료]
        G1[정리 작업]
        G2[리소스 해제]
    end
    
    Step1 --> Step2 --> Step3 --> Step4 --> Step5 --> Step6 --> Step7
    
    style Step1 fill:#e1f5e1
    style Step2 fill:#e1f0ff
    style Step3 fill:#fff4e1
    style Step4 fill:#f0e1ff
    style Step5 fill:#ffe1f0
    style Step6 fill:#e1ffff
    style Step7 fill:#ffe1e1
```

---

## 시스템 아키텍처

```mermaid
graph TB
    subgraph 입력층[입력 계층]
        CAM[USB 카메라<br/>320x240]
        TRK[트랙바 입력<br/>실시간 파라미터 조정]
        KEY[키보드 입력<br/>ESC/SPACE/L/B]
    end
    
    subgraph 처리층[처리 계층]
        IMG[이미지 처리 모듈]
        HIST[히스토그램 분석 모듈]
        DEC[방향 결정 모듈]
        SERVO[서보 제어 모듈]
    end
    
    subgraph 출력층[출력 계층]
        MOTOR[모터 제어<br/>4개 DC 모터]
        LED[LED 효과<br/>WS2812]
        BEEP[부저<br/>상태 알림]
        DISP[화면 출력<br/>4개 윈도우]
    end
    
    subgraph 하드웨어층[하드웨어 계층]
        RASP[Raspbot 하드웨어<br/>모터/서보/센서 통합]
    end
    
    CAM --> IMG
    TRK --> IMG
    TRK --> DEC
    KEY --> DEC
    
    IMG --> HIST
    HIST --> DEC
    DEC --> MOTOR
    DEC --> SERVO
    DEC --> LED
    DEC --> BEEP
    IMG --> DISP
    
    MOTOR --> RASP
    LED --> RASP
    BEEP --> RASP
    SERVO --> RASP
    
    style 입력층 fill:#e1f5e1
    style 처리층 fill:#e1f0ff
    style 출력층 fill:#fff4e1
    style 하드웨어층 fill:#ffe1e1
```

---

## 이미지 처리 파이프라인

```mermaid
flowchart TD
    A[원본 프레임<br/>320x240 BGR] --> B[ROI 영역 계산]
    B --> C[원근 변환<br/>Perspective Transform]
    C --> D[그레이스케일 변환]
    C --> E[HSV 변환]
    
    D --> F[밝기 기반 임계값<br/>회색/흰색 도로선]
    E --> G[빨간색 범위 감지<br/>HSV 0-10도, 170-180도]
    
    F --> H[회색 마스크]
    G --> I[빨간색 마스크]
    
    H --> J[마스크 결합<br/>OR 연산]
    I --> J
    
    J --> K[노이즈 제거<br/>Morphology CLOSE/OPEN]
    K --> L[최종 이진화 이미지<br/>도로선=255, 도로=0]
    
    L --> M[히스토그램 생성<br/>수직 방향 합산]
    M --> N[3등분 분석<br/>LEFT/CENTER/RIGHT]
    
    N --> O[방향 결정 알고리즘]
    
    style A fill:#e1f5e1
    style L fill:#ffe1e1
    style O fill:#fff4e1
    
    subgraph 색상감지[도로선 색상 감지]
        F
        G
    end
    
    subgraph 전처리[전처리 과정]
        B
        C
        D
        E
    end
    
    subgraph 후처리[후처리 및 분석]
        J
        K
        M
        N
    end
```

### 이미지 처리 단계별 상세 순서도

```mermaid
flowchart TD
    A[1. 원본 프레임 캡처<br/>320x240 BGR] --> B[2. ROI 영역 계산]
    B --> B1[ROI Top Y: 871/1000]
    B --> B2[ROI Bottom Y: 946/1000]
    B1 --> C[3. 사다리꼴 좌표 생성]
    B2 --> C
    C --> D[4. 원근 변환 행렬 계산]
    D --> E[5. 버드아이 뷰 변환]
    E --> F[6. HSV 색상 공간 변환]
    E --> G[6. 그레이스케일 변환]
    
    F --> H[7. 빨간색 범위 감지]
    H --> H1[범위 1: H 0-10도]
    H --> H2[범위 2: H 170-180도]
    H1 --> I[빨간색 마스크]
    H2 --> I
    
    G --> J[8. 밝기 임계값 계산]
    J --> J1[임계값 = detect_value - 30]
    J --> J2[어두운 영역 제거 < 50]
    J1 --> K[회색/흰색 마스크]
    J2 --> K
    
    I --> L[9. 마스크 결합<br/>OR 연산]
    K --> L
    L --> M[10. Morphology CLOSE<br/>작은 구멍 메우기]
    M --> N[11. Morphology OPEN<br/>작은 노이즈 제거]
    N --> O[12. 최종 이진화 이미지]
    
    O --> P[13. 히스토그램 생성<br/>수직 방향 합산]
    P --> Q[14. 3등분 분석]
    Q --> Q1[LEFT 영역 합계]
    Q --> Q2[CENTER 영역 합계]
    Q --> Q3[RIGHT 영역 합계]
    Q1 --> R[15. 방향 결정 알고리즘]
    Q2 --> R
    Q3 --> R
    
    style A fill:#e1f5e1
    style O fill:#ffe1e1
    style R fill:#fff4e1
```

### 이미지 처리 단계별 처리 시간

| 단계 | 처리 내용 | 예상 시간 | 비고 |
|------|----------|----------|------|
| 1 | 프레임 캡처 | 30ms | 카메라에서 읽기 |
| 2-3 | ROI 계산 및 좌표 생성 | 1ms | 사다리꼴 영역 |
| 4-5 | 원근 변환 | 5ms | 행렬 계산 + 변환 |
| 6 | 색상 공간 변환 | 3ms | HSV + 그레이스케일 |
| 7-8 | 도로선 감지 | 8ms | 빨간색 + 회색 마스크 |
| 9 | 마스크 결합 | 1ms | OR 연산 |
| 10-11 | Morphology 연산 | 5ms | CLOSE + OPEN |
| 12 | 이진화 완료 | - | 최종 이미지 |
| 13 | 히스토그램 생성 | 2ms | 수직 합산 |
| 14 | 3등분 분석 | 1ms | LEFT/CENTER/RIGHT |
| 15 | 방향 결정 | 1ms | 알고리즘 실행 |
| **총 시간** | **전체 처리** | **약 57ms** | **약 17-18 FPS** |

---

## 방향 결정 알고리즘

### 방향 결정 알고리즘 상세 순서도

```mermaid
flowchart TD
    A[히스토그램 수신<br/>LEFT, CENTER, RIGHT 합계] --> B[1단계: 각 영역 합계 계산]
    B --> B1[LEFT_SUM = 왼쪽 1/3 합계]
    B --> B2[CENTER_SUM = 중앙 1/3 합계]
    B --> B3[RIGHT_SUM = 오른쪽 1/3 합계]
    
    B1 --> C[2단계: 좌우 차이 계산]
    B2 --> C
    B3 --> C
    C --> C1[DIFF = abs LEFT_SUM - RIGHT_SUM]
    
    C1 --> D{3단계: DIFF > Threshold?<br/>35000}
    
    D -->|예, 차이가 큼| E{4단계: RIGHT > LEFT?}
    E -->|예, 오른쪽이 더 큼| F[LEFT 회전 결정<br/>오른쪽에 도로선 많음<br/>→ 왼쪽으로 회피]
    E -->|아니오, 왼쪽이 더 큼| G[RIGHT 회전 결정<br/>왼쪽에 도로선 많음<br/>→ 오른쪽으로 회피]
    
    D -->|아니오, 차이가 작음| H[5단계: CENTER 비율 계산]
    H --> H1[RATIO = CENTER_SUM / 전체 합계]
    H1 --> I{6단계: RATIO > 0.7?<br/>막다른 길 판단}
    
    I -->|예, 막다른 길| J[7단계: 막다른 길 처리]
    J --> J1[차량 정지<br/>car_stop]
    J1 --> J2[0.3초 대기<br/>time.sleep 0.3]
    J2 --> J3[랜덤 방향 선택<br/>random.choice LEFT/RIGHT]
    J3 --> J4[부저 2회 울림<br/>막다른 길 알림]
    J4 --> K[선택된 방향 반환]
    
    I -->|아니오, 정상| L[UP 직진 결정<br/>중앙 경로 주행 가능<br/>→ 직진]
    
    F --> M[8단계: 방향 반환]
    G --> M
    K --> M
    L --> M
    
    M --> N[9단계: 차량 제어 실행<br/>control_car direction]
    
    style A fill:#e1f5e1
    style J fill:#ffe1e1
    style N fill:#fff4e1
    style J3 fill:#fff4e1
    
    note1[교육생 과제:<br/>랜덤 대신 서보 모터로<br/>최적 경로 탐색]
    style note1 fill:#e1f0ff
```

### 방향 결정 알고리즘 단계별 설명

| 단계 | 처리 내용 | 계산식 | 판단 기준 |
|------|----------|--------|----------|
| 1 | 영역 합계 계산 | LEFT_SUM, CENTER_SUM, RIGHT_SUM | 각 영역의 픽셀 합계 |
| 2 | 좌우 차이 계산 | DIFF = \|LEFT_SUM - RIGHT_SUM\| | 절대값 차이 |
| 3 | 차이 임계값 비교 | DIFF > 35000 | 좌우 차이가 큰지 확인 |
| 4 | 좌우 비교 | RIGHT > LEFT? | 어느 쪽이 더 큰지 |
| 5 | 중앙 비율 계산 | RATIO = CENTER_SUM / 전체 | 중앙 영역 비율 |
| 6 | 막다른 길 판단 | RATIO > 0.7 | 중앙이 70% 이상 차지 |
| 7 | 막다른 길 처리 | 정지 → 대기 → 랜덤 선택 | 0.3초 대기 후 선택 |
| 8 | 방향 반환 | LEFT / RIGHT / UP | 결정된 방향 반환 |
| 9 | 차량 제어 | control_car(direction) | 모터 제어 실행 |

### 히스토그램 해석 로직 상세

```mermaid
flowchart TD
    A[이진화 이미지<br/>도로=0, 도로선=255] --> B[히스토그램 생성<br/>수직 방향 합산]
    B --> C[각 열의 픽셀 합계<br/>0~255 값들의 합]
    
    C --> D[3등분으로 분할]
    D --> D1[LEFT: 0 ~ width/3]
    D --> D2[CENTER: width/3 ~ 2*width/3]
    D --> D3[RIGHT: 2*width/3 ~ width]
    
    D1 --> E[LEFT_SUM 계산]
    D2 --> F[CENTER_SUM 계산]
    D3 --> G[RIGHT_SUM 계산]
    
    E --> H{합계 의미 해석}
    F --> H
    G --> H
    
    H --> I1[합계 낮음<br/>0에 가까움<br/>→ 검정 도로 많음<br/>→ 주행 가능 경로]
    H --> I2[합계 높음<br/>255에 가까움<br/>→ 도로선 많음<br/>→ 경계/막힘]
    
    I1 --> J[방향 판단]
    I2 --> J
    
    J --> K1[LEFT < RIGHT<br/>→ 왼쪽으로 회전]
    J --> K2[RIGHT < LEFT<br/>→ 오른쪽으로 회전]
    J --> K3[CENTER 낮음<br/>→ 직진 UP]
    J --> K4[CENTER 높음<br/>ratio > 0.7<br/>→ 막다른 길<br/>→ 랜덤 선택]
    
    style I1 fill:#e1f5e1
    style I2 fill:#ffe1e1
    style K3 fill:#e1f0ff
    style K4 fill:#fff4e1
```

### 히스토그램 값 해석 표

| 이진화 값 | 의미 | 히스토그램 합계 | 주행 가능성 | 방향 결정 |
|----------|------|----------------|------------|----------|
| 0 (검정) | 도로 | 낮음 (0에 가까움) | ✅ 주행 가능 | 해당 방향으로 이동 |
| 255 (흰색) | 도로선 | 높음 (255에 가까움) | ❌ 막힘/경계 | 해당 방향 회피 |
| LEFT_SUM < RIGHT_SUM | 왼쪽이 더 열려있음 | LEFT 낮음, RIGHT 높음 | ✅ 왼쪽 주행 가능 | LEFT 회전 |
| RIGHT_SUM < LEFT_SUM | 오른쪽이 더 열려있음 | RIGHT 낮음, LEFT 높음 | ✅ 오른쪽 주행 가능 | RIGHT 회전 |
| CENTER_SUM 낮음 | 중앙이 열려있음 | CENTER 낮음 | ✅ 직진 가능 | UP 직진 |
| CENTER_SUM 높음 (ratio > 0.7) | 중앙이 막힘 | CENTER 높음 (70% 이상) | ❌ 막다른 길 | 랜덤 LEFT/RIGHT |

---

## 주요 기능 상세

### 전체 시스템 초기화 순서도

```mermaid
flowchart TD
    A[프로그램 시작] --> B[1단계: 라이브러리 Import]
    B --> B1[import cv2, numpy, sys]
    B --> B2[import Raspbot_Lib]
    B1 --> C[2단계: 경로 설정]
    B2 --> C
    
    C --> C1[sys.path.append<br/>../lib/raspbot]
    C1 --> D[3단계: Raspbot 초기화]
    
    D --> D1[bot = Raspbot.Raspbot]
    D1 --> D2{초기화 성공?}
    D2 -->|실패| E[에러 출력 및 종료]
    D2 -->|성공| F[4단계: 카메라 초기화]
    
    F --> F1[cap = cv2.VideoCapture 0]
    F1 --> F2[해상도 설정 320x240]
    F2 --> F3[밝기/대비/채도 설정]
    F3 --> F4{카메라 성공?}
    F4 -->|실패| E
    F4 -->|성공| G[5단계: 하드웨어 초기 설정]
    
    G --> G1[LED 초기화 모드 2]
    G --> G2[부저 테스트 0.2초]
    G --> G3[서보1: 70도]
    G --> G4[서보2: 10도]
    G --> G5[모터 4개 정지]
    G1 --> H[6단계: 윈도우 생성]
    G2 --> H
    G3 --> H
    G4 --> H
    G5 --> H
    
    H --> H1[윈도우 4개 생성<br/>1_Frame, 2_transformed<br/>3_gray, 4_Processed]
    H1 --> I[7단계: 트랙바 생성]
    
    I --> I1[13개 트랙바 생성<br/>서보, ROI, 방향, 카메라<br/>모터, 이미지 처리]
    I1 --> J[초기화 완료<br/>메인 루프 시작]
    
    style A fill:#e1f5e1
    style E fill:#ffe1e1
    style J fill:#fff4e1
```

### 1. 하드웨어 초기화 기능

```mermaid
sequenceDiagram
    participant M as Main
    participant R as Raspbot
    participant C as Camera
    participant S as Servo
    participant L as LED
    
    M->>R: initialize_raspbot()
    R-->>M: bot 객체 반환
    
    M->>C: initialize_camera(320, 240)
    C->>C: 해상도 설정
    C->>C: 밝기/대비/채도 설정
    C-->>M: cap 객체 반환
    
    M->>S: setup_initial_hardware_state()
    S->>L: LED 초기화 (모드 2)
    S->>S: 부저 테스트 (0.2초)
    S->>S: 서보1: 70도 (좌우)
    S->>S: 서보2: 10도 (상하)
    S->>S: 모터 4개 정지
    S-->>M: 초기화 완료
```

### 2. 차량 제어 기능 상세

```mermaid
stateDiagram-v2
    [*] --> FORWARD: direction == "UP"
    [*] --> TURN_LEFT: direction == "LEFT"
    [*] --> TURN_RIGHT: direction == "RIGHT"
    [*] --> STOP: 막다른 길
    
    FORWARD --> LED_EFFECT_1: set_led_effect(1)
    TURN_LEFT --> LED_EFFECT_3: set_led_effect(3)
    TURN_RIGHT --> LED_EFFECT_3: set_led_effect(3)
    
    state FORWARD {
        [*] --> M0: motor_0 = +speed
        [*] --> M1: motor_1 = +speed
        [*] --> M2: motor_2 = +speed
        [*] --> M3: motor_3 = +speed
    }
    
    state TURN_LEFT {
        [*] --> M0: motor_0 = -speed_down
        [*] --> M1: motor_1 = -speed_down
        [*] --> M2: motor_2 = +speed_up
        [*] --> M3: motor_3 = +speed_up
    }
    
    state TURN_RIGHT {
        [*] --> M0: motor_0 = +speed_up
        [*] --> M1: motor_1 = +speed_up
        [*] --> M2: motor_2 = -speed_down
        [*] --> M3: motor_3 = -speed_down
    }
    
    LED_EFFECT_1 --> [*]
    LED_EFFECT_3 --> [*]
    STOP --> [*]
```

### 3. 막다른 길 감지 및 랜덤 방향 선택 알고리즘

```mermaid
flowchart LR
    A[decide_direction 호출] --> B[1단계: 히스토그램 3등분 분석]
    B --> B1[LEFT_SUM 계산]
    B --> B2[CENTER_SUM 계산]
    B --> B3[RIGHT_SUM 계산]
    
    B1 --> C[2단계: 중앙 비율 계산]
    B2 --> C
    B3 --> C
    C --> C1[center_ratio = CENTER_SUM / 전체 합계]
    
    C1 --> D{3단계: 막다른 길 판단<br/>center_ratio > 0.7?}
    
    D -->|예, 막다른 길| E[4단계: 막다른 길 처리]
    D -->|아니오, 정상| F[5단계: 정상 방향 분석]
    
    E --> E1[DEBUG 메시지 출력<br/>Dead end detected!]
    E1 --> E2[차량 정지<br/>car_stop]
    E2 --> E3[0.3초 대기<br/>time.sleep 0.3]
    E3 --> E4[랜덤 방향 선택<br/>random.choice LEFT/RIGHT]
    E4 --> E5[DEBUG 메시지<br/>Selected direction: LEFT/RIGHT]
    E5 --> E6[부저 2회 울림]
    E6 --> E61[부저 ON 0.1초]
    E61 --> E62[부저 OFF 0.1초]
    E62 --> E63[부저 ON 0.1초]
    E63 --> E64[부저 OFF]
    E64 --> G[랜덤 방향 반환]
    
    F --> F1[LEFT/RIGHT 차이 계산<br/>DIFF = abs LEFT - RIGHT]
    F1 --> F2{DIFF > Threshold?}
    F2 -->|예| F3{RIGHT > LEFT?}
    F2 -->|아니오| F4[UP 직진 반환]
    F3 -->|예| F5[LEFT 회전 반환]
    F3 -->|아니오| F6[RIGHT 회전 반환]
    
    G --> H[방향 반환 완료]
    F4 --> H
    F5 --> H
    F6 --> H
    
    H --> I[control_car direction 호출]
    
    style E fill:#ffe1e1
    style G fill:#fff4e1
    style H fill:#e1f5e1
```

### 막다른 길 처리 단계별 상세표

| 단계 | 처리 내용 | 함수/명령 | 파라미터 | 시간 |
|------|----------|-----------|---------|------|
| 1 | 히스토그램 분석 | analyze_histogram() | histogram | 즉시 |
| 2 | 중앙 비율 계산 | center_ratio = CENTER / 전체 | - | 즉시 |
| 3 | 막다른 길 판단 | if center_ratio > 0.7 | 0.7 | 즉시 |
| 4-1 | DEBUG 출력 | print("Dead end detected!") | - | 즉시 |
| 4-2 | 차량 정지 | car_stop() | - | 즉시 |
| 4-3 | 대기 | time.sleep(0.3) | 0.3초 | 0.3초 |
| 4-4 | 랜덤 선택 | random.choice(["LEFT", "RIGHT"]) | - | 즉시 |
| 4-5 | DEBUG 출력 | print("Selected:", direction) | - | 즉시 |
| 4-6 | 부저 1회 | bot.Beep(0.1) | 0.1초 | 0.1초 |
| 4-7 | 대기 | time.sleep(0.1) | 0.1초 | 0.1초 |
| 4-8 | 부저 2회 | bot.Beep(0.1) | 0.1초 | 0.1초 |
| **총 시간** | **막다른 길 처리** | - | - | **약 0.6초** |

### 교육생 실습: 서보 모터 대체 경로 탐색 알고리즘

```mermaid
flowchart TD
    A[막다른 길 감지<br/>center_ratio > 0.7] --> B[1단계: 차량 정지]
    B --> B1[car_stop 호출<br/>모든 모터 정지]
    B1 --> C[2단계: 서보 모터 회전]
    
    C --> C1[서보1: 70도 → 180도<br/>뒤쪽 확인]
    C --> C2[서보2: 10도 → 100도<br/>시야 확보]
    C1 --> D[0.5초 대기<br/>서보 안정화]
    C2 --> D
    
    D --> E[3단계: 새 프레임 캡처]
    E --> E1[cap.read<br/>뒤쪽 방향 프레임]
    E1 --> F[4단계: 이미지 처리]
    
    F --> F1[process_frame 호출<br/>ROI, 원근변환, 이진화]
    F1 --> G[5단계: 히스토그램 분석]
    
    G --> G1[히스토그램 생성<br/>수직 합산]
    G1 --> G2[3등분 분석<br/>LEFT, CENTER, RIGHT]
    G2 --> H[6단계: 최소값 찾기]
    
    H --> H1[MIN = min LEFT, CENTER, RIGHT<br/>도로선이 가장 적은 영역]
    H1 --> I[7단계: 최적 방향 결정]
    
    I --> I1{MIN == LEFT?}
    I --> I2{MIN == RIGHT?}
    I --> I3{MIN == CENTER?}
    
    I1 -->|예| J1[LEFT 반환]
    I2 -->|예| J2[RIGHT 반환]
    I3 -->|예| J3[UP 반환]
    
    J1 --> K[8단계: 서보 원위치]
    J2 --> K
    J3 --> K
    
    K --> K1[서보1: 180도 → 70도]
    K --> K2[서보2: 100도 → 10도]
    K1 --> L[최적 방향 반환]
    K2 --> L
    
    style A fill:#ffe1e1
    style H1 fill:#e1f5e1
    style L fill:#fff4e1
```

**현재 문제점**: 막다른 길에서 랜덤으로 방향을 선택하므로 비효율적

**개선 목표**: 서보 모터를 활용하여 실제로 주행 가능한 경로를 찾아 선택

### 구현 단계 상세표

| 단계 | 처리 내용 | 함수/명령 | 파라미터 | 예상 시간 |
|------|----------|-----------|---------|----------|
| 1 | 차량 정지 | car_stop() | - | 즉시 |
| 2-1 | 서보1 회전 | bot.Ctrl_Servo(1, 180) | 180도 | 0.3초 |
| 2-2 | 서보2 조정 | bot.Ctrl_Servo(2, 100) | 100도 | 0.3초 |
| 2-3 | 안정화 대기 | time.sleep(0.5) | 0.5초 | 0.5초 |
| 3 | 프레임 캡처 | cap.read() | - | 0.03초 |
| 4 | 이미지 처리 | process_frame() | detect_value, ROI | 0.05초 |
| 5-1 | 히스토그램 생성 | np.sum(axis=0) | - | 0.002초 |
| 5-2 | 3등분 분석 | analyze_histogram() | - | 0.001초 |
| 6 | 최소값 찾기 | min(LEFT, CENTER, RIGHT) | - | 즉시 |
| 7 | 방향 결정 | if-elif-else | - | 즉시 |
| 8-1 | 서보1 원위치 | bot.Ctrl_Servo(1, 70) | 70도 | 0.3초 |
| 8-2 | 서보2 원위치 | bot.Ctrl_Servo(2, 10) | 10도 | 0.3초 |
| **총 시간** | **전체 처리** | - | - | **약 1.5초** |

```python
# 교육생 구현 예시 (참고용)
def rotate_servo_and_check_direction(detect_value, roi_top_y, roi_bottom_y):
    # 1. 서보 회전
    bot.Ctrl_Servo(1, 180)
    bot.Ctrl_Servo(2, 100)
    time.sleep(0.5)
    
    # 2. 프레임 캡처 및 처리
    ret, frame = cap.read()
    processed_frame = process_frame(frame, detect_value, roi_top_y, roi_bottom_y)
    histogram = np.sum(processed_frame, axis=0)
    
    # 3. 3등분 분석
    left_sum, center_sum, right_sum, _, _, _ = analyze_histogram(histogram)
    
    # 4. 서보 원위치
    bot.Ctrl_Servo(1, 70)
    bot.Ctrl_Servo(2, 10)
    
    # 5. 최소값 방향 반환
    min_sum = min(left_sum, center_sum, right_sum)
    if min_sum == left_sum:
        return "LEFT"
    elif min_sum == right_sum:
        return "RIGHT"
    else:
        return "UP"
```

### 4. 키보드 입력 처리

```mermaid
graph TD
    A[키 입력 대기] --> B{키 확인}
    B -->|ESC 27| C[프로그램 종료]
    B -->|SPACE 32| D[일시정지]
    B -->|L 108| E[LED 토글]
    B -->|B 98| F[부저 테스트]
    B -->|없음| G[계속 실행]
    
    D --> H[차량 정지]
    H --> I[키 입력 대기]
    I --> G
    
    E --> J{LED 상태?}
    J -->|ON| K[LED OFF]
    J -->|OFF| L[LED ON]
    K --> G
    L --> G
    
    F --> M[부저 0.1초 울림]
    M --> G
    
    C --> N[cleanup_and_exit]
    
    style C fill:#ffe1e1
    style G fill:#e1f5e1
    style N fill:#ff9999
```

---

## 하드웨어 구성

```mermaid
graph TB
    subgraph Raspbot[Raspbot v2 메인보드]
        CPU[Raspberry Pi]
    end
    
    subgraph 모터시스템[모터 시스템]
        M0[모터 0<br/>왼쪽 앞]
        M1[모터 1<br/>왼쪽 뒤]
        M2[모터 2<br/>오른쪽 앞]
        M3[모터 3<br/>오른쪽 뒤]
    end
    
    subgraph 서보시스템[서보 모터 시스템]
        S1[서보 1<br/>좌우 회전<br/>0-180도]
        S2[서보 2<br/>상하 회전<br/>0-110도]
    end
    
    subgraph 입력장치[입력 장치]
        CAM[USB 카메라<br/>320x240]
    end
    
    subgraph 출력장치[출력 장치]
        LED[WS2812 LED<br/>RGB 라이트바]
        BEEP[부저<br/>상태 알림]
    end
    
    CPU --> M0
    CPU --> M1
    CPU --> M2
    CPU --> M3
    CPU --> S1
    CPU --> S2
    CPU --> LED
    CPU --> BEEP
    CAM --> CPU
    
    style CPU fill:#e1f0ff
    style 모터시스템 fill:#e1f5e1
    style 서보시스템 fill:#fff4e1
    style 입력장치 fill:#f0e1ff
    style 출력장치 fill:#ffe1f0
```

### 모터 제어 알고리즘 상세

```mermaid
flowchart TD
    A[방향 결정<br/>LEFT/UP/RIGHT] --> B{방향 확인}
    
    B -->|UP 직진| C[전진 제어]
    C --> C1[M0: +speed_up<br/>M1: +speed_up<br/>M2: +speed_up<br/>M3: +speed_up]
    C1 --> D[모든 모터 동일 속도]
    
    B -->|LEFT 좌회전| E[좌회전 제어]
    E --> E1[왼쪽 모터: -speed_down<br/>뒤로 이동]
    E --> E2[오른쪽 모터: +speed_up<br/>앞으로 이동]
    E1 --> F[왼쪽 뒤로, 오른쪽 앞으로]
    E2 --> F
    
    B -->|RIGHT 우회전| G[우회전 제어]
    G --> G1[왼쪽 모터: +speed_up<br/>앞으로 이동]
    G --> G2[오른쪽 모터: -speed_down<br/>뒤로 이동]
    G1 --> H[왼쪽 앞으로, 오른쪽 뒤로]
    G2 --> H
    
    D --> I[LED 효과 적용]
    F --> I
    H --> I
    
    I --> I1[UP: LED 효과 1<br/>직진 표시]
    I --> I2[LEFT/RIGHT: LED 효과 3<br/>회전 표시]
    
    style C fill:#e1f5e1
    style E fill:#fff4e1
    style G fill:#e1f0ff
```

### 모터 제어 매핑 상세표

| 모터 번호 | 위치 | 전진 (UP) | 좌회전 (LEFT) | 우회전 (RIGHT) | 속도 값 |
|---------|------|-----------|--------------|--------------|---------|
| Motor 0 | 왼쪽 앞 | +speed_up | -speed_down | +speed_up | 기본: 40/-30 |
| Motor 1 | 왼쪽 뒤 | +speed_up | -speed_down | +speed_up | 기본: 40/-30 |
| Motor 2 | 오른쪽 앞 | +speed_up | +speed_up | -speed_down | 기본: 40/-30 |
| Motor 3 | 오른쪽 뒤 | +speed_up | +speed_up | -speed_down | 기본: 40/-30 |

**제어 원리**:
- **전진**: 모든 모터가 같은 방향으로 같은 속도
- **좌회전**: 왼쪽 모터는 뒤로, 오른쪽 모터는 앞으로 → 왼쪽으로 회전
- **우회전**: 왼쪽 모터는 앞으로, 오른쪽 모터는 뒤로 → 오른쪽으로 회전

---

## 설정 파라미터

### 주요 파라미터 구성도

```mermaid
mindmap
  root((설정 파라미터))
    속도 설정
      DEFAULT_SPEED_UP: 40
      DEFAULT_SPEED_DOWN: 30
      범위: -255 ~ 255
    라인 검출
      DEFAULT_DETECT_VALUE: 120
      임계값 범위: 0 ~ 150
      밝기 기반 감지
    이미지 처리
      DEFAULT_BRIGHTNESS: 0
      DEFAULT_CONTRAST: 0
      Saturation: 50
      Exposure: 100
    방향 판단
      DIRECTION_THRESHOLD: 35000
      UP_THRESHOLD: 220000
      좌우 차이 비교
    서보 각도
      SERVO_1: 70도
        좌우 회전
        0-180도 범위
      SERVO_2: 10도
        상하 회전
        0-110도 범위
    디버그 옵션
      DEBUG_MODE: True
      USE_LED_EFFECTS: True
      USE_BEEP: True
      BEEP_ON_TURN: False
```

### 트랙바 파라미터 상세표

```mermaid
graph TD
    A[트랙바 파라미터] --> B[서보 제어]
    A --> C[ROI 설정]
    A --> D[방향 판단]
    A --> E[카메라 설정]
    A --> F[모터 속도]
    A --> G[이미지 처리]
    
    B --> B1[Servo_1_Angle: 0-180<br/>기본 70도]
    B --> B2[Servo_2_Angle: 0-110<br/>기본 10도]
    
    C --> C1[ROI_Top_Y: 0-1000<br/>기본 871]
    C --> C2[ROI_Bottom_Y: 0-1000<br/>기본 946]
    
    D --> D1[Direction_Threshold: 0-500000<br/>기본 35000]
    D --> D2[Up_Threshold: 0-500000<br/>기본 220000]
    
    E --> E1[Brightness: 0-100<br/>기본 0]
    E --> E2[Contrast: 0-100<br/>기본 0]
    E --> E3[Saturation: 0-100<br/>기본 0]
    E --> E4[Gain: 0-100<br/>기본 0]
    
    F --> F1[Motor_Up_Speed: 0-255<br/>기본 40]
    F --> F2[Motor_Down_Speed: 0-255<br/>기본 30]
    
    G --> G1[Detect_Value: 0-150<br/>기본 120]
```

| 카테고리 | 파라미터 | 범위 | 기본값 | 단위 | 설명 |
|---------|---------|------|--------|------|------|
| **서보 제어** | Servo_1_Angle | 0-180 | 70 | 도 | 카메라 좌우 회전 각도 |
| | Servo_2_Angle | 0-110 | 10 | 도 | 카메라 상하 회전 각도 |
| **ROI 설정** | ROI_Top_Y | 0-1000 | 871 | 비율 | 관심 영역 상단 Y 좌표 (0.871) |
| | ROI_Bottom_Y | 0-1000 | 946 | 비율 | 관심 영역 하단 Y 좌표 (0.946) |
| **방향 판단** | Direction_Threshold | 0-500000 | 35000 | 픽셀 합계 | 좌우 차이 임계값 (이상이면 회전) |
| | Up_Threshold | 0-500000 | 220000 | 픽셀 합계 | 직진 판단 임계값 (이하이면 직진) |
| **카메라 설정** | Brightness | 0-100 | 0 | % | 카메라 밝기 조절 |
| | Contrast | 0-100 | 0 | % | 카메라 대비 조절 |
| | Saturation | 0-100 | 0 | % | 카메라 채도 조절 |
| | Gain | 0-100 | 0 | % | 카메라 게인 조절 |
| **모터 속도** | Motor_Up_Speed | 0-255 | 40 | 속도 | 전진/회전 고속 (양수) |
| | Motor_Down_Speed | 0-255 | 30 | 속도 | 회전 저속 (음수) |
| **이미지 처리** | Detect_Value | 0-150 | 120 | 임계값 | 도로선 검출 밝기 임계값 |

### 파라미터 튜닝 가이드

| 상황 | 조정할 파라미터 | 권장값 | 효과 |
|------|---------------|--------|------|
| 도로선이 잘 안 보임 | Detect_Value | 100-110 | 더 낮은 밝기까지 감지 |
| 도로선이 너무 많이 감지됨 | Detect_Value | 130-150 | 더 높은 밝기만 감지 |
| 회전이 너무 민감함 | Direction_Threshold | 50000-100000 | 더 큰 차이에서만 회전 |
| 회전이 너무 둔함 | Direction_Threshold | 20000-30000 | 작은 차이에서도 회전 |
| 직진이 어려움 | Up_Threshold | 250000-300000 | 더 높은 값에서 직진 |
| 막다른 길을 못 찾음 | center_ratio 임계값 | 0.6-0.65 | 코드에서 수정 필요 |
| 카메라가 너무 어두움 | Brightness | 20-40 | 밝기 증가 |
| 카메라가 너무 밝음 | Brightness | 0, Contrast 증가 | 대비 조절 |

---

## 윈도우 출력 구성

```mermaid
graph LR
    subgraph 윈도우구성[화면 출력 구성]
        W1[1_Frame<br/>원본 프레임 + ROI 영역]
        W2[2_frame_transformed<br/>원근 변환 결과]
        W3[3_gray_frame<br/>그레이스케일 변환]
        W4[4_Processed Frame<br/>최종 이진화 + 방향 표시]
        W5[Camera Settings<br/>트랙바 컨트롤]
    end
    
    subgraph 정보표시[4번 윈도우 표시 정보]
        I1[방향: LEFT/UP/RIGHT]
        I2[히스토그램 합계: L/C/R]
        I3[비율: Low=주행가능]
        I4[3등분 구분선]
        I5[영역 라벨: LEFT/CENTER/RIGHT]
    end
    
    W4 --> I1
    W4 --> I2
    W4 --> I3
    W4 --> I4
    W4 --> I5
    
    style W4 fill:#e1f0ff
    style W5 fill:#fff4e1
```

---

## 도로선 감지 알고리즘 상세

### 도로선 감지 알고리즘 상세 순서도

```mermaid
flowchart TD
    A[원근 변환된 프레임<br/>320x240] --> B[1단계: 색상 공간 변환]
    B --> B1[HSV 변환<br/>색상 정보 추출]
    B --> B2[그레이스케일 변환<br/>밝기 정보 추출]
    
    B1 --> C[2단계: 빨간색 감지]
    C --> C1[범위 1: H 0-10도<br/>S 70-255, V 50-255]
    C --> C2[범위 2: H 170-180도<br/>S 70-255, V 50-255]
    C1 --> D[빨간색 마스크 1<br/>cv2.inRange]
    C2 --> E[빨간색 마스크 2<br/>cv2.inRange]
    D --> F[빨간색 마스크 결합<br/>cv2.bitwise_or]
    E --> F
    
    B2 --> G[3단계: 회색/흰색 감지]
    G --> G1[밝기 임계값 계산<br/>threshold = detect_value - 30]
    G --> G2[어두운 영역 제거<br/>밝기 < 50]
    G1 --> H[밝은 영역 마스크<br/>cv2.threshold]
    G2 --> I[어두운 영역 마스크<br/>cv2.threshold]
    H --> J[회색/흰색 마스크<br/>밝은 영역 AND NOT 어두운 영역]
    I --> J
    
    F --> K[4단계: 마스크 결합]
    J --> K
    K --> L[최종 마스크<br/>빨간색 OR 회색/흰색<br/>cv2.bitwise_or]
    
    L --> M[5단계: 노이즈 제거]
    M --> M1[Morphology CLOSE<br/>커널 3x3, 반복 1회<br/>작은 구멍 메우기]
    M1 --> M2[Morphology OPEN<br/>커널 3x3, 반복 1회<br/>작은 노이즈 제거]
    M2 --> N[최종 이진화 이미지<br/>도로선=255, 도로=0]
    
    style A fill:#e1f5e1
    style N fill:#ffe1e1
    style L fill:#fff4e1
```

### 도로선 감지 단계별 상세표

| 단계 | 처리 내용 | 함수/연산 | 파라미터 | 결과 |
|------|----------|-----------|---------|------|
| 1 | 색상 공간 변환 | cv2.cvtColor | BGR→HSV, BGR→GRAY | HSV, 그레이스케일 이미지 |
| 2-1 | 빨간색 범위 1 | cv2.inRange | H:0-10, S:70-255, V:50-255 | 빨간색 마스크 1 |
| 2-2 | 빨간색 범위 2 | cv2.inRange | H:170-180, S:70-255, V:50-255 | 빨간색 마스크 2 |
| 2-3 | 빨간색 결합 | cv2.bitwise_or | 마스크1, 마스크2 | 통합 빨간색 마스크 |
| 3-1 | 밝기 임계값 | cv2.threshold | threshold = detect_value - 30 | 밝은 영역 마스크 |
| 3-2 | 어두운 영역 제거 | cv2.threshold | threshold < 50 | 어두운 영역 마스크 |
| 3-3 | 회색/흰색 마스크 | 논리 연산 | 밝은 AND NOT 어두운 | 회색/흰색 마스크 |
| 4 | 마스크 결합 | cv2.bitwise_or | 빨간색 OR 회색/흰색 | 최종 마스크 |
| 5-1 | Morphology CLOSE | cv2.morphologyEx | 커널 3x3, 반복 1 | 구멍 메움 |
| 5-2 | Morphology OPEN | cv2.morphologyEx | 커널 3x3, 반복 1 | 노이즈 제거 |
| 최종 | 이진화 완료 | - | - | 도로선=255, 도로=0 |

### 도로선 감지 특징 비교표

| 구분 | 검출 대상 | 제외 대상 | 처리 방법 |
|------|----------|----------|----------|
| **빨간색 도로선** | ✅ HSV 색상 공간 활용 | ❌ 다른 색상 | cv2.inRange (2개 범위) |
| **회색/흰색 도로선** | ✅ 밝기 기준 감지 | ❌ 어두운 영역 (< 50) | cv2.threshold |
| **반사된 부분** | ✅ 밝은 영역 포함 | ❌ 너무 어두운 배경 | 임계값 조정 |
| **노이즈** | - | ❌ 작은 노이즈 | Morphology OPEN |
| **구멍** | - | ❌ 작은 구멍 | Morphology CLOSE |

---

## 성능 최적화 전략

```mermaid
flowchart TD
    A[성능 최적화 전략] --> B[이미지 처리 최적화]
    A --> C[연산 최적화]
    A --> D[하드웨어 최적화]
    
    B --> B1[해상도 제한<br/>320x240 고정]
    B --> B2[ROI 영역만 처리<br/>관심 영역 한정]
    B --> B3[Morphology 최소화<br/>3x3 커널, 반복 1회]
    B --> B4[색상 변환 최적화<br/>필요한 변환만 수행]
    
    C --> C1[히스토그램 1회 계산<br/>재사용]
    C --> C2[3등분 분석<br/>단순 합계 비교]
    C --> C3[Early Return<br/>빠른 결정]
    C --> C4[NumPy 벡터 연산<br/>루프 최소화]
    
    D --> D1[서보 이동 최소화<br/>필요 시에만]
    D --> D2[모터 직접 제어<br/>중간 레이어 없음]
    D --> D3[LED/부저 선택적 사용<br/>옵션으로 제어]
    D --> D4[프레임 스킵 없음<br/>모든 프레임 처리]
    
    style B1 fill:#e1f5e1
    style C2 fill:#e1f0ff
    style D2 fill:#fff4e1
```

### 성능 최적화 방법 비교표

| 최적화 영역 | 방법 | 효과 | 구현 난이도 | 적용 여부 |
|------------|------|------|------------|----------|
| **이미지 처리** | 해상도 제한 320x240 | 처리량 75% 감소 | 쉬움 | ✅ 적용됨 |
| | ROI 영역만 처리 | 처리량 30% 감소 | 쉬움 | ✅ 적용됨 |
| | Morphology 최소화 | 처리 시간 50% 감소 | 쉬움 | ✅ 적용됨 |
| **연산** | 히스토그램 1회 계산 | 중복 계산 제거 | 쉬움 | ✅ 적용됨 |
| | 3등분 단순 비교 | 복잡도 O(1) | 쉬움 | ✅ 적용됨 |
| | NumPy 벡터 연산 | Python 루프 제거 | 중간 | ✅ 적용됨 |
| **하드웨어** | 서보 이동 최소화 | 지연 시간 감소 | 쉬움 | ✅ 적용됨 |
| | 모터 직접 제어 | 오버헤드 제거 | 쉬움 | ✅ 적용됨 |
| | LED/부저 옵션 | 불필요한 연산 제거 | 쉬움 | ✅ 적용됨 |
| **추가 가능** | 멀티스레딩 | 병렬 처리 | 어려움 | ❌ 미적용 |
| | GPU 가속 | OpenCV GPU | 어려움 | ❌ 미적용 |
| | 프레임 버퍼링 | 지연 시간 감소 | 중간 | ❌ 미적용 |

---

## 에러 처리 및 안전 장치

```mermaid
sequenceDiagram
    participant M as Main
    participant H as Hardware
    participant C as Camera
    participant E as Error Handler
    
    M->>H: 초기화 시도
    alt 초기화 실패
        H-->>E: Exception 발생
        E->>E: 에러 메시지 출력
        E->>M: sys.exit(1)
    else 초기화 성공
        H-->>M: 정상 진행
    end
    
    M->>C: 프레임 읽기
    alt 프레임 읽기 실패
        C-->>M: ret = False
        M->>E: 에러 처리
        E->>M: 루프 종료
    else 프레임 읽기 성공
        C-->>M: frame 반환
    end
    
    M->>M: 메인 루프 실행
    alt KeyboardInterrupt
        M-->>E: Ctrl+C 감지
        E->>E: "Interrupted by user"
    else 일반 Exception
        M-->>E: 예외 발생
        E->>E: Traceback 출력
    end
    
    E->>M: finally 블록 실행
    M->>M: cleanup_and_exit()
    Note over M: 모터 정지<br/>LED 끄기<br/>서보 원위치<br/>카메라 해제
```

---

## 실행 환경 및 요구사항

### 시스템 요구사항

```mermaid
graph TB
    subgraph 하드웨어[하드웨어 요구사항]
        H1[Raspberry Pi<br/>라즈베리 파이]
        H2[Raspbot v2<br/>메인보드]
        H3[USB 카메라<br/>320x240 이상]
        H4[DC 모터 4개]
        H5[서보 모터 2개]
    end
    
    subgraph 소프트웨어[소프트웨어 요구사항]
        S1[Python 3.x]
        S2[OpenCV cv2]
        S3[NumPy]
        S4[Raspbot_Lib]
    end
    
    subgraph 환경설정[환경 설정]
        E1[라이브러리 경로<br/>../lib/raspbot]
        E2[카메라 권한]
        E3[GPIO 권한]
    end
    
    H1 --> S1
    H2 --> S4
    H3 --> S2
    S1 --> S2
    S1 --> S3
    S1 --> S4
    S4 --> E1
    S2 --> E2
    S4 --> E3
    
    style H2 fill:#e1f0ff
    style S1 fill:#e1f5e1
    style E1 fill:#fff4e1
```

---

## 향후 개선 방향

```mermaid
mindmap
  root((개선 방향))
    교육생 실습 과제
      서보 모터 대체 경로 탐색
        랜덤 선택 → 지능형 선택
        180도 회전 후 분석
        최적 경로 자동 결정
      막다른 길 고급 알고리즘
        다중 시도 로직
        이전 경로 기억
    알고리즘 개선
      딥러닝 기반 라인 검출
      차선 예측 알고리즘
      장애물 회피 로직
    성능 최적화
      멀티스레딩 적용
      GPU 가속 활용
      프레임 버퍼링
    기능 추가
      초음파 센서 통합
      신호등 인식
      주차 기능
      자동 속도 조절
    안정성 향상
      PID 제어 도입
      칼만 필터 적용
      예외 처리 강화
    사용성 개선
      웹 인터페이스
      설정 파일 저장
      로그 기록 기능
```

---

## 디버그 팁

### 주요 디버그 포인트

1. **이미지 처리 확인**
   - 4개 윈도우로 각 단계 시각화
   - ROI 영역이 적절한지 확인
   - 도로선이 제대로 감지되는지 확인

2. **히스토그램 분석**
   - DEBUG_MODE를 True로 설정
   - 콘솔에서 LEFT/CENTER/RIGHT 값 확인
   - 비율(ratio)이 적절한지 검토

3. **방향 결정 로직**
   - direction_threshold 값 조정
   - center_ratio 임계값 튜닝 (기본 0.7)
   - 막다른 길 감지 조건 확인

4. **막다른 길 감지**
   - center_ratio > 0.7일 때 감지됨
   - 부저 2회 울림으로 확인
   - 콘솔에서 "Dead end detected!" 메시지 확인
   - 랜덤 방향 선택 로그 확인

5. **차량 제어**
   - 모터 속도 조정 (up_speed, down_speed)
   - LED 효과로 상태 확인
   - 부저로 방향 전환 및 막다른 길 확인

6. **교육생 과제 디버깅**
   - 서보 모터 회전 각도 확인 (180도)
   - 프레임 캡처 타이밍 조정
   - 히스토그램 분석 결과 검증
   - 최적 경로 선택 로직 테스트

---

## 참고 자료

### 관련 문서
- `autoplot_설명서.md`: 기본 사용 설명서
- `QUICK_START.md`: 빠른 시작 가이드
- `TUNING_GUIDE.md`: 파라미터 튜닝 가이드

### 주요 라이브러리 문서
- OpenCV 공식 문서: https://docs.opencv.org/
- NumPy 공식 문서: https://numpy.org/doc/
- Raspbot 라이브러리: `/lib/raspbot/`

---

**작성일**: 2025-11-30  
**최종 수정일**: 2025-11-30  
**버전**: 1.1  
**작성자**: AI Coding Assistant  
**소스 파일**: `0_autoplot___test.py`

### 변경 이력
- **v1.1 (2025-11-30)**: 막다른 길 감지 시 랜덤 방향 선택 기능 추가, 서보 모터 대체 경로 탐색을 교육생 실습 과제로 이동
- **v1.0 (2025-11-30)**: 초기 문서 작성

