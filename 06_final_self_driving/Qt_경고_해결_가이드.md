# 🔧 Qt 플랫폼 플러그인 경고 해결 가이드

> Raspberry Pi에서 OpenCV GUI 사용 시 발생하는 Qt 경고 해결 방법

## ⚠️ 문제 증상

```
qt.qpa.plugin: Could not find the Qt platform plugin "wayland" in "/home/pi/.local/lib/python3.11/site-packages/cv2/qt/plugins"
```

또는

```
qt.qpa.plugin: Could not load the Qt platform plugin "xcb"
```

---

## 🔍 원인

OpenCV가 GUI 창을 표시하기 위해 Qt 백엔드를 사용하는데, Raspberry Pi의 디스플레이 환경 설정과 충돌이 발생합니다.

**주요 원인:**
1. Wayland 디스플레이 서버 사용 중이지만 Qt는 X11 기대
2. X11 사용 중이지만 필요한 라이브러리 미설치
3. SSH 원격 접속으로 디스플레이가 없는 환경

---

## ✅ 해결 방법

### 방법 1: 환경 변수 설정 (가장 간단, 권장)

#### 1-A. 스크립트에 직접 추가 (이미 적용됨)

`test_yolo_basic.py` 파일 상단에 이미 추가되어 있습니다:

```python
import os
os.environ["QT_QPA_PLATFORM"] = "xcb"  # X11 사용
```

#### 1-B. 터미널에서 실행 시 환경 변수 지정

```bash
# X11 사용 (GUI 있는 환경)
export QT_QPA_PLATFORM=xcb
python3 test_yolo_basic.py

# 또는 한 줄로
QT_QPA_PLATFORM=xcb python3 test_yolo_basic.py
```

#### 1-C. SSH 원격 접속 또는 GUI 없는 환경

```bash
# Offscreen 렌더링 (창 표시 안 함)
export QT_QPA_PLATFORM=offscreen
python3 test_yolo_basic.py

# 또는 한 줄로
QT_QPA_PLATFORM=offscreen python3 test_yolo_basic.py
```

---

### 방법 2: 필요한 Qt 라이브러리 설치

```bash
# X11 관련 라이브러리 설치
sudo apt-get update
sudo apt-get install -y libxcb-xinerama0 libxcb-cursor0 libxkbcommon-x11-0

# Qt 플랫폼 플러그인 설치
sudo apt-get install -y qt5-qmake qtbase5-dev

# OpenCV 재설치 (필요시)
pip3 uninstall opencv-python opencv-contrib-python
pip3 install opencv-python
```

---

### 방법 3: OpenCV 백엔드 변경

#### 3-A. GTK 백엔드로 변경

```bash
# GTK 라이브러리 설치
sudo apt-get install -y libgtk-3-0

# OpenCV headless 대신 full 버전 설치
pip3 uninstall opencv-python-headless
pip3 install opencv-python
```

#### 3-B. 스크립트에서 백엔드 지정

```python
import cv2
import os

# OpenCV가 GTK 사용하도록 설정
os.environ["OPENCV_VIDEOIO_PRIORITY_V4L2"] = "0"
```

---

### 방법 4: GUI 없는 모드로 실행 (SSH 환경)

카메라 테스트를 GUI 없이 실행하는 버전:

```python
# test_yolo_basic_no_gui.py
import cv2
import numpy as np
from ultralytics import YOLO

model = YOLO("./models/yolo11n.pt")
cap = cv2.VideoCapture(0)

frame_count = 0
detection_count = 0

print("카메라 테스트 시작 (GUI 없음, Ctrl+C로 종료)")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        if frame_count % 10 == 0:
            results = model(frame, conf=0.5, verbose=False)
            num_detections = len(results[0].boxes)
            
            if num_detections > 0:
                detection_count += num_detections
                print(f"프레임 {frame_count}: {num_detections}개 객체 감지")
                
                for box in results[0].boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    class_name = model.names[class_id]
                    print(f"  - {class_name} (신뢰도: {confidence:.2f})")
        
        # 프레임 저장 (선택)
        if frame_count % 100 == 0:
            cv2.imwrite(f"frame_{frame_count}.jpg", frame)
            print(f"📸 프레임 저장: frame_{frame_count}.jpg")

except KeyboardInterrupt:
    print("\n테스트 종료")

finally:
    cap.release()
    print(f"총 프레임: {frame_count}, 총 감지: {detection_count}")
```

