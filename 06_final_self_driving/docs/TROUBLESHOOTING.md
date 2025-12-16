# 🔧 문제 해결 가이드 (Troubleshooting Guide)

## 목차
1. [Qt 플랫폼 플러그인 에러](#qt-플랫폼-플러그인-에러)
2. [YOLO 모델 로드 실패](#yolo-모델-로드-실패)
3. [카메라 초기화 실패](#카메라-초기화-실패)
4. [네트워크 연결 문제](#네트워크-연결-문제)
5. [성능 최적화](#성능-최적화)

---

## Qt 플랫폼 플러그인 에러

### 증상
```
qt.qpa.plugin: Could not find the Qt platform plugin "wayland" in "/home/pi/.local/lib/python3.11/site-packages/cv2/qt/plugins"
```

### 해결 방법

#### ✅ 방법 1: 환경 변수 설정 (권장)
```bash
export QT_QPA_PLATFORM=xcb
python3 1_yolo_final_autoplot.py
```

또는 실행 스크립트 사용:
```bash
./run_yolo_autoplot.sh
```

#### ✅ 방법 2: Qt 라이브러리 설치
```bash
sudo apt-get update
sudo apt-get install -y libqt5gui5 libqt5test5 libqt5widgets5 python3-pyqt5
```

#### ✅ 방법 3: X11 포워딩 (SSH 접속 시)
```bash
# X11 포워딩으로 SSH 접속
ssh -X pi@raspberrypi.local

# DISPLAY 환경 변수 확인
echo $DISPLAY

# DISPLAY가 비어있으면 설정
export DISPLAY=:0
```

#### ✅ 방법 4: GTK 백엔드 사용
```bash
# GTK 라이브러리 설치
sudo apt-get install -y libgtk-3-dev

# OpenCV 재설치
pip3 uninstall opencv-python
pip3 install opencv-python
```

---

## YOLO 모델 로드 실패

### 증상
```
❌ Custom model not found: ./models/traffic_modeln.pt
```

### 해결 방법

#### ✅ 방법 1: 모델 파일 위치 확인
```bash
# 모델 디렉토리 확인
ls -la 06_final_self_driving/models/

# 모델 파일이 있는지 확인
ls -lh 06_final_self_driving/models/traffic_modeln.pt
```

#### ✅ 방법 2: 모델 파일 경로 수정
`1_yolo_final_autoplot.py` 파일에서 경로 확인:
```python
YOLO_MODEL_PATH = "./models/traffic_modeln.pt"  # 이 경로가 올바른지 확인
```

#### ✅ 방법 3: 모델 파일 복사
```bash
# 모델 파일을 올바른 위치에 복사
cp /path/to/your/model.pt 06_final_self_driving/models/traffic_modeln.pt
```

#### ✅ 방법 4: YOLO 없이 실행
YOLO 모델이 없어도 Haar Cascade로 표지판 감지 + 자율주행은 가능합니다.
```bash
# 모델 없이 실행 가능 (신호등 감지만 비활성화)
python3 1_yolo_final_autoplot.py
```

---

## 카메라 초기화 실패

### 증상
```
Cannot read frame from camera
Failed to initialize camera
```

### 해결 방법

#### ✅ 방법 1: 카메라 연결 확인
```bash
# 카메라 장치 확인
ls -la /dev/video*

# 카메라 테스트
v4l2-ctl --list-devices

# 간단한 카메라 테스트
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'FAIL')"
```

#### ✅ 방법 2: 카메라 권한 확인
```bash
# 현재 사용자를 video 그룹에 추가
sudo usermod -aG video $USER

# 재부팅 후 적용
sudo reboot
```

#### ✅ 방법 3: 다른 프로그램이 카메라 사용 중인지 확인
```bash
# 카메라 사용 중인 프로세스 확인
lsof /dev/video0

# 프로세스 종료 (PID 확인 후)
kill -9 <PID>
```

---

## 네트워크 연결 문제

### 증상
```
[Errno -3] Temporary failure in name resolution
pip install ultralytics 실패
```

### 해결 방법

#### ✅ 방법 1: WiFi 연결 확인
```bash
# 네트워크 연결 상태 확인
ping -c 3 8.8.8.8

# DNS 확인
ping -c 3 google.com

# WiFi 재시작
sudo systemctl restart dhcpcd
```

#### ✅ 방법 2: DNS 설정
```bash
# DNS 서버 추가 (Google DNS)
echo "nameserver 8.8.8.8" | sudo tee -a /etc/resolv.conf
echo "nameserver 8.8.4.4" | sudo tee -a /etc/resolv.conf
```

#### ✅ 방법 3: 오프라인 설치
```bash
# PC에서 다운로드 (인터넷 되는 컴퓨터)
pip download ultralytics -d ./ultralytics_packages

# Raspberry Pi로 전송
scp -r ./ultralytics_packages pi@raspberrypi.local:~/

# Raspberry Pi에서 설치
cd ~/ultralytics_packages
pip3 install --no-index --find-links . ultralytics
```

---

## 성능 최적화

### 느린 FPS 문제

#### ✅ 방법 1: 해상도 낮추기
코드에서 카메라 해상도를 낮춥니다:
```python
# initialize_camera 함수에서
cap = initialize_camera(width=320, height=240)  # 기본값
# 또는
cap = initialize_camera(width=160, height=120)  # 더 낮은 해상도
```

#### ✅ 방법 2: YOLO Confidence 조정
트랙바에서 `YOLO_Confidence`를 높이면 처리 속도 향상:
- 기본값: 50 (0.5)
- 빠른 처리: 70 (0.7)

#### ✅ 방법 3: 프레임 스킵
매 프레임마다 처리하지 않고 일부 프레임 스킵:
```python
# 메인 루프에서
if frame_count % 2 == 0:  # 2프레임마다 1번만 처리
    # YOLO 및 Haar Cascade 실행
```

#### ✅ 방법 4: Raspberry Pi 오버클럭
```bash
# /boot/config.txt 편집
sudo nano /boot/config.txt

# 아래 내용 추가 (Raspberry Pi 4/5)
over_voltage=6
arm_freq=2000

# 저장 후 재부팅
sudo reboot
```

---

## 기타 문제

### ImportError: No module named 'ultralytics'

```bash
# Ultralytics 설치
pip3 install ultralytics

# 또는
python3 -m pip install ultralytics
```

### ImportError: No module named 'Raspbot_Lib'

```bash
# 경로 확인
ls -la lib/raspbot/Raspbot_Lib.py

# 경로가 올바른지 확인
cd /Users/kimjongphil/Documents/GitHub/Raspbot-v2-self-driving-car
python3 06_final_self_driving/1_yolo_final_autoplot.py
```

### 서보 모터가 움직이지 않음

```bash
# 서보 모터 전원 확인
# 배터리 전압 확인 (최소 7.4V 필요)

# 서보 각도 범위 확인
# Servo 1: 0~180도
# Servo 2: 0~110도
```

### LED가 켜지지 않음

```bash
# LED 테스트 코드 실행
python3 02_Basic/02_RGB\ Light\ bar\ test.ipynb

# 또는 프로그램에서 'l' 키로 LED 토글
```

---

## 디버그 모드 활성화

문제 발생 시 자세한 로그를 보려면:

```python
# 1_yolo_final_autoplot.py에서
DEBUG_MODE = True  # 이미 기본값으로 설정됨
```

실행 시 자세한 로그가 출력됩니다.

---

## 문의 및 지원

문제가 해결되지 않으면:
1. 에러 메시지 전체 복사
2. 실행 환경 정보 (Raspberry Pi 모델, OS 버전)
3. 관련 로그 파일
4. 실행했던 명령어

위 정보와 함께 문의해주세요.

