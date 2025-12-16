# 🖥️ DISPLAY 문제 해결 가이드 (GUI Window Error Fix)

## 증상 (Symptoms)

프로그램이 다음 단계에서 멈춤:
```
==================================================
  STEP 4: Setting up Trackbars and Windows...
==================================================
```

**원인:** OpenCV가 GUI 창을 생성할 수 없음 (DISPLAY 환경 변수 문제 또는 디스플레이 서버 없음)

---

## 🚀 빠른 해결 방법

### ✅ 방법 1: 헤드리스 모드로 실행 (권장 - SSH 접속 시)

GUI 없이 실행 (가장 간단하고 안정적):

```bash
cd 06_final_self_driving
./run_headless.sh
```

**또는 직접 설정 변경:**

```python
# 1_yolo_final_autoplot.py 파일에서 (125번째 줄 근처)
# 변경 전:
ENABLE_GUI = True

# 변경 후:
ENABLE_GUI = False
```

그 후 실행:
```bash
python3 1_yolo_final_autoplot.py
```

**헤드리스 모드 특징:**
- ✅ GUI 창 없음 (OpenCV 윈도우 생성 안 함)
- ✅ 기본 설정값 사용 (트랙바 없음)
- ✅ 모터 제어 및 감지 기능 정상 작동
- ✅ SSH 접속에서 안정적으로 실행

---

### ✅ 방법 2: DISPLAY 환경 변수 설정

Raspberry Pi가 **모니터에 직접 연결**되어 있다면:

```bash
# DISPLAY 환경 변수 설정
export DISPLAY=:0

# 확인
echo $DISPLAY  # 출력: :0

# 실행
cd 06_final_self_driving
python3 1_yolo_final_autoplot.py
```

**영구 설정 (선택사항):**
```bash
# ~/.bashrc 파일에 추가
echo "export DISPLAY=:0" >> ~/.bashrc
source ~/.bashrc
```

---

### ✅ 방법 3: X11 포워딩으로 SSH 접속

**원격에서 GUI를 보고 싶다면** (SSH + X11 포워딩):

#### Mac/Linux에서:

```bash
# X11 포워딩으로 SSH 접속
ssh -X pi@raspberrypi.local
# 또는
ssh -Y pi@raspberrypi.local

# DISPLAY 확인
echo $DISPLAY  # 출력: localhost:10.0 같은 값이 나와야 함

# 실행
cd 06_final_self_driving
python3 1_yolo_final_autoplot.py
```

**Mac에서 XQuartz 필요:**
```bash
# XQuartz 설치 (한 번만)
brew install --cask xquartz

# XQuartz 실행 후 SSH 접속
open -a XQuartz
ssh -X pi@raspberrypi.local
```

#### Windows에서:

```bash
# 1. VcXsrv 또는 Xming 설치
# 2. X Server 실행
# 3. PuTTY 설정:
#    Connection → SSH → X11 → Enable X11 forwarding
# 4. 접속 후:
export DISPLAY=localhost:0.0
cd 06_final_self_driving
python3 1_yolo_final_autoplot.py
```

---

### ✅ 방법 4: VNC로 원격 데스크톱 접속 (가장 안정적)

VNC는 GUI를 완벽하게 지원하여 가장 안정적입니다:

#### Raspberry Pi에서 VNC 활성화:

```bash
# 1. VNC 서버 활성화
sudo raspi-config
# → 3. Interface Options
# → I3 VNC
# → Yes

# 2. VNC 해상도 설정 (헤드리스 모드용)
sudo raspi-config
# → 2. Display Options
# → D5 VNC Resolution
# → 1920x1080 선택

# 3. 재부팅
sudo reboot
```

#### VNC Viewer로 접속:

```
1. VNC Viewer 다운로드 및 설치
   - https://www.realvnc.com/download/viewer/

2. 접속 주소 입력:
   - raspberrypi.local:5900
   - 또는 IP 주소:5900

3. 로그인 (pi / 비밀번호)

4. Raspberry Pi 데스크톱에서 터미널 열기

5. 실행:
   cd 06_final_self_driving
   python3 1_yolo_final_autoplot.py
```

---

## 🔍 각 방법 비교

| 방법 | GUI 표시 | 설정 난이도 | 안정성 | 추천 상황 |
|------|----------|------------|--------|-----------|
| **헤드리스 모드** | ❌ 없음 | ⭐ 쉬움 | ⭐⭐⭐ 높음 | SSH 접속, GUI 불필요 |
| **DISPLAY=:0** | ✅ 모니터에만 | ⭐ 쉬움 | ⭐⭐⭐ 높음 | 모니터 직접 연결 |
| **X11 포워딩** | ✅ 원격 PC에 | ⭐⭐ 중간 | ⭐⭐ 중간 | 원격 GUI 필요, 느릴 수 있음 |
| **VNC** | ✅ 완벽한 원격 | ⭐⭐ 중간 | ⭐⭐⭐ 높음 | 원격 작업, 완전한 데스크톱 |

---

## 🛠️ 상세 해결 방법

### DISPLAY 환경 변수 확인

