"""
데이터셋 분할 스크립트

이미지와 라벨을 train/val/test로 분할합니다.
"""

import os
import shutil
import random
from pathlib import Path
from typing import Tuple, List
import argparse


class DatasetSplitter:
    """이미지와 라벨을 train/val/test로 분할하는 클래스"""

    def __init__(
        self,
        source_images_dir: str,
        source_labels_dir: str,
        output_dir: str,
        train_ratio: float = 0.7,
        val_ratio: float = 0.2,
        test_ratio: float = 0.1,
        random_seed: int = 42,
    ):
        """
        Args:
            source_images_dir: 원본 이미지 디렉토리
            source_labels_dir: 원본 라벨 디렉토리
            output_dir: 출력 디렉토리
            train_ratio: 훈련 데이터 비율
            val_ratio: 검증 데이터 비율
            test_ratio: 테스트 데이터 비율
            random_seed: 랜덤 시드 (재현성)
        """
        self.source_images_dir = Path(source_images_dir)
        self.source_labels_dir = Path(source_labels_dir)
        self.output_dir = Path(output_dir)

        # 비율 검증
        total_ratio = train_ratio + val_ratio + test_ratio
        if not abs(total_ratio - 1.0) < 0.001:
            raise ValueError(f"비율의 합이 1.0이 되어야 합니다 (현재: {total_ratio})")

        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio

        # 랜덤 시드 설정
        random.seed(random_seed)

        # 디렉토리 존재 확인
        if not self.source_images_dir.exists():
            raise ValueError(f"이미지 디렉토리가 없습니다: {source_images_dir}")

        if not self.source_labels_dir.exists():
            raise ValueError(f"라벨 디렉토리가 없습니다: {source_labels_dir}")

    def create_directory_structure(self):
        """출력 디렉토리 구조 생성"""
        print("📁 디렉토리 구조 생성 중...")

        for split in ["train", "val", "test"]:
            images_dir = self.output_dir / split / "images"
            labels_dir = self.output_dir / split / "labels"

            images_dir.mkdir(parents=True, exist_ok=True)
            labels_dir.mkdir(parents=True, exist_ok=True)

            print(f"   ✓ {split}/images")
            print(f"   ✓ {split}/labels")

        print("✅ 디렉토리 구조 생성 완료\n")

    def get_paired_files(self) -> List[Tuple[Path, Path]]:
        """
        이미지와 라벨 파일 쌍을 찾습니다.

        Returns:
            (이미지_경로, 라벨_경로) 튜플 리스트
        """
        print("🔍 이미지-라벨 쌍 검색 중...")

        paired_files = []
        missing_labels = []

        # 지원하는 이미지 확장자
        image_extensions = ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]

        for ext in image_extensions:
            for img_file in self.source_images_dir.glob(ext):
                label_file = self.source_labels_dir / f"{img_file.stem}.txt"

                if label_file.exists():
                    paired_files.append((img_file, label_file))
                else:
                    missing_labels.append(img_file.name)

        # 결과 출력
        print(f"   발견된 이미지-라벨 쌍: {len(paired_files)}개")

        if missing_labels:
            print(f"   ⚠️  라벨이 없는 이미지: {len(missing_labels)}개")
            for img in missing_labels[:3]:
                print(f"      - {img}")
            if len(missing_labels) > 3:
                print(f"      ... 외 {len(missing_labels) - 3}개")

        if not paired_files:
            raise ValueError("처리할 이미지-라벨 쌍이 없습니다")

        print("✅ 파일 검색 완료\n")
        return paired_files

    def split_dataset(self, paired_files: List[Tuple[Path, Path]]) -> dict:
        """
        데이터셋을 train/val/test로 분할합니다.

        Args:
            paired_files: 이미지-라벨 파일 쌍 리스트

        Returns:
            분할된 파일 딕셔너리
        """
        print("✂️  데이터셋 분할 중...")

        # 랜덤 셔플
        random.shuffle(paired_files)

        total = len(paired_files)
        train_end = int(total * self.train_ratio)
        val_end = train_end + int(total * self.val_ratio)

        splits = {
            "train": paired_files[:train_end],
            "val": paired_files[train_end:val_end],
            "test": paired_files[val_end:],
        }

        # 분할 결과 출력
        print(f"   총 데이터: {total}개")
        for split_name, files in splits.items():
            count = len(files)
            percentage = (count / total) * 100
            print(f"   - {split_name:5s}: {count:4d}개 ({percentage:5.1f}%)")

        print("✅ 분할 완료\n")
        return splits

    def copy_files(self, splits: dict):
        """파일을 각 분할 디렉토리로 복사합니다."""
        print("📋 파일 복사 중...")

        for split_name, file_pairs in splits.items():
            print(f"\n   {split_name} 복사 중...")

            for idx, (img_path, label_path) in enumerate(file_pairs, 1):
                # 이미지 복사
                dst_img = self.output_dir / split_name / "images" / img_path.name
                shutil.copy2(img_path, dst_img)

                # 라벨 복사
                dst_label = self.output_dir / split_name / "labels" / label_path.name
                shutil.copy2(label_path, dst_label)

                # 진행률 표시
                if idx % 10 == 0 or idx == len(file_pairs):
                    print(f"      진행: {idx}/{len(file_pairs)}", end="\r")

            print(f"   ✅ {split_name}: {len(file_pairs)}개 복사 완료")

        print("\n✅ 모든 파일 복사 완료\n")

    def create_summary_file(self, splits: dict):
        """분할 요약 파일을 생성합니다."""
        summary_path = self.output_dir / "split_summary.txt"

        with open(summary_path, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("데이터셋 분할 요약\n")
            f.write("=" * 60 + "\n\n")

            f.write(f"원본 디렉토리:\n")
            f.write(f"  이미지: {self.source_images_dir}\n")
            f.write(f"  라벨:   {self.source_labels_dir}\n\n")

            f.write(f"출력 디렉토리: {self.output_dir}\n\n")

            f.write(f"분할 비율:\n")
            f.write(f"  Train: {self.train_ratio * 100:.1f}%\n")
            f.write(f"  Val:   {self.val_ratio * 100:.1f}%\n")
            f.write(f"  Test:  {self.test_ratio * 100:.1f}%\n\n")

            total = sum(len(files) for files in splits.values())
            f.write(f"분할 결과:\n")
            for split_name, files in splits.items():
                count = len(files)
                percentage = (count / total) * 100
                f.write(f"  {split_name:5s}: {count:4d}개 ({percentage:5.1f}%)\n")

            f.write(f"\n총 데이터: {total}개\n")

        print(f"📄 요약 파일 생성: {summary_path}\n")

    def execute(self):
        """전체 분할 프로세스 실행"""
        print("\n" + "=" * 60)
        print("데이터셋 분할 시작")
        print("=" * 60 + "\n")

        try:
            # 1. 디렉토리 구조 생성
            self.create_directory_structure()

            # 2. 이미지-라벨 쌍 찾기
            paired_files = self.get_paired_files()

            # 3. 데이터셋 분할
            splits = self.split_dataset(paired_files)

            # 4. 파일 복사
            self.copy_files(splits)

            # 5. 요약 파일 생성
            self.create_summary_file(splits)

            # 완료 메시지
            print("=" * 60)
            print("✅ 데이터셋 분할이 성공적으로 완료되었습니다!")
            print("=" * 60)
            print(f"\n출력 디렉토리: {self.output_dir.absolute()}")
            print("\n다음 단계:")
            print("  1. data.yaml 파일 생성")
            print("  2. YOLO 모델 훈련 시작")
            print("=" * 60 + "\n")

        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            raise


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="YOLO 데이터셋을 train/val/test로 분할"
    )
    parser.add_argument(
        "--images", type=str, required=True, help="원본 이미지 디렉토리"
    )
    parser.add_argument("--labels", type=str, required=True, help="원본 라벨 디렉토리")
    parser.add_argument("--output", type=str, required=True, help="출력 디렉토리")
    parser.add_argument(
        "--train-ratio", type=float, default=0.7, help="훈련 데이터 비율 (기본값: 0.7)"
    )
    parser.add_argument(
        "--val-ratio", type=float, default=0.2, help="검증 데이터 비율 (기본값: 0.2)"
    )
    parser.add_argument(
        "--test-ratio", type=float, default=0.1, help="테스트 데이터 비율 (기본값: 0.1)"
    )
    parser.add_argument("--seed", type=int, default=42, help="랜덤 시드 (기본값: 42)")

    args = parser.parse_args()

    # 분할 실행
    splitter = DatasetSplitter(
        source_images_dir=args.images,
        source_labels_dir=args.labels,
        output_dir=args.output,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        random_seed=args.seed,
    )

    splitter.execute()


if __name__ == "__main__":
    # 예시 사용법
    # python dataset_splitter.py \
    #   --images raw_dataset/images \
    #   --labels raw_dataset/labels \
    #   --output yolo_dataset \
    #   --train-ratio 0.7 \
    #   --val-ratio 0.2 \
    #   --test-ratio 0.1

    # 또는 직접 실행
    splitter = DatasetSplitter(
        source_images_dir="raw_dataset/images",
        source_labels_dir="raw_dataset/labels",
        output_dir="yolo_dataset",
        train_ratio=0.7,
        val_ratio=0.2,
        test_ratio=0.1,
    )
    splitter.execute()
