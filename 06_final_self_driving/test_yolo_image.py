#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLO11 Image Test - Test YOLO with JPEG image files
Usage: python3 test_yolo_image.py
export QT_QPA_PLATFORM=xcb && python3 test_yolo_image.py
"""

import cv2
from ultralytics import YOLO
from datetime import datetime
import os

# Load model
model = YOLO("./models/yolo11n.pt")

# Create tmp directory
if not os.path.exists("./tmp"):
    os.makedirs("./tmp")

# Test image path
test_image = "./images/bus.jpg"

# Generate timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Run YOLO
print(f"Running YOLO on {test_image}...")
results = model(test_image, conf=0.4, verbose=False)

# Load image
image = cv2.imread(test_image)

# Draw boxes
print(f"\nDetection Results [{timestamp}]:")
for box in results[0].boxes:
    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
    confidence = float(box.conf[0])
    class_id = int(box.cls[0])
    class_name = model.names[class_id]

    # Draw box
    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 3)

    # Draw label
    label = f"{class_name} {confidence:.2f}"
    cv2.putText(
        image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
    )

    print(f"  {class_name} ({confidence:.2f}) at [{x1},{y1},{x2},{y2}]")

# Save result with timestamp
result_filename = f"./tmp/image_{timestamp}.jpg"
cv2.imwrite(result_filename, image)
print(f"\nSaved as {result_filename}")
print("Test completed")
