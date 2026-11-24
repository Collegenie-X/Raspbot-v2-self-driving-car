"""
[3단계] 라벨 품질 점검

학습 전에 라벨 오류를 찾아냅니다. (잘못된 라벨 1개가 수십 장의 좋은 라벨 효과를 깎아 먹습니다)

검사 항목
  ERROR : 형식 오류(5칸 아님), 클래스 ID 범위 밖, 좌표가 0~1 밖, 폭/높이 ≤ 0, 이미지 손상
  WARN  : 라벨 없는 이미지(미검토), 이미지 없는 라벨, 매우 작은 박스, 중복 박스, 클래스 불균형
결과
  reports/label_check.md        — 통계·문제 목록
  reports/label_preview/*.jpg   — 박스를 그린 샘플 이미지 (눈으로 확인용)

처리 흐름 (main)
  1) 옵션 · 설정 로드, 이미지 목록 확인
  2) 이미지별 검사: 라벨 유무 → 이미지 손상 → check_file() 로 줄 단위 검사 → 통계 집계
     (--fix 이면 클리핑·정리된 라벨로 덮어쓰기)
  3) 이미지 없는 라벨(고아 라벨) 찾기
  4) 데이터셋 전체 경고: 클래스 0개 / 너무 적음 / 불균형 / 배경 비율 과다
  5) 콘솔 출력 (요약 · 클래스 분포 막대 · 주요 ERROR)
  6) Markdown 리포트 저장
  7) 미리보기 이미지 저장 (무작위 샘플에 박스 그리기)
  8) 다음 단계 안내, --strict 이면 ERROR 시 종료코드 1

사용 예:
  python scripts/03_check_labels.py
  python scripts/03_check_labels.py --fix      # 좌표 클리핑·잘못된 줄 삭제 후 저장
"""
from __future__ import annotations

import argparse
import random
import sys
from collections import Counter, defaultdict

import cv2

from common import (add_config_arg, banner, draw_yolo_boxes, iou_xyxy, label_path_for,
                    labeled_dirs, list_images, load_config, path_of, write_yolo_labels,
                    yolo_to_xyxy)

TINY_AREA = 0.0004   # 이미지 면적의 0.04% 미만 → 너무 작은 박스 경고
                     # (예: 640×480 이미지에서 약 11×11 픽셀 이하)


