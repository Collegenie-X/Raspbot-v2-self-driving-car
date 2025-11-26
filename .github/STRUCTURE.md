# 📂 Raspbot 프로젝트 파일 구조

## 📋 전체 구조 개요

```
Raspbot-v2-self-driving-car/
│
├── 📁 docs/                         ⭐ 모든 문서 모음
│   ├── README.md                    # 문서 구조 가이드
│   ├── QUICK_START.md              # 빠른 시작 가이드
│   ├── SOURCE_CODE_GUIDE.md        # 소스 코드 상세 가이드
│   └── AUTOSTART_GUIDE.md          # 자동 실행 설정
│
├── 📁 01_Movies/                    # 시연 동영상
│   ├── _신호등_인식_동영상/
│   ├── _자율주행__Test__동영상/
│   ├── _자율주행_완료_영상/
│   └── 자율주행_테스트_화면_캡쳐/
│
├── 📁 02_Basic/                     # 기본 하드웨어 테스트
│   ├── 1.Buzzer driver.ipynb
│   ├── 2.RGB Light bar test.ipynb
│   ├── 3.Servo control.ipynb
│   ├── 4.Motor control.ipynb
│   ├── 5.Ultrasonic distance measurement.ipynb
│   ├── 6.Status of four-way line patrol module.ipynb
│   ├── Motor/
│   └── opencv_camera.py
│
├── 📁 03_self_driving/              ⭐ 자율주행 메인 코드
│   ├── 0_autoplot_print.py
│   ├── 1_autoplot___test_without_servo_motor.py
│   ├── 2_autoplot___test.py        # 기본 자율주행
│   ├── 3_color_dection.py
│   ├── 4_autoplot_harr_cascade.py
│   ├── 5_autoplot_harr_cascade_thread.py  # 표지판 인식
│   └── 6_custom_autoplot.py        # ⭐ 개선된 자율주행 (권장!)
│
├── 📁 04_cascade/                   # Haar Cascade 객체 인식
│   ├── YB_Pcb_Car.py               # 차량 제어 클래스
│   ├── 0_camera_color_rect.py
│   ├── 1_camera_weight.py
│   ├── 2_camera_write.py
│   ├── 3_object_camera_haarcascade.py
│   ├── 4_auto_plot_park_test.py
│   ├── 5_multi_thread_cascade.py
│   ├── cascade.xml
│   ├── Stop_cascade.xml
│   ├── park_data_example/
│   └── 06.Face_recognition/
│
├── 📁 05_final_self_driving/        # 최종 통합 버전 (개발 중)
│
├── 📁 lib/raspbot/                  ⭐ 핵심 라이브러리
│   ├── Raspbot_Lib.py              # 하드웨어 제어 라이브러리
│   ├── yb-discover.py              # UDP 디스커버리 서버
│   ├── raspbot.pyc                 # 메인 웹 서버 (컴파일됨)
│   ├── raspbot_start.sh            # 기본 시작 스크립트
│   ├── raspbot_start_improved.sh   # ⭐ 개선된 시작 스크립트
│   ├── raspbot_stop.sh             # 중지 스크립트
│   ├── raspbot_status.sh           # 상태 확인 스크립트
│   ├── install_autostart.sh        # ⭐ 자동 실행 설치 (원클릭)
│   ├── raspbot.service             # systemd 서비스 파일
│   ├── start_raspbot.desktop       # Desktop autostart 파일
│   ├── PID.py                      # PID 제어 알고리즘
│   ├── HSV_Config.py               # 색상 설정
│   ├── color_detection.py          # 색상 감지
│   ├── face_tracking.py            # 얼굴 추적
│   ├── gesture_action.py           # 제스처 인식
│   ├── compile.py                  # .pyc 컴파일 도구
│   ├── killprocess.py              # 프로세스 종료 도구
│   ├── templates/                  # 웹 UI 템플릿
│   │   ├── index.html
│   │   └── init.html
│   ├── object_detection/           # TensorFlow 객체 인식
│   └── ssdlite_mobilenet_v2_coco_2018_05_09/  # 사전 학습 모델
│
├── 📁 opencv/                       # OpenCV 고급 기능
│   ├── 03.Speech_Car_line_patrol/  # 음성 제어 + 라인 트래킹
│   ├── 04.Face_tracking/           # 얼굴 추적
│   ├── 05.Face_follow/             # 얼굴 따라가기
│   ├── 06.Speech_Track_color_Face/ # 음성 제어 + 색상/얼굴 추적
│   ├── 07.Vision_Based_Auto_LineFollowing/  # 비전 기반 자율주행
│   ├── 08.Autopilot_map_sandbox/   # 맵 기반 자율주행
│   ├── 09.Gesture_follows/         # 제스처 따라가기
│   └── openCV*.ipynb               # OpenCV 튜토리얼
│
├── 📁 .github/                      # GitHub 관련 파일
│   └── STRUCTURE.md                # 이 문서
│
├── README.md                        # ⭐ 프로젝트 메인 README
└── .gitignore

```

