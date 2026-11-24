"""Phase 1: ROI + 라인 추종 주행 루프 (HSV/Lab 모드 선택)."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2

from raspbot.control import PIDController, VehicleController
from raspbot.hardware import Camera, CameraConfig, RaspbotHardware
from raspbot.perception import apply_roi_overlay, calculate_roi_points, visualize_binary_debug, warp_perspective
from raspbot.perception import lane_detection_hsv, lane_detection_lab
from raspbot.perception.yolo_async import YoloAsyncRunner
from raspbot.perception.yolo_events import YoloEventDetector
from raspbot.planning.mission_fsm import BeepSequencer, MissionFSM
from raspbot.utils import FpsTimer, load_config


VISION_WINDOW = "phase1/vision"
CONTROL_WINDOW = "phase1/controls"
CAMERA_WINDOW = "phase1/camera"
YOLO_WINDOW = "phase1/yolo"
FRAME_WINDOW = "phase1/frame"
BINARY_WINDOW = "phase1/binary"
MODE_CHOICES = ("hsv", "lab")


def parse_args():
    parser = argparse.ArgumentParser(description="Phase1 라인 기반 자율주행 루프 (HSV/Lab)")
    parser.add_argument(
        "--config",
        type=str,
        default=str(Path(__file__).resolve().parents[2] / "configs" / "phase1_pid.yaml"),
        help="YAML 설정 파일 경로",
    )
    parser.add_argument(
        "--mode",
        choices=MODE_CHOICES,
        help="라인 검출 모드 선택 (hsv | lab). 미지정 시 설정 파일 값 사용.",
    )
    parser.add_argument(
        "--mock-hw",
        action="store_true",
        help="실기 없이 모터/서보/LED 호출을 콘솔 로그로 대체",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="OpenCV 윈도우를 띄우지 않고 동작",
    )
    return parser.parse_args()


def build_camera(cfg) -> Camera:
    camera_cfg = CameraConfig(
        index=cfg.get("index", 0),
        resolution=tuple(cfg.get("resolution", (320, 240))),
        brightness=cfg.get("brightness", 0),
        contrast=cfg.get("contrast", 0),
        saturation=cfg.get("saturation", 50),
        exposure=cfg.get("exposure", 100),
        gain=cfg.get("gain", 0),
    )
    return Camera(camera_cfg)


def create_trackbars(perception_cfg, control_cfg, hardware_cfg, runtime_cfg, mode: str) -> None:
    """실시간 조정을 위한 트랙바 UI 생성."""
    cv2.namedWindow(VISION_WINDOW, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(VISION_WINDOW, 420, 420)
    cv2.namedWindow(CONTROL_WINDOW, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(CONTROL_WINDOW, 420, 540)
    cv2.namedWindow(CAMERA_WINDOW, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(CAMERA_WINDOW, 420, 420)
    cv2.namedWindow(YOLO_WINDOW, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(YOLO_WINDOW, 420, 260)

    # 공통 ROI 및 밝기 임계
    cv2.createTrackbar("roi_top", VISION_WINDOW, int(perception_cfg.get("roi_top", 871)), 1000, lambda x: None)
    cv2.createTrackbar("roi_bottom", VISION_WINDOW, int(perception_cfg.get("roi_bottom", 946)), 1000, lambda x: None)
    mode_cfg = perception_cfg.get(mode, {})
    detect_init = int(mode_cfg.get("detect_value", perception_cfg.get("detect_value", 120)))
    cv2.createTrackbar("detect_value", VISION_WINDOW, detect_init, 255, lambda x: None)

    if mode == "lab":
        cv2.createTrackbar(
            "lab_red_l_min",
            VISION_WINDOW,
            int(mode_cfg.get("red_l_min", perception_cfg.get("lab_red_l_min", 30))),
            255,
            lambda x: None,
        )
        cv2.createTrackbar(
            "lab_red_a_min",
            VISION_WINDOW,
            int(mode_cfg.get("red_a_min", perception_cfg.get("lab_red_a_min", 150))),
            255,
            lambda x: None,
        )
        cv2.createTrackbar(
            "lab_red_b_min",
            VISION_WINDOW,
            int(mode_cfg.get("red_b_min", perception_cfg.get("lab_red_b_min", 140))),
            255,
            lambda x: None,
        )
        cv2.createTrackbar(
            "lab_gray_a_dev",
            VISION_WINDOW,
            int(mode_cfg.get("gray_a_dev", perception_cfg.get("lab_gray_a_dev", 15))),
            128,
            lambda x: None,
        )
        cv2.createTrackbar(
            "lab_gray_b_dev",
            VISION_WINDOW,
            int(mode_cfg.get("gray_b_dev", perception_cfg.get("lab_gray_b_dev", 15))),
            128,
            lambda x: None,
        )

    # PID 및 주행 속도
    cv2.createTrackbar(
        "pid_kp_x100",
        CONTROL_WINDOW,
        int(float(control_cfg.get("kp", 0.9)) * 100),
        6000,
        lambda x: None,
    )
    cv2.createTrackbar(
        "pid_ki_x100",
        CONTROL_WINDOW,
        int(float(control_cfg.get("ki", 0.0)) * 100),
        200,
        lambda x: None,
    )
    cv2.createTrackbar(
        "pid_kd_x100",
        CONTROL_WINDOW,
        int(float(control_cfg.get("kd", 0.05)) * 100),
        6000,
        lambda x: None,
    )
    cv2.createTrackbar("base_speed", CONTROL_WINDOW, int(control_cfg.get("base_speed", 40)), 255, lambda x: None)
    cv2.createTrackbar(
        "steer_scale_x100",
        CONTROL_WINDOW,
        int(float(control_cfg.get("steer_scale", 1.0)) * 100),
        300,
        lambda x: None,
    )

    # 회전 감지 및 제어 스케일
    turn_cfg = control_cfg.get("turn", {})
    cv2.createTrackbar(
        "turn_slope_thr_x100",
        CONTROL_WINDOW,
        int(float(turn_cfg.get("slope_thresh", 0.25)) * 100),
        300,
        lambda x: None,
    )
    cv2.createTrackbar(
        "turn_offset_thr_x100",
        CONTROL_WINDOW,
        int(float(turn_cfg.get("offset_thresh", 0.3)) * 100),
        300,
        lambda x: None,
    )
    cv2.createTrackbar(
        "turn_speed_scale_x100",
        CONTROL_WINDOW,
        int(float(turn_cfg.get("speed_scale", 0.7)) * 100),
        100,
        lambda x: None,
    )
    cv2.createTrackbar(
        "turn_steer_scale_x100",
        CONTROL_WINDOW,
        int(float(turn_cfg.get("steer_scale", 1.3)) * 100),
        300,
        lambda x: None,
    )

    # heading 가중치/연결 파라미터
    heading_cfg = control_cfg.get("heading", {})
    cv2.createTrackbar(
        "heading_smooth_x100",
        CONTROL_WINDOW,
        int(heading_cfg.get("smooth_alpha", 0.2) * 100),
        100,
        lambda x: None,
    )
    cv2.createTrackbar(
        "heading_connect_close_px",
        CONTROL_WINDOW,
        int(heading_cfg.get("connect_close_px", 1)),
        20,
        lambda x: None,
    )
    cv2.createTrackbar(
        "heading_merge_gap_px",
        CONTROL_WINDOW,
        int(heading_cfg.get("merge_gap_px", 1)),
        20,
        lambda x: None,
    )
    cv2.createTrackbar(
        "heading_p1_margin_px",
        CONTROL_WINDOW,
        int(heading_cfg.get("p1_margin_px", 1)),
        20,
        lambda x: None,
    )

    # 카메라 설정
    cam_cfg = hardware_cfg.get("camera", {})
    cv2.createTrackbar("brightness", CAMERA_WINDOW, int(cam_cfg.get("brightness", 0)), 200, lambda x: None)
    cv2.createTrackbar("contrast", CAMERA_WINDOW, int(cam_cfg.get("contrast", 0)), 200, lambda x: None)
    cv2.createTrackbar("saturation", CAMERA_WINDOW, int(cam_cfg.get("saturation", 50)), 200, lambda x: None)
    cv2.createTrackbar("exposure", CAMERA_WINDOW, int(cam_cfg.get("exposure", 100)), 300, lambda x: None)
    cv2.createTrackbar("gain", CAMERA_WINDOW, int(cam_cfg.get("gain", 0)), 200, lambda x: None)

    # 서보 각도 (카메라 앵글)
    servo_defaults = hardware_cfg.get("servo_defaults", (70, 10))
    cv2.createTrackbar("servo1_yaw", CAMERA_WINDOW, int(servo_defaults[0]), 180, lambda x: None)
    cv2.createTrackbar(
        "servo2_pitch",
        CAMERA_WINDOW,
        int(servo_defaults[1]),
        int(RaspbotHardware.SERVO_PITCH_LIMIT),
        lambda x: None,
    )

    # YOLO bbox 면적 비율 임계(0~0.2, x1000 스케일)
    yolo_cfg = perception_cfg.get("yolo", {})
    min_area_cfg = yolo_cfg.get("min_area_ratio", {})

    def _init_ratio(name: str, default: float = 0.0) -> int:
        return int(float(min_area_cfg.get(name, default)) * 1000)

    max_ratio_x1000 = 200
    cv2.createTrackbar("yolo_area_red_x1000", YOLO_WINDOW, _init_ratio("red", 0.0), max_ratio_x1000, lambda x: None)
    cv2.createTrackbar(
        "yolo_area_green_x1000", YOLO_WINDOW, _init_ratio("green", 0.0), max_ratio_x1000, lambda x: None
    )
    cv2.createTrackbar("yolo_area_oo_x1000", YOLO_WINDOW, _init_ratio("oo", 0.0), max_ratio_x1000, lambda x: None)
    cv2.createTrackbar("yolo_area_xx_x1000", YOLO_WINDOW, _init_ratio("xx", 0.0), max_ratio_x1000, lambda x: None)
    cv2.createTrackbar("yolo_area_car_x1000", YOLO_WINDOW, _init_ratio("car", 0.0), max_ratio_x1000, lambda x: None)

    # YOLO 추론 주기(밀리초, 0이면 매 프레임 시도)
    interval_ms = int(max(0.0, float(yolo_cfg.get("infer_interval_s", 0.0))) * 1000.0)
    interval_ms = max(0, min(interval_ms, 1000))
    cv2.createTrackbar("yolo_interval_ms", YOLO_WINDOW, interval_ms, 1000, lambda x: None)


def run(cfg, args) -> None:
    hardware_cfg = cfg.get("hardware", {})
    perception_cfg = cfg.get("perception", {})
    control_cfg = cfg.get("control", {})
    runtime_cfg = cfg.get("runtime", {})

    cfg_mode = str(perception_cfg.get("mode", "lab")).lower()
    mode = (args.mode or cfg_mode).lower()
    if mode not in MODE_CHOICES:
        print(f"[WARN] 지원하지 않는 모드 '{mode}', lab으로 강제 전환합니다.")
        mode = "lab"

    hsv_cfg = perception_cfg.get("hsv", {})
    lab_cfg = perception_cfg.get("lab", {})

    show_windows = runtime_cfg.get("show_windows", True) and not args.headless
    enable_sliders = runtime_cfg.get("enable_sliders", True) and show_windows
    if show_windows:
        cv2.namedWindow(FRAME_WINDOW, cv2.WINDOW_NORMAL)
        cv2.namedWindow(BINARY_WINDOW, cv2.WINDOW_NORMAL)

    hardware = RaspbotHardware(
        use_led=hardware_cfg.get("use_led", True),
        use_beep=hardware_cfg.get("use_beep", True),
        led_on_start=hardware_cfg.get("led_on_start", True),
        beep_on_start=hardware_cfg.get("beep_on_start", True),
        servo_defaults=tuple(hardware_cfg.get("servo_defaults", (70, 10))),
        servo_neutral=tuple(hardware_cfg.get("servo_neutral", (90, 25))),
        led_mode=hardware_cfg.get("led_mode", 2),
        enable_mock=args.mock_hw,
    )

    camera = build_camera(hardware_cfg.get("camera", {}))

    pid = PIDController(
        kp=float(control_cfg.get("kp", 0.9)),
        ki=float(control_cfg.get("ki", 0.0)),
        kd=float(control_cfg.get("kd", 0.05)),
        output_limits=(
            -float(control_cfg.get("steer_limit", 80)),
            float(control_cfg.get("steer_limit", 80)),
        ),
    )

    controller = VehicleController(
        hardware=hardware,
        base_speed=int(control_cfg.get("base_speed", 40)),
        speed_limit=int(control_cfg.get("speed_limit", 120)),
        steer_scale=float(control_cfg.get("steer_scale", 1.0)),
        deadband=float(control_cfg.get("steer_deadband", 0.0)),
    )

    roi_top = perception_cfg.get("roi_top", 871)
    roi_bottom = perception_cfg.get("roi_bottom", 946)
    ipm_resolution = tuple(perception_cfg.get("ipm_resolution", (320, 240)))

    # 모드별 초기값
    if mode == "lab":
        detect_value = int(lab_cfg.get("detect_value", perception_cfg.get("detect_value", 120)))
        lab_red_l_min = int(lab_cfg.get("red_l_min", perception_cfg.get("lab_red_l_min", 30)))
        lab_red_a_min = int(lab_cfg.get("red_a_min", perception_cfg.get("lab_red_a_min", 150)))
        lab_red_b_min = int(lab_cfg.get("red_b_min", perception_cfg.get("lab_red_b_min", 140)))
        lab_gray_a_dev = int(lab_cfg.get("gray_a_dev", perception_cfg.get("lab_gray_a_dev", 15)))
        lab_gray_b_dev = int(lab_cfg.get("gray_b_dev", perception_cfg.get("lab_gray_b_dev", 15)))
    else:
        detect_value = int(hsv_cfg.get("detect_value", perception_cfg.get("detect_value", 120)))
        lab_red_l_min = lab_red_a_min = lab_red_b_min = lab_gray_a_dev = lab_gray_b_dev = 0

    turn_cfg = control_cfg.get("turn", {})
    turn_slope_thresh = float(turn_cfg.get("slope_thresh", 0.25))
    turn_offset_thresh = float(turn_cfg.get("offset_thresh", 0.3))
    turn_speed_scale = float(turn_cfg.get("speed_scale", 0.7))
    turn_steer_scale = float(turn_cfg.get("steer_scale", 1.3))
    heading_cfg = control_cfg.get("heading", {})
    heading_smooth_alpha = float(heading_cfg.get("smooth_alpha", 0.2))
    heading_connect_close_px = int(heading_cfg.get("connect_close_px", 1))
    heading_merge_gap_px = int(heading_cfg.get("merge_gap_px", 1))
    heading_p1_margin_px = int(heading_cfg.get("p1_margin_px", 1))
    heading_prev = 0.0

    # ===== YOLO 이벤트 + 미션 FSM 초기화 =====
    yolo_cfg = perception_cfg.get("yolo", {})
    yolo_enabled = bool(yolo_cfg.get("enabled", True))
    yolo_targets = yolo_cfg.get("targets", ["red", "green", "oo", "xx", "car"])
    yolo_min_area_ratio_init = {
        k.lower(): float(v)
        for k, v in (yolo_cfg.get("min_area_ratio", {}) or {}).items()
        if v is not None
    }
    cooldown_s_cfg = dict(yolo_cfg.get("cooldown_s", {}) or {})
    cooldown_s_cfg.setdefault("car", float(yolo_cfg.get("car_cooldown_s", 3.0)))
    yolo_infer_interval_s_init = max(0.0, float(yolo_cfg.get("infer_interval_s", 0.0)))

    yolo_detector = None
    if yolo_enabled:
        try:
            from ultralytics import YOLO  # type: ignore

            model_path = Path(yolo_cfg.get("model", Path(__file__).resolve().parents[2] / "models" / "yolo" / "best.pt"))
            if not model_path.is_absolute():
                model_path = Path(__file__).resolve().parents[2] / model_path
            if not model_path.exists():
                raise FileNotFoundError(f"YOLO 모델 파일을 찾을 수 없습니다: {model_path}")

            print(f"[INFO] YOLO 모델 로드: {model_path}")
            model = YOLO(str(model_path))
            yolo_detector = YoloEventDetector(
                model=model,
                target_names=yolo_targets,
                imgsz=int(yolo_cfg.get("imgsz", 320)),
                conf=float(yolo_cfg.get("conf", 0.5)),
                device=yolo_cfg.get("device"),
                confirm_frames=int(yolo_cfg.get("confirm_frames", 3)),
                cooldown_s=cooldown_s_cfg,
                min_area_ratio=yolo_min_area_ratio_init,
            )
        except Exception as e:
            print(f"[WARN] YOLO 초기화 실패: {e} → YOLO 비활성화")
            yolo_detector = None
    yolo_runner = YoloAsyncRunner(yolo_detector, infer_interval_s=yolo_infer_interval_s_init) if yolo_detector else None

    beep_seq = BeepSequencer(hardware)
    mission_cfg = cfg.get("mission", {}) or {}
    mission_fsm = MissionFSM(
        beep_seq=beep_seq,
        steer_limit=float(control_cfg.get("steer_limit", 80)),
        parking_cfg=mission_cfg.get("parking", {}),
        hazard_cfg=mission_cfg.get("hazard", {}),
    )

    if enable_sliders:
        create_trackbars(perception_cfg, control_cfg, hardware_cfg, runtime_cfg, mode)
        last_cam_settings = (
            int(hardware_cfg.get("camera", {}).get("brightness", 0)),
            int(hardware_cfg.get("camera", {}).get("contrast", 0)),
            int(hardware_cfg.get("camera", {}).get("saturation", 50)),
            int(hardware_cfg.get("camera", {}).get("exposure", 100)),
            int(hardware_cfg.get("camera", {}).get("gain", 0)),
        )
        servo_defaults = tuple(hardware_cfg.get("servo_defaults", (70, 10)))
        last_servo_angles = (
            int(servo_defaults[0]),
            int(min(servo_defaults[1], RaspbotHardware.SERVO_PITCH_LIMIT)),
        )

    fps_timer = FpsTimer(window=int(runtime_cfg.get("fps_window", 15)))

    last_time = time.perf_counter()
    motors_enabled = False
    motors_was_enabled = motors_enabled
    controller.stop()

    # 미션 FSM 상태에 따라 LED 모드 상시 유지 (주행/인지 로직과 분리)
    drive_led_mode = int(hardware.led_mode)
    mission_led_mode_by_state = {
        MissionFSM.DRIVE: drive_led_mode,  # 평시 주행: YAML 기본 모드(예: 1)
        MissionFSM.WAIT_TRAFFIC_LIGHT: 0,  # 빨간 신호 정지: OFF
        MissionFSM.HAZARD_ACTION: 5,  # 위험정지: 5
        MissionFSM.PARKING_APPROACH: 3,  # 주차 접근: 3
        MissionFSM.PARKING_HOLD: 0,  # 파킹: OFF
    }
    last_led_mode = None

    # LOST 복구(3초 정지 → 2초 후진)
    lost_wait_s = float(runtime_cfg.get("lost_recovery_wait_s", 3.0))
    lost_reverse_speed = int(runtime_cfg.get("lost_reverse_speed", 20))
    lost_reverse_duration_s = float(runtime_cfg.get("lost_reverse_duration_s", 2.0))
    lost_episode_start = None
    lost_reverse_until = 0.0
    lost_recovery_done = False

    print(f"=== Phase 1: 라인 추종 주행 시작 (mode={mode}) ===")
    print("키 입력:")
    print("  ESC/q : 프로그램 종료")
    print("  s     : 모터 토글 일시정지/재개 (초기 상태: 정지)")
    print("  SPACE : 일시정지 (아무 키나 누르면 재개)")

    try:
        while True:
            if enable_sliders:
                # ROI 및 검출 임계값 업데이트
                roi_top = cv2.getTrackbarPos("roi_top", VISION_WINDOW)
                roi_bottom = cv2.getTrackbarPos("roi_bottom", VISION_WINDOW)
                detect_value = cv2.getTrackbarPos("detect_value", VISION_WINDOW)

                # PID/속도 파라미터 업데이트 (trackbar는 정수이므로 스케일링)
                pid.kp = cv2.getTrackbarPos("pid_kp_x100", CONTROL_WINDOW) / 100.0
                pid.ki = cv2.getTrackbarPos("pid_ki_x100", CONTROL_WINDOW) / 100.0
                pid.kd = cv2.getTrackbarPos("pid_kd_x100", CONTROL_WINDOW) / 100.0
                base_speed_slider = cv2.getTrackbarPos("base_speed", CONTROL_WINDOW)
                steer_scale_slider = cv2.getTrackbarPos("steer_scale_x100", CONTROL_WINDOW) / 100.0

                # 카메라 설정 실시간 적용
                brightness = cv2.getTrackbarPos("brightness", CAMERA_WINDOW)
                contrast = cv2.getTrackbarPos("contrast", CAMERA_WINDOW)
                saturation = cv2.getTrackbarPos("saturation", CAMERA_WINDOW)
                exposure = cv2.getTrackbarPos("exposure", CAMERA_WINDOW)
                gain = cv2.getTrackbarPos("gain", CAMERA_WINDOW)
                cam_settings = (brightness, contrast, saturation, exposure, gain)
                if cam_settings != last_cam_settings:
                    camera.apply_settings(
                        brightness=brightness,
                        contrast=contrast,
                        saturation=saturation,
                        exposure=exposure,
                        gain=gain,
                    )
                    last_cam_settings = cam_settings

                # 서보 각도 실시간 적용 (카메라 앵글)
                servo1 = cv2.getTrackbarPos("servo1_yaw", CAMERA_WINDOW)
                servo2 = cv2.getTrackbarPos("servo2_pitch", CAMERA_WINDOW)
                if (servo1, servo2) != last_servo_angles:
                    hardware.set_servo(1, servo1)
                    hardware.set_servo(2, servo2)
                    last_servo_angles = (servo1, servo2)

                # 회전 감지/제어 파라미터 업데이트
                turn_slope_thresh = cv2.getTrackbarPos("turn_slope_thr_x100", CONTROL_WINDOW) / 100.0
                turn_offset_thresh = cv2.getTrackbarPos("turn_offset_thr_x100", CONTROL_WINDOW) / 100.0
                turn_speed_scale = cv2.getTrackbarPos("turn_speed_scale_x100", CONTROL_WINDOW) / 100.0
                turn_steer_scale = cv2.getTrackbarPos("turn_steer_scale_x100", CONTROL_WINDOW) / 100.0
                heading_smooth_alpha = cv2.getTrackbarPos("heading_smooth_x100", CONTROL_WINDOW) / 100.0
                heading_connect_close_px = cv2.getTrackbarPos("heading_connect_close_px", CONTROL_WINDOW)
                heading_merge_gap_px = cv2.getTrackbarPos("heading_merge_gap_px", CONTROL_WINDOW)
                heading_p1_margin_px = cv2.getTrackbarPos("heading_p1_margin_px", CONTROL_WINDOW)

                if mode == "lab":
                    lab_red_l_min = cv2.getTrackbarPos("lab_red_l_min", VISION_WINDOW)
                    lab_red_a_min = cv2.getTrackbarPos("lab_red_a_min", VISION_WINDOW)
                    lab_red_b_min = cv2.getTrackbarPos("lab_red_b_min", VISION_WINDOW)
                    lab_gray_a_dev = cv2.getTrackbarPos("lab_gray_a_dev", VISION_WINDOW)
                    lab_gray_b_dev = cv2.getTrackbarPos("lab_gray_b_dev", VISION_WINDOW)

                # YOLO 면적 임계 실시간 조정(x1000 스케일)
                yolo_min_area_ratio = {
                    "red": cv2.getTrackbarPos("yolo_area_red_x1000", YOLO_WINDOW) / 1000.0,
                    "green": cv2.getTrackbarPos("yolo_area_green_x1000", YOLO_WINDOW) / 1000.0,
                    "oo": cv2.getTrackbarPos("yolo_area_oo_x1000", YOLO_WINDOW) / 1000.0,
                    "xx": cv2.getTrackbarPos("yolo_area_xx_x1000", YOLO_WINDOW) / 1000.0,
                    "car": cv2.getTrackbarPos("yolo_area_car_x1000", YOLO_WINDOW) / 1000.0,
                }
                yolo_infer_interval_s = cv2.getTrackbarPos("yolo_interval_ms", YOLO_WINDOW) / 1000.0
            else:
                # 슬라이더 미사용 시 기본 설정 유지
                base_speed_slider = int(control_cfg.get("base_speed", 40))
                steer_scale_slider = float(control_cfg.get("steer_scale", 1.0))
                turn_slope_thresh = float(turn_cfg.get("slope_thresh", 0.25))
                turn_offset_thresh = float(turn_cfg.get("offset_thresh", 0.3))
                turn_speed_scale = float(turn_cfg.get("speed_scale", 0.7))
                turn_steer_scale = float(turn_cfg.get("steer_scale", 1.3))
                heading_smooth_alpha = float(heading_cfg.get("smooth_alpha", 0.2))
                heading_connect_close_px = int(heading_cfg.get("connect_close_px", 1))
                heading_merge_gap_px = int(heading_cfg.get("merge_gap_px", 1))
                heading_p1_margin_px = int(heading_cfg.get("p1_margin_px", 1))
                if mode == "lab":
                    detect_value = int(lab_cfg.get("detect_value", perception_cfg.get("detect_value", 120)))
                    lab_red_l_min = int(lab_cfg.get("red_l_min", perception_cfg.get("lab_red_l_min", 30)))
                    lab_red_a_min = int(lab_cfg.get("red_a_min", perception_cfg.get("lab_red_a_min", 150)))
                    lab_red_b_min = int(lab_cfg.get("red_b_min", perception_cfg.get("lab_red_b_min", 140)))
                    lab_gray_a_dev = int(lab_cfg.get("gray_a_dev", perception_cfg.get("lab_gray_a_dev", 15)))
                    lab_gray_b_dev = int(lab_cfg.get("gray_b_dev", perception_cfg.get("lab_gray_b_dev", 15)))
                else:
                    detect_value = int(hsv_cfg.get("detect_value", perception_cfg.get("detect_value", 120)))

                yolo_min_area_ratio = dict(yolo_min_area_ratio_init)
                yolo_infer_interval_s = max(0.0, float(yolo_cfg.get("infer_interval_s", 0.0)))

            frame = camera.read()
            height, width = frame.shape[:2]

            pts_src, top_y, bottom_y = calculate_roi_points(width, height, roi_top, roi_bottom)
            frame_with_roi = apply_roi_overlay(frame, pts_src, width, height, top_y, bottom_y)

            warped, _ = warp_perspective(frame, pts_src, ipm_resolution)
            if mode == "lab":
                binary = lane_detection_lab.detect_road_lines(
                    warped,
                    detect_value,
                    lab_red_l_min,
                    lab_red_a_min,
                    lab_red_b_min,
                    lab_gray_a_dev,
                    lab_gray_b_dev,
                )
            else:
                gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
                binary = lane_detection_hsv.detect_road_lines(warped, gray, detect_value)

            error_norm, centroid_x = lane_detection_lab.compute_lane_error(binary)
            slope_norm, heading_centers, heading_offset, target_mask = lane_detection_lab.estimate_heading(
                binary,
                connect_close_px=heading_connect_close_px,
                merge_gap_px=heading_merge_gap_px,
                p1_margin_px=heading_p1_margin_px,
            )
            if heading_offset is not None:
                heading_prev = heading_smooth_alpha * heading_offset + (1 - heading_smooth_alpha) * heading_prev
                heading_used = heading_prev
            else:
                heading_used = None
            now = time.perf_counter()
            dt = now - last_time
            last_time = now

            # 논블로킹 비프 시퀀스 진행
            beep_seq.tick(now)

            if heading_used is None:
                direction = "LOST"
                steering_output = 0.0
            else:
                steering_output = pid.update(heading_used, dt)
                direction = "STRAIGHT"

            # 진행 상태 판별 (좌/우 회전/직진/길잃음) - heading 기반
            state = direction
            if heading_used is None:
                state = "LOST"
            else:
                turn_by_heading = slope_norm is not None and abs(slope_norm) > turn_slope_thresh
                turn_by_offset = abs(heading_used) > turn_offset_thresh
                if turn_by_heading or turn_by_offset:
                    if heading_used > 0:
                        state = "TURN_RIGHT"
                    else:
                        state = "TURN_LEFT"
                else:
                    state = "STRAIGHT"

            # 상태별 속도/조향 스케일 조정
            effective_speed = base_speed_slider
            effective_steer_scale = steer_scale_slider
            if state.startswith("TURN"):
                effective_speed = int(base_speed_slider * turn_speed_scale)
                effective_steer_scale = steer_scale_slider * turn_steer_scale

            controller.base_speed = effective_speed
            controller.steer_scale = effective_steer_scale

            # YOLO 추론 → 안정화 이벤트
            detections = {}
            triggers = {}
            yolo_raw_boxes = []
            yolo_last_ts = 0.0
            if yolo_runner is not None:
                yolo_runner.update_settings(infer_interval_s=yolo_infer_interval_s, min_area_ratio=yolo_min_area_ratio)
                yolo_runner.submit_frame(frame)
                detections, triggers, yolo_raw_boxes, yolo_last_ts = yolo_runner.poll()

            # 미션 FSM으로 override
            mission_cmd = mission_fsm.update(
                lane_steering=steering_output,
                lane_speed=effective_speed,
                detections=detections,
                triggers=triggers,
                now=now,
            )
            controller.base_speed = mission_cmd.base_speed
            desired_led_mode = mission_led_mode_by_state.get(mission_cmd.state, drive_led_mode)
            if desired_led_mode != last_led_mode:
                hardware.set_led_mode(desired_led_mode)
                last_led_mode = desired_led_mode

            applied_left_speed = 0
            applied_right_speed = 0
            if motors_enabled:
                if mission_cmd.force_stop:
                    controller.stop()
                    direction = mission_cmd.state
                    lost_episode_start = None
                    lost_reverse_until = 0.0
                    lost_recovery_done = False
                elif state == "LOST" and mission_cmd.state == "DRIVE":
                    # LOST 에피소드 시작 시점 기록
                    if lost_episode_start is None:
                        lost_episode_start = now
                        lost_recovery_done = False

                    if now < lost_reverse_until:
                        hardware.drive(-lost_reverse_speed, -lost_reverse_speed)
                        applied_left_speed = -lost_reverse_speed
                        applied_right_speed = -lost_reverse_speed
                        direction = "LOST_REVERSE"
                    else:
                        elapsed = now - float(lost_episode_start)
                        if (not lost_recovery_done) and elapsed >= lost_wait_s:
                            lost_reverse_until = now + lost_reverse_duration_s
                            lost_recovery_done = True
                            hardware.drive(-lost_reverse_speed, -lost_reverse_speed)
                            applied_left_speed = -lost_reverse_speed
                            applied_right_speed = -lost_reverse_speed
                            direction = "LOST_REVERSE"
                        else:
                            controller.stop()
                            direction = "LOST"
                            if runtime_cfg.get("fail_safe_beep", True):
                                hardware.beep(0.05)
                else:
                    lost_episode_start = None
                    lost_reverse_until = 0.0
                    lost_recovery_done = False
                    applied_left_speed, applied_right_speed, drive_dir = controller.drive(mission_cmd.steering)
                    if mission_cmd.state != "DRIVE":
                        direction = mission_cmd.state
                    else:
                        direction = state if state != "STRAIGHT" else drive_dir
            else:
                # 모터 일시정지 상태: 출력만 갱신, 실제 구동은 중단
                if motors_was_enabled:
                    controller.stop()
                direction = "PAUSE"
                state = "PAUSE"
                lost_episode_start = None
                lost_reverse_until = 0.0
                lost_recovery_done = False

            fps = fps_timer.lap()

            if runtime_cfg.get("print_debug", False) and motors_enabled:
                print(
                    f"heading_err={heading_used if heading_used is not None else 'None'} "
                    f"slope={slope_norm if slope_norm is not None else 'None'} "
                    f"state={state} "
                    f"mission={mission_cmd.state} "
                    f"steer={mission_cmd.steering:.2f} "
                    f"speed_l={applied_left_speed} "
                    f"speed_r={applied_right_speed}"
                )

            if show_windows:
                debug_input = cv2.bitwise_not(target_mask) if target_mask is not None else binary
                debug_binary = visualize_binary_debug(
                    debug_input,
                    direction,
                    centroid_x,
                    mission_cmd.steering,
                    fps,
                    heading=slope_norm,
                    heading_offset=heading_used,
                    turn_thresholds=(turn_slope_thresh, turn_offset_thresh),
                    centers=heading_centers,
                )
                # YOLO 시각화(크기 조건과 무관하게 raw 박스 전부 표시)
                # 트리거된 클래스는 노란색, 그 외는 클래스별 기본색
                display_frame = frame_with_roi.copy()
                if yolo_raw_boxes:
                    base_colors = {
                        "red": (0, 0, 255),
                        "green": (0, 255, 0),
                        "oo": (255, 255, 255),
                        "xx": (255, 0, 0),
                        "car": (255, 0, 0),
                    }
                    trigger_color = (0, 255, 255)
                    for box in yolo_raw_boxes:
                        cls_name = box.name
                        x1, y1, x2, y2 = box.bbox_xyxy
                        x1_i, y1_i, x2_i, y2_i = int(x1), int(y1), int(x2), int(y2)

                        color = base_colors.get(cls_name, (200, 200, 200))
                        thr = yolo_min_area_ratio.get(cls_name)
                        if thr is not None and box.area_ratio >= thr:
                            color = trigger_color

                        cv2.rectangle(display_frame, (x1_i, y1_i), (x2_i, y2_i), color, 2)

                        label = cls_name or str(box.cls_id)
                        cv2.putText(
                            display_frame,
                            f"{label} {box.conf:.2f}",
                            (x1_i, max(0, y1_i - 5)),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            color,
                            1,
                        )

                cv2.imshow(FRAME_WINDOW, display_frame)
                cv2.imshow(BINARY_WINDOW, debug_binary)

                key = cv2.waitKey(1) & 0xFF
                try:
                    if cv2.getWindowProperty(FRAME_WINDOW, cv2.WND_PROP_VISIBLE) < 1:
                        break
                    if cv2.getWindowProperty(BINARY_WINDOW, cv2.WND_PROP_VISIBLE) < 1:
                        break
                except cv2.error:
                    pass
                if key in (27, ord("q")):
                    break
                elif key == ord("s"):  # 's' 키: 모터 토글
                    motors_enabled = not motors_enabled
                    controller.stop()
                    if motors_enabled:
                        print("모터 재개")
                    else:
                        print("모터 일시정지 (영상/슬라이더 계속)")
                elif key == 32:  # 스페이스바: 일시정지
                    controller.stop()
                    print("일시정지. 아무 키나 누르면 재개...")
                    cv2.waitKey()
            else:
                time.sleep(runtime_cfg.get("headless_delay", 0.01))
            motors_was_enabled = motors_enabled

    finally:
        controller.stop()
        if yolo_runner is not None:
            yolo_runner.stop()
        camera.release()
        hardware.cleanup()
        if show_windows:
            cv2.destroyAllWindows()
        print("정상 종료되었습니다.")


def main():
    args = parse_args()
    cfg = load_config(args.config)
    run(cfg, args)


if __name__ == "__main__":
    sys.exit(main())
