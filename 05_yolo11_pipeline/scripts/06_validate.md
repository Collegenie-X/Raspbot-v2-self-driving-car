(venv) kimjongphil@kimjongphilui-Mac-Studio scripts % python 06_validate.py --config config.demo.yaml

  검증 설정 (그냥 엔터 → [ ] 안의 기본값 사용)
  모델(weights) [/Users/kimjongphil/Documents/GitHub/Raspbot-v2-self-driving-car/05_yolo11_pipeline/demo/models/best.pt]: 
  split (train/val/test) [val]: 
  imgsz [320]: 
  device (auto/cpu/mps/0) [auto]: 

================================================================
  [6단계] 모델 검증 (split=val)
================================================================
Ultralytics 8.4.218 🚀 Python-3.12.7 torch-2.15.0 CPU (Apple M2 Max)
YOLO11n summary (fused): 101 layers, 2,598,023 parameters, 0 gradients, 6.4 GFLOPs
val: Fast image access ✅ (ping: 0.0±0.0 ms, read: 4360.3±1624.8 MB/s, size: 125.4 KB)
val: Scanning /Users/kimjongphil/Documents/GitHub/Raspbot-v2-self-driving-car/05_yolo11_pipeline/demo/dataset/label…: 100% ━━━━━━━━━━━━ 47/47 24.6Mit/s 0.0s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 3/3 6.2it/s 0.5s
                   all         47         83      0.993          1      0.995      0.978
Speed: 0.1ms preprocess, 7.3ms inference, 0.0ms loss, 0.4ms postprocess per image
Results saved to /Users/kimjongphil/Documents/GitHub/Raspbot-v2-self-driving-car/05_yolo11_pipeline/demo/runs/val/val

  클래스                P       R      F1   mAP50  mAP50-95
  car            0.994   1.000   0.997   0.995     0.995
  green          0.988   1.000   0.994   0.995     0.986
  oo             0.993   1.000   0.996   0.995     0.976
  red            0.993   1.000   0.996   0.995     0.966
  xx             1.000   0.999   1.000   0.995     0.967
  [전체]          0.993   1.000   0.997   0.995     0.978

  속도(이미지당): 전처리 0.1ms | 추론 7.3ms | 후처리 0.4ms  (device=cpu)

  ── 합격 기준 ──
  ✅ map50              0.995  (기준 ≥ 0.5)
  ✅ map50_95           0.978  (기준 ≥ 0.3)
  ✅ precision          0.993  (기준 ≥ 0.5)
  ✅ recall             1.000  (기준 ≥ 0.5)
  ✅ map50[car]         0.995  (기준 ≥ 0.3)
  ✅ map50[green]       0.995  (기준 ≥ 0.3)
  ✅ map50[oo]          0.995  (기준 ≥ 0.3)
  ✅ map50[red]         0.995  (기준 ≥ 0.3)
  ✅ map50[xx]          0.995  (기준 ≥ 0.3)

  최종 판정: PASS ✅
  리포트: /Users/kimjongphil/Documents/GitHub/Raspbot-v2-self-driving-car/05_yolo11_pipeline/demo/reports/validate_val.md
  그래프: /Users/kimjongphil/Documents/GitHub/Raspbot-v2-self-driving-car/05_yolo11_pipeline/demo/runs/val/val
  다음 단계 → python scripts/07_test.py