"""
[2단계] 라벨링 도구 (OpenCV 기반, 추가 설치 불필요)

data/labeled/images 의 이미지에 바운딩 박스를 그려 YOLO 포맷 txt 로 저장합니다.
  - 저장 위치: data/labeled/labels/<이미지이름>.txt
  - 객체가 없는 이미지(배경)는 박스 없이 저장하면 빈 txt 가 생성 → '검토 완료된 배경'으로 학습에 사용

조작법 (창이 활성화된 상태에서):
  마우스 왼쪽 드래그 : 현재 클래스로 박스 그리기
  마우스 오른쪽 클릭 : 커서 아래 박스 삭제
  0~9               : 현재 클래스 선택 (선택된 박스가 있으면 그 박스의 클래스 변경)
  d / Space         : 저장 후 다음 이미지
  a                 : 저장 후 이전 이미지
  f                 : 아직 라벨이 없는 다음 이미지로 이동
  u                 : 마지막 박스 취소      c : 모든 박스 지우기
  s                 : 저장                 h : 도움말 표시 on/off
  q / ESC           : 저장 후 종료

사용 예:
  python scripts/02_label_tool.py
  python scripts/02_label_tool.py --only-unlabeled

처리 흐름:
  1) config 로드 → 클래스 목록, 라벨링 폴더(images/, labels/) 결정
  2) 사전 점검: 이미지 존재 여부, 화면(DISPLAY) 존재 여부
  3) labels/ 폴더 생성 + classes.txt 기록 (다른 라벨링 툴과 호환용)
  4) 시작 위치 결정 (--start 또는 --only-unlabeled)
  5) LabelTool.run() — 이벤트 루프 (render → 키 입력 → 상태 변경 → 저장)
  6) 종료 후 라벨 완료 개수 출력

좌표계 (중요):
  - self.boxes 는 항상 '원본 이미지 픽셀 좌표' [cls, x1, y1, x2, y2] 로 보관
  - 화면은 큰 이미지를 MAX_W×MAX_H 안으로 축소(self.scale)해서 보여 줌
  - 마우스 좌표(화면) ÷ scale = 원본 좌표,  저장할 때만 YOLO 정규화(0~1) 좌표로 변환

자세한 구조 분석: scripts/02_label_tool.md
"""
from __future__ import annotations

import argparse
import sys

import cv2

from common import (add_config_arg, banner, color_of, draw_box, has_display, label_path_for,
                    labeled_dirs, list_images, load_config, read_yolo_labels,
                    write_yolo_labels, xyxy_to_yolo, yolo_to_xyxy)

# ── 화면 / 도움말 상수 ──
WIN = "YOLO Label Tool"          # OpenCV 창 이름 (마우스 콜백 등록 시 같은 이름 사용)
MAX_W, MAX_H = 1280, 800         # 화면 표시 최대 크기 — 이보다 큰 이미지는 축소해서 보여 줌
HELP = ["drag:box  R-click:delete  0-9:class", "d/space:next  a:prev  f:next unlabeled",
        "u:undo  c:clear  s:save  h:help  q:quit"]   # 화면 좌상단에 그려지는 단축키 안내


