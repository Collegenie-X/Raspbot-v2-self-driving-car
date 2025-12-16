#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
카메라 연결 테스트 스크립트
Camera Connection Test Script
"""

import cv2
import sys

print("=" * 60)
print("  Camera Connection Test")
print("=" * 60)

# 여러 카메라 인덱스 시도
camera_indices = [0, 1, 2, -1]
found_cameras = []

for idx in camera_indices:
    print(f"\n[Test {idx}] Trying camera index: {idx}")
    try:
        cap = cv2.VideoCapture(idx)
        
        if cap.isOpened():
            ret, frame = cap.read()
            
            if ret and frame is not None:
                h, w = frame.shape[:2]
                print(f"✅ SUCCESS! Camera {idx} is working")
                print(f"   - Resolution: {w}x{h}")
                print(f"   - Frame shape: {frame.shape}")
                found_cameras.append(idx)
                
                # 테스트 이미지 저장
                filename = f"test_camera_{idx}.jpg"
                cv2.imwrite(filename, frame)
                print(f"   - Test image saved: {filename}")
            else:
                print(f"⚠️  Camera {idx} opened but cannot read frame")
            
            cap.release()
        else:
            print(f"❌ Camera {idx} cannot be opened")
            
    except Exception as e:
        print(f"❌ Error with camera {idx}: {e}")

print("\n" + "=" * 60)
print("  Test Summary")
print("=" * 60)

if found_cameras:
    print(f"✅ Found {len(found_cameras)} working camera(s): {found_cameras}")
    print(f"\n💡 Recommended: Use camera index {found_cameras[0]}")
    print(f"\n📝 Update 1_yolo_final_autoplot.py:")
    print(f"   cap = cv2.VideoCapture({found_cameras[0]})")
else:
    print("❌ No working cameras found!")
    print("\n🔍 Troubleshooting steps:")
    print("   1. Check if camera is connected:")
    print("      ls -la /dev/video*")
    print("   2. Check camera permissions:")
    print("      sudo usermod -aG video $USER")
    print("   3. Check if camera is used by another process:")
    print("      sudo lsof /dev/video0")
    print("   4. Reboot Raspberry Pi:")
    print("      sudo reboot")

print("=" * 60)

sys.exit(0 if found_cameras else 1)

