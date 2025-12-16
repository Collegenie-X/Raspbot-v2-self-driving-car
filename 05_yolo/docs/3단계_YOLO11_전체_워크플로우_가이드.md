# YOLO11 전체 워크플로우 가이드
## LabelImg 라벨링부터 모델 훈련 및 테스트까지

---

## 📋 목차
1. [전체 워크플로우 개요](#1-전체-워크플로우-개요)
2. [1단계: LabelImg 이미지 라벨링](#2-1단계-labelimg-이미지-라벨링)
3. [2단계: 데이터셋 구성](#3-2단계-데이터셋-구성)
4. [3단계: YOLO11 환경 설정](#4-3단계-yolo11-환경-설정)
5. [4단계: YOLO11 모델 훈련](#5-4단계-yolo11-모델-훈련)
6. [5단계: 모델 검증 및 테스트](#6-5단계-모델-검증-및-테스트)
7. [6단계: Raspberry Pi 실전 배포](#7-6단계-raspberry-pi-실전-배포)
8. [주요 함수 및 알고리즘](#8-주요-함수-및-알고리즘)
9. [트러블슈팅](#9-트러블슈팅)

---

## 1. 전체 워크플로우 개요

### 1.1 전체 프로세스 순서도

```
┌─────────────────────────────────────────────────────────────────┐
│                      YOLO11 객체 인식 전체 파이프라인                │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 1단계: 이미지 수집                                                 │
│   - 훈련용 이미지 촬영/수집 (최소 100장 이상 권장)                   │
│   - 다양한 조명, 각도, 배경에서 촬영                                │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2단계: LabelImg로 라벨링                                           │
│   - LabelImg 설치 및 실행                                         │
│   - 객체 영역 바운딩 박스 그리기                                   │
│   - 클래스 지정 (예: stop_sign, traffic_light)                   │
│   - YOLO 포맷으로 저장                                            │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3단계: 데이터셋 구성                                               │
│   - train/val/test 폴더 분할 (70%/20%/10%)                      │
│   - data.yaml 설정 파일 생성                                      │
│   - 클래스 정의 및 경로 설정                                       │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4단계: YOLO11 환경 설정                                            │
│   - Ultralytics 라이브러리 설치                                   │
│   - 사전 훈련된 가중치 다운로드 (yolo11n.pt)                       │
│   - GPU/CPU 설정 확인                                             │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5단계: 모델 훈련                                                   │
│   - 훈련 파라미터 설정 (epochs, batch, imgsz)                     │
│   - 전이 학습 실행                                                │
│   - 훈련 진행 상황 모니터링                                        │
│   - 최적 가중치 저장 (best.pt)                                    │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6단계: 모델 검증                                                   │
│   - 검증 데이터로 성능 평가                                        │
│   - mAP, Precision, Recall 확인                                  │
│   - 혼동 행렬 분석                                                │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7단계: 모델 테스트                                                 │
│   - 테스트 이미지로 추론 실행                                      │
│   - 실시간 비디오 스트림 테스트                                    │
│   - 성능 및 정확도 확인                                            │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8단계: Raspberry Pi 배포                                          │
│   - 모델 최적화 (경량화)                                          │
│   - Raspberry Pi로 전송                                          │
│   - 실시간 자율주행 시스템 통합                                    │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 필요 환경
- **Python**: 3.8 이상
- **LabelImg**: 이미지 라벨링 도구
- **Ultralytics**: YOLO11 구현체
- **PyTorch**: 딥러닝 프레임워크
- **OpenCV**: 이미지 처리
- **CUDA** (선택): GPU 가속

---

## 2. 1단계: LabelImg 이미지 라벨링

### 2.1 LabelImg 설치

#### macOS 설치
```bash
# Homebrew를 통한 의존성 설치
brew install qt
brew install libxml2

# pip를 통한 LabelImg 설치
pip3 install labelImg

# 실행
labelImg
```

#### Linux (Ubuntu) 설치
```bash
# 의존성 설치
sudo apt-get install pyqt5-dev-tools
sudo pip3 install -r requirements/requirements-linux-python3.txt

# LabelImg 설치
pip3 install labelImg

# 실행
labelImg
```

#### Windows 설치
```bash
# Anaconda Prompt에서 실행
conda install pyqt=5
conda install -c anaconda lxml

# LabelImg 설치
pip install labelImg

# 실행
labelImg
```

### 2.2 LabelImg 사용 방법

#### 2.2.1 초기 설정
1. LabelImg 실행
2. **File → Open Dir**: 라벨링할 이미지 폴더 선택
3. **File → Change Save Dir**: 라벨 저장 폴더 선택
4. **PascalVOC 버튼 → YOLO 포맷으로 전환** (좌측 하단)

#### 2.2.2 클래스 정의
`data/predefined_classes.txt` 파일 생성:
```text
stop_sign
traffic_light
pedestrian
lane_marker
obstacle
```

#### 2.2.3 라벨링 작업 프로세스
```
1. 이미지 로드
   ↓
2. 'w' 키 누르기 → 바운딩 박스 모드 활성화
   ↓
3. 마우스로 객체 영역 드래그
   ↓
4. 클래스 선택 (예: stop_sign)
   ↓
5. 'Ctrl + s' → 저장
   ↓
6. 'd' 키 → 다음 이미지
   ↓
7. 반복
```

#### 2.2.4 단축키 모음
| 단축키 | 기능 |
|--------|------|
| `w` | 바운딩 박스 그리기 모드 |
| `d` | 다음 이미지 |
| `a` | 이전 이미지 |
| `del` | 선택된 박스 삭제 |
| `Ctrl + s` | 저장 |
| `Ctrl + d` | 현재 박스 복사 |
| `Ctrl + u` | 디렉토리의 모든 이미지 로드 |
| `Space` | 이미지 검증 플래그 |

### 2.3 YOLO 포맷 이해

#### 2.3.1 출력 파일 구조
```
dataset/
├── images/
│   ├── image_001.jpg
│   ├── image_002.jpg
│   └── image_003.jpg
└── labels/
    ├── image_001.txt
    ├── image_002.txt
    └── image_003.txt
```

#### 2.3.2 YOLO 라벨 포맷
각 `.txt` 파일은 다음 형식:
```
<class_id> <x_center> <y_center> <width> <height>
```

**예시**: `image_001.txt`
```
0 0.515625 0.398148 0.120313 0.185185
1 0.234375 0.612037 0.089063 0.151852
```

**좌표 정규화 계산**:
```python
x_center = (bbox_x + bbox_width / 2) / image_width
y_center = (bbox_y + bbox_height / 2) / image_height
width = bbox_width / image_width
height = bbox_height / image_height
```

### 2.4 라벨링 품질 검증

#### 2.4.1 체크리스트
- [ ] 모든 이미지에 라벨이 있는가?
- [ ] 바운딩 박스가 객체를 정확히 포함하는가?
- [ ] 클래스가 올바르게 지정되었는가?
- [ ] 작은 객체도 빠짐없이 라벨링했는가?
- [ ] 부분적으로 가려진 객체도 라벨링했는가?

#### 2.4.2 품질 검증 스크립트
```python
# label_quality_checker.py
import os
from pathlib import Path

def validate_labels(images_dir, labels_dir):
    """
    라벨 파일의 품질과 일관성을 검증합니다.
    
    Args:
        images_dir: 이미지 디렉토리 경로
        labels_dir: 라벨 디렉토리 경로
    """
    image_files = set([f.stem for f in Path(images_dir).glob('*.jpg')])
    label_files = set([f.stem for f in Path(labels_dir).glob('*.txt')])
    
    # 라벨이 없는 이미지 찾기
    missing_labels = image_files - label_files
    if missing_labels:
        print(f"⚠️  라벨이 없는 이미지: {len(missing_labels)}개")
        for img in list(missing_labels)[:5]:
            print(f"   - {img}")
    
    # 이미지가 없는 라벨 찾기
    orphan_labels = label_files - image_files
    if orphan_labels:
        print(f"⚠️  이미지가 없는 라벨: {len(orphan_labels)}개")
    
    # 라벨 파일 내용 검증
    invalid_count = 0
    for label_file in Path(labels_dir).glob('*.txt'):
        with open(label_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                parts = line.strip().split()
                if len(parts) != 5:
                    print(f"❌ {label_file.name} 라인 {line_num}: 잘못된 형식")
                    invalid_count += 1
                    continue
                
                try:
                    class_id, x, y, w, h = map(float, parts)
                    if not (0 <= x <= 1 and 0 <= y <= 1 and 0 <= w <= 1 and 0 <= h <= 1):
                        print(f"❌ {label_file.name} 라인 {line_num}: 좌표 범위 오류")
                        invalid_count += 1
                except ValueError:
                    print(f"❌ {label_file.name} 라인 {line_num}: 숫자 변환 오류")
                    invalid_count += 1
    
    if invalid_count == 0 and not missing_labels and not orphan_labels:
        print("✅ 모든 라벨 파일이 정상입니다!")
    
    return len(missing_labels), len(orphan_labels), invalid_count

if __name__ == "__main__":
    images_dir = "dataset/images"
    labels_dir = "dataset/labels"
    validate_labels(images_dir, labels_dir)
```

---

## 3. 2단계: 데이터셋 구성

### 3.1 데이터셋 분할 전략

#### 3.1.1 분할 비율
- **Train (훈련)**: 70% - 모델 학습용
- **Validation (검증)**: 20% - 하이퍼파라미터 튜닝 및 조기 종료 판단
- **Test (테스트)**: 10% - 최종 성능 평가

#### 3.1.2 디렉토리 구조
```
yolo_dataset/
├── data.yaml
├── train/
│   ├── images/
│   │   ├── img_001.jpg
│   │   └── ...
│   └── labels/
│       ├── img_001.txt
│       └── ...
├── val/
│   ├── images/
│   └── labels/
└── test/
    ├── images/
    └── labels/
```

### 3.2 데이터셋 분할 스크립트

```python
# dataset_splitter.py
import os
import shutil
import random
from pathlib import Path
from typing import Tuple, List

class DatasetSplitter:
    """
    이미지와 라벨을 train/val/test로 분할하는 클래스
    """
    
    def __init__(self, 
                 source_images_dir: str,
                 source_labels_dir: str,
                 output_dir: str,
                 train_ratio: float = 0.7,
                 val_ratio: float = 0.2,
                 test_ratio: float = 0.1):
        """
        Args:
            source_images_dir: 원본 이미지 디렉토리
            source_labels_dir: 원본 라벨 디렉토리
            output_dir: 출력 디렉토리
            train_ratio: 훈련 데이터 비율
            val_ratio: 검증 데이터 비율
            test_ratio: 테스트 데이터 비율
        """
        self.source_images_dir = Path(source_images_dir)
        self.source_labels_dir = Path(source_labels_dir)
        self.output_dir = Path(output_dir)
        
        # 비율 검증
        if not abs(train_ratio + val_ratio + test_ratio - 1.0) < 0.001:
            raise ValueError("비율의 합이 1.0이 되어야 합니다")
        
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
    
    def create_directory_structure(self):
        """출력 디렉토리 구조 생성"""
        for split in ['train', 'val', 'test']:
            (self.output_dir / split / 'images').mkdir(parents=True, exist_ok=True)
            (self.output_dir / split / 'labels').mkdir(parents=True, exist_ok=True)
        print("✅ 디렉토리 구조 생성 완료")
    
    def get_paired_files(self) -> List[Tuple[Path, Path]]:
        """
        이미지와 라벨 파일 쌍을 찾습니다.
        
        Returns:
            (이미지_경로, 라벨_경로) 튜플 리스트
        """
        paired_files = []
        
        for img_file in self.source_images_dir.glob('*.jpg'):
            label_file = self.source_labels_dir / f"{img_file.stem}.txt"
            
            if not label_file.exists():
                print(f"⚠️  라벨 없음: {img_file.name}")
                continue
            
            paired_files.append((img_file, label_file))
        
        print(f"✅ 총 {len(paired_files)}개의 이미지-라벨 쌍 발견")
        return paired_files
    
    def split_dataset(self, paired_files: List[Tuple[Path, Path]]) -> dict:
        """
        데이터셋을 train/val/test로 분할합니다.
        
        Args:
            paired_files: 이미지-라벨 파일 쌍 리스트
            
        Returns:
            분할된 파일 딕셔너리
        """
        random.shuffle(paired_files)
        total = len(paired_files)
        
        train_end = int(total * self.train_ratio)
        val_end = train_end + int(total * self.val_ratio)
        
        splits = {
            'train': paired_files[:train_end],
            'val': paired_files[train_end:val_end],
            'test': paired_files[val_end:]
        }
        
        for split_name, count in [(k, len(v)) for k, v in splits.items()]:
            print(f"  {split_name}: {count}개 ({count/total*100:.1f}%)")
        
        return splits
    
    def copy_files(self, splits: dict):
        """파일을 각 분할 디렉토리로 복사합니다."""
        for split_name, file_pairs in splits.items():
            for img_path, label_path in file_pairs:
                # 이미지 복사
                shutil.copy2(
                    img_path,
                    self.output_dir / split_name / 'images' / img_path.name
                )
                # 라벨 복사
                shutil.copy2(
                    label_path,
                    self.output_dir / split_name / 'labels' / label_path.name
                )
            print(f"✅ {split_name} 파일 복사 완료: {len(file_pairs)}개")
    
    def execute(self):
        """전체 분할 프로세스 실행"""
        print("🚀 데이터셋 분할 시작...")
        
        self.create_directory_structure()
        paired_files = self.get_paired_files()
        
        if not paired_files:
            print("❌ 처리할 파일이 없습니다")
            return
        
        splits = self.split_dataset(paired_files)
        self.copy_files(splits)
        
        print("✅ 데이터셋 분할 완료!")

# 사용 예시
if __name__ == "__main__":
    splitter = DatasetSplitter(
        source_images_dir="raw_dataset/images",
        source_labels_dir="raw_dataset/labels",
        output_dir="yolo_dataset",
        train_ratio=0.7,
        val_ratio=0.2,
        test_ratio=0.1
    )
    splitter.execute()
```

### 3.3 data.yaml 설정 파일 생성

`data.yaml` 파일은 YOLO 훈련에 필수적인 설정 파일입니다.

```yaml
# data.yaml

# 데이터셋 경로 (절대 경로 또는 상대 경로)
path: /Users/username/yolo_dataset  # 데이터셋 루트 경로
train: train/images  # 훈련 이미지 경로 (path 기준 상대 경로)
val: val/images      # 검증 이미지 경로
test: test/images    # 테스트 이미지 경로 (선택사항)

# 클래스 정의
nc: 5  # 클래스 개수
names: 
  0: stop_sign
  1: traffic_light
  2: pedestrian
  3: lane_marker
  4: obstacle
```

#### data.yaml 자동 생성 스크립트
```python
# create_data_yaml.py
import yaml
from pathlib import Path

def create_data_yaml(dataset_path: str, 
                     classes: list,
                     output_file: str = "data.yaml"):
    """
    YOLO data.yaml 파일을 생성합니다.
    
    Args:
        dataset_path: 데이터셋 루트 경로
        classes: 클래스 이름 리스트
        output_file: 출력 파일명
    """
    data_config = {
        'path': str(Path(dataset_path).absolute()),
        'train': 'train/images',
        'val': 'val/images',
        'test': 'test/images',
        'nc': len(classes),
        'names': {i: name for i, name in enumerate(classes)}
    }
    
    output_path = Path(dataset_path) / output_file
    with open(output_path, 'w') as f:
        yaml.dump(data_config, f, default_flow_style=False, sort_keys=False)
    
    print(f"✅ data.yaml 파일 생성 완료: {output_path}")
    print(f"   클래스 개수: {len(classes)}")
    for i, name in enumerate(classes):
        print(f"   [{i}] {name}")

# 사용 예시
if __name__ == "__main__":
    classes = [
        'stop_sign',
        'traffic_light', 
        'pedestrian',
        'lane_marker',
        'obstacle'
    ]
    
    create_data_yaml(
        dataset_path="yolo_dataset",
        classes=classes
    )
```

---

## 4. 3단계: YOLO11 환경 설정

### 4.1 Ultralytics 설치

```bash
# PyTorch 설치 (CUDA 지원)
pip install torch torchvision torchaudio

# Ultralytics YOLO 설치
pip install ultralytics

# 추가 의존성
pip install opencv-python
pip install matplotlib
pip install pandas
pip install seaborn
```

### 4.2 YOLO11 모델 종류

| 모델 | 크기 | mAPval | 속도 (ms) | 파라미터 | 용도 |
|------|------|--------|-----------|----------|------|
| YOLOv11n | 2.6MB | 39.5 | 1.5 | 2.6M | 엣지 디바이스 (Raspberry Pi) |
| YOLOv11s | 9.4MB | 47.0 | 2.5 | 9.4M | 모바일 |
| YOLOv11m | 20.1MB | 51.5 | 4.7 | 20.1M | 일반 용도 |
| YOLOv11l | 25.3MB | 53.4 | 6.2 | 25.3M | 높은 정확도 |
| YOLOv11x | 56.9MB | 54.7 | 11.3 | 56.9M | 최고 정확도 |

**Raspberry Pi 자율주행 추천**: **YOLOv11n** (가장 경량)

### 4.3 사전 훈련된 가중치 다운로드

```python
# download_weights.py
from ultralytics import YOLO

def download_pretrained_weights(model_size='n'):
    """
    사전 훈련된 YOLO11 가중치를 다운로드합니다.
    
    Args:
        model_size: 모델 크기 ('n', 's', 'm', 'l', 'x')
    """
    model_name = f'yolo11{model_size}.pt'
    print(f"📥 {model_name} 다운로드 중...")
    
    model = YOLO(model_name)
    print(f"✅ {model_name} 다운로드 완료")
    print(f"   저장 위치: ~/.cache/ultralytics/")
    
    return model

if __name__ == "__main__":
    # Raspberry Pi용 경량 모델
    model = download_pretrained_weights('n')
```

### 4.4 GPU 설정 확인

```python
# check_gpu.py
import torch

def check_gpu_availability():
    """GPU 사용 가능 여부를 확인합니다."""
    print("=== GPU 정보 ===")
    print(f"PyTorch 버전: {torch.__version__}")
    print(f"CUDA 사용 가능: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"CUDA 버전: {torch.version.cuda}")
        print(f"GPU 개수: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
            print(f"  메모리: {torch.cuda.get_device_properties(i).total_memory / 1e9:.2f} GB")
    else:
        print("⚠️  CPU 모드로 실행됩니다 (훈련 시간이 오래 걸릴 수 있습니다)")

if __name__ == "__main__":
    check_gpu_availability()
```

---

## 5. 4단계: YOLO11 모델 훈련

### 5.1 훈련 파라미터 이해

#### 주요 하이퍼파라미터
| 파라미터 | 설명 | 권장값 | 영향 |
|---------|------|--------|------|
| `epochs` | 전체 데이터셋 반복 횟수 | 50-300 | 높을수록 정확하지만 과적합 위험 |
| `batch` | 한 번에 처리할 이미지 수 | 16-32 | GPU 메모리에 따라 조정 |
| `imgsz` | 입력 이미지 크기 | 640 | 크면 정확, 작으면 빠름 |
| `lr0` | 초기 학습률 | 0.01 | 학습 속도 조절 |
| `patience` | 조기 종료 인내 | 50 | 개선 없을 시 종료 |
| `augment` | 데이터 증강 사용 | True | 과적합 방지 |

### 5.2 훈련 스크립트

```python
# train_yolo11.py
from ultralytics import YOLO
import torch
from pathlib import Path

class YOLO11Trainer:
    """
    YOLO11 모델 훈련을 관리하는 클래스
    """
    
    def __init__(self,
                 model_size: str = 'n',
                 data_yaml: str = 'data.yaml',
                 project_name: str = 'yolo11_training',
                 experiment_name: str = 'exp'):
        """
        Args:
            model_size: 모델 크기 ('n', 's', 'm', 'l', 'x')
            data_yaml: 데이터 설정 파일 경로
            project_name: 프로젝트 이름
            experiment_name: 실험 이름
        """
        self.model_size = model_size
        self.data_yaml = data_yaml
        self.project_name = project_name
        self.experiment_name = experiment_name
        
        # 모델 초기화
        model_path = f'yolo11{model_size}.pt'
        self.model = YOLO(model_path)
        
        # 장치 설정
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"🔧 훈련 장치: {self.device}")
    
    def train(self,
              epochs: int = 100,
              batch: int = 16,
              imgsz: int = 640,
              patience: int = 50,
              save_period: int = 10,
              resume: bool = False):
        """
        모델을 훈련합니다.
        
        Args:
            epochs: 훈련 에포크 수
            batch: 배치 크기
            imgsz: 이미지 크기
            patience: 조기 종료 인내 (에포크)
            save_period: 체크포인트 저장 주기
            resume: 이전 훈련 재개 여부
        """
        print("🚀 YOLO11 훈련 시작...")
        print(f"   모델: yolo11{self.model_size}")
        print(f"   데이터: {self.data_yaml}")
        print(f"   에포크: {epochs}")
        print(f"   배치 크기: {batch}")
        print(f"   이미지 크기: {imgsz}")
        
        # 훈련 실행
        results = self.model.train(
            data=self.data_yaml,
            epochs=epochs,
            batch=batch,
            imgsz=imgsz,
            device=self.device,
            patience=patience,
            save_period=save_period,
            project=self.project_name,
            name=self.experiment_name,
            resume=resume,
            
            # 데이터 증강 설정
            augment=True,
            hsv_h=0.015,  # 색조 증강
            hsv_s=0.7,    # 채도 증강
            hsv_v=0.4,    # 명도 증강
            degrees=0.0,  # 회전 증강
            translate=0.1,  # 이동 증강
            scale=0.5,    # 크기 증강
            shear=0.0,    # 전단 증강
            perspective=0.0,  # 원근 증강
            flipud=0.0,   # 상하 반전
            fliplr=0.5,   # 좌우 반전
            mosaic=1.0,   # 모자이크 증강
            mixup=0.0,    # 믹스업 증강
            
            # 최적화 설정
            optimizer='auto',  # 'SGD', 'Adam', 'AdamW', 'auto'
            lr0=0.01,     # 초기 학습률
            lrf=0.01,     # 최종 학습률 (lr0 * lrf)
            momentum=0.937,  # SGD 모멘텀
            weight_decay=0.0005,  # 가중치 감쇠
            warmup_epochs=3.0,  # 워밍업 에포크
            warmup_momentum=0.8,  # 워밍업 모멘텀
            warmup_bias_lr=0.1,  # 워밍업 바이어스 학습률
            
            # 기타 설정
            verbose=True,  # 상세 출력
            seed=0,  # 랜덤 시드
            deterministic=True,  # 결과 재현성
            single_cls=False,  # 단일 클래스 훈련
            rect=False,  # 직사각형 훈련
            cos_lr=False,  # 코사인 학습률 스케줄러
            close_mosaic=10,  # 마지막 N 에포크에서 모자이크 비활성화
            amp=True,  # 자동 혼합 정밀도
            fraction=1.0,  # 훈련 데이터 비율
            profile=False,  # ONNX 및 TensorRT 속도 프로파일링
            freeze=None,  # 동결할 레이어 수
            multi_scale=False,  # 멀티스케일 훈련
        )
        
        print("✅ 훈련 완료!")
        print(f"   최적 가중치: {self.project_name}/{self.experiment_name}/weights/best.pt")
        print(f"   최종 가중치: {self.project_name}/{self.experiment_name}/weights/last.pt")
        
        return results
    
    def export_results(self):
        """훈련 결과를 요약합니다."""
        results_dir = Path(self.project_name) / self.experiment_name
        
        print("\n📊 훈련 결과 파일:")
        print(f"   - 가중치: {results_dir}/weights/")
        print(f"   - 결과 그래프: {results_dir}/results.png")
        print(f"   - 혼동 행렬: {results_dir}/confusion_matrix.png")
        print(f"   - 검증 배치: {results_dir}/val_batch*.jpg")

# 사용 예시
if __name__ == "__main__":
    trainer = YOLO11Trainer(
        model_size='n',  # Raspberry Pi용 경량 모델
        data_yaml='yolo_dataset/data.yaml',
        project_name='raspbot_yolo11',
        experiment_name='traffic_detection'
    )
    
    # 훈련 실행
    results = trainer.train(
        epochs=100,
        batch=16,
        imgsz=640,
        patience=50
    )
    
    # 결과 요약
    trainer.export_results()
```

### 5.3 훈련 명령어 (간단 버전)

```bash
# 기본 훈련
yolo task=detect mode=train model=yolo11n.pt data=data.yaml epochs=100 imgsz=640

# GPU 지정
yolo task=detect mode=train model=yolo11n.pt data=data.yaml device=0

# 배치 크기 조정
yolo task=detect mode=train model=yolo11n.pt data=data.yaml batch=32

# 멀티 GPU 훈련
yolo task=detect mode=train model=yolo11n.pt data=data.yaml device=0,1
```

### 5.4 훈련 모니터링

#### TensorBoard 사용
```bash
# TensorBoard 설치
pip install tensorboard

# TensorBoard 실행
tensorboard --logdir runs/detect/train

# 브라우저에서 확인
# http://localhost:6006
```

#### 실시간 모니터링 스크립트
```python
# monitor_training.py
import time
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

def monitor_training(results_csv_path: str, interval: int = 10):
    """
    훈련 진행 상황을 실시간으로 모니터링합니다.
    
    Args:
        results_csv_path: results.csv 파일 경로
        interval: 업데이트 간격 (초)
    """
    results_path = Path(results_csv_path)
    
    if not results_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {results_csv_path}")
        return
    
    plt.ion()  # 인터랙티브 모드
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    try:
        while True:
            df = pd.read_csv(results_path)
            
            # 1. Loss 그래프
            axes[0, 0].clear()
            axes[0, 0].plot(df['epoch'], df['train/box_loss'], label='Box Loss')
            axes[0, 0].plot(df['epoch'], df['train/cls_loss'], label='Class Loss')
            axes[0, 0].set_title('Training Loss')
            axes[0, 0].set_xlabel('Epoch')
            axes[0, 0].legend()
            
            # 2. mAP 그래프
            axes[0, 1].clear()
            axes[0, 1].plot(df['epoch'], df['metrics/mAP50(B)'], label='mAP50')
            axes[0, 1].plot(df['epoch'], df['metrics/mAP50-95(B)'], label='mAP50-95')
            axes[0, 1].set_title('Validation mAP')
            axes[0, 1].set_xlabel('Epoch')
            axes[0, 1].legend()
            
            # 3. Precision & Recall
            axes[1, 0].clear()
            axes[1, 0].plot(df['epoch'], df['metrics/precision(B)'], label='Precision')
            axes[1, 0].plot(df['epoch'], df['metrics/recall(B)'], label='Recall')
            axes[1, 0].set_title('Precision & Recall')
            axes[1, 0].set_xlabel('Epoch')
            axes[1, 0].legend()
            
            # 4. 학습률
            axes[1, 1].clear()
            axes[1, 1].plot(df['epoch'], df['lr/pg0'], label='Learning Rate')
            axes[1, 1].set_title('Learning Rate')
            axes[1, 1].set_xlabel('Epoch')
            axes[1, 1].legend()
            
            plt.tight_layout()
            plt.pause(interval)
            
    except KeyboardInterrupt:
        print("\n⏹️  모니터링 종료")
    finally:
        plt.ioff()
        plt.show()

if __name__ == "__main__":
    monitor_training("raspbot_yolo11/traffic_detection/results.csv")
```

---

## 6. 5단계: 모델 검증 및 테스트

### 6.1 모델 검증

```python
# validate_model.py
from ultralytics import YOLO

class ModelValidator:
    """
    훈련된 YOLO 모델을 검증하는 클래스
    """
    
    def __init__(self, weights_path: str, data_yaml: str):
        """
        Args:
            weights_path: 가중치 파일 경로 (best.pt)
            data_yaml: 데이터 설정 파일
        """
        self.model = YOLO(weights_path)
        self.data_yaml = data_yaml
    
    def validate(self, imgsz: int = 640, conf: float = 0.25, iou: float = 0.6):
        """
        검증 데이터셋으로 모델 성능을 평가합니다.
        
        Args:
            imgsz: 이미지 크기
            conf: 신뢰도 임계값
            iou: IoU 임계값 (NMS)
            
        Returns:
            검증 결과 딕셔너리
        """
        print("🔍 모델 검증 시작...")
        
        results = self.model.val(
            data=self.data_yaml,
            imgsz=imgsz,
            conf=conf,
            iou=iou,
            batch=16,
            save_json=True,  # COCO JSON 형식 저장
            save_hybrid=True,  # 하이브리드 라벨 저장
            plots=True  # 시각화 저장
        )
        
        # 결과 출력
        print("\n📊 검증 결과:")
        print(f"   mAP50: {results.results_dict['metrics/mAP50(B)']:.4f}")
        print(f"   mAP50-95: {results.results_dict['metrics/mAP50-95(B)']:.4f}")
        print(f"   Precision: {results.results_dict['metrics/precision(B)']:.4f}")
        print(f"   Recall: {results.results_dict['metrics/recall(B)']:.4f}")
        
        return results
    
    def get_class_metrics(self, results):
        """클래스별 성능 지표를 출력합니다."""
        print("\n📋 클래스별 성능:")
        print(f"{'Class':<20} {'Precision':<12} {'Recall':<12} {'mAP50':<12}")
        print("-" * 60)
        
        # 클래스별 지표 (results 객체에서 추출)
        # 실제 구현 시 results 구조에 맞게 수정 필요

# 사용 예시
if __name__ == "__main__":
    validator = ModelValidator(
        weights_path="raspbot_yolo11/traffic_detection/weights/best.pt",
        data_yaml="yolo_dataset/data.yaml"
    )
    
    results = validator.validate()
```

### 6.2 성능 지표 이해

#### 주요 지표 설명
| 지표 | 설명 | 이상적 값 |
|------|------|----------|
| **mAP50** | IoU 0.5에서의 평균 정밀도 | > 0.7 |
| **mAP50-95** | IoU 0.5~0.95의 평균 정밀도 | > 0.5 |
| **Precision** | 정밀도 (TP / (TP + FP)) | > 0.8 |
| **Recall** | 재현율 (TP / (TP + FN)) | > 0.7 |
| **F1-Score** | Precision과 Recall의 조화 평균 | > 0.75 |

#### 혼동 행렬 분석
```python
# confusion_matrix_analyzer.py
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def analyze_confusion_matrix(matrix_path: str, class_names: list):
    """
    혼동 행렬을 분석하고 시각화합니다.
    
    Args:
        matrix_path: 혼동 행렬 npy 파일 경로
        class_names: 클래스 이름 리스트
    """
    # 혼동 행렬 로드
    cm = np.load(matrix_path)
    
    # 정규화
    cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    
    # 시각화
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        cm_normalized,
        annot=True,
        fmt='.2f',
        cmap='Blues',
        xticklabels=class_names + ['Background'],
        yticklabels=class_names
    )
    plt.title('Normalized Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig('confusion_matrix_analyzed.png', dpi=300)
    plt.show()
    
    # 클래스별 정확도
    print("\n📊 클래스별 정확도:")
    for i, class_name in enumerate(class_names):
        accuracy = cm_normalized[i, i]
        print(f"   {class_name}: {accuracy:.2%}")
```

### 6.3 테스트 이미지 추론

```python
# test_inference.py
from ultralytics import YOLO
import cv2
from pathlib import Path
import time

class YOLOInference:
    """
    훈련된 YOLO 모델로 추론을 수행하는 클래스
    """
    
    def __init__(self, weights_path: str, conf_threshold: float = 0.25):
        """
        Args:
            weights_path: 모델 가중치 경로
            conf_threshold: 신뢰도 임계값
        """
        self.model = YOLO(weights_path)
        self.conf_threshold = conf_threshold
    
    def predict_image(self, image_path: str, save: bool = True):
        """
        단일 이미지에 대해 추론합니다.
        
        Args:
            image_path: 이미지 파일 경로
            save: 결과 이미지 저장 여부
            
        Returns:
            추론 결과 객체
        """
        results = self.model.predict(
            source=image_path,
            conf=self.conf_threshold,
            save=save,
            save_txt=True,  # 라벨 저장
            save_conf=True,  # 신뢰도 저장
            line_width=2,
            show_labels=True,
            show_conf=True
        )
        
        return results[0]
    
    def predict_directory(self, directory_path: str):
        """
        디렉토리 내 모든 이미지에 대해 추론합니다.
        
        Args:
            directory_path: 이미지 디렉토리 경로
        """
        image_dir = Path(directory_path)
        image_files = list(image_dir.glob('*.jpg')) + list(image_dir.glob('*.png'))
        
        print(f"🖼️  총 {len(image_files)}개의 이미지 처리 중...")
        
        total_time = 0
        for img_path in image_files:
            start_time = time.time()
            results = self.predict_image(str(img_path))
            inference_time = time.time() - start_time
            total_time += inference_time
            
            # 검출된 객체 출력
            num_detections = len(results.boxes)
            print(f"   {img_path.name}: {num_detections}개 객체 검출 ({inference_time*1000:.1f}ms)")
        
        avg_time = total_time / len(image_files)
        print(f"\n⏱️  평균 추론 시간: {avg_time*1000:.1f}ms")
        print(f"   FPS: {1/avg_time:.1f}")
    
    def visualize_results(self, results, original_image_path: str):
        """
        추론 결과를 시각화합니다.
        
        Args:
            results: 추론 결과
            original_image_path: 원본 이미지 경로
        """
        img = cv2.imread(original_image_path)
        
        # 검출 결과 그리기
        for box in results.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            conf = box.conf[0].cpu().numpy()
            cls = int(box.cls[0].cpu().numpy())
            label = f"{results.names[cls]} {conf:.2f}"
            
            # 바운딩 박스
            cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            
            # 라벨
            cv2.putText(
                img, label,
                (int(x1), int(y1) - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (0, 255, 0), 2
            )
        
        # 결과 표시
        cv2.imshow('YOLO11 Detection', img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

# 사용 예시
if __name__ == "__main__":
    inference = YOLOInference(
        weights_path="raspbot_yolo11/traffic_detection/weights/best.pt",
        conf_threshold=0.25
    )
    
    # 단일 이미지 테스트
    results = inference.predict_image("test_images/test_001.jpg")
    
    # 디렉토리 전체 테스트
    inference.predict_directory("test_images/")
```

### 6.4 실시간 비디오 추론

```python
# realtime_video_inference.py
from ultralytics import YOLO
import cv2
import time

class RealtimeVideoInference:
    """
    실시간 비디오 스트림에서 YOLO 추론을 수행하는 클래스
    """
    
    def __init__(self, weights_path: str, conf_threshold: float = 0.25):
        """
        Args:
            weights_path: 모델 가중치 경로
            conf_threshold: 신뢰도 임계값
        """
        self.model = YOLO(weights_path)
        self.conf_threshold = conf_threshold
    
    def run_webcam(self):
        """웹캠으로 실시간 추론을 실행합니다."""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ 웹캠을 열 수 없습니다")
            return
        
        print("🎥 실시간 추론 시작 (q 키로 종료)")
        
        fps_list = []
        
        while True:
            start_time = time.time()
            
            ret, frame = cap.read()
            if not ret:
                break
            
            # YOLO 추론
            results = self.model.predict(
                source=frame,
                conf=self.conf_threshold,
                verbose=False
            )[0]
            
            # 결과 시각화
            annotated_frame = results.plot()
            
            # FPS 계산
            fps = 1 / (time.time() - start_time)
            fps_list.append(fps)
            
            # FPS 표시
            cv2.putText(
                annotated_frame,
                f"FPS: {fps:.1f}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1, (0, 255, 0), 2
            )
            
            # 화면 표시
            cv2.imshow('YOLO11 Realtime Detection', annotated_frame)
            
            # 종료 조건
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        # 평균 FPS 출력
        if fps_list:
            avg_fps = sum(fps_list) / len(fps_list)
            print(f"\n⏱️  평균 FPS: {avg_fps:.1f}")
    
    def run_video_file(self, video_path: str, save_output: bool = True):
        """
        비디오 파일로 추론을 실행합니다.
        
        Args:
            video_path: 비디오 파일 경로
            save_output: 결과 비디오 저장 여부
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"❌ 비디오를 열 수 없습니다: {video_path}")
            return
        
        # 비디오 정보
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"🎬 비디오 처리 중...")
        print(f"   해상도: {width}x{height}")
        print(f"   FPS: {fps}")
        print(f"   총 프레임: {total_frames}")
        
        # 출력 비디오 설정
        if save_output:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(
                'output_detection.mp4',
                fourcc, fps, (width, height)
            )
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # YOLO 추론
            results = self.model.predict(
                source=frame,
                conf=self.conf_threshold,
                verbose=False
            )[0]
            
            # 결과 시각화
            annotated_frame = results.plot()
            
            # 진행률 표시
            progress = (frame_count / total_frames) * 100
            cv2.putText(
                annotated_frame,
                f"Progress: {progress:.1f}%",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1, (0, 255, 0), 2
            )
            
            # 저장
            if save_output:
                out.write(annotated_frame)
            
            # 화면 표시
            cv2.imshow('YOLO11 Video Detection', annotated_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        if save_output:
            out.release()
        cv2.destroyAllWindows()
        
        print(f"✅ 비디오 처리 완료: {frame_count}프레임")

# 사용 예시
if __name__ == "__main__":
    inference = RealtimeVideoInference(
        weights_path="raspbot_yolo11/traffic_detection/weights/best.pt",
        conf_threshold=0.3
    )
    
    # 웹캠 실시간 추론
    # inference.run_webcam()
    
    # 비디오 파일 추론
    inference.run_video_file("test_video.mp4", save_output=True)
```

---

## 7. 6단계: Raspberry Pi 실전 배포

### 7.1 모델 최적화

#### 7.1.1 ONNX 변환
```python
# export_to_onnx.py
from ultralytics import YOLO

def export_model_to_onnx(weights_path: str, 
                         simplify: bool = True,
                         dynamic: bool = False):
    """
    YOLO 모델을 ONNX 포맷으로 변환합니다.
    
    Args:
        weights_path: PyTorch 가중치 경로 (.pt)
        simplify: ONNX 모델 단순화 여부
        dynamic: 동적 입력 크기 지원 여부
    """
    model = YOLO(weights_path)
    
    print("🔄 ONNX 변환 중...")
    
    # ONNX 내보내기
    model.export(
        format='onnx',
        simplify=simplify,
        dynamic=dynamic,
        opset=12  # ONNX opset 버전
    )
    
    output_path = weights_path.replace('.pt', '.onnx')
    print(f"✅ ONNX 모델 저장: {output_path}")
    
    return output_path

if __name__ == "__main__":
    export_model_to_onnx(
        "raspbot_yolo11/traffic_detection/weights/best.pt",
        simplify=True
    )
```

#### 7.1.2 TensorFlow Lite 변환
```python
# export_to_tflite.py
from ultralytics import YOLO

def export_model_to_tflite(weights_path: str, int8: bool = False):
    """
    YOLO 모델을 TensorFlow Lite 포맷으로 변환합니다.
    
    Args:
        weights_path: PyTorch 가중치 경로
        int8: INT8 양자화 여부 (더 경량화)
    """
    model = YOLO(weights_path)
    
    print("🔄 TensorFlow Lite 변환 중...")
    
    # TFLite 내보내기
    model.export(
        format='tflite',
        int8=int8  # INT8 양자화
    )
    
    output_path = weights_path.replace('.pt', '_saved_model')
    print(f"✅ TFLite 모델 저장: {output_path}")
    
    return output_path

if __name__ == "__main__":
    export_model_to_tflite(
        "raspbot_yolo11/traffic_detection/weights/best.pt",
        int8=True  # Raspberry Pi를 위한 최적화
    )
```

### 7.2 Raspberry Pi 설치

```bash
# Raspberry Pi에서 실행

# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 의존성 설치
sudo apt install -y python3-pip python3-opencv libopencv-dev

# Ultralytics 설치 (경량 버전)
pip3 install ultralytics[export]

# OpenCV 설치
pip3 install opencv-python-headless

# 추가 의존성
pip3 install numpy Pillow
```

### 7.3 Raspberry Pi 추론 스크립트

```python
# raspberrypi_inference.py
"""
Raspberry Pi 자율주행 자동차용 YOLO11 추론 스크립트
"""
from ultralytics import YOLO
import cv2
import numpy as np
from picamera2 import Picamera2
import time

class RaspberryPiYOLO:
    """
    Raspberry Pi에서 YOLO 추론을 수행하는 클래스
    """
    
    def __init__(self, 
                 model_path: str,
                 conf_threshold: float = 0.3,
                 img_size: int = 320):  # 경량화를 위해 320 사용
        """
        Args:
            model_path: 모델 경로 (best.pt 또는 best.onnx)
            conf_threshold: 신뢰도 임계값
            img_size: 입력 이미지 크기 (작을수록 빠름)
        """
        print("🚗 RaspberryPi YOLO 초기화 중...")
        
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold
        self.img_size = img_size
        
        # Picamera2 초기화
        self.picam2 = Picamera2()
        camera_config = self.picam2.create_preview_configuration(
            main={"size": (640, 480)}
        )
        self.picam2.configure(camera_config)
        self.picam2.start()
        
        print("✅ 초기화 완료")
    
    def preprocess_frame(self, frame):
        """
        프레임을 전처리합니다.
        
        Args:
            frame: 원본 프레임
            
        Returns:
            전처리된 프레임
        """
        # 리사이즈 (성능 향상)
        if frame.shape[:2] != (self.img_size, self.img_size):
            frame = cv2.resize(frame, (self.img_size, self.img_size))
        
        return frame
    
    def detect_objects(self, frame):
        """
        객체를 검출합니다.
        
        Args:
            frame: 입력 프레임
            
        Returns:
            검출 결과 리스트
        """
        # 추론
        results = self.model.predict(
            source=frame,
            conf=self.conf_threshold,
            verbose=False,
            imgsz=self.img_size
        )[0]
        
        # 검출 결과 파싱
        detections = []
        for box in results.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            conf = float(box.conf[0].cpu().numpy())
            cls = int(box.cls[0].cpu().numpy())
            class_name = results.names[cls]
            
            detections.append({
                'class': class_name,
                'confidence': conf,
                'bbox': (int(x1), int(y1), int(x2), int(y2))
            })
        
        return detections
    
    def run_detection_loop(self, display: bool = False):
        """
        실시간 객체 검출 루프를 실행합니다.
        
        Args:
            display: 화면 표시 여부 (False 권장 - 성능)
        """
        print("🎥 실시간 검출 시작...")
        
        fps_list = []
        
        try:
            while True:
                start_time = time.time()
                
                # 프레임 캡처
                frame = self.picam2.capture_array()
                
                # RGB로 변환
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # 전처리
                processed_frame = self.preprocess_frame(frame_rgb)
                
                # 객체 검출
                detections = self.detect_objects(processed_frame)
                
                # FPS 계산
                fps = 1 / (time.time() - start_time)
                fps_list.append(fps)
                
                # 검출 결과 출력
                if detections:
                    print(f"[FPS: {fps:.1f}] 검출: {len(detections)}개")
                    for det in detections:
                        print(f"  - {det['class']}: {det['confidence']:.2f}")
                
                # 화면 표시 (선택)
                if display:
                    for det in detections:
                        x1, y1, x2, y2 = det['bbox']
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        label = f"{det['class']} {det['confidence']:.2f}"
                        cv2.putText(
                            frame, label, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (0, 255, 0), 2
                        )
                    
                    cv2.imshow('Detection', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
        except KeyboardInterrupt:
            print("\n⏹️  검출 종료")
        
        finally:
            self.cleanup()
            
            if fps_list:
                avg_fps = sum(fps_list) / len(fps_list)
                print(f"⏱️  평균 FPS: {avg_fps:.1f}")
    
    def cleanup(self):
        """리소스를 정리합니다."""
        self.picam2.stop()
        cv2.destroyAllWindows()
        print("✅ 리소스 정리 완료")

# 사용 예시
if __name__ == "__main__":
    detector = RaspberryPiYOLO(
        model_path="best.pt",  # 또는 "best.onnx"
        conf_threshold=0.3,
        img_size=320  # 성능을 위해 작은 크기 사용
    )
    
    detector.run_detection_loop(display=False)
```

### 7.4 자율주행 통합

```python
# autonomous_driving_system.py
"""
YOLO 객체 검출을 통합한 자율주행 시스템
"""
from raspberrypi_inference import RaspberryPiYOLO
import RPi.GPIO as GPIO
import time

class AutonomousDrivingSystem:
    """
    YOLO 기반 자율주행 시스템
    """
    
    def __init__(self, model_path: str):
        """
        Args:
            model_path: YOLO 모델 경로
        """
        # YOLO 검출기 초기화
        self.detector = RaspberryPiYOLO(
            model_path=model_path,
            conf_threshold=0.4,
            img_size=320
        )
        
        # 모터 제어 초기화 (하드웨어에 맞게 수정)
        self.setup_motors()
        
        # 주행 상태
        self.current_speed = 0
        self.is_obstacle_detected = False
        self.stop_sign_detected = False
    
    def setup_motors(self):
        """모터 제어 GPIO 설정"""
        GPIO.setmode(GPIO.BCM)
        
        # 모터 핀 설정 (예시)
        self.MOTOR_LEFT_FORWARD = 17
        self.MOTOR_LEFT_BACKWARD = 27
        self.MOTOR_RIGHT_FORWARD = 22
        self.MOTOR_RIGHT_BACKWARD = 23
        
        # GPIO 초기화
        for pin in [self.MOTOR_LEFT_FORWARD, self.MOTOR_LEFT_BACKWARD,
                    self.MOTOR_RIGHT_FORWARD, self.MOTOR_RIGHT_BACKWARD]:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
    
    def move_forward(self, speed: int = 50):
        """전진"""
        # PWM 제어 구현 (예시)
        GPIO.output(self.MOTOR_LEFT_FORWARD, GPIO.HIGH)
        GPIO.output(self.MOTOR_RIGHT_FORWARD, GPIO.HIGH)
        self.current_speed = speed
    
    def stop(self):
        """정지"""
        for pin in [self.MOTOR_LEFT_FORWARD, self.MOTOR_LEFT_BACKWARD,
                    self.MOTOR_RIGHT_FORWARD, self.MOTOR_RIGHT_BACKWARD]:
            GPIO.output(pin, GPIO.LOW)
        self.current_speed = 0
    
    def process_detections(self, detections: list):
        """
        검출 결과를 처리하고 주행 결정을 내립니다.
        
        Args:
            detections: 검출된 객체 리스트
        """
        # 정지 신호 감지
        if any(det['class'] == 'stop_sign' and det['confidence'] > 0.6 
               for det in detections):
            if not self.stop_sign_detected:
                print("🛑 정지 신호 감지 - 3초 정지")
                self.stop()
                self.stop_sign_detected = True
                time.sleep(3)
        else:
            self.stop_sign_detected = False
        
        # 장애물 감지
        obstacles = [det for det in detections 
                    if det['class'] in ['pedestrian', 'obstacle']]
        
        if obstacles:
            # 가장 가까운 장애물 찾기
            closest_obstacle = min(
                obstacles,
                key=lambda x: (x['bbox'][2] - x['bbox'][0]) * 
                             (x['bbox'][3] - x['bbox'][1])
            )
            
            bbox = closest_obstacle['bbox']
            bbox_size = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
            
            # 바운딩 박스 크기로 거리 추정
            if bbox_size > 50000:  # 너무 가까움
                print("⚠️  장애물 근접 - 정지")
                self.stop()
                self.is_obstacle_detected = True
            else:
                self.is_obstacle_detected = False
        else:
            self.is_obstacle_detected = False
        
        # 정상 주행
        if not self.is_obstacle_detected and not self.stop_sign_detected:
            self.move_forward(speed=50)
    
    def run(self):
        """자율주행 시스템 실행"""
        print("🚗 자율주행 시작...")
        
        try:
            while True:
                # 프레임 캡처
                frame = self.detector.picam2.capture_array()
                
                # 객체 검출
                detections = self.detector.detect_objects(frame)
                
                # 주행 결정
                self.process_detections(detections)
                
                time.sleep(0.1)  # CPU 부하 감소
                
        except KeyboardInterrupt:
            print("\n⏹️  자율주행 종료")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """리소스 정리"""
        self.stop()
        self.detector.cleanup()
        GPIO.cleanup()
        print("✅ 시스템 종료 완료")

# 사용 예시
if __name__ == "__main__":
    system = AutonomousDrivingSystem(model_path="best.pt")
    system.run()
```

---

## 8. 주요 함수 및 알고리즘

### 8.1 YOLO 핵심 알고리즘

#### 8.1.1 바운딩 박스 예측
```python
def decode_yolo_predictions(predictions, anchors, num_classes):
    """
    YOLO 출력을 바운딩 박스로 디코딩합니다.
    
    Args:
        predictions: 모델 출력 (batch, grid_h, grid_w, anchors, 5+classes)
        anchors: 앵커 박스 크기
        num_classes: 클래스 개수
        
    Returns:
        boxes: (x, y, w, h) 바운딩 박스
        confidences: 객체 신뢰도
        class_probs: 클래스 확률
    """
    grid_h, grid_w = predictions.shape[1:3]
    num_anchors = len(anchors)
    
    # 그리드 좌표 생성
    grid_x = np.arange(grid_w).reshape(1, 1, grid_w, 1, 1)
    grid_y = np.arange(grid_h).reshape(1, grid_h, 1, 1, 1)
    
    # 바운딩 박스 중심 좌표 계산
    pred_x = (sigmoid(predictions[..., 0]) + grid_x) / grid_w
    pred_y = (sigmoid(predictions[..., 1]) + grid_y) / grid_h
    
    # 바운딩 박스 크기 계산
    pred_w = np.exp(predictions[..., 2]) * anchors[..., 0] / grid_w
    pred_h = np.exp(predictions[..., 3]) * anchors[..., 1] / grid_h
    
    # 신뢰도 및 클래스 확률
    confidences = sigmoid(predictions[..., 4])
    class_probs = sigmoid(predictions[..., 5:])
    
    return (pred_x, pred_y, pred_w, pred_h), confidences, class_probs

def sigmoid(x):
    """시그모이드 활성화 함수"""
    return 1 / (1 + np.exp(-x))
```

#### 8.1.2 Non-Maximum Suppression (NMS)
```python
def non_max_suppression(boxes, scores, iou_threshold=0.5):
    """
    중복 박스를 제거하는 NMS 알고리즘
    
    Args:
        boxes: (N, 4) 바운딩 박스 [x1, y1, x2, y2]
        scores: (N,) 신뢰도 점수
        iou_threshold: IoU 임계값
        
    Returns:
        선택된 박스 인덱스
    """
    # 신뢰도 기준 정렬
    sorted_indices = np.argsort(scores)[::-1]
    
    keep_indices = []
    
    while len(sorted_indices) > 0:
        # 가장 높은 신뢰도 박스 선택
        current_idx = sorted_indices[0]
        keep_indices.append(current_idx)
        
        # 나머지 박스들과 IoU 계산
        if len(sorted_indices) == 1:
            break
        
        current_box = boxes[current_idx]
        other_boxes = boxes[sorted_indices[1:]]
        
        # IoU 계산
        ious = compute_iou(current_box, other_boxes)
        
        # IoU가 임계값 이하인 박스만 유지
        sorted_indices = sorted_indices[1:][ious < iou_threshold]
    
    return keep_indices

def compute_iou(box1, boxes):
    """
    IoU (Intersection over Union) 계산
    
    Args:
        box1: (4,) 단일 박스 [x1, y1, x2, y2]
        boxes: (N, 4) 여러 박스
        
    Returns:
        (N,) IoU 값
    """
    # 교집합 영역 계산
    x1 = np.maximum(box1[0], boxes[:, 0])
    y1 = np.maximum(box1[1], boxes[:, 1])
    x2 = np.minimum(box1[2], boxes[:, 2])
    y2 = np.minimum(box1[3], boxes[:, 3])
    
    intersection = np.maximum(0, x2 - x1) * np.maximum(0, y2 - y1)
    
    # 합집합 영역 계산
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    union = area1 + area2 - intersection
    
    # IoU 계산
    iou = intersection / (union + 1e-6)
    
    return iou
```

### 8.2 데이터 증강 알고리즘

```python
def mosaic_augmentation(images, labels, grid_size=2):
    """
    모자이크 데이터 증강
    
    Args:
        images: 이미지 리스트 (최소 4개)
        labels: 라벨 리스트
        grid_size: 그리드 크기 (2x2)
        
    Returns:
        증강된 이미지 및 라벨
    """
    import random
    
    # 4개 이미지 랜덤 선택
    indices = random.sample(range(len(images)), 4)
    
    # 출력 이미지 크기
    h, w = images[0].shape[:2]
    mosaic_img = np.zeros((h * grid_size, w * grid_size, 3), dtype=np.uint8)
    mosaic_labels = []
    
    # 4개 이미지를 그리드에 배치
    for i, idx in enumerate(indices):
        row = i // grid_size
        col = i % grid_size
        
        # 이미지 배치
        y1 = row * h
        y2 = (row + 1) * h
        x1 = col * w
        x2 = (col + 1) * w
        
        mosaic_img[y1:y2, x1:x2] = images[idx]
        
        # 라벨 좌표 조정
        for label in labels[idx]:
            class_id, x_center, y_center, width, height = label
            
            # 새로운 좌표 계산
            new_x = (x_center * w + x1) / (w * grid_size)
            new_y = (y_center * h + y1) / (h * grid_size)
            new_w = width / grid_size
            new_h = height / grid_size
            
            mosaic_labels.append([class_id, new_x, new_y, new_w, new_h])
    
    return mosaic_img, mosaic_labels
```

### 8.3 성능 최적화 함수

```python
def optimize_inference_speed(model, input_size=(320, 320)):
    """
    추론 속도 최적화
    
    Args:
        model: YOLO 모델
        input_size: 입력 크기
    """
    import torch
    
    # Half precision (FP16) 변환
    if torch.cuda.is_available():
        model.half()
    
    # 정적 입력 크기 설정
    dummy_input = torch.randn(1, 3, *input_size)
    
    # TorchScript 컴파일
    traced_model = torch.jit.trace(model, dummy_input)
    
    # 최적화
    traced_model = torch.jit.optimize_for_inference(traced_model)
    
    return traced_model
```

---

## 9. 트러블슈팅

### 9.1 일반적인 문제 및 해결책

#### 문제 1: 훈련 시 GPU 메모리 부족
**증상**: `CUDA out of memory` 에러

**해결책**:
```python
# 배치 크기 줄이기
batch=8  # 기존 16에서 8로

# 이미지 크기 줄이기
imgsz=416  # 기존 640에서 416으로

# Gradient accumulation 사용
accumulate=4  # 4번 누적 후 업데이트
```

#### 문제 2: 과적합 (Overfitting)
**증상**: 훈련 정확도는 높지만 검증 정확도는 낮음

**해결책**:
```python
# 1. 데이터 증강 강화
augment=True
mosaic=1.0
mixup=0.5

# 2. Dropout 추가
dropout=0.1

# 3. 조기 종료
patience=30  # 30 에포크 동안 개선 없으면 종료

# 4. 정규화 강화
weight_decay=0.001
```

#### 문제 3: 작은 객체 검출 실패
**증상**: 큰 객체는 잘 검출하지만 작은 객체는 놓침

**해결책**:
```python
# 1. 더 큰 이미지 크기 사용
imgsz=1280  # 기존 640에서 증가

# 2. 작은 객체 데이터 증강
# - 복사 및 붙여넣기
# - 크기 조정

# 3. 멀티스케일 훈련
multi_scale=True
```

#### 문제 4: Raspberry Pi에서 낮은 FPS
**증상**: 실시간 추론이 너무 느림 (< 5 FPS)

**해결책**:
```python
# 1. 더 작은 입력 크기
imgsz=320  # 기존 640에서 감소

# 2. 경량 모델 사용
model = YOLO('yolo11n.pt')  # nano 버전

# 3. ONNX 또는 TFLite 변환
model.export(format='onnx', simplify=True)

# 4. 해상도 감소
frame = cv2.resize(frame, (320, 240))
```

### 9.2 디버깅 체크리스트

#### 라벨링 단계
- [ ] 모든 이미지에 라벨이 있는가?
- [ ] 라벨 포맷이 올바른가? (YOLO 형식)
- [ ] 좌표가 0~1 범위인가?
- [ ] 클래스 ID가 올바른가?

#### 데이터셋 단계
- [ ] data.yaml 경로가 정확한가?
- [ ] train/val/test 분할이 올바른가?
- [ ] 클래스 개수가 일치하는가?
- [ ] 이미지와 라벨 파일명이 일치하는가?

#### 훈련 단계
- [ ] GPU가 정상 동작하는가?
- [ ] 배치 크기가 적절한가?
- [ ] Loss가 감소하는가?
- [ ] mAP가 증가하는가?
- [ ] 과적합 징후가 있는가?

#### 추론 단계
- [ ] 모델이 정상 로드되는가?
- [ ] 신뢰도 임계값이 적절한가?
- [ ] FPS가 충분한가?
- [ ] 검출 정확도가 만족스러운가?

### 9.3 성능 벤치마크

| 환경 | 모델 | 크기 | FPS | mAP50 |
|------|------|------|-----|-------|
| Desktop GPU (RTX 3080) | YOLOv11n | 640 | 150 | 0.85 |
| Desktop GPU (RTX 3080) | YOLOv11s | 640 | 100 | 0.90 |
| Laptop CPU (i7) | YOLOv11n | 640 | 15 | 0.85 |
| Laptop CPU (i7) | YOLOv11n | 320 | 30 | 0.82 |
| Raspberry Pi 4 | YOLOv11n | 640 | 3 | 0.85 |
| Raspberry Pi 4 | YOLOv11n | 320 | 8 | 0.82 |
| Raspberry Pi 4 (ONNX) | YOLOv11n | 320 | 12 | 0.82 |

---

## 10. 참고 자료

### 공식 문서
- [Ultralytics YOLO11 공식 문서](https://docs.ultralytics.com/)
- [LabelImg GitHub](https://github.com/HumanSignal/labelImg)
- [PyTorch 공식 문서](https://pytorch.org/docs/)

### 추천 튜토리얼
- YOLO 객체 검출 완전 가이드
- 자율주행을 위한 컴퓨터 비전
- Raspberry Pi 딥러닝 최적화

### 데이터셋
- COCO Dataset (일반 객체)
- KITTI Dataset (자율주행)
- BDD100K (자율주행)

---

## 📝 마무리

이 가이드를 통해 다음을 수행할 수 있습니다:
1. ✅ LabelImg로 이미지 라벨링
2. ✅ 데이터셋 구성 및 분할
3. ✅ YOLO11 모델 훈련
4. ✅ 모델 검증 및 테스트
5. ✅ Raspberry Pi에 배포
6. ✅ 실시간 자율주행 통합

**추가 지원이 필요하면 Ultralytics 커뮤니티 또는 GitHub Issues를 활용하세요!**

---

**작성일**: 2025-12-09  
**버전**: 1.0  
**프로젝트**: Raspbot v2 자율주행 자동차
