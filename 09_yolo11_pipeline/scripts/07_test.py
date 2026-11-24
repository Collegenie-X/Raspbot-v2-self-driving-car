"""
[7단계] 모델 테스트 — 실제 운영 조건에서 이미지 단위 오류 분석

6단계(mAP)는 '모든 신뢰도 구간의 평균' 점수입니다. 하지만 로봇은 하나의 conf 임계값(예: 0.5)과
작은 입력 크기(imgsz=320)로 동작합니다. 이 단계는 **실제 운영 설정 그대로** test 이미지를 추론해
정답과 1:1 로 비교합니다.

  TP (정탐)      : 정답 박스와 IoU ≥ 0.5, 클래스도 일치
  FP (오탐)      : 정답이 없는 곳을 탐지
  FN (미탐)      : 정답 객체를 놓침
  WRONG (오분류) : 위치는 맞는데 클래스가 틀림 (예: red ↔ green)

입력:
  models/best.pt  +  datasets/raspbot/{images,labels}/<split>/

출력:
  reports/test_<split>.md          — 클래스별 TP/FP/FN, 혼동표, 최악 이미지 목록, 지연시간
  reports/test_<split>.json        — 같은 내용 (기계 판독용)
  reports/test_failures/*.jpg      — 틀린 이미지 (초록=정답, 빨강=예측)

처리 흐름 (main):
  1) 설정 로드 — split / conf / imgsz / 매칭 IoU (운영 조건)
  2) 모델 로드 + 워밍업 (첫 추론의 초기화 시간이 지연시간 통계에 섞이지 않도록)
  3) 이미지마다: 정답 읽기 → 추론(시간 측정) → match() 로 TP/FP/FN/WRONG 분류
     → 통계 누적, 오류 이미지는 정답/예측 박스를 그려 저장
  4) 집계 — 클래스별·전체 정밀도/재현율, 완벽 이미지 비율, 지연시간(평균/p95)
  5) 콘솔 출력 + 리포트(.md / .json) 저장

사용 예:
  python scripts/07_test.py
  python scripts/07_test.py --conf 0.4 --imgsz 640
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

import cv2

from common import (add_config_arg, banner, data_yaml_path, default_weights, draw_box,
                    iou_xyxy, list_images, load_config, path_of, pick_device, read_yolo_labels,
                    yolo_to_xyxy)


def match(gts, preds, iou_th):
    """탐욕적 매칭. gts/preds: [(cls, x1,y1,x2,y2)] (preds 는 conf 내림차순)
    반환: tp, fp, fn, wrong 리스트 (각각 원소 튜플)

    - tp    : [(정답, 예측)]  같은 클래스 + IoU ≥ iou_th
    - fp    : [예측]          어떤 정답과도 겹치지 않음
    - fn    : [정답]          어떤 예측과도 매칭되지 않음
    - wrong : [(정답, 예측)]  위치는 겹치지만 클래스가 다름
    신뢰도가 높은 예측부터 처리하고, 정답 하나는 예측 하나에만 매칭됩니다(used 집합).
    """
    used = set()                              # 이미 매칭된 정답 박스의 인덱스
    tp, fp, wrong = [], [], []
    for p in preds:
        # best_iou 를 iou_th 로 시작 → 기준 미만 IoU 는 자동으로 후보에서 제외
        best_i, best_iou = -1, iou_th
        for i, g in enumerate(gts):           # 1) 같은 클래스 우선
            if i in used or g[0] != p[0]:
                continue
            iou = iou_xyxy(g[1:5], p[1:5])     # g[1:5], p[1:5] = (x1, y1, x2, y2)
            if iou >= best_iou:                # 가장 많이 겹치는 같은 클래스 정답을 선택
                best_i, best_iou = i, iou
        if best_i >= 0:
            used.add(best_i)
            tp.append((gts[best_i], p))
            continue
        for i, g in enumerate(gts):           # 2) 클래스가 다른 정답과 겹치면 오분류
            if i not in used and iou_xyxy(g[1:5], p[1:5]) >= iou_th:
                used.add(i)
                wrong.append((g, p))
                break
        else:                                 # for-else: break 없이 끝남 = 겹치는 정답 없음 → 오탐
            fp.append(p)
    fn = [g for i, g in enumerate(gts) if i not in used]   # 끝까지 매칭 안 된 정답 = 미탐
    return tp, fp, fn, wrong


def main():
    """7단계 실행: 운영 조건(conf/imgsz) 그대로 split 이미지를 추론해 정답과 1:1 비교·분석한다."""
    ap = add_config_arg(argparse.ArgumentParser(description=__doc__,
                                                formatter_class=argparse.RawDescriptionHelpFormatter))
    ap.add_argument("--weights")
    ap.add_argument("--split", help="test / val (기본: config test.split)")
    ap.add_argument("--conf", type=float)
    ap.add_argument("--imgsz", type=int)
    ap.add_argument("--device")
    args = ap.parse_args()

    from ultralytics import YOLO

    # ── 1) 설정 로드 (운영 조건) ──
    cfg = load_config(args.config)
    tc = cfg.get("test", {})
    split = args.split or tc.get("split", "test")
    conf = args.conf or tc.get("conf", 0.5)        # 로봇이 실제로 쓰는 신뢰도 임계값
    imgsz = args.imgsz or tc.get("imgsz", 320)     # 라즈베리파이 운영 입력 크기
    iou_th = tc.get("match_iou", 0.5)              # 정답-예측 매칭 IoU 기준
    weights = Path(args.weights) if args.weights else default_weights(cfg)
    device = pick_device(args.device or cfg["train"].get("device", "auto"))
    ds = path_of(cfg, "dataset")
    img_dir, lbl_dir = ds / "images" / split, ds / "labels" / split

    banner("7단계", f"모델 테스트 (split={split}, conf={conf}, imgsz={imgsz})")
    if not weights.exists() or not data_yaml_path(cfg).exists():
        sys.exit("[ERROR] models/best.pt 또는 data.yaml 이 없습니다. 4~5단계를 먼저 실행하세요.")
    images = list_images(img_dir)
    if not images:
        sys.exit(f"[ERROR] {img_dir} 에 이미지가 없습니다.")

    # ── 2) 모델 로드 + 워밍업 ──
    model = YOLO(str(weights))
    names = [model.names[i] for i in range(len(model.names))]   # dict → id 순서 리스트
    model.predict(cv2.imread(str(images[0])), imgsz=imgsz, device=device, verbose=False)  # 워밍업

    stats = {k: Counter() for k in ("tp", "fp", "fn", "gt")}   # stats[종류][class_id] = 개수
    confusion = Counter()                      # (정답, 예측) 오분류 쌍
    per_image, latencies = [], []              # 이미지별 결과 / 추론 시간(ms)
    fail_dir = path_of(cfg, "reports") / "test_failures"
    fail_dir.mkdir(parents=True, exist_ok=True)
    for old in fail_dir.glob("*.jpg"):         # 이전 실행의 실패 이미지 삭제
        old.unlink()
    n_fail_saved = 0

    # ── 3) 이미지별 추론 + 매칭 ──
    for img_path in images:
        img = cv2.imread(str(img_path))
        h, w = img.shape[:2]
        # 정답: YOLO 정규화 좌표 → 픽셀 (cls, x1, y1, x2, y2)
        gts = [(b[0], *yolo_to_xyxy(b, w, h)) for b in read_yolo_labels(lbl_dir / f"{img_path.stem}.txt")]
        t0 = time.perf_counter()
        r = model.predict(img, conf=conf, imgsz=imgsz, device=device, verbose=False)[0]
        latencies.append((time.perf_counter() - t0) * 1000)   # 전처리+추론+후처리 포함 ms
        # 신뢰도 내림차순 정렬 → 확신 높은 예측이 먼저 정답을 차지 (탐욕적 매칭)
        order = r.boxes.conf.argsort(descending=True).tolist()
        cls, xyxy, cf = r.boxes.cls.tolist(), r.boxes.xyxy.tolist(), r.boxes.conf.tolist()
        preds = [(int(cls[i]), *xyxy[i], cf[i]) for i in order]   # (cls, x1, y1, x2, y2, conf)

        tp, fp, fn, wrong = match(gts, preds, iou_th)
        for g in gts:
            stats["gt"][g[0]] += 1
        for g, _ in tp:
            stats["tp"][g[0]] += 1
        for p in fp:
            stats["fp"][p[0]] += 1
        for g in fn:
            stats["fn"][g[0]] += 1
        # 오분류는 '정답 클래스 입장에선 미탐(FN)' + '예측 클래스 입장에선 오탐(FP)' 으로 동시에 집계
        for g, p in wrong:
            stats["fn"][g[0]] += 1
            stats["fp"][p[0]] += 1
            confusion[(names[g[0]], names[p[0]])] += 1
        errors = len(fp) + len(fn) + len(wrong)
        per_image.append({"image": img_path.name, "gt": len(gts), "tp": len(tp), "fp": len(fp),
                          "fn": len(fn), "wrong": len(wrong), "errors": errors})

        # 오류가 있는 이미지는 시각화해 저장 (최대 max_failure_images 장)
        if errors and n_fail_saved < tc.get("max_failure_images", 50):
            vis = img.copy()
            for g in gts:
                draw_box(vis, g[1:5], f"GT {names[g[0]]}", (0, 200, 0), 2)              # 초록 = 정답
            for p in preds:
                draw_box(vis, p[1:5], f"{names[p[0]]} {p[5]:.2f}", (0, 0, 255), 2)      # 빨강 = 예측
            # 파일명 앞에 오류 종류 태그 (예: FP_WRONG__img001.jpg) → 탐색기에서 종류별 정렬 쉬움
            tag = "_".join(t for t, n in (("FP", len(fp)), ("FN", len(fn)), ("WRONG", len(wrong))) if n)
            cv2.imwrite(str(fail_dir / f"{tag}__{img_path.stem}.jpg"), vis)
            n_fail_saved += 1

    # ---------------- 집계 ----------------
    # ── 4) 집계 ──
    rows = []   # (클래스명, 정답 수, TP, FP, FN, 정밀도, 재현율)
    for i, n in enumerate(names):
        tp, fp, fn = stats["tp"][i], stats["fp"][i], stats["fn"][i]
        p = tp / (tp + fp) if tp + fp else 0.0     # 정밀도 = TP / (TP + FP)
        r = tp / (tp + fn) if tp + fn else 0.0     # 재현율 = TP / (TP + FN)
        rows.append((n, stats["gt"][i], tp, fp, fn, p, r))
    TP, FP, FN = (sum(stats[k].values()) for k in ("tp", "fp", "fn"))
    P = TP / (TP + FP) if TP + FP else 0.0
    R = TP / (TP + FN) if TP + FN else 0.0
    perfect = sum(1 for x in per_image if x["errors"] == 0)   # 오류 0 인 이미지 수
    lat_mean = statistics.mean(latencies)
    # p95 = 정렬 후 95% 위치 값 (가끔 느려지는 최악 상황을 보기 위함)
    lat_p95 = sorted(latencies)[int(0.95 * (len(latencies) - 1))]

    # ── 5) 콘솔 출력 + 리포트 저장 ──
    print(f"\n  {'클래스':<12}{'정답':>6}{'TP':>6}{'FP':>6}{'FN':>6}{'정밀도':>9}{'재현율':>9}")
    for n, g, tp, fp, fn, p, r in rows:
        print(f"  {n:<12}{g:>6}{tp:>6}{fp:>6}{fn:>6}{p:>9.3f}{r:>9.3f}")
    print(f"  {'[전체]':<11}{sum(stats['gt'].values()):>6}{TP:>6}{FP:>6}{FN:>6}{P:>9.3f}{R:>9.3f}")
    print(f"\n  완벽히 맞힌 이미지: {perfect}/{len(per_image)} ({perfect / len(per_image):.1%})")
    if confusion:
        print("  오분류(정답→예측): " + ", ".join(f"{a}→{b} {c}회" for (a, b), c in confusion.most_common()))
    print(f"  지연시간(이 PC, device={device}): 평균 {lat_mean:.1f}ms | p95 {lat_p95:.1f}ms | "
          f"≈ {1000 / lat_mean:.1f} FPS")

    # 오류 개수가 많은 순으로 상위 20장
    worst = sorted((x for x in per_image if x["errors"]), key=lambda x: -x["errors"])[:20]
    report_dir = path_of(cfg, "reports")
    md = [f"# 모델 테스트 리포트 ({split})", "",
          f"- 모델: `{weights}`", f"- 운영 조건: conf={conf}, imgsz={imgsz}, 매칭 IoU={iou_th}",
          f"- 이미지: {len(per_image)} 장, 완벽히 맞힘 {perfect} 장 ({perfect / len(per_image):.1%})",
          f"- 지연시간: 평균 {lat_mean:.1f} ms / p95 {lat_p95:.1f} ms (device={device})", "",
          "| 클래스 | 정답 | TP | FP(오탐) | FN(미탐) | 정밀도 | 재현율 |", "|---|---|---|---|---|---|---|"]
    md += [f"| {n} | {g} | {tp} | {fp} | {fn} | {p:.3f} | {r:.3f} |" for n, g, tp, fp, fn, p, r in rows]
    md += [f"| **전체** | {sum(stats['gt'].values())} | {TP} | {FP} | {FN} | **{P:.3f}** | **{R:.3f}** |",
           "", "## 오분류 (정답 → 예측)", ""]
    md += [f"- {a} → {b}: {c}회" for (a, b), c in confusion.most_common()] or ["- 없음"]
    md += ["", "## 오류가 많은 이미지 Top 20", "", "| 이미지 | 정답 | TP | FP | FN | 오분류 |",
           "|---|---|---|---|---|---|"]
    md += [f"| {x['image']} | {x['gt']} | {x['tp']} | {x['fp']} | {x['fn']} | {x['wrong']} |" for x in worst]
    md += ["", f"실패 이미지(초록=정답, 빨강=예측): `{fail_dir}`",
           "", "> 실패 이미지를 보고 원인을 분류하세요: ① 라벨 오류 → 3단계 수정, "
               "② 데이터 부족 상황(역광/원거리/흐림) → 1단계 추가 수집, ③ conf 임계값 조정"]
    (report_dir / f"test_{split}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (report_dir / f"test_{split}.json").write_text(json.dumps(
        {"split": split, "conf": conf, "imgsz": imgsz, "precision": P, "recall": R,
         "per_class": [dict(zip(("name", "gt", "tp", "fp", "fn", "precision", "recall"), r)) for r in rows],
         "confusion": {f"{a}->{b}": c for (a, b), c in confusion.items()},
         "latency_ms": {"mean": lat_mean, "p95": lat_p95}, "images": per_image},
        indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n  리포트: {report_dir / f'test_{split}.md'}")
    print(f"  실패 이미지: {fail_dir} ({n_fail_saved} 장)")
    print("  다음 단계 → python scripts/08_predict.py --source <이미지/동영상/카메라>")


if __name__ == "__main__":
    main()
