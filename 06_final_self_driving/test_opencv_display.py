#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple OpenCV Display Test
Quick test to verify cv2.imshow() is working

Usage:
    python3 test_opencv_display.py
"""

import sys
import os

print("=" * 70)
print("  OpenCV Display Test")
print("=" * 70)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test 1: Environment Check
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[Test 1] Environment Check")
print("-" * 70)

display = os.environ.get('DISPLAY')
if display:
    print(f"✅ DISPLAY is set: {display}")
else:
    print(f"⚠️  DISPLAY is NOT set")
    print(f"   Tip: Run 'export DISPLAY=:0' first")

qt_platform = os.environ.get('QT_QPA_PLATFORM')
if qt_platform:
    print(f"✅ QT_QPA_PLATFORM is set: {qt_platform}")
else:
    print(f"ℹ️  QT_QPA_PLATFORM not set (will use default)")
    # Set it now
    os.environ["QT_QPA_PLATFORM"] = "xcb"
    print(f"   → Setting to 'xcb'")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test 2: Import OpenCV
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[Test 2] Import OpenCV")
print("-" * 70)

try:
    import cv2
    print(f"✅ OpenCV imported successfully")
    print(f"   Version: {cv2.__version__}")
except ImportError as e:
    print(f"❌ Cannot import OpenCV: {e}")
    sys.exit(1)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test 3: Create Test Image
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[Test 3] Create Test Image")
print("-" * 70)

try:
    import numpy as np
    
    # Create colorful test image
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Draw colored rectangles
    cv2.rectangle(img, (50, 50), (200, 150), (0, 0, 255), -1)  # Red
    cv2.rectangle(img, (220, 50), (370, 150), (0, 255, 0), -1)  # Green
    cv2.rectangle(img, (390, 50), (540, 150), (255, 0, 0), -1)  # Blue
    
    # Add text
    cv2.putText(img, "OpenCV Display Test", (150, 250), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(img, "If you see this window,", (150, 300), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(img, "cv2.imshow() is working!", (150, 330), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(img, "Press any key to continue...", (130, 400), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    
    print(f"✅ Test image created (640x480)")
except Exception as e:
    print(f"❌ Failed to create test image: {e}")
    sys.exit(1)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test 4: Display Window
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[Test 4] Display Window")
print("-" * 70)

window_name = "OpenCV Display Test"

try:
    print(f"🔄 Creating window...")
    
    # Create named window with specific flags
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 640, 480)
    
    print(f"✅ Window created: '{window_name}'")
    print(f"\n💡 Check if window appeared on your screen!")
    print(f"   → If yes: Press any key in the window")
    print(f"   → If no: See troubleshooting below")
    
    # Display the image
    cv2.imshow(window_name, img)
    
    print(f"\n⏳ Waiting for key press (or timeout in 10 seconds)...")
    key = cv2.waitKey(10000)  # Wait 10 seconds
    
    if key == -1:
        print(f"\n⏰ Timeout (no key pressed)")
        print(f"   → Window might not be visible")
    else:
        print(f"\n✅ Key pressed! Window is working correctly!")
    
    cv2.destroyAllWindows()
    
except Exception as e:
    print(f"❌ Failed to display window: {e}")
    print(f"\n💡 Troubleshooting:")
    print(f"   1. Check DISPLAY: echo $DISPLAY")
    print(f"   2. If SSH: Use 'ssh -X' for X11 forwarding")
    print(f"   3. Try: export QT_QPA_PLATFORM=xcb")
    print(f"   4. Install: sudo apt-get install libxcb-xinerama0")
    sys.exit(1)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test 5: Camera Test (Optional)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[Test 5] Camera Test (Optional)")
print("-" * 70)

user_input = input("Test camera display? (y/N): ").strip().lower()

if user_input == "y":
    try:
        print(f"\n🔄 Opening camera...")
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print(f"❌ Cannot open camera")
        else:
            print(f"✅ Camera opened successfully")
            print(f"\n📹 Displaying live camera feed...")
            print(f"   Press ESC or 'q' to quit")
            
            # Create window
            camera_window = "Camera Test"
            cv2.namedWindow(camera_window, cv2.WINDOW_NORMAL)
            
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    print(f"❌ Cannot read frame")
                    break
                
                frame_count += 1
                
                # Add frame counter
                cv2.putText(frame, f"Frame: {frame_count}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(frame, "Press 'q' to quit", (10, 70),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                
                # Display
                try:
                    cv2.imshow(camera_window, frame)
                except Exception as e:
                    print(f"❌ Cannot display frame: {e}")
                    break
                
                # Check for quit
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:
                    print(f"\n🛑 User quit")
                    break
            
            cap.release()
            cv2.destroyAllWindows()
            
            print(f"✅ Camera test completed ({frame_count} frames)")
    
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
else:
    print(f"⏭️  Camera test skipped")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Final Results
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n" + "=" * 70)
print("  Test Summary")
print("=" * 70)
print("\n✨ Results:")
print("  1. ✅ Environment checked")
print("  2. ✅ OpenCV imported")
print("  3. ✅ Test image created")
print("  4. ✅ Window display attempted")

if user_input == "y":
    print("  5. ✅ Camera test completed")

print("\n💡 Next Steps:")
print("  - If window appeared: cv2.imshow() is working! ✅")
print("  - If window did NOT appear: See OpenCV_Display_Troubleshooting.md")
print("  - Ready to test YOLO: python3 test_yolo_basic.py")
print("\n" + "=" * 70)

