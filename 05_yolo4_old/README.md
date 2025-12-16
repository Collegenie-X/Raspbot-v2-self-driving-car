# 🎯 YOLOv4 커스텀 모델 제작 완전 가이드

> **라즈베리파이 자율주행 자동차를 위한 YOLOv4-tiny 커스텀 객체 인식 모델 제작**

## 📚 프로젝트 개요

이 프로젝트는 YOLOv4-tiny를 활용하여 커스텀 객체 인식 모델을 처음부터 끝까지 만드는 완전한 가이드입니다.
- 데이터 수집 → 라벨링 → 모델 훈련 → 테스트 → 배포까지 전 과정 포함
- 라즈베리파이에 최적화된 경량 모델 (YOLOv4-tiny)
- 실전 예제: 쓰레기 분류, 교통 표지판 인식 등

---

## 🎯 학습 목표

이 가이드를 완료하면 다음을 할 수 있습니다:

✅ YOLOv4의 작동 원리 이해  
✅ 커스텀 데이터셋 수집 및 라벨링  
✅ YOLOv4-tiny 모델 훈련  
✅ 모델 성능 평가 및 최적화  
✅ 라즈베리파이에 모델 배포 및 실시간 추론

---

## 📂 프로젝트 구조

```
05_yolo4_old/
├── README.md                          # 본 파일 (전체 가이드)
├── docs/                              # 상세 문서
│   ├── 1_YOLOv4_소개_및_환경설정.md
│   ├── 2_데이터셋_준비_가이드.md
│   ├── 3_모델_훈련_가이드.md
│   ├── 4_모델_평가_및_최적화.md
│   └── 5_라즈베리파이_배포_가이드.md
├── scripts/                           # 유틸리티 스크립트
│   ├── data_preparation/              # 데이터 준비
│   │   ├── collect_images.py          # 이미지 수집
│   │   ├── label_converter.py         # 라벨 포맷 변환
│   │   └── dataset_split.py           # 데이터셋 분할
│   ├── training/                      # 모델 훈련
│   │   ├── train_yolov4_tiny.py       # YOLOv4-tiny 훈련
│   │   └── config_generator.py        # 설정 파일 생성
│   ├── inference/                     # 추론 및 테스트
│   │   ├── test_model.py              # 모델 테스트
│   │   └── real_time_detection.py    # 실시간 객체 인식
│   └── evaluation/                    # 모델 평가
│       └── calculate_map.py           # mAP 계산
├── examples/                          # 예제 코드
│   ├── custom_detector.py             # 커스텀 검출기 (개선된 garbage_identify)
│   ├── traffic_sign_detector.py       # 교통표지판 인식 예제
│   └── multi_class_detector.py        # 다중 클래스 인식
├── model_data/                        # 모델 파일
│   ├── yolo4_tiny.cfg                 # YOLOv4-tiny 설정
│   ├── yolo4_tiny.weights             # 사전 훈련 가중치
│   ├── custom_classes.txt             # 클래스 이름
│   └── anchors.txt                    # 앵커 박스
└── dataset/                           # 데이터셋 (예제)
    ├── images/                        # 이미지 파일
    ├── labels/                        # 라벨 파일 (YOLO 포맷)
    ├── train/                         # 훈련 데이터
    ├── val/                           # 검증 데이터
    └── test/                          # 테스트 데이터
```

---

## 🚀 빠른 시작 (Quick Start)

### 1단계: 환경 설정

```bash
# 1. 필수 패키지 설치
pip install tensorflow==2.10.0 keras opencv-python numpy pillow

# 2. Darknet 설치 (YOLOv4 훈련용)
git clone https://github.com/AlexeyAB/darknet
cd darknet
make

# 3. 사전 훈련된 가중치 다운로드
wget https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v4_pre/yolov4-tiny.conv.29
```

### 2단계: 데이터셋 준비

