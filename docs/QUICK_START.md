# 🚀 Raspbot 빠른 시작 가이드

## 📖 문서 목록

- **[SOURCE_CODE_GUIDE.md](./SOURCE_CODE_GUIDE.md)** - 📚 전체 소스 코드 구조 및 상세 가이드
- **[AUTOSTART_GUIDE.md](./AUTOSTART_GUIDE.md)** - ⚙️ 자동 실행 설정 가이드
- **QUICK_START.md** (이 문서) - 🎯 빠른 시작 가이드
- **[docs/README.md](./README.md)** - 📋 문서 구조 및 가이드

---

## ⚡ 5분 안에 시작하기

### 1️⃣ 기본 자율주행 실행

```bash
# Raspberry Pi에서 실행
cd ~/project_demo/03_self_driving
python3 2_autoplot___test.py
```

**조작법**:
- `ESC`: 종료
- `SPACE`: 일시정지
- 트랙바로 실시간 파라미터 조절 가능!

---

### 2️⃣ 개선된 자율주행 실행 (추천!)

```bash
cd ~/project_demo/03_self_driving
python3 6_custom_autoplot.py
```

**특징**:
- ✨ 더 빠른 속도
- 🎯 향상된 라인 검출
- 💬 자세한 디버그 정보
- 📊 FPS 표시

---

### 3️⃣ 표지판 인식 자율주행

```bash
cd ~/project_demo/03_self_driving
python3 5_autoplot_harr_cascade_thread.py
```

**인식 가능한 표지판**:
- 🚫 진입금지
- 🛑 정지 신호
- ⚠️ 장애물

---

## 🛠️ 코드 수정하는 방법

### 방법 1: 기본값 변경 (가장 쉬움!)

`6_custom_autoplot.py` 파일을 열고 **"사용자 설정 영역"**을 수정하세요:

```python
# ============================
# 사용자 설정 영역 (여기를 수정하세요!)
# ============================

# 기본 속도 설정
DEFAULT_SPEED_UP = 120        # 더 빠르게!
DEFAULT_SPEED_DOWN = 60       # 회전 속도도 증가

# 라인 검출 설정
DEFAULT_DETECT_VALUE = 40     # 민감도 증가

# 디버그 모드
DEBUG_MODE = False            # 상세 로그 끄기
```

**수정 후 바로 실행**:
```bash
python3 6_custom_autoplot.py
```

---

### 방법 2: 실시간 조절

프로그램 실행 중 **트랙바로 실시간 조절** 가능:

- `Motor Up Speed`: 직진 속도
- `Motor Down Speed`: 회전 속도
- `Detect Value`: 라인 검출 민감도
- `Direction Threshold`: 방향 전환 민감도
- `Servo 1/2 Angle`: 카메라 각도

**💡 팁**: 최적 값을 찾으면 코드에 기본값으로 저장하세요!

---

## 📂 주요 파일 위치

### 수정 가능한 파일들

```
03_self_driving/
├── 2_autoplot___test.py           # 기본 자율주행
├── 5_autoplot_harr_cascade_thread.py  # 표지판 인식
└── 6_custom_autoplot.py           # 개선된 버전 (추천!) ⭐

lib/raspbot/
├── Raspbot_Lib.py                 # 하드웨어 제어 라이브러리
├── PID.py                         # PID 제어
├── HSV_Config.py                  # 색상 설정
└── yb-discover.py                 # UDP 디스커버리

04_cascade/
└── YB_Pcb_Car.py                  # 차량 제어 클래스
```

---

## 🎯 수정 시나리오별 가이드

### 시나리오 1: "차가 너무 느려요"

**파일**: `6_custom_autoplot.py`

```python
# 22-24줄 수정
DEFAULT_SPEED_UP = 110        # 90 → 110
DEFAULT_SPEED_DOWN = 60       # 55 → 60
SPEED_BOOST = 20              # 15 → 20
```

---

### 시나리오 2: "라인을 잘 못 찾아요"

**파일**: `6_custom_autoplot.py`

```python
# 27-29줄 수정
DEFAULT_DETECT_VALUE = 40     # 35 → 40 (더 민감)
DEFAULT_BRIGHTNESS = 80       # 75 → 80 (더 밝게)
DEFAULT_CONTRAST = 85         # 80 → 85 (대비 증가)
```

---

### 시나리오 3: "너무 자주 방향을 바꿔요"

**파일**: `6_custom_autoplot.py`

```python
# 38-39줄 수정
DEFAULT_DIRECTION_THRESHOLD = 45000  # 35000 → 45000 (덜 민감)
```

---

### 시나리오 4: "카메라 각도를 바꾸고 싶어요"

**파일**: `6_custom_autoplot.py`

```python
# 42-43줄 수정
DEFAULT_SERVO_1 = 90          # 좌우 각도
DEFAULT_SERVO_2 = 110         # 115 → 110 (더 아래로)
```

---

### 시나리오 5: "LED를 제어하고 싶어요"

**파일**: `lib/raspbot/Raspbot_Lib.py`

```python
# 새로운 Python 스크립트 생성
import sys
sys.path.append('/home/pi/project_demo/lib/raspbot')
from Raspbot_Lib import Raspbot

car = Raspbot()

# 모든 LED를 빨간색으로
car.Ctrl_WQ2812_ALL(1, 0)  # 0=빨강, 1=초록, 2=파랑

# 개별 LED 제어
car.Ctrl_WQ2812_Alone(1, 1, 3)  # 1번 LED를 노란색으로

# 밝기 제어
car.Ctrl_WQ2812_brightness_ALL(255, 0, 0)  # 빨간색 최대 밝기
```