```bash
# 현재 DISPLAY 확인
echo $DISPLAY

# 비어있으면 설정 필요
# 출력 예시:
#   :0        → 로컬 모니터
#   localhost:10.0 → X11 포워딩
#   (empty)   → 설정 안 됨
```

### X11 설정 확인

```bash
# X11 포워딩이 활성화되었는지 확인
echo $SSH_CONNECTION  # SSH 접속인지 확인
echo $DISPLAY         # DISPLAY가 설정되었는지 확인

# X11 테스트
xclock  # 작은 시계 창이 나타나면 성공
```

### Qt 백엔드 확인

```bash
# Qt 플랫폼 플러그인 목록
ls ~/.local/lib/python3.11/site-packages/cv2/qt/plugins/

# Qt 라이브러리 설치
sudo apt-get update
sudo apt-get install -y libqt5gui5 libqt5widgets5 python3-pyqt5
```

---

## 📋 실행 모드별 가이드

### 1. **헤드리스 모드** (GUI 없음)

**장점:**
- ✅ 설정 불필요
- ✅ SSH에서 바로 실행 가능
- ✅ 안정적
- ✅ 리소스 절약

**단점:**
- ❌ 실시간 영상 확인 불가
- ❌ 트랙바로 설정 조정 불가

**사용법:**
```bash
cd 06_final_self_driving
./run_headless.sh
```

**설정 변경:**
```python
# 1_yolo_final_autoplot.py에서 파라미터 직접 수정
DEFAULT_SPEED_UP = 15
DEFAULT_SPEED_DOWN = 8
DEFAULT_R_WEIGHT = 30
DEFAULT_G_WEIGHT = 40
DEFAULT_B_WEIGHT = 60
# ... 등등
```

---

### 2. **GUI 모드** (창 표시)

**장점:**
- ✅ 실시간 영상 확인
- ✅ 트랙바로 즉시 조정
- ✅ 디버깅 편리

**단점:**
- ❌ DISPLAY 설정 필요
- ❌ 더 많은 리소스 사용

**사용법:**
```bash
# DISPLAY 설정 후
export DISPLAY=:0
cd 06_final_self_driving
python3 1_yolo_final_autoplot.py
```

---

## 🔧 고급 문제 해결

### SSH 설정 파일 수정 (X11 포워딩 활성화)

**Raspberry Pi에서:**
```bash
sudo nano /etc/ssh/sshd_config

# 아래 항목 확인 및 수정:
X11Forwarding yes
X11DisplayOffset 10
X11UseLocalhost yes

# SSH 재시작
sudo systemctl restart ssh
```

**클라이언트 PC에서 (Mac/Linux):**
```bash
nano ~/.ssh/config

# 추가:
Host raspberrypi
    HostName raspberrypi.local
    User pi
    ForwardX11 yes
    ForwardX11Trusted yes

# 접속:
ssh raspberrypi
```

### VNC 해상도 설정 (헤드리스 모드)

모니터 없이 VNC 사용 시:

```bash
sudo nano /boot/config.txt

# 아래 추가:
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=82  # 1920x1080 60Hz
# 또는
hdmi_mode=85  # 1280x720 60Hz

# 저장 후 재부팅
sudo reboot
```

---

## ✅ 해결 확인

### 헤드리스 모드 성공:

```
==================================================
  STEP 4: Setting up Trackbars and Windows...
==================================================
⚠️  GUI Mode: DISABLED (Headless mode)
   - No OpenCV windows will be created
   - Trackbars will use default values
   - Program will run in background mode
⚠️  Trackbars skipped (Headless mode)
   Using default values from configuration

==================================================
  STEP 5: Defining Image Processing Functions
==================================================
```

### GUI 모드 성공:

```
==================================================
  STEP 4: Setting up Trackbars and Windows...
==================================================
✅ GUI Mode: ENABLED
✅ GUI windows created successfully
Trackbars and windows configured successfully
⭐ YOLO Confidence/IOU trackbars added
...
```

---

## 💡 권장 사용 시나리오

### 🏠 **로컬 테스트 (모니터 직접 연결)**
```bash
export DISPLAY=:0
python3 1_yolo_final_autoplot.py
```
→ GUI로 실시간 조정 및 디버깅

### 🌐 **원격 SSH 접속**
```bash
./run_headless.sh
```
→ 헤드리스 모드로 안정적 실행

### 🖥️ **원격 개발 및 디버깅**
```
VNC 접속 → GUI 모드 실행
```
→ 완벽한 원격 제어

### 🚗 **실제 자율주행 (자동 실행)**
```bash
# 헤드리스 모드 + 자동 시작
./run_headless.sh
```
→ 부팅 시 자동 실행 설정 가능

---

## 📞 추가 도움말

### 로그 확인:

```bash
# 헤드리스 모드로 실행하면서 로그 저장
./run_headless.sh 2>&1 | tee autoplot_log.txt
```

### 디버그 출력만 확인:

```python
# 1_yolo_final_autoplot.py에서
DEBUG_MODE = True  # 기본값
ENABLE_GUI = False  # 헤드리스 모드
```

이제 SSH로 접속하여 안전하게 실행할 수 있습니다! 🚗💨