```bash
# 이미지 수집
python scripts/data_preparation/collect_images.py \
  --output dataset/images \
  --num_images 500

# 라벨링 (LabelImg 사용)
labelImg dataset/images dataset/labels

# 데이터셋 분할 (train/val/test)
python scripts/data_preparation/dataset_split.py \
  --images dataset/images \
  --labels dataset/labels \
  --train_ratio 0.7 \
  --val_ratio 0.2 \
  --test_ratio 0.1
```

### 3단계: 모델 훈련

```bash
# 설정 파일 생성
python scripts/training/config_generator.py \
  --classes garbage plastic metal paper glass \
  --output model_data

# YOLOv4-tiny 훈련
python scripts/training/train_yolov4_tiny.py \
  --data dataset/data.yaml \
  --cfg model_data/yolo4_tiny_custom.cfg \
  --weights model_data/yolo4_tiny.conv.29 \
  --epochs 300 \
  --batch 64
```

### 4단계: 모델 테스트

```bash
# 이미지로 테스트
python scripts/inference/test_model.py \
  --weights model_data/custom_best.weights \
  --config model_data/yolo4_tiny_custom.cfg \
  --image test_image.jpg

# 실시간 추론 (웹캠)
python scripts/inference/real_time_detection.py \
  --weights model_data/custom_best.weights \
  --config model_data/yolo4_tiny_custom.cfg \
  --webcam 0
```

---

## 📖 상세 가이드

### 📄 문서 읽는 순서

| 순서 | 문서 | 내용 | 소요 시간 |
|------|------|------|----------|
| 1 | [1_YOLOv4_소개_및_환경설정.md](docs/1_YOLOv4_소개_및_환경설정.md) | YOLOv4 원리, 환경 설정 | 1시간 |
| 2 | [2_데이터셋_준비_가이드.md](docs/2_데이터셋_준비_가이드.md) | 데이터 수집, 라벨링 | 2-3시간 |
| 3 | [3_모델_훈련_가이드.md](docs/3_모델_훈련_가이드.md) | 모델 훈련 및 설정 | 3-4시간 |
| 4 | [4_모델_평가_및_최적화.md](docs/4_모델_평가_및_최적화.md) | 성능 평가, 최적화 | 2-3시간 |
| 5 | [5_라즈베리파이_배포_가이드.md](docs/5_라즈베리파이_배포_가이드.md) | 라즈베리파이 배포 | 2시간 |

---

## 💡 주요 특징

### 1. 경량화 (YOLOv4-tiny)
- **모델 크기**: ~23MB (YOLOv4: ~250MB)
- **추론 속도**: 라즈베리파이 4에서 ~15-20 FPS
- **정확도**: mAP@0.5 ~40-60% (데이터셋에 따라 다름)

### 2. 라즈베리파이 최적화
```python
# TensorFlow Lite 변환
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_model = converter.convert()

# 추론 최적화
interpreter = tf.lite.Interpreter(model_path="model.tflite")
interpreter.allocate_tensors()
```

### 3. 실시간 추론
```python
# 예제: 실시간 객체 인식
detector = CustomDetector(
    model_path="model_data/custom_best.h5",
    classes_path="model_data/classes.txt",
    score_threshold=0.5,
    iou_threshold=0.3
)

while True:
    ret, frame = camera.read()
    detections, frame = detector.detect(frame)
    cv2.imshow("Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
```

---

## 🎓 학습 경로

### 초급 경로 (처음 시작)
```
1. YOLOv4 기본 개념 이해
   ↓
2. 사전 훈련된 모델로 테스트
   ↓
3. 소량 데이터로 파인튜닝 (50-100장)
   ↓
4. 간단한 2-3 클래스 인식
```

### 중급 경로 (실전 프로젝트)
```
1. 대규모 데이터셋 구축 (500+ 장)
   ↓
2. 데이터 증강 기법 적용
   ↓
3. 하이퍼파라미터 튜닝
   ↓
4. 5-10 클래스 다중 객체 인식
```

