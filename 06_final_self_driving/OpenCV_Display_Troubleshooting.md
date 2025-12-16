# 🖥️ OpenCV Display Troubleshooting Guide

> Solutions for "cv2.imshow() not working" issues on Raspberry Pi

## 🔍 Common Problem

**Symptom:**
- Script runs without errors
- Detection works (printed in console)
- But window does not appear
- `cv2.imshow()` seems to do nothing

---

## ✅ Quick Fixes

### Fix 1: Check DISPLAY Environment Variable

```bash
# Check if DISPLAY is set
echo $DISPLAY

# If empty or not set, configure it
export DISPLAY=:0

# Then run your script
python3 test_yolo_basic.py
```

### Fix 2: Use X11 Forwarding (SSH Connection)

```bash
# Connect with X11 forwarding
ssh -X pi@raspberrypi.local

# Or with compression for better performance
ssh -XC pi@raspberrypi.local

# Verify DISPLAY is set
echo $DISPLAY
# Should show something like: localhost:10.0

# Run your script
python3 test_yolo_basic.py
```

### Fix 3: Install X11 Dependencies

```bash
# Install required X11 libraries
sudo apt-get update
sudo apt-get install -y libxcb-xinerama0 libxcb-cursor0 libxkbcommon-x11-0

# Install additional Qt dependencies
sudo apt-get install -y libqt5gui5 libqt5core5a qtbase5-dev

# Reboot for changes to take effect
sudo reboot
```

### Fix 4: Set Qt Platform Explicitly

The scripts already include this, but you can also set it manually:

```bash
# For X11 (with monitor)
export QT_QPA_PLATFORM=xcb
python3 test_yolo_basic.py

# For headless (no window, console output only)
export QT_QPA_PLATFORM=offscreen
python3 test_yolo_basic.py
```

---

## 🔧 Environment-Specific Solutions

### 🖥️ Direct Connection (Monitor + Keyboard)

**This should work without any issues.**

```bash
# Just run the script
python3 test_yolo_basic.py
```

If it doesn't work:
1. Check if you're in GUI mode (not console mode)
2. Try: `export DISPLAY=:0`
3. Restart the desktop: `sudo systemctl restart lightdm`

---

### 🌐 SSH Connection (Remote)

**Method 1: X11 Forwarding (Recommended)**

```bash
# On your local machine (Mac/Linux)
ssh -X pi@raspberrypi.local

# On Windows with PuTTY:
# 1. Enable X11 Forwarding in Connection → SSH → X11
# 2. Install Xming or VcXsrv on Windows
# 3. Start Xming before connecting
```

**Method 2: VNC (Alternative)**

```bash
# Enable VNC on Raspberry Pi
sudo raspi-config
# Navigate to: Interface Options → VNC → Enable

# Connect using VNC Viewer from your computer
# Then open terminal in VNC and run scripts
```

---

### 🔄 VNC Connection

**This usually works perfectly.**

```bash
# Connect via VNC Viewer
# Open terminal in VNC session
python3 test_yolo_basic.py
```

---

## 🐛 Advanced Debugging

### Check OpenCV Build Information

```python
import cv2
print(cv2.getBuildInformation())
```

Look for:
- **GUI:** Should show `GTK` or `QT`
- **Video I/O:** Should show `V4L/V4L2`

### Test Minimal OpenCV Window

Create a test script to isolate the issue:

```python
#!/usr/bin/env python3
import cv2
import numpy as np
import os

print(f"DISPLAY: {os.environ.get('DISPLAY', 'NOT SET')}")
print(f"OpenCV version: {cv2.__version__}")

# Create test image
img = np.zeros((480, 640, 3), dtype=np.uint8)
cv2.putText(img, "Test Window", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

# Try to display
try:
    cv2.namedWindow("Test", cv2.WINDOW_NORMAL)
    cv2.imshow("Test", img)
    print("✅ Window created successfully")
    print("⏳ Press any key to close...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    print("✅ Test passed!")
except Exception as e:
    print(f"❌ Error: {e}")
```

Save as `test_opencv_display.py` and run:

```bash
python3 test_opencv_display.py
```

---

## 📝 Environment Variable Reference

