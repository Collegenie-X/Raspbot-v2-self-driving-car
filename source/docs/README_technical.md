# P Project (Raspbot V2)

자율주행 Phase 1(주행 가능 도로 전체를 라인 추종하는 확장판) 파이프라인. 하드웨어 제어, 인지, 제어, 실행 루프를 모듈화했고 설정은 YAML 한 곳에 모아 관리합니다.

## 리포 구조
```
P_project/
├ Readme.md
├ configs/                 # 설정(YAML)
│  └ phase1_pid.yaml       # ROI, Lab/HSV 임계, PID/턴/헤딩, YOLO/미션/LOST 복구 옵션
├ models/
│  └ yolo/
│     └ best.pt            # 학습된 YOLOv8 모델(라벨: red/green/oo/xx/car)
├ scripts/
│  └ run_phase1.py         # 실행 엔트리(phase1_baseline 호출)
│
└ raspbot/                 # 소스 패키지
   ├ hardware/             # 카메라/모터/서보 HAL
   │  ├ camera.py               # 카메라 HAL (Camera, CameraConfig)
   │  └ raspbot.py              # RaspbotHardware/MockRaspbot
   │
   ├ control/              # PID/차량 제어
   │  ├ pid.py                  # PIDController
   │  └ vehicle_controller.py   # VehicleController
   │
   ├ perception/           # 인지
   │  ├ lane_detection_hsv.py   # HSV 차선 검출
   │  ├ lane_detection_lab.py   # Lab 차선 검출/헤딩 추정
   │  ├ preprocessing.py        # ROI/IPM 계산
   │  ├ visualization.py        # 디버그 오버레이
   │  ├ yolo_events.py          # YOLO 안정화 이벤트 공급자
   │  └ yolo_stop_on_red.py     # YOLO 단독 정지 테스트
   │
   ├ planning/             # 행동 계획/미션 FSM
   │  └ mission_fsm.py          # Layer B 미션 FSM + 논블로킹 비프 시퀀서
   │
   ├ runtime/
   │  └ phase1_baseline.py      # HSV/Lab 통합 실행 루프
   │
   └ utils/                # FPS 측정/설정 로더
      ├ config_loader.py        # YAML 로더
      └ timing.py               # FPSTimer
```

## 실행하기
```bash
python3 scripts/run_phase1.py                # 기본 설정
python3 scripts/run_phase1.py --mode lab     # Lab 모드 명시
python3 scripts/run_phase1.py --mode hsv     # HSV 모드 명시
python3 scripts/run_phase1.py --config configs/phase1_pid.yaml  # 다른 설정 파일 사용
python3 scripts/run_phase1.py --mock-hw      # 모터/서보 호출을 콘솔 로그로 대체
python3 scripts/run_phase1.py --headless     # OpenCV 윈도우 없이 실행
```

## 라인 검출 모드 선택
- 설정: `perception.mode: lab | hsv` (default: lab)
- CLI: `python3 scripts/run_phase1.py --mode lab` 또는 `--mode hsv` (설정값을 덮어씀)
- 파일 교체 없이 모드에 따라 트랙바/파라미터도 자동으로 분기됩니다.

## 설정 파일(주요 항목)
- `perception`  
  - `mode`: `lab | hsv`  
  - 공통: `roi_top`, `roi_bottom`, `ipm_resolution`  
  - `hsv.detect_value`: 회색 밝기 임계  
  - `lab.detect_value`: L 밝기 임계  
  - `lab.red_l_min/red_a_min/red_b_min`, `lab.gray_a_dev/gray_b_dev`: Lab 임계값(L/a/b 최소 혹은 a/b 편차)
  - `yolo`: YOLOv8 이벤트 인식 설정(모델 경로/입력크기/신뢰도, Confirm/쿨다운, `min_area_ratio.{red,green,oo,xx,car}`)
- `control`  
  - `base_speed`, `speed_limit`, `steer_limit`, `steer_scale`, `steer_deadband`  
  - PID: `kp`, `ki`, `kd`  
  - `turn`: `slope_thresh`, `offset_thresh`, `speed_scale`, `steer_scale`  
  - `heading`: `smooth_alpha`, `connect_close_px`, `merge_gap_px`, `p1_margin_px`
- `runtime`  
  - `show_windows`, `print_debug`, `fail_safe_beep`, `fps_window`, `headless_delay`, `enable_sliders`
  - LOST 복구: `lost_recovery_wait_s`, `lost_reverse_speed`, `lost_reverse_duration_s`
- `mission`
  - `hazard.beep_delay`
  - `parking.approach_speed`, `parking.missing_frames`, `parking.steer_kp`

## 런타임 제어(키)
- `ESC` / `q`: 종료
- `s`: 모터 시작/일시정지 토글(초기 상태: 정지)
- `SPACE`: 일시정지 후 아무 키나 눌러 재개

## 슬라이더(Windows 활성 시)
- ROI/밝기 임계: `roi_top`, `roi_bottom`, `detect_value`
- Lab 모드 전용: `lab_red_l_min`, `lab_red_a_min`, `lab_red_b_min`, `lab_gray_a_dev`, `lab_gray_b_dev`
- 조향/속도: `pid_kp_x100`, `pid_ki_x100`, `pid_kd_x100`, `base_speed`, `steer_scale_x100`
- 턴 파라미터: `turn_slope_thr_x100`, `turn_offset_thr_x100`, `turn_speed_scale_x100`, `turn_steer_scale_x100`
- 헤딩 파라미터: `heading_smooth_x100`, `heading_connect_close_px`, `heading_merge_gap_px`, `heading_p1_margin_px`
- 카메라/서보: `brightness`, `contrast`, `saturation`, `exposure`, `gain`, `servo1_yaw`, `servo2_pitch`
- YOLO 면적 임계: `yolo_area_red_x1000`, `yolo_area_green_x1000`, `yolo_area_oo_x1000`, `yolo_area_xx_x1000`, `yolo_area_car_x1000`

## 주요 처리 흐름
1) 프레임 입력(원본)  
2) ROI 계산/오버레이 → IPM 변환 → HSV/Lab 차선 이진화  
3) 헤딩 추정 → PID로 조향 계산  
4) Layer A(차선 상태: STRAIGHT/TURN/LOST)로 속도·조향 스케일링  
5) 같은 원본 프레임으로 YOLO 추론 수행  
   - `yolo_events`에서 Confirm/min_area_ratio/cooldown 안정화 후 이벤트 생성  
6) Layer B(미션 FSM: DRIVE/WAIT_TRAFFIC_LIGHT/HAZARD/PARKING)로 최종 출력 override  
7) LOST가 3초 지속되면 2초 후진 복구 수행  
8) 모터/서보 출력 및 디버그 시각화(차선 바이너리 + YOLO 박스)

## 디버그/로그
- 모터 활성 상태에서만 터미널 로그 출력: `heading_err`, `slope`, `state`, `mission`, `steer`, `speed_l/r`
- OpenCV 창: `phase1/frame`(ROI+YOLO 박스 오버레이), `phase1/binary`(선택 도로 영역 강조)
- YOLO 박스 색: 클래스 기본색, 임계(`min_area_ratio`) 이상이면 노란색
- 모터 정지 시에는 출력/구동이 멈추며, `target_mask`를 반전한 디버그 바이너리가 계속 표시됩니다.

## 개발 팁
- Lab 임계 조정은 `detect_value`(L 밝기)와 `lab_red_*`/`lab_gray_*` 슬라이더를 함께 조절해 그림자·반사에 맞추세요.