### 고급 경로 (최적화 및 배포)
```
1. 모델 경량화 (Quantization)
   ↓
2. TensorFlow Lite 변환
   ↓
3. 라즈베리파이 실시간 추론 최적화
   ↓
4. 실전 자율주행 통합
```

---

## 📊 성능 벤치마크

### 라즈베리파이 4 (4GB)

| 모델 | 이미지 크기 | FPS | mAP@0.5 | 모델 크기 |
|------|------------|-----|---------|----------|
| YOLOv4-tiny | 416x416 | 18-22 | 45-60% | 23MB |
| YOLOv4-tiny | 320x320 | 25-30 | 40-55% | 23MB |
| YOLOv3-tiny | 416x416 | 15-20 | 35-50% | 34MB |

### 라즈베리파이 5 (8GB)

| 모델 | 이미지 크기 | FPS | mAP@0.5 | 모델 크기 |
|------|------------|-----|---------|----------|
| YOLOv4-tiny | 416x416 | 30-35 | 45-60% | 23MB |
| YOLOv4-tiny | 320x320 | 40-45 | 40-55% | 23MB |
| YOLOv4 | 416x416 | 8-12 | 65-80% | 250MB |

---

## 🛠️ 스크립트 사용법

### 데이터 준비 스크립트

#### 1. 이미지 수집
```bash
python scripts/data_preparation/collect_images.py \
  --source webcam \              # 소스: webcam, video, folder
  --output dataset/images \      # 출력 디렉토리
  --num_images 500 \             # 수집할 이미지 수
  --interval 0.5                 # 캡처 간격 (초)
```

#### 2. 라벨 포맷 변환
```bash
python scripts/data_preparation/label_converter.py \
  --input_format pascal_voc \    # 입력 포맷: pascal_voc, coco
  --output_format yolo \         # 출력 포맷: yolo
  --input dataset/annotations \  # 입력 디렉토리
  --output dataset/labels        # 출력 디렉토리
```

#### 3. 데이터셋 분할
```bash
python scripts/data_preparation/dataset_split.py \
  --images dataset/images \
  --labels dataset/labels \
  --output dataset \
  --train_ratio 0.7 \
  --val_ratio 0.2 \
  --test_ratio 0.1 \
  --seed 42                      # 재현성을 위한 시드
```

### 모델 훈련 스크립트

#### 1. 설정 파일 생성
```bash
python scripts/training/config_generator.py \
  --classes garbage plastic metal paper glass \
  --width 416 \
  --height 416 \
  --batch 64 \
  --subdivisions 16 \
  --output model_data/yolo4_tiny_custom.cfg
```

#### 2. 모델 훈련
```bash
python scripts/training/train_yolov4_tiny.py \
  --data dataset/data.yaml \
  --cfg model_data/yolo4_tiny_custom.cfg \
  --weights model_data/yolo4_tiny.conv.29 \
  --epochs 300 \
  --batch 64 \
  --img_size 416 \
  --device 0 \                   # GPU ID (CPU는 -1)
  --workers 4                    # 데이터 로더 워커 수
```

### 추론 및 평가 스크립트

#### 1. 모델 테스트
```bash
# 단일 이미지
python scripts/inference/test_model.py \
  --weights model_data/custom_best.weights \
  --config model_data/yolo4_tiny_custom.cfg \
  --classes model_data/classes.txt \
  --source test.jpg \
  --output results/

# 폴더 내 모든 이미지
python scripts/inference/test_model.py \
  --weights model_data/custom_best.weights \
  --config model_data/yolo4_tiny_custom.cfg \
  --classes model_data/classes.txt \
  --source test_images/ \
  --output results/

# 동영상
python scripts/inference/test_model.py \
  --weights model_data/custom_best.weights \
  --config model_data/yolo4_tiny_custom.cfg \
  --classes model_data/classes.txt \
  --source test_video.mp4 \
  --output results/output.mp4
```

