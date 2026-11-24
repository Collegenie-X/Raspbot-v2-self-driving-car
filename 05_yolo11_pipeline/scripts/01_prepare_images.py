"""
[1단계] 수집 데이터 정리 — 라벨링 전에 이미지 준비

수집한 원본(data/raw)의 사진·동영상을 라벨링용 이미지(data/labeled/images)로 정리합니다.
  1) 동영상 → N 프레임마다 1장 추출
  2) 너무 큰 이미지는 축소, 너무 작은/깨진 이미지는 제외
  3) dHash 로 거의 같은 이미지(연속 프레임 등) 제거
  4) "<원본이름>_<번호>.jpg" 형식으로 저장  →  4단계에서 같은 원본끼리 묶는 데 사용

입력 : data/raw/ (하위 폴더 포함) 의 사진·동영상
출력 : data/labeled/images/*.jpg

처리 흐름 (main)
  1) 설정 로드 및 옵션(--src/--dst/--every/--dedupe) 결정
  2) 원본 폴더 확인 (없으면 만들고 안내 후 종료)
  3) Writer 준비 (크기 필터 · 리사이즈 · 중복 제거 · 저장 담당)
  4) 파일 하나씩 처리: 사진 → 그대로 저장 / 동영상 → every 프레임마다 저장
  5) 결과 통계 출력

사용 예:
  python scripts/01_prepare_images.py
  python scripts/01_prepare_images.py --src ~/captures --every 5 --dedupe 0
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import cv2
import numpy as np

from common import (IMG_EXTS, VIDEO_EXTS, add_config_arg, banner, labeled_dirs,
                    load_config, path_of)


def dhash(img: np.ndarray, size: int = 8) -> int:
    """차분 해시(dHash) — 이미지가 비슷하면 비트가 비슷하다.

    1) 흑백 변환 → 2) (size+1)×size 로 아주 작게 축소 → 3) 가로로 이웃한 픽셀끼리
    '오른쪽이 더 밝은가?' 를 비교해 1/0 비트로 만든다 → size×size = 64비트 정수.
    두 해시의 다른 비트 수(해밍거리)가 작을수록 비슷한 이미지.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img   # ndim==3 → 컬러
    # 폭을 size+1 로 해야 인접 비교 후 정확히 size 개의 비트가 나온다
    small = cv2.resize(gray, (size + 1, size), interpolation=cv2.INTER_AREA)
    bits = (small[:, 1:] > small[:, :-1]).flatten()        # 오른쪽 픽셀 > 왼쪽 픽셀 → True
    return int("".join("1" if b else "0" for b in bits), 2)   # 비트 문자열 → 2진수 정수


def safe_stem(p: Path) -> str:
    """파일/폴더 이름을 저장용 안전한 이름으로 변환 (영문·숫자·한글·'-' 만 남김)."""
    # '_' 는 그룹 구분자로 쓰므로 원본 이름 안의 '_' 와 특수문자는 '-' 로 치환
    #   정규식 [^...]+ : 허용 문자(0-9 A-Z a-z 가-힣 -) 가 아닌 문자가 1개 이상 연속된 구간
    return re.sub(r"[^0-9A-Za-z가-힣\-]+", "-", p.stem).strip("-") or "img"   # 다 지워지면 "img"