---

## 🎯 주요 디렉토리 설명

### 📚 `docs/` - 프로젝트 문서
**모든 문서가 한 곳에!**

| 파일 | 용도 | 대상 |
|------|------|------|
| `README.md` | 문서 구조 가이드 | 모든 사용자 |
| `QUICK_START.md` | 5분 안에 시작하기 | 초보자 |
| `SOURCE_CODE_GUIDE.md` | 코드 상세 설명 | 개발자 |
| `AUTOSTART_GUIDE.md` | 자동 실행 설정 | 배포자 |

### 🚗 `03_self_driving/` - 자율주행 코드
**여기서 시작하세요!**

| 파일 | 기능 | 난이도 |
|------|------|--------|
| `6_custom_autoplot.py` ⭐ | 개선된 자율주행 (권장) | ⭐⭐ |
| `2_autoplot___test.py` | 기본 라인 트래킹 | ⭐ |
| `5_autoplot_harr_cascade_thread.py` | 표지판 인식 | ⭐⭐⭐ |

### 🔧 `lib/raspbot/` - 핵심 라이브러리
**모든 하드웨어 제어와 유틸리티**

#### Python 라이브러리
- `Raspbot_Lib.py` - 전체 하드웨어 제어 (모터, LED, 센서)
- `yb-discover.py` - UDP 네트워크 검색
- `PID.py` - PID 제어 알고리즘

#### Shell 스크립트
- `install_autostart.sh` ⭐ - 자동 실행 원클릭 설치
- `raspbot_start_improved.sh` - 향상된 시작 스크립트
- `raspbot_stop.sh` - 서비스 중지
- `raspbot_status.sh` - 상태 확인

#### 설정 파일
- `raspbot.service` - systemd 서비스
- `start_raspbot.desktop` - Desktop autostart

---

## 📝 파일 명명 규칙

### Python 파일
- `[번호]_[기능]_[세부사항].py` 형식
- 예: `6_custom_autoplot.py`, `5_autoplot_harr_cascade_thread.py`

### Shell 스크립트
- `raspbot_[동작].sh` 형식
- 예: `raspbot_start.sh`, `raspbot_stop.sh`

### 문서
- 대문자로 시작 (예: `README.md`, `QUICK_START.md`)
- 언더스코어로 구분 (예: `SOURCE_CODE_GUIDE.md`)

---

## 🔍 파일 찾기 가이드

### "자율주행 코드를 수정하고 싶어요"
👉 `03_self_driving/6_custom_autoplot.py`

### "하드웨어를 제어하고 싶어요"
👉 `lib/raspbot/Raspbot_Lib.py`

### "자동 실행을 설정하고 싶어요"
👉 `lib/raspbot/install_autostart.sh`

### "표지판 인식을 추가하고 싶어요"
👉 `03_self_driving/5_autoplot_harr_cascade_thread.py`

