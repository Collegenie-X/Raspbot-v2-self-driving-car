#!/bin/bash

# ==========================================
# 자동 시작 비활성화 스크립트
# ==========================================
# 모든 Raspbot 및 Jupyter 자동 시작을 비활성화합니다.
# lsof -i :8000
# lsof -i :8888
# kill PID

### 실행 방법 
### sudo chmod +x ./stop_autostart.sh 
### ./stop_autostart.sh

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================="
echo "자동 시작 비활성화 스크립트"
echo -e "===================================${NC}"
echo ""

# ==========================================
# 1. systemd 서비스 비활성화
# ==========================================
echo -e "${YELLOW}[1/5] systemd 서비스 비활성화${NC}"

# jupyter.service 비활성화
if systemctl is-active --quiet jupyter.service; then
    echo -e "  ${BLUE}→ jupyter.service 중지 중...${NC}"
    sudo systemctl stop jupyter.service
fi

if systemctl is-enabled --quiet jupyter.service 2>/dev/null; then
    echo -e "  ${BLUE}→ jupyter.service 자동 시작 비활성화 중...${NC}"
    sudo systemctl disable jupyter.service
    echo -e "  ${GREEN}✓ jupyter.service 비활성화 완료${NC}"
else
    echo -e "  ${YELLOW}⚠ jupyter.service가 없거나 이미 비활성화됨${NC}"
fi

# raspbot.service 비활성화
if systemctl is-active --quiet raspbot.service 2>/dev/null; then
    echo -e "  ${BLUE}→ raspbot.service 중지 중...${NC}"
    sudo systemctl stop raspbot.service
fi

if systemctl is-enabled --quiet raspbot.service 2>/dev/null; then
    echo -e "  ${BLUE}→ raspbot.service 자동 시작 비활성화 중...${NC}"
    sudo systemctl disable raspbot.service
    echo -e "  ${GREEN}✓ raspbot.service 비활성화 완료${NC}"
else
    echo -e "  ${YELLOW}⚠ raspbot.service가 없거나 이미 비활성화됨${NC}"
fi

echo ""

# ==========================================
# 2. 현재 실행 중인 프로세스 종료
# ==========================================
echo -e "${YELLOW}[2/5] 현재 실행 중인 프로세스 종료${NC}"

# jupyter 종료
if pgrep -f "jupyter-lab" > /dev/null; then
    echo -e "  ${BLUE}→ jupyter-lab 종료 중...${NC}"
    pkill -f "jupyter-lab"
    echo -e "  ${GREEN}✓ jupyter-lab 종료 완료${NC}"
else
    echo -e "  ${YELLOW}⚠ jupyter-lab 실행 중이지 않음${NC}"
fi

# raspbot.pyc 종료
if pgrep -f "raspbot.pyc" > /dev/null; then
    echo -e "  ${BLUE}→ raspbot.pyc 종료 중...${NC}"
    pkill -f "raspbot.pyc"
    echo -e "  ${GREEN}✓ raspbot.pyc 종료 완료${NC}"
else
    echo -e "  ${YELLOW}⚠ raspbot.pyc 실행 중이지 않음${NC}"
fi

# yb-discover.py 종료
if pgrep -f "yb-discover.py" > /dev/null; then
    echo -e "  ${BLUE}→ yb-discover.py 종료 중...${NC}"
    pkill -f "yb-discover.py"
    echo -e "  ${GREEN}✓ yb-discover.py 종료 완료${NC}"
else
    echo -e "  ${YELLOW}⚠ yb-discover.py 실행 중이지 않음${NC}"
fi

echo ""

# ==========================================
# 3. autostart 파일 제거
# ==========================================
echo -e "${YELLOW}[3/5] autostart 파일 제거${NC}"

removed=false

# 사용자 autostart 파일 제거
for file in ~/.config/autostart/start_raspbot.desktop \
            ~/.config/autostart/raspbot*.desktop \
            ~/.config/autostart/jupyter*.desktop; do
    if [ -f "$file" ]; then
        echo -e "  ${BLUE}→ 제거: $file${NC}"
        rm "$file"
        removed=true
    fi
done

# 전역 autostart 파일 제거
for file in /etc/xdg/autostart/raspbot*.desktop \
            /etc/xdg/autostart/jupyter*.desktop; do
    if [ -f "$file" ]; then
        echo -e "  ${BLUE}→ 제거: $file${NC}"
        sudo rm "$file"
        removed=true
    fi
