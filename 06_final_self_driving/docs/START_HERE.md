# 🚗 시작 가이드 (Quick Start Guide)

Raspberry Pi YOLO11 + Haar Cascade 자율주행 시스템

---

## 🎯 어떤 방법으로 실행할까요?

### 📌 상황별 실행 방법

| 상황 | 실행 방법 | 명령어 |
|------|----------|--------|
| **SSH로 접속** (GUI 불필요) | 헤드리스 모드 | `./run_headless.sh` |
| **모니터 직접 연결** | GUI 모드 | `./run_yolo_autoplot.sh` |
| **VNC 원격 접속** | GUI 모드 | `python3 1_yolo_final_autoplot.py` |
| **X11 포워딩 설정됨** | GUI 모드 | `python3 1_yolo_final_autoplot.py` |

---

## ⚡ 가장 빠른 시작

### 1️⃣ SSH로 접속했다면 (가장 흔한 경우)

```bash
cd 06_final_self_driving
./run_headless.sh
```

**특징:**
- ✅ GUI 창 없음 (설정 불필요)
- ✅ 기본 설정으로 바로 실행
- ✅ 모터 제어 및 감지 기능 모두 작동
- ✅ 가장 안정적

---

### 2️⃣ 모니터에 직접 연결했다면

```bash
cd 06_final_self_driving
./run_yolo_autoplot.sh
```

**특징:**
- ✅ 실시간 영상 확인
- ✅ 트랙바로 파라미터 조정
- ✅ 디버깅 편리

---

### 3️⃣ VNC로 원격 접속했다면

```bash
cd 06_final_self_driving
python3 1_yolo_final_autoplot.py
```

**특징:**
- ✅ 완벽한 GUI 지원
- ✅ 원격에서 모든 기능 사용
- ✅ 가장 편리한 개발 환경

---

## 🔧 첫 실행 전 체크리스트

### ✅ 필수 확인 사항

```bash
# 1. 현재 위치 확인
pwd
# 출력: /home/pi (또는 다른 경로)

# 2. 프로젝트 디렉토리로 이동
cd ~/Raspbot-v2-self-driving-car/06_final_self_driving

# 3. 실행 권한 확인 및 부여
chmod +x run_yolo_autoplot.sh
chmod +x run_headless.sh
chmod +x diagnose_camera.sh
chmod +x test_camera.py
```

### ✅ 카메라 확인

```bash
# 카메라 진단
./diagnose_camera.sh

# 또는 간단 테스트
python3 test_camera.py
```

**출력 예시:**
```
✅ Found 1 working camera(s): [0]
💡 Recommended: Use camera index 0
```

### ✅ YOLO 모델 확인 (선택사항)

```bash
# 모델 파일 확인
ls -lh models/traffic_modeln.pt
```

**모델이 없어도 실행 가능:**
- ✅ Haar Cascade 표지판 감지 작동
- ✅ 자율주행 기능 작동
- ❌ 신호등 감지만 비활성화

---

## 🎮 실행 중 조작 키

실행 후 사용 가능한 키:

| 키 | 기능 |
|----|------|
| **ESC** | 프로그램 종료 |
| **SPACE** | 모터 ON/OFF 토글 |
| **L** | LED ON/OFF 토글 |
| **B** | 부저 ON/OFF 토글 |

---

## 🛠️ 문제 해결

### 문제 1: 프로그램이 멈춤

```
STEP 4: Setting up Trackbars and Windows...
(여기서 멈춤)
```

**해결:**
```bash
# 헤드리스 모드로 실행
./run_headless.sh
```

📚 자세한 해결: `DISPLAY_FIX_GUIDE.md`

---

### 문제 2: 카메라를 찾을 수 없음

```
Failed to initialize camera: Cannot read frame from camera
```

**해결:**
```bash
# 1. 카메라 진단
./diagnose_camera.sh

# 2. 권한 추가
sudo usermod -aG video $USER
sudo reboot

# 3. 다시 실행
./run_headless.sh
```

📚 자세한 해결: `CAMERA_FIX_GUIDE.md`

---

### 문제 3: YOLO 모델 없음

```
❌ Custom model not found: ./models/traffic_modeln.pt
```

**해결:**
1. 모델 없이 실행해도 됨 (신호등 감지만 비활성화)
2. 또는 커스텀 모델 파일을 `models/` 폴더에 복사

```bash
# 모델 파일 복사 (있다면)
cp /path/to/your/model.pt models/traffic_modeln.pt

# 모델 없이 실행 (Haar Cascade + 자율주행만)
./run_headless.sh
```

---

### 문제 4: Qt 플랫폼 플러그인 에러

```
qt.qpa.plugin: Could not find the Qt platform plugin "wayland"
```

**해결:**
```bash
# 자동으로 해결됨 (코드에 이미 포함)
# 또는 수동 설정:
export QT_QPA_PLATFORM=xcb
./run_yolo_autoplot.sh
```

