#!/bin/bash
# 헤드리스 모드 실행 스크립트 (GUI 없이 실행)
# Headless mode execution script (Run without GUI)

echo "=================================================="
echo "  YOLO11 + Haar Cascade Autoplot (Headless Mode)"
echo "=================================================="
echo ""
echo "⚠️  Running in HEADLESS mode (No GUI windows)"
echo "   - Best for SSH connections without X11 forwarding"
echo "   - Uses default parameter values"
echo "   - Motor control and detection still active"
echo ""

# Qt 플랫폼 설정
export QT_QPA_PLATFORM=xcb

# Display 확인 및 경고
if [ -z "$DISPLAY" ]; then
    echo "⚠️  Warning: DISPLAY not set"
    echo "   This is normal for headless mode"
fi

# 스크립트 경로로 이동
cd "$(dirname "$0")"

# 헤드리스 모드 설정 파일 생성
echo "Temporarily modifying config for headless mode..."
sed -i.backup 's/^ENABLE_GUI = True/ENABLE_GUI = False/' 1_yolo_final_autoplot.py

# 파이썬 스크립트 실행
echo "Starting program..."
echo ""
python3 1_yolo_final_autoplot.py

# 원래 설정 복원
if [ -f "1_yolo_final_autoplot.py.backup" ]; then
    echo ""
    echo "Restoring original configuration..."
    mv 1_yolo_final_autoplot.py.backup 1_yolo_final_autoplot.py
fi

echo ""
echo "=================================================="
echo "  Program ended"
echo "=================================================="