### "LED 효과를 바꾸고 싶어요"
👉 `lib/raspbot/Raspbot_Lib.py` (LightShow 클래스)

### "웹 서버를 수정하고 싶어요"
👉 `lib/raspbot/raspbot.pyc` (⚠️ 원본 .py 파일 필요)

---

## 📊 파일 중요도

### ⭐⭐⭐ 필수 파일
- `03_self_driving/6_custom_autoplot.py` - 개선된 자율주행
- `lib/raspbot/Raspbot_Lib.py` - 하드웨어 제어
- `docs/QUICK_START.md` - 빠른 시작 가이드
- `README.md` - 프로젝트 소개

### ⭐⭐ 중요 파일
- `lib/raspbot/install_autostart.sh` - 자동 실행 설치
- `03_self_driving/5_autoplot_harr_cascade_thread.py` - 표지판 인식
- `docs/SOURCE_CODE_GUIDE.md` - 코드 가이드
- `04_cascade/YB_Pcb_Car.py` - 차량 제어 클래스

### ⭐ 참고 파일
- `02_Basic/` - 하드웨어 테스트 예제
- `opencv/` - OpenCV 고급 기능
- `lib/raspbot/PID.py` - PID 제어

---

## 🗂️ 작업별 파일 위치

### 자율주행 개발
```
03_self_driving/
├── 6_custom_autoplot.py          # 메인 작업 파일
├── 2_autoplot___test.py          # 참고용
└── 5_autoplot_harr_cascade_thread.py  # 표지판 인식
```

### 하드웨어 제어
```
lib/raspbot/
├── Raspbot_Lib.py                # 메인 라이브러리
└── PID.py                        # PID 제어

04_cascade/
└── YB_Pcb_Car.py                 # 기본 차량 제어
```

### 배포 및 자동화
```
lib/raspbot/
├── install_autostart.sh          # 설치 스크립트
├── raspbot_start_improved.sh     # 시작
├── raspbot_stop.sh               # 중지
├── raspbot_status.sh             # 상태
├── raspbot.service               # systemd
└── start_raspbot.desktop         # desktop autostart
```

### 문서 작업
```
docs/
├── README.md                     # 문서 인덱스
├── QUICK_START.md               # 초보자 가이드
├── SOURCE_CODE_GUIDE.md         # 개발자 가이드
└── AUTOSTART_GUIDE.md           # 배포 가이드
```

---

## 💾 백업 권장 파일

### 필수 백업
1. `03_self_driving/` - 모든 자율주행 코드
2. `lib/raspbot/Raspbot_Lib.py` - 하드웨어 제어
3. `docs/` - 모든 문서

### 선택 백업
1. `04_cascade/YB_Pcb_Car.py` - 차량 제어 클래스
2. `lib/raspbot/*.sh` - 유틸리티 스크립트
3. `opencv/` - 고급 기능 예제

---

## 🔄 버전별 파일 관리

### v1.0 (기본)
- `03_self_driving/2_autoplot___test.py`
- `04_cascade/YB_Pcb_Car.py`

### v2.0 (개선)
- `03_self_driving/6_custom_autoplot.py` ⭐
- `lib/raspbot/Raspbot_Lib.py`
- `lib/raspbot/raspbot_start_improved.sh`

### v3.0 (통합) - 개발 중
- `05_final_self_driving/`

---

## 📌 참고사항

### 수정 가능한 파일
- ✅ `*.py` (Python 소스)
- ✅ `*.sh` (Shell 스크립트)
- ✅ `*.md` (문서)
- ✅ `*.xml` (Haar Cascade 모델)

### 수정 불가능한 파일
- ❌ `*.pyc` (컴파일된 Python)
- ❌ `*.pb` (TensorFlow 모델)
- ❌ `*.ckpt*` (체크포인트)

---

**이 구조도는 프로젝트 전체를 한눈에 파악하는 데 도움이 됩니다! 📂✨**

