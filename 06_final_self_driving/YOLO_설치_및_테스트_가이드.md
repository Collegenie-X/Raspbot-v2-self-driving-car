# 🚀 YOLO11 설치 및 테스트 가이드

> Raspbot v2 자율주행 시스템을 위한 YOLO11 라이브러리 설치 및 기본 동작 확인

## 📋 목차

1. [시스템 요구사항](#-1-시스템-요구사항)
2. [설치 방법](#-2-설치-방법)
3. [기본 테스트](#-3-기본-테스트)
4. [문제 해결](#-4-문제-해결)

---

## 💻 1. 시스템 요구사항

### 최소 요구사항
- **OS**: Raspberry Pi OS (Bullseye 이상) 또는 Ubuntu 20.04+
- **Python**: 3.8 이상
- **RAM**: 2GB 이상 (권장: 4GB)
- **저장공간**: 2GB 이상 여유 공간

### 필수 패키지
```bash
# Python 3 및 pip 확인
python3 --version
pip3 --version
```

---

## 📦 2. 설치 방법

### 방법 1: 온라인 설치 (권장)

```bash
# 1. pip 업그레이드
pip3 install --upgrade pip

# 2. Ultralytics YOLO 설치 (자동으로 의존성 설치)
pip3 install ultralytics

# 3. 추가 패키지 설치 (OpenCV 등)
pip3 install opencv-python
```

### 방법 2: 오프라인 설치

```bash
# 1. 의존성 패키지 먼저 설치
pip3 install torch torchvision --no-deps
pip3 install opencv-python pillow pyyaml numpy

# 2. Ultralytics 설치 (의존성 체크 건너뛰기)
pip3 install ultralytics --no-deps
```

### 방법 3: 가상환경 사용 (권장)

```bash
# 1. 가상환경 생성
python3 -m venv yolo_env

# 2. 가상환경 활성화
source yolo_env/bin/activate

# 3. Ultralytics 설치
pip install ultralytics

# 4. 필요한 추가 패키지
pip install opencv-python
```

### 설치 확인

```bash
# Ultralytics 버전 확인
python3 -c "import ultralytics; print(ultralytics.__version__)"
```

**정상 출력 예시:**
```
✅ 8.x.x (또는 최신 버전)
```

---

## ✅ 3. 기본 테스트

### 테스트 1: 간단한 설치 확인

```bash
cd 06_final_self_driving
python3 test_yolo_basic.py
```

**테스트 내용:**
1. ✅ Ultralytics 패키지 import 확인
2. ✅ 필수 모듈 확인 (PyTorch, OpenCV, NumPy 등)
3. ✅ YOLO11 모델 로드 테스트
4. ✅ 더미 이미지로 추론 테스트
5. ✅ 샘플 이미지로 추론 테스트
6. 🎥 (선택) 카메라 실시간 테스트

**예상 출력:**
```
======================================================================
  YOLO11 기본 동작 테스트
======================================================================

[테스트 1] Ultralytics 패키지 import 확인
----------------------------------------------------------------------
✅ Ultralytics 설치 확인
   버전: 8.x.x

[테스트 2] 필수 모듈 확인
----------------------------------------------------------------------
✅ PyTorch: 2.x.x
✅ OpenCV: 4.x.x
✅ NumPy: 1.x.x
✅ Pillow: 10.x.x

[테스트 3] YOLO 모델 로드 테스트
----------------------------------------------------------------------
🔄 YOLO11n 모델 다운로드 및 로드 중...
   (처음 실행 시 인터넷에서 자동 다운로드, 약 10-30초 소요)
✅ YOLO11 모델 로드 성공!
   모델 이름: yolo11n
   태스크: detect

[테스트 4] 더미 이미지로 추론 테스트
----------------------------------------------------------------------
🔄 YOLO 추론 실행 중...
✅ YOLO 추론 성공!
   입력 이미지: 640x640x3
   검출된 객체: 0 개
     (더미 이미지이므로 검출 없음은 정상입니다)

[테스트 5] 샘플 이미지로 테스트
----------------------------------------------------------------------
🔄 샘플 이미지 다운로드 및 추론 중...
✅ 샘플 이미지 추론 성공!
   검출된 객체: 4 개
     - 객체 1: person (신뢰도: 0.88)
       위치: x1=12, y1=234, x2=567, y2=789
     - 객체 2: bus (신뢰도: 0.92)
       위치: x1=50, y1=100, x2=800, y2=600
     ...

======================================================================
  ✅ YOLO11 기본 테스트 완료!
======================================================================

✨ 테스트 결과 요약:
  1. ✅ Ultralytics 패키지 정상 동작
  2. ✅ YOLO11 모델 로드 성공
  3. ✅ 추론 엔진 정상 동작

💡 다음 단계:
  - 커스텀 모델 테스트: python3 test_yolo_model.py
  - 자율주행 시스템: python3 1_yolo_final_autoplot.py
======================================================================
```

### 테스트 2: 커스텀 모델 테스트 (신호등 감지)

```bash
# 커스텀 모델이 있는 경우
python3 test_yolo_model.py
```

**전제 조건:**
- `./models/traffic_modeln.pt` 파일 존재
- 또는 `./models/yolo11n.pt` 파일 존재

**기능:**
- 실시간 카메라 신호등 감지
- 빨간불/초록불 구분 (커스텀 모델)
- 일반 신호등 감지 (사전 학습 모델)

---

## 🐛 4. 문제 해결

### 문제 1: ModuleNotFoundError: No module named 'ultralytics'

**원인:** Ultralytics 패키지가 설치되지 않음

**해결:**
```bash
pip3 install ultralytics
```

---

### 문제 2: ImportError: cannot import name 'YOLO'

**원인:** Ultralytics 버전이 너무 낮음

**해결:**
```bash
pip3 install --upgrade ultralytics
```

---

### 문제 3: YOLO 모델 다운로드 실패

**원인:** 인터넷 연결 문제 또는 방화벽

**해결:**
```bash
# 1. 인터넷 연결 확인
ping google.com

# 2. 프록시 설정 (필요시)
export http_proxy=http://your-proxy:port
export https_proxy=http://your-proxy:port

# 3. 수동 다운로드
# https://github.com/ultralytics/assets/releases/download/v8.2.0/yolo11n.pt
# 다운로드 후 ~/.cache/ultralytics/ 폴더에 복사
```

---

### 문제 4: RuntimeError: CUDA not available

**원인:** GPU 사용 시도했지만 CUDA 미설치

**해결:**
```bash
# CPU 버전으로 강제 실행
python3 -c "import torch; print(torch.cuda.is_available())"

# CPU 모드로 YOLO 실행 (자동으로 CPU 사용)
# Raspberry Pi는 기본적으로 CPU만 사용
```

---

### 문제 5: 추론 속도가 너무 느림 (Raspberry Pi)

**원인:** Raspberry Pi의 제한된 성능

**해결:**
```python
# 1. 더 작은 모델 사용
model = YOLO("yolo11n.pt")  # nano 버전 (가장 작음)

# 2. 입력 이미지 크기 축소
results = model(frame, imgsz=320)  # 기본 640에서 320으로

# 3. 낮은 신뢰도 임계값
results = model(frame, conf=0.3)  # 기본 0.5에서 0.3으로

# 4. 프레임 건너뛰기
if frame_count % 10 == 0:  # 10프레임마다 1번만 추론
    results = model(frame)
```

**성능 비교 (Raspberry Pi 4):**
| 모델 | 입력 크기 | 추론 시간 | FPS |
|:---|:---:|:---:|:---:|
| yolo11n | 640x640 | 100-150ms | 6-10 |
| yolo11n | 320x320 | 50-80ms | 12-20 |
| yolo11s | 640x640 | 200-300ms | 3-5 |

---

### 문제 6: 카메라를 열 수 없습니다

**원인:** 카메라 권한 또는 다른 프로세스에서 사용 중

**해결:**
```bash
# 1. 카메라 장치 확인
ls -la /dev/video*

# 2. 권한 확인
sudo usermod -aG video $USER

# 3. 다른 프로세스 확인
sudo lsof /dev/video0

# 4. 프로세스 종료 (필요시)
sudo pkill -9 python
```

---

## 📚 5. 추가 리소스

### YOLO11 공식 문서
- [Ultralytics 공식 문서](https://docs.ultralytics.com/)
- [YOLO11 모델 소개](https://docs.ultralytics.com/models/yolo11/)

### 커스텀 모델 학습
- [커스텀 데이터셋 학습 가이드](https://docs.ultralytics.com/modes/train/)
- [신호등 감지 모델 학습 예제](https://docs.ultralytics.com/datasets/detect/)

### 성능 최적화
- [YOLO 최적화 가이드](https://docs.ultralytics.com/guides/optimizing-yolo/)
- [Raspberry Pi 최적화](https://docs.ultralytics.com/guides/raspberry-pi/)

---

## 🔄 6. 테스트 스크립트 비교

| 스크립트 | 용도 | 실행 시간 | 카메라 필요 |
|:---|:---|:---:|:---:|
| `test_yolo_basic.py` | 기본 설치 확인 | 30초-1분 | ❌ |
| `test_yolo_model.py` | 커스텀 모델 테스트 | 실시간 | ✅ |
| `1_yolo_final_autoplot.py` | 전체 자율주행 | 실시간 | ✅ |

---

## ✅ 7. 체크리스트

설치 및 테스트 완료 확인:

- [ ] Ultralytics 패키지 설치 완료
- [ ] `python3 -c "import ultralytics"` 오류 없음
- [ ] `test_yolo_basic.py` 모든 테스트 통과
- [ ] YOLO11 모델 로드 성공
- [ ] 더미 이미지 추론 성공
- [ ] (선택) 카메라 실시간 테스트 성공
- [ ] (선택) 커스텀 모델 테스트 성공

---

**문서 버전**: v1.0  
**최종 수정**: 2025-12-16  
**작성자**: Raspbot v2 개발팀

