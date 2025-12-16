# 📂 05_yolo 프로젝트 구조 가이드

> **YOLO11 커스텀 객체 인식 프로젝트의 완전한 구조 설명**

---

## 📋 전체 구조

```
05_yolo/
├── 📄 README.md                          # 메인 가이드 (시작점)
├── 📄 PROJECT_STRUCTURE.md               # 본 파일 (구조 설명)
│
├── 📚 docs/                              # 📚 상세 문서
│   ├── 📚_문서_가이드.md                 # 문서 네비게이션 가이드
│   ├── 1단계_HAAR_CASCADE_vs_YOLO_비교분석.md
│   ├── 2단계_RASPBERRY_PI_5_최적화_가이드.md  # ⭐ Pi 5 최적화
│   ├── 3단계_YOLO11_전체_워크플로우_가이드.md  # ⭐ 완전 가이드
│   ├── 단계별_1_실행_가이드.md
│   ├── 단계별_2_실행_가이드_COMPLETE.md
│   └── labelimg.md                       # LabelImg 사용법
│
├── 🛠️ scripts/                          # 🛠️ 유틸리티 스크립트
│   ├── dataset/                         # 데이터셋 관리
│   │   ├── dataset_splitter.py          # 데이터셋 분할 (train/val/test)
│   │   └── create_data_yaml.py          # data.yaml 생성
│   ├── labeling/                        # 라벨링 도구
│   │   └── label_quality_checker.py     # 라벨 품질 검증
│   ├── training/                        # 모델 훈련
│   │   ├── train_yolo11.py              # 범용 훈련 스크립트
│   │   └── train_yolo11_pi5_optimized.py # ⭐ Pi 5 최적화 훈련
│   ├── inference/                       # 추론 및 테스트
│   │   └── test_inference.py            # 모델 테스트
│   └── deployment/                      # 배포 도구 (예정)
│
├── 💡 examples/                          # 💡 예제 코드
│   ├── basic_detection.py               # 기본 객체 인식
│   ├── real_time_webcam.py              # 실시간 웹캠 인식
│   ├── traffic_sign_detection.py        # 교통표지판 인식 (예정)
│   └── autonomous_driving_integration.py # 자율주행 통합 (예정)
│
├── 🎓 tutorials/                         # 🎓 튜토리얼
│   ├── 01_quick_start.md                # ⭐ 30분 빠른 시작
│   ├── 02_data_collection.md            # 데이터 수집 (예정)
│   ├── 03_model_training.md             # 모델 훈련 (예정)
│   └── 04_deployment.md                 # 배포 (예정)
│
├── 📦 model_data/                        # 📦 모델 파일
│   ├── weights/                         # 가중치 파일 (.pt, .onnx)
│   └── configs/                         # 설정 파일 (.yaml)
│
├── 🔧 labelImg-master/                   # 🔧 라벨링 도구
│   └── (LabelImg 소스코드)
│
├── 📊 results/                           # 📊 실험 결과
│   └── (훈련/추론 결과 저장)
│
└── 🗂️ yolov3/                           # 🗂️ 레거시 (참고용)
    └── (YOLOv3 관련 파일)
```

---

## 📚 docs/ - 문서 디렉토리

### 문서 읽는 순서

#### 초보자 경로
```
1. README.md (메인)
   ↓
2. tutorials/01_quick_start.md (30분)
   ↓
3. docs/📚_문서_가이드.md (네비게이션)
   ↓
4. docs/2단계_RASPBERRY_PI_5_최적화_가이드.md
```

#### 고급자 경로
```
1. README.md
   ↓
2. docs/3단계_YOLO11_전체_워크플로우_가이드.md (완전 가이드)
   ↓
3. 실습 및 최적화
```

### 문서별 특징

