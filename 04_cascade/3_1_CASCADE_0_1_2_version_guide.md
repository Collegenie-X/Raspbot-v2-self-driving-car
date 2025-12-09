# 🎥 Cascade 카메라 프로그램 가이드

> Raspbot 자율주행 자동차의 카메라 기반 객체 감지 시스템  
> 단계별 학습 및 기능 비교 문서

---

## 📑 목차

1. [개요](#-개요)
2. [파일 구조 및 단계별 설명](#-파일-구조-및-단계별-설명)
3. [기능 비교표](#-기능-비교표)
4. [시스템 아키텍처](#-시스템-아키텍처)
5. [단계별 순서도](#-단계별-순서도)
6. [핵심 알고리즘](#-핵심-알고리즘)
7. [사용법](#-사용법)
8. [트러블슈팅](#-트러블슈팅)

---

## 📋 개요

이 프로젝트는 **3단계 학습 구조**로 설계되어 있습니다:

| 단계 | 파일명 | 학습 목표 |
|:---:|--------|----------|
| **0단계** | `0_camera_color_rect.py` | 카메라 기본 설정 및 그레이스케일 변환 |
| **1단계** | `1_camera_weight.py` | RGB 가중치 기반 커스텀 그레이스케일 |
| **2단계** | `2_object_camera_haarcascade.py` | Haar Cascade 객체 감지 |

```mermaid
flowchart LR
    A[0단계<br/>기본 카메라] --> B[1단계<br/>가중치 변환]
    B --> C[2단계<br/>객체 감지]
    
    style A fill:#e1f5fe,color:#111
    style B fill:#fff3e0,color:#111
    style C fill:#e8f5e9,color:#111
```

---

## 📁 파일 구조 및 단계별 설명

### 📷 0단계: `0_camera_color_rect.py`

**목적**: 카메라 및 서보모터 기본 설정 테스트

```mermaid
flowchart TB
    subgraph 초기화
        A[카메라 초기화] --> B[Raspbot 초기화]
        B --> C[서보모터 초기 위치]
        C --> D[UI 트랙바 생성]
    end
    
    subgraph 메인루프
        E[트랙바 값 읽기] --> F[카메라 설정 적용]
        F --> G[서보모터 제어]
        G --> H[프레임 읽기]
        H --> I[그레이스케일 변환]
        I --> J[화면 표시]
        J --> K{키 입력?}
        K -->|SPACE| L[이미지 저장]
        K -->|ESC| M[종료]
        K -->|기타| E
    end
    
    D --> E
    L --> E
```

**핵심 기능**:
- 카메라 해상도: 320×240
- OpenCV 기본 그레이스케일 변환 (`cv2.COLOR_BGR2GRAY`)
- 트랙바: 서보 각도(2개), 카메라 설정(4개)

**소스 코드 - 그레이스케일 변환**:
```python
# 기본 OpenCV 그레이스케일 변환
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
```

---

### ⚖️ 1단계: `1_camera_weight.py`

**목적**: RGB 가중치 기반 커스텀 그레이스케일 변환

```mermaid
flowchart TB
    subgraph RGB_가중치_변환
        A[입력 이미지 BGR] --> B[RGB 가중치 정규화]
        B --> C[R 채널 × R가중치]
        B --> D[G 채널 × G가중치]
        B --> E[B 채널 × B가중치]
        C --> F[가중 합산]
        D --> F
        E --> F
        F --> G[출력 그레이스케일]
    end
```

**핵심 기능**:
- RGB 채널별 가중치 조절 (0-100)
- 커스텀 그레이스케일 생성
- 특정 색상 강조/억제 가능

**소스 코드 - 가중치 그레이스케일 변환**:
```python
def weighted_grayscale_conversion(image, r_weight, g_weight, b_weight):
    """
    RGB 가중치를 사용하여 그레이스케일 이미지로 변환합니다.
    """
    sum_weight = r_weight + g_weight + b_weight
    
    # 가중치 합이 0이면 기본값 사용
    if sum_weight == 0:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 가중치를 0-1 범위로 정규화
    r_norm = r_weight / sum_weight
    g_norm = g_weight / sum_weight
    b_norm = b_weight / sum_weight
    
    # BGR 순서로 가중치 적용 (OpenCV는 BGR 사용)
    weighted_rg = cv2.addWeighted(image[:, :, 2], r_norm, image[:, :, 1], g_norm, 0)
    weighted_result = cv2.addWeighted(weighted_rg, 1.0, image[:, :, 0], b_norm, 0)
    
    return weighted_result
```

---

### 🎯 2단계: `2_object_camera_haarcascade.py`

**목적**: Haar Cascade 기반 실시간 객체 감지

```mermaid
flowchart TB
    subgraph 초기화
        A[카메라 초기화<br/>640×480] --> B[Cascade 분류기 로드]
        B --> C[Raspbot 초기화]
        C --> D[LED/부저 초기화]
        D --> E[UI 트랙바 생성]
    end
    
    subgraph 객체감지_루프
        F[프레임 읽기] --> G[가중치 그레이스케일]
        G --> H{감지 소스?}
        H -->|0: Frame| I[컬러 입력]
        H -->|1: Gray| J[그레이스케일 입력]
        I --> K[Haar Cascade 감지]
        J --> K
        K --> L[감지 결과 그리기]
        L --> M[LED Bar 제어]
        M --> N[부저 제어]
        N --> O[화면 표시]
    end
    
    E --> F
    O --> F
```

**핵심 기능**:
- 고해상도 카메라: 640×480
- Haar Cascade 객체 감지
- LED Bar 알림 (감지 수에 따라)
- 부저 알림 (삐익삐익)
- 감지 소스 선택 (컬러/그레이스케일)

**소스 코드 - 객체 감지**:
```python
def detect_objects(cascade, gray_image):
    """
    Haar Cascade를 사용하여 객체를 감지합니다.
    """
    # detectMultiScale는 (x, y, w, h) 튜플의 numpy 배열(np.ndarray)을 반환합니다.
    # 각 튜플은 감지된 객체의 좌상단 좌표(x, y)와 너비(w), 높이(h)를 의미합니다.
    objects = cascade.detectMultiScale(
        gray_image,
        scaleFactor=SCALE_FACTOR,      # 1.1
        minNeighbors=MIN_NEIGHBORS,    # 5
        minSize=MIN_SIZE,              # (30, 30)
    )
    # 예시: 2개 감지 시, 결과는 np.array([[100, 50, 30, 30], [200, 80, 40, 40]])
    # 즉, objects[0]: x=100, y=50, w=30, h=30 / objects[1]: x=200, y=80, w=40, h=40

    # 일반적으로 아래처럼 각 객체 박스를 그리거나, 후처리/출력에 활용합니다:
    for (x, y, w, h) in objects:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)   # 화면에 사각형 표시
        # 필요에 따라 여기서 감지된 영역만 crop하거나, ROI 추가 분석도 가능

    # "감지 소스"는 gray_image(그레이스케일), 또는 입력이미지(frame)을 선택적으로 적용  
    # 예시: detectMultiScale의 첫 번째 인자만 변경
    # objects = cascade.detectMultiScale(frame, ...)   # 컬러 입력 사용 (보통은 gray가 성능 우수)
    return objects
```

---

## 📊 기능 비교표

### 전체 기능 비교

| 기능 | 0단계 | 1단계 | 2단계 |
|------|:-----:|:-----:|:-----:|
| **카메라 해상도** | 320×240 | 320×240 | 640×480 |
| **서보모터 제어** | ✅ | ✅ | ✅ |
| **카메라 설정 조절** | ✅ | ✅ | ✅ |
| **기본 그레이스케일** | ✅ | ❌ | ❌ |
| **가중치 그레이스케일** | ❌ | ✅ | ✅ |
| **RGB 가중치 트랙바** | ❌ | ✅ | ✅ |
| **객체 감지** | ❌ | ❌ | ✅ |
| **LED Bar 알림** | ❌ | ❌ | ✅ |
| **부저 알림** | ❌ | ❌ | ✅ |
| **감지 소스 선택** | ❌ | ❌ | ✅ |
| **이미지 저장** | ✅ | ✅ | ✅ |

### 트랙바 비교

| 트랙바 | 0단계 | 1단계 | 2단계 | 범위 |
|--------|:-----:|:-----:|:-----:|------|
| Servo 1 Angle | ✅ | ✅ | ✅ | 0-180 |
| Servo 2 Angle | ✅ | ✅ | ✅ | 0-180 |
| Brightness | ✅ | ✅ | ✅ | 0-100 |
| Contrast | ✅ | ✅ | ✅ | 0-100 |
| Saturation | ✅ | ✅ | ✅ | 0-100 |
| Gain | ✅ | ✅ | ✅ | 0-100 |
| R_weight | ❌ | ✅ | ✅ | 0-100 |
| G_weight | ❌ | ✅ | ✅ | 0-100 |
| B_weight | ❌ | ✅ | ✅ | 0-100 |
| Detect_Source | ❌ | ❌ | ✅ | 0-1 |

### 코드 복잡도 비교

| 항목 | 0단계 | 1단계 | 2단계 |
|------|-------|-------|-------|
| **총 코드 라인** | ~395줄 | ~474줄 | ~780줄 |
| **함수 개수** | 10개 | 11개 | 16개 |
| **상수 정의** | 10개 | 13개 | 20개 |

---

## 🏗️ 시스템 아키텍처

### 전체 시스템 구조

```mermaid
flowchart TB
    subgraph 하드웨어["🔧 하드웨어 계층"]
        CAM[USB 카메라]
        SERVO[서보모터 x2]
        LED[LED Bar x3]
        BUZZER[부저]
    end
    
    subgraph 라이브러리["📚 라이브러리 계층"]
        OPENCV[OpenCV<br/>영상 처리]
        RASPBOT[Raspbot_Lib<br/>모터/센서 제어]
        NUMPY[NumPy<br/>수치 연산]
    end
    
    subgraph 애플리케이션["💻 애플리케이션 계층"]
        INIT[초기화 모듈]
        CAMERA[카메라 모듈]
        SERVO_CTRL[서보 제어 모듈]
        GRAY[그레이스케일 모듈]
        DETECT[객체 감지 모듈]
        ALERT[알림 모듈]
        UI[UI 모듈]
    end
    
    CAM --> OPENCV
    SERVO --> RASPBOT
    LED --> RASPBOT
    BUZZER --> RASPBOT
    
    OPENCV --> CAMERA
    OPENCV --> GRAY
    OPENCV --> DETECT
    OPENCV --> UI
    
    RASPBOT --> SERVO_CTRL
    RASPBOT --> ALERT
    
    NUMPY --> GRAY
```

### 모듈별 함수 구조

```mermaid
classDiagram
    class 카메라모듈 {
        +initialize_camera()
        +apply_camera_settings()
        +calculate_fps()
    }
    
    class 서보모듈 {
        +control_servo_motor()
    }
    
    class 그레이스케일모듈 {
        +weighted_grayscale_conversion()
    }
    
    class 객체감지모듈 {
        +load_cascade_classifier()
        +detect_objects()
        +draw_detection_results()
    }
    
    class 알림모듈 {
        +control_led_bar()
        +control_buzzer_beep()
    }
    
    class UI모듈 {
        +initialize_ui()
        +get_trackbar_values()
        +handle_key_input()
        +trackbar_callback()
    }
    
    class 저장모듈 {
        +save_image()
        +save_detected_image()
    }
    
    카메라모듈 <-- 메인
    서보모듈 <-- 메인
    그레이스케일모듈 <-- 메인
    객체감지모듈 <-- 메인
    알림모듈 <-- 메인
    UI모듈 <-- 메인
    저장모듈 <-- 메인
```

---

## 📈 단계별 순서도

### 0단계: 기본 카메라 프로그램

```mermaid
sequenceDiagram
    participant User as 사용자
    participant Main as main()
    participant Camera as 카메라
    participant Servo as 서보모터
    participant UI as UI/트랙바
    
    User->>Main: 프로그램 시작
    Main->>Camera: initialize_camera()
    Camera-->>Main: cap 객체
    Main->>Servo: control_servo_motor(초기값)
    Main->>UI: initialize_ui()
    
    loop 메인 루프
        Main->>UI: get_trackbar_values()
        UI-->>Main: params
        Main->>Camera: apply_camera_settings()
        Main->>Servo: control_servo_motor()
        Main->>Camera: cap.read()
        Camera-->>Main: frame
        Main->>Main: cvtColor(BGR2GRAY)
        Main->>UI: imshow()
        Main->>UI: waitKey()
        alt SPACE 키
            Main->>Main: save_image()
        else ESC 키
            Main->>Main: break
        end
    end
    
    Main->>Camera: cap.release()
    Main->>UI: destroyAllWindows()
```

### 2단계: 객체 감지 프로그램

```mermaid
sequenceDiagram
    participant Main as main()
    participant Camera as 카메라
    participant Cascade as Haar Cascade
    participant Alert as LED/부저
    participant UI as UI
    
    Main->>Camera: initialize_camera()
    Main->>Cascade: load_cascade_classifier()
    Main->>Alert: 초기화 (LED OFF, 부저 OFF)
    Main->>UI: initialize_ui()
    
    loop 메인 루프
        Main->>Camera: cap.read()
        Camera-->>Main: frame
        Main->>Main: weighted_grayscale_conversion()
        Main-->>Main: gray
        
        alt detect_source == 0
            Main->>Cascade: detect_objects(frame)
        else detect_source == 1
            Main->>Cascade: detect_objects(gray)
        end
        
        Cascade-->>Main: detected_objects
        Main->>Main: draw_detection_results()
        
        Main->>Alert: control_led_bar(count)
        Main->>Alert: control_buzzer_beep(count)
        
        Main->>UI: imshow()
    end
```

---

## 🔬 핵심 알고리즘

### 1. RGB 가중치 그레이스케일 변환

**일반 그레이스케일 공식**:
```
Gray = 0.299 × R + 0.587 × G + 0.114 × B
```

**가중치 그레이스케일 공식**:
```
Gray = (R_weight × R + G_weight × G + B_weight × B) / (R_weight + G_weight + B_weight)
```

```mermaid
flowchart LR
    subgraph 입력
        R[R 채널]
        G[G 채널]
        B[B 채널]
    end
    
    subgraph 가중치
        RW[R_weight]
        GW[G_weight]
        BW[B_weight]
    end
    
    subgraph 처리
        NR[R × R_norm]
        NG[G × G_norm]
        NB[B × B_norm]
        SUM[합산]
    end
    
    R --> NR
    G --> NG
    B --> NB
    RW --> NR
    GW --> NG
    BW --> NB
    NR --> SUM
    NG --> SUM
    NB --> SUM
    SUM --> OUT[Gray 출력]
```

### 2. Haar Cascade 객체 감지 알고리즘

```mermaid
flowchart TB
    A[입력 이미지] --> B[이미지 피라미드 생성]
    B --> C[슬라이딩 윈도우]
    C --> D[Haar 특징 계산]
    D --> E[Cascade 분류기]
    E --> F{객체?}
    F -->|Yes| G[후보 영역 저장]
    F -->|No| H[다음 윈도우]
    G --> I[비최대 억제<br/>NMS]
    H --> C
    I --> J[최종 검출 결과]
```

**파라미터 설명**:

| 파라미터 | 값 | 설명 |
|----------|-----|------|
| `scaleFactor` | 1.1 | 이미지 피라미드 축소 비율 |
| `minNeighbors` | 5 | 최소 인접 검출 수 (높을수록 정확) |
| `minSize` | (30, 30) | 최소 검출 크기 |

### 3. LED Bar 제어 알고리즘

```mermaid
flowchart TD
    A[감지된 객체 수] --> B{count == 0?}
    B -->|Yes| C[LED 모두 OFF]
    B -->|No| D{count == 1?}
    D -->|Yes| E[LED1 ON<br/>LED2,3 OFF]
    D -->|No| F{count == 2?}
    F -->|Yes| G[LED1,2 ON<br/>LED3 OFF]
    F -->|No| H[LED 모두 ON]
```

### 4. 부저 삐익삐익 알고리즘

```mermaid
flowchart TD
    A[프레임 카운터] --> B[beep_cycle = frame_counter // 15 % 2]
    B --> C{객체 감지?}
    C -->|No| D[부저 OFF]
    C -->|Yes| E{beep_cycle?}
    E -->|0| F[부저 ON]
    E -->|1| G[부저 OFF]
```

**소스 코드**:
```python
def control_buzzer_beep(car, detected_count, frame_counter):
    if detected_count > 0:
        # 15프레임마다 부저 토글 (삐익삐익 효과)
        beep_cycle = (frame_counter // 15) % 2
        if beep_cycle == 0:
            car.Ctrl_Buzzer(1)
        else:
            car.Ctrl_Buzzer(0)
    else:
        car.Ctrl_Buzzer(0)
```

---

## 🚀 사용법

### 실행 순서

```bash
# 1단계: 기본 카메라 테스트
python 0_camera_color_rect.py

# 2단계: 가중치 그레이스케일 테스트
python 1_camera_weight.py

# 3단계: 객체 감지 실행
python 2_object_camera_haarcascade.py
```

### 키보드 조작

| 키 | 기능 |
|----|------|
| `ESC` | 프로그램 종료 |
| `SPACE` | 현재 프레임 저장 |

### 트랙바 조작 가이드

```mermaid
flowchart LR
    subgraph 서보모터
        S1[Servo 1<br/>좌우 회전]
        S2[Servo 2<br/>상하 회전]
    end
    
    subgraph 카메라설정
        BR[Brightness<br/>밝기]
        CT[Contrast<br/>대비]
        SA[Saturation<br/>채도]
        GA[Gain<br/>게인]
    end
    
    subgraph 그레이스케일
        RW[R_weight<br/>빨강 강조]
        GW[G_weight<br/>초록 강조]
        BW[B_weight<br/>파랑 강조]
    end
    
    subgraph 감지소스
        DS[Detect_Source<br/>0:컬러 1:그레이]
    end
```

### 저장 경로

| 프로그램 | 저장 경로 |
|----------|-----------|
| 0단계 | `./positive/rect/` |
| 1단계 | `./rectagle/rect/` |
| 2단계 | `./save_images/detected_objects/` |

---

## 🔧 트러블슈팅

### 자주 발생하는 오류

| 오류 메시지 | 원인 | 해결 방법 |
|-------------|------|-----------|
| `Cannot open camera` | 카메라 연결 안됨 | USB 연결 확인, 다른 프로그램 종료 |
| `Cascade file not found` | XML 파일 없음 | `cascade.xml` 파일 경로 확인 |
| `Raspbot initialization failed` | 하드웨어 연결 안됨 | GPIO 연결 확인, 권한 확인 |

### 성능 최적화 팁

```mermaid
flowchart TB
    A[성능 문제] --> B{FPS 낮음?}
    B -->|Yes| C[해상도 낮추기]
    B -->|Yes| D[scaleFactor 높이기]
    B -->|Yes| E[minSize 크게]
    
    A --> F{오탐지 많음?}
    F -->|Yes| G[minNeighbors 높이기]
    F -->|Yes| H[Cascade 재학습]
    
    A --> I{미탐지 많음?}
    I -->|Yes| J[minNeighbors 낮추기]
    I -->|Yes| K[minSize 작게]
    I -->|Yes| L[RGB 가중치 조절]
```

---

## 📚 참고 자료

### OpenCV 함수 참조

| 함수 | 설명 |
|------|------|
| `cv2.VideoCapture()` | 카메라 캡처 객체 생성 |
| `cv2.cvtColor()` | 색공간 변환 |
| `cv2.CascadeClassifier()` | Haar Cascade 분류기 |
| `detectMultiScale()` | 다중 스케일 객체 감지 |
| `cv2.addWeighted()` | 이미지 가중 합성 |
| `cv2.createTrackbar()` | 트랙바 생성 |

### 상수 기본값 정리

| 상수명 | 0단계 | 1단계 | 2단계 |
|--------|-------|-------|-------|
| CAMERA_WIDTH | 320 | 320 | 640 |
| CAMERA_HEIGHT | 240 | 240 | 480 |
| SERVO_1_INITIAL | 90 | 90 | 90 |
| SERVO_2_INITIAL | 35 | 35 | 35 |
| BRIGHTNESS_INITIAL | 70 | 70 | 70 |
| CONTRAST_INITIAL | 70 | 70 | 70 |
| SATURATION_INITIAL | 70 | 70 | 70 |
| GAIN_INITIAL | 80 | 80 | 80 |
| R_WEIGHT_INITIAL | - | 33 | 33 |
| G_WEIGHT_INITIAL | - | 33 | 33 |
| B_WEIGHT_INITIAL | - | 33 | 33 |

---

## 🎓 학습 로드맵

```mermaid
flowchart TD
    subgraph 기초단계["🟢 기초 단계"]
        A[0_camera_color_rect.py<br/>카메라 기본]
    end
    
    subgraph 중급단계["🟡 중급 단계"]
        B[1_camera_weight.py<br/>가중치 변환]
    end
    
    subgraph 고급단계["🔴 고급 단계"]
        C[2_object_camera_haarcascade.py<br/>객체 감지]
    end
    
    subgraph 응용단계["🟣 응용 단계"]
        D[자율주행 통합]
        E[딥러닝 적용]
    end
    
    A -->|"그레이스케일 이해"| B
    B -->|"영상 전처리 이해"| C
    C -->|"감지 알고리즘 이해"| D
    C -->|"AI 확장"| E
```

---

> 📝 **문서 버전**: v1.0  
> 📅 **최종 수정**: 2025-12-08  
> 👤 **작성**: Raspbot 개발팀

