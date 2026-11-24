"""
[4단계] 데이터셋 분할 + data.yaml 생성

라벨이 완료된 이미지(라벨 txt 가 있는 이미지)만 train / val / test 로 나눕니다.

  train (70%) : 모델이 학습하는 데이터
  val   (20%) : 학습 중 성능 확인 · best.pt 선택 기준
  test  (10%) : 학습/튜닝에 전혀 쓰지 않고 '최종 시험'에만 사용

group_by_prefix=true 이면 같은 동영상/촬영 세션(파일명 '<그룹>_<번호>')에서 나온 이미지를
같은 split 에 넣습니다. 거의 같은 연속 프레임이 train 과 test 에 나뉘어 들어가면
테스트 점수가 실제보다 부풀려지기 때문입니다(데이터 누수).
그룹이 너무 적으면(그룹 < 10) 자동으로 '클래스 기준 층화 분할'로 전환합니다.

입력:
  data/labeled/images/*.jpg  +  data/labeled/labels/*.txt   (1~3단계 결과)

출력:
  datasets/raspbot/
    images/{train,val,test}/*.jpg
    labels/{train,val,test}/*.txt
    data.yaml            ← 학습에 사용하는 설정
    split_summary.md

처리 흐름 (main):
  1) 설정 로드 — split 비율(합=1 검사), 난수 seed
  2) 라벨이 있는 이미지만 수집 (라벨 없는 이미지 = 미검토 → 제외)
  3) 분할 방식 결정 — 그룹 ≥ 10 이면 그룹 분할, 아니면 클래스 층화 분할
  4) 이전 분할 결과 폴더/캐시 삭제
  5) split 별로 이미지·라벨 복사(또는 심볼릭 링크) + 클래스별 박스 수 집계
  6) data.yaml 작성 (Ultralytics 학습 설정)
  7) 콘솔 요약 출력 + split_summary.md 저장

사용 예:
  python scripts/04_split_dataset.py
  python scripts/04_split_dataset.py --no-group --link
"""
from __future__ import annotations

import argparse
import os
import random
import shutil
import sys
from collections import Counter, defaultdict

import yaml

from common import (add_config_arg, banner, data_yaml_path, label_path_for, labeled_dirs,
                    list_images, load_config, path_of, read_yolo_labels)

SPLITS = ("train", "val", "test")   # 분할 이름 (순서대로 출력·통계에 사용)


def group_key(stem: str) -> str:
    """파일명(확장자 제외)에서 그룹 이름을 추출.

    1단계에서 '<그룹>_<번호>' 형식으로 저장했으므로 마지막 '_' 앞부분이 그룹입니다.
    예) 'drive01_000120' → 'drive01'   ('_' 가 없으면 파일명 전체가 그룹)
    """
    return stem.rsplit("_", 1)[0] if "_" in stem else stem


def stratified_split(items, ratios, rng, primary_cls):
    """이미지를 '가장 희귀한 클래스' 기준으로 묶어 각 묶음을 비율대로 나눔.

    Args:
        items: (이미지 경로, 라벨 경로, 박스 목록) 튜플 리스트
        ratios: {"train": 0.7, "val": 0.2, "test": 0.1}
        rng: 재현 가능한 random.Random 객체
        primary_cls: 이미지 → 대표 클래스(가장 희귀한 클래스, 없으면 "bg") 함수
    Returns:
        {"train": [...], "val": [...], "test": [...]}
    """
    # 대표 클래스별로 바구니(bucket)에 나눠 담기 → 각 클래스가 모든 split 에 고르게 들어감
    buckets = defaultdict(list)
    for it in items:
        buckets[primary_cls(it)].append(it)
    out = {s: [] for s in SPLITS}
    # 바구니 순서를 정렬해 고정 → 같은 seed 면 항상 같은 결과 (클래스 id 와 "bg" 가 섞여 있어 str 로 비교)
    for _, group in sorted(buckets.items(), key=lambda kv: str(kv[0])):
        rng.shuffle(group)
        n = len(group)
        n_val = round(n * ratios["val"])
        n_test = round(n * ratios["test"])
        if n >= 3:   # 작은 클래스라도 val/test 에 최소 1장씩
            n_val, n_test = max(1, n_val), max(1, n_test) if ratios["test"] > 0 else 0
        # 섞인 목록을 앞에서부터 val → test → 나머지는 train 으로 잘라 배정
        out["val"] += group[:n_val]
        out["test"] += group[n_val:n_val + n_test]
        out["train"] += group[n_val + n_test:]
    return out