#### 2. 실시간 추론
```bash
python scripts/inference/real_time_detection.py \
  --weights model_data/custom_best.weights \
  --config model_data/yolo4_tiny_custom.cfg \
  --classes model_data/classes.txt \
  --webcam 0 \                   # 웹캠 ID
  --conf_threshold 0.5 \         # 신뢰도 임계값
  --iou_threshold 0.3            # NMS IoU 임계값
```

#### 3. 모델 평가 (mAP 계산)
```bash
python scripts/evaluation/calculate_map.py \
  --weights model_data/custom_best.weights \
  --config model_data/yolo4_tiny_custom.cfg \
  --data dataset/data.yaml \
  --iou_threshold 0.5
```

---

## 🎯 실전 예제

### 예제 1: 쓰레기 분류 (5 클래스)

```python
from examples.custom_detector import CustomDetector

# 검출기 초기화
detector = CustomDetector(
    model_path="model_data/garbage_best.h5",
    classes_path="model_data/garbage_classes.txt",
    anchors_path="model_data/anchors.txt",
    score_threshold=0.5,
    iou_threshold=0.3
)

# 이미지 추론
image = cv2.imread("test_image.jpg")
detections, result_image = detector.detect(image)

# 결과 출력
for det in detections:
    print(f"클래스: {det['class']}, 신뢰도: {det['confidence']:.2f}")
    print(f"위치: {det['bbox']}")

cv2.imshow("Result", result_image)
cv2.waitKey(0)
```

### 예제 2: 교통 표지판 인식

```python
from examples.traffic_sign_detector import TrafficSignDetector

# 검출기 초기화
detector = TrafficSignDetector(
    model_path="model_data/traffic_sign_best.h5",
    conf_threshold=0.6
)

# 실시간 추론
camera = cv2.VideoCapture(0)
while True:
    ret, frame = camera.read()
    if not ret:
        break
    
    signs, frame = detector.detect(frame)
    
    # 제어 로직
    for sign in signs:
        if sign['class'] == 'stop':
            print("정지 표지판 감지! 차량 정지")
            # 차량 제어 코드
        elif sign['class'] == 'speed_limit':
            print(f"속도 제한: {sign['value']}km/h")
    
    cv2.imshow("Traffic Sign Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
```

---

## 🔧 트러블슈팅

### 일반적인 문제 및 해결

#### 1. GPU 메모리 부족
```bash
# 배치 크기 줄이기
--batch 32  # 64에서 32로

# Subdivisions 늘리기 (cfg 파일)
subdivisions=32  # 16에서 32로
```

#### 2. 낮은 mAP
```python
# 더 많은 데이터 수집 (최소 500장 권장)
# 데이터 증강 적용
augmentation = {
    'flip': True,
    'rotation': 15,
    'brightness': 0.2,
    'saturation': 0.3
}

# 더 긴 훈련 (300+ 에폭)
# Learning rate 조정
```

#### 3. 느린 추론 속도
```python
# 이미지 크기 줄이기
img_size = 320  # 416에서 320으로

# TensorFlow Lite 변환
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]

# INT8 양자화 적용
def representative_dataset():
    for _ in range(100):
        yield [np.random.randn(1, 416, 416, 3).astype(np.float32)]

converter.representative_dataset = representative_dataset
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
```

#### 4. 클래스 불균형
```python
# 클래스별 가중치 적용
class_weights = {
    0: 1.0,  # 많은 클래스
    1: 2.0,  # 적은 클래스 (가중치 2배)
    2: 1.5
}

# 오버샘플링
from imblearn.over_sampling import RandomOverSampler
```

---

## 📈 모델 최적화 팁

### 1. 데이터 증강
```python
import albumentations as A

transform = A.Compose([
    A.HorizontalFlip(p=0.5),
    A.RandomBrightnessContrast(p=0.3),
    A.Rotate(limit=15, p=0.3),
    A.GaussNoise(p=0.2),
    A.MotionBlur(p=0.2)
], bbox_params=A.BboxParams(format='yolo'))
```

