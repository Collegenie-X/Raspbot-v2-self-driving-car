#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[Pi5] YOLO11n 탐지 테스트 — 카메라 영상에 OpenCV 사각형으로 '표시만' 합니다 (모터/주행 제어 없음)

final_08_autoplot.py 의 카메라 초기화 / YOLO 추론 / 박스 그리기 부분만 떼어 낸 최소 버전입니다.
  - 모델 : 05_yolo11_pipeline 에서 학습·변환한 best.onnx (best.pt, best_ncnn_model/ 도 가능)
  - 클래스: 모델 파일 안에 저장된 이름을 그대로 사용 (car / green / oo / red / xx)
            → final_08 의 CLASS_ID_TO_NAME(obstacle, mark_O ...) 과 순서가 다르니 섞어 쓰지 마세요.

모델 위치 (기본값):
  05_yolo11_pipeline/models/best.onnx   ← 9단계(09_export.py) 결과가 저장되는 곳
  (이 파일은 05_yolo11_pipeline/scripts/ 에 있으므로 한 단계 위 폴더의 models/ 를 봅니다)

준비 (Pi5):
  1) 모델 복사 (Mac → Pi, Pi 에도 같은 폴더 구조로):
       scp 05_yolo11_pipeline/models/best.onnx pi@<pi주소>:~/<저장소>/05_yolo11_pipeline/models/
  2) 패키지:
       pip install ultralytics onnxruntime      # best.onnx 는 onnxruntime 필요

실행 (scripts/ 폴더에서):
  python3 10_yolo11_test.py                                 # ../models/best.onnx + 카메라 0번
  python3 10_yolo11_test.py --model ../demo/models/best.onnx  # 데모 모델
  python3 10_yolo11_test.py --model ../models/best.pt
  python3 10_yolo11_test.py --conf 0.4 --every 2            # 2프레임마다 추론 (FPS ↑)
  python3 10_yolo11_test.py --source drive.mp4              # 카메라 대신 동영상
  python3 10_yolo11_test.py --headless                      # 화면 없이(SSH) 탐지 결과만 출력

키 (영상 창에서):  q / ESC = 종료,  s = 현재 화면 저장 (05_yolo11_pipeline/runs/camera_test/)

주의:
  - best.onnx / ncnn 은 변환할 때의 imgsz(320) 로 입력 크기가 고정됩니다 → --imgsz 는 320 그대로 두세요.
  - 라즈베리파이 OS(Wayland) 에서 창이 안 뜨면:  export QT_QPA_PLATFORM=xcb