def group_split(items, ratios, rng):
    """같은 그룹(동영상/촬영 세션)의 이미지를 통째로 하나의 split 에 배정.

    연속 프레임이 train/test 에 갈라져 들어가는 '데이터 누수'를 막습니다.
    배정은 그리디: 큰 그룹부터, 목표 장수 대비 가장 부족한 split 에 넣습니다.
    """
    groups = defaultdict(list)
    for it in items:
        groups[group_key(it[0].stem)].append(it)
    keys = list(groups)
    rng.shuffle(keys)                             # 같은 크기 그룹끼리의 순서는 seed 로 무작위
    keys.sort(key=lambda k: -len(groups[k]))      # 큰 그룹부터 배치 → 비율 맞추기 쉬움 (sort 는 안정 정렬)
    total = len(items)
    out = {s: [] for s in SPLITS}
    for k in keys:
        # 목표 대비 가장 많이 부족한 split 에 그룹 통째로 배정
        # deficit = (목표 장수) - (현재 장수). 비율 0 인 split 은 후보에서 제외
        deficit = {s: ratios[s] * total - len(out[s]) for s in SPLITS if ratios[s] > 0}
        out[max(deficit, key=deficit.get)] += groups[k]
    return out


def main():
    """4단계 실행: 라벨 완료 이미지를 train/val/test 로 나누고 data.yaml 을 만든다."""
    ap = add_config_arg(argparse.ArgumentParser(description=__doc__,
                                                formatter_class=argparse.RawDescriptionHelpFormatter))
    ap.add_argument("--no-group", action="store_true", help="그룹 분할 끄기 (층화 분할만)")
    ap.add_argument("--link", action="store_true", help="복사 대신 심볼릭 링크 (디스크 절약)")
    args = ap.parse_args()

    # ── 1) 설정 로드 ──
    cfg = load_config(args.config)
    names = cfg["classes"]
    sc = cfg.get("split", {})
    # config 에 값이 없으면 기본값 0.7 / 0.2 / 0.1 사용
    ratios = {s: float(sc.get(s, d)) for s, d in zip(SPLITS, (0.7, 0.2, 0.1))}
    if abs(sum(ratios.values()) - 1) > 1e-6:     # 부동소수 오차를 감안해 합이 1 인지 확인
        sys.exit(f"[ERROR] split 비율 합이 1 이 아닙니다: {ratios}")
    rng = random.Random(sc.get("seed", 42))      # seed 고정 → 다시 실행해도 같은 분할

    images_dir, labels_dir = labeled_dirs(cfg)
    out_dir = path_of(cfg, "dataset")
    banner("4단계", "데이터셋 분할 (train / val / test) + data.yaml")

    # ── 2) 라벨이 있는 이미지만 수집 ──
    items = []   # (이미지 경로, 라벨 경로, 박스 목록)
    for img in list_images(images_dir):
        txt = label_path_for(img, images_dir, labels_dir)
        if txt.exists():                         # 빈 txt(배경)도 '검토 완료'로 포함
            items.append((img, txt, read_yolo_labels(txt)))
    skipped = len(list_images(images_dir)) - len(items)   # 라벨 없는(미검토) 이미지 수
    if len(items) < 10:
        sys.exit(f"[ERROR] 라벨 완료 이미지가 {len(items)} 장뿐입니다. (최소 수십~수백 장 필요)")

    # 전체 데이터에서 클래스별 박스 수 — '희귀한 클래스' 판단 기준
    inst_total = Counter(b[0] for it in items for b in it[2])

    def primary_cls(it):
        """이미지의 대표 클래스 = 그 이미지에 있는 클래스 중 전체에서 가장 희귀한 것 (박스 없으면 "bg")."""
        cls = {b[0] for b in it[2]}
        return min(cls, key=lambda c: inst_total[c]) if cls else "bg"

    # ── 3) 분할 방식 결정 ──
    n_groups = len({group_key(it[0].stem) for it in items})
    # 그룹이 10개 미만이면 그룹 단위로는 비율을 맞추기 어려워 층화 분할로 대체
    use_group = sc.get("group_by_prefix", True) and not args.no_group and n_groups >= 10
    if sc.get("group_by_prefix", True) and not args.no_group and not use_group:
        print(f"  [INFO] 그룹이 {n_groups} 개뿐이라 층화 분할로 전환합니다.")
    split = group_split(items, ratios, rng) if use_group else stratified_split(items, ratios, rng, primary_cls)

    # ── 4) 출력 폴더 초기화 (이전 분할 결과 삭제) ──
    for sub in ("images", "labels"):
        if (out_dir / sub).exists():
            shutil.rmtree(out_dir / sub)
    # Ultralytics 가 만든 라벨 캐시 — 남아 있으면 예전 분할 정보를 재사용할 수 있어 삭제
    for f in out_dir.glob("labels/*.cache"):
        f.unlink()

    # ── 5) split 별 파일 복사 + 클래스별 박스 수 집계 ──
    stats = {s: Counter() for s in SPLITS}       # stats[split][class_id] = 박스 수
    for s, its in split.items():
        (out_dir / "images" / s).mkdir(parents=True, exist_ok=True)
        (out_dir / "labels" / s).mkdir(parents=True, exist_ok=True)
        for img, txt, boxes in its:
            dst_img = out_dir / "images" / s / img.name
            # Ultralytics 규칙: images/<split>/a.jpg ↔ labels/<split>/a.txt (같은 이름)
            dst_txt = out_dir / "labels" / s / (img.stem + ".txt")
            if args.link:
                os.symlink(img.resolve(), dst_img)   # 원본을 가리키는 링크만 생성 (디스크 절약)
            else:
                shutil.copy2(img, dst_img)
            shutil.copy2(txt, dst_txt)               # 라벨은 작으므로 항상 복사
            for b in boxes:
                stats[s][b[0]] += 1
        # 어떤 파일이 어느 split 에 들어갔는지 기록 (재현/추적용)
        (out_dir / f"{s}.txt").write_text("\n".join(str(i[0].name) for i in its) + "\n", encoding="utf-8")

    # ── 6) data.yaml 작성 (5~7단계가 사용하는 학습 설정) ──
    data = {
        "path": str(out_dir.resolve()),    # 데이터셋 루트 (절대경로)
        "train": "images/train",           # 아래는 path 기준 상대경로
        "val": "images/val",
        "test": "images/test",
        "nc": len(names),                  # 클래스 수
        "names": {i: n for i, n in enumerate(names)},   # class_id → 이름
    }
    with open(data_yaml_path(cfg), "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)

    # ── 7) 요약 출력 + split_summary.md 저장 ──
    header = f"  {'클래스':<12}" + "".join(f"{s:>8}" for s in SPLITS)
    lines = [header]
    for i, n in enumerate(names):
        lines.append(f"  {i}:{n:<10}" + "".join(f"{stats[s][i]:>8}" for s in SPLITS))
    lines.append(f"  {'이미지 수':<11}" + "".join(f"{len(split[s]):>8}" for s in SPLITS))
    print(f"  분할 방식: {'그룹(동영상/세션) 단위' if use_group else '클래스 층화'} | 미라벨 제외: {skipped} 장")
    print("\n".join(lines))
    # val/test 에 한 번도 등장하지 않는 클래스가 있으면 그 클래스는 평가할 수 없음 → 경고
    for s in ("val", "test"):
        missing = [names[i] for i in range(len(names)) if stats[s][i] == 0 and ratios[s] > 0]
        if missing:
            print(f"  ⚠ {s} 에 없는 클래스: {missing} → 해당 클래스 데이터를 더 모으거나 --no-group 사용")

    md = ["# 데이터셋 분할 요약", "", f"- 분할 방식: {'그룹' if use_group else '층화'}",
          f"- seed: {sc.get('seed', 42)}", "", "| 클래스 | train | val | test |", "|---|---|---|---|"]
    md += [f"| {n} | " + " | ".join(str(stats[s][i]) for s in SPLITS) + " |" for i, n in enumerate(names)]
    md += ["| **이미지 수** | " + " | ".join(str(len(split[s])) for s in SPLITS) + " |"]
    (out_dir / "split_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"\n  data.yaml: {data_yaml_path(cfg)}")
    print("  다음 단계 → python scripts/05_train.py")


if __name__ == "__main__":
    main()
