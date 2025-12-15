#!/bin/bash

# ==========================================
# 자동 시작 활성화 스크립트
# ==========================================
# Raspbot 및 Jupyter 자동 시작을 활성화합니다.

### 실행 방법 
### sudo chmod +x ./start_autostart.sh 
### ./start_autostart.sh

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================="
echo "자동 시작 활성화 스크립트"
echo -e "===================================${NC}"
echo ""

# ==========================================
# 1. systemd 서비스 활성화
# ==========================================
echo -e "${YELLOW}[1/4] systemd 서비스 활성화${NC}"

# jupyter.service 활성화
if systemctl list-unit-files | grep -q "jupyter.service"; then
    echo -e "  ${BLUE}→ jupyter.service 활성화 중...${NC}"
    sudo systemctl enable jupyter.service
    sudo systemctl start jupyter.service
    
    if systemctl is-active --quiet jupyter.service; then
        echo -e "  ${GREEN}✓ jupyter.service 활성화 및 시작 완료${NC}"
    else
        echo -e "  ${YELLOW}⚠ jupyter.service 시작 실패 (로그 확인 필요)${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠ jupyter.service 파일이 없습니다${NC}"
    echo -e "  ${BLUE}  수동으로 Jupyter를 설치하거나 서비스 파일을 생성하세요${NC}"
fi

echo ""

# raspbot.service 활성화
RASPBOT_SERVICE="/home/pi/project_demo/raspbot/raspbot.service"
if [ -f "$RASPBOT_SERVICE" ]; then
    echo -e "  ${BLUE}→ raspbot.service 설치 및 활성화 중...${NC}"
    
    # 서비스 파일 복사
    sudo cp "$RASPBOT_SERVICE" /etc/systemd/system/
    sudo chmod 644 /etc/systemd/system/raspbot.service
    
    # systemd 데몬 리로드
    sudo systemctl daemon-reload
    
    # 서비스 활성화 및 시작
    sudo systemctl enable raspbot.service
    sudo systemctl start raspbot.service
    
    if systemctl is-active --quiet raspbot.service; then
        echo -e "  ${GREEN}✓ raspbot.service 활성화 및 시작 완료${NC}"
    else
        echo -e "  ${YELLOW}⚠ raspbot.service 시작 실패 (로그 확인 필요)${NC}"
        echo -e "  ${BLUE}  확인: sudo journalctl -u raspbot.service -n 20${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠ raspbot.service 파일을 찾을 수 없습니다${NC}"
    echo -e "  ${BLUE}  경로: $RASPBOT_SERVICE${NC}"
fi

echo ""

# ==========================================
# 2. autostart 파일 복원
# ==========================================
echo -e "${YELLOW}[2/4] autostart 파일 복원${NC}"

# autostart 디렉토리 생성
mkdir -p ~/.config/autostart

# raspbot autostart 파일 복원
RASPBOT_DESKTOP="/home/pi/project_demo/raspbot/start_raspbot.desktop"
if [ -f "$RASPBOT_DESKTOP" ]; then
    echo -e "  ${BLUE}→ raspbot autostart 파일 복사 중...${NC}"
    cp "$RASPBOT_DESKTOP" ~/.config/autostart/
    chmod +x ~/.config/autostart/start_raspbot.desktop
    echo -e "  ${GREEN}✓ raspbot autostart 파일 복원 완료${NC}"
else
    echo -e "  ${YELLOW}⚠ raspbot desktop 파일을 찾을 수 없습니다${NC}"
    echo -e "  ${BLUE}  경로: $RASPBOT_DESKTOP${NC}"
fi

echo ""

# ==========================================
# 3. 서비스 시작 확인
# ==========================================
echo -e "${YELLOW}[3/4] 서비스 시작 확인${NC}"

# 스크립트 실행 권한 확인
RASPBOT_START="/home/pi/project_demo/raspbot/raspbot_start.sh"
if [ -f "$RASPBOT_START" ]; then
    echo -e "  ${BLUE}→ 시작 스크립트 권한 설정 중...${NC}"
    chmod +x "$RASPBOT_START"
    echo -e "  ${GREEN}✓ 시작 스크립트 권한 설정 완료${NC}"
fi

echo ""

# ==========================================
# 4. 현재 상태 확인
# ==========================================
echo -e "${YELLOW}[4/4] 현재 상태 확인${NC}"
echo ""

# jupyter.service 상태
echo -e "${BLUE}→ jupyter.service 상태:${NC}"
if systemctl is-enabled --quiet jupyter.service 2>/dev/null; then
    echo -e "  ${GREEN}✓ 활성화됨 (부팅 시 자동 시작)${NC}"
    if systemctl is-active --quiet jupyter.service; then
        echo -e "  ${GREEN}✓ 현재 실행 중${NC}"
    else
        echo -e "  ${YELLOW}⚠ 현재 중지됨${NC}"
    fi
else
    echo -e "  ${RED}✗ 비활성화됨${NC}"
fi