---

## 🔧 하드웨어 직접 제어

### 기본 차량 제어

```python
import sys
sys.path.append('/home/pi/project_demo/04_cascade')
from YB_Pcb_Car import YB_Pcb_Car
import time

car = YB_Pcb_Car()

# 전진
car.Car_Run(80, 80)
time.sleep(2)

# 좌회전
car.Car_Left(50, 80)
time.sleep(1)

# 우회전
car.Car_Right(80, 50)
time.sleep(1)

# 정지
car.Car_Stop()

# 서보 모터 (카메라 각도)
car.Ctrl_Servo(1, 90)   # 서보1: 좌우
car.Ctrl_Servo(2, 100)  # 서보2: 상하
```

---

## 🚦 자동 실행 설정

### 원클릭 설치

```bash
cd ~/project_demo/lib/raspbot
chmod +x install_autostart.sh
./install_autostart.sh
```

**3가지 방법 선택**:
1. systemd (권장) - 가장 안정적
2. Desktop autostart - GUI용
3. Cron - 가장 간단

**자세한 내용**: [AUTOSTART_GUIDE.md](./AUTOSTART_GUIDE.md) 참고

---

## 🐛 문제 해결

### 카메라가 작동하지 않음

```bash
# 카메라 테스트
raspistill -o test.jpg

# OpenCV에서 카메라 확인
python3 -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

### I2C 에러 (모터/서보 작동 안 함)

```bash
# I2C 활성화 확인
sudo raspi-config
# Interface Options → I2C → Enable

# I2C 장치 확인
sudo i2cdetect -y 1
```

### OpenCV 에러

```bash
# OpenCV 재설치
pip3 install opencv-python opencv-contrib-python
```

### 속도가 너무 느림

```bash
# Raspberry Pi 오버클럭 (주의!)
sudo nano /boot/config.txt
# 다음 추가:
# over_voltage=2
# arm_freq=1750

sudo reboot
```

---

## 📊 성능 모니터링

### CPU/메모리 사용량 확인

```bash
# 실시간 모니터링
htop

# 온도 확인
vcgencmd measure_temp

# CPU 주파수 확인
vcgencmd measure_clock arm
```

### 프로세스 확인

```bash
# Raspbot 프로세스 확인
ps aux | grep python

# 포트 사용 확인
sudo netstat -tulpn | grep 8000
```

---

## 💡 유용한 팁

### 1. 백업 만들기

```bash
# 중요 파일 백업
cd ~/project_demo
tar -czf raspbot_backup_$(date +%Y%m%d).tar.gz 03_self_driving/ lib/
```

### 2. 원격 개발

```bash
# VSCode Remote-SSH로 연결
# 또는 VNC로 GUI 접속
vncserver :1
```

### 3. 로그 확인

```bash
# systemd 서비스 로그
sudo journalctl -u raspbot.service -f

# 커스텀 로그
tail -f /tmp/raspbot_logs/*.log
```

### 4. 비디오 녹화

```python
# 자율주행 코드에 추가
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('output.avi', fourcc, 20.0, (320, 240))

# 메인 루프에서
out.write(frame)

# 종료 시
out.release()
```

---

## 📚 더 배우기

### OpenCV 튜토리얼
- 엣지 검출: https://docs.opencv.org/master/da/d22/tutorial_py_canny.html
- 이미지 변환: https://docs.opencv.org/master/da/d6e/tutorial_py_geometric_transformations.html

### Raspberry Pi GPIO
- 공식 문서: https://www.raspberrypi.org/documentation/

### 머신러닝 추가
- TensorFlow Lite: https://www.tensorflow.org/lite
- YOLOv5: https://github.com/ultralytics/yolov5

---

## ✅ 체크리스트

시작하기 전:
- [ ] Raspberry Pi 전원 연결
- [ ] 카메라 모듈 연결 및 활성화
- [ ] I2C 활성화 (모터/서보용)
- [ ] 배터리 충전 완료
- [ ] 테스트 트랙 준비

첫 실행:
- [ ] 기본 자율주행 테스트 (`2_autoplot___test.py`)
- [ ] 트랙바로 파라미터 조절
- [ ] 최적 값 찾기
- [ ] 코드에 기본값으로 저장

고급 기능:
- [ ] 표지판 인식 테스트
- [ ] 커스텀 효과 추가
- [ ] 자동 실행 설정
- [ ] 성능 최적화

---

## 🎓 다음 단계

1. ✅ 기본 자율주행 테스트
2. ✅ 파라미터 최적화
3. 🔄 표지판 인식 추가
4. 🔄 커스텀 알고리즘 개발
5. 🔄 머신러닝 통합
6. 🔄 완전 자율주행 구현

---

## 🆘 도움이 필요하신가요?

1. **상세 가이드**: [SOURCE_CODE_GUIDE.md](./SOURCE_CODE_GUIDE.md) 참고
2. **자동 실행**: [AUTOSTART_GUIDE.md](./AUTOSTART_GUIDE.md) 참고
3. **문서 구조**: [docs/README.md](./README.md) 참고
4. **코드 이해**: 주석을 자세히 읽어보세요!
5. **디버깅**: `DEBUG_MODE = True` 설정

---

**즐거운 코딩 되세요! 🚗💨**

