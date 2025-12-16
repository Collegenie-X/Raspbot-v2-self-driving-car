#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLO11 Basic Installation and Operation Test Script
Simple test to verify library is working correctly

Test Sequence:
1. Check Ultralytics package import
2. Verify YOLO11 model loading
3. Test inference with dummy image
4. (Optional) Real-time camera test

Usage:
    python3 test_yolo_basic.py
    export QT_QPA_PLATFORM=xcb && python3 test_yolo_basic.py
"""

import sys
import os

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Qt Platform Plugin Error Prevention (Raspberry Pi)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
os.environ["QT_QPA_PLATFORM"] = "xcb"  # Use X11
# For headless environment: os.environ["QT_QPA_PLATFORM"] = "offscreen"

print("=" * 70)
print("  YOLO11 Basic Operation Test")
print("=" * 70)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test 1: Verify Ultralytics Package Installation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[Test 1] Check Ultralytics Package Import")
print("-" * 70)

try:
    import ultralytics

    print(f"✅ Ultralytics installation confirmed")
    print(f"   Version: {ultralytics.__version__}")
except ImportError as e:
    print(f"❌ Ultralytics is not installed")
    print(f"   Error: {e}")
    print(f"\n📦 Installation method:")
    print(f"   pip3 install ultralytics")
    print(f"\n   Or (offline environment)")
    print(f"   pip3 install ultralytics --no-deps")
    print(f"   pip3 install torch torchvision opencv-python pillow pyyaml")
    sys.exit(1)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test 2: Check Required Modules
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[Test 2] Check Required Modules")
print("-" * 70)

required_modules = {
    "torch": "PyTorch",
    "cv2": "OpenCV",
    "numpy": "NumPy",
    "PIL": "Pillow",
}

all_ok = True
for module_name, display_name in required_modules.items():
    try:
        if module_name == "cv2":
            import cv2

            print(f"✅ {display_name}: {cv2.__version__}")
        elif module_name == "torch":
            import torch

            print(f"✅ {display_name}: {torch.__version__}")
        elif module_name == "numpy":
            import numpy

            print(f"✅ {display_name}: {numpy.__version__}")
        elif module_name == "PIL":
            import PIL

            print(f"✅ {display_name}: {PIL.__version__}")
    except ImportError:
        print(f"❌ {display_name}: Not installed")
        all_ok = False

if not all_ok:
    print(f"\n⚠️  Some modules are not installed.")
    print(f"   However, YOLO basic test will continue...\n")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test 3: YOLO Model Loading Test (Pretrained Model)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[Test 3] YOLO Model Loading Test")
print("-" * 70)

try:
    from ultralytics import YOLO

    print("🔄 Downloading and loading YOLO11n model...")
    print("   (First run: auto-download from internet, takes ~10-30 seconds)")

    # Test with smallest model (yolo11n.pt)
    model = YOLO("./models/yolo11n.pt")

    print("✅ YOLO11 model loaded successfully!")
    print(f"   Model name: {model.model.yaml.get('model_name', 'yolo11n')}")
    print(f"   Task: {model.task}")

except Exception as e:
    print(f"❌ YOLO model loading failed")
    print(f"   Error: {e}")
    print(f"\n💡 Solutions:")
    print(f"   1. Check internet connection (model download required on first run)")
    print(f"   2. Reinstall Ultralytics: pip3 install --upgrade ultralytics")
    sys.exit(1)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test 4: Inference Test with Dummy Image
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[Test 4] Inference Test with Dummy Image")
print("-" * 70)

try:
    import numpy as np

    # Generate 640x640 RGB dummy image
    dummy_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

    print("🔄 Running YOLO inference...")
    results = model(dummy_image, verbose=False)

    print("✅ YOLO inference successful!")
    print(f"   Input image: 640x640x3")
    print(f"   Detected objects: {len(results[0].boxes)}")

    # Display detected objects if any
    if len(results[0].boxes) > 0:
        for i, box in enumerate(results[0].boxes):
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            class_name = model.names[class_id]
            print(f"     - Object {i+1}: {class_name} (confidence: {confidence:.2f})")
    else:
        print(f"     (No detection is normal for dummy image)")

except Exception as e:
    print(f"❌ Inference test failed")
    print(f"   Error: {e}")
    sys.exit(1)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test 5: Test with Real Sample Image (if available)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[Test 5] Test with Sample Image")
print("-" * 70)

try:
    import cv2

    # Test with sample image from Ultralytics
    sample_url = "./images/bus.jpg"

    print("🔄 Downloading and inferencing sample image...")
    results = model(sample_url, verbose=False)

    print("✅ Sample image inference successful!")
    print(f"   Detected objects: {len(results[0].boxes)}")

    if len(results[0].boxes) > 0:
        for i, box in enumerate(results[0].boxes):
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            class_name = model.names[class_id]
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            print(f"     - Object {i+1}: {class_name} (confidence: {confidence:.2f})")
            print(
                f"       Position: x1={x1:.0f}, y1={y1:.0f}, x2={x2:.0f}, y2={y2:.0f}"
            )

except Exception as e:
    print(f"⚠️  Sample image test skipped (requires internet connection)")
    print(f"   Error: {e}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test 6: Camera Test (Optional)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[Test 6] Real-time Camera Test (Optional)")
print("-" * 70)

user_input = input("Would you like to test with camera? (y/N): ").strip().lower()

if user_input == "y":
    try:
        import cv2

        print("\n🔄 Initializing camera...")
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("❌ Cannot open camera")
        else:
            print("✅ Camera initialized successfully")

            # Check display environment
            import os

            display = os.environ.get("DISPLAY")
            if not display:
                print("⚠️  Warning: DISPLAY environment variable not set")
                print("   If running via SSH, use: ssh -X user@host")

            print("\nReal-time object detection started (Press ESC or 'q' to quit)")
            print("-" * 70)

            # Create window with specific flags
            window_name = "YOLO11 Camera Test"
            try:
                cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
                cv2.resizeWindow(window_name, 640, 480)
                print("✅ Display window created successfully")
            except Exception as e:
                print(f"⚠️  Warning: Could not create window: {e}")
                print("   Detection will continue, but display may not work")

            frame_count = 0
            detection_count = 0
            last_results = None

            while True:
                ret, frame = cap.read()
                if not ret:
                    print("❌ Cannot read frame")
                    break

                frame_count += 1

                # YOLO inference (every 5 frames for better responsiveness)
                if frame_count % 5 == 0:
                    results = model(frame, conf=0.4, verbose=False)
                    last_results = results

                    # Count detections
                    num_detections = len(results[0].boxes)
                    if num_detections > 0:
                        detection_count += num_detections
                        print(f"Frame {frame_count}: {num_detections} objects detected")

                        # Print detected objects
                        for box in results[0].boxes:
                            class_id = int(box.cls[0])
                            confidence = float(box.conf[0])
                            class_name = model.names[class_id]
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            print(
                                f"  → {class_name} ({confidence:.2f}) at [{x1:.0f},{y1:.0f},{x2:.0f},{y2:.0f}]"
                            )

                # Draw annotations on every frame
                annotated_frame = frame.copy()

                if last_results is not None:
                    # Manually draw boxes and labels for better control
                    for box in last_results[0].boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                        confidence = float(box.conf[0])
                        class_id = int(box.cls[0])
                        class_name = model.names[class_id]

                        # Draw bounding box (GREEN)
                        cv2.rectangle(
                            annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2
                        )

                        # Prepare label
                        label = f"{class_name} {confidence:.2f}"

                        # Draw label background
                        (label_width, label_height), baseline = cv2.getTextSize(
                            label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
                        )
                        cv2.rectangle(
                            annotated_frame,
                            (x1, y1 - label_height - 10),
                            (x1 + label_width, y1),
                            (0, 255, 0),
                            -1,
                        )

                        # Draw label text (BLACK)
                        cv2.putText(
                            annotated_frame,
                            label,
                            (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 0, 0),
                            2,
                        )

                # Display frame info
                cv2.putText(
                    annotated_frame,
                    f"Frame: {frame_count} | Detections: {detection_count}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )

                # Display FPS
                cv2.putText(
                    annotated_frame,
                    "Press 'q' or ESC to quit",
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 0),
                    2,
                )

                # Try to display the frame
                try:
                    cv2.imshow(window_name, annotated_frame)
                except Exception as e:
                    if frame_count == 1:  # Only print error once
                        print(f"⚠️  Cannot display window: {e}")
                        print("   Detection continues in background...")

                key = cv2.waitKey(1) & 0xFF
                if key == 27 or key == ord("q"):  # ESC or 'q'
                    print("\n🛑 User requested quit")
                    break

            cap.release()
            cv2.destroyAllWindows()

            print(f"\n✅ Camera test completed")
            print(f"   Total frames: {frame_count}")
            print(f"   Total detections: {detection_count}")

    except Exception as e:
        print(f"❌ Camera test failed")
        print(f"   Error: {e}")
        import traceback

        traceback.print_exc()
else:
    print("⏭️  Camera test skipped")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Final Results
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n" + "=" * 70)
print("  ✅ YOLO11 Basic Test Completed!")
print("=" * 70)
print("\n✨ Test Results Summary:")
print("  1. ✅ Ultralytics package working properly")
print("  2. ✅ YOLO11 model loaded successfully")
print("  3. ✅ Inference engine working properly")
print("\n💡 Next Steps:")
print("  - Custom model test: python3 test_yolo_model.py")
print("  - Autonomous driving system: python3 1_yolo_final_autoplot.py")
print("=" * 70 + "\n")