| 문서 | 분량 | 난이도 | 대상 | 용도 |
|------|------|--------|------|------|
| README.md | 중간 | ⭐ | 모두 | 프로젝트 개요 |
| 📚_문서_가이드.md | 짧음 | ⭐ | 모두 | 문서 네비게이션 |
| 1단계_HAAR_CASCADE_vs_YOLO_비교분석.md | 중간 | ⭐⭐ | 비교 필요 | 기술 비교 |
| 2단계_RASPBERRY_PI_5_최적화_가이드.md | 길음 | ⭐⭐⭐ | Pi 5 사용자 | 최적화 |
| 3단계_YOLO11_전체_워크플로우_가이드.md | 매우 길음 | ⭐⭐⭐⭐ | 고급 | 완전 가이드 |
| 단계별_1_실행_가이드.md | 중간 | ⭐⭐ | 초급-중급 | 단계별 실행 |
| 단계별_2_실행_가이드_COMPLETE.md | 길음 | ⭐⭐⭐ | 중급-고급 | 완전 실행 |
| labelimg.md | 짧음 | ⭐ | 모두 | 라벨링 도구 |

---

## 🛠️ scripts/ - 스크립트 디렉토리

### dataset/ - 데이터셋 관리

#### dataset_splitter.py
```bash
# 용도: 데이터셋을 train/val/test로 분할
python scripts/dataset/dataset_splitter.py \
  --images dataset/images \
  --labels dataset/labels \
  --output yolo_dataset \
  --train_ratio 0.7 \
  --val_ratio 0.2 \
  --test_ratio 0.1
```

**기능**:
- 이미지-라벨 매칭 검증
- 랜덤 셔플 및 분할
- data.yaml 자동 생성
- 분할 결과 검증

#### create_data_yaml.py
```bash
# 용도: YOLO 훈련용 data.yaml 생성
python scripts/dataset/create_data_yaml.py \
  --dataset yolo_dataset \
  --classes stop go warning \
  --output yolo_dataset/data.yaml
```

### labeling/ - 라벨링 도구

#### label_quality_checker.py
```bash
# 용도: 라벨 품질 검증
python scripts/labeling/label_quality_checker.py \
  --images dataset/images \
  --labels dataset/labels \
  --output quality_report.txt
```

**검증 항목**:
- 이미지-라벨 매칭
- 바운딩 박스 유효성
- 클래스 ID 범위
- 중복 라벨 검출

### training/ - 모델 훈련

#### train_yolo11.py (범용)
```bash
# 용도: 일반적인 YOLO11 훈련
python scripts/training/train_yolo11.py \
  --data data.yaml \
  --model yolo11n.pt \
  --epochs 150 \
  --imgsz 640
```

#### train_yolo11_pi5_optimized.py ⭐ (Pi 5 최적화)
```bash
# 용도: 라즈베리파이 5 최적화 훈련
python scripts/training/train_yolo11_pi5_optimized.py \
  --data data.yaml \
  --epochs 150 \
  --imgsz 416 \
  --batch 32
```

**최적화 특징**:
- 이미지 크기: 416x416
- 배치 크기: 32
- 옵티마이저: AdamW
- 데이터 증강 최적화

### inference/ - 추론 및 테스트

#### test_inference.py
```bash
# 용도: 모델 테스트 및 추론
python scripts/inference/test_inference.py \
  --weights best.pt \
  --source test.jpg \
  --conf 0.5
```

**지원 소스**:
- 이미지 파일
- 비디오 파일
- 웹캠
- 폴더

---

## 💡 examples/ - 예제 코드

### basic_detection.py
```bash
# 용도: 가장 기본적인 객체 인식
python examples/basic_detection.py --source test.jpg
```

### real_time_webcam.py ⭐
```bash
# 용도: 실시간 웹캠 객체 인식
python examples/real_time_webcam.py --model yolo11n.pt
```

**기능**:
- 실시간 FPS 표시
- 키보드 제어
- 스크린샷 저장
- 신뢰도 조정

---

