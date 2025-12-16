# 🎯 YOLO11 커스텀 객체 인식 - 완전 가이드

> **라즈베리파이 5 최적화 | 실시간 객체 인식 | 커스텀 모델 제작**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![YOLO](https://img.shields.io/badge/YOLO-v11-green.svg)](https://github.com/ultralytics/ultralytics)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-5-red.svg)](https://www.raspberrypi.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📚 프로젝트 개요

**최신 YOLO11**을 활용한 커스텀 객체 인식 모델 제작 완전 가이드입니다.
- ✅ 데이터 수집부터 배포까지 전 과정 포함
- ✅ 라즈베리파이 5 최적화 (25-30 FPS)
- ✅ 실전 예제 및 자율주행 통합
- ✅ 12,000+ 줄의 상세한 문서

---

## 🎯 학습 목표

이 가이드를 완료하면 다음을 할 수 있습니다:

✅ **YOLO11의 작동 원리 완전 이해**  
✅ **커스텀 데이터셋 수집 및 라벨링**  
✅ **라즈베리파이 5 최적화 모델 훈련**  
✅ **실시간 객체 인식 시스템 구축**  
✅ **자율주행 자동차에 통합**

---

## 📂 프로젝트 구조

```
05_yolo/
├── 📄 README.md                          # 본 파일 (메인 가이드)
├── 📚 docs/                              # 상세 문서
│   ├── 📚_문서_가이드.md                 # 문서 네비게이션
│   ├── 1단계_HAAR_CASCADE_vs_YOLO_비교분석.md
│   ├── 2단계_RASPBERRY_PI_5_최적화_가이드.md
│   ├── 3단계_YOLO11_전체_워크플로우_가이드.md
│   ├── 단계별_1_실행_가이드.md
│   └── 단계별_2_실행_가이드_COMPLETE.md
├── 🛠️ scripts/                          # 유틸리티 스크립트
│   ├── dataset/                         # 데이터셋 관리
│   │   ├── dataset_splitter.py          # 데이터셋 분할
│   │   └── create_data_yaml.py          # 설정 파일 생성
│   ├── labeling/                        # 라벨링 도구
│   │   └── label_quality_checker.py     # 라벨 품질 검증
│   ├── training/                        # 모델 훈련
│   │   ├── train_yolo11.py              # 범용 훈련
│   │   └── train_yolo11_pi5_optimized.py # Pi 5 최적화
│   ├── inference/                       # 추론 및 테스트
│   │   └── test_inference.py            # 모델 테스트
│   └── deployment/                      # 배포 도구
├── 💡 examples/                          # 예제 코드
│   ├── basic_detection.py               # 기본 객체 인식
│   ├── real_time_webcam.py              # 실시간 웹캠
│   ├── traffic_sign_detection.py        # 교통표지판 인식
│   └── autonomous_driving_integration.py # 자율주행 통합
├── 🎓 tutorials/                         # 튜토리얼
│   ├── 01_quick_start.md                # 빠른 시작
│   ├── 02_data_collection.md            # 데이터 수집
│   ├── 03_model_training.md             # 모델 훈련
│   └── 04_deployment.md                 # 배포
├── 📦 model_data/                        # 모델 파일
│   ├── weights/                         # 가중치 파일
│   └── configs/                         # 설정 파일
├── 🔧 labelImg-master/                   # 라벨링 도구
└── 📊 results/                           # 실험 결과
```

---

## 🚀 빠른 시작 (30분)

### 1단계: 환경 설정 (5분)

```bash
# 1. 저장소 클론
cd ~/Documents/GitHub/Raspbot-v2-self-driving-car/05_yolo

# 2. 가상환경 생성
python3 -m venv yolo_env
source yolo_env/bin/activate

# 3. 패키지 설치
pip install ultralytics opencv-python pillow pyyaml tqdm
```

### 2단계: 사전 훈련 모델 테스트 (5분)

```bash
# 웹캠으로 실시간 객체 인식
python examples/real_time_webcam.py --model yolo11n.pt
```

### 3단계: 커스텀 데이터 준비 (10분)

```bash
# 데이터 수집 (웹캠)
python scripts/dataset/collect_images.py \
  --source webcam \
  --output dataset/images \
  --num_images 100

# 라벨링 (LabelImg)
labelImg dataset/images dataset/labels

# 데이터셋 분할
python scripts/dataset/dataset_splitter.py \
  --images dataset/images \
  --labels dataset/labels \
  --output yolo_dataset
```

### 4단계: 모델 훈련 (10분)

```bash
# 라즈베리파이 5 최적화 훈련
python scripts/training/train_yolo11_pi5_optimized.py \
  --data yolo_dataset/data.yaml \
  --epochs 50 \
  --imgsz 416
```

---

## 📖 문서 가이드

### 🎯 상황별 추천 문서

#### 1️⃣ 완전 초보자 (처음 시작)

**시작 순서**:
1. 📖 [README.md](README.md) - **본 문서 (여기)**
2. 🚀 [tutorials/01_quick_start.md](tutorials/01_quick_start.md) - 30분 빠른 시작
3. 📚 [docs/📚_문서_가이드.md](docs/📚_문서_가이드.md) - 문서 네비게이션

#### 2️⃣ Raspberry Pi 5 사용자 (권장!)

**필수 문서**:
1. 🍓 [docs/2단계_RASPBERRY_PI_5_최적화_가이드.md](docs/2단계_RASPBERRY_PI_5_최적화_가이드.md) - **핵심!**
   - Pi 5 vs Pi 4 비교
   - YOLOv11n 커스텀 훈련
   - 성능 최적화 (25-30 FPS)
   - 하이퍼파라미터 완전 가이드

2. 📋 [docs/단계별_1_실행_가이드.md](docs/단계별_1_실행_가이드.md) - 단계별 실행

#### 3️⃣ Haar Cascade에서 전환

**비교 문서**:
- ⚖️ [docs/1단계_HAAR_CASCADE_vs_YOLO_비교분석.md](docs/1단계_HAAR_CASCADE_vs_YOLO_비교분석.md)
  - 기술 개요 및 성능 비교
  - 실제 테스트 결과
  - 마이그레이션 가이드

#### 4️⃣ 고급 사용자 (깊이 이해)

**전체 문서**:
- 📚 [docs/3단계_YOLO11_전체_워크플로우_가이드.md](docs/3단계_YOLO11_전체_워크플로우_가이드.md)
  - 12,000+ 줄 완전 가이드
  - 알고리즘 상세 설명
  - 트러블슈팅 완벽 가이드

---

## 💡 주요 특징

### 1. 라즈베리파이 5 최적화

| 항목 | 최적화 전 | 최적화 후 |
|------|----------|----------|
| 모델 | YOLOv11s | YOLOv11n |
| 이미지 크기 | 640x640 | 416x416 |
| FPS | 8-12 | 25-30 |
| mAP50 | 0.85 | 0.75-0.85 |
| 모델 크기 | 22MB | 6MB |

### 2. 실시간 객체 인식

```python
from ultralytics import YOLO

# 모델 로드
model = YOLO('yolo11n.pt')

# 실시간 추론
results = model.predict(
    source=0,              # 웹캠
    conf=0.35,             # 신뢰도 임계값
    iou=0.5,               # NMS IoU 임계값
    show=True,             # 결과 표시
    stream=True            # 스트리밍 모드
)

for result in results:
    boxes = result.boxes   # 바운딩 박스
    print(f"검출된 객체: {len(boxes)}개")
```

### 3. 커스텀 모델 훈련

```python
from ultralytics import YOLO

# 모델 초기화
model = YOLO('yolo11n.pt')

# 훈련
results = model.train(
    data='data.yaml',      # 데이터셋 설정
    epochs=150,            # 에폭 수
    imgsz=416,             # 이미지 크기
    batch=32,              # 배치 크기
    device='cpu',          # CPU 사용
    optimizer='AdamW',     # 옵티마이저
    lr0=0.01,              # 초기 학습률
    augment=True           # 데이터 증강
)
```

---

## 🛠️ 스크립트 사용법

### 데이터셋 관리

#### 1. 데이터셋 분할

```bash
python scripts/dataset/dataset_splitter.py \
  --images dataset/images \
  --labels dataset/labels \
  --output yolo_dataset \
  --train_ratio 0.7 \
  --val_ratio 0.2 \
  --test_ratio 0.1
```

#### 2. data.yaml 생성

```bash
python scripts/dataset/create_data_yaml.py \
  --dataset yolo_dataset \
  --classes stop go left right \
  --output yolo_dataset/data.yaml
```

#### 3. 라벨 품질 검증

```bash
python scripts/labeling/label_quality_checker.py \
  --images dataset/images \
  --labels dataset/labels \
  --output quality_report.txt
```

### 모델 훈련

#### 1. 범용 훈련

```bash
python scripts/training/train_yolo11.py \
  --data yolo_dataset/data.yaml \
  --model yolo11n.pt \
  --epochs 150 \
  --imgsz 640 \
  --batch 16
```

#### 2. 라즈베리파이 5 최적화 훈련

```bash
python scripts/training/train_yolo11_pi5_optimized.py \
  --data yolo_dataset/data.yaml \
  --epochs 150 \
  --imgsz 416 \
  --batch 32 \
  --device cpu
```

### 추론 및 테스트

#### 1. 모델 테스트

```bash
# 이미지
python scripts/inference/test_inference.py \
  --weights best.pt \
  --source test.jpg

# 웹캠
python scripts/inference/test_inference.py \
  --weights best.pt \
  --source webcam

# 비디오
python scripts/inference/test_inference.py \
  --weights best.pt \
  --source video.mp4
```

---

## 🎓 학습 경로

### 초급 경로 (1-2일)

```
1. 환경 설정 (1시간)
   ↓
2. 사전 훈련 모델 테스트 (30분)
   ↓
3. 소량 데이터 수집 (50-100장, 2시간)
   ↓
4. 간단한 2-3 클래스 훈련 (3-4시간)
   ↓
5. 실시간 추론 테스트 (1시간)
```

### 중급 경로 (3-5일)

```
1. 대규모 데이터셋 구축 (500+ 장, 1일)
   ↓
2. 데이터 증강 및 전처리 (반나절)
   ↓
3. 하이퍼파라미터 튜닝 (1일)
   ↓
4. 5-10 클래스 다중 객체 인식 (1-2일)
   ↓
5. 성능 최적화 (반나절)
```

### 고급 경로 (1-2주)

```
1. 알고리즘 깊이 이해 (2-3일)
   ↓
2. 커스텀 아키텍처 수정 (2-3일)
   ↓
3. 모델 경량화 (ONNX, TFLite, 2일)
   ↓
4. 엣지 디바이스 최적화 (2-3일)
   ↓
5. 실전 자율주행 통합 (3-4일)
```

---

## 📊 성능 벤치마크

### 라즈베리파이 5 (8GB)

| 모델 | 이미지 크기 | FPS | mAP@0.5 | 모델 크기 | 메모리 |
|------|------------|-----|---------|----------|--------|
| YOLOv11n | 416x416 | 25-30 | 0.75-0.85 | 6MB | ~500MB |
| YOLOv11n | 320x320 | 35-40 | 0.70-0.80 | 6MB | ~400MB |
| YOLOv11s | 416x416 | 15-20 | 0.80-0.90 | 22MB | ~800MB |
| YOLOv11m | 416x416 | 8-12 | 0.85-0.92 | 50MB | ~1.2GB |

### 라즈베리파이 4 (4GB)

| 모델 | 이미지 크기 | FPS | mAP@0.5 | 모델 크기 |
|------|------------|-----|---------|----------|
| YOLOv11n | 416x416 | 15-18 | 0.75-0.85 | 6MB |
| YOLOv11n | 320x320 | 20-25 | 0.70-0.80 | 6MB |

---

## 🎯 실전 예제

### 예제 1: 교통 표지판 인식

```python
from ultralytics import YOLO
import cv2

# 모델 로드
model = YOLO('traffic_sign_best.pt')

# 웹캠 초기화
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # 추론
    results = model(frame, conf=0.5)
    
    # 결과 처리
    for result in results:
        boxes = result.boxes
        for box in boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            class_name = model.names[cls]
            
            # 제어 로직
            if class_name == 'stop' and conf > 0.7:
                print("🛑 정지 표지판 감지! 차량 정지")
                # 차량 제어 코드
            elif class_name == 'speed_limit':
                print(f"⚠️  속도 제한 표지판")
    
    # 결과 표시
    annotated = results[0].plot()
    cv2.imshow('Traffic Sign Detection', annotated)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

### 예제 2: 자율주행 통합

```python
from ultralytics import YOLO
import cv2

class AutonomousDriving:
    def __init__(self, model_path='best.pt'):
        self.model = YOLO(model_path)
        self.cap = cv2.VideoCapture(0)
    
    def detect_and_control(self):
        """객체 검출 및 차량 제어"""
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            # 객체 검출
            results = self.model(frame, conf=0.35)
            
            # 제어 로직
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    cls = int(box.cls[0])
                    class_name = self.model.names[cls]
                    
                    # 장애물 회피
                    if class_name == 'obstacle':
                        self.avoid_obstacle()
                    # 라인 팔로잉
                    elif class_name == 'lane':
                        self.follow_lane(box)
                    # 표지판 인식
                    elif class_name in ['stop', 'go']:
                        self.handle_traffic_sign(class_name)
            
            # 화면 표시
            annotated = results[0].plot()
            cv2.imshow('Autonomous Driving', annotated)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    def avoid_obstacle(self):
        """장애물 회피 로직"""
        print("⚠️  장애물 감지! 회피 중...")
        # 차량 제어 코드
    
    def follow_lane(self, box):
        """라인 팔로잉 로직"""
        # PID 제어 등
        pass
    
    def handle_traffic_sign(self, sign):
        """교통 표지판 처리"""
        if sign == 'stop':
            print("🛑 정지")
        elif sign == 'go':
            print("✅ 출발")

# 실행
if __name__ == "__main__":
    driver = AutonomousDriving('best.pt')
    driver.detect_and_control()
```

---

## 🔧 트러블슈팅

### 일반적인 문제

#### 1. 낮은 FPS

**해결 방법**:
```python
# 이미지 크기 줄이기
model.predict(source=0, imgsz=320)

# ONNX 변환
model.export(format='onnx')
model_onnx = YOLO('best.onnx')

# 배치 처리 비활성화
model.predict(source=0, stream=True)
```

#### 2. 낮은 정확도

**해결 방법**:
```bash
# 더 많은 데이터 수집 (최소 500장)
# 더 긴 훈련 (150+ 에폭)
# 데이터 증강 활성화
# 하이퍼파라미터 튜닝
```

#### 3. 메모리 부족

**해결 방법**:
```python
# 배치 크기 줄이기
model.train(data='data.yaml', batch=8)

# 더 작은 모델 사용
model = YOLO('yolo11n.pt')  # nano 모델

# 이미지 크기 줄이기
model.train(data='data.yaml', imgsz=320)
```

---

## 📈 모델 최적화 팁

### 1. 데이터 증강

```yaml
# data.yaml에 추가
augment: true
hsv_h: 0.015
hsv_s: 0.7
hsv_v: 0.4
degrees: 10.0
translate: 0.1
scale: 0.5
shear: 0.0
perspective: 0.0
flipud: 0.0
fliplr: 0.5
mosaic: 1.0
mixup: 0.0
```

### 2. 하이퍼파라미터 튜닝

```python
model.train(
    data='data.yaml',
    epochs=150,
    imgsz=416,
    batch=32,
    lr0=0.01,              # 초기 학습률
    lrf=0.01,              # 최종 학습률
    momentum=0.937,
    weight_decay=0.0005,
    warmup_epochs=3,
    warmup_momentum=0.8,
    warmup_bias_lr=0.1,
    box=7.5,               # 박스 손실 가중치
    cls=0.5,               # 클래스 손실 가중치
    dfl=1.5,               # DFL 손실 가중치
    optimizer='AdamW'
)
```

### 3. 모델 변환

```python
# ONNX 변환 (추론 속도 향상)
model.export(format='onnx', dynamic=False, simplify=True)

# TensorFlow Lite 변환 (모바일/엣지)
model.export(format='tflite', int8=True)

# OpenVINO 변환 (Intel 하드웨어)
model.export(format='openvino')
```

---

## 📝 체크리스트

### 데이터셋 준비
- [ ] 클래스 정의 (2-10개 권장)
- [ ] 이미지 수집 (클래스당 최소 100장)
- [ ] 이미지 라벨링 (YOLO 포맷)
- [ ] 데이터셋 분할 (train/val/test)
- [ ] 라벨 품질 검증

### 모델 훈련
- [ ] 환경 설정 완료
- [ ] 데이터셋 준비 완료
- [ ] 하이퍼파라미터 설정
- [ ] 모델 훈련 (150+ 에폭)
- [ ] 훈련 로그 확인

### 모델 평가
- [ ] mAP 계산 (목표: >0.70)
- [ ] 클래스별 정확도 확인
- [ ] FPS 측정 (목표: >20)
- [ ] 실전 환경 테스트

### 배포
- [ ] 모델 최적화 (ONNX)
- [ ] 라즈베리파이 테스트
- [ ] 실시간 추론 확인
- [ ] 자율주행 통합

---

## 🔗 참고 자료

### 공식 문서
- [Ultralytics YOLO11](https://docs.ultralytics.com/)
- [Raspberry Pi](https://www.raspberrypi.com/documentation/)
- [OpenCV](https://docs.opencv.org/)

### 유용한 도구
- [LabelImg](https://github.com/HumanSignal/labelImg) - 이미지 라벨링
- [Netron](https://netron.app/) - 모델 시각화
- [WandB](https://wandb.ai/) - 실험 추적

### 커뮤니티
- [Ultralytics GitHub](https://github.com/ultralytics/ultralytics)
- [Raspberry Pi Forums](https://forums.raspberrypi.com/)
- [r/computervision](https://reddit.com/r/computervision)

---

## 🤝 기여 및 문의

### 기여 방법
1. 이슈 등록: 버그, 개선 사항, 질문
2. Pull Request: 코드 개선, 문서 수정
3. 예제 공유: 새로운 사용 사례

### 문의
- GitHub Issues
- 프로젝트 이메일

---

## 📄 라이선스

본 프로젝트는 MIT 라이선스를 따릅니다.

---

## 🎉 다음 단계

### 기본 학습 완료 후
- [ ] YOLOv8, YOLOv10 비교 학습
- [ ] 앙상블 모델 구축
- [ ] 실시간 추적 (ByteTrack) 통합

### 실전 프로젝트
- [ ] 자율주행 자동차에 통합
- [ ] 교통 표지판 인식 시스템
- [ ] 객체 추적 및 카운팅

### 고급 주제
- [ ] 모델 압축 (Pruning, Quantization)
- [ ] Edge TPU 배포
- [ ] 분산 훈련

---

**시작하기**: 
1. 📚 [docs/📚_문서_가이드.md](docs/📚_문서_가이드.md) - 문서 네비게이션
2. 🚀 [tutorials/01_quick_start.md](tutorials/01_quick_start.md) - 30분 빠른 시작
3. 🍓 [docs/2단계_RASPBERRY_PI_5_최적화_가이드.md](docs/2단계_RASPBERRY_PI_5_최적화_가이드.md) - Pi 5 최적화

**버전**: 2.0  
**최종 업데이트**: 2024-12-16  
**프로젝트**: Raspbot v2 자율주행 자동차
