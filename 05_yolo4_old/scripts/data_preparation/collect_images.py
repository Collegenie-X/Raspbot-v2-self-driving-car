#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
이미지 수집 스크립트

웹캠, 비디오 파일 또는 폴더에서 이미지를 수집합니다.
YOLOv4 커스텀 데이터셋 제작을 위한 첫 번째 단계입니다.

사용법:
    python collect_images.py --source webcam --output dataset/images --num_images 500
    python collect_images.py --source video --input video.mp4 --output dataset/images
    python collect_images.py --source folder --input raw_images/ --output dataset/images
"""

import cv2
import os
import argparse
from pathlib import Path
from tqdm import tqdm
import time


class ImageCollector:
    """이미지 수집 클래스"""

    def __init__(self, source="webcam", output_dir="dataset/images"):
        """
        초기화

        Args:
            source: 이미지 소스 ('webcam', 'video', 'folder')
            output_dir: 출력 디렉토리
        """
        self.source = source
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.image_count = len(list(self.output_dir.glob("*.jpg")))

    def collect_from_webcam(self, num_images=500, interval=0.5, webcam_id=0):
        """
        웹캠으로부터 이미지 수집

        Args:
            num_images: 수집할 이미지 수
            interval: 캡처 간격 (초)
            webcam_id: 웹캠 ID
        """
        print(f"📷 웹캠에서 {num_images}장의 이미지 수집 시작...")
        print(f"   - 캡처 간격: {interval}초")
        print(f"   - 's' 키: 수동 저장")
        print(f"   - 'q' 키: 종료")

        cap = cv2.VideoCapture(webcam_id)
        if not cap.isOpened():
            raise ValueError("웹캠을 열 수 없습니다.")

        # 카메라 설정
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        collected = 0
        last_capture_time = time.time()

        with tqdm(total=num_images, desc="이미지 수집") as pbar:
            while collected < num_images:
                ret, frame = cap.read()
                if not ret:
                    print("❌ 프레임을 읽을 수 없습니다.")
                    break

                # 화면에 정보 표시
                display_frame = frame.copy()
                cv2.putText(
                    display_frame,
                    f"수집: {collected}/{num_images}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2,
                )
                cv2.putText(
                    display_frame,
                    "s: 저장 | q: 종료",
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2,
                )

                # 자동 캡처
                current_time = time.time()
                if current_time - last_capture_time >= interval:
                    self._save_image(frame)
                    collected += 1
                    pbar.update(1)
                    last_capture_time = current_time

                cv2.imshow("Image Collection", display_frame)

                # 키보드 입력 처리
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    print("\n⚠️  사용자가 수집을 중단했습니다.")
                    break
                elif key == ord("s"):
                    # 수동 저장
                    self._save_image(frame)
                    collected += 1
                    pbar.update(1)
                    print(f"\n✅ 수동 저장: {collected}번째 이미지")

        cap.release()
        cv2.destroyAllWindows()
        print(f"\n✅ 총 {collected}장의 이미지를 수집했습니다.")
        print(f"   저장 위치: {self.output_dir}")

    def collect_from_video(self, video_path, interval=1.0, max_images=None):
        """
        비디오 파일에서 이미지 추출

        Args:
            video_path: 비디오 파일 경로
            interval: 프레임 추출 간격 (초)
            max_images: 최대 추출 이미지 수 (None이면 제한 없음)
        """
        print(f"🎥 비디오에서 이미지 추출: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"비디오 파일을 열 수 없습니다: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_interval = int(fps * interval)

        print(f"   - FPS: {fps}")
        print(f"   - 총 프레임: {total_frames}")
        print(f"   - 추출 간격: {frame_interval} 프레임")

        collected = 0
        frame_count = 0

        with tqdm(total=total_frames, desc="비디오 처리") as pbar:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_count % frame_interval == 0:
                    self._save_image(frame)
                    collected += 1

                    if max_images and collected >= max_images:
                        break

                frame_count += 1
                pbar.update(1)

        cap.release()
        print(f"\n✅ 총 {collected}장의 이미지를 추출했습니다.")
        print(f"   저장 위치: {self.output_dir}")

    def collect_from_folder(self, input_folder, copy_mode=True):
        """
        폴더에서 이미지 복사 또는 이동

        Args:
            input_folder: 입력 폴더 경로
            copy_mode: True면 복사, False면 이동
        """
        input_path = Path(input_folder)
        if not input_path.exists():
            raise ValueError(f"입력 폴더가 존재하지 않습니다: {input_folder}")

        # 지원하는 이미지 확장자
        extensions = [".jpg", ".jpeg", ".png", ".bmp"]
        image_files = []
        for ext in extensions:
            image_files.extend(list(input_path.glob(f"*{ext}")))
            image_files.extend(list(input_path.glob(f"*{ext.upper()}")))

        print(f"📁 폴더에서 이미지 처리: {input_folder}")
        print(f"   - 발견된 이미지: {len(image_files)}장")
        print(f"   - 모드: {'복사' if copy_mode else '이동'}")

        for img_file in tqdm(image_files, desc="이미지 처리"):
            img = cv2.imread(str(img_file))
            if img is not None:
                self._save_image(img)

                if not copy_mode:
                    # 원본 파일 삭제
                    img_file.unlink()

        print(f"\n✅ 총 {len(image_files)}장의 이미지를 처리했습니다.")
        print(f"   저장 위치: {self.output_dir}")

    def _save_image(self, image):
        """
        이미지 저장 (내부 메서드)

        Args:
            image: OpenCV 이미지 (BGR)
        """
        filename = f"img_{self.image_count:06d}.jpg"
        filepath = self.output_dir / filename
        cv2.imwrite(str(filepath), image)
        self.image_count += 1


def main():
    parser = argparse.ArgumentParser(
        description="YOLOv4 커스텀 데이터셋을 위한 이미지 수집"
    )
    parser.add_argument(
        "--source",
        type=str,
        default="webcam",
        choices=["webcam", "video", "folder"],
        help="이미지 소스 (기본값: webcam)",
    )
    parser.add_argument(
        "--input", type=str, default=None, help="입력 파일/폴더 경로 (video, folder 모드)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="dataset/images",
        help="출력 디렉토리 (기본값: dataset/images)",
    )
    parser.add_argument(
        "--num_images",
        type=int,
        default=500,
        help="수집할 이미지 수 (webcam 모드, 기본값: 500)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="캡처 간격 초 (기본값: 0.5)",
    )
    parser.add_argument(
        "--webcam_id", type=int, default=0, help="웹캠 ID (기본값: 0)"
    )
    parser.add_argument(
        "--max_images",
        type=int,
        default=None,
        help="최대 추출 이미지 수 (video 모드)",
    )
    parser.add_argument(
        "--move",
        action="store_true",
        help="복사 대신 이동 (folder 모드)",
    )

    args = parser.parse_args()

    # 이미지 수집기 초기화
    collector = ImageCollector(source=args.source, output_dir=args.output)

    # 소스에 따라 수집
    if args.source == "webcam":
        collector.collect_from_webcam(
            num_images=args.num_images,
            interval=args.interval,
            webcam_id=args.webcam_id,
        )
    elif args.source == "video":
        if not args.input:
            raise ValueError("video 모드에서는 --input 인자가 필요합니다.")
        collector.collect_from_video(
            video_path=args.input,
            interval=args.interval,
            max_images=args.max_images,
        )
    elif args.source == "folder":
        if not args.input:
            raise ValueError("folder 모드에서는 --input 인자가 필요합니다.")
        collector.collect_from_folder(input_folder=args.input, copy_mode=not args.move)


if __name__ == "__main__":
    main()