# raspbot.service 상태
echo -e "${BLUE}→ raspbot.service 상태:${NC}"
if systemctl is-enabled --quiet raspbot.service 2>/dev/null; then
    echo -e "  ${GREEN}✓ 활성화됨 (부팅 시 자동 시작)${NC}"
    if systemctl is-active --quiet raspbot.service; then
        echo -e "  ${GREEN}✓ 현재 실행 중${NC}"
    else
        echo -e "  ${YELLOW}⚠ 현재 중지됨${NC}"
    fi
else
    echo -e "  ${RED}✗ 비활성화됨${NC}"
fi

echo ""

# autostart 파일 확인
echo -e "${BLUE}→ autostart 파일:${NC}"
if [ -f ~/.config/autostart/start_raspbot.desktop ]; then
    echo -e "  ${GREEN}✓ raspbot autostart 파일 존재${NC}"
else
    echo -e "  ${RED}✗ raspbot autostart 파일 없음${NC}"
fi

echo ""

# 실행 중인 프로세스 확인
echo -e "${BLUE}→ 실행 중인 프로세스:${NC}"

if pgrep -f "jupyter-lab" > /dev/null; then
    jupyter_pid=$(pgrep -f "jupyter-lab")
    echo -e "  ${GREEN}✓ jupyter-lab 실행 중 (PID: $jupyter_pid)${NC}"
else
    echo -e "  ${YELLOW}⚠ jupyter-lab 실행 중이지 않음${NC}"
fi

if pgrep -f "raspbot.pyc" > /dev/null; then
    raspbot_pid=$(pgrep -f "raspbot.pyc")
    echo -e "  ${GREEN}✓ raspbot.pyc 실행 중 (PID: $raspbot_pid)${NC}"
else
    echo -e "  ${YELLOW}⚠ raspbot.pyc 실행 중이지 않음${NC}"
fi

if pgrep -f "yb-discover.py" > /dev/null; then
    yb_pid=$(pgrep -f "yb-discover.py")
    echo -e "  ${GREEN}✓ yb-discover.py 실행 중 (PID: $yb_pid)${NC}"
else
    echo -e "  ${YELLOW}⚠ yb-discover.py 실행 중이지 않음${NC}"
fi

echo ""

# 포트 사용 확인
echo -e "${BLUE}→ 포트 사용 확인:${NC}"

if lsof -i :8888 2>/dev/null | grep -q LISTEN; then
    echo -e "  ${GREEN}✓ 포트 8888 사용 중 (Jupyter)${NC}"
    lsof -i :8888 | grep LISTEN | awk '{print "  " $1 " (PID: " $2 ")"}'
else
    echo -e "  ${YELLOW}⚠ 포트 8888 사용 안 함${NC}"
fi

if lsof -i :8000 2>/dev/null > /dev/null; then
    echo -e "  ${GREEN}✓ 포트 8000 사용 중 (yb-discover)${NC}"
    lsof -i :8000 | grep -v COMMAND | awk '{print "  " $1 " (PID: " $2 ")"}'
else
    echo -e "  ${YELLOW}⚠ 포트 8000 사용 안 함${NC}"
fi

echo ""
echo -e "${BLUE}==================================="
echo "완료!"
echo -e "===================================${NC}"
echo ""
echo -e "${YELLOW}다음 단계:${NC}"
echo ""
echo -e "1. ${BLUE}서비스가 제대로 시작되었는지 확인:${NC}"
echo -e "   ${GREEN}sudo systemctl status raspbot.service${NC}"
echo -e "   ${GREEN}sudo systemctl status jupyter.service${NC}"
echo ""
echo -e "2. ${BLUE}재부팅하여 자동 시작 테스트:${NC}"
echo -e "   ${GREEN}sudo reboot${NC}"
echo ""
echo -e "3. ${BLUE}재부팅 후 확인:${NC}"
echo -e "   ${GREEN}ps aux | grep -E 'jupyter|raspbot' | grep -v grep${NC}"
echo -e "   ${GREEN}lsof -i :8888${NC}"
echo -e "   ${GREEN}lsof -i :8000${NC}"
echo ""
echo -e "${GREEN}참고:${NC} 부팅 시 자동으로 시작됩니다!"
echo ""

# ==========================================
# 추가 정보
# ==========================================
echo -e "${BLUE}=== 추가 정보 ===${NC}"
echo ""
echo -e "${YELLOW}Jupyter Lab 접속:${NC}"
echo -e "  브라우저에서: ${GREEN}http://라즈베리파이IP:8888${NC}"
echo -e "  토큰 확인: ${GREEN}jupyter lab list${NC}"
echo ""
echo -e "${YELLOW}서비스 제어:${NC}"
echo -e "  시작: ${GREEN}sudo systemctl start raspbot.service${NC}"
echo -e "  중지: ${GREEN}sudo systemctl stop raspbot.service${NC}"
echo -e "  상태: ${GREEN}sudo systemctl status raspbot.service${NC}"
echo ""
echo -e "${YELLOW}로그 확인:${NC}"
echo -e "  ${GREEN}sudo journalctl -u raspbot.service -f${NC}"
echo -e "  ${GREEN}sudo journalctl -u jupyter.service -f${NC}"
echo ""

