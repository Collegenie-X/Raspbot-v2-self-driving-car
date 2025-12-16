# 🚀 YOLO11 빠른 시작 가이드 (30분)

> **30분 안에 첫 번째 커스텀 객체 인식 모델 만들기**

---

## 📋 목표

이 가이드를 완료하면:
- ✅ YOLO11 환경 설정 완료
- ✅ 사전 훈련 모델로 실시간 객체 인식
- ✅ 간단한 커스텀 데이터셋 제작
- ✅ 첫 번째 커스텀 모델 훈련

**소요 시간**: 약 30분

---

## 1단계: 환경 설정 (5분)

### 필수 요구사항

- Python 3.8 이상
- 8GB RAM 이상
- 10GB 이상 저장공간

### 설치

```bash
# 1. 가상환경 생성 (권장)
python3 -m venv yolo_env
source yolo_env/bin/activate  # Linux/Mac
# yolo_env\Scripts\activate  # Windows

# 2. Ultralytics 설치
pip install ultralytics

# 3. 추가 패키지
pip install opencv-python pillow pyyaml tqdm

# 4. 설치 확인
yolo version
```

**예상 출력**:
```
Ultralytics YOLOv8.x.x Python-3.x.x torch-2.x.x
```

---

## 2단계: 사전 훈련 모델 테스트 (5분)

### 웹캠으로 실시간 객체 인식

```python
# test_webcam.py
from ultralytics import YOLO

# 모델 로드 (자동 다운로드)
model = YOLO('yolo11n.pt')

# 웹캠 추론
results = model.predict(
    source=0,          # 웹캠 ID
    show=True,         # 결과 표시
    conf=0.5,          # 신뢰도 임계값
    save=False         # 저장 안 함
)
```

```bash
# 실행
python test_webcam.py
```

**키보드 단축키**:
- `q`: 종료
- `s`: 스크린샷 저장

### 이미지로 테스트

```python
# test_image.py
from ultralytics import YOLO

model = YOLO('yolo11n.pt')
results = model('test_image.jpg')

# 결과 표시
results[0].show()

# 결과 저장
results[0].save('result.jpg')
```

---

## 3단계: 커스텀 데이터 수집 (10분)

### 웹캠으로 이미지 수집

```python
# collect_data.py
import cv2
import os
from pathlib import Path

# 출력 디렉토리
output_dir = Path('dataset/images')
output_dir.mkdir(parents=True, exist_ok=True)

# 웹캠 초기화
cap = cv2.VideoCapture(0)
count = 0
target = 50  # 목표 이미지 수

print("📷 이미지 수집 시작")
print("   - 's' 키: 저장")
print("   - 'q' 키: 종료")

while count < target:
    ret, frame = cap.read()
    if not ret:
        break
    
    # 정보 표시
    cv2.putText(frame, f"수집: {count}/{target}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, "s: 저장 | q: 종료", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    cv2.imshow('Data Collection', frame)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('s'):
        # 이미지 저장
        filename = output_dir / f'img_{count:04d}.jpg'
        cv2.imwrite(str(filename), frame)
        count += 1
        print(f"✅ 저장: {filename}")
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print(f"\n✅ 총 {count}장 수집 완료!")
```

```bash
python collect_data.py
```

---

## 4단계: 라벨링 (5분)

### LabelImg 사용

```bash
# LabelImg 설치
pip install labelImg

# 실행
labelImg dataset/images dataset/labels
```

### 라벨링 방법

1. **Create RectBox** 클릭 또는 `w` 키
2. 객체 주위에 박스 그리기
3. 클래스 이름 입력
4. **Save** 클릭 또는 `Ctrl+S`
5. **Next Image** 클릭 또는 `d` 키

**팁**:
- 최소 50장 이상 라벨링 권장
- 다양한 각도와 조명 조건
- 객체가 화면 중앙에 위치

---

## 5단계: 데이터셋 준비 (3분)

### 디렉토리 구조

```
dataset/
├── images/
│   ├── img_0000.jpg
│   ├── img_0001.jpg
│   └── ...
└── labels/
    ├── img_0000.txt
    ├── img_0001.txt
    └── ...
```

### data.yaml 생성

