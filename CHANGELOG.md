# 📝 Raspbot v2 변경 이력

## [2.0.0] - 2025-11-25

### 🎉 주요 변경사항

#### ✨ 새로운 기능
- **최신 Raspbot_Lib 라이브러리 적용**
  - `YB_Pcb_Car` 대신 `Raspbot_Lib.Raspbot` 사용
  - 더 많은 하드웨어 제어 기능 (LED, 부저, 센서)
  
- **개선된 자율주행 코드**
  - `03_self_driving/6_custom_autoplot.py` 완전 재작성
  - 올바른 모터 제어 방식 적용
  - LED 효과 통합 (방향별 색상 표시)
  - 부저 기능 통합 (옵션)
  - 향상된 에러 처리

- **자동 카메라 감지 지원** ⭐
  - Picamera2 자동 감지 (Pi Camera 모듈)
  - USB 카메라 fallback 지원
  - 상세한 에러 메시지 및 해결 방법 제공
  - 카메라 타입별 최적화

- **완전한 문서화**
  - 📚 `docs/` 폴더에 모든 문서 통합
  - 🔄 `MIGRATION_GUIDE.md` 추가 (전환 가이드)
  - 📷 `CAMERA_SETUP.md` 추가 (카메라 설정 가이드)
  - 📖 `QUICK_START.md` 개선
  - 📚 `SOURCE_CODE_GUIDE.md` 업데이트
  - ⚙️ `AUTOSTART_GUIDE.md` 완성

### 🔧 기술적 변경사항

#### 모터 제어
- **이전**: `car.Car_Run(speed1, speed2)` (0~255)
- **현재**: `bot.Ctrl_Muto(motor_id, speed)` (-255~255)
- 음수 값으로 후진 표현

#### 서보 모터
- **서보 2 최대 각도**: 180° → 110°
- **기본 각도**: S1=90°, S2=25° (이전 119°)

#### 속도 제어
- **속도 범위**: -255 ~ 255 (음수=후진)
- **기본 속도**: 전진 100, 회전 55
- **속도 부스트**: 직진 시 +15

#### LED 제어
- 전진: 초록색 (1)
- 좌/우회전: 노란색 (3)
- 시작: 파란색 (2)
- 정지: LED 끄기

### 📦 파일 변경

#### 추가된 파일
```
docs/
├── MIGRATION_GUIDE.md          # 신규
├── CAMERA_SETUP.md             # 신규
├── README.md                   # 신규
├── QUICK_START.md              # 이동 (루트에서)
├── SOURCE_CODE_GUIDE.md        # 이동 (루트에서)
└── AUTOSTART_GUIDE.md          # 이동 (lib/raspbot에서)

03_self_driving/
├── 6_custom_autoplot.py        # 완전 재작성
└── 6_custom_autoplot_old.py   # 백업

.github/
└── STRUCTURE.md                # 신규

CHANGELOG.md                    # 이 파일
```

#### 수정된 파일
```
README.md                       # 업데이트
docs/README.md                  # docs 인덱스 추가
lib/raspbot/
├── install_autostart.sh        # 개선
├── raspbot_start_improved.sh   # 신규
├── raspbot_stop.sh             # 신규
├── raspbot_status.sh           # 신규
└── raspbot.service             # 신규
```

### 🔄 마이그레이션 가이드

기존 코드를 새 버전으로 업데이트하려면:
1. `docs/MIGRATION_GUIDE.md` 참조
2. `03_self_driving/6_custom_autoplot.py` 예제 확인
3. `02_Basic/` 폴더의 공식 예제 참고

### ⚠️ 중요 변경사항 (Breaking Changes)

1. **라이브러리 Import 필수 변경**
   ```python
   # ❌ 이전
   import YB_Pcb_Car
   car = YB_Pcb_Car.YB_Pcb_Car()
   
   # ✅ 현재
   from Raspbot_Lib import Raspbot
   bot = Raspbot()
   ```

2. **모터 제어 방식 완전 변경**
   ```python
   # ❌ 이전
   car.Car_Run(100, 100)
   
   # ✅ 현재
   bot.Ctrl_Muto(0, 100)  # 각 모터 개별 제어
   bot.Ctrl_Muto(1, 100)
   bot.Ctrl_Muto(2, 100)
   bot.Ctrl_Muto(3, 100)
   ```

3. **서보 2 각도 제한**
   ```python
   # ❌ 이전
   car.Ctrl_Servo(2, 119)  # 0~180
   
   # ✅ 현재
   bot.Ctrl_Servo(2, 25)   # 0~110 (최대 110)
   ```

4. **객체 삭제 필수**
   ```python
   # 프로그램 종료 시 필수
   del bot
   ```

### 🎯 업그레이드 우선순위

#### 필수 (즉시 업데이트 권장)
- ✅ 새 프로젝트
- ✅ LED/부저 기능이 필요한 프로젝트
- ✅ 더 정밀한 모터 제어가 필요한 프로젝트

#### 선택 (기존 코드 계속 사용 가능)
- 기존 작동 중인 프로젝트
- 단순 테스트 코드
- `YB_Pcb_Car`로 충분한 경우

### 📚 참고 문서

- [QUICK_START.md](./docs/QUICK_START.md) - 빠른 시작
- [MIGRATION_GUIDE.md](./docs/MIGRATION_GUIDE.md) - 전환 가이드
- [SOURCE_CODE_GUIDE.md](./docs/SOURCE_CODE_GUIDE.md) - 상세 가이드
- [AUTOSTART_GUIDE.md](./docs/AUTOSTART_GUIDE.md) - 자동 실행

### 🙏 감사의 말

- Yahboom Tech의 `02_Basic` 예제 참고
- OpenCV 커뮤니티
- Raspberry Pi Foundation

---

## [1.0.0] - 2024-07-12

### 초기 버전
- YB_Pcb_Car 라이브러리 사용
- 기본 자율주행 기능
- 표지판 인식
- Haar Cascade 객체 인식

---

**전체 변경 이력**: https://github.com/YOUR_USERNAME/Raspbot-v2-self-driving-car/compare/v1.0.0...v2.0.0

