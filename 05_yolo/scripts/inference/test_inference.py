"""
YOLO11 추론 테스트 스크립트

훈련된 모델로 이미지, 비디오, 웹캠에서 객체 검출을 수행합니다.
"""

from ultralytics import YOLO
import cv2
from pathlib import Path
import time
import argparse


class YOLOInference:
    """YOLO 모델로 추론을 수행하는 클래스"""

    def __init__(
        self,
        weights_path: str,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
    ):
        """
        Args:
            weights_path: 모델 가중치 경로 (.pt 파일)
            conf_threshold: 신뢰도 임계값
            iou_threshold: IoU 임계값 (NMS)
        """
        if not Path(weights_path).exists():
            raise FileNotFoundError(f"모델 파일이 없습니다: {weights_path}")

        print(f"📥 모델 로딩: {weights_path}")
        self.model = YOLO(weights_path)
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold

        print(f"✅ 모델 로딩 완료")
        print(f"   신뢰도 임계값: {conf_threshold}")
        print(f"   IoU 임계값: {iou_threshold}\n")

    def predict_image(
        self, image_path: str, save: bool = True, save_dir: str = "inference_results"
    ):
        """
        단일 이미지에 대해 추론합니다.

        Args:
            image_path: 이미지 파일 경로
            save: 결과 이미지 저장 여부
            save_dir: 결과 저장 디렉토리

        Returns:
            추론 결과 객체
        """
        if not Path(image_path).exists():
            raise FileNotFoundError(f"이미지 파일이 없습니다: {image_path}")

        print(f"🖼️  추론 중: {image_path}")
        start_time = time.time()

        results = self.model.predict(
            source=image_path,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            save=save,
            save_txt=True,
            save_conf=True,
            project=save_dir,
            name="predict",
            exist_ok=True,
            line_width=2,
            show_labels=True,
            show_conf=True,
        )

        inference_time = (time.time() - start_time) * 1000

        result = results[0]
        num_detections = len(result.boxes)

        print(f"   검출 객체: {num_detections}개")
        print(f"   추론 시간: {inference_time:.1f}ms")

        # 검출된 객체 상세 정보
        if num_detections > 0:
            print(f"\n   검출 결과:")
            for box in result.boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                class_name = result.names[cls]
                print(f"      - {class_name}: {conf:.2f}")

        return result

    def predict_directory(
        self, directory_path: str, save_dir: str = "inference_results"
    ):
        """
        디렉토리 내 모든 이미지에 대해 추론합니다.

        Args:
            directory_path: 이미지 디렉토리 경로
            save_dir: 결과 저장 디렉토리
        """
        image_dir = Path(directory_path)

        if not image_dir.exists():
            raise FileNotFoundError(f"디렉토리가 없습니다: {directory_path}")

        # 지원하는 이미지 확장자
        extensions = ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]
        image_files = []

        for ext in extensions:
            image_files.extend(image_dir.glob(ext))

        if not image_files:
            print(f"⚠️  이미지 파일을 찾을 수 없습니다: {directory_path}")
            return

        print(f"📂 디렉토리 추론: {directory_path}")
        print(f"   이미지 개수: {len(image_files)}\n")

        total_time = 0
        total_detections = 0

        for idx, img_path in enumerate(image_files, 1):
            print(f"[{idx}/{len(image_files)}]", end=" ")
            result = self.predict_image(str(img_path), save=True, save_dir=save_dir)

            total_detections += len(result.boxes)

            if hasattr(result, "speed"):
                total_time += result.speed["inference"]

        # 통계 출력
        print(f"\n{'=' * 60}")
        print(f"추론 완료 통계")
        print(f"{'=' * 60}")
        print(f"총 이미지: {len(image_files)}개")
        print(f"총 검출 객체: {total_detections}개")

        if len(image_files) > 0:
            avg_time = total_time / len(image_files)
            print(f"평균 추론 시간: {avg_time:.1f}ms")
            print(f"FPS: {1000/avg_time:.1f}")

        print(f"{'=' * 60}\n")

    def predict_video(
        self, video_path: str, save: bool = True, save_dir: str = "inference_results"
    ):
        """
        비디오 파일로 추론을 실행합니다.

        Args:
            video_path: 비디오 파일 경로
            save: 결과 비디오 저장 여부
            save_dir: 결과 저장 디렉토리
        """
        if not Path(video_path).exists():
            raise FileNotFoundError(f"비디오 파일이 없습니다: {video_path}")

        print(f"🎬 비디오 추론: {video_path}")

        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(f"비디오를 열 수 없습니다: {video_path}")

        # 비디오 정보
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"   해상도: {width}x{height}")
        print(f"   FPS: {fps}")
        print(f"   총 프레임: {total_frames}\n")

        # 출력 비디오 설정
        if save:
            output_path = (
                Path(save_dir) / "predict" / f"{Path(video_path).stem}_detected.mp4"
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
            print(f"💾 저장 경로: {output_path}")

        frame_count = 0
        total_detections = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1

                # YOLO 추론
                results = self.model.predict(
                    source=frame,
                    conf=self.conf_threshold,
                    iou=self.iou_threshold,
                    verbose=False,
                )[0]

                # 결과 시각화
                annotated_frame = results.plot()

                # 검출 개수
                num_detections = len(results.boxes)
                total_detections += num_detections

                # 진행률 표시
                progress = (frame_count / total_frames) * 100
                cv2.putText(
                    annotated_frame,
                    f"Frame: {frame_count}/{total_frames} ({progress:.1f}%)",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )

                cv2.putText(
                    annotated_frame,
                    f"Detections: {num_detections}",
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )

                # 저장
                if save:
                    out.write(annotated_frame)

                # 화면 표시
                cv2.imshow("YOLO11 Video Detection", annotated_frame)

                # 'q' 키로 중단
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    print("\n⚠️  사용자에 의해 중단됨")
                    break

                # 진행률 출력
                if frame_count % 30 == 0:
                    print(
                        f"   처리 중: {frame_count}/{total_frames} ({progress:.1f}%)",
                        end="\r",
                    )

        finally:
            cap.release()
            if save:
                out.release()
            cv2.destroyAllWindows()

        print(f"\n\n✅ 비디오 처리 완료")
        print(f"   처리된 프레임: {frame_count}")
        print(f"   총 검출 객체: {total_detections}")
        print(f"   평균 검출/프레임: {total_detections/frame_count:.2f}\n")

    def predict_webcam(self):
        """웹캠으로 실시간 추론을 실행합니다."""
        print("🎥 웹캠 실시간 추론 시작 (q 키로 종료)")

        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            raise ValueError("웹캠을 열 수 없습니다")

        fps_list = []

        try:
            while True:
                start_time = time.time()

                ret, frame = cap.read()
                if not ret:
                    break

                # YOLO 추론
                results = self.model.predict(
                    source=frame,
                    conf=self.conf_threshold,
                    iou=self.iou_threshold,
                    verbose=False,
                )[0]

                # 결과 시각화
                annotated_frame = results.plot()

                # FPS 계산
                fps = 1 / (time.time() - start_time)
                fps_list.append(fps)

                # FPS 및 검출 정보 표시
                cv2.putText(
                    annotated_frame,
                    f"FPS: {fps:.1f}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2,
                )

                num_detections = len(results.boxes)
                cv2.putText(
                    annotated_frame,
                    f"Objects: {num_detections}",
                    (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2,
                )

                # 화면 표시
                cv2.imshow("YOLO11 Webcam Detection", annotated_frame)

                # 'q' 키로 종료
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

        finally:
            cap.release()
            cv2.destroyAllWindows()

        # 평균 FPS 출력
        if fps_list:
            avg_fps = sum(fps_list) / len(fps_list)
            print(f"\n⏱️  평균 FPS: {avg_fps:.1f}")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="YOLO11 추론 테스트 스크립트")

    # 필수 인자
    parser.add_argument(
        "--weights", type=str, required=True, help="모델 가중치 파일 경로 (.pt)"
    )

    # 입력 소스
    parser.add_argument(
        "--source", type=str, help="입력 소스 (이미지/디렉토리/비디오 경로)"
    )
    parser.add_argument("--webcam", action="store_true", help="웹캠 사용")

    # 추론 설정
    parser.add_argument(
        "--conf", type=float, default=0.25, help="신뢰도 임계값 (기본값: 0.25)"
    )
    parser.add_argument(
        "--iou", type=float, default=0.45, help="IoU 임계값 (기본값: 0.45)"
    )

    # 출력 설정
    parser.add_argument(
        "--save-dir",
        type=str,
        default="inference_results",
        help="결과 저장 디렉토리 (기본값: inference_results)",
    )
    parser.add_argument("--no-save", action="store_true", help="결과 저장 안 함")

    args = parser.parse_args()

    # 추론 객체 생성
    inference = YOLOInference(
        weights_path=args.weights, conf_threshold=args.conf, iou_threshold=args.iou
    )

    # 추론 실행
    if args.webcam:
        inference.predict_webcam()
    elif args.source:
        source_path = Path(args.source)

        if source_path.is_file():
            # 비디오 확장자 확인
            video_exts = [".mp4", ".avi", ".mov", ".mkv"]
            if source_path.suffix.lower() in video_exts:
                inference.predict_video(
                    str(source_path), save=not args.no_save, save_dir=args.save_dir
                )
            else:
                # 이미지 파일
                inference.predict_image(
                    str(source_path), save=not args.no_save, save_dir=args.save_dir
                )
        elif source_path.is_dir():
            # 디렉토리
            inference.predict_directory(str(source_path), save_dir=args.save_dir)
        else:
            print(f"❌ 잘못된 경로: {args.source}")
    else:
        print("❌ --source 또는 --webcam 중 하나를 지정해야 합니다")
        parser.print_help()


if __name__ == "__main__":
    # 예시 사용법
    # python test_inference.py --weights best.pt --source test_image.jpg
    # python test_inference.py --weights best.pt --source test_images/
    # python test_inference.py --weights best.pt --source test_video.mp4
    # python test_inference.py --weights best.pt --webcam

    # 또는 직접 실행
    inference = YOLOInference(
        weights_path="raspbot_yolo11/traffic_detection/weights/best.pt",
        conf_threshold=0.25,
    )

    # 단일 이미지 테스트
    # inference.predict_image("test_images/test_001.jpg")

    # 디렉토리 전체 테스트
    # inference.predict_directory("test_images/")

    # 웹캠 테스트
    # inference.predict_webcam()
