#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os

# Raspbot 라이브러리 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib", "raspbot"))

import cv2
import numpy as np
import random
import time
from Raspbot_Lib import Raspbot
from ultralytics import YOLO

# =========================
# UI / OUTPUT SWITCH
# =========================
UI_ENABLED   = True
IMSHOW_ON    = True

def imshow(name, img):
    if UI_ENABLED and IMSHOW_ON:
        cv2.imshow(name, img)

def wait_key(delay=1):
    if UI_ENABLED:
        return cv2.waitKey(delay) & 0xFF
    time.sleep(delay / 1000.0)
    return 255

# =========================
# YOLO 설정
# =========================
YOLO_USE_GRAY = False
YOLO_MODEL_PATH = "/home/pi/models/color_best.pt"
YOLO_IMGSZ = 256
YOLO_EVERY_N_FRAMES = 3
YOLO_ENABLED = True

# =========================
# class id
# =========================
OBSTACLE_ID = 0
MARK_O_ID   = 1
MARK_X_ID   = 2
TL_GREEN_ID = 3
TL_RED_ID   = 4

CLASS_ID_TO_NAME = {
    0: "obstacle",
    1: "mark_O",
    2: "mark_X",
    3: "traffic_green",
    4: "traffic_red",
}

# =========================
# Traffic Light FSM params
# =========================
TL_RED_MIN_CONF = 0.25
TL_GREEN_MIN_CONF = 0.25
TL_CONSEC = 2
TL_BEEP_DELAY_SEC = 0.20
TL_HOLD_SEC = 1.5

# =========================
# Obstacle params
# =========================
OBSTACLE_MIN_CONF = 0.35
OBSTACLE_CONSEC = 2
OB_STOP_SEC = 1.0

ob_streak = 0
ob_active_until = 0.0
OB_RETRIGGER_COOLDOWN_SEC = 3
ob_cooldown_until = 0.0

# =========================
# Parking params (확정 주차 FSM)
# =========================
MARK_O_MIN_CONF = 0.25
MARK_X_MIN_CONF = 0.25

# --- O priority hold (O를 잠깐이라도 봤으면 일정 시간 X 무시)
O_PRIORITY_HOLD_SEC = 1.2

# --- park trigger (주차 모드 진입 조건)
PARK_TRIGGER_MIN_AREA_RATIO = 0.005
PARK_TRIGGER_CENTER_PX      = 220
PARK_CONSEC = 1

# ✅ "최근에 봤다" 판정 시간
PARK_SEEN_RECENT_SEC = 0.35

# =========================
# ✅ 확정 주차 FSM 파라미터
# =========================
PARK_CENTER_PX = 35
PARK_CENTER_PX_APPROACH = 60

PARK_AREA_ARM  = 0.06
PARK_AREA_STOP_MIN = 0.03

PARK_ARM_CONSEC = 6
PARK_LOST_STOP_CONSEC = 3

PARK_USE_DROP_STOP = True
PARK_AREA_DROP_RATIO = 0.65

PARK_EMA_ALPHA = 0.35

PARK_SPEED_RATIO_APPROACH = 0.55
PARK_SPEED_RATIO_ARMED    = 0.40

# 기존 creep_with_steer는 유지하되,
# ✅ "휙 도는" 문제 때문에 주차에서는 아래 Smooth Follow를 사용하도록 변경
PARK_O_ALIGN_DEAD_PX  = 20  # (기존 25보다 조금 타이트)

# =========================
# ✅ PASS(지나감) 판정
# =========================
PARK_PASS_PEAK_MIN = 0.045
PARK_PASS_LOST_CONSEC = 2

# =========================
# ✅ O 추종을 '더 확실하지만 부드럽게' 만드는 튜닝 (핵심)
# =========================
PARK_OFF_CLIP_PX = 160            # bbox 순간 튐 방지 (오프셋 클램프)
PARK_ALIGN_DEAD_PX = 10           # 이 안이면 거의 직진
PARK_KP_MIN = 0.06                # 멀리 있을 때 조향 게인
PARK_KP_MAX = 0.16                # 가까울 때 조향 게인
PARK_STEER_MAX_RATIO = 0.45       # base_speed 대비 최대 조향량 비율
PARK_STEER_SLEW_PER_SEC = 220.0   # 조향 변화율 제한(휙 도는 문제 해결)
PARK_SLOW_OFF_PX = 90             # 오프셋 크면 전진 속도 자동 감속
PARK_SLOW_MAX_DROP = 0.45         # 감속 최대 비율

# =========================
# Parking states
# =========================
park_mode = False
park_done = False
park_streak = 0

park_fsm = "SEARCH"   # SEARCH / APPROACH / ARMED / STOP
park_arm_cnt = 0
park_lost_cnt = 0
park_area_peak = 0.0

last_o_det = None
last_o_conf = 0.0
last_o_area_ratio = 0.0
last_o_center_off = 0.0
last_o_time = 0.0

park_area_ema = 0.0
park_off_ema  = 0.0
park_ema_inited = False

# ✅ PASS 판정 상태
park_pass_ready = False
park_pass_lost_cnt = 0

# ✅ Smooth Follow 내부 상태
park_last_follow_t = time.time()
park_steer_cmd = 0.0

# =========================
# Mark X avoid params
# =========================
X_CONSEC = 2

X_STOP_SEC    = 0.35
X_TURN_SEC    = 0.75
X_RECOVER_SEC = 0.25

X_RETRIGGER_COOLDOWN_SEC = 1.5
X_LOST_INFER_TO_REARM = 3
X_LOCK_MAX_SEC = 4.0

x_turn_dir = "PENDING"
x_bbox_cand = "LEFT"

x_stop_acc_L = 0.0
x_stop_acc_R = 0.0
x_stop_acc_n = 0

x_streak = 0
x_phase_start = 0.0
x_active_until = 0.0
x_cooldown_until = 0.0

x_locked = False
x_lock_time = 0.0
x_lost_infer_count = 0

# =========================
# Global state
# =========================
tl_state = "GO"
tl_red_streak = 0
tl_green_streak = 0
tl_last_stop_time = 0.0
TL_PHASE = "GO"

YOLO_CONF = 0.25
YOLO_CONTROL_ENABLE = True

# now 전역(함수들이 참조)
now = 0.0

# =========================
# 기본 속도/카메라/필터
# =========================
DEFAULT_SPEED_UP = 50
DEFAULT_SPEED_DOWN = 25

