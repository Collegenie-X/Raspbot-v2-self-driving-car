# 📚 Raspbot 프로젝트 문서

이 폴더에는 Raspbot 자율주행 로봇 카 프로젝트의 모든 문서가 포함되어 있습니다.

---

## 📖 문서 목록

### 🚀 [QUICK_START.md](./QUICK_START.md)
**빠른 시작 가이드** - 5분 안에 시작하기

- 기본 자율주행 실행 방법
- 코드 수정하는 방법
- 실시간 파라미터 조절
- 시나리오별 수정 예제
- 문제 해결 가이드

**대상**: 처음 시작하는 사용자, 빠른 테스트를 원하는 사용자

---

### 📚 [SOURCE_CODE_GUIDE.md](./SOURCE_CODE_GUIDE.md)
**소스 코드 상세 가이드** - 전체 구조 및 수정 방법

- 프로젝트 전체 구조 설명
- 수정 가능한 모든 소스 코드 목록
- 각 파일의 기능 및 주요 메서드
- 상세한 수정 워크플로우
- 디버깅 팁

**대상**: 코드를 깊이 이해하고 싶은 개발자, 고급 수정을 원하는 사용자

---

### ⚙️ [AUTOSTART_GUIDE.md](./AUTOSTART_GUIDE.md)
**자동 실행 설정 가이드** - 부팅 시 자동 시작

- systemd 서비스 설정 (권장)
- Desktop autostart 설정 (GUI용)
- Cron 설정 (간단한 방법)
- 서비스 관리 명령어
- 트러블슈팅

**대상**: Raspberry Pi에서 자동 실행을 설정하려는 사용자

---

### 🔄 [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)
**마이그레이션 가이드** - YB_Pcb_Car → Raspbot_Lib 전환

- 주요 변경사항 요약
- 라이브러리 Import 변경
- 모터 제어 방식 변경
- 서보 모터 각도 제한
- 추가 기능 (LED, 부저, 센서)
- 전체 코드 비교 예제

**대상**: 기존 코드를 최신 버전으로 업데이트하려는 개발자

---

### 📷 [CAMERA_SETUP.md](./CAMERA_SETUP.md)
**카메라 설정 가이드** - Pi Camera & USB 카메라

- Pi Camera 모듈 설정
- USB 카메라 설정
- 자동 감지 방식
- 문제 해결 (권한, 인식 등)
- 카메라 성능 최적화

**대상**: 카메라 설정 및 문제를 해결하려는 사용자

---

### 🎛️ [TUNING_GUIDE.md](./TUNING_GUIDE.md)
**자율주행 튜닝 가이드** - 밝기/라인검출 조절 ⭐ **NEW**

- 화면이 너무 밝을 때 해결 방법
- 화면이 너무 어두울 때 해결 방법
- 라인 검출 최적화
- 트랙바 설정 가이드
- 환경별 설정 레시피 (실내/야외)
- 단계별 튜닝 방법

**대상**: 라인 검출이 안 되는 사용자, 환경에 맞게 최적화하려는 사용자

---

## 🗺️ 문서 읽는 순서

### 초보자
1. **[QUICK_START.md](./QUICK_START.md)** - 기본 실행 및 간단한 수정
2. **[TUNING_GUIDE.md](./TUNING_GUIDE.md)** - 밝기/라인검출 조절 ⭐ **(화면이 안 보이면 여기!)**
3. **[SOURCE_CODE_GUIDE.md](./SOURCE_CODE_GUIDE.md)** - 더 깊이 이해하기
4. **[AUTOSTART_GUIDE.md](./AUTOSTART_GUIDE.md)** - 자동화 설정

### 중급자
1. **[SOURCE_CODE_GUIDE.md](./SOURCE_CODE_GUIDE.md)** - 전체 구조 파악
2. **[QUICK_START.md](./QUICK_START.md)** - 빠른 수정 팁
3. **[MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)** - 코드 업데이트
4. **[AUTOSTART_GUIDE.md](./AUTOSTART_GUIDE.md)** - 배포 설정

### 고급자 / 기존 사용자
1. **[MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)** - 기존 코드 전환
2. 필요한 부분만 참고
3. 각 문서의 특정 섹션으로 바로 이동

---

## 🎯 목적별 문서 찾기

