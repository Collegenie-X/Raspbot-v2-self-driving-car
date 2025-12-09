"""
YOLO11 모델 훈련 스크립트

전이 학습을 통해 커스텀 데이터셋으로 YOLO11 모델을 훈련합니다.
"""

from ultralytics import YOLO
import torch
from pathlib import Path
import argparse
from datetime import datetime


class YOLO11Trainer:
    """YOLO11 모델 훈련을 관리하는 클래스"""

    def __init__(
        self,
        model_size: str = "n",
        data_yaml: str = "data.yaml",
        project_name: str = "yolo11_training",
        experiment_name: str = None,
    ):
        """
        Args:
            model_size: 모델 크기 ('n', 's', 'm', 'l', 'x')
            data_yaml: 데이터 설정 파일 경로
            project_name: 프로젝트 이름
            experiment_name: 실험 이름 (None이면 타임스탬프 사용)
        """
        # 모델 크기 검증
        valid_sizes = ["n", "s", "m", "l", "x"]
        if model_size not in valid_sizes:
            raise ValueError(f"모델 크기는 {valid_sizes} 중 하나여야 합니다")

        self.model_size = model_size
        self.data_yaml = data_yaml
        self.project_name = project_name

        # 실험 이름 설정
        if experiment_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.experiment_name = f"exp_{timestamp}"
        else:
            self.experiment_name = experiment_name

        # 데이터 파일 존재 확인
        if not Path(data_yaml).exists():
            raise FileNotFoundError(f"데이터 파일이 없습니다: {data_yaml}")

        # 모델 초기화
        model_path = f"yolo11{model_size}.pt"
        print(f"📥 모델 로딩: {model_path}")
        self.model = YOLO(model_path)

        # 장치 설정
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🔧 훈련 장치: {self.device}")

        if self.device == "cuda":
            print(f"   GPU: {torch.cuda.get_device_name(0)}")
            print(
                f"   메모리: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB"
            )

    def train(
        self,
        epochs: int = 100,
        batch: int = 16,
        imgsz: int = 640,
        patience: int = 50,
        save_period: int = 10,
        resume: bool = False,
        optimizer: str = "auto",
        lr0: float = 0.01,
        lrf: float = 0.01,
        momentum: float = 0.937,
        weight_decay: float = 0.0005,
        warmup_epochs: float = 3.0,
        augment: bool = True,
        verbose: bool = True,
    ):
        """
        모델을 훈련합니다.

        Args:
            epochs: 훈련 에포크 수
            batch: 배치 크기
            imgsz: 이미지 크기
            patience: 조기 종료 인내 (에포크)
            save_period: 체크포인트 저장 주기
            resume: 이전 훈련 재개 여부
            optimizer: 최적화 알고리즘 ('SGD', 'Adam', 'AdamW', 'auto')
            lr0: 초기 학습률
            lrf: 최종 학습률 비율
            momentum: SGD 모멘텀
            weight_decay: 가중치 감쇠
            warmup_epochs: 워밍업 에포크
            augment: 데이터 증강 사용 여부
            verbose: 상세 출력 여부
        """
        print("\n" + "=" * 80)
        print("YOLO11 훈련 시작")
        print("=" * 80)
        print(f"모델: yolo11{self.model_size}")
        print(f"데이터: {self.data_yaml}")
        print(f"에포크: {epochs}")
        print(f"배치 크기: {batch}")
        print(f"이미지 크기: {imgsz}")
        print(f"장치: {self.device}")
        print(f"프로젝트: {self.project_name}/{self.experiment_name}")
        print("=" * 80 + "\n")

        try:
            # 훈련 실행
            results = self.model.train(
                data=self.data_yaml,
                epochs=epochs,
                batch=batch,
                imgsz=imgsz,
                device=self.device,
                patience=patience,
                save_period=save_period,
                project=self.project_name,
                name=self.experiment_name,
                resume=resume,
                exist_ok=True,
                # 데이터 증강 설정
                augment=augment,
                hsv_h=0.015,  # 색조 증강
                hsv_s=0.7,  # 채도 증강
                hsv_v=0.4,  # 명도 증강
                degrees=0.0,  # 회전 증강
                translate=0.1,  # 이동 증강
                scale=0.5,  # 크기 증강
                shear=0.0,  # 전단 증강
                perspective=0.0,  # 원근 증강
                flipud=0.0,  # 상하 반전
                fliplr=0.5,  # 좌우 반전
                mosaic=1.0,  # 모자이크 증강
                mixup=0.0,  # 믹스업 증강
                # 최적화 설정
                optimizer=optimizer,
                lr0=lr0,
                lrf=lrf,
                momentum=momentum,
                weight_decay=weight_decay,
                warmup_epochs=warmup_epochs,
                warmup_momentum=0.8,
                warmup_bias_lr=0.1,
                # 기타 설정
                verbose=verbose,
                seed=0,
                deterministic=True,
                single_cls=False,
                rect=False,
                cos_lr=False,
                close_mosaic=10,
                amp=True,
                fraction=1.0,
                profile=False,
                freeze=None,
                multi_scale=False,
            )

            # 훈련 완료
            print("\n" + "=" * 80)
            print("✅ 훈련 완료!")
            print("=" * 80)

            self.print_results_summary()

            return results

        except KeyboardInterrupt:
            print("\n⚠️  훈련이 사용자에 의해 중단되었습니다")
            print("   마지막 체크포인트가 저장되었습니다")
            return None

        except Exception as e:
            print(f"\n❌ 훈련 중 오류 발생: {e}")
            raise

    def print_results_summary(self):
        """훈련 결과 요약을 출력합니다."""
        results_dir = Path(self.project_name) / self.experiment_name

        print(f"\n📁 결과 디렉토리: {results_dir.absolute()}")
        print(f"\n📊 주요 파일:")
        print(f"   - 최적 가중치: {results_dir}/weights/best.pt")
        print(f"   - 최종 가중치: {results_dir}/weights/last.pt")
        print(f"   - 결과 그래프: {results_dir}/results.png")
        print(f"   - 혼동 행렬:   {results_dir}/confusion_matrix.png")
        print(f"   - 훈련 로그:   {results_dir}/results.csv")

        print(f"\n🚀 다음 단계:")
        print(f"   1. 모델 검증:")
        print(
            f"      yolo task=detect mode=val model={results_dir}/weights/best.pt data={self.data_yaml}"
        )
        print(f"\n   2. 모델 추론:")
        print(
            f"      yolo task=detect mode=predict model={results_dir}/weights/best.pt source=test_image.jpg"
        )
        print(f"\n   3. 모델 내보내기:")
        print(f"      yolo export model={results_dir}/weights/best.pt format=onnx")
        print("=" * 80 + "\n")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="YOLO11 모델 훈련 스크립트")

    # 필수 인자
    parser.add_argument("--data", type=str, required=True, help="data.yaml 파일 경로")

    # 모델 설정
    parser.add_argument(
        "--model",
        type=str,
        default="n",
        choices=["n", "s", "m", "l", "x"],
        help="모델 크기 (n=nano, s=small, m=medium, l=large, x=xlarge)",
    )

    # 훈련 파라미터
    parser.add_argument(
        "--epochs", type=int, default=100, help="훈련 에포크 수 (기본값: 100)"
    )
    parser.add_argument("--batch", type=int, default=16, help="배치 크기 (기본값: 16)")
    parser.add_argument(
        "--imgsz", type=int, default=640, help="이미지 크기 (기본값: 640)"
    )
    parser.add_argument(
        "--patience", type=int, default=50, help="조기 종료 인내 (기본값: 50)"
    )

    # 최적화 설정
    parser.add_argument(
        "--optimizer",
        type=str,
        default="auto",
        choices=["SGD", "Adam", "AdamW", "auto"],
        help="최적화 알고리즘 (기본값: auto)",
    )
    parser.add_argument(
        "--lr0", type=float, default=0.01, help="초기 학습률 (기본값: 0.01)"
    )

    # 프로젝트 설정
    parser.add_argument(
        "--project",
        type=str,
        default="yolo11_training",
        help="프로젝트 이름 (기본값: yolo11_training)",
    )
    parser.add_argument(
        "--name", type=str, default=None, help="실험 이름 (기본값: 타임스탬프)"
    )

    # 기타
    parser.add_argument("--resume", action="store_true", help="이전 훈련 재개")
    parser.add_argument(
        "--no-augment", action="store_true", help="데이터 증강 비활성화"
    )

    args = parser.parse_args()

    # 훈련 실행
    trainer = YOLO11Trainer(
        model_size=args.model,
        data_yaml=args.data,
        project_name=args.project,
        experiment_name=args.name,
    )

    trainer.train(
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        patience=args.patience,
        resume=args.resume,
        optimizer=args.optimizer,
        lr0=args.lr0,
        augment=not args.no_augment,
    )


if __name__ == "__main__":
    # 예시 사용법
    # python train_yolo11.py --data yolo_dataset/data.yaml --model n --epochs 100 --batch 16

    # 또는 직접 실행 (Raspberry Pi용 경량 모델)
    trainer = YOLO11Trainer(
        model_size="n",  # nano 모델 (가장 경량)
        data_yaml="yolo_dataset/data.yaml",
        project_name="raspbot_yolo11",
        experiment_name="traffic_detection",
    )

    results = trainer.train(epochs=100, batch=16, imgsz=640, patience=50)
