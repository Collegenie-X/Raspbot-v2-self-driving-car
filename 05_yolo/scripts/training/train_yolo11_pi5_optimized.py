"""
Raspberry Pi 5 최적화 YOLO11n 훈련 스크립트

이 스크립트는 Raspberry Pi 5에서 최고 성능을 발휘하도록
특별히 최적화된 설정으로 YOLOv11n 모델을 훈련합니다.
"""

from ultralytics import YOLO
import torch
from pathlib import Path
import argparse
from datetime import datetime
import yaml


class RaspberryPi5Trainer:
    """Raspberry Pi 5 최적화 YOLO11n 트레이너"""

    def __init__(
        self,
        data_yaml: str,
        project_name: str = "raspberrypi5_yolo11",
        experiment_name: str = None,
    ):
        """
        Args:
            data_yaml: 데이터 설정 파일 경로
            project_name: 프로젝트 이름
            experiment_name: 실험 이름
        """
        self.data_yaml = data_yaml
        self.project_name = project_name

        # 실험 이름 설정
        if experiment_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.experiment_name = f"pi5_optimized_{timestamp}"
        else:
            self.experiment_name = experiment_name

        # 데이터 파일 확인
        if not Path(data_yaml).exists():
            raise FileNotFoundError(f"데이터 파일이 없습니다: {data_yaml}")

        # 클래스 정보 로드
        with open(data_yaml, "r") as f:
            data_config = yaml.safe_load(f)
            self.num_classes = data_config["nc"]
            self.class_names = data_config["names"]

        # YOLOv11n 모델 초기화 (Raspberry Pi는 nano만!)
        print("📥 YOLOv11n 모델 로딩 (Raspberry Pi 5 최적화)")
        self.model = YOLO("yolo11n.pt")

        # 장치 설정
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🔧 훈련 장치: {self.device}")

        if self.device == "cuda":
            print(f"   GPU: {torch.cuda.get_device_name(0)}")

        self.print_config_info()

    def print_config_info(self):
        """설정 정보 출력"""
        print("\n" + "=" * 70)
        print("🍓 Raspberry Pi 5 최적화 훈련 설정")
        print("=" * 70)
        print(f"모델: YOLOv11n (nano)")
        print(f"클래스 개수: {self.num_classes}")
        print(f"클래스: {self.class_names}")
        print(f"데이터: {self.data_yaml}")
        print(f"프로젝트: {self.project_name}/{self.experiment_name}")
        print("=" * 70)
        print("\n최적화 전략:")
        print("  ✅ 입력 크기: 416x416 (속도-정확도 균형)")
        print("  ✅ 배치 크기: 32-64 (일반화 성능 향상)")
        print("  ✅ 최적화: AdamW (과적합 방지)")
        print("  ✅ 증강: 자율주행 특화")
        print("  ✅ 목표: Raspberry Pi 5에서 25-30 FPS")
        print("=" * 70 + "\n")

    def train_pi5_optimized(
        self, epochs: int = 150, batch: int = 32, patience: int = 50
    ):
        """
        Raspberry Pi 5 최적화 훈련 실행

        Args:
            epochs: 훈련 에포크 수
            batch: 배치 크기
            patience: 조기 종료 인내
        """
        print("🚀 Raspberry Pi 5 최적화 훈련 시작...\n")

        try:
            # Raspberry Pi 5 최적화 훈련
            results = self.model.train(
                # 기본 설정
                data=self.data_yaml,
                epochs=epochs,
                batch=batch,
                imgsz=416,  # ✅ Pi 5 최적 크기 (640보다 2배 빠름)
                device=self.device,
                patience=patience,
                save_period=20,
                project=self.project_name,
                name=self.experiment_name,
                exist_ok=True,
                # Raspberry Pi Camera 특성 고려 증강
                augment=True,
                hsv_h=0.015,  # 색조 (Pi Camera 자동 화이트밸런스)
                hsv_s=0.7,  # 채도 (다양한 조명)
                hsv_v=0.4,  # 명도 (밝기 변화)
                # 자율주행 특화 기하학적 증강
                degrees=5.0,  # ✅ 약간의 회전 (차량 흔들림)
                translate=0.1,  # ✅ 이동 (카메라 위치 변화)
                scale=0.5,  # ✅ 크기 변화 (거리 변화)
                shear=0.0,  # 전단 (자율주행에 불필요)
                perspective=0.0,  # 원근 (자율주행에 불필요)
                # 반전 (자율주행 특성)
                flipud=0.0,  # ✅ 상하 반전 안 함
                fliplr=0.5,  # ✅ 좌우 반전만
                # 모자이크 증강 (소량 데이터 극복)
                mosaic=1.0,  # ✅ 활성화
                mixup=0.0,  # 비활성화 (자율주행에 부적합)
                copy_paste=0.0,  # 비활성화
                # 최적화 알고리즘 (엣지 디바이스 최적)
                optimizer="AdamW",  # ✅ 과적합 방지
                lr0=0.01,  # 초기 학습률
                lrf=0.01,  # 최종 학습률 비율
                momentum=0.937,
                weight_decay=0.0005,  # 정규화
                warmup_epochs=3.0,
                warmup_momentum=0.8,
                warmup_bias_lr=0.1,
                # 기타 설정
                verbose=True,
                seed=42,  # 재현성
                deterministic=True,
                single_cls=False,
                rect=False,
                cos_lr=False,
                close_mosaic=10,  # 마지막 10 에포크에서 모자이크 비활성화
                amp=True,  # 자동 혼합 정밀도 (GPU만)
                fraction=1.0,
                profile=False,
                freeze=None,
                multi_scale=False,  # 단일 크기로 고정 (속도 최적화)
                overlap_mask=True,
                mask_ratio=4,
                dropout=0.0,
                val=True,
            )

            print("\n" + "=" * 70)
            print("✅ 훈련 완료!")
            print("=" * 70)

            self.print_results_summary()
            self.export_for_raspberry_pi()

            return results

        except KeyboardInterrupt:
            print("\n⚠️  훈련이 사용자에 의해 중단되었습니다")
            return None

        except Exception as e:
            print(f"\n❌ 훈련 중 오류 발생: {e}")
            raise

    def print_results_summary(self):
        """훈련 결과 요약"""
        results_dir = Path(self.project_name) / self.experiment_name
        best_weights = results_dir / "weights" / "best.pt"

        print(f"\n📁 결과 디렉토리: {results_dir.absolute()}")
        print(f"\n📊 주요 파일:")
        print(f"   - 최적 가중치: {best_weights}")
        print(f"   - 결과 그래프: {results_dir}/results.png")
        print(f"   - 혼동 행렬: {results_dir}/confusion_matrix.png")
        print(f"   - 훈련 로그: {results_dir}/results.csv")

    def export_for_raspberry_pi(self):
        """Raspberry Pi 5용 모델 내보내기"""
        results_dir = Path(self.project_name) / self.experiment_name
        best_weights = results_dir / "weights" / "best.pt"

        if not best_weights.exists():
            print("\n⚠️  가중치 파일을 찾을 수 없습니다")
            return

        print("\n" + "=" * 70)
        print("🍓 Raspberry Pi 5용 모델 내보내기")
        print("=" * 70)

        model = YOLO(str(best_weights))

        # 1. ONNX 변환 (추론 속도 30% 향상)
        print("\n1️⃣ ONNX 변환 중... (추론 속도 30% 향상)")
        try:
            onnx_path = model.export(
                format="onnx", simplify=True, opset=12, dynamic=False, imgsz=416
            )
            print(f"   ✅ ONNX: {onnx_path}")
        except Exception as e:
            print(f"   ❌ ONNX 변환 실패: {e}")

        # 2. TensorFlow Lite 변환 (선택사항)
        print("\n2️⃣ TensorFlow Lite 변환 중... (선택사항)")
        try:
            tflite_path = model.export(
                format="tflite", int8=False, imgsz=416  # INT8 양자화는 정확도 저하 가능
            )
            print(f"   ✅ TFLite: {tflite_path}")
        except Exception as e:
            print(f"   ⚠️  TFLite 변환 실패 (선택사항): {e}")

        # 3. NCNN 변환 (Raspberry Pi CPU 최적화)
        print("\n3️⃣ NCNN 변환 중... (CPU 최적화)")
        try:
            ncnn_path = model.export(format="ncnn", imgsz=416)
            print(f"   ✅ NCNN: {ncnn_path}")
        except Exception as e:
            print(f"   ⚠️  NCNN 변환 실패 (선택사항): {e}")

        print("\n" + "=" * 70)
        print("🚀 Raspberry Pi 5 배포 가이드")
        print("=" * 70)
        print("\n1. 모델 전송:")
        print(f"   scp {best_weights} pi@raspberrypi.local:~/models/")
        print(f"   scp {onnx_path} pi@raspberrypi.local:~/models/")

        print("\n2. Raspberry Pi 5에서 실행:")
        print("   python3 autonomous_driving_pi5.py --model ~/models/best.onnx")

        print("\n3. 기대 성능:")
        print("   - FPS: 25-30 (416x416, ONNX)")
        print("   - 정확도: mAP50 0.75-0.85")
        print("   - 메모리: ~500MB")
        print("=" * 70 + "\n")

    def validate(self):
        """모델 검증"""
        results_dir = Path(self.project_name) / self.experiment_name
        best_weights = results_dir / "weights" / "best.pt"

        if not best_weights.exists():
            print("❌ 가중치 파일을 찾을 수 없습니다")
            return

        print("\n🔍 모델 검증 중...")
        model = YOLO(str(best_weights))

        metrics = model.val(
            data=self.data_yaml,
            imgsz=416,
            batch=16,
            conf=0.25,
            iou=0.6,
            device=self.device,
        )

        print("\n📊 검증 결과:")
        print(f"   mAP50: {metrics.box.map50:.4f}")
        print(f"   mAP50-95: {metrics.box.map:.4f}")
        print(f"   Precision: {metrics.box.mp:.4f}")
        print(f"   Recall: {metrics.box.mr:.4f}")

        # Raspberry Pi 5 성능 평가
        print("\n🍓 Raspberry Pi 5 예상 성능:")
        if metrics.box.map50 > 0.80:
            print("   ✅ 우수 (mAP50 > 0.80)")
        elif metrics.box.map50 > 0.70:
            print("   ✅ 양호 (mAP50 > 0.70)")
        elif metrics.box.map50 > 0.60:
            print("   ⚠️  보통 (mAP50 > 0.60)")
        else:
            print("   ❌ 부족 (mAP50 < 0.60) - 추가 훈련 필요")

        return metrics


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="Raspberry Pi 5 최적화 YOLO11n 훈련 스크립트"
    )

    # 필수 인자
    parser.add_argument("--data", type=str, required=True, help="data.yaml 파일 경로")

    # 프로젝트 설정
    parser.add_argument(
        "--project",
        type=str,
        default="raspberrypi5_yolo11",
        help="프로젝트 이름 (기본값: raspberrypi5_yolo11)",
    )

    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="실험 이름 (기본값: pi5_optimized_타임스탬프)",
    )

    # 훈련 파라미터
    parser.add_argument(
        "--epochs",
        type=int,
        default=150,
        help="훈련 에포크 수 (기본값: 150, Pi 5 최적)",
    )

    parser.add_argument(
        "--batch",
        type=int,
        default=32,
        help="배치 크기 (기본값: 32, GPU 메모리 충분하면 64 권장)",
    )

    parser.add_argument(
        "--patience", type=int, default=50, help="조기 종료 인내 (기본값: 50)"
    )

    # 추가 옵션
    parser.add_argument("--validate", action="store_true", help="훈련 후 검증 실행")

    args = parser.parse_args()

    # 트레이너 초기화
    trainer = RaspberryPi5Trainer(
        data_yaml=args.data, project_name=args.project, experiment_name=args.name
    )

    # 훈련 실행
    results = trainer.train_pi5_optimized(
        epochs=args.epochs, batch=args.batch, patience=args.patience
    )

    # 검증 (선택)
    if args.validate and results is not None:
        trainer.validate()


if __name__ == "__main__":
    """
    사용 예시:
    
    # 기본 사용
    python train_yolo11_pi5_optimized.py --data yolo_dataset/data.yaml
    
    # 커스텀 설정
    python train_yolo11_pi5_optimized.py \
        --data yolo_dataset/data.yaml \
        --epochs 200 \
        --batch 64 \
        --project my_pi5_project \
        --name traffic_detection \
        --validate
    
    # 또는 직접 실행
    """

    # 직접 실행 예시
    trainer = RaspberryPi5Trainer(
        data_yaml="yolo_dataset/data.yaml",
        project_name="raspberrypi5_yolo11",
        experiment_name="optimized",
    )

    # Raspberry Pi 5 최적화 훈련
    results = trainer.train_pi5_optimized(epochs=150, batch=32, patience=50)

    # 검증
    if results:
        trainer.validate()
