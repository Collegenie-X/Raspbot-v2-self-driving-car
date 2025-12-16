#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLO11 Model Test Script
Simple test for traffic light detection using pretrained or custom model

Usage:
    python3 test_yolo_model.py
"""

import cv2
import os
import sys

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Qt Platform Plugin Error Prevention (Raspberry Pi)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
os.environ["QT_QPA_PLATFORM"] = "xcb"  # Use X11
# For headless environment: os.environ["QT_QPA_PLATFORM"] = "offscreen"

try:
    from ultralytics import YOLO

    print("✅ Ultralytics YOLO Loaded Successfully")
except ImportError:
    print("❌ Ultralytics package is not installed")
    print("   Install with: pip install ultralytics")
    exit(1)

# Model path configuration
CUSTOM_MODEL = "./models/traffic_light_yolo11.pt"
PRETRAINED_MODEL = "./models/yolo11n.pt"

print("\n" + "=" * 60)
print("  YOLO11 Model Test")
print("=" * 60)

# Select and load model
if os.path.exists(CUSTOM_MODEL):
    print(f"\n🔍 Custom model found: {CUSTOM_MODEL}")
    model = YOLO(CUSTOM_MODEL)
    model_type = "custom"
    print("✅ Custom model loaded (can distinguish red/green)")
else:
    print(f"\n⚠️  Custom model not found: {CUSTOM_MODEL}")
    print(f"📦 Using pretrained model: {PRETRAINED_MODEL}")
    model = YOLO(PRETRAINED_MODEL)
    model_type = "pretrained"
    print("✅ Pretrained model loaded successfully (COCO dataset)")
    print("   ⚠️  Cannot detect red/green, detects Class 9 (traffic_light) only")

# Initialize camera
print("\n📷 Initializing camera...")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Cannot open camera")
    exit(1)

print("✅ Camera initialized successfully")

# Check display environment
display = os.environ.get("DISPLAY")
if not display:
    print("⚠️  Warning: DISPLAY environment variable not set")
    print("   If running via SSH, use: ssh -X user@host")

print("\n" + "=" * 60)
print("  Real-time Traffic Light Detection Started")
print("=" * 60)
print("Keyboard shortcuts:")
print("  'q' or ESC: Quit")
print("  's': Save screenshot")
print("=" * 60 + "\n")

# Create window with specific flags
window_name = "YOLO11 Traffic Light Detection Test"
try:
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 640, 480)
    print("✅ Display window created successfully\n")
except Exception as e:
    print(f"⚠️  Warning: Could not create window: {e}")
    print("   Detection will continue, but display may not work\n")

frame_count = 0
detection_count = 0

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Cannot read frame")
            break

        frame_count += 1

        # YOLO inference (every frame for traffic lights - critical)
        if model_type == "custom":
            # Custom model: Detect all classes (0, 1, 2)
            results = model(frame, conf=0.4, verbose=False)
        else:
            # Pretrained model: Filter Class 9 only
            results = model(frame, conf=0.4, verbose=False, classes=[9])

        # Draw results
        annotated_frame = frame.copy()
        current_detections = 0

        for result in results:
            boxes = result.boxes

            if len(boxes) > 0:
                print(f"\n[Frame {frame_count}] Detected {len(boxes)} object(s):")

            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])

                if model_type == "custom":
                    # Custom model display
                    if class_id == 0:  # red
                        color = (0, 0, 255)  # RED (BGR)
                        label = f"RED LIGHT"
                        status = "🔴 RED"
                    elif class_id == 1:  # green
                        color = (0, 255, 0)  # GREEN (BGR)
                        label = f"GREEN LIGHT"
                        status = "🟢 GREEN"
                    else:  # traffic_light
                        color = (255, 255, 0)  # CYAN (BGR)
                        label = f"TRAFFIC LIGHT"
                        status = "⚪ LIGHT"
                else:
                    # Pretrained model display (Class 9)
                    color = (0, 255, 255)  # YELLOW (BGR)
                    label = f"TRAFFIC LIGHT"
                    status = "🚦 TRAFFIC LIGHT"

                # Print detection info
                print(
                    f"  {status} - Conf: {confidence:.2f} - Pos: [{x1},{y1},{x2},{y2}]"
                )

                # Draw thick bounding box
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 3)

                # Prepare label with confidence
                label_with_conf = f"{label} {confidence:.2f}"

                # Get label size for background
                (label_width, label_height), baseline = cv2.getTextSize(
                    label_with_conf, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
                )

                # Draw label background (filled rectangle)
                cv2.rectangle(
                    annotated_frame,
                    (x1, y1 - label_height - 15),
                    (x1 + label_width + 10, y1),
                    color,
                    -1,  # Filled
                )

                # Draw label text (BLACK for better contrast)
                cv2.putText(
                    annotated_frame,
                    label_with_conf,
                    (x1 + 5, y1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 0),  # BLACK
                    2,
                )

                current_detections += 1

        detection_count += current_detections

        # Display frame information
        cv2.putText(
            annotated_frame,
            f"Frame: {frame_count} | Total Detections: {detection_count}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),  # WHITE
            2,
        )

        # Display model type
        model_text = f"Model: {model_type.upper()}"
        cv2.putText(
            annotated_frame,
            model_text,
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 255),  # YELLOW
            2,
        )

        # Display instructions
        cv2.putText(
            annotated_frame,
            "Press 'q' or ESC to quit, 's' to save",
            (10, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),  # WHITE
            1,
        )

        # Try to show window
        try:
            cv2.imshow(window_name, annotated_frame)
        except Exception as e:
            if frame_count == 1:  # Only print error once
                print(f"⚠️  Cannot display window: {e}")
                print("   Detection continues in background...")

        # Handle key input
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q") or key == 27:  # 'q' or ESC
            print("\n🛑 Quitting...")
            break
        elif key == ord("s"):  # Screenshot
            filename = f"screenshot_{frame_count}.jpg"
            cv2.imwrite(filename, annotated_frame)
            print(f"📸 Screenshot saved: {filename}")

except KeyboardInterrupt:
    print("\n🛑 User interrupted")

except Exception as e:
    print(f"\n❌ Error occurred: {e}")
    import traceback

    traceback.print_exc()

finally:
    cap.release()
    cv2.destroyAllWindows()
    print("\n" + "=" * 60)
    print(f"Total frames: {frame_count}")
    print(f"Total detections: {detection_count}")
    print("✅ Test completed")
    print("=" * 60)