### 2. 하이퍼파라미터 튜닝
```yaml
# data.yaml
train: dataset/train
val: dataset/val
nc: 5  # 클래스 수
names: ['class1', 'class2', 'class3', 'class4', 'class5']

# 하이퍼파라미터
lr0: 0.01         # 초기 학습률
momentum: 0.937
weight_decay: 0.0005
warmup_epochs: 3
mosaic: 1.0       # 모자이크 증강
```

### 3. 앵커 박스 최적화
```bash
# 데이터셋에 맞는 앵커 계산
python scripts/training/calculate_anchors.py \
  --data dataset/data.yaml \
  --num_clusters 6 \
  --output model_data/anchors.txt
```

---

## 🔗 참고 자료

### 공식 문서
- [YOLOv4 논문](https://arxiv.org/abs/2004.10934)
- [Darknet GitHub](https://github.com/AlexeyAB/darknet)
- [TensorFlow](https://www.tensorflow.org/)

### 유용한 도구
- [LabelImg](https://github.com/HumanSignal/labelImg) - 이미지 라벨링 도구
- [Netron](https://netron.app/) - 모델 시각화 도구
- [WandB](https://wandb.ai/) - 실험 추적 도구

### 추가 학습 자료
- [YOLOv4 Tutorial](https://github.com/AlexeyAB/darknet#how-to-train-to-detect-your-custom-objects)
- [Object Detection Metrics](https://github.com/rafaelpadilla/Object-Detection-Metrics)

---

## 📝 체크리스트

### 데이터셋 준비
- [ ] 클래스 정의 (2-10개 권장)
- [ ] 이미지 수집 (클래스당 최소 100장)
- [ ] 이미지 라벨링 (LabelImg)
- [ ] 데이터셋 분할 (train/val/test)
- [ ] 라벨 품질 검증

### 모델 훈련
- [ ] 환경 설정 완료
- [ ] 설정 파일 생성
- [ ] 사전 훈련 가중치 다운로드
- [ ] 모델 훈련 (300+ 에폭)
- [ ] 훈련 로그 확인

### 모델 평가
- [ ] mAP 계산 (목표: >0.5)
- [ ] 클래스별 정확도 확인
- [ ] 오탐지/미탐지 분석
- [ ] 혼동 행렬 분석

### 배포
- [ ] 모델 경량화 (TFLite)
- [ ] 라즈베리파이 테스트
- [ ] 실시간 추론 FPS 확인 (목표: >15)
- [ ] 실전 환경 테스트

---

## 🤝 기여 및 문의

### 기여 방법
1. 이슈 등록: 버그, 개선 사항, 질문
2. Pull Request: 코드 개선, 문서 수정
3. 예제 공유: 새로운 사용 사례

### 문의
- GitHub Issues
- 이메일: [프로젝트 이메일]

---

## 📄 라이선스

본 프로젝트는 MIT 라이선스를 따릅니다.

---

## 🎉 다음 단계

### 1. 기본 학습 완료 후
- [ ] YOLOv5, YOLOv8 비교 학습
- [ ] 앙상블 모델 구축
- [ ] 실시간 추적 (DeepSORT) 통합

### 2. 실전 프로젝트
- [ ] 자율주행 자동차에 통합
- [ ] 교통 표지판 인식 시스템
- [ ] 쓰레기 자동 분류 시스템

### 3. 고급 주제
- [ ] 모델 압축 기법 (Pruning, Quantization)
- [ ] Edge TPU 배포
- [ ] 모바일 최적화 (TFLite, ONNX)

---

**시작하기**: [1_YOLOv4_소개_및_환경설정.md](docs/1_YOLOv4_소개_및_환경설정.md) 👈 여기서 시작하세요!

**버전**: 1.0  
**최종 업데이트**: 2024-12-16  
**프로젝트**: Raspbot v2 자율주행 자동차

