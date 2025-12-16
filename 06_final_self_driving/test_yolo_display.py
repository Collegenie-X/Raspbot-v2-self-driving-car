#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLO11 Real-time Display Test
YOLO + cv2.imshow() together

Requirements:
- VNC connection (recommended) OR
- Direct monitor connection OR
- SSH with X11 forwarding (ssh -X)

Usage:
    # Simple:
    python3 test_yolo_display.py

    # If display issues:
    export QT_QPA_PLATFORM=xcb && python3 test_yolo_display.py

Controls:
    'q' - Quit
    's' - Save screenshot
"""

import cv2
from ultralytics import YOLO
from datetime import datetime
import os
import sys

# Set Qt platform for Raspberry Pi (if not already set)
if not os.environ.get("QT_QPA_PLATFORM"):
    os.environ["QT_QPA_PLATFORM"] = "xcb"

print("=" * 70)
print("  YOLO11 Real-time Display Test")
print("=" * 70)
print(f"Display: {os.environ.get('DISPLAY', 'NOT SET')}")
print(f"Qt Platform: {os.environ.get('QT_QPA_PLATFORM', 'NOT SET')}")
print("=" * 70)

# Load model
print("\nLoading YOLO model...")
model = YOLO("./models/yolo11n.pt")
print("✅ Model loaded")

# Create tmp directory
if not os.path.exists("./tmp"):
    os.makedirs("./tmp")

# Open camera
print("\nOpening camera...")
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Cannot open camera")
    sys.exit(1)

print("✅ Camera opened")

# Window setup
window_name = "YOLO11 Detection"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.resizeWindow(window_name, 800, 600)

print("\n" + "=" * 70)
print("Starting detection...")
print("Controls: 'q' to quit, 's' to save screenshot")
print("=" * 70 + "\n")

frame_count = 0

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # Save frame as JPEG for YOLO
        temp_path = "./tmp/yolo_temp.jpg"
        cv2.imwrite(temp_path, frame)

        # Run YOLO detection
        results = model(temp_path, conf=0.4, verbose=False)

        # Draw results on frame
        annotated = frame.copy()

        detection_count = 0
        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            class_name = model.names[class_id]

            # Draw bounding box (GREEN)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 3)

            # Draw label
            label = f"{class_name} {confidence:.2f}"
            cv2.putText(
                annotated,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

            detection_count += 1

            # Print to console (every 30 frames)
            if frame_count % 30 == 1:
                print(f"  {class_name} ({confidence:.2f}) at [{x1},{y1},{x2},{y2}]")

        # Add frame info on screen
        info_text = f"Frame: {frame_count} | Detections: {detection_count}"
        cv2.putText(
            annotated,
            info_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )

        # Add controls info
        cv2.putText(
            annotated,
            "Press 'q' to quit, 's' to save",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2,
        )

        # Display
        cv2.imshow(window_name, annotated)

        # Handle keyboard
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            print("\nQuitting...")
            break
        elif key == ord("s"):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"./tmp/screenshot_{timestamp}.jpg"
            cv2.imwrite(filename, annotated)
            print(f"📸 Screenshot saved: {filename}")

except KeyboardInterrupt:
    print("\nStopped by Ctrl+C")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback

    traceback.print_exc()

finally:
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()

    if os.path.exists("./tmp/yolo_temp.jpg"):
        os.remove("./tmp/yolo_temp.jpg")

    print(f"\n{'=' * 70}")
    print(f"Completed - Total frames: {frame_count}")
    print(f"{'=' * 70}")