class Writer:
    """이미지 저장 담당: 크기 필터 → 리사이즈 → 중복 검사 → JPG 저장 + 통계 집계."""

    def __init__(self, dst: Path, max_side: int, min_side: int, dedupe: int):
        """dst: 출력 폴더 / max_side: 긴 변 최대 크기 / min_side: 짧은 변 최소 크기 /
        dedupe: 중복 판정 해밍거리 (0 이하면 중복 제거 끔)"""
        self.dst, self.max_side, self.min_side, self.dedupe = dst, max_side, min_side, dedupe
        self.hashes: list[int] = []               # 지금까지 저장한 이미지들의 dHash
        self.saved = self.dup = self.small = 0    # 통계: 저장 / 중복 제외 / 작아서 제외

    def is_dup(self, h: int) -> bool:
        """해시 h 가 이미 저장한 이미지와 거의 같은지(해밍거리 ≤ dedupe) 판단."""
        if self.dedupe <= 0:
            return False
        # 최근 2000장과만 비교 (대량 데이터에서도 빠르게)
        #   h ^ o : XOR → 서로 다른 비트만 1  /  bit_count() : 1 의 개수 = 해밍거리
        return any((h ^ o).bit_count() <= self.dedupe for o in self.hashes[-2000:])

    def save(self, img: np.ndarray, name: str) -> None:
        """이미지 1장을 조건에 맞으면 '<name>.jpg' 로 저장 (조건에 안 맞으면 통계만 증가)."""
        h, w = img.shape[:2]
        if min(h, w) < self.min_side:             # 너무 작은 이미지는 학습에 도움이 안 됨
            self.small += 1
            return
        scale = self.max_side / max(h, w)
        if scale < 1:                              # 긴 변이 max_side 보다 클 때만 축소 (확대는 안 함)
            img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        hv = dhash(img)
        if self.is_dup(hv):
            self.dup += 1
            return
        self.hashes.append(hv)
        out = self.dst / f"{name}.jpg"
        if out.exists():                           # 이미 있으면 덮어쓰지 않음 (재실행해도 안전)
            return
        cv2.imwrite(str(out), img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        self.saved += 1


def main() -> None:
    """명령줄 옵션을 읽어 원본 폴더의 사진/동영상을 라벨링용 이미지로 정리한다."""
    # ── 1) 설정 로드 및 옵션 결정 ──
    ap = add_config_arg(argparse.ArgumentParser(description=__doc__,
                                                formatter_class=argparse.RawDescriptionHelpFormatter))
    ap.add_argument("--src", help="원본 폴더 (기본: config paths.raw)")
    ap.add_argument("--dst", help="출력 폴더 (기본: data/labeled/images)")
    ap.add_argument("--every", type=int, help="동영상 프레임 추출 간격")
    ap.add_argument("--dedupe", type=int, help="중복 판정 해밍거리 (0=끄기)")
    args = ap.parse_args()

    cfg = load_config(args.config)
    pc = cfg.get("prepare", {})
    # 명령줄 옵션이 있으면 우선, 없으면 config 값 사용 (expanduser: '~' → 홈 폴더)
    src = Path(args.src).expanduser() if args.src else path_of(cfg, "raw")
    dst = Path(args.dst).expanduser() if args.dst else labeled_dirs(cfg)[0]
    every = args.every or pc.get("video_every_n", 10)
    # --dedupe 0 은 '끄기' 라는 의미 있는 값이므로 'or' 대신 None 비교로 처리
    dedupe = pc.get("dedupe_hamming", 4) if args.dedupe is None else args.dedupe

    banner("1단계", "수집 데이터 정리 (프레임 추출 · 리사이즈 · 중복 제거)")
    print(f"  원본: {src}\n  출력: {dst}")

    # ── 2) 원본 폴더 확인 ──
    if not src.exists():
        src.mkdir(parents=True, exist_ok=True)
        sys.exit(f"[안내] {src} 폴더를 만들었습니다. 수집한 사진/동영상을 넣고 다시 실행하세요.")

    # ── 3) Writer 준비 ──
    dst.mkdir(parents=True, exist_ok=True)
    wr = Writer(dst, pc.get("max_side", 1280), pc.get("min_side", 160), dedupe)
    files = sorted(p for p in src.rglob("*") if p.is_file() and not p.name.startswith("."))
    broken = 0                                     # 읽을 수 없는(손상된) 사진 수

    # ── 4) 파일별 처리 ──
    for f in files:
        ext = f.suffix.lower()
        if ext in IMG_EXTS:
            # [사진] 한 장씩 읽어서 저장
            img = cv2.imread(str(f))
            if img is None:                        # imread 실패 = 손상 또는 지원하지 않는 형식
                broken += 1
                continue
            # 사진은 상위 폴더 이름을 그룹으로 사용 (같은 촬영 세션 = 같은 split)
            #   raw/ 바로 아래 있는 사진은 모두 "photo" 그룹
            group = safe_stem(f.parent) if f.parent != src else "photo"
            wr.save(img, f"{group}_{safe_stem(f)}")
        elif ext in VIDEO_EXTS:
            # [동영상] 프레임을 순서대로 읽으며 every 프레임마다 1장 저장
            cap = cv2.VideoCapture(str(f))
            idx = kept = 0                         # idx: 읽은 프레임 번호 / kept: 실제 저장된 수
            while True:
                ok, frame = cap.read()
                if not ok:                         # 영상 끝
                    break
                if idx % every == 0:
                    before = wr.saved
                    # 이름 = "<영상이름>_<프레임번호 6자리>" → '_' 앞부분이 4단계 그룹 키가 됨
                    wr.save(frame, f"{safe_stem(f)}_{idx:06d}")
                    kept += wr.saved - before      # 중복/작음으로 버려졌으면 0 이 더해짐
                idx += 1
            cap.release()
            print(f"  🎞  {f.name}: {idx} 프레임 → {kept} 장 저장")

    # ── 5) 결과 출력 ──
    print("\n  ── 결과 ──")
    print(f"  저장: {wr.saved} 장 | 중복 제외: {wr.dup} | 작은 이미지 제외: {wr.small} | 손상: {broken}")
    print(f"  다음 단계 → python scripts/02_label_tool.py")


if __name__ == "__main__":
    main()
