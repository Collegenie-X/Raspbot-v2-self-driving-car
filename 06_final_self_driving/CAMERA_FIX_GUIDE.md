# 🎥 카메라 문제 해결 가이드 (Camera Fix Guide)

## 증상 (Symptoms)

```
[ WARN:0@0.071] global cap_v4l.cpp:999 open VIDEOIO(V4L2:/dev/video0): can't open camera by index
[ERROR:0@0.074] global obsensor_uvc_stream_channel.cpp:158 getStreamChannelGroup Camera index out of range
Failed to initialize camera: Cannot read frame from camera
```

---

## 🚀 빠른 해결 방법 (Quick Fix)

### 단계 1: 자동 진단 실행

```bash
cd 06_final_self_driving
./diagnose_camera.sh
```

이 스크립트가 자동으로:
- 카메라 장치 확인
- 사용 중인 프로세스 확인
- 권한 확인
- Python으로 카메라 테스트

### 단계 2: 카메라 테스트

```bash
cd 06_final_self_driving
python3 test_camera.py
```

이 스크립트가:
- 여러 카메라 인덱스 (0, 1, 2, -1) 자동 시도
- 작동하는 카메라 찾기
- 테스트 이미지 저장
- 권장 설정 출력

---

## 🔍 상세 해결 방법 (Detailed Solutions)

### 해결법 1: 카메라 장치 확인

```bash
# 카메라 장치가 인식되었는지 확인
ls -la /dev/video*
```

**예상 결과:**
```
crw-rw----+ 1 root video 81, 0 Dec 16 10:30 /dev/video0
crw-rw----+ 1 root video 81, 1 Dec 16 10:30 /dev/video1
```

**만약 아무것도 안 나오면:**
- 카메라 USB 케이블 재연결
- Raspberry Pi 재부팅: `sudo reboot`
- 다른 USB 포트 시도

---

### 해결법 2: 권한 문제 해결

```bash
# 현재 사용자를 video 그룹에 추가
sudo usermod -aG video $USER

# 그룹 확인
groups

# video 그룹이 보이지 않으면 재로그인 필요
# 또는 재부팅
sudo reboot
```

**확인 방법:**
```bash
# 다시 로그인 후
groups
# 출력에 'video'가 포함되어야 함
```

---

### 해결법 3: 다른 프로그램이 카메라 사용 중

```bash
# 카메라를 사용하는 프로세스 확인
sudo lsof /dev/video0
```

**만약 프로세스가 있다면:**
```bash
# PID 확인 후 종료
sudo kill -9 <PID>

# 예시:
# COMMAND   PID USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
# python3  1234 pi      3u   CHR   81,0      0t0  456 /dev/video0
sudo kill -9 1234
```

---

### 해결법 4: 카메라 인덱스 변경

카메라가 `/dev/video0`이 아닐 수 있습니다.

#### 자동 감지 (권장)

최신 버전의 `1_yolo_final_autoplot.py`는 **자동으로 카메라를 찾습니다**.

```bash
# 그냥 실행하면 자동으로 카메라 검색
python3 1_yolo_final_autoplot.py
```

출력:
```
Initializing camera...
   - Searching for available camera...
   - Found camera at index: 0
✅ USB camera initialized successfully
```

#### 수동 설정

만약 특정 카메라를 사용하려면:

```python
# 1_yolo_final_autoplot.py 파일에서 (265번째 줄 근처)
# 변경 전:
cap = initialize_camera()

# 변경 후 (카메라 인덱스 지정):
cap = initialize_camera(camera_index=0)  # 또는 1, 2
```

---

### 해결법 5: V4L2 드라이버 확인

```bash
# V4L2 유틸리티 설치
sudo apt-get update
sudo apt-get install -y v4l-utils

# 카메라 정보 확인
v4l2-ctl --list-devices

# 카메라 지원 형식 확인
v4l2-ctl --device=/dev/video0 --list-formats-ext
```

---

### 해결법 6: Raspberry Pi Camera Module 사용 시

**CSI 카메라 (리본 케이블 연결)를 사용하는 경우:**

```bash
# 카메라 인터페이스 활성화
sudo raspi-config
# → 3. Interface Options
# → P1 Camera
# → Enable

# 재부팅
sudo reboot

# legacy 카메라 드라이버 활성화
sudo raspi-config
# → 3. Interface Options
# → I1 Legacy Camera
# → Enable

sudo reboot
```

**또는 libcamera 사용:**

```bash
# libcamera 테스트
libcamera-hello

# OpenCV가 libcamera를 사용하도록 설정
# /boot/config.txt 편집
sudo nano /boot/config.txt

# 아래 추가:
camera_auto_detect=1
dtoverlay=vc4-kms-v3d

sudo reboot
```

