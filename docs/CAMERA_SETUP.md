# 📷 Raspbot 카메라 설정 가이드

Raspberry Pi에서 카메라를 설정하는 방법입니다.

---

## 📋 지원하는 카메라

1. **Raspberry Pi Camera 모듈** (권장)
   - Pi Camera v1, v2, v3
   - HQ Camera
   - Picamera2 라이브러리 사용

2. **USB 카메라**
   - 일반 웹캠
   - OpenCV VideoCapture 사용

---

## 🎯 자동 감지 방식

`6_custom_autoplot.py`는 다음 순서로 카메라를 자동 감지합니다:

1. **Picamera2 시도** (Pi Camera 모듈)
2. **USB 카메라 시도** (cv2.VideoCapture)
3. 둘 다 실패 시 에러 메시지 출력

---

## 🔧 Raspberry Pi Camera 모듈 설정

### 1단계: 하드웨어 연결

1. Raspberry Pi 전원 끄기
2. 카메라 모듈을 CSI 포트에 연결
   - 파란색 면이 이더넷 포트 방향
   - 접촉면이 HDMI 포트 방향
3. 케이블이 단단히 고정되었는지 확인

### 2단계: 카메라 활성화

```bash
# 설정 도구 실행
sudo raspi-config

# Interface Options 선택
# → Camera 선택
# → Yes 선택하여 활성화
# → Finish 선택

# 재부팅
sudo reboot
```

### 3단계: 카메라 테스트

#### Raspberry Pi OS Bullseye 이상 (최신)

```bash
# 카메라 테스트 (5초간 미리보기)
libcamera-hello -t 5000

# 사진 촬영
libcamera-still -o test.jpg

# 카메라 정보 확인
libcamera-hello --list-cameras
```

**출력 예시**:
```
Available cameras
-----------------
0 : imx219 [3280x2464] (/base/soc/i2c0mux/i2c@1/imx219@10)
    Modes: 'SRGGB10_CSI2P' : 640x480 [206.65 fps - (1000, 752)/1280x960 crop]
```

#### Raspberry Pi OS Buster 이하 (구 버전)

```bash
# 카메라 테스트
raspistill -o test.jpg

# 동영상 녹화 (5초)
raspivid -o test.h264 -t 5000
```

### 4단계: Picamera2 설치 (필요 시)

```bash
# Python 패키지 업데이트
sudo apt update
sudo apt install -y python3-picamera2

# 또는 pip로 설치
pip3 install picamera2
```

### 5단계: 권한 설정

```bash
# video 그룹에 사용자 추가
sudo usermod -aG video $USER

# 재부팅
sudo reboot
```

---

## 🔌 USB 카메라 설정

### 1단계: 카메라 연결

1. USB 카메라를 Raspberry Pi의 USB 포트에 연결
2. 전원이 충분한지 확인 (필요시 전원 공급 USB 허브 사용)

### 2단계: 카메라 인식 확인

```bash
# 비디오 장치 목록 확인
ls -l /dev/video*

# 출력 예시:
# crw-rw---- 1 root video 81, 0 Nov 25 10:00 /dev/video0

# 상세 정보 확인
v4l2-ctl --list-devices

# USB 장치 확인
lsusb
```

### 3단계: 테스트

```bash
# fswebcam으로 사진 촬영
sudo apt install fswebcam
fswebcam -r 320x240 test.jpg

# 또는 Python으로 테스트
python3 << EOF
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if ret:
    cv2.imwrite('test.jpg', frame)
    print("Success!")
else:
    print("Failed!")
cap.release()
EOF
```

---

## 🐛 문제 해결

### 에러 1: "can't open camera by index"

**원인**: 카메라가 인식되지 않음

**해결 방법**:
```bash
# 1. 카메라 연결 확인
ls /dev/video*

# 2. 카메라 활성화 확인
sudo raspi-config
# Interface Options → Camera → Enable

# 3. 재부팅
sudo reboot

# 4. 다른 프로그램에서 카메라 사용 중인지 확인
sudo lsof | grep video

# 5. 카메라 모듈이 로드되었는지 확인
lsmod | grep bcm2835
```

### 에러 2: "Permission denied"

**원인**: 권한 부족

**해결 방법**:
```bash
# video 그룹에 추가
sudo usermod -aG video $USER

# 재부팅 (필수!)
sudo reboot
```

### 에러 3: Picamera2를 찾을 수 없음

**원인**: Picamera2가 설치되지 않음

