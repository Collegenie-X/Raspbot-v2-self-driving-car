"""
data.yaml 생성 스크립트

YOLO 훈련에 필요한 data.yaml 설정 파일을 생성합니다.
"""

import yaml
from pathlib import Path
import argparse


class DataYamlCreator:
    """YOLO data.yaml 파일을 생성하는 클래스"""

    def __init__(
        self, dataset_path: str, classes: list, output_filename: str = "data.yaml"
    ):
        """
        Args:
            dataset_path: 데이터셋 루트 경로
            classes: 클래스 이름 리스트
            output_filename: 출력 파일명
        """
        self.dataset_path = Path(dataset_path)
        self.classes = classes
        self.output_filename = output_filename

        if not self.dataset_path.exists():
            raise ValueError(f"데이터셋 경로가 존재하지 않습니다: {dataset_path}")

        if not classes:
            raise ValueError("클래스 리스트가 비어있습니다")

    def validate_directory_structure(self) -> bool:
        """
        디렉토리 구조를 검증합니다.

        Returns:
            검증 성공 여부
        """
        print("🔍 디렉토리 구조 검증 중...")

        required_dirs = ["train/images", "train/labels", "val/images", "val/labels"]

        optional_dirs = ["test/images", "test/labels"]

        all_valid = True

        for dir_path in required_dirs:
            full_path = self.dataset_path / dir_path
            if full_path.exists():
                file_count = len(list(full_path.glob("*")))
                print(f"   ✓ {dir_path:20s} ({file_count}개 파일)")
            else:
                print(f"   ❌ {dir_path:20s} (없음)")
                all_valid = False

        for dir_path in optional_dirs:
            full_path = self.dataset_path / dir_path
            if full_path.exists():
                file_count = len(list(full_path.glob("*")))
                print(f"   ✓ {dir_path:20s} ({file_count}개 파일) [선택사항]")

        if all_valid:
            print("✅ 디렉토리 구조 검증 완료\n")
        else:
            print("❌ 필수 디렉토리가 누락되었습니다\n")

        return all_valid

    def create_yaml(self, use_absolute_path: bool = True):
        """
        data.yaml 파일을 생성합니다.

        Args:
            use_absolute_path: 절대 경로 사용 여부
        """
        print("📝 data.yaml 파일 생성 중...")

        # 경로 설정
        if use_absolute_path:
            dataset_path_str = str(self.dataset_path.absolute())
        else:
            dataset_path_str = str(self.dataset_path)

        # data.yaml 구성
        data_config = {
            "path": dataset_path_str,
            "train": "train/images",
            "val": "val/images",
            "nc": len(self.classes),
            "names": self.classes,
        }

        # test 디렉토리가 있으면 추가
        test_dir = self.dataset_path / "test" / "images"
        if test_dir.exists():
            data_config["test"] = "test/images"

        # 파일 저장
        output_path = self.dataset_path / self.output_filename

        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(
                data_config,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

        print(f"✅ 파일 생성 완료: {output_path}\n")

        return output_path

    def display_summary(self, yaml_path: Path):
        """생성된 yaml 파일의 요약을 출력합니다."""
        print("=" * 60)
        print("data.yaml 요약")
        print("=" * 60)

        with open(yaml_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        print(f"\n📍 데이터셋 경로: {config['path']}")
        print(f"\n📂 분할 디렉토리:")
        print(f"   - Train: {config['train']}")
        print(f"   - Val:   {config['val']}")
        if "test" in config:
            print(f"   - Test:  {config['test']}")

        print(f"\n🏷️  클래스 정보:")
        print(f"   - 클래스 개수: {config['nc']}")
        print(f"   - 클래스 목록:")
        for i, name in enumerate(config["names"]):
            print(f"      [{i}] {name}")

        print("\n" + "=" * 60)
        print("다음 단계:")
        print("  1. YOLO 모델 훈련 명령어:")
        print(
            f"     yolo task=detect mode=train model=yolo11n.pt data={yaml_path.name} epochs=100"
        )
        print("\n  2. 또는 Python 스크립트 사용:")
        print(f"     python train_yolo11.py --data {yaml_path}")
        print("=" * 60 + "\n")

    def execute(self, use_absolute_path: bool = True, validate: bool = True):
        """
        전체 프로세스를 실행합니다.

        Args:
            use_absolute_path: 절대 경로 사용 여부
            validate: 디렉토리 구조 검증 여부
        """
        print("\n" + "=" * 60)
        print("data.yaml 생성 시작")
        print("=" * 60 + "\n")

        try:
            # 디렉토리 구조 검증
            if validate:
                if not self.validate_directory_structure():
                    print("⚠️  경고: 디렉토리 구조에 문제가 있지만 계속 진행합니다...")

            # yaml 파일 생성
            yaml_path = self.create_yaml(use_absolute_path)

            # 요약 출력
            self.display_summary(yaml_path)

            print("✅ data.yaml 생성이 완료되었습니다!\n")

        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            raise


def load_classes_from_file(file_path: str) -> list:
    """
    파일에서 클래스 목록을 로드합니다.

    Args:
        file_path: 클래스 파일 경로 (한 줄에 하나씩)

    Returns:
        클래스 이름 리스트
    """
    with open(file_path, "r", encoding="utf-8") as f:
        classes = [line.strip() for line in f if line.strip()]

    return classes


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="YOLO data.yaml 파일 생성")
    parser.add_argument(
        "--dataset", type=str, required=True, help="데이터셋 루트 디렉토리"
    )
    parser.add_argument(
        "--classes", type=str, nargs="+", help="클래스 이름 리스트 (공백으로 구분)"
    )
    parser.add_argument(
        "--classes-file", type=str, help="클래스 이름이 저장된 파일 경로"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data.yaml",
        help="출력 파일명 (기본값: data.yaml)",
    )
    parser.add_argument(
        "--relative-path",
        action="store_true",
        help="상대 경로 사용 (기본값: 절대 경로)",
    )
    parser.add_argument(
        "--no-validate", action="store_true", help="디렉토리 구조 검증 생략"
    )

    args = parser.parse_args()

    # 클래스 로드
    if args.classes_file:
        classes = load_classes_from_file(args.classes_file)
    elif args.classes:
        classes = args.classes
    else:
        raise ValueError("--classes 또는 --classes-file 중 하나를 지정해야 합니다")

    # yaml 생성
    creator = DataYamlCreator(
        dataset_path=args.dataset, classes=classes, output_filename=args.output
    )

    creator.execute(
        use_absolute_path=not args.relative_path, validate=not args.no_validate
    )


if __name__ == "__main__":
    # 예시 사용법 1: 직접 클래스 지정
    # python create_data_yaml.py \
    #   --dataset yolo_dataset \
    #   --classes stop_sign traffic_light pedestrian lane_marker obstacle

    # 예시 사용법 2: 파일에서 클래스 로드
    # python create_data_yaml.py \
    #   --dataset yolo_dataset \
    #   --classes-file classes.txt

    # 또는 직접 실행
    classes = ["stop_sign", "traffic_light", "pedestrian", "lane_marker", "obstacle"]

    creator = DataYamlCreator(dataset_path="yolo_dataset", classes=classes)
    creator.execute()
