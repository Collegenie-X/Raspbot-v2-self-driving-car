#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLO11 Camera Test - Real-time YOLO detection with camera
export QT_QPA_PLATFORM=xcb && python3 1_yolo_camera_test.py
Usage: python3 1_yolo_camera_test.py
Press 'q' to quit
"""

import cv2
from ultralytics import YOLO
import threading
from datetime import datetime
import os

# Load model
model = YOLO("./models/yolo11n.pt")

# Create tmp directory
if not os.path.exists("./tmp"):
    os.makedirs("./tmp")

# Keyboard input handler
quit_flag = False


def keyboard_listener():
    global quit_flag
    while not quit_flag:
        try:
            key = input()
            if key.lower() == "q":
                print("\n'q' pressed - quitting...")
                quit_flag = True
                break
        except:
            pass


if not os.environ.get("QT_QPA_PLATFORM"):
    os.environ["QT_QPA_PLATFORM"] = "xcb"

# Start keyboard listener thread
keyboard_thread = threading.Thread(target=keyboard_listener, daemon=True)
keyboard_thread.start()


# Open camera
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()

print("Camera opened")
print("Press 'q' and ENTER to quit")
print("Saving every frame with timestamp...")

frame_count = 0

# Main loop
try:
    while not quit_flag:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save frame as JPEG
        temp_path = "./tmp/yolo_temp.jpg"
        cv2.imwrite(temp_path, frame)

        # Run YOLO
        results = model(temp_path, conf=0.4, verbose=False)

        # Print detections
        if len(results[0].boxes) > 0:
            print(
                f"\n[Frame {frame_count} | {timestamp}] Detected {len(results[0].boxes)} objects:"
            )
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = model.names[class_id]
                print(f"  {class_name} ({confidence:.2f}) at [{x1},{y1},{x2},{y2}]")

            # Draw boxes
            annotated = frame.copy()
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = model.names[class_id]
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 3)
                label = f"{class_name} {confidence:.2f}"
                cv2.putText(
                    annotated,
                    label,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )

            # Save with timestamp
            result_filename = f"./tmp/camera_{timestamp}.jpg"
            cv2.imwrite(result_filename, annotated)
            print(f"Saved {result_filename}")

except KeyboardInterrupt:
    print("\nStopped by Ctrl+C")

# Cleanup
quit_flag = True
cap.release()

if os.path.exists("./tmp/yolo_temp.jpg"):
    os.remove("./tmp/yolo_temp.jpg")

print(f"\nTest completed - Total frames: {frame_count}")
print(f"Results saved in ./tmp/camera_YYYYMMDD_HHMMSS.jpg")