| 목적 | 문서 | 섹션 |
|------|------|------|
| 빠르게 시작하기 | QUICK_START.md | "5분 안에 시작하기" |
| 속도 조절하기 | QUICK_START.md | "시나리오 1: 차가 너무 느려요" |
| 라인 검출 개선 | QUICK_START.md | "시나리오 2: 라인을 잘 못 찾아요" |
| 코드 구조 이해 | SOURCE_CODE_GUIDE.md | "주요 수정 가능한 소스 코드" |
| 표지판 인식 추가 | SOURCE_CODE_GUIDE.md | "시나리오 2: 표지판 인식 추가" |
| LED 효과 변경 | SOURCE_CODE_GUIDE.md | "시나리오 3: LED 효과 변경" |
| 자동 실행 설정 | AUTOSTART_GUIDE.md | "방법 1: systemd 서비스" |
| 서비스 관리 | AUTOSTART_GUIDE.md | "서비스 제어 명령어" |
| 코드 업데이트 | MIGRATION_GUIDE.md | "전체 예제 비교" |
| 라이브러리 전환 | MIGRATION_GUIDE.md | "YB_Pcb_Car → Raspbot_Lib" |
| 카메라 설정 | CAMERA_SETUP.md | "Pi Camera 모듈 설정" |
| 카메라 에러 | CAMERA_SETUP.md | "문제 해결" |
| **화면이 너무 밝아요** | **TUNING_GUIDE.md** | **"문제 1: 화면이 너무 밝아요"** ⭐ |
| **라인 검출 안됨** | **TUNING_GUIDE.md** | **"문제 3: 라인 검출이 안 돼요"** ⭐ |
| 트랙바 조절 | TUNING_GUIDE.md | "트랙바 설정 가이드" |
| 환경별 설정 | TUNING_GUIDE.md | "빠른 설정 레시피" |
| 문제 해결 | QUICK_START.md | "문제 해결" |
| 디버깅 | SOURCE_CODE_GUIDE.md | "디버깅 팁" |

---

## 💡 빠른 참조

### 주요 파일 위치

```
03_self_driving/
├── 2_autoplot___test.py           # 기본 자율주행
├── 5_autoplot_harr_cascade_thread.py  # 표지판 인식
└── 6_custom_autoplot.py           # 개선된 버전 ⭐

lib/raspbot/
├── Raspbot_Lib.py                 # 하드웨어 제어
├── yb-discover.py                 # UDP 디스커버리
└── raspbot.pyc                    # 메인 서버 (수정 불가)

04_cascade/
└── YB_Pcb_Car.py                  # 차량 제어 클래스
```

### 주요 명령어

```bash
# 자율주행 실행
python3 ~/project_demo/03_self_driving/6_custom_autoplot.py

# 자동 실행 설치
~/project_demo/lib/raspbot/install_autostart.sh

# 서비스 상태 확인
~/project_demo/lib/raspbot/raspbot_status.sh

# 서비스 중지
~/project_demo/lib/raspbot/raspbot_stop.sh
```

---

## 🔗 관련 스크립트

문서와 함께 사용할 수 있는 유틸리티 스크립트들:

- `lib/raspbot/install_autostart.sh` - 자동 실행 설치 (원클릭)
- `lib/raspbot/raspbot_start_improved.sh` - 개선된 시작 스크립트
- `lib/raspbot/raspbot_stop.sh` - 서비스 중지
- `lib/raspbot/raspbot_status.sh` - 상태 확인
- `03_self_driving/6_custom_autoplot.py` - 개선된 자율주행 코드

---

## 📝 문서 업데이트

이 문서들은 프로젝트와 함께 업데이트됩니다. 

마지막 업데이트: 2025년 11월

---

## 🆘 도움이 필요하신가요?

1. 먼저 **[QUICK_START.md](./QUICK_START.md)** 를 읽어보세요
2. 더 자세한 내용은 **[SOURCE_CODE_GUIDE.md](./SOURCE_CODE_GUIDE.md)** 를 참고하세요
3. 자동 실행 설정은 **[AUTOSTART_GUIDE.md](./AUTOSTART_GUIDE.md)** 를 확인하세요
4. 각 문서 마지막의 "문제 해결" 섹션을 확인하세요

---

**Happy Coding! 🚗💨**