DEFAULT_DETECT_VALUE = 150
DEFAULT_BRIGHTNESS = 0
DEFAULT_CONTRAST = 0
DEFAULT_SATURATION = 0
DEFAULT_GAIN = 0

DEFAULT_R_WEIGHT = 20
DEFAULT_G_WEIGHT = 25
DEFAULT_B_WEIGHT = 40

DEFAULT_DIRECTION_THRESHOLD = 35000
DEFAULT_UP_THRESHOLD = 220000
CENTER_CLEAR_THRESHOLD = 0.2

DEFAULT_SERVO_1 = 74
DEFAULT_SERVO_2 = 5

USE_LED_EFFECTS = True
LED_ON_START = True

USE_BEEP = True
BEEP_ON_START = True

mouse_use = True

led_state = LED_ON_START
beep_state = BEEP_ON_START
frame_count = 0

# =========================
# Hardware init
# =========================
def initialize_raspbot():
    return Raspbot()

def initialize_camera(width=320, height=240):
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_BRIGHTNESS, DEFAULT_BRIGHTNESS)
    cap.set(cv2.CAP_PROP_CONTRAST, DEFAULT_CONTRAST)
    cap.set(cv2.CAP_PROP_SATURATION, DEFAULT_SATURATION)
    cap.set(cv2.CAP_PROP_GAIN, DEFAULT_GAIN)

    ret, frame = cap.read()
    if not ret or frame is None:
        raise RuntimeError("Cannot read frame from camera")
    return cap

def setup_initial_hardware_state(bot):
    global led_state, beep_state

    if led_state and USE_LED_EFFECTS:
        bot.Ctrl_WQ2812_ALL(1, 2)
    else:
        bot.Ctrl_WQ2812_ALL(0, 0)

    bot.Ctrl_BEEP_Switch(0)

    bot.Ctrl_Servo(1, DEFAULT_SERVO_1)
    bot.Ctrl_Servo(2, DEFAULT_SERVO_2)

    for i in range(4):
        bot.Ctrl_Muto(i, 0)

bot = initialize_raspbot()
cap = initialize_camera()
setup_initial_hardware_state(bot)

# =========================
# YOLO load
# =========================
try:
    yolo_model = YOLO(YOLO_MODEL_PATH)
except Exception:
    yolo_model = None
    YOLO_ENABLED = False

# =========================
# YOLO utils
# =========================
def run_yolo_inference(frame, model, imgsz=320, conf=0.35):
    if model is None:
        return [], None

    if YOLO_USE_GRAY:
        g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_in = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
    else:
        frame_in = frame

    results = model.predict(frame_in, imgsz=imgsz, conf=conf, verbose=False)
    r = results[0]

    dets = []
    if r.boxes is not None and len(r.boxes) > 0:
        for b in r.boxes:
            cls = int(b.cls[0].item())
            c = float(b.conf[0].item())
            x1, y1, x2, y2 = b.xyxy[0].tolist()
            dets.append({"cls": cls, "conf": c, "xyxy": (x1, y1, x2, y2)})

    return dets, frame_in

