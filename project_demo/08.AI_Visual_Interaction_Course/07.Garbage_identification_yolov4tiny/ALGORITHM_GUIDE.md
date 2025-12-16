# YOLO v4 Tiny 쓰레기 인식 알고리즘 상세 가이드

## 📋 목차

1. [시스템 개요](#시스템-개요)
2. [전체 아키텍처](#전체-아키텍처)
3. [클래스 구조](#클래스-구조)
4. [알고리즘 상세 흐름도](#알고리즘-상세-흐름도)
5. [주요 처리 단계](#주요-처리-단계)
6. [데이터 흐름](#데이터-흐름)
7. [성능 최적화](#성능-최적화)

---

## 시스템 개요

### 목적
라즈베리파이 기반 임베디드 환경에서 실시간으로 쓰레기를 감지하고 분류하는 시스템

### 핵심 기술
- **YOLOv4-Tiny**: 경량화된 객체 감지 신경망
- **TensorFlow/Keras**: 딥러닝 프레임워크
- **OpenCV**: 영상 처리
- **PIL**: 이미지 처리 및 시각화

### 주요 기능
1. 실시간 쓰레기 객체 감지 및 분류
2. 바운딩 박스 및 신뢰도 점수 시각화
3. OLED 디스플레이 연동
4. 로봇 팔 제어를 위한 좌표 계산

---

## 전체 아키텍처

```mermaid
graph TB
    subgraph 입력부
        A[카메라 입력] --> B[이미지 프레임]
    end
    
    subgraph 전처리부
        B --> C[크기 조정 640x480]
        C --> D[색상 변환 BGR→RGB]
        D --> E[Letterbox 패딩]
        E --> F[정규화 0-1]
        F --> G[배치 차원 추가]
    end
    
    subgraph 추론부
        G --> H{실행 모드?}
        H -->|Graph 모드| I[TensorFlow Session]
        H -->|Eager 모드| J[직접 예측]
        I --> K[YOLO 모델 추론]
        J --> K
        K --> L[Feature Map 생성]
    end
    
    subgraph 후처리부
        L --> M[YOLO Eval]
        M --> N[신뢰도 필터링]
        N --> O[NMS 적용]
        O --> P[바운딩 박스 생성]
    end
    
    subgraph 시각화부
        P --> Q[좌표 조정]
        Q --> R[박스 그리기]
        R --> S[라벨 표시]
        S --> T[OLED 업데이트]
    end
    
    subgraph 출력부
        T --> U[처리된 이미지]
        T --> V[감지 정보 딕셔너리]
    end
    
    style 입력부 fill:#e1f5ff
    style 전처리부 fill:#fff4e1
    style 추론부 fill:#ffe1e1
    style 후처리부 fill:#e1ffe1
    style 시각화부 fill:#f0e1ff
    style 출력부 fill:#ffe1f0
```

---

## 클래스 구조

```mermaid
classDiagram
    class garbage_identify {
        -Yahboom_OLED oled
        -float score
        -float iou
        -bool eager
        -FPS fps
        -list class_names
        -ndarray anchors
        -tuple model_image_size
        -Model yolo_model
        -Session sess
        -list colors
        -int garbage_index
        
        +__init__()
        +_get_class() list
        +_get_anchors() ndarray
        +generate() void
        +detect_image(image) tuple
        +garbage_run(img) tuple
    }
    
    class YOLO_Model {
        <<external>>
        +yolo_body()
        +yolo_eval()
    }
    
    class TensorFlow {
        <<framework>>
        +Session
        +Model
        +predict()
    }
    
    class OpenCV {
        <<library>>
        +cvtColor()
        +resize()
        +putText()
    }
    
    class PIL_Image {
        <<library>>
        +ImageDraw
        +ImageFont
        +fromarray()
    }
    
    garbage_identify --> YOLO_Model : uses
    garbage_identify --> TensorFlow : uses
    garbage_identify --> OpenCV : uses
    garbage_identify --> PIL_Image : uses
```

---

## 알고리즘 상세 흐름도

### 1. 초기화 프로세스

```mermaid
flowchart TD
    Start([시스템 시작]) --> Init1[OLED 디스플레이 초기화]
    Init1 --> Init2[모델 파라미터 설정<br/>score=0.5, iou=0.3]
    Init2 --> Init3[파일 경로 설정]
    Init3 --> Init4[클래스 목록 로드]
    Init4 --> Init5[앵커 박스 로드]
    Init5 --> Init6{Eager 모드?}
    Init6 -->|No| Init7[Graph 모드 설정<br/>Eager Execution 비활성화]
    Init6 -->|Yes| Init8[Eager 모드 설정]
    Init7 --> Init9[YOLO 모델 생성]
    Init8 --> Init9
    Init9 --> Init10[가중치 로드 .h5]
    Init10 --> Init11[후처리 파이프라인 구성]
    Init11 --> Init12[색상 팔레트 생성]
    Init12 --> End([초기화 완료])
    
    style Start fill:#90EE90,color:#111
    style End fill:#90EE90,color:#111
    style Init9 fill:#FFB6C1,color:#111
    style Init10 fill:#FFB6C1,color:#111
```

### 2. 메인 실행 루프 (garbage_run)

```mermaid
flowchart TD
    Start([프레임 입력]) --> Step1[이미지 크기 조정 640x480]
    Step1 --> Step2[FPS 업데이트 및 표시]
    Step2 --> Step3{garbage_index < 3?}
    
    Step3 -->|Yes| Loading1[로딩 메시지 표시]
    Loading1 --> Loading2[garbage_index++]
    Loading2 --> Return1[빈 결과 반환]
    Return1 --> End1([종료])
    
    Step3 -->|No| Detect1[detect_image 호출]
    Detect1 --> Detect2{예외 발생?}
    Detect2 -->|Yes| Error[예외 처리<br/>무시]
    Detect2 -->|No| Success[결과 획득]
    Error --> Return2[현재 이미지, 빈 딕셔너리 반환]
    Success --> Return3[처리된 이미지, 감지 정보 반환]
    Return2 --> End2([종료])
    Return3 --> End2
    
    style Start fill:#87CEEB,color:#111
    style End1 fill:#87CEEB,color:#111
    style End2 fill:#87CEEB,color:#111
    style Detect1 fill:#FFD700,color:#111
```

### 3. 객체 감지 프로세스 (detect_image)

```mermaid
flowchart TD
    Start([이미지 입력]) --> Pre1[BGR → RGB 변환]
    Pre1 --> Pre2[NumPy → PIL 변환]
    Pre2 --> Pre3[Letterbox 이미지 생성<br/>416x416, 종횡비 유지]
    Pre3 --> Pre4[정규화 ÷ 255.0]
    Pre4 --> Pre5[배치 차원 추가<br/>shape: 1,416,416,3]
    
    Pre5 --> Infer1{실행 모드?}
    
    Infer1 -->|Graph| Graph1[세션 준비]
    Graph1 --> Graph2[feed_dict 생성]
    Graph2 --> Graph3[sess.run 실행]
    
    Infer1 -->|Eager| Eager1[입력 형태 준비]
    Eager1 --> Eager2[model.predict 실행]
    
    Graph3 --> Post1[YOLO 출력 획득]
    Eager2 --> Post1
    
    Post1 --> Post2[boxes, scores, classes 분리]
    Post2 --> Post3{감지된 객체 존재?}
    
    Post3 -->|No| NoDetect[OLED에 None 표시]
    NoDetect --> Return1[원본 이미지, 빈 딕셔너리 반환]
    
    Post3 -->|Yes| Loop1[각 객체에 대해 반복]
    
    Loop1 --> Visual1[좌표 추출 및 조정]
    Visual1 --> Visual2[박스 확장 ±5]
    Visual2 --> Visual3[경계 제한 적용]
    Visual3 --> Visual4[라벨 텍스트 생성]
    Visual4 --> Visual5[중심점 계산]
    Visual5 --> Visual6[바운딩 박스 그리기]
    Visual6 --> Visual7[중심점 원 그리기]
    Visual7 --> Visual8[라벨 텍스트 표시]
    Visual8 --> Visual9[OLED 업데이트]
    Visual9 --> Visual10[좌표 정규화<br/>로봇 제어용]
    Visual10 --> Visual11[결과 딕셔너리 저장]
    
    Visual11 --> Loop2{다음 객체?}
    Loop2 -->|Yes| Loop1
    Loop2 -->|No| Final1[RGB → BGR 변환]
    
    Final1 --> Return2[처리된 이미지, 감지 정보 반환]
    Return1 --> End([종료])
    Return2 --> End
    
    style Start fill:#98FB98,color:#111
    style End fill:#98FB98,color:#111
    style Infer1 fill:#FFA07A,color:#111
    style Post1 fill:#DDA0DD,color:#111
```

---

## 주요 처리 단계

### 1단계: 이미지 전처리

```mermaid
graph LR
    A[원본 이미지<br/>HxWx3] --> B[크기 조정<br/>640x480x3]
    B --> C[색상 변환<br/>BGR→RGB]
    C --> D[Letterbox<br/>416x416x3]
    D --> E[정규화<br/>0.0-1.0]
    E --> F[배치 추가<br/>1x416x416x3]
    
    style A fill:#FFE4B5
    style F fill:#FFE4B5
```

**Letterbox 패딩 원리:**

```mermaid
graph TD
    subgraph 원본이미지
        A[640x480<br/>4:3 비율]
    end
    
    subgraph Letterbox처리
        B[크기조정<br/>416x312]
        C[상하패딩추가<br/>52px씩]
        D[최종크기<br/>416x416]
    end
    
    A --> B
    B --> C
    C --> D
    
    style A fill:#87CEEB
    style D fill:#90EE90
```

### 2단계: YOLO 추론

```mermaid
sequenceDiagram
    participant Input as 입력 이미지
    participant Model as YOLO 모델
    participant Backbone as 백본 네트워크
    participant Neck as 넥 네트워크
    participant Head as 헤드
    participant Output as 출력
    
    Input->>Model: 1x416x416x3
    Model->>Backbone: Feature 추출
    Backbone->>Neck: 다중 스케일 Feature
    Neck->>Head: Feature 융합
    Head->>Output: 예측 결과
    Output->>Output: boxes, scores, classes
```

**YOLO 출력 구조:**

```mermaid
graph TB
    A[YOLO 출력] --> B[13x13 Grid<br/>큰 객체]
    A --> C[26x26 Grid<br/>작은 객체]
    
    B --> D[각 셀당 3개 앵커]
    C --> E[각 셀당 3개 앵커]
    
    D --> F[예측값<br/>x,y,w,h,conf,classes]
    E --> G[예측값<br/>x,y,w,h,conf,classes]
```

### 3단계: 후처리 (NMS)

```mermaid
flowchart TD
    Start[예측 결과] --> Filter1[신뢰도 필터링<br/>threshold > 0.5]
    Filter1 --> NMS1[클래스별 그룹화]
    NMS1 --> NMS2[IoU 계산]
    NMS2 --> NMS3{IoU > 0.3?}
    NMS3 -->|Yes| Remove[낮은 점수 박스 제거]
    NMS3 -->|No| Keep[박스 유지]
    Remove --> NMS4{남은 박스?}
    Keep --> NMS4
    NMS4 -->|Yes| NMS2
    NMS4 -->|No| Final[최종 박스 선택]
    
    style Start fill:#FFE4E1
    style Final fill:#E1FFE4
```

**NMS (Non-Maximum Suppression) 알고리즘:**

```mermaid
graph LR
    A[박스 1<br/>score: 0.95] --> D{IoU > 0.3?}
    B[박스 2<br/>score: 0.87] --> D
    C[박스 3<br/>score: 0.76] --> D
    
    D -->|Yes| E[중복 제거<br/>낮은 점수 삭제]
    D -->|No| F[모두 유지]
    
    E --> G[박스 1만 유지]
    F --> H[모두 출력]
    
    style A fill:#90EE90
    style G fill:#90EE90
```

### 4단계: 시각화

```mermaid
flowchart LR
    A[감지 결과] --> B[좌표 조정]
    B --> C[바운딩 박스 그리기]
    C --> D[중심점 표시]
    D --> E[라벨 텍스트]
    E --> F[OLED 업데이트]
    F --> G[최종 이미지]
    
    style A fill:#FFB6C1
    style G fill:#90EE90
```

---

## 데이터 흐름

### 전체 데이터 파이프라인

```mermaid
graph TB
    subgraph 입력
        A1[카메라] --> A2[640x480x3 BGR]
    end
    
    subgraph 전처리
        A2 --> B1[리사이즈]
        B1 --> B2[색상 변환 RGB]
        B2 --> B3[Letterbox 416x416]
        B3 --> B4[정규화 float32]
        B4 --> B5[배치 1x416x416x3]
    end
    
    subgraph YOLO모델
        B5 --> C1[백본: CSPDarknet53-Tiny]
        C1 --> C2[넥: PANet]
        C2 --> C3[헤드: YOLO Head]
        C3 --> C4[출력 Feature Map]
    end
    
    subgraph 후처리
        C4 --> D1[앵커 박스 디코딩]
        D1 --> D2[신뢰도 필터링]
        D2 --> D3[NMS 적용]
        D3 --> D4[최종 박스]
    end
    
    subgraph 시각화
        D4 --> E1[좌표 변환]
        E1 --> E2[그래픽 렌더링]
        E2 --> E3[OLED 업데이트]
    end
    
    subgraph 출력
        E3 --> F1[처리된 이미지]
        E3 --> F2[감지 정보 딕셔너리]
    end
    
    style 입력 fill:#E6F3FF
    style 전처리 fill:#FFF4E6
    style YOLO모델 fill:#FFE6E6
    style 후처리 fill:#E6FFE6
    style 시각화 fill:#F0E6FF
    style 출력 fill:#FFE6F0
```

### 좌표 변환 흐름

```mermaid
sequenceDiagram
    participant Original as 원본 이미지<br/>640x480
    participant Letterbox as Letterbox<br/>416x416
    participant YOLO as YOLO 출력<br/>상대 좌표
    participant Absolute as 절대 좌표<br/>원본 기준
    participant Robot as 로봇 좌표<br/>정규화
    
    Original->>Letterbox: 크기 조정 + 패딩
    Letterbox->>YOLO: 모델 추론
    YOLO->>Absolute: 역변환 (패딩 제거)
    Absolute->>Robot: 정규화 변환<br/>(x-320)/4000
    Robot->>Robot: 제어 명령 생성
```

---

## 성능 최적화

### 최적화 전략

```mermaid
mindmap
    root((성능 최적화))
        모델 경량화
            YOLOv4-Tiny 사용
            앵커 개수 절반
            Feature Map 축소
        추론 최적화
            Graph 모드 사용
            배치 처리
            GPU 메모리 동적 할당
        전처리 최적화
            고정 입력 크기
            효율적인 리사이징
            벡터화 연산
        후처리 최적화
            조기 종료 필터링
            효율적인 NMS
            메모리 재사용
```

### 실행 모드 비교

```mermaid
graph LR
    subgraph Graph모드
        A1[정적 그래프 생성] --> A2[그래프 최적화]
        A2 --> A3[Session 실행]
        A3 --> A4[빠른 추론 속도]
    end
    
    subgraph Eager모드
        B1[즉시 실행] --> B2[동적 그래프]
        B2 --> B3[디버깅 용이]
        B3 --> B4[느린 추론 속도]
    end
    
    style A4 fill:#90EE90
    style B3 fill:#FFD700
```

### FPS 향상 기법

```mermaid
flowchart TD
    A[입력 프레임] --> B{해상도 조정}
    B -->|640x480| C[표준 처리]
    B -->|더 작게| D[빠른 처리]
    
    C --> E{모델 선택}
    E -->|YOLOv4| F[높은 정확도<br/>느린 속도]
    E -->|YOLOv4-Tiny| G[적당한 정확도<br/>빠른 속도]
    
    G --> H{GPU 사용?}
    H -->|Yes| I[GPU 가속<br/>20-30 FPS]
    H -->|No| J[CPU 처리<br/>5-10 FPS]
    
    style I fill:#90EE90
    style G fill:#FFD700
```

---

## 주요 알고리즘 상세

### 1. Letterbox 알고리즘

```python
"""
Letterbox 이미지 생성 알고리즘

목적: 종횡비를 유지하면서 이미지를 목표 크기로 조정

입력: 원본 이미지 (W, H), 목표 크기 (target_W, target_H)
출력: 패딩이 추가된 이미지 (target_W, target_H)

단계:
1. 종횡비 계산: ratio = min(target_W/W, target_H/H)
2. 새 크기 계산: new_W = W * ratio, new_H = H * ratio
3. 이미지 리사이즈
4. 패딩 계산: pad_W = (target_W - new_W) / 2, pad_H = (target_H - new_H) / 2
5. 회색 패딩 추가
"""
```

```mermaid
flowchart TD
    A[원본 이미지<br/>640x480] --> B[종횡비 계산<br/>4:3]
    B --> C{목표 크기<br/>416x416}
    C --> D[스케일 계산<br/>min: 416/640, 416/480]
    D --> E[새 크기<br/>416x312]
    E --> F[패딩 계산<br/>상하 52px]
    F --> G[회색 패딩 추가]
    G --> H[최종 이미지<br/>416x416]
    
    style A fill:#FFE4B5
    style H fill:#90EE90
```

### 2. 좌표 정규화 알고리즘

```python
"""
로봇 제어를 위한 좌표 정규화

입력: 이미지 좌표 (x, y) - 픽셀 단위
출력: 정규화된 좌표 (a, b) - 로봇 좌표계

변환 공식:
a = (x - 320) / 4000  # 수평 위치, 중심 기준
b = ((480 - y) / 3000) * 0.8 + 0.19  # 수직 위치, Y축 반전

설명:
- x = 320: 이미지 중심 (640/2)
- y = 480: 이미지 하단에서 상단으로
- 스케일 팩터: 경험적으로 결정된 값
- 오프셋: 로봇 팔 작업 공간 보정
"""
```

```mermaid
graph TD
    A[이미지 좌표<br/>x=400, y=200] --> B[중심 기준 변환<br/>x-320 = 80]
    B --> C[스케일링<br/>80/4000 = 0.02]
    
    A --> D[Y축 반전<br/>480-200 = 280]
    D --> E[스케일링<br/>280/3000 = 0.093]
    E --> F[조정<br/>0.093*0.8+0.19 = 0.264]
    
    C --> G[로봇 좌표<br/>a=0.02, b=0.264]
    F --> G
    
    style A fill:#FFE4B5
    style G fill:#90EE90
```

### 3. NMS 상세 알고리즘

```mermaid
flowchart TD
    Start[모든 예측 박스] --> Sort[신뢰도 기준 정렬]
    Sort --> Select[최고 점수 박스 선택]
    Select --> Loop{남은 박스?}
    
    Loop -->|No| End[최종 박스 리스트]
    Loop -->|Yes| Calc[IoU 계산]
    
    Calc --> Compare{IoU > threshold?}
    Compare -->|Yes| Remove[박스 제거<br/>중복으로 판단]
    Compare -->|No| Keep[박스 유지]
    
    Remove --> Loop
    Keep --> AddList[결과 리스트 추가]
    AddList --> Loop
    
    style Start fill:#FFE4B5
    style End fill:#90EE90
```

**IoU (Intersection over Union) 계산:**

```mermaid
graph LR
    A[박스 A] --> C[교집합 면적]
    B[박스 B] --> C
    A --> D[합집합 면적]
    B --> D
    C --> E[IoU = 교집합 / 합집합]
    D --> E
    E --> F{IoU > 0.3?}
    F -->|Yes| G[중복 박스]
    F -->|No| H[별개 박스]
    
    style G fill:#FFB6C1
    style H fill:#90EE90
```

---

## 시스템 상태 다이어그램

```mermaid
stateDiagram-v2
    [*] --> 초기화
    초기화 --> 모델로딩
    모델로딩 --> 대기중
    
    대기중 --> 프레임수신 : 카메라 입력
    프레임수신 --> 로딩중 : index < 3
    프레임수신 --> 전처리 : index >= 3
    
    로딩중 --> 대기중 : index++
    
    전처리 --> 추론
    추론 --> 후처리
    후처리 --> 시각화
    시각화 --> 결과반환
    
    결과반환 --> 대기중 : 다음 프레임
    
    추론 --> 에러처리 : 예외 발생
    에러처리 --> 대기중
    
    note right of 로딩중
        초기 3프레임 대기
        모델 워밍업
    end note
    
    note right of 추론
        YOLO 모델 실행
        GPU/CPU 선택
    end note
```

---

## 타이밍 다이어그램

```mermaid
sequenceDiagram
    autonumber
    participant Camera as 카메라
    participant Main as garbage_run
    participant Detect as detect_image
    participant Model as YOLO 모델
    participant Display as OLED
    
    Camera->>Main: 프레임 전달
    Main->>Main: 크기 조정
    Main->>Main: FPS 업데이트
    
    alt 초기 로딩 (index < 3)
        Main->>Main: 로딩 메시지 표시
        Main->>Main: index++
        Main-->>Camera: 빈 결과 반환
    else 정상 실행 (index >= 3)
        Main->>Detect: 프레임 전달
        Detect->>Detect: 전처리 (BGR→RGB)
        Detect->>Detect: Letterbox 패딩
        Detect->>Detect: 정규화
        Detect->>Model: 추론 요청
        Model->>Model: Feature 추출
        Model->>Model: 객체 감지
        Model-->>Detect: boxes, scores, classes
        Detect->>Detect: NMS 적용
        Detect->>Detect: 박스 그리기
        Detect->>Display: 감지 정보 전달
        Display->>Display: 화면 업데이트
        Detect-->>Main: 처리된 이미지, 딕셔너리
        Main-->>Camera: 결과 반환
    end
```

---

## 메모리 사용 패턴

```mermaid
graph TB
    subgraph 모델메모리
        A1[YOLO 가중치<br/>~20MB]
        A2[Feature Maps<br/>~10MB]
    end
    
    subgraph 프레임메모리
        B1[원본 프레임<br/>640x480x3 = 0.9MB]
        B2[전처리 프레임<br/>416x416x3 = 0.5MB]
        B3[출력 프레임<br/>640x480x3 = 0.9MB]
    end
    
    subgraph 추론메모리
        C1[중간 Feature<br/>~5MB]
        C2[예측 결과<br/>~1MB]
    end
    
    Total[총 메모리<br/>~40MB] --> A1
    Total --> A2
    Total --> B1
    Total --> B2
    Total --> B3
    Total --> C1
    Total --> C2
    
    style Total fill:#FFB6C1
```

---

## 에러 처리 흐름

```mermaid
flowchart TD
    A[시스템 실행] --> B{초기화 성공?}
    B -->|No| E1[모델 파일 확인]
    E1 --> E2[경로 수정 또는 재설치]
    E2 --> A
    
    B -->|Yes| C[프레임 수신]
    C --> D{전처리 성공?}
    D -->|No| E3[이미지 형식 확인]
    E3 --> C
    
    D -->|Yes| F{추론 성공?}
    F -->|No| E4[메모리 부족 확인]
    E4 --> E5[리소스 해제]
    E5 --> F
    
    F -->|Yes| G{후처리 성공?}
    G -->|No| E6[예외 로깅]
    E6 --> H[빈 결과 반환]
    
    G -->|Yes| I[정상 결과 반환]
    
    H --> C
    I --> C
    
    style A fill:#90EE90
    style I fill:#90EE90
    style E1 fill:#FFB6C1
    style E3 fill:#FFB6C1
    style E4 fill:#FFB6C1
    style E6 fill:#FFB6C1
```

---

## 핵심 수식

### 1. IoU (Intersection over Union)

$$IoU = \frac{Area(Box_A \cap Box_B)}{Area(Box_A \cup Box_B)}$$

### 2. 신뢰도 점수

$$Score = P(Object) \times IoU(pred, truth) \times P(Class|Object)$$

### 3. 좌표 정규화

$$a = \frac{x - center_x}{scale_x}$$

$$b = \frac{image_height - y}{scale_y} \times weight + offset$$

---

## 성능 메트릭

```mermaid
graph LR
    A[성능 지표] --> B[FPS<br/>초당 프레임 수]
    A --> C[정확도<br/>mAP]
    A --> D[추론 시간<br/>ms/frame]
    A --> E[메모리 사용량<br/>MB]
    
    B --> B1[목표: 15-20 FPS]
    C --> C1[목표: mAP > 0.8]
    D --> D1[목표: < 100ms]
    E --> E1[목표: < 100MB]
    
    style B1 fill:#90EE90
    style C1 fill:#90EE90
    style D1 fill:#90EE90
    style E1 fill:#90EE90
```

---

## 결론

이 시스템은 **YOLOv4-Tiny** 기반의 경량화된 객체 감지 알고리즘을 사용하여 라즈베리파이에서 실시간으로 쓰레기를 인식합니다.

### 주요 특징:
1. ✅ **효율적인 전처리**: Letterbox 패딩으로 왜곡 방지
2. ✅ **빠른 추론**: Graph 모드로 최적화된 성능
3. ✅ **정확한 후처리**: NMS로 중복 제거
4. ✅ **직관적인 시각화**: 바운딩 박스와 신뢰도 표시
5. ✅ **로봇 연동**: 정규화된 좌표로 제어 가능

### 적용 가능 분야:
- 🤖 자율 쓰레기 분류 로봇
- ♻️ 재활용 자동화 시스템
- 🏭 산업용 물체 분류 시스템
- 📚 교육용 AI 프로젝트