**해결 방법**:
```bash
# 패키지 업데이트
sudo apt update
sudo apt upgrade

# Picamera2 설치
sudo apt install -y python3-picamera2

# 또는
pip3 install picamera2
```

### 에러 4: "Camera is being used by another application"

**원인**: 다른 프로그램이 카메라 사용 중

**해결 방법**:
```bash
# 카메라를 사용 중인 프로세스 찾기
sudo lsof | grep video

# 프로세스 종료
sudo kill -9 [PID]

# 또는 재부팅
sudo reboot
```

### 에러 5: 이미지가 뒤집혀 있음

**해결 방법**:

코드에서 수정:
```python
# Picamera2의 경우
camera_config["transform"] = libcamera.Transform(hflip=1, vflip=1)

# USB 카메라의 경우
frame = cv2.flip(frame, -1)  # 상하좌우 반전
frame = cv2.flip(frame, 0)   # 상하 반전
frame = cv2.flip(frame, 1)   # 좌우 반전
```

---

## 🎛️ 카메라 설정 최적화

### 해상도 변경

```python
# Picamera2
camera_config = picam2.create_preview_configuration(
    main={"format": 'RGB888', "size": (640, 480)}  # 원하는 해상도
)

# USB 카메라
cap.set(3, 640)  # 폭
cap.set(4, 480)  # 높이
```

### 프레임레이트 설정

```python
# USB 카메라
cap.set(cv2.CAP_PROP_FPS, 30)
```

### 밝기/대비 설정

```python
# USB 카메라
cap.set(cv2.CAP_PROP_BRIGHTNESS, 50)
cap.set(cv2.CAP_PROP_CONTRAST, 50)
cap.set(cv2.CAP_PROP_SATURATION, 50)
```

---

## 📊 카메라 비교

| 항목 | Pi Camera 모듈 | USB 카메라 |
|------|---------------|-----------|
| **장점** | - 빠른 속도<br>- 낮은 CPU 사용률<br>- Raspberry Pi 최적화 | - 범용성<br>- 교체 쉬움<br>- 다양한 선택 |
| **단점** | - 전용 케이블 필요<br>- 고정된 위치 | - 높은 CPU 사용률<br>- USB 포트 필요 |
| **권장 용도** | 자율주행, 실시간 처리 | 간단한 테스트, 개발 |
| **해상도** | 최대 8MP (v2) | 카메라마다 다름 |
| **FPS** | 30fps 이상 | 보통 30fps |

---

## 🔍 카메라 성능 테스트

다음 스크립트로 카메라 성능을 테스트하세요:

```python
import cv2
import time

# Picamera2 테스트
try:
    from picamera2 import Picamera2
    picam2 = Picamera2()
    picam2.start()
    
    start = time.time()
    for _ in range(100):
        frame = picam2.capture_array()
    elapsed = time.time() - start
    fps = 100 / elapsed
    print(f"Picamera2 FPS: {fps:.1f}")
    picam2.stop()
except:
    print("Picamera2 not available")

# USB 카메라 테스트
try:
    cap = cv2.VideoCapture(0)
    cap.set(3, 320)
    cap.set(4, 240)
    
    start = time.time()
    for _ in range(100):
        ret, frame = cap.read()
    elapsed = time.time() - start
    fps = 100 / elapsed
    print(f"USB Camera FPS: {fps:.1f}")
    cap.release()
except:
    print("USB Camera not available")
```

---

## 💡 추가 팁

### 1. 카메라 품질 향상

```bash
# GPU 메모리 증가 (카메라 성능 향상)
sudo nano /boot/config.txt

# 다음 줄 추가 또는 수정:
gpu_mem=256

# 저장 후 재부팅
sudo reboot
```

### 2. 저조도 환경

- 밝기 증가: `cap.set(cv2.CAP_PROP_BRIGHTNESS, 80)`
- 게인 증가: `cap.set(cv2.CAP_PROP_GAIN, 50)`
- IR 카메라 사용 고려

### 3. 고속 촬영

- 해상도 낮추기 (320x240)
- 프레임 처리 최적화
- GPU 가속 활용

---

## 📚 참고 자료

- [Raspberry Pi Camera 공식 문서](https://www.raspberrypi.com/documentation/accessories/camera.html)
- [Picamera2 문서](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf)
- [OpenCV VideoCapture](https://docs.opencv.org/master/d8/dfe/classcv_1_1VideoCapture.html)

---

**업데이트**: 2025-11-25