"""
import argparse
import os
import sys
import time
from pathlib import Path

# Pi OS(Wayland) 에서 OpenCV(Qt) 창이 뜨지 않는 문제 방지 (1_yolo_camera_test.py 와 동일)
os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

import cv2

HERE = Path(__file__).resolve().parent         # .../05_yolo11_pipeline/scripts
ROOT = HERE.parent                              # .../05_yolo11_pipeline
REPO = ROOT.parent                              # 저장소 최상위 (Raspbot-v2-self-driving-car)
# Raspbot 라이브러리 경로 (final_08 의 '../lib/raspbot' 과 같은 위치) — 카메라 서보 각도만 맞추는 용도
sys.path.append(str(REPO / "lib" / "raspbot"))

# =========================
# 설정 (final_08_autoplot.py 와 같은 이름 사용)
# =========================
YOLO_MODEL_PATH = ROOT / "models" / "best.onnx"   # 9단계 변환 결과 (config.yaml 의 paths.models)
SAVE_DIR = ROOT / "runs" / "camera_test"          # 's' 키로 저장한 화면
YOLO_IMGSZ = 320            # 변환(export) 때의 imgsz 와 같아야 함 (onnx/ncnn 은 입력 크기 고정)
YOLO_CONF = 0.5             # 05_yolo11_pipeline config.yaml 의 predict.conf 와 동일
YOLO_EVERY_N_FRAMES = 1     # N 프레임마다 1번 추론 (사이 프레임은 직전 결과를 그대로 표시)

CAM_WIDTH, CAM_HEIGHT = 320, 240

DEFAULT_SERVO_1 = 74        # 카메라 좌우
DEFAULT_SERVO_2 = 5         # 카메라 상하

# 클래스별 박스 색 (BGR). 모델에 없는 id 는 노란색
CLASS_COLORS = {
    "car":   (0, 165, 255),    # 주황
    "green": (0, 200, 0),      # 초록
    "oo":    (255, 128, 0),    # 파랑
    "red":   (0, 0, 255),      # 빨강
    "xx":    (255, 0, 255),    # 보라
}
DEFAULT_COLOR = (0, 255, 255)


# =========================
# 하드웨어 초기화
# =========================
def initialize_bot():
    """카메라 서보를 기본 각도로 맞추고 모터는 정지 상태로 둔다. Raspbot 라이브러리가 없으면 건너뜀."""
    try:
        from Raspbot_Lib import Raspbot
        bot = Raspbot()
        bot.Ctrl_Servo(1, DEFAULT_SERVO_1)
        bot.Ctrl_Servo(2, DEFAULT_SERVO_2)
        for i in range(4):
            bot.Ctrl_Muto(i, 0)                 # 혹시 돌고 있던 모터 정지 (이 스크립트는 주행하지 않음)
        print(f"  Raspbot: 서보 {DEFAULT_SERVO_1}/{DEFAULT_SERVO_2}, 모터 정지")
        return bot
    except Exception as e:                      # PC 에서 실행하거나 라이브러리가 없을 때
        print(f"  Raspbot 없이 실행 (서보 제어 생략): {e}")
        return None


def initialize_camera(source, width=CAM_WIDTH, height=CAM_HEIGHT):
    """카메라 번호("0") 또는 동영상 경로로 VideoCapture 를 연다. 첫 프레임을 못 읽으면 에러."""
    is_cam = str(source).isdigit()
    cap = cv2.VideoCapture(int(source) if is_cam else str(source))
    if is_cam:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    if not cap.isOpened():
        raise RuntimeError(f"카메라/동영상을 열 수 없습니다: {source}")
    return cap


def has_display():
    """imshow 창을 띄울 수 있는 환경인지 (SSH 로 접속하면 DISPLAY 가 없음)."""
    return sys.platform in ("darwin", "win32") or bool(
        os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


# =========================
# YOLO
# =========================
def load_model(path):
    from ultralytics import YOLO                # torch 로드가 무거워서 필요한 시점에 import
    path = Path(path)
    if not path.exists():
        sys.exit(f"[ERROR] 모델이 없습니다: {path}\n"
                 f"        9단계(09_export.py)로 {YOLO_MODEL_PATH} 를 만들거나 --model 로 경로를 지정하세요.\n"
                 f"        (데모 모델: --model {ROOT / 'demo' / 'models' / 'best.onnx'})")
    # task="detect": onnx/ncnn 은 작업 종류를 못 읽는 경우가 있어 명시
    return YOLO(str(path), task="detect")


def run_yolo_inference(frame, model, imgsz=YOLO_IMGSZ, conf=YOLO_CONF):
    """프레임 1장 추론 → [{"cls", "name", "conf", "xyxy"}] 리스트 (final_08 과 같은 형식 + name)."""
    r = model.predict(frame, imgsz=imgsz, conf=conf, verbose=False)[0]
    dets = []
    if r.boxes is not None:
        for b in r.boxes:
            cls = int(b.cls[0].item())
            dets.append({
                "cls": cls,
                "name": model.names.get(cls, str(cls)),
                "conf": float(b.conf[0].item()),
                "xyxy": tuple(b.xyxy[0].tolist()),
            })
    return dets


def draw_dets(frame, dets):
    """탐지 결과를 사각형 + '이름:신뢰도' 글자로 그린 새 이미지를 반환."""
    out = frame.copy()
    for d in dets:
        x1, y1, x2, y2 = map(int, d["xyxy"])
        color = CLASS_COLORS.get(d["name"], DEFAULT_COLOR)
        text = f"{d['name']}:{d['conf']:.2f}"
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        # 글자 배경 상자 (글자가 배경에 묻히지 않도록)
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        ty = y1 - 4 if y1 - th - 6 > 0 else y1 + th + 4     # 위쪽 공간이 없으면 박스 안쪽에 표시
        cv2.rectangle(out, (x1, ty - th - 2), (x1 + tw + 2, ty + 2), color, -1)
        cv2.putText(out, text, (x1 + 1, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    return out


def draw_status(img, fps, infer_ms, n_dets):
    """좌상단에 FPS / 추론 시간 / 탐지 개수 표시."""
    cv2.putText(img, f"FPS {fps:.1f} | infer {infer_ms:.0f}ms | dets {n_dets}", (8, 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)


# =========================
# MAIN
# =========================
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=str(YOLO_MODEL_PATH), help="best.onnx / best.pt / best_ncnn_model")
    ap.add_argument("--source", default="0", help="카메라 번호(0) 또는 동영상 경로")
    ap.add_argument("--conf", type=float, default=YOLO_CONF)
    ap.add_argument("--imgsz", type=int, default=YOLO_IMGSZ)
    ap.add_argument("--every", type=int, default=YOLO_EVERY_N_FRAMES, help="N 프레임마다 추론")
    ap.add_argument("--headless", action="store_true", help="창 없이 탐지 결과만 콘솔 출력")
    args = ap.parse_args()

    show = not args.headless and has_display()
    if not args.headless and not show:
        print("  [WARN] 화면(DISPLAY)이 없어 headless 로 실행합니다. (VNC/모니터 연결 시 창 표시)")

    print(f"  모델: {args.model} | imgsz {args.imgsz} | conf {args.conf} | every {args.every}")
    model = load_model(args.model)
    bot = initialize_bot()
    cap = initialize_camera(args.source)
    save_dir = SAVE_DIR

    frame_count = 0
    last_dets, infer_ms, fps = [], 0.0, 0.0
    t_prev = time.time()
    print("  시작 — q/ESC: 종료, s: 화면 저장" if show else "  시작 — Ctrl+C: 종료")

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("  프레임을 더 읽을 수 없습니다 (카메라 끊김 또는 동영상 끝).")
                break
            frame_count += 1

            # ── N 프레임마다 추론, 나머지 프레임은 직전 결과 재사용 (final_08 과 같은 방식) ──
            if frame_count % max(1, args.every) == 0:
                t0 = time.perf_counter()
                last_dets = run_yolo_inference(frame, model, args.imgsz, args.conf)
                infer_ms = (time.perf_counter() - t0) * 1000
                if not show and last_dets:
                    print(f"  [{frame_count}] " + ", ".join(f"{d['name']}:{d['conf']:.2f}" for d in last_dets))

            # FPS (지수 이동 평균으로 부드럽게)
            now = time.time()
            dt = now - t_prev
            t_prev = now
            if dt > 0:
                fps = 1.0 / dt if fps == 0 else fps * 0.9 + (1.0 / dt) * 0.1

            if show:
                vis = draw_dets(frame, last_dets)
                draw_status(vis, fps, infer_ms, len(last_dets))
                cv2.imshow("YOLO11", vis)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27):
                    break
                if key == ord("s"):
                    save_dir.mkdir(parents=True, exist_ok=True)
                    p = save_dir / f"yolo11_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
                    cv2.imwrite(str(p), vis)
                    print(f"  저장: {p}")
            elif frame_count % 30 == 0:
                print(f"  ... {frame_count} 프레임 | FPS {fps:.1f} | infer {infer_ms:.0f}ms")
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        if show:
            cv2.destroyAllWindows()
        if bot is not None:
            for i in range(4):
                bot.Ctrl_Muto(i, 0)
        print(f"  종료 ({frame_count} 프레임)")


if __name__ == "__main__":
    main()