---

## 🎯 환경별 권장 방법

| 환경 | 권장 방법 | 명령어 |
|:---|:---|:---|
| **Raspberry Pi + 모니터 연결** | 방법 1-B (xcb) | `QT_QPA_PLATFORM=xcb python3 test_yolo_basic.py` |
| **SSH 원격 접속** | 방법 1-C (offscreen) 또는 방법 4 (GUI 없음) | `QT_QPA_PLATFORM=offscreen python3 test_yolo_basic.py` |
| **VNC 연결** | 방법 1-B (xcb) | `QT_QPA_PLATFORM=xcb python3 test_yolo_basic.py` |
| **Wayland 사용 중** | 방법 2 (라이브러리 설치) | 상세 명령어는 위 참조 |

---

## 📋 체크리스트

문제 해결 시도 순서:

- [ ] 1. 스크립트 재실행 (이미 환경 변수 적용됨)
  ```bash
  python3 test_yolo_basic.py
  ```

- [ ] 2. 환경 변수 명시적 설정
  ```bash
  QT_QPA_PLATFORM=xcb python3 test_yolo_basic.py
  ```

- [ ] 3. GUI 없는 환경이면 offscreen 사용
  ```bash
  QT_QPA_PLATFORM=offscreen python3 test_yolo_basic.py
  ```

- [ ] 4. Qt 라이브러리 설치
  ```bash
  sudo apt-get install -y libxcb-xinerama0
  ```

- [ ] 5. GUI 없는 버전으로 테스트
  ```bash
  # 위의 "방법 4" 코드 사용
  ```

---

## 🔍 디버깅 명령어

### 현재 디스플레이 환경 확인

```bash
# 현재 사용 중인 디스플레이 서버 확인
echo $XDG_SESSION_TYPE
# 출력: x11 또는 wayland

# DISPLAY 환경 변수 확인
echo $DISPLAY
# 출력: :0 또는 비어있음 (SSH)

# Qt 플랫폼 확인
echo $QT_QPA_PLATFORM
# 출력: 설정된 값 또는 비어있음
```

### OpenCV 백엔드 확인

```python
import cv2
print("OpenCV 백엔드:")
print(cv2.getBuildInformation())
```

### 카메라 장치 확인

```bash
# 사용 가능한 카메라 확인
ls -la /dev/video*

# 카메라 정보
v4l2-ctl --list-devices
```

---

## 💡 추가 팁

### 1. 경고 무시하고 계속 실행

경고 메시지가 나와도 실제로는 정상 동작할 수 있습니다. 창이 정상적으로 표시되는지 확인하세요.

### 2. 환구 변수 영구 설정

매번 설정하기 번거로우면 `.bashrc`에 추가:

```bash
echo 'export QT_QPA_PLATFORM=xcb' >> ~/.bashrc
source ~/.bashrc
```

### 3. systemd 서비스 실행 시

`/etc/systemd/system/yolo_autoplot.service` 파일에 환경 변수 추가:

```ini
[Service]
Environment="QT_QPA_PLATFORM=xcb"
ExecStart=/usr/bin/python3 /home/pi/1_yolo_final_autoplot.py
```

---

## ✅ 해결 확인

다음 중 하나가 성공하면 문제 해결:

1. ✅ 경고 메시지 없이 프로그램 실행
2. ✅ 경고는 있지만 카메라 창 정상 표시
3. ✅ (GUI 없는 환경) 콘솔에 감지 결과 정상 출력

---

**문서 버전**: v1.0  
**최종 수정**: 2025-12-16  
**작성자**: Raspbot v2 개발팀