done

if [ "$removed" = false ]; then
    echo -e "  ${YELLOW}⚠ autostart 파일이 없음${NC}"
else
    echo -e "  ${GREEN}✓ autostart 파일 제거 완료${NC}"
fi

echo ""

# ==========================================
# 4. cron 작업 확인
# ==========================================
echo -e "${YELLOW}[4/5] cron 작업 확인${NC}"

if crontab -l 2>/dev/null | grep -E "@reboot.*(jupyter|raspbot|yb-discover)" > /dev/null; then
    echo -e "  ${RED}⚠ cron에 자동 시작 설정이 있습니다!${NC}"
    echo -e "  ${YELLOW}  다음 명령어로 수동으로 제거하세요:${NC}"
    echo -e "  ${BLUE}  crontab -e${NC}"
    echo ""
    echo -e "  ${YELLOW}  @reboot로 시작하는 다음 줄을 삭제하거나 주석 처리:${NC}"
    crontab -l | grep -E "@reboot.*(jupyter|raspbot|yb-discover)" | sed 's/^/  /'
else
    echo -e "  ${GREEN}✓ cron에 자동 시작 설정 없음${NC}"
fi

echo ""

# ==========================================
# 5. 확인
# ==========================================
echo -e "${YELLOW}[5/5] 현재 상태 확인${NC}"
echo ""

# jupyter.service 상태
echo -e "${BLUE}→ jupyter.service 상태:${NC}"
if systemctl is-enabled --quiet jupyter.service 2>/dev/null; then
    echo -e "  ${RED}✗ 활성화됨 (자동 시작됨)${NC}"
else
    echo -e "  ${GREEN}✓ 비활성화됨 (자동 시작 안 됨)${NC}"
fi

# raspbot.service 상태
echo -e "${BLUE}→ raspbot.service 상태:${NC}"
if systemctl is-enabled --quiet raspbot.service 2>/dev/null; then
    echo -e "  ${RED}✗ 활성화됨 (자동 시작됨)${NC}"
else
    echo -e "  ${GREEN}✓ 비활성화됨 (자동 시작 안 됨)${NC}"
fi

echo ""

# 실행 중인 프로세스 확인
echo -e "${BLUE}→ 실행 중인 프로세스:${NC}"
if ps aux | grep -E "jupyter|raspbot|yb-discover" | grep -v grep > /dev/null; then
    echo -e "  ${YELLOW}⚠ 아직 실행 중인 프로세스가 있습니다:${NC}"
    ps aux | grep -E "jupyter|raspbot|yb-discover" | grep -v grep | awk '{print "  " $11}' | head -n 5
else
    echo -e "  ${GREEN}✓ 실행 중인 프로세스 없음${NC}"
fi

echo ""

# 포트 사용 확인
echo -e "${BLUE}→ 포트 사용 확인:${NC}"

if lsof -i :8888 2>/dev/null | grep -q LISTEN; then
    echo -e "  ${YELLOW}⚠ 포트 8888 사용 중${NC}"
    lsof -i :8888 | grep LISTEN | awk '{print "  " $1 " (PID: " $2 ")"}'
else
    echo -e "  ${GREEN}✓ 포트 8888 사용 안 함${NC}"
fi

if lsof -i :8000 2>/dev/null > /dev/null; then
    echo -e "  ${YELLOW}⚠ 포트 8000 사용 중${NC}"
    lsof -i :8000 | grep -v COMMAND | awk '{print "  " $1 " (PID: " $2 ")"}'
else
    echo -e "  ${GREEN}✓ 포트 8000 사용 안 함${NC}"
fi

echo ""
echo -e "${BLUE}==================================="
echo "완료!"
echo -e "===================================${NC}"
echo ""
echo -e "${YELLOW}다음 단계:${NC}"
echo -e "1. ${BLUE}재부팅${NC}하여 설정을 완전히 적용하세요:"
echo -e "   ${GREEN}sudo reboot${NC}"
echo ""
echo -e "2. 재부팅 후 다음 명령어로 확인:"
echo -e "   ${GREEN}ps aux | grep -E 'jupyter|raspbot' | grep -v grep${NC}"
echo -e "   ${GREEN}lsof -i :8888${NC}"
echo -e "   ${GREEN}lsof -i :8000${NC}"
echo ""
echo -e "${YELLOW}참고:${NC} cron에 자동 시작 설정이 있다면 수동으로 제거해야 합니다."
echo ""

