# 1. YOLOv4 소개 및 환경설정

## 📚 목차

1. [YOLOv4 개요](#yolov4-개요)
2. [YOLOv4 vs YOLOv3](#yolov4-vs-yolov3)
3. [YOLOv4-tiny 소개](#yolov4-tiny-소개)
4. [환경 설정](#환경-설정)
5. [필수 도구 설치](#필수-도구-설치)
6. [사전 학습 모델 다운로드](#사전-학습-모델-다운로드)

---

## YOLOv4 개요

### YOLO란?

**YOLO (You Only Look Once)**는 실시간 객체 인식을 위한 딥러닝 알고리즘입니다.

#### 주요 특징
- **빠른 속도**: 한 번의 forward pass로 객체 검출
- **실시간 처리**: 초당 30-60 프레임 처리 가능
- **end-to-end 학습**: 이미지에서 바로 바운딩 박스와 클래스 예측

#### YOLO의 작동 원리

```
입력 이미지 (416x416)
    ↓
특징 추출 (Backbone: CSPDarknet53)
    ↓
특징 맵 생성 (13x13, 26x26, 52x52)
    ↓
바운딩 박스 예측 + 클래스 분류
    ↓
NMS (Non-Maximum Suppression)
    ↓
최종 검출 결과
```

### YOLOv4의 혁신

YOLOv4는 다음과 같은 기술들을 결합하여 성능을 크게 향상시켰습니다:

1. **Bag of Freebies (BoF)**: 추가 비용 없이 정확도 향상
   - 데이터 증강: Mosaic, MixUp
   - 정규화: DropBlock
   - 손실 함수: CIoU loss

2. **Bag of Specials (BoS)**: 약간의 비용으로 큰 성능 향상
   - CSPDarknet53 backbone
   - SPP (Spatial Pyramid Pooling)
   - PAN (Path Aggregation Network)

3. **최적화 기법**
   - Mish 활성화 함수
   - SAM (Spatial Attention Module)

---

## YOLOv4 vs YOLOv3

### 성능 비교

| 특징 | YOLOv3 | YOLOv4 |
|------|--------|--------|
| Backbone | Darknet53 | CSPDarknet53 |
| mAP (COCO) | 57.9% | 65.7% |
| FPS (V100) | 60 | 65 |
| 파라미터 수 | 61.9M | 64.4M |
| 모델 크기 | 248MB | 256MB |

### 주요 개선 사항

1. **정확도 향상**: mAP가 약 8% 증가
2. **속도 유지**: FPS가 오히려 약간 증가
3. **학습 안정성**: 더 빠르고 안정적인 수렴
4. **작은 객체 검출 개선**: SPP와 PAN 덕분

---

## YOLOv4-tiny 소개

### 왜 YOLOv4-tiny인가?

**라즈베리파이와 같은 엣지 디바이스에 최적화된 경량 모델**

#### YOLOv4 vs YOLOv4-tiny

| 특징 | YOLOv4 | YOLOv4-tiny |
|------|--------|-------------|
| 모델 크기 | 256MB | 23MB |
| 파라미터 수 | 64.4M | 6.1M |
| FPS (RTX 2080 Ti) | 65 | 371 |
| FPS (Pi 4) | ~5 | ~18 |
| mAP (COCO) | 65.7% | 40.2% |

#### 언제 YOLOv4-tiny를 사용해야 하나?

✅ **사용하기 좋은 경우**:
- 라즈베리파이, Jetson Nano 등 엣지 디바이스
- 실시간 처리가 중요한 경우
- 모델 크기가 중요한 경우
- 비교적 단순한 객체 검출

❌ **사용하기 어려운 경우**:
- 매우 높은 정확도가 필요한 경우
- 작은 객체를 검출해야 하는 경우
- 복잡한 배경이 많은 경우

---

## 환경 설정

### 시스템 요구사항

#### 개발 환경 (PC/서버)

**최소 사양**:
- OS: Ubuntu 18.04+ / Windows 10+ / macOS 10.14+
- CPU: Intel i5 이상
- RAM: 8GB 이상
- GPU: NVIDIA GPU (CUDA 지원) - 선택사항
- 저장공간: 20GB 이상

**권장 사양**:
- CPU: Intel i7 / AMD Ryzen 7 이상
- RAM: 16GB 이상
- GPU: NVIDIA RTX 2060 이상 (6GB+ VRAM)
- 저장공간: 50GB 이상 (SSD 권장)

#### 배포 환경 (라즈베리파이)

**라즈베리파이 4 (4GB)**:
- OS: Raspberry Pi OS (64-bit 권장)
- microSD: 32GB 이상 (Class 10)
- 전원: 5V 3A 공식 어댑터

**라즈베리파이 5 (8GB)** - 권장:
- OS: Raspberry Pi OS (64-bit)
- microSD: 64GB 이상 (UHS-I)
- 전원: 5V 5A 공식 어댑터

### Python 환경 설정

#### 1. Python 버전 확인

```bash
python3 --version  # Python 3.7+ 필요
```

#### 2. 가상환경 생성 (권장)

```bash
# venv 사용
python3 -m venv yolov4_env
source yolov4_env/bin/activate  # Linux/Mac
# yolov4_env\Scripts\activate  # Windows

# 또는 conda 사용
conda create -n yolov4 python=3.8
conda activate yolov4
```

---

## 필수 도구 설치

### 1. TensorFlow / Keras 설치

```bash
# GPU 버전 (NVIDIA GPU가 있는 경우)
pip install tensorflow==2.10.0

# CPU 버전 (GPU가 없는 경우)
pip install tensorflow-cpu==2.10.0

# Keras는 TensorFlow 2.x에 포함됨
```

### 2. OpenCV 설치

```bash
# OpenCV
pip install opencv-python==4.8.0.76
pip install opencv-contrib-python==4.8.0.76
```

### 3. 기타 필수 라이브러리

```bash
# 이미지 처리
pip install Pillow==10.0.0
pip install numpy==1.23.5

# 데이터 처리
pip install pandas==2.0.3
pip install matplotlib==3.7.2
pip install seaborn==0.12.2

# 진행 표시
pip install tqdm==4.66.1

# 설정 파일
pip install PyYAML==6.0.1
```

### 4. requirements.txt 생성

```bash
cat > requirements.txt << EOF
tensorflow==2.10.0
opencv-python==4.8.0.76
opencv-contrib-python==4.8.0.76
Pillow==10.0.0
numpy==1.23.5
pandas==2.0.3
matplotlib==3.7.2
seaborn==0.12.2
tqdm==4.66.1
PyYAML==6.0.1
EOF

# 일괄 설치
pip install -r requirements.txt
```

---

## Darknet 설치 (훈련용)

### Linux / macOS

```bash
# 1. Darknet 클론
git clone https://github.com/AlexeyAB/darknet
cd darknet

# 2. Makefile 수정 (GPU 사용 시)
# GPU=1
# CUDNN=1
# OPENCV=1

# 3. 컴파일
make

# 4. 테스트
./darknet
```

### GPU 설정 (NVIDIA)

```bash
# CUDA 설치 확인
nvcc --version

# cuDNN 설치 확인
cat /usr/local/cuda/include/cudnn_version.h | grep CUDNN_MAJOR -A 2

# Makefile에서 GPU 활성화
sed -i 's/GPU=0/GPU=1/' Makefile
sed -i 's/CUDNN=0/CUDNN=1/' Makefile
sed -i 's/OPENCV=0/OPENCV=1/' Makefile

# 재컴파일
make clean
make
```

### Windows

```bash
# Visual Studio 2019/2022 필요

# 1. CMake 사용
git clone https://github.com/AlexeyAB/darknet
cd darknet
mkdir build
cd build

# 2. CMake 설정
cmake .. -DCMAKE_BUILD_TYPE=Release

# 3. 빌드
cmake --build . --config Release
```

---

## 사전 학습 모델 다운로드

### YOLOv4-tiny 가중치

```bash
# 사전 학습된 가중치 (COCO 데이터셋)
wget https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v4_pre/yolov4-tiny.weights

# 전이 학습용 가중치
wget https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v4_pre/yolov4-tiny.conv.29
```

### YOLOv4-tiny 설정 파일

```bash
# cfg 파일 다운로드
wget https://raw.githubusercontent.com/AlexeyAB/darknet/master/cfg/yolov4-tiny.cfg

# 또는 직접 생성 (다음 장에서 설명)
```

---

## 설치 확인

### 1. TensorFlow 확인

```python
import tensorflow as tf
print(f"TensorFlow 버전: {tf.__version__}")
print(f"GPU 사용 가능: {tf.config.list_physical_devices('GPU')}")
```

### 2. OpenCV 확인

```python
import cv2
print(f"OpenCV 버전: {cv2.__version__}")

# 카메라 테스트
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if ret:
    print("카메라 정상 작동")
    cv2.imshow("Test", frame)
    cv2.waitKey(1000)
cap.release()
cv2.destroyAllWindows()
```

### 3. Darknet 확인

```bash
# Darknet 버전 확인
./darknet version

# 테스트 이미지로 검출
./darknet detect cfg/yolov4-tiny.cfg yolov4-tiny.weights data/dog.jpg
```

---

## 라즈베리파이 환경 설정

### 1. 기본 설정

```bash
# 시스템 업데이트
sudo apt update
sudo apt upgrade -y

# 필수 패키지
sudo apt install -y python3-pip python3-dev
sudo apt install -y libhdf5-dev libhdf5-serial-dev
sudo apt install -y libatlas-base-dev libjasper-dev
sudo apt install -y libqtgui4 libqt4-test
```

### 2. TensorFlow Lite 설치

```bash
# TensorFlow Lite (라즈베리파이 최적화)
pip3 install --extra-index-url https://google-coral.github.io/py-repo/ tflite_runtime

# 또는 전체 TensorFlow
pip3 install tensorflow==2.10.0
```

### 3. OpenCV 설치 (라즈베리파이)

```bash
# 사전 컴파일된 버전
sudo apt install -y python3-opencv

# 또는 pip로 설치
pip3 install opencv-python
```

### 4. 성능 최적화

```bash
# GPU 메모리 할당
sudo nano /boot/config.txt
# gpu_mem=256 추가

# 스왑 메모리 증가
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

---

## 디렉토리 구조 설정

### 프로젝트 디렉토리 생성

```bash
mkdir -p ~/yolov4_custom
cd ~/yolov4_custom

# 필요한 디렉토리들
mkdir -p {dataset/{images,labels,train,val,test},model_data,results,scripts}

# 구조 확인
tree -L 2
```

### 예상 디렉토리 구조

```
~/yolov4_custom/
├── dataset/
│   ├── images/          # 원본 이미지
│   ├── labels/          # YOLO 포맷 라벨
│   ├── train/           # 훈련 데이터
│   ├── val/             # 검증 데이터
│   └── test/            # 테스트 데이터
├── model_data/
│   ├── yolov4-tiny.cfg
│   ├── yolov4-tiny.weights
│   ├── classes.txt
│   └── anchors.txt
├── results/             # 추론 결과
├── scripts/             # 유틸리티 스크립트
└── darknet/             # Darknet 소스코드
```

---

## 테스트 실행

### 1. 간단한 테스트 스크립트

```python
# test_setup.py
import sys
import cv2
import numpy as np
import tensorflow as tf
from PIL import Image

def test_installation():
    print("=" * 50)
    print("환경 설정 테스트")
    print("=" * 50)
    
    # Python 버전
    print(f"Python 버전: {sys.version}")
    
    # TensorFlow
    print(f"TensorFlow 버전: {tf.__version__}")
    gpus = tf.config.list_physical_devices('GPU')
    print(f"GPU 사용 가능: {len(gpus) > 0}")
    if gpus:
        for gpu in gpus:
            print(f"  - {gpu}")
    
    # OpenCV
    print(f"OpenCV 버전: {cv2.__version__}")
    
    # NumPy
    print(f"NumPy 버전: {np.__version__}")
    
    # PIL
    print(f"Pillow 버전: {Image.__version__}")
    
    # 카메라 테스트
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        print("카메라: 정상")
        cap.release()
    else:
        print("카메라: 감지 안 됨")
    
    print("=" * 50)
    print("✅ 모든 설치 완료!")
    print("=" * 50)

if __name__ == "__main__":
    test_installation()
```

```bash
python test_setup.py
```

---

## 다음 단계

✅ 환경 설정 완료!

**다음 문서**: [2_데이터셋_준비_가이드.md](2_데이터셋_준비_가이드.md)

여기서 다음을 배웁니다:
- 이미지 수집 방법
- LabelImg를 사용한 라벨링
- 데이터셋 분할 및 검증
- 데이터 증강 기법

---

## 참고 자료

### 공식 문서
- [YOLOv4 논문](https://arxiv.org/abs/2004.10934)
- [Darknet GitHub](https://github.com/AlexeyAB/darknet)
- [TensorFlow 설치 가이드](https://www.tensorflow.org/install)

### 유용한 링크
- [CUDA 설치](https://developer.nvidia.com/cuda-downloads)
- [cuDNN 설치](https://developer.nvidia.com/cudnn)
- [Raspberry Pi 공식 문서](https://www.raspberrypi.com/documentation/)

---

**버전**: 1.0  
**최종 업데이트**: 2024-12-16

