# Raspberry Pi 자동 실행 가이드

Raspbot 서비스 관리를 위한 간단한 가이드입니다.

---

## 📌 목차

1. [현재 실행 중인 서비스 확인 및 종료](#1-현재-실행-중인-서비스-확인-및-종료)
2. [부팅 시 자동 시작 막기](#2-부팅-시-자동-시작-막기)
3. [부팅 시 자동 시작 설정](#3-부팅-시-자동-시작-설정)

---

## 1. 현재 실행 중인 서비스 확인 및 종료

### 1단계: 포트 8888 확인 및 종료

```bash
# 포트 8888 사용 프로세스 확인
lsof -i :8888

# 출력 예시:
# COMMAND   PID USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
# jupyter-l 880   pi    9u  IPv4  10473      0t0  TCP *:8888 (LISTEN)

# PID(880)를 사용하여 프로세스 종료
kill 880

# 확인
lsof -i :8888
# (아무것도 출력되지 않으면 성공)
```

### 2단계: 포트 8000 확인 및 종료

```bash
# 포트 8000 사용 프로세스 확인
lsof -i :8000

# 출력 예시:
# COMMAND  PID USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
# python3 1326   pi    3u  IPv4   9384      0t0  UDP *:8000

# PID(1326)를 사용하여 프로세스 종료
kill 1326

# 확인
lsof -i :8000
# (아무것도 출력되지 않으면 성공)
```

### 3단계: 이름으로 프로세스 종료 (대안)

```bash
# yb-discover.py 종료 (포트 8000 사용)
pkill -f "yb-discover.py"

# raspbot.pyc 종료
pkill -f "raspbot.pyc"

# jupyter 종료 (포트 8888 사용)
pkill -f "jupyter"
```

---

## 2. 부팅 시 자동 시작 막기

### 방법 1: systemd 서비스 비활성화 (raspbot)

```bash
# 1. 현재 실행 중인 서비스 중지
sudo systemctl stop raspbot.service

# 2. 부팅 시 자동 시작 비활성화
sudo systemctl disable raspbot.service

# 3. 확인
sudo systemctl status raspbot.service
# (disabled로 표시되면 성공)
```

### 방법 2: Jupyter 자동 시작 막기

#### 2-1. systemd 서비스 확인

```bash
# jupyter 관련 서비스 찾기
sudo systemctl list-units --all | grep jupyter

# 발견된 서비스 비활성화 (예: jupyter.service)
sudo systemctl stop jupyter.service
sudo systemctl disable jupyter.service
```

#### 2-2. cron 확인

```bash
# crontab 편집
crontab -e

# @reboot로 시작하는 jupyter 관련 줄 찾아서 삭제 또는 주석 처리
# 예: @reboot jupyter lab --no-browser
# 주석 처리: # @reboot jupyter lab --no-browser
```

#### 2-3. autostart 확인

```bash
# autostart 디렉토리 확인
ls ~/.config/autostart/

# jupyter 관련 .desktop 파일 삭제
rm ~/.config/autostart/jupyter*.desktop
```

### 방법 3: 모든 자동 시작 확인

```bash
# systemd 서비스 목록
sudo systemctl list-unit-files --state=enabled

# cron 작업 확인
crontab -l

# autostart 확인
ls ~/.config/autostart/
```

---

## 3. 부팅 시 자동 시작 설정

### 3-1. raspbot 서비스 등록 (systemd 방식 - 권장)

```bash
# 1. 서비스 파일 복사
sudo cp /home/pi/project_demo/raspbot/raspbot.service /etc/systemd/system/

# 2. 권한 설정
sudo chmod 644 /etc/systemd/system/raspbot.service

# 3. systemd 리로드
sudo systemctl daemon-reload

# 4. 서비스 활성화 (부팅 시 자동 시작)
sudo systemctl enable raspbot.service

# 5. 서비스 시작 (지금 바로 시작)
sudo systemctl start raspbot.service

# 6. 상태 확인
sudo systemctl status raspbot.service
```

### 3-2. cron 방식 (간단한 방법)

```bash
# 1. crontab 편집
crontab -e

# 2. 맨 아래에 추가
@reboot sleep 10 && /bin/sh /home/pi/project_demo/raspbot/raspbot_start.sh

# 3. 저장 후 종료 (Ctrl+X, Y, Enter)

# 4. 확인
crontab -l
```

### 3-3. Desktop Autostart 방식 (GUI 환경)

```bash
# 1. autostart 디렉토리 생성
mkdir -p ~/.config/autostart

# 2. Desktop 파일 복사
cp /home/pi/project_demo/raspbot/start_raspbot.desktop ~/.config/autostart/

# 3. 권한 설정
chmod +x ~/.config/autostart/start_raspbot.desktop

# 4. 재부팅
sudo reboot
```

---

## 🔧 서비스 제어 명령어 (빠른 참조)

### systemd 방식

```bash
# 서비스 시작
sudo systemctl start raspbot.service

# 서비스 중지
sudo systemctl stop raspbot.service

# 서비스 재시작
sudo systemctl restart raspbot.service

# 서비스 상태 확인
sudo systemctl status raspbot.service

# 자동 시작 활성화
sudo systemctl enable raspbot.service

# 자동 시작 비활성화
sudo systemctl disable raspbot.service

# 로그 확인 (실시간)
sudo journalctl -u raspbot.service -f
```

### 프로세스 직접 제어

```bash
# 프로세스 찾기
ps aux | grep -E "raspbot|jupyter|yb-discover"

# 프로세스 종료
pkill -f "프로세스명"

# 포트 사용 확인
lsof -i :8888
lsof -i :8000
```

---

## 📋 실행되는 서비스 정보

### 포트 8888: Jupyter Lab
- **프로세스**: jupyter-lab
- **역할**: Jupyter 노트북 서버
- **종료 방법**: `pkill -f "jupyter"` 또는 `kill PID`

### 포트 8000: yb-discover.py
- **프로세스**: python3 yb-discover.py
- **역할**: Raspbot 디바이스 검색 서버 (UDP)
- **종료 방법**: `pkill -f "yb-discover.py"` 또는 `kill PID`

### raspbot.pyc
- **프로세스**: python3 raspbot.pyc
- **역할**: Raspbot 메인 제어 프로그램
- **종료 방법**: `pkill -f "raspbot.pyc"` 또는 `kill PID`

---

## 💡 자주 사용하는 시나리오

### 시나리오 1: 모든 서비스 즉시 중지

```bash
# 포트 8888 (Jupyter)
pkill -f "jupyter"

# 포트 8000 (yb-discover)
pkill -f "yb-discover.py"

# raspbot
pkill -f "raspbot.pyc"

# systemd 서비스도 중지
sudo systemctl stop raspbot.service
```

### 시나리오 2: 재부팅 후 자동 시작 완전히 막기

```bash
# 1. systemd 서비스 비활성화
sudo systemctl disable raspbot.service
sudo systemctl stop raspbot.service

# 2. cron 확인 및 제거
crontab -e
# @reboot 줄 삭제

# 3. autostart 제거
rm ~/.config/autostart/start_raspbot.desktop 2>/dev/null
rm ~/.config/autostart/jupyter*.desktop 2>/dev/null

# 4. jupyter 서비스 비활성화
sudo systemctl disable jupyter.service 2>/dev/null
```

### 시나리오 3: 개발 모드 (자동 시작 끄고 수동 제어)

```bash
# 자동 시작 비활성화
sudo systemctl disable raspbot.service

# 필요할 때만 수동 시작
sudo systemctl start raspbot.service

# 작업 완료 후 중지
sudo systemctl stop raspbot.service
```

---

## 🆘 문제 해결

### "Permission denied" 오류

```bash
# sudo 권한 필요
sudo systemctl stop raspbot.service
sudo lsof -i :8000
```

### 프로세스가 종료되지 않음

```bash
# 강제 종료 (-9 옵션)
sudo kill -9 PID

# 또는
sudo pkill -9 -f "프로세스명"
```

### 서비스가 계속 재시작됨

```bash
# raspbot.service는 실패 시 자동 재시작 설정됨
# 완전히 중지하려면 비활성화 필요
sudo systemctl disable raspbot.service
sudo systemctl stop raspbot.service
```

### 어떤 서비스가 자동 시작되는지 모름

```bash
# 활성화된 systemd 서비스 확인
sudo systemctl list-unit-files --state=enabled

# cron 작업 확인
crontab -l

# autostart 파일 확인
ls -la ~/.config/autostart/
```

---

## 📚 관련 문서

- **서비스 상세 정보**: [lib/raspbot/SERVICE_INFO.md](../lib/raspbot/SERVICE_INFO.md)
- **빠른 가이드**: [lib/raspbot/빠른_서비스_제어_가이드.md](../lib/raspbot/빠른_서비스_제어_가이드.md)

---

**마지막 업데이트**: 2025-12-15
