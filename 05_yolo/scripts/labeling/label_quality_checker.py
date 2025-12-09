"""
라벨 품질 검증 스크립트

LabelImg로 생성한 YOLO 라벨의 품질과 일관성을 검증합니다.
"""

import os
from pathlib import Path
from typing import Tuple


class LabelQualityChecker:
    """YOLO 라벨 파일의 품질을 검증하는 클래스"""

    def __init__(self, images_dir: str, labels_dir: str):
        """
        Args:
            images_dir: 이미지 디렉토리 경로
            labels_dir: 라벨 디렉토리 경로
        """
        self.images_dir = Path(images_dir)
        self.labels_dir = Path(labels_dir)

        if not self.images_dir.exists():
            raise ValueError(f"이미지 디렉토리가 존재하지 않습니다: {images_dir}")

        if not self.labels_dir.exists():
            raise ValueError(f"라벨 디렉토리가 존재하지 않습니다: {labels_dir}")

    def get_image_files(self) -> set:
        """이미지 파일 목록을 반환합니다."""
        extensions = ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]
        image_files = set()

        for ext in extensions:
            image_files.update(f.stem for f in self.images_dir.glob(ext))

        return image_files

    def get_label_files(self) -> set:
        """라벨 파일 목록을 반환합니다."""
        return set(f.stem for f in self.labels_dir.glob("*.txt"))

    def check_missing_labels(self, image_files: set, label_files: set) -> set:
        """라벨이 없는 이미지를 찾습니다."""
        missing_labels = image_files - label_files

        if missing_labels:
            print(f"⚠️  라벨이 없는 이미지: {len(missing_labels)}개")
            for img in list(missing_labels)[:5]:
                print(f"   - {img}")
            if len(missing_labels) > 5:
                print(f"   ... 외 {len(missing_labels) - 5}개")

        return missing_labels

    def check_orphan_labels(self, image_files: set, label_files: set) -> set:
        """이미지가 없는 라벨을 찾습니다."""
        orphan_labels = label_files - image_files

        if orphan_labels:
            print(f"⚠️  이미지가 없는 라벨: {len(orphan_labels)}개")
            for lbl in list(orphan_labels)[:5]:
                print(f"   - {lbl}")
            if len(orphan_labels) > 5:
                print(f"   ... 외 {len(orphan_labels) - 5}개")

        return orphan_labels

    def validate_label_format(self) -> int:
        """
        라벨 파일의 형식을 검증합니다.

        Returns:
            오류가 있는 라벨 개수
        """
        invalid_count = 0

        for label_file in self.labels_dir.glob("*.txt"):
            try:
                with open(label_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                    # 빈 파일 체크
                    if not lines:
                        print(f"⚠️  {label_file.name}: 빈 파일")
                        invalid_count += 1
                        continue

                    for line_num, line in enumerate(lines, 1):
                        line = line.strip()

                        # 빈 라인 무시
                        if not line:
                            continue

                        parts = line.split()

                        # 5개 값 확인 (class_id x y w h)
                        if len(parts) != 5:
                            print(
                                f"❌ {label_file.name} 라인 {line_num}: "
                                f"잘못된 형식 (5개 값 필요, {len(parts)}개 발견)"
                            )
                            invalid_count += 1
                            continue

                        try:
                            class_id = int(parts[0])
                            x, y, w, h = map(float, parts[1:])

                            # 클래스 ID 범위 확인
                            if class_id < 0:
                                print(
                                    f"❌ {label_file.name} 라인 {line_num}: "
                                    f"음수 클래스 ID ({class_id})"
                                )
                                invalid_count += 1

                            # 좌표 범위 확인 (0~1)
                            if not (
                                0 <= x <= 1
                                and 0 <= y <= 1
                                and 0 <= w <= 1
                                and 0 <= h <= 1
                            ):
                                print(
                                    f"❌ {label_file.name} 라인 {line_num}: "
                                    f"좌표 범위 오류 (x:{x:.3f}, y:{y:.3f}, w:{w:.3f}, h:{h:.3f})"
                                )
                                invalid_count += 1

                            # 크기 확인 (너무 작거나 큼)
                            if w < 0.001 or h < 0.001:
                                print(
                                    f"⚠️  {label_file.name} 라인 {line_num}: "
                                    f"너무 작은 박스 (w:{w:.4f}, h:{h:.4f})"
                                )

                            if w > 0.99 or h > 0.99:
                                print(
                                    f"⚠️  {label_file.name} 라인 {line_num}: "
                                    f"너무 큰 박스 (w:{w:.4f}, h:{h:.4f})"
                                )

                        except ValueError as e:
                            print(
                                f"❌ {label_file.name} 라인 {line_num}: "
                                f"숫자 변환 오류 ({e})"
                            )
                            invalid_count += 1

            except Exception as e:
                print(f"❌ {label_file.name}: 파일 읽기 오류 ({e})")
                invalid_count += 1

        return invalid_count

    def validate(self) -> Tuple[int, int, int]:
        """
        전체 검증을 수행합니다.

        Returns:
            (missing_labels_count, orphan_labels_count, invalid_format_count)
        """
        print("=" * 60)
        print("YOLO 라벨 품질 검증 시작")
        print("=" * 60)

        # 파일 목록 수집
        print("\n📁 파일 목록 수집 중...")
        image_files = self.get_image_files()
        label_files = self.get_label_files()

        print(f"   이미지 파일: {len(image_files)}개")
        print(f"   라벨 파일: {len(label_files)}개")

        # 1. 라벨이 없는 이미지 확인
        print("\n1️⃣  라벨 누락 확인...")
        missing_labels = self.check_missing_labels(image_files, label_files)

        # 2. 이미지가 없는 라벨 확인
        print("\n2️⃣  고아 라벨 확인...")
        orphan_labels = self.check_orphan_labels(image_files, label_files)

        # 3. 라벨 형식 검증
        print("\n3️⃣  라벨 형식 검증...")
        invalid_count = self.validate_label_format()

        # 결과 요약
        print("\n" + "=" * 60)
        print("검증 결과 요약")
        print("=" * 60)

        total_issues = len(missing_labels) + len(orphan_labels) + invalid_count

        if total_issues == 0:
            print("✅ 모든 라벨 파일이 정상입니다!")
        else:
            print(f"⚠️  총 {total_issues}개의 문제가 발견되었습니다:")
            print(f"   - 라벨 누락: {len(missing_labels)}개")
            print(f"   - 고아 라벨: {len(orphan_labels)}개")
            print(f"   - 형식 오류: {invalid_count}개")

        print("=" * 60)

        return len(missing_labels), len(orphan_labels), invalid_count


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="YOLO 라벨 품질 검증 스크립트")
    parser.add_argument(
        "--images", type=str, required=True, help="이미지 디렉토리 경로"
    )
    parser.add_argument("--labels", type=str, required=True, help="라벨 디렉토리 경로")

    args = parser.parse_args()

    # 검증 실행
    checker = LabelQualityChecker(images_dir=args.images, labels_dir=args.labels)

    checker.validate()


if __name__ == "__main__":
    # 예시 사용법
    # python label_quality_checker.py --images dataset/images --labels dataset/labels

    # 또는 직접 실행
    checker = LabelQualityChecker(
        images_dir="dataset/images", labels_dir="dataset/labels"
    )
    checker.validate()