class LabelTool:
    """OpenCV 창 하나로 동작하는 바운딩 박스 라벨링 도구.

    상태(state)
      idx        : 현재 보고 있는 이미지 인덱스
      cls        : 새 박스에 붙일 '현재 클래스' ID (숫자키로 변경)
      boxes      : 현재 이미지의 박스 목록 [[cls, x1, y1, x2, y2], ...] (원본 픽셀 좌표)
      selected   : 선택된 박스 인덱스 (굵게 표시, 숫자키로 클래스 변경 대상)
      drag_start : 드래그 시작점 (원본 좌표). None 이면 드래그 중이 아님
      scale      : 화면 표시 배율 (≤ 1.0)
      dirty      : 마지막 저장 이후 변경이 있었는지 (불필요한 저장 방지)
    """

    def __init__(self, images, images_dir, labels_dir, names):
        """images: 이미지 경로 리스트, images_dir/labels_dir: 라벨 경로 계산용 기준 폴더, names: 클래스 이름."""
        self.images, self.images_dir, self.labels_dir, self.names = images, images_dir, labels_dir, names
        self.idx, self.cls, self.show_help = 0, 0, True
        self.boxes: list[list] = []      # [cls, x1, y1, x2, y2] (원본 픽셀 좌표)
        self.drag_start = None           # 드래그 시작점 (원본 좌표)
        self.drag_now = None             # 드래그 중 현재 마우스 위치 (미리보기 박스용)
        self.selected = None             # 선택된 박스 인덱스
        self.img = None                  # 현재 원본 이미지 (BGR ndarray)
        self.scale = 1.0                 # 화면 배율 = min(1, MAX_W/w, MAX_H/h)
        self.dirty = False               # 미저장 변경 여부

    # ---------------- 파일 ----------------
    def label_file(self, i=None):
        """i 번째(기본: 현재) 이미지에 대응하는 라벨 txt 경로. (images/a/b.jpg → labels/a/b.txt)"""
        return label_path_for(self.images[self.idx if i is None else i], self.images_dir, self.labels_dir)

    def load(self):
        """현재 idx 의 이미지와 기존 라벨을 메모리로 읽어 옴. 이미지가 손상되었으면 False."""
        self.img = cv2.imread(str(self.images[self.idx]))
        if self.img is None:
            print(f"  [WARN] 이미지를 읽을 수 없음: {self.images[self.idx]}")
            return False
        h, w = self.img.shape[:2]
        # 화면에 맞게 축소 배율 계산 (확대는 하지 않으므로 최대 1.0)
        self.scale = min(1.0, MAX_W / w, MAX_H / h)
        # 기존 YOLO 라벨(정규화 좌표)을 원본 픽셀 좌표 [cls, x1, y1, x2, y2] 로 변환해 편집 가능하게 함
        self.boxes = [[b[0], *yolo_to_xyxy(b, w, h)] for b in read_yolo_labels(self.label_file())]
        self.selected, self.dirty = None, False
        return True

    def save(self, force=False):
        """현재 박스를 YOLO txt 로 저장.

        - 변경 없음(dirty=False) + 라벨 파일이 이미 있음 + force=False → 저장 생략
        - force=True 이면 박스가 0개여도 '빈 txt' 를 만듦 → 검토 완료된 배경 이미지로 기록
        """
        if self.img is None or (not self.dirty and not force and self.label_file().exists()):
            return
        h, w = self.img.shape[:2]
        # 픽셀 좌표 → YOLO 정규화 좌표. 폭/높이 2px 미만의 '점 같은' 박스는 버림
        boxes = [xyxy_to_yolo(c, x1, y1, x2, y2, w, h) for c, x1, y1, x2, y2 in self.boxes
                 if abs(x2 - x1) >= 2 and abs(y2 - y1) >= 2]
        write_yolo_labels(self.label_file(), boxes)
        self.dirty = False

    # ---------------- 마우스 ----------------
    def on_mouse(self, event, x, y, flags, _):
        """OpenCV 마우스 콜백. (x, y) 는 '화면' 좌표이므로 scale 로 나눠 원본 좌표로 바꿔서 사용."""
        ox, oy = x / self.scale, y / self.scale          # 화면 좌표 → 원본 이미지 좌표
        if event == cv2.EVENT_LBUTTONDOWN:
            # 드래그 시작
            self.drag_start, self.drag_now = (ox, oy), (ox, oy)
        elif event == cv2.EVENT_MOUSEMOVE and self.drag_start:
            # 드래그 중 → render() 가 얇은 미리보기 박스를 그림
            self.drag_now = (ox, oy)
        elif event == cv2.EVENT_LBUTTONUP and self.drag_start:
            (x1, y1), (x2, y2) = self.drag_start, (ox, oy)
            self.drag_start = None
            # 화면 기준 4px 보다 크게 끌었을 때만 '박스 생성', 아니면 '클릭'으로 간주
            if abs(x2 - x1) * self.scale > 4 and abs(y2 - y1) * self.scale > 4:
                # 어느 방향으로 드래그했든 (좌상단, 우하단) 순서로 정렬해서 저장
                self.boxes.append([self.cls, min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)])
                self.selected, self.dirty = len(self.boxes) - 1, True   # 방금 만든 박스를 선택 상태로
            else:  # 클릭만 했으면 박스 선택
                self.selected = self.box_at(ox, oy)
        elif event == cv2.EVENT_RBUTTONDOWN:
            # 오른쪽 클릭 → 커서 아래 박스 삭제
            i = self.box_at(ox, oy)
            if i is not None:
                self.boxes.pop(i)
                self.selected, self.dirty = None, True

    def box_at(self, x, y):
        """원본 좌표 (x, y) 를 포함하는 박스 인덱스. 여러 개가 겹치면 '면적이 가장 작은' 박스를 고름.

        큰 박스 안에 작은 박스가 있을 때(예: 차 안의 신호등) 작은 박스를 클릭할 수 있게 하기 위함.
        """
        hits = [(abs((b[3] - b[1]) * (b[4] - b[2])), i) for i, b in enumerate(self.boxes)
                if b[1] <= x <= b[3] and b[2] <= y <= b[4]]      # (면적, 인덱스) 목록
        return min(hits)[1] if hits else None   # 겹치면 가장 작은 박스

    # ---------------- 화면 ----------------
    def render(self):
        """현재 상태를 창에 그림: 박스 → 드래그 미리보기 → 축소 → 상태줄/도움말."""
        vis = self.img.copy()                    # 원본은 건드리지 않고 복사본에 그림
        for i, (c, *xyxy) in enumerate(self.boxes):
            name = self.names[c] if c < len(self.names) else f"id{c}"
            # 선택된 박스는 두께 4, 나머지는 2
            draw_box(vis, xyxy, f"{c}:{name}", color_of(c), 4 if i == self.selected else 2)
        if self.drag_start and self.drag_now:
            # 드래그 중인 박스 미리보기 (얇은 선, 텍스트 없음)
            draw_box(vis, (*self.drag_start, *self.drag_now), "", color_of(self.cls), 1)
        if self.scale < 1:
            # 박스를 원본 좌표로 먼저 그린 뒤 통째로 축소 → 좌표 변환 실수가 없음
            vis = cv2.resize(vis, None, fx=self.scale, fy=self.scale, interpolation=cv2.INTER_AREA)
        # 진행률: 라벨 txt 가 존재하는 이미지 수 (매 프레임 계산하지만 수천 장 수준에서는 충분히 빠름)
        done = sum(1 for i in range(len(self.images)) if self.label_file(i).exists())
        status = (f"[{self.idx + 1}/{len(self.images)}] {self.images[self.idx].name} | "
                  f"class {self.cls}:{self.names[self.cls]} | boxes {len(self.boxes)} | "
                  f"labeled {done}/{len(self.images)}{' *' if self.dirty else ''}")   # '*' = 미저장 변경 있음
        lines = [status] + (HELP + [" ".join(f"{i}:{n}" for i, n in enumerate(self.names))]
                            if self.show_help else [])
        for k, t in enumerate(lines):
            y = 22 + k * 22
            # 검은 두꺼운 글씨 위에 흰 얇은 글씨 → 어떤 배경에서도 읽히는 외곽선 효과
            cv2.putText(vis, t, (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(vis, t, (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.imshow(WIN, vis)

    def goto(self, i):
        """현재 이미지를 저장한 뒤 i 번째 이미지로 이동 (범위 밖이면 양 끝으로 고정).

        이동한 이미지가 손상되어 열리지 않으면 목록에서 제거하고 그 자리의 이미지를 다시 로드.
        """
        self.save()
        self.idx = max(0, min(len(self.images) - 1, i))   # 0 ~ len-1 로 클램프
        if not self.load():
            self.images.pop(self.idx)
            self.idx = min(self.idx, len(self.images) - 1)
            self.load()

    def next_unlabeled(self):
        """현재 위치 다음부터 끝까지, 이어서 처음부터 현재까지 순환하며 라벨 없는 이미지를 찾아 이동."""
        for i in list(range(self.idx + 1, len(self.images))) + list(range(0, self.idx + 1)):
            if not self.label_file(i).exists():
                return self.goto(i)
        print("  ✅ 모든 이미지에 라벨이 있습니다.")

    # ---------------- 루프 ----------------
    def run(self, start=0):
        """메인 이벤트 루프. 20ms 마다 화면을 다시 그리고 키 입력을 처리."""
        cv2.namedWindow(WIN, cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback(WIN, self.on_mouse)          # 마우스 이벤트 → on_mouse()
        self.idx = start
        self.load()
        while True:
            self.render()
            key = cv2.waitKey(20) & 0xFF                  # 20ms 대기 (≈50fps 로 화면 갱신)
            if key == 255:                                # 255 = 입력 없음
                if cv2.getWindowProperty(WIN, cv2.WND_PROP_VISIBLE) < 1:   # 창 닫기 버튼
                    break
                continue
            ch = chr(key)
            if ch.isdigit() and int(ch) < len(self.names):
                # 숫자키: 현재 클래스 변경 + 선택된 박스가 있으면 그 박스의 클래스도 변경
                self.cls = int(ch)
                if self.selected is not None and self.selected < len(self.boxes):
                    self.boxes[self.selected][0] = self.cls
                    self.dirty = True
            elif ch in ("d", " "):
                # 다음: force 저장 → 박스가 없어도 빈 txt 생성 (배경 이미지 검토 완료 표시)
                self.save(force=True)
                if self.idx < len(self.images) - 1:
                    self.goto(self.idx + 1)
            elif ch == "a":
                # 이전: goto() 내부에서 변경분만 저장
                self.goto(self.idx - 1)
            elif ch == "f":
                self.save(force=True)
                self.next_unlabeled()
            elif ch == "u" and self.boxes:
                # 되돌리기: 마지막에 추가된 박스 삭제
                self.boxes.pop()
                self.selected, self.dirty = None, True
            elif ch == "c":
                self.boxes, self.selected, self.dirty = [], None, True
            elif ch == "s":
                self.save(force=True)
                print(f"  저장: {self.label_file().name}")
            elif ch == "h":
                self.show_help = not self.show_help
            elif ch == "q" or key == 27:                  # 27 = ESC
                break
        self.save()                                       # 종료 직전 변경분 저장
        cv2.destroyAllWindows()


def main():
    """CLI 진입점: 인자 파싱 → 사전 점검 → LabelTool 실행 → 결과 출력."""
    # ── 1) 인자 / 설정 ──
    ap = add_config_arg(argparse.ArgumentParser(description=__doc__,
                                                formatter_class=argparse.RawDescriptionHelpFormatter))
    ap.add_argument("--only-unlabeled", action="store_true", help="라벨 없는 이미지부터 시작")
    ap.add_argument("--start", type=int, default=0, help="시작 인덱스")
    args = ap.parse_args()

    cfg = load_config(args.config)
    names = cfg["classes"]                          # 순서 = class_id
    images_dir, labels_dir = labeled_dirs(cfg)      # data/labeled/images, data/labeled/labels
    banner("2단계", "라벨링 (YOLO 포맷)")

    # ── 2) 사전 점검 ──
    if len(names) > 10:
        print("  [WARN] 숫자키는 0~9 까지만 지원합니다. 클래스 10개 이상이면 Label Studio 사용을 권장합니다.")
    images = list_images(images_dir)
    if not images:
        sys.exit(f"[ERROR] 이미지가 없습니다: {images_dir}  (1단계 01_prepare_images.py 먼저 실행)")
    if not has_display():
        # SSH 로 접속한 라즈베리파이 등 GUI 가 없는 환경에서는 창을 띄울 수 없음
        sys.exit("[ERROR] 화면(DISPLAY)이 없습니다. PC 에서 실행하거나 VNC/모니터를 연결하세요.")

    # ── 3) 출력 폴더 + classes.txt (LabelImg 등 다른 도구와 호환) ──
    labels_dir.mkdir(parents=True, exist_ok=True)
    (labels_dir.parent / "classes.txt").write_text("\n".join(names) + "\n", encoding="utf-8")

    # ── 4) 시작 위치 결정 ──
    tool = LabelTool(images, images_dir, labels_dir, names)
    start = args.start
    if args.only_unlabeled:
        # 라벨 txt 가 없는 첫 이미지 (모두 있으면 0)
        start = next((i for i in range(len(images)) if not tool.label_file(i).exists()), 0)
    print(f"  이미지 {len(images)} 장 | 클래스: {', '.join(f'{i}:{n}' for i, n in enumerate(names))}")
    print("  창을 클릭한 뒤 키보드를 사용하세요. (q: 종료)")

    # ── 5) 이벤트 루프 실행 ──
    tool.run(start)

    # ── 6) 결과 ──
    done = sum(1 for i in range(len(tool.images)) if tool.label_file(i).exists())
    print(f"\n  라벨 완료: {done}/{len(tool.images)}")
    print("  다음 단계 → python scripts/03_check_labels.py")


if __name__ == "__main__":
    main()
