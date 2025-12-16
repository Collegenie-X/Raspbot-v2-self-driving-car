#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터셋 분할 스크립트

이미지와 라벨을 train/val/test 세트로 자동 분할합니다.

사용법:
    python dataset_split.py --images dataset/images --labels dataset/labels \\
        --output dataset --train_ratio 0.7 --val_ratio 0.2 --test_ratio 0.1
"""

import os
import shutil
import argparse
import random
from pathlib import Path
from tqdm import tqdm
import yaml


def split_dataset(
    images_dir, labels_dir, output_dir, train_ratio=0.7, val_ratio=0.2, test_ratio=0.1, seed=42
):
    """
    데이터셋을 train/val/test로 분할

    Args:
        images_dir: 이미지 디렉토리
        labels_dir: 라벨 디렉토리
        output_dir: 출력 디렉토리
        train_ratio: 훈련 데이터 비율
        val_ratio: 검증 데이터 비율
        test_ratio: 테스트 데이터 비율
        seed: 랜덤 시드
    """
    # 경로 설정
    images_path = Path(images_dir)
    labels_path = Path(labels_dir)
    output_path = Path(output_dir)

    # 비율 검증
    total_ratio = train_ratio + val_ratio + test_ratio
    if abs(total_ratio - 1.0) > 0.001:
        raise ValueError(f"비율의 합이 1.0이어야 합니다. 현재: {total_ratio}")

    print("=" * 60)
    print("📊 데이터셋 분할 시작")
    print("=" * 60)
    print(f"입력 이미지: {images_dir}")
    print(f"입력 라벨: {labels_dir}")
    print(f"출력 디렉토리: {output_dir}")
    print(f"분할 비율 - Train: {train_ratio}, Val: {val_ratio}, Test: {test_ratio}")
    print(f"랜덤 시드: {seed}")

    # 출력 디렉토리 생성
    for split in ["train", "val", "test"]:
        (output_path / split / "images").mkdir(parents=True, exist_ok=True)
        (output_path / split / "labels").mkdir(parents=True, exist_ok=True)

    # 이미지 파일 목록
    image_files = []
    for ext in [".jpg", ".jpeg", ".png", ".bmp"]:
        image_files.extend(list(images_path.glob(f"*{ext}")))
        image_files.extend(list(images_path.glob(f"*{ext.upper()}")))

    # 라벨이 있는 이미지만 필터링
    valid_pairs = []
    for img_file in image_files:
        label_file = labels_path / f"{img_file.stem}.txt"
        if label_file.exists():
            valid_pairs.append((img_file, label_file))

    total_images = len(valid_pairs)
    print(f"\n✅ 발견된 이미지: {len(image_files)}장")
    print(f"✅ 라벨이 있는 이미지: {total_images}장")

    if total_images == 0:
        raise ValueError("라벨이 있는 이미지를 찾을 수 없습니다.")

    # 셔플
    random.seed(seed)
    random.shuffle(valid_pairs)

    # 분할 인덱스 계산
    train_end = int(total_images * train_ratio)
    val_end = train_end + int(total_images * val_ratio)

    splits = {
        "train": valid_pairs[:train_end],
        "val": valid_pairs[train_end:val_end],
        "test": valid_pairs[val_end:],
    }

    # 파일 복사
    print("\n📁 파일 복사 중...")
    for split_name, pairs in splits.items():
        print(f"\n{split_name.upper()}: {len(pairs)}장")
        for img_file, label_file in tqdm(pairs, desc=f"{split_name} 복사"):
            # 이미지 복사
            dst_img = output_path / split_name / "images" / img_file.name
            shutil.copy2(img_file, dst_img)

            # 라벨 복사
            dst_label = output_path / split_name / "labels" / label_file.name
            shutil.copy2(label_file, dst_label)

    # data.yaml 생성
    create_data_yaml(output_path, splits)

    # 통계 출력
    print("\n" + "=" * 60)
    print("✅ 데이터셋 분할 완료!")
    print("=" * 60)
    print(f"Train: {len(splits['train'])}장 ({len(splits['train'])/total_images*100:.1f}%)")
    print(f"Val:   {len(splits['val'])}장 ({len(splits['val'])/total_images*100:.1f}%)")
    print(f"Test:  {len(splits['test'])}장 ({len(splits['test'])/total_images*100:.1f}%)")
    print(f"Total: {total_images}장")
    print(f"\n💾 data.yaml 생성됨: {output_path / 'data.yaml'}")


def create_data_yaml(output_dir, splits):
    """
    YOLO 훈련용 data.yaml 파일 생성

    Args:
        output_dir: 출력 디렉토리
        splits: 분할된 데이터 정보
    """
    output_path = Path(output_dir)

    # 클래스 정보 수집 (첫 번째 라벨 파일에서)
    classes = set()
    for split_name, pairs in splits.items():
        if pairs:
            # 첫 번째 라벨 파일 읽기
            _, label_file = pairs[0]
            with open(label_file, "r") as f:
                for line in f:
                    class_id = int(line.strip().split()[0])
                    classes.add(class_id)

    classes = sorted(list(classes))
    num_classes = len(classes)

    # classes.txt에서 클래스 이름 읽기 (있는 경우)
    classes_file = output_path.parent / "classes.txt"
    if classes_file.exists():
        with open(classes_file, "r") as f:
            class_names = [line.strip() for line in f.readlines()]
    else:
        class_names = [f"class_{i}" for i in range(num_classes)]

    # data.yaml 생성
    data_yaml = {
        "path": str(output_path.absolute()),
        "train": "train/images",
        "val": "val/images",
        "test": "test/images",
        "nc": num_classes,
        "names": class_names[:num_classes],
    }

    yaml_path = output_path / "data.yaml"
    with open(yaml_path, "w") as f:
        yaml.dump(data_yaml, f, default_flow_style=False, sort_keys=False)

    print(f"\n📄 data.yaml 내용:")
    print(yaml.dump(data_yaml, default_flow_style=False, sort_keys=False))


def verify_split(output_dir):
    """
    분할 결과 검증

    Args:
        output_dir: 출력 디렉토리
    """
    output_path = Path(output_dir)

    print("\n" + "=" * 60)
    print("🔍 데이터셋 검증")
    print("=" * 60)

    for split in ["train", "val", "test"]:
        images_dir = output_path / split / "images"
        labels_dir = output_path / split / "labels"

        if not images_dir.exists() or not labels_dir.exists():
            print(f"❌ {split}: 디렉토리가 존재하지 않습니다.")
            continue

        image_files = list(images_dir.glob("*"))
        label_files = list(labels_dir.glob("*.txt"))

        print(f"\n{split.upper()}:")
        print(f"  이미지: {len(image_files)}장")
        print(f"  라벨: {len(label_files)}개")

        # 이미지-라벨 매칭 확인
        unmatched = 0
        for img_file in image_files:
            label_file = labels_dir / f"{img_file.stem}.txt"
            if not label_file.exists():
                unmatched += 1

        if unmatched > 0:
            print(f"  ⚠️  라벨 없는 이미지: {unmatched}장")
        else:
            print(f"  ✅ 모든 이미지에 라벨 있음")


def main():
    parser = argparse.ArgumentParser(description="YOLOv4 데이터셋 분할")
    parser.add_argument(
        "--images", type=str, required=True, help="이미지 디렉토리"
    )
    parser.add_argument(
        "--labels", type=str, required=True, help="라벨 디렉토리"
    )
    parser.add_argument(
        "--output", type=str, required=True, help="출력 디렉토리"
    )
    parser.add_argument(
        "--train_ratio", type=float, default=0.7, help="훈련 데이터 비율 (기본값: 0.7)"
    )
    parser.add_argument(
        "--val_ratio", type=float, default=0.2, help="검증 데이터 비율 (기본값: 0.2)"
    )
    parser.add_argument(
        "--test_ratio", type=float, default=0.1, help="테스트 데이터 비율 (기본값: 0.1)"
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="랜덤 시드 (기본값: 42)"
    )
    parser.add_argument(
        "--verify", action="store_true", help="분할 후 검증 수행"
    )

    args = parser.parse_args()

    # 데이터셋 분할
    split_dataset(
        images_dir=args.images,
        labels_dir=args.labels,
        output_dir=args.output,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed,
    )

    # 검증
    if args.verify:
        verify_split(args.output)


if __name__ == "__main__":
    main()

