#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실시간 웹캠 객체 인식

웹캠을 사용한 실시간 객체 인식 예제입니다.
FPS 표시 및 키보드 제어 기능 포함.

사용법:
    python real_time_webcam.py
    python real_time_webcam.py --model custom_best.pt
"""

from ultralytics import YOLO
import cv2
import argparse
import time


class RealtimeDetector:
    """실시간 객체 검출기 클래스"""

    def __init__(self, model_path="yolo11n.pt", conf=0.5, iou=0.5):
        """
        초기화

        Args:
            model_path: 모델 경로
            conf: 신뢰도 임계값
            iou: NMS IoU 임계값
        """
        self.model = YOLO(model_path)
        self.conf = conf
        self.iou = iou
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()

    def calculate_fps(self):
        """FPS 계산"""
        self.frame_count += 1
        elapsed_time = time.time() - self.start_time
        if elapsed_time > 0:
            self.fps = self.frame_count / elapsed_time
        return self.fps

    def draw_info(self, frame, detections):
        """
        프레임에 정보 그리기

        Args:
            frame: OpenCV 프레임
            detections: 검출 결과
        """
        # FPS 표시
        fps_text = f"FPS: {self.fps:.1f}"
        cv2.putText(
            frame,
            fps_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

        # 검출 객체 수
        obj_text = f"Objects: {len(detections)}"
        cv2.putText(
            frame,
            obj_text,
            (10, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

        # 키 안내
        help_text = "q: 종료 | s: 저장 | c: 신뢰도 조정"
        cv2.putText(
            frame,
            help_text,
            (10, frame.shape[0] - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            1,
        )

        return frame

    def run(self, webcam_id=0):
        """
        실시간 검출 실행

        Args:
            webcam_id: 웹캠 ID
        """
        print("=" * 60)
        print("📹 실시간 웹캠 객체 인식")
        print("=" * 60)
        print(f"웹캠 ID: {webcam_id}")
        print(f"신뢰도 임계값: {self.conf}")
        print("\n키보드 제어:")
        print("  q: 종료")
        print("  s: 스크린샷 저장")
        print("  c: 신뢰도 임계값 조정")
        print("  +/-: 신뢰도 증가/감소")
        print("=" * 60)

        cap = cv2.VideoCapture(webcam_id)
        if not cap.isOpened():
            raise ValueError(f"웹캠을 열 수 없습니다: {webcam_id}")

        # 카메라 설정
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        screenshot_count = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("❌ 프레임을 읽을 수 없습니다.")
                    break

                # 객체 검출
                results = self.model.predict(
                    frame,
                    conf=self.conf,
                    iou=self.iou,
                    verbose=False,
                )

                # 결과 그리기
                annotated_frame = results[0].plot()

                # FPS 계산
                self.calculate_fps()

                # 정보 표시
                annotated_frame = self.draw_info(
                    annotated_frame, results[0].boxes
                )

                # 화면 표시
                cv2.imshow("YOLO11 Real-time Detection", annotated_frame)

                # 키보드 입력 처리
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    print("\n👋 종료합니다.")
                    break
                elif key == ord("s"):
                    # 스크린샷 저장
                    filename = f"screenshot_{screenshot_count:04d}.jpg"
                    cv2.imwrite(filename, annotated_frame)
                    screenshot_count += 1
                    print(f"\n📸 스크린샷 저장: {filename}")
                elif key == ord("+") or key == ord("="):
                    # 신뢰도 증가
                    self.conf = min(1.0, self.conf + 0.05)
                    print(f"\n📈 신뢰도: {self.conf:.2f}")
                elif key == ord("-") or key == ord("_"):
                    # 신뢰도 감소
                    self.conf = max(0.0, self.conf - 0.05)
                    print(f"\n📉 신뢰도: {self.conf:.2f}")

        finally:
            cap.release()
            cv2.destroyAllWindows()

        print(f"\n✅ 총 {self.frame_count}프레임 처리")
        print(f"   평균 FPS: {self.fps:.1f}")
        print(f"   스크린샷: {screenshot_count}장")


def main():
    parser = argparse.ArgumentParser(description="실시간 웹캠 객체 인식")
    parser.add_argument(
        "--model",
        type=str,
        default="yolo11n.pt",
        help="모델 경로 (기본값: yolo11n.pt)",
    )
    parser.add_argument(
        "--webcam",
        type=int,
        default=0,
        help="웹캠 ID (기본값: 0)",
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

    args = parser.parse_args()

    # 검출기 초기화 및 실행
    detector = RealtimeDetector(
        model_path=args.model,
        conf=args.conf,
        iou=args.iou,
    )
    detector.run(webcam_id=args.webcam)


if __name__ == "__main__":
    main()

