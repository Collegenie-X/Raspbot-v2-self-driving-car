"""
공통 유틸리티 모듈 (모든 단계 스크립트가 import 해서 사용)

- 설정 파일(config.yaml) 로드 / 경로 해석
- 디바이스(CUDA / Apple MPS / CPU) 자동 선택
- YOLO 라벨(txt) 읽기·쓰기, 좌표 변환
- 박스 그리기, IoU 계산

구성 (위에서 아래 순서)
  1) 상수           : ROOT, DEFAULT_CONFIG, 확장자 목록, 클래스 색상표
  2) 설정 / 경로     : add_config_arg, load_config, resolve, path_of, labeled_dirs,
                      data_yaml_path, default_weights, pick_device, banner
                      대화형 입력: add_yes_arg, interactive, ask (엔터 = 기본값)
  3) 파일 목록       : list_images, label_path_for
  4) YOLO 라벨 I/O  : read_yolo_labels, write_yolo_labels, yolo_to_xyxy, xyxy_to_yolo, iou_xyxy
  5) 시각화          : color_of, draw_box, draw_yolo_boxes, has_display

좌표 표기 약속
  YOLO  : (class, x_center, y_center, width, height)  — 0~1 로 정규화된 값
  xyxy  : (x1, y1, x2, y2)                            — 픽셀 단위 좌상단/우하단 꼭짓점
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

import yaml

# 09_yolo11_pipeline/ 폴더 (scripts/ 의 상위)
#   __file__ = .../09_yolo11_pipeline/scripts/common.py → parent(scripts) → parent(09_yolo11_pipeline)
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config.yaml"

# 이미지 / 동영상으로 인식할 확장자 (비교 시 소문자로 변환해서 사용)
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".m4v"}

# 클래스별 표시 색상 (BGR)
#   OpenCV 는 RGB 가 아니라 BGR 순서를 사용합니다. class_id 를 10 으로 나눈 나머지로 색을 고릅니다.
PALETTE = [
    (56, 56, 255), (151, 157, 255), (31, 112, 255), (29, 178, 255), (49, 210, 207),
    (10, 249, 72), (23, 204, 146), (134, 219, 61), (52, 147, 26), (187, 212, 0),
]


# --------------------------------------------------------------------------- #
# 설정 / 경로
# --------------------------------------------------------------------------- #
def add_config_arg(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """argparse 파서에 공통 옵션 --config 를 추가하고 같은 파서를 돌려준다."""
    parser.add_argument("--config", default=str(DEFAULT_CONFIG),
                        help="설정 파일 경로 (기본: config.yaml)")
    return parser


def load_config(path: str | Path | None = None) -> dict:
    """config.yaml 을 읽어 dict 로 반환한다.

    - 상대경로인데 현재 폴더에 없으면 09_yolo11_pipeline/ 기준으로 다시 찾는다.
    - 파일이 없거나 classes 가 비어 있으면 프로그램을 종료한다.
    - 반환 dict 에 '_config_path'(실제로 읽은 경로)를 추가해 둔다.
    """
    cfg_path = Path(path) if path else DEFAULT_CONFIG
    # 현재 작업 폴더 기준으로 못 찾으면 → 파이프라인 루트 기준으로 재시도
    if not cfg_path.is_absolute() and not cfg_path.exists():
        cfg_path = ROOT / cfg_path
    if not cfg_path.exists():
        sys.exit(f"[ERROR] 설정 파일을 찾을 수 없습니다: {cfg_path}")
    with open(cfg_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)            # safe_load: 임의 파이썬 객체 생성을 막는 안전한 로더
    cfg["_config_path"] = str(cfg_path)
    if not cfg.get("classes"):             # 클래스 목록이 없으면 어떤 단계도 진행할 수 없음
        sys.exit("[ERROR] config 의 classes 가 비어 있습니다.")
    return cfg


def resolve(p: str | Path) -> Path:
    """config 안의 상대경로는 09_yolo11_pipeline/ 기준으로 해석."""
    p = Path(p)
    return p if p.is_absolute() else (ROOT / p)


def path_of(cfg: dict, key: str) -> Path:
    """config 의 paths.<key> 값을 절대경로(Path)로 반환. 예: path_of(cfg, "models") → .../models"""
    return resolve(cfg["paths"][key])


def labeled_dirs(cfg: dict) -> tuple[Path, Path]:
    """라벨링 작업 폴더 (images/, labels/) 반환."""
    base = path_of(cfg, "labeled")
    return base / "images", base / "labels"


def data_yaml_path(cfg: dict) -> Path:
    """4단계에서 만드는 학습용 data.yaml 의 경로 (datasets/<이름>/data.yaml)."""
    return path_of(cfg, "dataset") / "data.yaml"


def default_weights(cfg: dict) -> Path:
    """6~9단계가 기본으로 사용하는 모델 경로 (models/best.pt, 5단계에서 자동 복사됨)."""
    return path_of(cfg, "models") / "best.pt"


def pick_device(pref: str | int | None = "auto") -> str:
    """auto → CUDA GPU(0) 가 있으면 GPU, 없으면 CPU.

    Apple MPS 는 자동 선택하지 않습니다. PyTorch 버전과 macOS 버전 조합에 따라
    MPS 학습이 파이썬 예외 없이 프로세스째 종료(NSInvalidArgumentException)되는 경우가 있어,
    필요하면 config 의 device: mps 또는 --device mps 로 직접 지정하세요.

    반환값은 Ultralytics 의 device 인자 형식("0", "cpu", "mps" ...) 문자열입니다.
    """
    if pref not in (None, "", "auto"):      # 사용자가 직접 지정했으면 그대로 사용
        return str(pref)
    try:
        import torch                         # torch 가 없어도 동작하도록 함수 안에서 import
        if torch.cuda.is_available():
            return "0"                       # 첫 번째 CUDA GPU
    except Exception:
        pass
    return "cpu"


def banner(step: str, title: str) -> None:
    """콘솔에 '[단계] 제목' 형태의 구분선 배너를 출력."""
    line = "=" * 64
    print(f"\n{line}\n  [{step}] {title}\n{line}")


def add_yes_arg(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """-y/--yes 인자 추가: 값을 묻지 않고 기본값(config)으로 바로 실행."""
    parser.add_argument("-y", "--yes", action="store_true",
                        help="값을 묻지 않고 바로 기본값(config)으로 실행")
    return parser


def interactive(args: argparse.Namespace) -> bool:
    """값을 물어봐도 되는지: -y 가 없고, 터미널에서 직접 실행한 경우만 True.

    파이프/백그라운드(nohup) 실행처럼 입력할 터미널이 없으면 묻지 않음 → 입력 대기로 멈추지 않음.
    """
    return not getattr(args, "yes", False) and sys.stdin.isatty()


def ask(label: str, default, cast=str, choices=None):
    """터미널에서 값을 물어봄. 그냥 엔터 → default 그대로 사용.

    cast=int 인데 숫자가 아닌 값, 또는 choices 에 없는 값을 넣으면 다시 물어봅니다.
    입력 스트림이 끝난 경우(EOF)에도 default 를 사용합니다.
    """
    hint = f" ({'/'.join(map(str, choices))})" if choices else ""
    while True:
        try:
            s = input(f"  {label}{hint} [{default}]: ").strip()
        except EOFError:
            print()
            return default
        if not s:
            return default
        try:
            value = cast(s)
        except ValueError:
            print("    ↳ 숫자를 입력하세요 (엔터 = 기본값).")
            continue
        if choices and value not in choices:
            print(f"    ↳ {'/'.join(map(str, choices))} 중에서 입력하세요 (엔터 = 기본값).")
            continue
        return value


# --------------------------------------------------------------------------- #
# 파일 목록
# --------------------------------------------------------------------------- #
def list_images(folder: Path) -> list[Path]:
    """folder 아래(하위 폴더 포함)의 이미지 파일을 정렬된 리스트로 반환.

    숨김 파일('.' 으로 시작, 예: macOS 의 ._xxx.jpg)은 제외한다. 폴더가 없으면 빈 리스트.
    """
    if not folder.exists():
        return []
    # rglob("*") = 하위 폴더까지 재귀 탐색 / 확장자는 대소문자 구분 없이 비교
    return sorted(p for p in folder.rglob("*") if p.suffix.lower() in IMG_EXTS and not p.name.startswith("."))


def label_path_for(img: Path, images_dir: Path, labels_dir: Path) -> Path:
    """이미지 경로에 대응하는 라벨(txt) 경로를 계산.

    예) images/sub/a.jpg → labels/sub/a.txt  (images_dir 기준 상대경로를 그대로 유지)
    """
    rel = img.relative_to(images_dir).with_suffix(".txt")
    return labels_dir / rel


# --------------------------------------------------------------------------- #
# YOLO 라벨 I/O
#   한 줄 = "class_id x_center y_center width height" (모두 0~1 정규화)
# --------------------------------------------------------------------------- #
def read_yolo_labels(txt: Path) -> list[tuple[int, float, float, float, float]]:
    """YOLO 라벨 파일을 읽어 [(cls, xc, yc, w, h), ...] 로 반환.

    파일이 없으면 빈 리스트. 형식이 잘못된 줄(값 5개 아님 / 숫자 아님)은 조용히 건너뛴다.
    (엄격한 검사는 03_check_labels.py 가 담당)
    """
    boxes = []
    if not txt.exists():
        return boxes
    for line in txt.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) != 5:
            continue
        try:
            c = int(float(parts[0]))         # "0.0" 처럼 저장된 클래스 ID 도 허용
            xc, yc, w, h = map(float, parts[1:])
        except ValueError:
            continue
        boxes.append((c, xc, yc, w, h))
    return boxes


def write_yolo_labels(txt: Path, boxes: Iterable[tuple[int, float, float, float, float]]) -> None:
    """박스 목록을 YOLO 라벨 파일로 저장 (소수점 6자리).

    박스가 0개면 빈 파일이 만들어진다 → '검토 완료된 배경 이미지' 라는 의미.
    """
    txt.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{int(c)} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}" for c, xc, yc, w, h in boxes]
    # 내용이 있을 때만 마지막 줄바꿈을 붙임 (빈 라벨은 완전히 빈 파일)
    txt.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def yolo_to_xyxy(box, img_w: int, img_h: int) -> tuple[float, float, float, float]:
    """YOLO (cls, xc, yc, w, h) 정규화 좌표 → 픽셀 (x1, y1, x2, y2).

    x1 = (중심 - 폭/2) × 이미지폭,  x2 = (중심 + 폭/2) × 이미지폭  (y 도 동일)
    img_w=img_h=1 을 넣으면 정규화 좌표 그대로의 xyxy 를 얻을 수 있다.
    """
    _, xc, yc, w, h = box
    return ((xc - w / 2) * img_w, (yc - h / 2) * img_h,
            (xc + w / 2) * img_w, (yc + h / 2) * img_h)


def xyxy_to_yolo(cls: int, x1, y1, x2, y2, img_w: int, img_h: int):
    """픽셀 (x1, y1, x2, y2) → YOLO (cls, xc, yc, w, h) 정규화 좌표.

    - 이미지 밖으로 나간 좌표는 0 ~ 이미지 크기로 잘라낸다(클리핑).
    - sorted() 로 x1<x2, y1<y2 가 되도록 정렬 → 어느 방향으로 드래그해도 안전.
    """
    x1, x2 = sorted((max(0.0, x1), min(float(img_w), x2)))
    y1, y2 = sorted((max(0.0, y1), min(float(img_h), y2)))
    # 중심 = 두 꼭짓점의 평균, 크기 = 차이 → 각각 이미지 크기로 나눠 0~1 로 정규화
    return (int(cls), (x1 + x2) / 2 / img_w, (y1 + y2) / 2 / img_h,
            (x2 - x1) / img_w, (y2 - y1) / img_h)


def iou_xyxy(a, b) -> float:
    """두 박스 (x1, y1, x2, y2) 의 IoU(Intersection over Union, 0~1) 계산.

    IoU = 겹치는 면적 / (A 면적 + B 면적 - 겹치는 면적).  1 이면 완전히 일치, 0 이면 안 겹침.
    """
    # 교집합 사각형: 왼쪽/위는 더 큰 값, 오른쪽/아래는 더 작은 값
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)     # 안 겹치면 음수 → 0 으로
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0           # 0 으로 나누기 방지


# --------------------------------------------------------------------------- #
# 시각화
# --------------------------------------------------------------------------- #
def color_of(cls: int) -> tuple[int, int, int]:
    """클래스 ID 에 해당하는 표시 색상(BGR). 클래스가 10개를 넘으면 색이 순환한다."""
    return PALETTE[int(cls) % len(PALETTE)]


def draw_box(img, xyxy, text: str, color, thickness: int = 2) -> None:
    """이미지(img, 직접 수정됨)에 사각형과 라벨 글자를 그린다.

    text 가 있으면 박스 왼쪽 위에 색이 채워진 배경 + 흰 글자를 표시한다.
    """
    import cv2
    x1, y1, x2, y2 = (int(round(v)) for v in xyxy)     # OpenCV 는 정수 픽셀 좌표만 받음
    cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
    if text:
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)   # 글자 폭/높이
        ty = max(y1, th + 4)       # 박스가 화면 맨 위에 붙어 있으면 글자가 잘리지 않도록 아래로 내림
        cv2.rectangle(img, (x1, ty - th - 4), (x1 + tw + 4, ty), color, -1)   # -1 = 내부 채우기
        cv2.putText(img, text, (x1 + 2, ty - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (255, 255, 255), 1, cv2.LINE_AA)       # LINE_AA = 안티에일리어싱(부드러운 글자)


def draw_yolo_boxes(img, boxes, names: list[str], color=None, prefix: str = "") -> None:
    """YOLO 정규화 박스 목록을 이미지 크기에 맞게 변환해 모두 그린다.

    color 를 주면 모든 박스를 같은 색으로, 없으면 클래스별 색으로 그린다.
    prefix 는 글자 앞에 붙일 문자열(예: "GT ").
    """
    h, w = img.shape[:2]
    for b in boxes:
        c = int(b[0])
        name = names[c] if 0 <= c < len(names) else f"id{c}"   # 범위 밖 ID 는 'id7' 처럼 표시
        draw_box(img, yolo_to_xyxy(b, w, h), f"{prefix}{name}", color or color_of(c))


def has_display() -> bool:
    """화면(GUI 창)을 띄울 수 있는 환경인지 확인.

    리눅스(라즈베리파이 SSH 등)는 DISPLAY / WAYLAND_DISPLAY 환경변수가 있어야 창을 띄울 수 있다.
    macOS / Windows 는 항상 True 로 본다.
    """
    import os
    if sys.platform.startswith("linux"):
        return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    return True
