#!/usr/bin/env python3
# coding: utf-8
"""
07. 카메라 영상 (터미널 버전 — 화면/창 없이 SSH 에서 실행 가능)
  Pi 에 창을 띄우지 않고 웹 브라우저로 영상을 봅니다.
    노트북 브라우저에서  http://<Pi IP>:8080  접속
  터미널 명령:
    b 30      밝기 (-100 ~ 100, 기본 0)
    c 1.5     대비 (0.1 ~ 3.0, 기본 1.0)
    f 1       뒤집기 0=원본 1=좌우 2=상하 3=180도
    g         흑백 켜기/끄기
    s         현재 화면 저장 (snapshot_*.jpg)
    q         종료
실행: python3 07_camera_cli.py [--device 0] [--port 8080]
"""
import os
import sys

# Raspbot 라이브러리 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib", "raspbot"))

import cv2
import numpy as np
import random
import time
from Raspbot_Lib import Raspbot

import argparse
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

FLIP_CODES = [None, 1, 0, -1]
settings = {"beta": 0, "alpha": 1.0, "flip": 0, "gray": False}
latest = {"jpeg": None, "frame": None}
frame_ready = threading.Condition()
stop_event = threading.Event()

PAGE = b"""<html><head><title>Raspbot Camera</title></head>
<body style="background:#222;color:#eee;font-family:sans-serif;text-align:center">
<h3>Raspbot Camera</h3><img src="/stream" style="max-width:100%"></body></html>"""


def capture_loop(cap):
    """카메라 프레임 읽기 → 보정 → JPEG 로 저장 (별도 스레드)"""
    while not stop_event.is_set():
        ok, frame = cap.read()
        if not ok:
            print("Failed to read frame.")
            time.sleep(0.5)
            continue
        frame = cv2.convertScaleAbs(frame, alpha=settings["alpha"], beta=settings["beta"])
        flip = FLIP_CODES[settings["flip"]]
        if flip is not None:
            frame = cv2.flip(frame, flip)
        if settings["gray"]:
            frame = cv2.cvtColor(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
        ok, jpg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
        if ok:
            with frame_ready:
                latest["jpeg"] = jpg.tobytes()
                latest["frame"] = frame
                frame_ready.notify_all()


class StreamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(PAGE)
        elif self.path == "/stream":
            # MJPEG: JPEG 를 계속 이어서 보내면 브라우저가 영상처럼 표시
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.end_headers()
            try:
                while not stop_event.is_set():
                    with frame_ready:
                        frame_ready.wait(timeout=1.0)
                        jpg = latest["jpeg"]
                    if jpg is None:
                        continue
                    self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\n")
                    self.wfile.write(f"Content-Length: {len(jpg)}\r\n\r\n".encode())
                    self.wfile.write(jpg + b"\r\n")
            except (BrokenPipeError, ConnectionResetError):
                pass  # 브라우저 탭을 닫음
        else:
            self.send_error(404)

    def log_message(self, *args):
        pass  # 접속 로그 출력 안 함


def pi_ip():
    try:
        return subprocess.check_output(["hostname", "-I"], text=True,
                                       stderr=subprocess.DEVNULL).split()[0]
    except Exception:
        return "<Pi IP>"


def main():
    parser = argparse.ArgumentParser(description="카메라 웹 스트리밍")
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.device)
    if not cap.isOpened():
        print(f"Error: Cannot open camera {args.device}.")
        return
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    server = ThreadingHTTPServer(("0.0.0.0", args.port), StreamHandler)
    server.daemon_threads = True
    threading.Thread(target=capture_loop, args=(cap,), daemon=True).start()
    threading.Thread(target=server.serve_forever, daemon=True).start()

    print(__doc__)
    print(f"▶ 브라우저에서 열기: http://{pi_ip()}:{args.port}")
    try:
        while True:
            parts = input("> ").strip().lower().split()
            if not parts:
                continue
            cmd = parts[0]
            try:
                if cmd in ("q", "quit", "exit"):
                    break
                elif cmd == "b" and len(parts) == 2:
                    settings["beta"] = min(max(int(parts[1]), -100), 100)
                elif cmd == "c" and len(parts) == 2:
                    settings["alpha"] = min(max(float(parts[1]), 0.1), 3.0)
                elif cmd == "f" and len(parts) == 2:
                    settings["flip"] = min(max(int(parts[1]), 0), 3)
                elif cmd == "g":
                    settings["gray"] = not settings["gray"]
                elif cmd == "s":
                    if latest["frame"] is None:
                        print("아직 프레임이 없습니다.")
                        continue
                    name = time.strftime("snapshot_%Y%m%d_%H%M%S.jpg")
                    cv2.imwrite(name, latest["frame"])
                    print(f"Saved {name}")
                    continue
                else:
                    print("알 수 없는 명령입니다.")
                    continue
                print("설정:", settings)
            except ValueError:
                print("값을 숫자로 입력하세요. 예: b 30")
    except (KeyboardInterrupt, EOFError):
        print()
    finally:
        stop_event.set()
        server.shutdown()
        cap.release()  # 카메라를 해제해야 다른 프로그램에서 사용 가능
        print("Camera released.")


if __name__ == "__main__":
    main()