def check_file(txt, n_cls):
    """라벨 파일 1개 검사 → (정상 박스 목록, 에러 목록, 경고 목록, 수정 필요 여부)

    txt   : 라벨 파일 경로
    n_cls : 클래스 개수 (유효한 ID 는 0 ~ n_cls-1)
    정상 박스 목록은 이미지 밖으로 나간 좌표를 0~1 로 잘라낸(클리핑) 결과이며,
    --fix 시 이 목록이 그대로 파일에 다시 저장된다.
    """
    good, errors, warns, changed = [], [], [], False
    for ln, line in enumerate(txt.read_text(encoding="utf-8").splitlines(), 1):   # ln: 1부터 시작하는 줄 번호
        if not line.strip():                     # 빈 줄은 무시
            continue
        parts = line.split()
        # [검사 1] 값이 정확히 5개인가 (class xc yc w h)
        if len(parts) != 5:
            errors.append(f"L{ln}: 값이 5개가 아님 → '{line}'")
            changed = True
            continue
        # [검사 2] 모두 숫자인가
        try:
            c = int(float(parts[0]))
            xc, yc, w, h = map(float, parts[1:])
        except ValueError:
            errors.append(f"L{ln}: 숫자가 아님 → '{line}'")
            changed = True
            continue
        # [검사 3] 클래스 ID 가 범위 안인가
        if not 0 <= c < n_cls:
            errors.append(f"L{ln}: 클래스 ID {c} 가 범위(0~{n_cls - 1}) 밖")
            changed = True
            continue
        # [검사 4] 폭/높이가 양수인가
        if w <= 0 or h <= 0:
            errors.append(f"L{ln}: 폭/높이 ≤ 0")
            changed = True
            continue
        # [검사 5] 박스가 이미지(0~1) 안에 있는가 — 중심/크기 → 꼭짓점 좌표로 바꿔서 확인
        x1, y1, x2, y2 = xc - w / 2, yc - h / 2, xc + w / 2, yc + h / 2
        if min(x1, y1) < -0.01 or max(x2, y2) > 1.01:   # 1% 이상 벗어나면 에러로 보고 (작은 반올림 오차는 허용)
            errors.append(f"L{ln}: 박스가 이미지 밖 (정규화 좌표 0~1 초과)")
        if min(x1, y1) < 0 or max(x2, y2) > 1:     # 클리핑
            # 조금이라도 벗어나면 0~1 로 잘라낸 뒤 중심/크기를 다시 계산
            x1, y1, x2, y2 = max(0, x1), max(0, y1), min(1, x2), min(1, y2)
            xc, yc, w, h = (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1
            changed = True
        # [검사 6] 너무 작은 박스 (w*h = 이미지 대비 면적 비율)
        if w * h < TINY_AREA:
            warns.append(f"L{ln}: 매우 작은 박스 (면적 {w * h:.5f})")
        good.append((c, xc, yc, w, h))
    # [검사 7] 중복 박스: 같은 클래스끼리 IoU > 0.9 이면 같은 객체를 두 번 그렸을 가능성
    #   모든 쌍(i<j)을 비교. 정규화 좌표이므로 이미지 크기 대신 1, 1 을 넣어 변환
    for i in range(len(good)):
        for j in range(i + 1, len(good)):
            if good[i][0] == good[j][0] and iou_xyxy(yolo_to_xyxy(good[i], 1, 1),
                                                     yolo_to_xyxy(good[j], 1, 1)) > 0.9:
                warns.append(f"중복 박스 의심 (클래스 {good[i][0]}, IoU>0.9)")
    return good, errors, warns, changed


def main():
    """라벨 폴더 전체를 검사하고 콘솔 요약 · Markdown 리포트 · 미리보기 이미지를 만든다."""
    # ── 1) 옵션 · 설정 로드 ──
    ap = add_config_arg(argparse.ArgumentParser(description=__doc__,
                                                formatter_class=argparse.RawDescriptionHelpFormatter))
    ap.add_argument("--fix", action="store_true", help="좌표 클리핑, 잘못된 줄 삭제 후 덮어쓰기")
    ap.add_argument("--preview", type=int, default=24, help="미리보기 이미지 수")
    ap.add_argument("--strict", action="store_true", help="ERROR 가 있으면 종료코드 1")
    args = ap.parse_args()

    cfg = load_config(args.config)
    names = cfg["classes"]
    images_dir, labels_dir = labeled_dirs(cfg)
    report_dir = path_of(cfg, "reports")
    banner("3단계", "라벨 품질 점검")

    images = list_images(images_dir)
    if not images:
        sys.exit(f"[ERROR] 이미지가 없습니다: {images_dir}")

    # 집계용 변수
    inst = Counter()                     # 클래스별 박스 수
    img_per_cls = Counter()              # 클래스별 등장 이미지 수
    errors, warns = defaultdict(list), defaultdict(list)   # {이미지이름: [메시지, ...]}
    unlabeled, background, labeled = [], [], []            # 미라벨 / 빈 라벨(배경) / 라벨 있음
    sizes = defaultdict(list)            # 클래스별 박스 면적 비율

    # ── 2) 이미지별 검사 ──
    for img in images:
        txt = label_path_for(img, images_dir, labels_dir)
        if not txt.exists():             # 라벨 파일 자체가 없음 = 아직 검토 안 한 이미지
            unlabeled.append(img)
            continue
        if cv2.imread(str(img)) is None:
            errors[img.name].append("이미지를 읽을 수 없음 (손상)")
            continue
        good, e, w, changed = check_file(txt, len(names))
        errors[img.name] += e
        warns[img.name] += w
        if args.fix and changed:         # --fix: 정상 박스만 남겨 덮어쓰기 (잘못된 줄 삭제 + 클리핑)
            write_yolo_labels(txt, good)
        labeled.append(img)
        if not good:                     # 박스 0개 = 배경 이미지 (객체 없음)
            background.append(img)
        for b in good:
            inst[b[0]] += 1
            sizes[b[0]].append(b[3] * b[4])          # w*h = 이미지 대비 면적 비율
        for c in {b[0] for b in good}:               # set → 한 이미지에서 같은 클래스는 1번만 셈
            img_per_cls[c] += 1

    # ── 3) 이미지 없는 라벨(고아 라벨) 찾기 ──
    #   확장자를 뗀 상대경로로 비교 (images/a.jpg ↔ labels/a.txt)
    img_stems = {p.relative_to(images_dir).with_suffix("") for p in images}
    orphans = [t for t in labels_dir.rglob("*.txt")
               if t.relative_to(labels_dir).with_suffix("") not in img_stems] if labels_dir.exists() else []

    # ── 4) 데이터셋 전체 경고 ──
    # 클래스 불균형
    global_warns = []
    counts = [inst[i] for i in range(len(names))]
    for i, n in enumerate(names):
        if inst[i] == 0:
            global_warns.append(f"클래스 '{n}' 의 라벨이 0개 — 학습 불가")
        elif inst[i] < 50:
            global_warns.append(f"클래스 '{n}' 라벨 {inst[i]}개 (권장: 클래스당 최소 100~300개 이상)")
    # 가장 많은 클래스가 가장 적은 클래스의 5배를 넘으면 불균형 경고 (0개 클래스가 있으면 위에서 이미 경고)
    if min(counts) > 0 and max(counts) / min(counts) > 5:
        global_warns.append(f"클래스 불균형 큼 (최대/최소 = {max(counts) / min(counts):.1f}배) — 적은 클래스 데이터 보강 권장")
    # 배경(빈 라벨) 이미지가 30% 를 넘으면 경고 — 너무 많으면 모델이 '없음' 쪽으로 치우침
    if labeled and len(background) / len(labeled) > 0.3:
        global_warns.append(f"배경 이미지 비율 {len(background) / len(labeled):.0%} (권장 ≤ 10~20%)")

    n_err = sum(len(v) for v in errors.values())
    n_warn = sum(len(v) for v in warns.values())

    # ---------------- 콘솔 출력 ----------------
    # ── 5) 콘솔 출력 ──
    print(f"  전체 이미지 {len(images)} | 라벨 완료 {len(labeled)} | 미라벨 {len(unlabeled)} | "
          f"배경(빈 라벨) {len(background)} | 이미지 없는 라벨 {len(orphans)}")
    print("\n  클래스        박스수  이미지수  평균크기   분포")
    total = max(1, sum(counts))                     # 0 으로 나누기 방지
    for i, n in enumerate(names):
        avg = sum(sizes[i]) / len(sizes[i]) if sizes[i] else 0
        bar = "█" * int(30 * inst[i] / total)       # 전체 박스 대비 비율을 최대 30칸 막대로 표시
        print(f"  {i}:{n:<10} {inst[i]:>6}  {img_per_cls[i]:>7}   {avg:>6.1%}   {bar}")
    print(f"\n  ERROR {n_err} 건 | WARN {n_warn} 건")
    for g in global_warns:
        print(f"  ⚠ {g}")
    # 에러가 있는 파일 중 앞 10개만, 각 파일의 첫 에러 + '외 N건' 형태로 출력
    for name, es in list((k, v) for k, v in errors.items() if v)[:10]:
        print(f"  ❌ {name}: {es[0]}{' 외 %d건' % (len(es) - 1) if len(es) > 1 else ''}")

    # ---------------- 리포트 ----------------
    # ── 6) Markdown 리포트 저장 ──
    report_dir.mkdir(parents=True, exist_ok=True)
    md = ["# 라벨 품질 점검 리포트", "",
          "| 항목 | 값 |", "|---|---|",
          f"| 전체 이미지 | {len(images)} |", f"| 라벨 완료 | {len(labeled)} |",
          f"| 미라벨(미검토) | {len(unlabeled)} |", f"| 배경(빈 라벨) | {len(background)} |",
          f"| 이미지 없는 라벨 | {len(orphans)} |", f"| ERROR | {n_err} |", f"| WARN | {n_warn} |", "",
          "## 클래스 분포", "", "| ID | 클래스 | 박스 수 | 이미지 수 | 평균 박스 크기(면적비) |",
          "|---|---|---|---|---|"]
    for i, n in enumerate(names):
        avg = sum(sizes[i]) / len(sizes[i]) if sizes[i] else 0
        md.append(f"| {i} | {n} | {inst[i]} | {img_per_cls[i]} | {avg:.2%} |")
    # 'A or ["없음"]' : 목록이 비어 있으면 "없음" 한 줄로 대체
    md += ["", "## 전체 경고", ""] + [f"- ⚠ {g}" for g in global_warns or ["없음"]]
    md += ["", "## 파일별 ERROR", ""]
    md += [f"- `{k}`: " + "; ".join(v) for k, v in errors.items() if v] or ["- 없음"]
    md += ["", "## 파일별 WARN", ""]
    md += [f"- `{k}`: " + "; ".join(v) for k, v in warns.items() if v] or ["- 없음"]
    if unlabeled:
        md += ["", f"## 미라벨 이미지 ({len(unlabeled)})", ""] + [f"- `{p.name}`" for p in unlabeled[:200]]  # 최대 200개
    if orphans:
        md += ["", "## 이미지 없는 라벨", ""] + [f"- `{p.name}`" for p in orphans]
    (report_dir / "label_check.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    # 미리보기 이미지
    # ── 7) 미리보기 이미지 저장 ──
    prev_dir = report_dir / "label_preview"
    prev_dir.mkdir(parents=True, exist_ok=True)
    for old in prev_dir.glob("*.jpg"):              # 이전 실행 결과 삭제
        old.unlink()
    rng = random.Random(0)                          # seed 고정 → 실행할 때마다 같은 샘플이 뽑힘
    for img in rng.sample(labeled, min(args.preview, len(labeled))):
        im = cv2.imread(str(img))
        if im is None:
            continue
        # check_file(...)[0] = 정상(클리핑된) 박스 목록만 그림
        draw_yolo_boxes(im, check_file(label_path_for(img, images_dir, labels_dir), len(names))[0], names)
        cv2.imwrite(str(prev_dir / img.name), im)

    # ── 8) 다음 단계 안내 ──
    print(f"\n  리포트: {report_dir / 'label_check.md'}")
    print(f"  미리보기: {prev_dir}  ← 박스 위치가 맞는지 눈으로 확인하세요")
    if n_err and not args.fix:
        print("  ERROR 를 02_label_tool.py 로 수정하거나 --fix 로 자동 정리하세요.")
    else:
        print("  다음 단계 → python scripts/04_split_dataset.py")
    if args.strict and n_err and not args.fix:      # 자동화 파이프라인에서 실패로 인식시키기 위함
        sys.exit(1)


if __name__ == "__main__":
    main()