```yaml
# dataset/data.yaml
path: /absolute/path/to/dataset
train: images
val: images  # 간단한 테스트용 (실전에서는 분리)

nc: 2  # 클래스 수
names: ['class1', 'class2']  # 클래스 이름
```

**예제** (교통 표지판):
```yaml
path: /home/pi/yolo_dataset
train: images
val: images

nc: 3
names: ['stop', 'go', 'warning']
```

---

## 6단계: 모델 훈련 (2분 설정)

### 간단한 훈련

```python
# train_simple.py
from ultralytics import YOLO

# 모델 초기화
model = YOLO('yolo11n.pt')

# 훈련
results = model.train(
    data='dataset/data.yaml',
    epochs=50,             # 빠른 테스트용 (실전: 150+)
    imgsz=416,             # 이미지 크기
    batch=16,              # 배치 크기
    device='cpu',          # CPU 사용
    project='runs/train',  # 결과 저장 위치
    name='quick_test'
)

print("✅ 훈련 완료!")
print(f"모델 저장 위치: runs/train/quick_test/weights/best.pt")
```

```bash
# 훈련 시작 (백그라운드)
nohup python train_simple.py > train.log 2>&1 &

# 로그 확인
tail -f train.log
```

**예상 시간**:
- CPU: 30-60분 (50 에폭, 50장)
- GPU: 5-10분

---

## 7단계: 모델 테스트

### 훈련된 모델로 추론

```python
# test_custom_model.py
from ultralytics import YOLO

# 커스텀 모델 로드
model = YOLO('runs/train/quick_test/weights/best.pt')

# 웹캠 테스트
results = model.predict(
    source=0,
    show=True,
    conf=0.5
)
```

### 성능 확인

```python
# evaluate.py
from ultralytics import YOLO

model = YOLO('runs/train/quick_test/weights/best.pt')

# 검증 데이터로 평가
metrics = model.val()

print(f"mAP50: {metrics.box.map50:.3f}")
print(f"mAP50-95: {metrics.box.map:.3f}")
```

---

## 🎉 완료!

축하합니다! 첫 번째 커스텀 YOLO 모델을 만들었습니다!

### 다음 단계

#### 성능 개선
1. **더 많은 데이터**: 클래스당 200+ 장
2. **더 긴 훈련**: 150+ 에폭
3. **데이터 증강**: 다양한 변형
4. **하이퍼파라미터 튜닝**

#### 고급 기능
1. **모델 최적화**: ONNX 변환
2. **라즈베리파이 배포**
3. **실시간 추적**: ByteTrack
4. **자율주행 통합**

---

## 📚 추가 학습 자료

### 필수 문서
- [README.md](../README.md) - 전체 가이드
- [2단계_RASPBERRY_PI_5_최적화_가이드.md](../docs/2단계_RASPBERRY_PI_5_최적화_가이드.md) - Pi 5 최적화
- [3단계_YOLO11_전체_워크플로우_가이드.md](../docs/3단계_YOLO11_전체_워크플로우_가이드.md) - 완전 가이드

### 스크립트
- `scripts/dataset/dataset_splitter.py` - 데이터셋 분할
- `scripts/training/train_yolo11_pi5_optimized.py` - Pi 5 최적화 훈련
- `scripts/inference/test_inference.py` - 모델 테스트

---

## 🔧 트러블슈팅

### Q: 웹캠이 열리지 않아요
```python
# 다른 카메라 ID 시도
cap = cv2.VideoCapture(1)  # 또는 2, 3...
```

### Q: 훈련이 너무 느려요
```python
# 배치 크기 줄이기
model.train(data='data.yaml', batch=8)

# 이미지 크기 줄이기
model.train(data='data.yaml', imgsz=320)
```

### Q: 정확도가 낮아요
- 더 많은 데이터 수집 (최소 100장/클래스)
- 더 긴 훈련 (150+ 에폭)
- 라벨 품질 확인
- 데이터 증강 활성화

---

**소요 시간 요약**:
- 환경 설정: 5분
- 모델 테스트: 5분
- 데이터 수집: 10분
- 라벨링: 5분
- 데이터셋 준비: 3분
- 훈련 설정: 2분
- **총 30분** (훈련 시간 제외)

**다음**: [02_data_collection.md](02_data_collection.md) - 데이터 수집 심화

---

**버전**: 1.0  
**최종 업데이트**: 2024-12-16

