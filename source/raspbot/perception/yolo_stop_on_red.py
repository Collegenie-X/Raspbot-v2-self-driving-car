"""YOLOv8n 기반 적색 신호 감지 후 정지 테스트.

카메라 스트림을 보며 지정한 클래스(예: red, red_light)를 감지하면 모터를 정지한다.
ESC 또는 q 키로 종료 가능.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, Optional, Set

import cv2
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from raspbot.hardware.camera import Camera, CameraConfig  # noqa: E402
from raspbot.hardware.raspbot import RaspbotHardware  # noqa: E402


def resolve_model_path(model_arg: Optional[str]) -> Path:
    if model_arg:
        model_path = Path(model_arg).expanduser().resolve()
    else:
        model_path = PROJECT_ROOT / "models" / "yolo" / "best.pt"
    if not model_path.exists():
        raise FileNotFoundError(f"YOLO 모델 파일을 찾을 수 없습니다: {model_path}")
    return model_path


def parse_stop_classes(raw: str) -> Set[str]:
    return {name.strip().lower() for name in raw.split(",") if name.strip()}


def match_target_classes(
    target_names: Iterable[str],
    model_names: dict,
    detections,
    frame_area: float,
    min_area_ratio: float,
) -> Optional[str]:
    names_lc = {k: v.lower() for k, v in model_names.items()}
    targets = set(target_names)
    for box in detections:
        cls_id = int(box.cls.item()) if hasattr(box.cls, "item") else int(box.cls)
        cls_name = names_lc.get(cls_id, "")
        if cls_name in targets:
            if min_area_ratio > 0:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
                if frame_area > 0 and (area / frame_area) < min_area_ratio:
                    continue
            return cls_name
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="적색 감지 후 정지 테스트")
    parser.add_argument("--model", type=str, help="모델(.pt) 경로. 기본: models/yolo/best.pt")
    parser.add_argument("--imgsz", type=int, default=320, help="입력 이미지 크기")
    parser.add_argument("--conf", type=float, default=0.5, help="신뢰도 임계값")
    parser.add_argument("--device", type=str, default=None, help="cuda, cpu 등 강제 디바이스 지정")
    parser.add_argument("--cam-index", type=int, default=0, help="카메라 인덱스")
    parser.add_argument("--width", type=int, default=320, help="카메라 가로 해상도")
    parser.add_argument("--height", type=int, default=240, help="카메라 세로 해상도")
    parser.add_argument("--speed", type=int, default=40, help="직진 모터 속도")
    parser.add_argument(
        "--stop-classes",
        type=str,
        default="red,red_light,red light",
        help="감지 시 정지할 클래스 이름(쉼표 구분, 소문자 비교)",
    )
    parser.add_argument(
        "--min-area-ratio",
        type=float,
        default=0.0,
        help="정지 대상으로 인정할 최소 박스 면적 비율(0~1). 예: 0.01은 화면의 1%% 이상일 때만 정지.",
    )
    parser.add_argument("--mock", action="store_true", help="실기 없이 모터 제어를 모킹")
    return parser.parse_args()


def main():
    args = parse_args()
    model_path = resolve_model_path(args.model)

    print(f"[INFO] YOLO 모델 로드: {model_path}")
    model = YOLO(str(model_path))
    if args.device:
        model.to(args.device)

    targets = parse_stop_classes(args.stop_classes)
    print("[INFO] 모델 클래스 목록:")
    for cls_id, name in model.names.items():
        print(f"  {cls_id}: {name}")
    print(f"[INFO] 감지 시 정지 대상: {', '.join(sorted(targets))}")

    cam_cfg = CameraConfig(index=args.cam_index, resolution=(args.width, args.height))
    camera = Camera(cam_cfg)
    hardware = RaspbotHardware(enable_mock=args.mock)

    stopped = False
    print(f"[INFO] 직진 시작 (속도={args.speed}). ESC/q로 종료.")
    hardware.drive(args.speed, args.speed)

    try:
        while True:
            try:
                frame = camera.read()
            except RuntimeError as e:
                print(f"[WARN] 프레임을 읽지 못했습니다: {e}")
                continue

            results = model(frame, imgsz=args.imgsz, conf=args.conf, verbose=False)
            frame_h, frame_w = results[0].orig_shape[:2]
            frame_area = float(frame_h * frame_w)
            det_name = match_target_classes(
                targets, model.names, results[0].boxes, frame_area, args.min_area_ratio
            )

            if det_name and not stopped:
                print(f"[INFO] '{det_name}' 감지 → 모터 정지")
                hardware.stop()
                stopped = True

            annotated = results[0].plot()
            state_text = "STOP" if stopped else "DRIVE"
            cv2.putText(
                annotated,
                f"STATE: {state_text}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 0, 255) if stopped else (0, 255, 0),
                2,
            )
            cv2.imshow("YOLO Stop on Red", annotated)
            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q")):
                print("[INFO] 종료 키 입력. 프로그램을 종료합니다.")
                break
    finally:
        hardware.stop()
        hardware.cleanup()
        camera.release()
        cv2.destroyAllWindows()
        print("[INFO] 정리 완료.")


if __name__ == "__main__":
    main()
