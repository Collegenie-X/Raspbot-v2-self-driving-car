#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
기본 객체 인식 예제

YOLO11을 사용한 가장 기본적인 객체 인식 코드입니다.

사용법:
    python basic_detection.py --source test.jpg
    python basic_detection.py --source 0  # 웹캠
    python basic_detection.py --source video.mp4
"""

from ultralytics import YOLO
import cv2
import argparse


def main():
    parser = argparse.ArgumentParser(description="YOLO11 기본 객체 인식")
    parser.add_argument(
        "--model",
        type=str,
        default="yolo11n.pt",
        help="모델 경로 (기본값: yolo11n.pt)",
    )
    parser.add_argument(
        "--source",
        type=str,
        default="0",
        help="입력 소스 (이미지/비디오/웹캠)",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.5,
        help="신뢰도 임계값 (기본값: 0.5)",
    )
    parser.add_argument(
        "--iou",
        type=float,
        default=0.5,
        help="NMS IoU 임계값 (기본값: 0.5)",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="결과 저장",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        default=True,
        help="결과 표시",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🎯 YOLO11 기본 객체 인식")
    print("=" * 60)
    print(f"모델: {args.model}")
    print(f"소스: {args.source}")
    print(f"신뢰도 임계값: {args.conf}")
    print(f"IoU 임계값: {args.iou}")
    print("=" * 60)

    # 모델 로드
    print("\n📦 모델 로딩 중...")
    model = YOLO(args.model)
    print("✅ 모델 로드 완료!")

    # 웹캠인 경우 정수로 변환
    source = args.source
    if source.isdigit():
        source = int(source)

    # 추론
    print(f"\n🔍 추론 시작: {source}")
    results = model.predict(
        source=source,
        conf=args.conf,
        iou=args.iou,
        show=args.show,
        save=args.save,
        stream=True,  # 스트리밍 모드
    )

    # 결과 처리
    for i, result in enumerate(results):
        boxes = result.boxes
        print(f"\n프레임 {i+1}: {len(boxes)}개 객체 검출")

        # 각 검출 객체 정보 출력
        for box in boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            class_name = model.names[cls]
            print(f"  - {class_name}: {conf:.2f}")

    print("\n✅ 추론 완료!")


if __name__ == "__main__":
    main()

