# 🚗 Raspbot v2 - 자율주행 로봇 카

Raspberry Pi 기반의 자율주행 로봇 카 프로젝트입니다. OpenCV를 활용한 라인 트래킹, 표지판 인식, 장애물 회피 기능을 제공합니다.

![Raspbot](https://img.shields.io/badge/Raspberry%20Pi-A22846?style=for-the-badge&logo=Raspberry%20Pi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)

---

## 📋 목차

- [주요 기능](#-주요-기능)
- [빠른 시작](#-빠른-시작)
- [프로젝트 구조](#-프로젝트-구조)
- [문서](#-문서)
- [주요 파일](#-주요-파일)
- [하드웨어 요구사항](#️-하드웨어-요구사항)
- [설치 방법](#-설치-방법)
- [사용 예제](#-사용-예제)
- [기여하기](#-기여하기)
- [라이선스](#-라이선스)

---

## ✨ 주요 기능

### 🚦 자율주행
- **라인 트래킹**: 흰색/검은색 라인 추적
- **실시간 파라미터 조절**: OpenCV 트랙바를 통한 실시간 튜닝
- **적응형 주행**: 막다른 길 감지 및 경로 탐색

### 🛑 표지판 인식
- **Haar Cascade 기반 객체 인식**
- 진입금지, 정지, 장애물 표지판 인식
- 멀티스레딩을 통한 실시간 처리

### 🎮 하드웨어 제어
- **모터 제어**: I2C 통신 기반 4륜 독립 제어
- **서보 모터**: 카메라 각도 조절 (상하좌우)
- **LED 효과**: 14개 RGB LED 제어 및 특수 효과
- **센서**: 초음파, 적외선, 라인 트래킹 센서

### 🌐 네트워크 기능
- **웹 서버**: 실시간 카메라 스트리밍
- **UDP 디스커버리**: 네트워크에서 자동 검색

---

## 🚀 빠른 시작

### 1. 기본 자율주행 실행

```bash
cd ~/project_demo/03_self_driving
python3 6_custom_autoplot.py
```

### 2. 표지판 인식 자율주행

```bash
cd ~/project_demo/03_self_driving
python3 5_autoplot_harr_cascade_thread.py
```

### 3. 자동 실행 설정

```bash
cd ~/project_demo/lib/raspbot
chmod +x install_autostart.sh
./install_autostart.sh
```

**더 자세한 내용은 [문서](#-문서)를 참고하세요!**

---

## 📂 프로젝트 구조

```
Raspbot-v2-self-driving-car/
├── 📁 01_Movies/                    # 시연 동영상
├── 📁 02_Basic/                     # 기본 하드웨어 테스트
├── 📁 03_self_driving/              # ⭐ 자율주행 메인 코드
│   ├── 2_autoplot___test.py        # 기본 자율주행
│   ├── 5_autoplot_harr_cascade_thread.py  # 표지판 인식
│   └── 6_custom_autoplot.py        # 개선된 버전 (추천!)
├── 📁 04_cascade/                   # Haar Cascade 객체 인식
├── 📁 05_final_self_driving/        # 최종 통합 버전 (개발 중)
├── 📁 lib/raspbot/                  # ⭐ 핵심 라이브러리
│   ├── Raspbot_Lib.py              # 하드웨어 제어 라이브러리
│   ├── yb-discover.py              # UDP 디스커버리 서버
│   ├── raspbot.pyc                 # 메인 웹 서버
│   ├── install_autostart.sh        # 자동 실행 설치 스크립트
│   ├── raspbot_start_improved.sh   # 시작 스크립트
│   ├── raspbot_stop.sh             # 중지 스크립트
│   └── raspbot_status.sh           # 상태 확인 스크립트
├── 📁 opencv/                       # OpenCV 예제 및 고급 기능
└── 📁 docs/                         # ⭐ 프로젝트 문서
    ├── QUICK_START.md              # 빠른 시작 가이드
    ├── SOURCE_CODE_GUIDE.md        # 소스 코드 상세 가이드
    └── AUTOSTART_GUIDE.md          # 자동 실행 설정 가이드
```

---

## 📚 문서

완전한 문서는 [`docs/`](./docs/) 폴더에 있습니다.

### 📖 주요 문서

| 문서 | 설명 | 대상 |
|------|------|------|
| **[QUICK_START.md](./docs/QUICK_START.md)** | 5분 안에 시작하기, 빠른 수정 예제 | 초보자 |
| **[SOURCE_CODE_GUIDE.md](./docs/SOURCE_CODE_GUIDE.md)** | 전체 코드 구조, 상세 수정 가이드 | 개발자 |
| **[CAMERA_SETUP.md](./docs/CAMERA_SETUP.md)** | Pi Camera & USB 카메라 설정 및 문제 해결 | 모든 사용자 |
| **[MIGRATION_GUIDE.md](./docs/MIGRATION_GUIDE.md)** | YB_Pcb_Car → Raspbot_Lib 전환 가이드 | 기존 사용자 |
| **[AUTOSTART_GUIDE.md](./docs/AUTOSTART_GUIDE.md)** | 부팅 시 자동 실행 설정 | 배포자 |

### 📖 [docs/README.md](./docs/README.md)
문서 구조와 읽는 순서에 대한 상세 가이드

---

## 🎯 주요 파일

### 자율주행 코드

- **`03_self_driving/6_custom_autoplot.py`** ⭐ (추천!)
  - 개선된 자율주행 알고리즘
  - 쉬운 파라미터 설정
  - 상세한 디버그 정보
  
- **`03_self_driving/2_autoplot___test.py`**
  - 기본 라인 트래킹
  - 실시간 트랙바 조절
  
- **`03_self_driving/5_autoplot_harr_cascade_thread.py`**
  - 표지판 인식 통합
  - 멀티스레드 처리

### 라이브러리

- **`lib/raspbot/Raspbot_Lib.py`**
  - 전체 하드웨어 제어
  - LED 특수 효과
  
- **`04_cascade/YB_Pcb_Car.py`**
  - 기본 차량 제어
  - I2C 통신

### 유틸리티

- **`lib/raspbot/install_autostart.sh`**
  - 원클릭 자동 실행 설치
  
- **`lib/raspbot/raspbot_status.sh`**
  - 서비스 상태 확인

---

## 🛠️ 하드웨어 요구사항

### 필수 구성품
- Raspberry Pi 3/4
- Raspbot 차량 키트 (Yahboom)
- Pi Camera Module
- 배터리

### 센서 및 액추에이터
- DC 모터 x4
- 서보 모터 x2
- RGB LED x14
- 초음파 센서
- 라인 트래킹 센서
- 적외선 리모컨 수신기
- 부저

---

## 💾 설치 방법

### 1. Raspberry Pi 설정

```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# I2C 활성화
sudo raspi-config
# Interface Options → I2C → Enable

# 카메라 활성화
sudo raspi-config
# Interface Options → Camera → Enable
```

### 2. 필수 패키지 설치

```bash
# OpenCV 및 의존성
pip3 install opencv-python opencv-contrib-python
pip3 install numpy

# I2C 라이브러리
pip3 install smbus2

# GPIO 라이브러리
pip3 install RPi.GPIO
```

### 3. 프로젝트 클론

```bash
git clone https://github.com/YOUR_USERNAME/Raspbot-v2-self-driving-car.git
cd Raspbot-v2-self-driving-car
```

### 4. 권한 설정

```bash
chmod +x lib/raspbot/*.sh
chmod +x 03_self_driving/*.py
```

---

## 🎮 사용 예제

### 기본 자율주행

```bash
cd 03_self_driving
python3 6_custom_autoplot.py
```

**조작법**:
- `ESC`: 종료
- `SPACE`: 일시정지/디버그

### 하드웨어 직접 제어

```python
import sys
sys.path.append('/home/pi/project_demo/04_cascade')
from YB_Pcb_Car import YB_Pcb_Car
import time

car = YB_Pcb_Car()

# 전진
car.Car_Run(80, 80)
time.sleep(2)

# 우회전
car.Car_Right(80, 50)
time.sleep(1)

# 정지
car.Car_Stop()
```

### LED 제어

```python
import sys
sys.path.append('/home/pi/project_demo/lib/raspbot')
from Raspbot_Lib import Raspbot

car = Raspbot()

# 모든 LED를 빨간색으로
car.Ctrl_WQ2812_ALL(1, 0)

# LED 특수 효과
from Raspbot_Lib import LightShow
light = LightShow()
light.execute_effect('river', 10, 0.1)  # 10초간 흐르는 효과
```

---

## 🎓 학습 자료

### OpenCV 튜토리얼
- [엣지 검출](https://docs.opencv.org/master/da/d22/tutorial_py_canny.html)
- [이미지 변환](https://docs.opencv.org/master/da/d6e/tutorial_py_geometric_transformations.html)

### Raspberry Pi
- [공식 문서](https://www.raspberrypi.org/documentation/)
- [GPIO 가이드](https://www.raspberrypi.org/documentation/usage/gpio/)

---

## 🐛 문제 해결

### 카메라가 작동하지 않음

```bash
# 최신 OS: Picamera2
libcamera-hello -t 5000

# 구 버전 OS
raspistill -o test.jpg

# 카메라 모듈 확인
vcgencmd get_camera

# USB 카메라 확인
ls /dev/video*
```

**자세한 해결 방법**: [docs/CAMERA_SETUP.md](./docs/CAMERA_SETUP.md)

### I2C 에러

```bash
# I2C 장치 확인
sudo i2cdetect -y 1

# I2C 권한 확인
sudo usermod -aG i2c pi
```

### 더 많은 문제 해결 방법
[QUICK_START.md - 문제 해결](./docs/QUICK_START.md#-문제-해결) 섹션을 참고하세요.

---

## 🤝 기여하기

기여를 환영합니다! 다음 방법으로 기여할 수 있습니다:

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

---

## 📧 연락처

프로젝트 링크: [https://github.com/YOUR_USERNAME/Raspbot-v2-self-driving-car](https://github.com/YOUR_USERNAME/Raspbot-v2-self-driving-car)

---

## 🙏 감사의 말

- [Yahboom](https://www.yahboom.com/) - Raspbot 하드웨어 키트
- [OpenCV](https://opencv.org/) - 컴퓨터 비전 라이브러리
- [Raspberry Pi Foundation](https://www.raspberrypi.org/) - Raspberry Pi

---

## 📊 프로젝트 현황

- ✅ 기본 라인 트래킹
- ✅ 표지판 인식
- ✅ 웹 스트리밍
- ✅ 자동 실행 설정
- 🔄 머신러닝 통합 (진행 중)
- 🔄 완전 자율주행 (진행 중)

---

**Happy Coding! 🚗💨**

