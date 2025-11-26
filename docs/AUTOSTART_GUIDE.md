# Raspberry Pi 자동 실행 가이드

Raspbot 서비스를 Raspberry Pi 부팅 시 자동으로 실행하는 방법입니다.

---

## 🎯 방법 1: systemd 서비스 (가장 권장)

### 장점
- 안정적이고 전문적인 방법
- 자동 재시작 기능
- 로그 관리 용이
- 서비스 상태 모니터링 가능

### 설치 방법

1. **서비스 파일 복사**
```bash
sudo cp /home/pi/project_demo/raspbot/raspbot.service /etc/systemd/system/
```

2. **권한 설정**
```bash
sudo chmod 644 /etc/systemd/system/raspbot.service
```

3. **서비스 등록 및 활성화**
```bash
# systemd 데몬 리로드
sudo systemctl daemon-reload

# 서비스 활성화 (부팅 시 자동 시작)
sudo systemctl enable raspbot.service

# 서비스 시작
sudo systemctl start raspbot.service
```

4. **서비스 상태 확인**
```bash
# 서비스 상태 확인
sudo systemctl status raspbot.service

# 로그 확인
sudo journalctl -u raspbot.service -f
```

### 서비스 제어 명령어
```bash
# 서비스 시작
sudo systemctl start raspbot.service

# 서비스 중지
sudo systemctl stop raspbot.service

# 서비스 재시작
sudo systemctl restart raspbot.service

# 자동 시작 비활성화
sudo systemctl disable raspbot.service

# 로그 보기 (실시간)
sudo journalctl -u raspbot.service -f

# 로그 보기 (최근 100줄)
sudo journalctl -u raspbot.service -n 100
```

---

## 📝 방법 2: Desktop Autostart (GUI 환경)

### 장점
- 설정이 간단함
- GUI 환경에서 자동 실행

### 설치 방법

1. **autostart 디렉토리 생성**
```bash
mkdir -p ~/.config/autostart
```

2. **Desktop 파일 복사**
```bash
cp /home/pi/project_demo/raspbot/start_raspbot.desktop ~/.config/autostart/
```

3. **권한 설정**
```bash
chmod +x ~/.config/autostart/start_raspbot.desktop
chmod +x /home/pi/project_demo/raspbot/raspbot_start.sh
```

4. **재부팅**
```bash
sudo reboot
```

### 자동 시작 해제
```bash
rm ~/.config/autostart/start_raspbot.desktop
```

---

## ⏰ 방법 3: Cron (간단한 방법)

### 장점
- 가장 간단한 방법
- 추가 설정 파일 불필요

### 설치 방법

1. **crontab 편집**
```bash
crontab -e
```

2. **다음 줄 추가** (파일 맨 아래에)
```bash
@reboot sleep 10 && /bin/sh /home/pi/project_demo/raspbot/raspbot_start.sh
```

3. **저장 후 재부팅**
```bash
sudo reboot
```

### 자동 시작 해제
```bash
crontab -e
# 위에서 추가한 줄 삭제
```

---

## 🔧 스크립트 개선 (선택사항)

현재 `raspbot_start.sh`의 경로가 하드코딩되어 있습니다. 더 유연하게 만들려면:

```bash
#!/bin/sh
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$SCRIPT_DIR/raspbot.pyc" &
python3 "$SCRIPT_DIR/yb-discover.py" &
```

---

## ✅ 추천 방법

- **일반 사용자**: **방법 1 (systemd)** - 가장 안정적이고 관리하기 쉬움
- **GUI 환경**: **방법 2 (Desktop Autostart)** - 간단하고 GUI에서 실행
- **빠른 테스트**: **방법 3 (Cron)** - 가장 간단하지만 기능 제한적

---

## 🐛 트러블슈팅

### 서비스가 시작되지 않는 경우

1. **로그 확인**
```bash
sudo journalctl -u raspbot.service -n 50
```

2. **권한 확인**
```bash
ls -l /home/pi/project_demo/raspbot/raspbot_start.sh
chmod +x /home/pi/project_demo/raspbot/raspbot_start.sh
```

3. **Python 경로 확인**
```bash
which python3
```

### 프로세스 확인

```bash
# raspbot 프로세스 확인
ps aux | grep raspbot

# 포트 8000 사용 확인
sudo netstat -tulpn | grep 8000
```

### 수동으로 프로세스 종료

```bash
# PID로 종료
pkill -f "yb-discover.py"
pkill -f "raspbot.pyc"

# 또는 서비스 중지
sudo systemctl stop raspbot.service
```

---

## 📌 참고사항

- Raspberry Pi를 재부팅하면 자동으로 서비스가 시작됩니다
- 네트워크가 준비된 후에 서비스가 시작됩니다
- 서비스가 실패하면 5초 후 자동으로 재시작됩니다
- UDP 서버는 포트 8000에서 실행됩니다

