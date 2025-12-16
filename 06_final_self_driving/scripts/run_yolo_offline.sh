#!/bin/bash
# YOLO Final Autoplot 실행 스크립트 (오프라인 모드)
# Run YOLO autoplot in offline mode (no internet required)

echo "=================================================="
echo "  YOLO11 + Haar Cascade Autoplot Start"
echo "  (Offline Mode - No Internet Required)"
echo "=================================================="

# Qt 플랫폼 설정
export QT_QPA_PLATFORM=xcb

# YOLO 오프라인 설정
export YOLO_OFFLINE=1
export YOLO_VERBOSE=False

# PyTorch 오프라인 설정
export TORCH_HOME=./models
export HF_HUB_OFFLINE=1

# Display 확인 및 설정
if [ -z "$DISPLAY" ]; then
    echo "⚠️  Warning: DISPLAY not set"
    echo "   Setting DISPLAY=:0 (local monitor)"
    export DISPLAY=:0
else
    echo "✅ DISPLAY is set: $DISPLAY"
fi

# 스크립트 경로로 이동
cd "$(dirname "$0")"

echo ""
echo "🚀 Starting program..."
echo "   - YOLO Offline Mode: ON"
echo "   - Network Access: DISABLED"
echo "   - Using local model only"
echo ""
echo "Press ESC to exit, SPACE to toggle motor"
echo ""

# 파이썬 스크립트 실행
python3 1_yolo_final_autoplot.py

# 종료 코드 확인
EXIT_CODE=$?

echo ""
echo "=================================================="
echo "  Program End (Exit code: $EXIT_CODE)"
echo "=================================================="

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "⚠️  Program exited with error"
    echo ""
    echo "💡 Troubleshooting:"
    echo "   1. Check if model exists: ls -lh models/traffic_modeln.pt"
    echo "   2. Run diagnostics: ./diagnose_camera.sh"
    echo "   3. Check logs above for error messages"
    echo ""
fi