📚 자세한 해결: `TROUBLESHOOTING.md`

---

## 📚 전체 문서 목록

| 문서 | 내용 |
|------|------|
| **START_HERE.md** *(이 파일)* | 빠른 시작 가이드 |
| **CAMERA_FIX_GUIDE.md** | 카메라 문제 해결 |
| **DISPLAY_FIX_GUIDE.md** | GUI/DISPLAY 문제 해결 |
| **TROUBLESHOOTING.md** | 전체 문제 해결 가이드 |
| **QUICKSTART.md** | YOLO 통합 시스템 가이드 |

---

## 🚀 실행 스크립트 목록

| 스크립트 | 용도 | 사용 시기 |
|---------|------|----------|
| **run_yolo_autoplot.sh** | GUI 모드 실행 | 모니터 연결 또는 VNC 사용 시 |
| **run_headless.sh** | 헤드리스 모드 | SSH 접속 시 (권장) |
| **diagnose_camera.sh** | 카메라 진단 | 카메라 문제 발생 시 |
| **test_camera.py** | 카메라 테스트 | 카메라 확인 필요 시 |

---

## 💡 추천 워크플로우

### 🔰 처음 사용하는 경우

```bash
# 1. 카메라 확인
cd 06_final_self_driving
./diagnose_camera.sh

# 2. 카메라 테스트
python3 test_camera.py

# 3. 헤드리스 모드로 첫 실행
./run_headless.sh

# 4. 정상 작동 확인 후 설정 조정
nano 1_yolo_final_autoplot.py
# (DEFAULT_SPEED_UP, RGB 가중치 등 조정)

# 5. 다시 실행
./run_headless.sh
```

### 🎯 개발 및 디버깅

```bash
# 1. VNC로 접속 (또는 모니터 직접 연결)

# 2. GUI 모드로 실행
cd 06_final_self_driving
python3 1_yolo_final_autoplot.py

# 3. 트랙바로 실시간 조정

# 4. 최적 설정 찾으면 코드에 반영
nano 1_yolo_final_autoplot.py
```

### 🚗 실제 자율주행

```bash
# 헤드리스 모드 + 최적화된 설정
cd 06_final_self_driving
./run_headless.sh
```

---

## ⚙️ 주요 설정 조정

실행 전 설정을 변경하려면 `1_yolo_final_autoplot.py` 파일 편집:

```python
# 기본 속도 설정
DEFAULT_SPEED_UP = 15      # 직진 속도 (높일수록 빠름)
DEFAULT_SPEED_DOWN = 8     # 회전 속도 (낮을수록 느림)

# RGB 가중치 (빛 반사 필터링)
DEFAULT_R_WEIGHT = 30      # 빨강 채널
DEFAULT_G_WEIGHT = 40      # 초록 채널
DEFAULT_B_WEIGHT = 60      # 파랑 채널

# 방향 판단 임계값
DEFAULT_DIRECTION_THRESHOLD = 35000   # 회전 시작 기준
DEFAULT_UP_THRESHOLD = 220000         # 막다른 골목 감지

# GUI 모드 (SSH 접속 시 False 권장)
ENABLE_GUI = True    # True: GUI 창 표시, False: 헤드리스
```

---

## 🎓 학습 리소스

### 시스템 구성 이해하기

```
1. YOLO11 (최우선)
   └─→ 신호등 감지 (빨강/초록/일반)
        └─→ 빨간불: 정지 (초록불 대기)
        └─→ 초록불: 재시작

2. Haar Cascade (차순위)
   └─→ 표지판 감지 (STOP/NO DRIVE)
        └─→ 표지판 발견: 정지
        └─→ 표지판 사라짐: 재시작

3. Line Tracing (기본)
   └─→ RGB 필터링 + 히스토그램 분석
        └─→ 방향 결정 (직진/좌회전/우회전)
```

### 알고리즘 이해

- **RGB 가중치 필터링**: 도로 빛 반사 제거
- **3등분 히스토그램**: 좌/중앙/우 영역 분석
- **상태 기반 제어**: 신호등/표지판/자율주행 우선순위

---

## 📞 도움이 필요하신가요?

### 1. 문서 확인
- 각 가이드 문서 참조 (위 목록)

### 2. 진단 실행
```bash
./diagnose_camera.sh > diagnostic_log.txt
python3 test_camera.py >> diagnostic_log.txt
```

### 3. 로그 수집
```bash
./run_headless.sh 2>&1 | tee execution_log.txt
```

---

## ✅ 시작 준비 완료!

이제 다음 명령어로 시작하세요:

```bash
cd ~/Raspbot-v2-self-driving-car/06_final_self_driving

# SSH 접속한 경우 (권장):
./run_headless.sh

# 모니터 연결한 경우:
./run_yolo_autoplot.sh
```

**Happy Self-Driving! 🚗💨**