---

### 해결법 7: USB 카메라 드라이버 재설치

```bash
# USB Video Class 드라이버 다시 로드
sudo modprobe -r uvcvideo
sudo modprobe uvcvideo

# 확인
lsmod | grep uvcvideo
```

---

## 🧪 테스트 도구 사용법

### 1. `test_camera.py` - 카메라 기본 테스트

```bash
cd 06_final_self_driving
python3 test_camera.py
```

**출력 예시:**
```
============================================================
  Camera Connection Test
============================================================

[Test 0] Trying camera index: 0
✅ SUCCESS! Camera 0 is working
   - Resolution: 640x480
   - Frame shape: (480, 640, 3)
   - Test image saved: test_camera_0.jpg

============================================================
  Test Summary
============================================================
✅ Found 1 working camera(s): [0]

💡 Recommended: Use camera index 0

📝 Update 1_yolo_final_autoplot.py:
   cap = cv2.VideoCapture(0)
============================================================
```

### 2. `diagnose_camera.sh` - 전체 진단

```bash
cd 06_final_self_driving
./diagnose_camera.sh
```

이 스크립트는:
- ✅ 모든 카메라 장치 확인
- ✅ V4L2 정보 확인
- ✅ USB 장치 확인
- ✅ 프로세스 사용 여부 확인
- ✅ 권한 확인
- ✅ Python 테스트 자동 실행

---

## 📋 체크리스트

카메라가 작동하지 않을 때 순서대로 확인:

- [ ] 1. 카메라 물리적 연결 확인 (`ls -la /dev/video*`)
- [ ] 2. 권한 확인 (`groups | grep video`)
- [ ] 3. 다른 프로세스 사용 여부 (`sudo lsof /dev/video0`)
- [ ] 4. 자동 진단 실행 (`./diagnose_camera.sh`)
- [ ] 5. 카메라 테스트 실행 (`python3 test_camera.py`)
- [ ] 6. 권한 추가 및 재부팅 (`sudo usermod -aG video $USER && sudo reboot`)
- [ ] 7. USB 포트 변경 시도
- [ ] 8. 다른 카메라로 테스트
- [ ] 9. Raspberry Pi 전원 재부팅

---

## 🔧 고급 문제 해결

### 카메라가 간헐적으로 작동

```bash
# USB 전력 관리 비활성화
sudo nano /etc/udev/rules.d/99-usb-no-power-management.rules

# 아래 추가:
ACTION=="add", SUBSYSTEM=="usb", DRIVER=="usb", ATTR{power/control}="on"

sudo udevadm control --reload-rules
sudo reboot
```

### 해상도 문제

```bash
# 카메라가 지원하는 해상도 확인
v4l2-ctl --device=/dev/video0 --list-formats-ext

# 지원되는 해상도로 변경
# 1_yolo_final_autoplot.py에서:
cap = initialize_camera(width=640, height=480)  # 지원되는 해상도 사용
```

### OpenCV 재설치

```bash
# 기존 OpenCV 제거
pip3 uninstall opencv-python opencv-contrib-python

# 재설치
pip3 install opencv-python

# 또는 전체 버전
pip3 install opencv-contrib-python
```

---

## 💡 최종 확인

모든 해결 방법을 시도한 후:

```bash
# 1. 최신 코드 실행
cd 06_final_self_driving
python3 1_yolo_final_autoplot.py

# 2. 성공 메시지 확인
# ✅ USB camera initialized successfully
#    - Camera index: 0
#    - Requested resolution: 320x240
#    - Actual resolution: 320x240
```

---

## 📞 추가 지원

여전히 문제가 해결되지 않으면:

1. **진단 결과 수집:**
   ```bash
   ./diagnose_camera.sh > camera_diagnostic_log.txt
   python3 test_camera.py >> camera_diagnostic_log.txt
   ```

2. **시스템 정보 수집:**
   ```bash
   uname -a > system_info.txt
   cat /proc/device-tree/model >> system_info.txt
   vcgencmd version >> system_info.txt
   ```

3. **로그 파일과 함께 문의**

---

## ✅ 성공 확인

카메라가 정상 작동하면 다음과 같이 표시됩니다:

```
==================================================
  STEP 3: Initializing Hardware...
==================================================
Raspbot hardware initialized successfully

Initializing camera...
   - Searching for available camera...
   - Found camera at index: 0
✅ USB camera initialized successfully
   - Camera index: 0
   - Requested resolution: 320x240
   - Actual resolution: 320x240
```

이제 YOLO + Haar Cascade 자율주행 시스템을 사용할 수 있습니다! 🚗💨