### Permanent Configuration

Add to `~/.bashrc` to make permanent:

```bash
# For X11
echo 'export DISPLAY=:0' >> ~/.bashrc
echo 'export QT_QPA_PLATFORM=xcb' >> ~/.bashrc

# Reload
source ~/.bashrc
```

### Temporary Configuration

For single session only:

```bash
export DISPLAY=:0
export QT_QPA_PLATFORM=xcb
```

---

## 🎯 Testing Checklist

Use this checklist to verify your setup:

- [ ] **Step 1**: Check DISPLAY variable
  ```bash
  echo $DISPLAY
  # Should NOT be empty
  ```

- [ ] **Step 2**: Test basic OpenCV
  ```bash
  python3 test_opencv_display.py
  ```

- [ ] **Step 3**: Check camera access
  ```bash
  ls -la /dev/video*
  # Should show /dev/video0
  ```

- [ ] **Step 4**: Test with minimal script
  ```python
  import cv2
  cap = cv2.VideoCapture(0)
  ret, frame = cap.read()
  if ret:
      cv2.imshow("Test", frame)
      cv2.waitKey(3000)
  cap.release()
  cv2.destroyAllWindows()
  ```

- [ ] **Step 5**: Run full test
  ```bash
  python3 test_yolo_basic.py
  ```

---

## 🆘 Still Not Working?

### Last Resort Solutions

**1. Reinstall OpenCV with GUI support:**

```bash
pip3 uninstall opencv-python opencv-python-headless
pip3 install opencv-contrib-python
```

**2. Use alternative display method (save frames):**

Modify the script to save frames instead of displaying:

```python
# Instead of cv2.imshow()
cv2.imwrite(f"frame_{frame_count}.jpg", annotated_frame)
```

**3. Use framebuffer display (no X11):**

```bash
export QT_QPA_PLATFORM=linuxfb
python3 test_yolo_basic.py
```

---

## 📊 Performance Tips

Once display is working, optimize performance:

```python
# Reduce inference frequency
if frame_count % 10 == 0:  # Only process every 10th frame
    results = model(frame, conf=0.5, verbose=False)

# Reduce image size
frame_resized = cv2.resize(frame, (320, 240))
results = model(frame_resized, ...)

# Lower confidence threshold
results = model(frame, conf=0.3, verbose=False)
```

---

## 🔍 Common Error Messages

### Error: "Could not initialize video system: No available video device"

**Solution:**
```bash
export SDL_VIDEODRIVER=dummy
python3 test_yolo_basic.py
```

### Error: "qt.qpa.plugin: Could not load the Qt platform plugin"

**Solution:**
```bash
export QT_QPA_PLATFORM=xcb
# Or
export QT_QPA_PLATFORM=offscreen
```

### Error: "Unable to init server: Could not connect: Connection refused"

**Solution:**
```bash
# Grant X11 access
xhost +local:
export DISPLAY=:0
```

---

## ✅ Verification Script

Run this complete verification script:

```bash
#!/bin/bash
echo "=== OpenCV Display Environment Check ==="
echo ""
echo "1. DISPLAY variable:"
echo "   DISPLAY=$DISPLAY"
echo ""
echo "2. X11 socket:"
ls -la /tmp/.X11-unix/ 2>/dev/null || echo "   Not found"
echo ""
echo "3. Video devices:"
ls -la /dev/video* 2>/dev/null || echo "   Not found"
echo ""
echo "4. Qt platform:"
echo "   QT_QPA_PLATFORM=$QT_QPA_PLATFORM"
echo ""
echo "5. Python packages:"
python3 -c "import cv2; print(f'   OpenCV: {cv2.__version__}')" 2>/dev/null || echo "   OpenCV not installed"
python3 -c "import ultralytics; print(f'   Ultralytics: {ultralytics.__version__}')" 2>/dev/null || echo "   Ultralytics not installed"
echo ""
echo "=== End of Check ==="
```

Save as `check_display_env.sh`, make executable, and run:

```bash
chmod +x check_display_env.sh
./check_display_env.sh
```

---

**Document Version:** v1.0  
**Last Updated:** 2025-12-16  
**Author:** Raspbot v2 Development Team

