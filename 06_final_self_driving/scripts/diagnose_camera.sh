#!/bin/bash
# 카메라 진단 스크립트
# Camera Diagnostic Script

echo "=================================================="
echo "  Camera Diagnostic Tool"
echo "=================================================="

# 1. 카메라 장치 확인
echo ""
echo "[1] Checking camera devices..."
if ls /dev/video* 1> /dev/null 2>&1; then
    echo "✅ Camera devices found:"
    ls -la /dev/video*
else
    echo "❌ No camera devices found at /dev/video*"
    echo "   → Please check if camera is connected"
fi

# 2. V4L2 정보 확인
echo ""
echo "[2] Checking V4L2 camera information..."
if command -v v4l2-ctl &> /dev/null; then
    v4l2-ctl --list-devices
else
    echo "⚠️  v4l2-ctl not installed"
    echo "   Install with: sudo apt-get install v4l-utils"
fi

# 3. USB 카메라 확인
echo ""
echo "[3] Checking USB devices..."
if command -v lsusb &> /dev/null; then
    echo "All USB devices:"
    lsusb
    echo ""
    echo "Camera-related devices:"
    lsusb | grep -iE 'camera|webcam|video' || echo "   → No camera devices found in USB list"
else
    echo "⚠️  lsusb not installed"
fi

# 4. 카메라 사용 프로세스 확인
echo ""
echo "[4] Checking processes using camera..."
if command -v lsof &> /dev/null; then
    if [ -e /dev/video0 ]; then
        PROCESSES=$(sudo lsof /dev/video0 2>/dev/null)
        if [ -z "$PROCESSES" ]; then
            echo "✅ No process is using /dev/video0"
        else
            echo "⚠️  Processes using /dev/video0:"
            echo "$PROCESSES"
        fi
    else
        echo "⚠️  /dev/video0 not found"
    fi
else
    echo "⚠️  lsof not installed"
    echo "   Install with: sudo apt-get install lsof"
fi

# 5. 현재 사용자 권한 확인
echo ""
echo "[5] Checking user permissions..."
CURRENT_USER=$(whoami)
echo "Current user: $CURRENT_USER"

if groups | grep -q video; then
    echo "✅ User is in 'video' group"
else
    echo "❌ User is NOT in 'video' group"
    echo "   Fix with: sudo usermod -aG video $CURRENT_USER"
    echo "   Then logout/login or reboot"
fi

# 6. Python 카메라 테스트
echo ""
echo "[6] Testing camera with Python..."
if command -v python3 &> /dev/null; then
    python3 test_camera.py
else
    echo "❌ python3 not found"
fi

echo ""
echo "=================================================="
echo "  Diagnostic Complete"
echo "=================================================="
echo ""
echo "📝 Quick Fix Commands:"
echo "   1. Add user to video group:"
echo "      sudo usermod -aG video \$USER"
echo "      sudo reboot"
echo ""
echo "   2. Kill processes using camera:"
echo "      sudo lsof /dev/video0"
echo "      sudo kill -9 <PID>"
echo ""
echo "   3. Install required tools:"
echo "      sudo apt-get install -y v4l-utils lsof"
echo ""
echo "   4. Test camera manually:"
echo "      python3 test_camera.py"
echo "=================================================="