## 🎓 tutorials/ - 튜토리얼

### 01_quick_start.md ⭐
- **소요 시간**: 30분
- **난이도**: ⭐
- **내용**: 환경 설정부터 첫 모델 훈련까지

### 02_data_collection.md (예정)
- **소요 시간**: 1-2시간
- **난이도**: ⭐⭐
- **내용**: 데이터 수집 심화

### 03_model_training.md (예정)
- **소요 시간**: 2-3시간
- **난이도**: ⭐⭐⭐
- **내용**: 모델 훈련 심화

### 04_deployment.md (예정)
- **소요 시간**: 1-2시간
- **난이도**: ⭐⭐⭐
- **내용**: 라즈베리파이 배포

---

## 📦 model_data/ - 모델 파일

### 디렉토리 구조
```
model_data/
├── weights/
│   ├── yolo11n.pt              # Nano 모델
│   ├── yolo11s.pt              # Small 모델
│   ├── custom_best.pt          # 커스텀 모델
│   └── custom_best.onnx        # ONNX 변환
└── configs/
    ├── data.yaml               # 데이터셋 설정
    └── hyp.yaml                # 하이퍼파라미터
```

---

## 📊 results/ - 실험 결과

### 자동 생성 구조
```
results/
├── train/
│   └── exp1/
│       ├── weights/
│       │   ├── best.pt
│       │   └── last.pt
│       ├── results.png
│       ├── confusion_matrix.png
│       └── val_batch0_pred.jpg
└── predict/
    └── exp1/
        └── (추론 결과)
```

---

## 🔍 파일 찾기 가이드

### "X를 하고 싶어요"

#### 빠르게 시작하고 싶어요
→ `tutorials/01_quick_start.md`

#### 라즈베리파이 5에서 사용하고 싶어요
→ `docs/2단계_RASPBERRY_PI_5_최적화_가이드.md`
→ `scripts/training/train_yolo11_pi5_optimized.py`

#### 데이터셋을 준비하고 싶어요
→ `scripts/dataset/dataset_splitter.py`
→ `scripts/labeling/label_quality_checker.py`

#### 모델을 훈련하고 싶어요
→ `scripts/training/train_yolo11.py` (범용)
→ `scripts/training/train_yolo11_pi5_optimized.py` (Pi 5)

#### 실시간으로 테스트하고 싶어요
→ `examples/real_time_webcam.py`

#### 완전한 가이드를 보고 싶어요
→ `docs/3단계_YOLO11_전체_워크플로우_가이드.md`

---

## 📝 권장 워크플로우

### 1단계: 학습 (1-2시간)
```
README.md
  ↓
tutorials/01_quick_start.md
  ↓
docs/📚_문서_가이드.md
```

### 2단계: 실습 (2-3시간)
```
examples/basic_detection.py (테스트)
  ↓
scripts/dataset/dataset_splitter.py (데이터 준비)
  ↓
scripts/training/train_yolo11_pi5_optimized.py (훈련)
  ↓
examples/real_time_webcam.py (테스트)
```

### 3단계: 심화 (1-2일)
```
docs/2단계_RASPBERRY_PI_5_최적화_가이드.md
  ↓
하이퍼파라미터 튜닝
  ↓
모델 최적화 (ONNX)
  ↓
실전 배포
```

---

## 🔗 관련 링크

- **메인 README**: [README.md](README.md)
- **문서 가이드**: [docs/📚_문서_가이드.md](docs/📚_문서_가이드.md)
- **빠른 시작**: [tutorials/01_quick_start.md](tutorials/01_quick_start.md)
- **Pi 5 최적화**: [docs/2단계_RASPBERRY_PI_5_최적화_가이드.md](docs/2단계_RASPBERRY_PI_5_최적화_가이드.md)

---

**버전**: 1.0  
**최종 업데이트**: 2024-12-16  
**프로젝트**: Raspbot v2 자율주행 자동차