def draw_dets_light(frame, dets):
    out = frame.copy()
    for d in dets:
        cls = int(d["cls"])
        conf = float(d["conf"])
        x1, y1, x2, y2 = map(int, d["xyxy"])
        name = CLASS_ID_TO_NAME.get(cls, str(cls))
        cv2.rectangle(out, (x1, y1), (x2, y2), (0, 255, 255), 2, lineType=cv2.LINE_8)
        cv2.putText(out, f"{name}:{conf:.2f}", (x1, max(15, y1 - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, lineType=cv2.LINE_8)
    return out

def get_best_conf(dets, cls_id):
    best = 0.0
    for d in dets:
        if int(d.get("cls", -1)) == int(cls_id):
            best = max(best, float(d.get("conf", 0.0)))
    return best

def get_best_det(dets, cls_id):
    best = None
    best_c = 0.0
    for d in dets:
        if int(d.get("cls", -1)) == int(cls_id):
            c = float(d.get("conf", 0.0))
            if c > best_c:
                best_c = c
                best = d
    return best, best_c

def det_geom(det, frame_w, frame_h):
    x1, y1, x2, y2 = det["xyxy"]
    w = max(1.0, (x2 - x1))
    h = max(1.0, (y2 - y1))
    area_ratio = (w * h) / float(frame_w * frame_h)
    cx = (x1 + x2) * 0.5
    center_off = cx - (frame_w * 0.5)
    return area_ratio, center_off

def is_o_priority(now_local):
    return (last_o_det is not None) and ((now_local - last_o_time) < O_PRIORITY_HOLD_SEC) and (last_o_conf >= MARK_O_MIN_CONF)

def apply_mark_priority(dets):
    if is_o_priority(time.time()):
        return [d for d in dets if int(d.get("cls", -1)) != int(MARK_X_ID)]

    o_conf = get_best_conf(dets, MARK_O_ID)
    x_conf = get_best_conf(dets, MARK_X_ID)
    o_seen = (o_conf >= MARK_O_MIN_CONF)
    x_seen = (x_conf >= MARK_X_MIN_CONF)
    if o_seen and x_seen:
        dets = [d for d in dets if int(d.get("cls", -1)) != int(MARK_X_ID)]
    return dets

# =========================
# BEEP Scheduler (non-blocking)
# =========================
beep_task = None
ob_seen_count = 0

def _start_beep_steps(steps, delay_sec=0.0):
    global beep_task, beep_state
    if (not USE_BEEP) or (not beep_state):
        return
    beep_task = {"steps": steps, "i": 0, "t": time.time() + delay_sec, "armed": True}
    bot.Ctrl_BEEP_Switch(0)

def start_beep_pattern(name):
    if not USE_BEEP:
        return
    if name == "TL_RED":
        steps = []
        for _ in range(3):
            steps += [(1, 0.15), (0, 0.10)]
        steps += [(0, 0.01)]
        _start_beep_steps(steps, delay_sec=TL_BEEP_DELAY_SEC)
        return
    if name == "OB1":
        _start_beep_steps([(1, 0.80), (0, 0.10), (0, 0.01)])
        return
    if name == "OB2":
        _start_beep_steps([(1, 0.40), (0, 0.12), (1, 0.40), (0, 0.10), (0, 0.01)])
        return
    if name == "OB3":
        _start_beep_steps([(1, 0.20), (0, 0.10), (1, 0.20), (0, 0.10), (1, 0.20), (0, 0.10), (0, 0.01)])
        return

def service_beep_task():
    global beep_task
    if not USE_BEEP or beep_task is None:
        return

    now_local = time.time()

    if beep_task.get("armed", False):
        if now_local < beep_task["t"]:
            return
        beep_task["armed"] = False
        beep_task["t"] = now_local
        bot.Ctrl_BEEP_Switch(1 if beep_task["steps"][0][0] else 0)
        return

    steps = beep_task["steps"]
    i = beep_task["i"]
    t0 = beep_task["t"]

    on, dur = steps[i]
    if now_local - t0 >= dur:
        i += 1
        if i >= len(steps):
            beep_task = None
            if not beep_state:
                bot.Ctrl_BEEP_Switch(0)
            return
        beep_task["i"] = i
        beep_task["t"] = now_local
        bot.Ctrl_BEEP_Switch(1 if steps[i][0] else 0)

def is_beep_running():
    return beep_task is not None

# =========================
# Car control
# =========================
def set_motor_speeds(m0, m1, m2, m3):
    if not mouse_use:
        bot.Ctrl_Muto(0, 0); bot.Ctrl_Muto(1, 0); bot.Ctrl_Muto(2, 0); bot.Ctrl_Muto(3, 0)
        return
    bot.Ctrl_Muto(0, int(m0)); bot.Ctrl_Muto(1, int(m1)); bot.Ctrl_Muto(2, int(m2)); bot.Ctrl_Muto(3, int(m3))

def car_run(speed_left, speed_right):
    set_motor_speeds(speed_left, speed_left, speed_right, speed_right)

def car_stop():
    set_motor_speeds(0, 0, 0, 0)

def creep_with_steer(off_px, fwd_sp=18, steer_sp=8):
    fwd_sp = int(np.clip(fwd_sp, 10, 255))
    steer_sp = int(np.clip(steer_sp, 0, fwd_sp - 1))

    if abs(off_px) <= PARK_O_ALIGN_DEAD_PX:
        car_run(fwd_sp, fwd_sp)
        return

    if off_px > 0:
        set_motor_speeds(fwd_sp, fwd_sp, fwd_sp - steer_sp, fwd_sp - steer_sp)
    else:
        set_motor_speeds(fwd_sp - steer_sp, fwd_sp - steer_sp, fwd_sp, fwd_sp)

def car_left(speed_left, speed_right):
    set_motor_speeds(-speed_left, -speed_left, speed_right, speed_right)

def car_right(speed_left, speed_right):
    set_motor_speeds(speed_left, speed_left, -speed_right, -speed_right)

def car_back(speed_left, speed_right):
    set_motor_speeds(-speed_left, -speed_left, -speed_right, -speed_right)

def set_led_effect(mode):
    global led_state
    if not USE_LED_EFFECTS or not led_state:
        return
    bot.Ctrl_WQ2812_ALL(1, mode)

POSTURE_DEADZONE_RATIO = 0.7
POSTURE_MAX_DELTA_RATIO = 0.2

def control_car_with_posture(direction, up_speed, down_speed, hist_left, hist_right, direction_threshold):
    if direction == "LEFT":
        car_left(down_speed, up_speed)
        set_led_effect(3)
        return
    if direction == "RIGHT":
        car_right(up_speed, down_speed)
        set_led_effect(3)
        return

    base_speed = up_speed
    diff = hist_right - hist_left
    th = max(1, direction_threshold)
    deadzone = th * POSTURE_DEADZONE_RATIO

    if abs(diff) < deadzone:
        car_run(base_speed, base_speed)
        set_led_effect(1)
        return

    norm = np.clip(diff / th, -1.0, 1.0)
    max_delta = int(base_speed * POSTURE_MAX_DELTA_RATIO)
    delta = int(norm * max_delta)

    left_speed  = int(np.clip(base_speed - delta,  0, 255))
    right_speed = int(np.clip(base_speed + delta,  0, 255))

    set_motor_speeds(left_speed, left_speed, right_speed, right_speed)
    set_led_effect(1)

# =========================
# ✅ 주차용 Smooth Follow (휙 도는 문제 해결 + 더 세밀한 추종)
# =========================
def follow_o_smooth(off_px, area_ratio, base_speed):
    """
    - off_px(픽셀) 기반 P제어 조향
    - area_ratio로 '가까울수록' 게인 조금 증가
    - steer 변화율 제한(slew)로 급회전 방지
    - off가 크면 전진 속도 자동 감속
    """
    global park_last_follow_t, park_steer_cmd

    t = time.time()
    dt = t - park_last_follow_t
    if dt <= 0.0:
        dt = 0.02
    park_last_follow_t = t

    off = float(np.clip(off_px, -PARK_OFF_CLIP_PX, PARK_OFF_CLIP_PX))

    # 가까울수록 게인 up (0~PARK_AREA_ARM 구간만 사용)
    a_norm = float(np.clip(area_ratio / max(1e-6, PARK_AREA_ARM), 0.0, 1.0))
    kp = PARK_KP_MIN + (PARK_KP_MAX - PARK_KP_MIN) * a_norm

    # 타겟 조향량(픽셀 -> 속도차)
    steer_target = kp * off

    # 최대 조향량(속도 비율 기반)
    bs = int(np.clip(base_speed, 10, 255))
    steer_max = int(np.clip(bs * PARK_STEER_MAX_RATIO, 8, 120))
    steer_target = float(np.clip(steer_target, -steer_max, steer_max))

    # 조향 변화율 제한(휙 도는 문제 핵심 해결)
    max_step = PARK_STEER_SLEW_PER_SEC * dt
    park_steer_cmd += float(np.clip(steer_target - park_steer_cmd, -max_step, max_step))

    # 데드존
    if abs(off) <= PARK_ALIGN_DEAD_PX:
        park_steer_cmd *= 0.6

    # 오프셋이 크면 전진 속도 자동 감속 (회전하면서 앞으로 밀고 가지 않게)
    off_mag = abs(off)
    slow_ratio = np.clip(off_mag / max(1.0, PARK_SLOW_OFF_PX), 0.0, 1.0)
    speed_drop = PARK_SLOW_MAX_DROP * slow_ratio
    bs2 = int(np.clip(bs * (1.0 - speed_drop), 10, 255))

    # 좌/우 속도 계산
    steer = int(np.clip(park_steer_cmd, -steer_max, steer_max))
    left  = int(np.clip(bs2 + steer, 0, 255))
    right = int(np.clip(bs2 - steer, 0, 255))

    set_motor_speeds(left, left, right, right)

# =========================
# Servo
# =========================
def rotate_servo(servo_id, angle):
    if servo_id == 2 and angle > 110:
        angle = 110
    bot.Ctrl_Servo(servo_id, angle)

# =========================
# YOLO FSM updates
# =========================
def update_mark_x_state(dets, frame_w):
    global x_streak, x_phase_start, x_active_until, x_turn_dir, x_cooldown_until
    global x_locked, x_lock_time, x_lost_infer_count
    global x_bbox_cand, x_stop_acc_L, x_stop_acc_R, x_stop_acc_n

    if park_mode or is_o_priority(time.time()):
        x_streak = 0
        return get_best_conf(dets, MARK_X_ID)

    if now < x_active_until:
        return get_best_conf(dets, MARK_X_ID)

    x_det, x_conf = get_best_det(dets, MARK_X_ID)
    seen = (x_det is not None) and (x_conf >= MARK_X_MIN_CONF)

    if x_locked:
        if (now - x_lock_time) > X_LOCK_MAX_SEC:
            x_locked = False
            x_lost_infer_count = 0
        else:
            if seen:
                x_lost_infer_count = 0
                x_streak = 0
                return x_conf
            x_lost_infer_count += 1
            x_streak = 0
            if x_lost_infer_count >= X_LOST_INFER_TO_REARM:
                x_locked = False
                x_lost_infer_count = 0
            return x_conf

    if now < x_cooldown_until:
        x_streak = 0
        return x_conf

    if not seen:
        x_streak = 0
        return x_conf

    x_streak += 1
    if x_streak >= X_CONSEC:
        x_phase_start = now
        x_active_until = now + (X_STOP_SEC + X_TURN_SEC + X_RECOVER_SEC)
        x_cooldown_until = x_active_until + X_RETRIGGER_COOLDOWN_SEC

        x_turn_dir = "PENDING"

        x1, y1, x2, y2 = x_det["xyxy"]
        cx = (x1 + x2) * 0.5
        x_bbox_cand = "RIGHT" if cx < (frame_w * 0.5) else "LEFT"

        x_stop_acc_L = 0.0
        x_stop_acc_R = 0.0
        x_stop_acc_n = 0

        x_locked = True
        x_lock_time = now
        x_lost_infer_count = 0
        x_streak = 0

    return x_conf

def update_obstacle_state(dets, frame_w, frame_h):
    global ob_streak, ob_active_until, ob_cooldown_until, ob_seen_count

    if now < ob_active_until:
        return get_best_conf(dets, OBSTACLE_ID)

    if now < ob_cooldown_until:
        ob_streak = 0
        return get_best_conf(dets, OBSTACLE_ID)

    ob_det, ob_conf = get_best_det(dets, OBSTACLE_ID)
    seen = (ob_det is not None) and (ob_conf >= OBSTACLE_MIN_CONF)

    if not seen:
        ob_streak = 0
        return ob_conf

    ob_streak += 1
    if ob_streak >= OBSTACLE_CONSEC:
        ob_active_until = now + OB_STOP_SEC
        ob_cooldown_until = ob_active_until + OB_RETRIGGER_COOLDOWN_SEC
        ob_streak = 0

        ob_seen_count += 1
        idx = ((ob_seen_count - 1) % 3) + 1
        start_beep_pattern(f"OB{idx}")

    return ob_conf

def update_parking_state(dets, frame_w, frame_h):
    global park_streak, park_mode, park_done
    global last_o_det, last_o_conf, last_o_area_ratio, last_o_center_off, last_o_time
    global park_fsm, park_arm_cnt, park_lost_cnt, park_area_peak
    global park_area_ema, park_off_ema, park_ema_inited
    global park_pass_ready, park_pass_lost_cnt
    global park_last_follow_t, park_steer_cmd

    o_det, o_conf = get_best_det(dets, MARK_O_ID)
    seen = (o_det is not None) and (o_conf >= MARK_O_MIN_CONF)

    if seen:
        last_o_det = o_det
        last_o_conf = o_conf

        area, off = det_geom(o_det, frame_w, frame_h)
        last_o_area_ratio, last_o_center_off = area, off
        last_o_time = time.time()

        if not park_ema_inited:
            park_area_ema = float(area)
            park_off_ema  = float(off)
            park_ema_inited = True
        else:
            a = PARK_EMA_ALPHA
            park_area_ema = (1 - a) * park_area_ema + a * float(area)
            park_off_ema  = (1 - a) * park_off_ema  + a * float(off)

        if (area >= PARK_TRIGGER_MIN_AREA_RATIO) and (abs(off) <= PARK_TRIGGER_CENTER_PX):
            park_streak += 1
        else:
            park_streak = 0
    else:
        park_streak = 0

    if (not park_mode) and (park_streak >= PARK_CONSEC):
        park_mode = True
        park_done = False
        park_fsm = "APPROACH"
        park_arm_cnt = 0
        park_lost_cnt = 0
        park_area_peak = 0.0
        park_streak = 0

        # PASS 상태 리셋
        park_pass_ready = False
        park_pass_lost_cnt = 0

        # ✅ Smooth Follow 상태도 리셋(진입 순간 급조향 방지)
        park_last_follow_t = time.time()
        park_steer_cmd = 0.0

    return o_conf

def update_traffic_light_state(dets):
    global TL_PHASE, tl_state, tl_red_streak, tl_green_streak, tl_last_stop_time

    red_conf = get_best_conf(dets, TL_RED_ID)
    green_conf = get_best_conf(dets, TL_GREEN_ID)

    if TL_PHASE == "GO":
        if red_conf >= TL_RED_MIN_CONF:
            tl_red_streak += 1
        else:
            tl_red_streak = 0

        if tl_red_streak >= TL_CONSEC:
            TL_PHASE = "RED_BEEP"
            tl_last_stop_time = now
            tl_red_streak = 0
            tl_green_streak = 0
            tl_state = "STOP"
            start_beep_pattern("TL_RED")

        return tl_state, red_conf, green_conf

    tl_state = "STOP"

    if TL_PHASE == "RED_BEEP":
        if (now - tl_last_stop_time) >= TL_HOLD_SEC and (not is_beep_running()):
            TL_PHASE = "WAIT_GREEN"
        return tl_state, red_conf, green_conf

    if TL_PHASE == "WAIT_GREEN":
        if red_conf >= TL_RED_MIN_CONF:
            tl_green_streak = 0
            return tl_state, red_conf, green_conf

        if green_conf >= TL_GREEN_MIN_CONF:
            tl_green_streak += 1
        else:
            tl_green_streak = 0

        if tl_green_streak >= TL_CONSEC:
            TL_PHASE = "GO"
            tl_state = "GO"
            tl_green_streak = 0
            tl_red_streak = 0

        return tl_state, red_conf, green_conf

    return tl_state, red_conf, green_conf

# =========================
# UI Trackbars
# =========================
def nothing(x): pass

if UI_ENABLED:
    cv2.namedWindow("Camera Settings", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Camera Settings", 500, 900)
    cv2.namedWindow("YOLO", cv2.WINDOW_NORMAL)
    cv2.namedWindow("1_Frame", cv2.WINDOW_NORMAL)
    cv2.namedWindow("4_Processed Frame", cv2.WINDOW_NORMAL)
    cv2.namedWindow("4_Binary", cv2.WINDOW_NORMAL)

    cv2.createTrackbar("Servo_1_Angle", "Camera Settings", DEFAULT_SERVO_1, 180, nothing)
    cv2.createTrackbar("Servo_2_Angle", "Camera Settings", DEFAULT_SERVO_2, 110, nothing)

    cv2.createTrackbar("ROI_Top_Y", "Camera Settings", 700, 1000, nothing)
    cv2.createTrackbar("ROI_Bottom_Y", "Camera Settings", 900, 1000, nothing)
    cv2.createTrackbar("Direction_Threshold", "Camera Settings", DEFAULT_DIRECTION_THRESHOLD, 500000, nothing)
    cv2.createTrackbar("Up_Threshold", "Camera Settings", DEFAULT_UP_THRESHOLD, 500000, nothing)

    cv2.createTrackbar("Brightness", "Camera Settings", DEFAULT_BRIGHTNESS, 100, nothing)
    cv2.createTrackbar("Contrast", "Camera Settings", DEFAULT_CONTRAST, 100, nothing)
    cv2.createTrackbar("Detect_Value", "Camera Settings", DEFAULT_DETECT_VALUE, 150, nothing)
    cv2.createTrackbar("Motor_Up_Speed", "Camera Settings", DEFAULT_SPEED_UP, 255, nothing)
    cv2.createTrackbar("Motor_Down_Speed", "Camera Settings", DEFAULT_SPEED_DOWN, 255, nothing)
    cv2.createTrackbar("Saturation", "Camera Settings", DEFAULT_SATURATION, 100, nothing)
    cv2.createTrackbar("Gain", "Camera Settings", DEFAULT_GAIN, 100, nothing)

    cv2.createTrackbar("R_weight", "Camera Settings", DEFAULT_R_WEIGHT, 100, nothing)
    cv2.createTrackbar("G_weight", "Camera Settings", DEFAULT_G_WEIGHT, 100, nothing)
    cv2.createTrackbar("B_weight", "Camera Settings", DEFAULT_B_WEIGHT, 100, nothing)

# =========================
# Image processing
# =========================
def apply_roi_visualization(frame, pts_src, actual_w, actual_h, top_y, bottom_y):
    pts = pts_src.reshape((-1, 1, 2)).astype(np.int32)
    frame_with_rect = cv2.polylines(frame.copy(), [pts], isClosed=True, color=(0, 255, 0), thickness=2)
    return frame_with_rect

def calculate_roi_points(actual_w, actual_h, roi_top_y, roi_bottom_y):
    top_y = int(roi_top_y * actual_h / 1000)
    bottom_y = int(roi_bottom_y * actual_h / 1000)

    top_y = int(np.clip(top_y, 0, actual_h - 2))
    bottom_y = int(np.clip(bottom_y, top_y + 1, actual_h))

    bottom_y_vis = bottom_y - 1

    margin = 10
    center_x = actual_w / 2.0
    bottom_half = (actual_w - 2 * margin) / 2.0

    TOP_WIDTH_RATIO = 0.85
    top_half = bottom_half * TOP_WIDTH_RATIO

    pts_src = np.float32([
        [margin,              bottom_y_vis],
        [actual_w - margin,   bottom_y_vis],
        [center_x + top_half, top_y],
        [center_x - top_half, top_y],
    ])
    return pts_src, top_y, bottom_y

def weighted_gray(image, r_weight, g_weight, b_weight):
    r_weight /= 100.0
    g_weight /= 100.0
    b_weight /= 100.0
    weighted_gray_frame = cv2.addWeighted(
        cv2.addWeighted(image[:, :, 2], r_weight, image[:, :, 1], g_weight, 0),
        1.0,
        image[:, :, 0],
        b_weight,
        0,
    )
    return weighted_gray_frame

def detect_road_lines(color_frame, gray_frame, detect_value):
    hsv_frame = cv2.cvtColor(color_frame, cv2.COLOR_BGR2HSV)

    lower_red1 = np.array([0, 70, 50])
    upper_red1 = np.array([10, 255, 255])
    mask_red1 = cv2.inRange(hsv_frame, lower_red1, upper_red1)

    lower_red2 = np.array([170, 70, 50])
    upper_red2 = np.array([180, 255, 255])
    mask_red2 = cv2.inRange(hsv_frame, lower_red2, upper_red2)

    mask_red = cv2.bitwise_or(mask_red1, mask_red2)

    threshold_gray = max(detect_value - 30, 80)
    _, mask_gray = cv2.threshold(gray_frame, threshold_gray, 255, cv2.THRESH_BINARY)

    dark_threshold = 50
    _, mask_dark = cv2.threshold(gray_frame, dark_threshold, 255, cv2.THRESH_BINARY)
    mask_gray = cv2.bitwise_and(mask_gray, mask_dark)

    mask_lines = cv2.bitwise_or(mask_red, mask_gray)

    kernel = np.ones((3, 3), np.uint8)
    mask_lines = cv2.morphologyEx(mask_lines, cv2.MORPH_CLOSE, kernel)
    mask_lines = cv2.morphologyEx(mask_lines, cv2.MORPH_OPEN, kernel)

    return mask_lines

def visualize_direction_on_frame(binary_frame, direction, left_sum, center_sum, right_sum, rgb_weights):
    frame_color = cv2.cvtColor(binary_frame, cv2.COLOR_GRAY2BGR)
    h, w = frame_color.shape[:2]

    overlay = frame_color.copy()
    cv2.rectangle(overlay, (0, 0), (w, 110), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, frame_color, 0.3, 0, frame_color)

    direction_text = f"DIR: {direction}"
    direction_color = (0, 255, 0) if direction == "UP" else (0, 255, 255)
    cv2.putText(frame_color, direction_text, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, direction_color, 2)

    hist_text = f"L:{left_sum:7d} C:{center_sum:7d} R:{right_sum:7d}"
    cv2.putText(frame_color, hist_text, (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

    left_end = w // 3
    right_start = 2 * w // 3

    denom_L = max(1, left_end * h * 255)
    denom_C = max(1, (right_start - left_end) * h * 255)
    denom_R = max(1, (w - right_start) * h * 255)

    left_ratio   = left_sum   / denom_L
    center_ratio = center_sum / denom_C
    right_ratio  = right_sum  / denom_R

    ratio_text = f"Ratio(Low=OK) - L:{left_ratio:.2f} C:{center_ratio:.2f} R:{right_ratio:.2f}"
    cv2.putText(frame_color, ratio_text, (10, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

    r_w, g_w, b_w = rgb_weights
    rgb_text = f"RGB Filter: R:{r_w} G:{g_w} B:{b_w}"
    cv2.putText(frame_color, rgb_text, (10, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (150, 255, 255), 1)

    left_line = w // 3
    right_line = 2 * w // 3
    cv2.line(frame_color, (left_line, 0), (left_line, h), (255, 0, 0), 2)
    cv2.line(frame_color, (right_line, 0), (right_line, h), (255, 0, 0), 2)

    label_y = h - 10
    cv2.putText(frame_color, "LEFT", (w // 6 - 20, label_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    cv2.putText(frame_color, "CENTER", (w // 2 - 35, label_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(frame_color, "RIGHT", (5 * w // 6 - 25, label_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    return frame_color

def process_frame(frame, detect_value, roi_top_y, roi_bottom_y, r_weight, g_weight, b_weight):
    blurred = cv2.medianBlur(frame, 3)

    actual_h, actual_w = frame.shape[:2]
    pts_src, top_y, bottom_y = calculate_roi_points(actual_w, actual_h, roi_top_y, roi_bottom_y)

    frame_with_rect = apply_roi_visualization(blurred, pts_src, actual_w, actual_h, top_y, bottom_y)
    imshow("1_Frame", frame_with_rect)

    roi = blurred[top_y:bottom_y, :]
    frame_transformed = roi

    gray_frame = weighted_gray(frame_transformed, r_weight, g_weight, b_weight)
    binary_frame = detect_road_lines(frame_transformed, gray_frame, detect_value)

    mask = np.zeros_like(binary_frame, dtype=np.uint8)
    pts_roi = pts_src.copy()
    pts_roi[:, 1] -= top_y

    roi_h = binary_frame.shape[0]
    pts_roi[:, 1] = np.clip(pts_roi[:, 1], 0, roi_h - 1)

    cv2.fillPoly(mask, [pts_roi.astype(np.int32)], 255)
    binary_frame = cv2.bitwise_and(binary_frame, mask)

    imshow("4_Binary", binary_frame)
    return binary_frame, top_y, bottom_y

# =========================
# Direction decision
# =========================
def analyze_histogram(histogram, height):
    length = len(histogram)
    left_end = length // 3
    right_start = 2 * length // 3

    left_sum = int(np.sum(histogram[:left_end]))
    center_sum = int(np.sum(histogram[left_end:right_start]))
    right_sum = int(np.sum(histogram[right_start:]))

    denom_L = max(1, left_end * height * 255)
    denom_C = max(1, (right_start - left_end) * height * 255)
    denom_R = max(1, (length - right_start) * height * 255)

    left_ratio = left_sum / denom_L
    center_ratio = center_sum / denom_C
    right_ratio = right_sum / denom_R

    return left_sum, center_sum, right_sum, left_ratio, center_ratio, right_ratio

def decide_direction(histogram, direction_threshold, up_threshold, frame_h):
    left_sum, center_sum, right_sum, left_ratio, center_ratio, right_ratio = analyze_histogram(histogram, frame_h)

    if abs(right_sum - left_sum) > direction_threshold:
        direction = "LEFT" if right_sum > left_sum else "RIGHT"
        return direction, left_sum, center_sum, right_sum

    if center_ratio < CENTER_CLEAR_THRESHOLD:
        return "UP", left_sum, center_sum, right_sum

    left_right_avg = (left_sum + right_sum) // 2
    if left_right_avg > up_threshold:
        return random.choice(["LEFT", "RIGHT"]), left_sum, center_sum, right_sum

    return "UP", left_sum, center_sum, right_sum

# =========================
# Helpers
# =========================
def handle_keyboard_input():
    global mouse_use, led_state, beep_state, beep_task
    key = wait_key(1)

    if key == 27:
        return "EXIT"

    if key == 32:
        mouse_use = not mouse_use
        if not mouse_use:
            car_stop()

    if key == ord("l"):
        led_state = not led_state
        if led_state:
            bot.Ctrl_WQ2812_ALL(1, 2)
        else:
            bot.Ctrl_WQ2812_ALL(0, 0)

    if key == ord("b"):
        beep_state = not beep_state
        if not beep_state:
            beep_task = None
            bot.Ctrl_BEEP_Switch(0)
        else:
            bot.Ctrl_BEEP_Switch(0)

    return "CONTINUE"

def read_trackbar_values():
    if not UI_ENABLED:
        return {
            "brightness": DEFAULT_BRIGHTNESS,
            "contrast": DEFAULT_CONTRAST,
            "saturation": DEFAULT_SATURATION,
            "gain": DEFAULT_GAIN,
            "detect_value": DEFAULT_DETECT_VALUE,
            "motor_up_speed": DEFAULT_SPEED_UP,
            "motor_down_speed": DEFAULT_SPEED_DOWN,
            "servo_1_angle": DEFAULT_SERVO_1,
            "servo_2_angle": DEFAULT_SERVO_2,
            "roi_top_y": 700,
            "roi_bottom_y": 900,
            "direction_threshold": DEFAULT_DIRECTION_THRESHOLD,
            "up_threshold": DEFAULT_UP_THRESHOLD,
            "r_weight": DEFAULT_R_WEIGHT,
            "g_weight": DEFAULT_G_WEIGHT,
            "b_weight": DEFAULT_B_WEIGHT,
        }

    return {
        "brightness": cv2.getTrackbarPos("Brightness", "Camera Settings"),
        "contrast": cv2.getTrackbarPos("Contrast", "Camera Settings"),
        "saturation": cv2.getTrackbarPos("Saturation", "Camera Settings"),
        "gain": cv2.getTrackbarPos("Gain", "Camera Settings"),
        "detect_value": cv2.getTrackbarPos("Detect_Value", "Camera Settings"),
        "motor_up_speed": cv2.getTrackbarPos("Motor_Up_Speed", "Camera Settings"),
        "motor_down_speed": cv2.getTrackbarPos("Motor_Down_Speed", "Camera Settings"),
        "servo_1_angle": cv2.getTrackbarPos("Servo_1_Angle", "Camera Settings"),
        "servo_2_angle": cv2.getTrackbarPos("Servo_2_Angle", "Camera Settings"),
        "roi_top_y": cv2.getTrackbarPos("ROI_Top_Y", "Camera Settings"),
        "roi_bottom_y": cv2.getTrackbarPos("ROI_Bottom_Y", "Camera Settings"),
        "direction_threshold": cv2.getTrackbarPos("Direction_Threshold", "Camera Settings"),
        "up_threshold": cv2.getTrackbarPos("Up_Threshold", "Camera Settings"),
        "r_weight": cv2.getTrackbarPos("R_weight", "Camera Settings"),
        "g_weight": cv2.getTrackbarPos("G_weight", "Camera Settings"),
        "b_weight": cv2.getTrackbarPos("B_weight", "Camera Settings"),
    }

_last_cam_settings = {"brightness": None, "contrast": None, "saturation": None, "gain": None}
_last_s1 = None
_last_s2 = None

def apply_camera_settings(cap, brightness, contrast, saturation, gain):
    global _last_cam_settings
    settings = {
        "brightness": (cv2.CAP_PROP_BRIGHTNESS, brightness),
        "contrast":   (cv2.CAP_PROP_CONTRAST, contrast),
        "saturation": (cv2.CAP_PROP_SATURATION, saturation),
        "gain":       (cv2.CAP_PROP_GAIN, gain),
    }
    for key, (prop_id, val) in settings.items():
        if _last_cam_settings.get(key) != val:
            cap.set(prop_id, val)
            _last_cam_settings[key] = val

def cleanup_and_exit(bot, cap):
    car_stop()
    try:
        bot.Ctrl_WQ2812_ALL(0, 0)
    except Exception:
        pass
    try:
        bot.Ctrl_BEEP_Switch(0)
    except Exception:
        pass
    try:
        bot.Ctrl_Servo(1, 90)
        bot.Ctrl_Servo(2, 25)
    except Exception:
        pass

    try:
        cap.release()
    except Exception:
        pass

    if UI_ENABLED:
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass

    try:
        del bot
    except Exception:
        pass

# =========================
# MAIN LOOP
# =========================
start_time = time.time()
last_dets = []
last_yolo_show = None

try:
    while True:
        now = time.time()
        frame_count += 1
        service_beep_task()

        params = read_trackbar_values()

        apply_camera_settings(
            cap,
            params["brightness"],
            params["contrast"],
            params["saturation"],
            params["gain"],
        )

        ret, frame = cap.read()
        if not ret:
            break

        did_infer = False
        dets = last_dets

        red_c = get_best_conf(dets, TL_RED_ID)
        green_c = get_best_conf(dets, TL_GREEN_ID)
        ob_c = get_best_conf(dets, OBSTACLE_ID)
        park_c = get_best_conf(dets, MARK_O_ID)
        x_c = get_best_conf(dets, MARK_X_ID)
        tl_state_now = tl_state

        if YOLO_ENABLED and (yolo_model is not None):
            infer_N = 1 if park_mode else YOLO_EVERY_N_FRAMES

            if (frame_count % infer_N) == 0:
                dets_new, base_frame = run_yolo_inference(frame, yolo_model, imgsz=YOLO_IMGSZ, conf=YOLO_CONF)

                park_c = update_parking_state(dets_new, frame.shape[1], frame.shape[0])
                dets_new = apply_mark_priority(dets_new)

                last_dets = dets_new
                did_infer = True

                last_yolo_show = draw_dets_light(base_frame, last_dets)

                tl_state_now, red_c, green_c = update_traffic_light_state(last_dets)
                tl_state = tl_state_now

                ob_c = update_obstacle_state(last_dets, frame.shape[1], frame.shape[0])

                if is_o_priority(time.time()):
                    x_active_until = 0.0
                    x_locked = False
                    x_lost_infer_count = 0
                    x_streak = 0

                if time.time() < ob_active_until:
                    x_c = get_best_conf(last_dets, MARK_X_ID)
                else:
                    x_c = update_mark_x_state(last_dets, frame.shape[1])

            dets = last_dets

            if not did_infer:
                red_c = get_best_conf(dets, TL_RED_ID)
                green_c = get_best_conf(dets, TL_GREEN_ID)
                ob_c = get_best_conf(dets, OBSTACLE_ID)
                park_c = get_best_conf(dets, MARK_O_ID)
                x_c = get_best_conf(dets, MARK_X_ID)
                tl_state_now = tl_state

            base = last_yolo_show if last_yolo_show is not None else frame
            show = base.copy()

            if YOLO_USE_GRAY and (last_yolo_show is None):
                g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                show = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)

            cv2.putText(
                show,
                f"TL={tl_state_now} r={red_c:.2f} g={green_c:.2f} | "
                f"ob={ob_c:.2f} x={x_c:.2f} park={park_c:.2f} mode={'PARK' if park_mode else 'RUN'} fsm={park_fsm}",
                (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 255),
                2,
            )
            imshow("YOLO", show)

        if params["servo_1_angle"] != _last_s1:
            rotate_servo(1, params["servo_1_angle"])
            _last_s1 = params["servo_1_angle"]

        if params["servo_2_angle"] != _last_s2:
            rotate_servo(2, params["servo_2_angle"])
            _last_s2 = params["servo_2_angle"]

        # =========================
        # 1) TL / OB stop
        # =========================
        stop_by_tl = (YOLO_CONTROL_ENABLE and tl_state == "STOP")
        stop_by_ob = (YOLO_CONTROL_ENABLE and (time.time() < ob_active_until))

        if stop_by_tl or stop_by_ob:
            car_stop()
            imshow("1_Frame", frame)
            if handle_keyboard_input() == "EXIT":
                break
            continue

        # =========================
        # 2) PARK CONTROL (✅ 더 세밀 + 부드러운 O 추종)
        # =========================
        if YOLO_CONTROL_ENABLE and park_mode:
            if park_done or (park_fsm == "STOP"):
                park_mode = True
                park_done = True
                park_fsm = "STOP"
                car_stop()
                if handle_keyboard_input() == "EXIT":
                    break
                continue

            seen_recent = (
                (last_o_det is not None)
                and ((time.time() - last_o_time) < PARK_SEEN_RECENT_SEC)
                and (last_o_conf >= MARK_O_MIN_CONF)
            )

            o_off  = float(park_off_ema)  if park_ema_inited else float(last_o_center_off)
            o_area = float(park_area_ema) if park_ema_inited else float(last_o_area_ratio)

            up = params["motor_up_speed"]

            if seen_recent:
                park_area_peak = max(float(park_area_peak), float(o_area))
                if park_area_peak >= PARK_PASS_PEAK_MIN:
                    park_pass_ready = True
                park_pass_lost_cnt = 0
            else:
                if park_pass_ready:
                    park_pass_lost_cnt += 1
                    car_stop()
                    if park_pass_lost_cnt >= PARK_PASS_LOST_CONSEC:
                        car_stop()
                        park_done = True
                        park_fsm = "STOP"
                        park_mode = True
                    if handle_keyboard_input() == "EXIT":
                        break
                    continue

                car_stop()
                if handle_keyboard_input() == "EXIT":
                    break
                continue

            if park_fsm == "SEARCH":
                if seen_recent:
                    park_fsm = "APPROACH"
                    park_arm_cnt = 0
                    park_lost_cnt = 0
                    park_area_peak = float(o_area)
                    park_pass_ready = False
                    park_pass_lost_cnt = 0
                    park_steer_cmd = 0.0
                    park_last_follow_t = time.time()
                else:
                    car_stop()
                if handle_keyboard_input() == "EXIT":
                    break
                continue

            elif park_fsm == "APPROACH":
                park_sp = max(12, int(up * PARK_SPEED_RATIO_APPROACH))

                # ✅ 기존보다 더 정확히 "중심" 잡되, slew로 급회전 방지
                follow_o_smooth(o_off, o_area, base_speed=park_sp)

                if (abs(o_off) <= PARK_CENTER_PX_APPROACH) and (o_area >= PARK_AREA_ARM):
                    park_arm_cnt += 1
                else:
                    park_arm_cnt = 0

                if park_arm_cnt >= PARK_ARM_CONSEC:
                    park_fsm = "ARMED"
                    park_lost_cnt = 0
                    park_steer_cmd = 0.0
                    park_last_follow_t = time.time()

                if handle_keyboard_input() == "EXIT":
                    break
                continue

            elif park_fsm == "ARMED":
                park_sp = max(10, int(up * PARK_SPEED_RATIO_ARMED))

                # ✅ ARMED는 더 천천히, 더 안정적으로
                follow_o_smooth(o_off, o_area, base_speed=park_sp)

                if PARK_USE_DROP_STOP and park_area_peak >= PARK_AREA_STOP_MIN:
                    if o_area < park_area_peak * PARK_AREA_DROP_RATIO:
                        car_stop()
                        park_done = True
                        park_fsm = "STOP"
                        park_mode = True

                if handle_keyboard_input() == "EXIT":
                    break
                continue

        # =========================
        # 3) LINE PROCESS
        # =========================
        processed_frame, top_y, bottom_y = process_frame(
            frame,
            params["detect_value"],
            params["roi_top_y"],
            params["roi_bottom_y"],
            params["r_weight"],
            params["g_weight"],
            params["b_weight"]
        )

        # O가 보이면(주차 중) 라인에서 O 영역 마스킹(선택)
        if (last_o_det is not None
            and park_mode
            and (park_c >= MARK_O_MIN_CONF)
            and ((time.time() - last_o_time) < 0.6)):

            x1, y1, x2, y2 = map(int, last_o_det["xyxy"])
            y1r = y1 - top_y
            y2r = y2 - top_y

            h, w = processed_frame.shape[:2]
            x1 = max(0, min(w - 1, x1))
            x2 = max(0, min(w,     x2))
            y1r = max(0, min(h - 1, y1r))
            y2r = max(0, min(h,     y2r))

            pad = 6
            x1 = max(0, x1 - pad); x2 = min(w, x2 + pad)
            y1r = max(0, y1r - pad); y2r = min(h, y2r + pad)

            if x2 > x1 and y2r > y1r:
                processed_frame[y1r:y2r, x1:x2] = 0

        histogram = np.sum(processed_frame, axis=0)
        _, _, _, left_ratio, _, right_ratio = analyze_histogram(histogram, processed_frame.shape[0])

        direction, hist_left, hist_center, hist_right = decide_direction(
            histogram,
            params["direction_threshold"],
            params["up_threshold"],
            processed_frame.shape[0],
        )

        rgb_weights = (params["r_weight"], params["g_weight"], params["b_weight"])
        processed_frame_visual = visualize_direction_on_frame(
            processed_frame, direction, hist_left, hist_center, hist_right, rgb_weights
        )
        imshow("4_Processed Frame", processed_frame_visual)

        # =========================
        # 4) X AVOID CONTROL
        # =========================
        if YOLO_CONTROL_ENABLE and (time.time() < x_active_until) and (not is_o_priority(time.time())) and (not park_mode):
            t = time.time() - x_phase_start

            up = params["motor_up_speed"]
            dn = params["motor_down_speed"]
            fwd_base = max(10, int(up * 0.70))

            if t < X_STOP_SEC:
                car_stop()
                x_stop_acc_L += float(left_ratio)
                x_stop_acc_R += float(right_ratio)
                x_stop_acc_n += 1

            elif t < (X_STOP_SEC + X_TURN_SEC):
                if x_turn_dir == "PENDING":
                    if x_stop_acc_n > 0:
                        avgL = x_stop_acc_L / x_stop_acc_n
                        avgR = x_stop_acc_R / x_stop_acc_n
                        if abs(avgL - avgR) < 1e-6:
                            x_turn_dir = x_bbox_cand
                        else:
                            x_turn_dir = "LEFT" if (avgL < avgR) else "RIGHT"
                    else:
                        x_turn_dir = x_bbox_cand

                if x_turn_dir == "LEFT":
                    car_left(dn, up)
                else:
                    car_right(up, dn)

            else:
                car_run(fwd_base, fwd_base)

            if handle_keyboard_input() == "EXIT":
                break
            continue

        # =========================
        # 5) NORMAL LINE CONTROL
        # =========================
        control_car_with_posture(
            direction,
            params["motor_up_speed"],
            params["motor_down_speed"],
            hist_left,
            hist_right,
            params["direction_threshold"],
        )

        if handle_keyboard_input() == "EXIT":
            break

except KeyboardInterrupt:
    pass
finally:
    cleanup_and_exit(bot, cap)
