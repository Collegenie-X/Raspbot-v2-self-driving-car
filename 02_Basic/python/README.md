# 02_Basic — Pi 실행용 Python

`02_Basic/*.ipynb` 노트북을 Jupyter 없이 Pi에서 바로 실행할 수 있게 만든 스크립트입니다.
같은 기능을 **두 가지 버전**으로 제공합니다.

| 버전 | 파일 이름 | 조작 방법 | 실행 환경 |
|---|---|---|---|
| OpenCV trackbar | `01_buzzer.py` … | 창의 슬라이더 + 키 | Pi 데스크톱 / VNC / `ssh -X` (화면 필요) |
| 터미널 (창 없음) | `01_buzzer_cli.py` … | 터미널 명령 입력 | **SSH 그대로 실행 가능** |

SSH에서 trackbar 버전을 실행하면 `qt.qpa.xcb: could not connect to display` 오류가 납니다.
이때는 `_cli` 버전을 쓰거나, Pi 데스크톱이 로그인된 상태라면 `DISPLAY=:0 python3 01_buzzer.py` 로 실행하세요(창은 Pi 화면/VNC에 뜸).

## 파일 목록

| 노트북 | trackbar 버전 | 터미널 버전 |
|---|---|---|
| 01_Buzzer driver | `01_buzzer.py` — BEEP, Duration / SPACE 비프 | `01_buzzer_cli.py` — Enter 비프, `1.2`, `on`, `off`, `d 0.3` |
| 02_RGB Light bar test | `02_rgb_light.py` — Preset, R, G, B, Effect… / `e` 효과 | `02_rgb_light_cli.py` — `0~6`, `red`, `rgb 255 100 0`, `effect river 5 0.01`, `key` |
| 03_Servo control | `03_servo.py` — S1, S2 / `r` 리셋 | `03_servo_cli.py` — `90 40`, `s1 120`, `s2 60`, `sweep`, `r` |
| 04_Motor control | `04_motor.py` — M1~M4, Speed / `w/s/a/d` | `04_motor_cli.py` — `w/s/a/d` 즉시 반응, SPACE 정지, `+/-` 속도, `1~4` 모터 개별 |
| 05_Ultrasonic distance | `05_ultrasonic.py` — Interval, Warn, Beep | `05_ultrasonic_cli.py --warn 200 --beep` |
| 06_four-way line patrol | `06_line_tracker.py` — Interval, Print | `06_line_tracker_cli.py [--all]` |
| 07_Camera_Driving | `07_camera.py` — 밝기, 대비, Flip, Gray / `s` 저장 | `07_camera_cli.py` — 브라우저로 `http://<Pi IP>:8080` 시청, `b 30`, `c 1.5`, `f 1`, `g`, `s` |

종료: trackbar 버전은 `q`/`ESC`, 터미널 버전은 `q` 또는 `Ctrl+C`.
종료 시 모터 정지 · LED/부저 OFF · 서보 기본 위치 · 초음파 OFF · 카메라 해제를 자동으로 합니다.

## 실행

```bash
cd ~/Raspbot-v2-self-driving-car/02_Basic/python
```

```bash
python3 04_motor_cli.py
```

`Raspbot_Lib` 은 각 스크립트가 `../lib/raspbot` (= `02_Basic/lib/raspbot/Raspbot_Lib.py`)를 `sys.path` 에 추가해 불러옵니다.
`append` 라서 Pi에 `Raspbot_Lib` 이 이미 설치되어 있으면 설치된 쪽이 먼저 사용됩니다.
`python` 폴더만 다른 곳(예: `~/Desktop/python`)으로 복사했다면 `lib` 폴더도 같은 위치 관계(`~/Desktop/lib/raspbot`)로 복사하세요.
노트북(Jupyter) 커널이 `bot` 객체를 아직 쥐고 있으면 충돌하므로, 노트북 커널을 먼저 종료하세요.

## 참고

- `04_motor*`: 바퀴를 띄우거나 넓은 곳에서 테스트하세요. trackbar 버전은 0~510 을 쓰고 `값 - 255` 가 실제 속도입니다.
- `02_rgb_light*`: 효과는 지속 시간 동안 실행되고 끝나야 다음 입력을 받습니다. KEY1 읽기가 실패해도 원본 노트북처럼 멈추지 않습니다.
- `05`, `06`: 원본의 OLED 표시는 빼고 창/터미널에 표시합니다.
- `07_camera_cli.py`: 노트북과 Pi 가 같은 Wi-Fi 에 있어야 브라우저로 볼 수 있습니다. 포트 변경은 `--port 8000`.
