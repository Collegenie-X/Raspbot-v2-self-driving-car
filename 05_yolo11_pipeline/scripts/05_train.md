# 05_train.py 구조 분석 — YOLO11 전이학습

> 파이프라인 **5단계**. COCO 로 사전학습된 `yolo11n.pt` 에서 출발해 우리 데이터셋(`data.yaml`)으로
> 미세조정(fine-tuning)하고, 가장 좋은 가중치를 `models/best.pt` 로 정리합니다.
> 실제 학습 엔진은 Ultralytics 이고, 이 스크립트는 **설정 병합 · 실행 · 결과 정리**를 담당하는 래퍼입니다.

---

## 1. 한눈에 보기

| 항목 | 내용 |
|---|---|
| 실행 | `python scripts/05_train.py [--model M] [--epochs N] [--imgsz S] [--batch B] [--device D] [--name X] [--resume]` |
| 입력 | `datasets/raspbot/data.yaml` (4단계 결과), 시작 가중치 (`yolo11n.pt` 등) |
| 출력 | `runs/train/<name>/` (가중치·그래프·로그), `models/best.pt`, `models/train_info.json` |
| 설정 | `config.yaml` 의 `train:` 섹션 (+ `train.extra` 증강 인자) |
| 이전 단계 | `04_split_dataset.py` |
| 다음 단계 | `06_validate.py` (mAP 합격 판정) |

```mermaid
flowchart LR
    D[(datasets/raspbot/<br/>data.yaml + images/labels)] --> T[05_train.py]
    W[yolo11n.pt<br/>COCO 사전학습] --> T
    C[config.yaml<br/>train 섹션] --> T
    T --> R[(runs/train/name/<br/>weights/best.pt, last.pt<br/>results.csv/png ...)]
    T --> M[(models/best.pt<br/>models/train_info.json)]
    M --> V[06_validate.py]
    M --> TT[07_test.py]
    M --> P[08_predict.py]
    M --> E[09_export.py]
```

---

## 2. 코드 구성

```
05_train.py
├── summarize_results_csv(csv_path)   results.csv → best/last epoch 지표 요약
└── main()
    ├── 1) 인자 파싱 + config.train 병합 (CLI > config)
    ├── 2) device / 출력 경로 결정
    ├── 3) data.yaml 존재 확인
    ├── 4) 학습 (--resume 분기)
    ├── 5) best.pt → models/best.pt 복사
    ├── 6) train_info.json 기록
    └── 7) 콘솔 요약 출력
```

---

## 3. 실행 흐름

```mermaid
flowchart TD
    S([시작]) --> A[argparse<br/>지정 안 한 인자는 None]
    A --> B[tc = dict cfg.train<br/>None 이 아닌 CLI 값으로 덮어쓰기]
    B --> C[device = pick_device<br/>name, project, data_yaml]
    C --> D{data.yaml 있음?}
    D -- 없음 --> X1[[종료: 4단계 먼저]]
    D -- 있음 --> E{--resume?}
    E -- 예 --> F{last.pt 있음?}
    F -- 없음 --> X2[[종료]]
    F -- 있음 --> G[YOLO last.pt<br/>train resume=True]
    E -- 아니오 --> H[YOLO tc.model<br/>train data, epochs, imgsz, batch,<br/>device, workers, patience, seed,<br/>project, name, exist_ok, plots, **extra]
    G --> I[save_dir = model.trainer.save_dir]
    H --> I
    I --> J{weights/best.pt 있음?}
    J -- 없음 --> X3[[종료]]
    J -- 있음 --> K[models/best.pt 로 복사]
    K --> L[summarize_results_csv<br/>→ train_info.json]
    L --> N[결과 요약 출력 → 6단계 안내]
```

---

## 4. 핵심 로직 상세

### 4.1 설정 병합 — "CLI > config"

```python
tc = dict(cfg["train"])                          # 원본을 건드리지 않게 복사
for k in ("model", "epochs", "imgsz", "batch", "device"):
    if getattr(args, k) is not None:             # 사용자가 CLI 로 준 값만
        tc[k] = getattr(args, k)
```

- argparse 기본값을 `None` 으로 두어 "사용자가 지정했는지"를 구분합니다.
- 덮어쓸 수 있는 키: `model, epochs, imgsz, batch, device`. 나머지(`workers, patience, seed, extra`)는 config 에서만 변경.

| 값 | config.yaml 기본 | CLI 예 |
|---|---|---|
| model | `yolo11n.pt` | `--model yolo11s.pt` |
| epochs | 100 | `--epochs 50` |
| imgsz | 640 | `--imgsz 320` |
| batch | 16 | `--batch 8` |
| device | `auto` | `--device cpu` / `0` / `mps` |

### 4.2 디바이스 선택 — `pick_device()` (common.py)

| 입력 | 결과 |
|---|---|
| `auto` / 빈 값 | CUDA 가 있으면 `"0"`, 없으면 `"cpu"` |
| 그 외 (`cpu`, `0`, `mps` ...) | 그대로 사용 |

Apple **MPS 는 자동 선택하지 않습니다.** PyTorch·macOS 조합에 따라 MPS 학습이 파이썬 예외 없이
프로세스째 종료되는 경우가 있어, 필요하면 `--device mps` 로 직접 지정하도록 설계되어 있습니다.

### 4.3 전이학습 (새 학습)

```python
model = YOLO(tc["model"])        # 'yolo11n.pt' → 없으면 자동 다운로드
model.train(data=..., epochs=..., ..., **(tc.get("extra") or {}))
```

- **전이학습**: COCO(80 클래스)로 배운 특징 추출기(backbone)를 재사용하고, 탐지 헤드는 `data.yaml` 의
  `nc=5` 에 맞게 새로 구성되어 학습됩니다. 적은 데이터로도 빠르게 수렴하는 이유입니다.
- 주요 학습 인자

| 인자 | 의미 | 조절 팁 |
|---|---|---|
| `epochs` | 전체 데이터 반복 횟수 | 성능이 계속 오르면 ↑ |
| `imgsz` | 학습 입력 크기 | 작은 객체가 많으면 640 유지, 운영(320)과 차이 확인은 7단계에서 |
| `batch` | 배치 크기 | GPU 메모리 부족 시 8 또는 `-1`(자동) |
| `patience` | 개선 없을 때 조기 종료까지 epoch 수 | 기본 30 |
| `seed` | 난수 시드 | 재현성 |
| `exist_ok=True` | 같은 이름 폴더 재사용 | `name2`, `name3` 처럼 폴더가 늘어나지 않음 (대신 덮어씀) |
| `plots=True` | 그래프 저장 | `results.png`, `confusion_matrix.png` 등 |

- `train.extra` (증강) — config 값이 그대로 `train()` 에 전달됩니다.

| 키 | 값 | 의미 |
|---|---|---|
| `hsv_h / hsv_s / hsv_v` | 0.015 / 0.7 / 0.4 | 색상·채도·밝기 무작위 변화 (조명 변화 대응) |
| `degrees` | 5.0 | ±5° 회전 |
| `translate` | 0.1 | ±10% 이동 |
| `scale` | 0.5 | ±50% 크기 변화 (거리 변화 대응) |
| `fliplr` | **0.0** | 좌우 반전 끔 — 좌/우 의미가 있는 표지판·신호에 안전 |
| `mosaic` | 1.0 | 4장 합성 증강 |
| `close_mosaic` | 10 | 마지막 10 epoch 는 mosaic 끔 (실제 분포에 맞춰 마무리) |

### 4.4 이어서 학습 (`--resume`)

```python
last = project / name / "weights" / "last.pt"
YOLO(str(last)).train(resume=True)
```

- `last.pt` 안에는 가중치뿐 아니라 **epoch 위치, optimizer 상태, 원래 학습 인자**가 저장되어 있어
  `resume=True` 하나로 중단 지점부터 이어집니다.
- 따라서 resume 시에는 `--epochs`, `--batch` 등 **CLI/config 값이 무시**됩니다 (원래 설정 유지).
- 다른 이름으로 학습했다면 `--name` 을 같이 줘야 해당 `last.pt` 를 찾습니다.

### 4.5 결과 정리

```python
save_dir = Path(model.trainer.save_dir)     # 실제로 결과가 저장된 폴더
shutil.copy2(save_dir/"weights"/"best.pt", models_dir/"best.pt")
```

- 경로를 직접 조립하지 않고 `trainer.save_dir` 를 쓰는 이유: resume 이나 Ultralytics 내부 규칙에 따라
  폴더명이 달라져도 정확한 위치를 얻기 위함.
- `models/best.pt` 는 6~9단계의 **기본 모델 경로**(`common.default_weights`)입니다.

### 4.6 `summarize_results_csv()` — 학습 로그 요약

Ultralytics 는 epoch 마다 `results.csv` 에 한 줄씩 기록합니다.

```
epoch, train/box_loss, ..., metrics/precision(B), metrics/recall(B), metrics/mAP50(B), metrics/mAP50-95(B), ...
```

| 단계 | 처리 |
|---|---|
| 읽기 | `csv.DictReader` + 키/값 `strip()` (버전에 따라 공백 패딩이 있음) |
| best | `metrics/mAP50-95(B)` 가 최대인 행 |
| last | 마지막 행 |
| 반환 | `{"best": {...}, "last": {...}, "epochs_run": N}` — 파일이 없으면 `{}` |

`(B)` 는 Box(탐지) 지표라는 뜻입니다 (세그멘테이션이면 `(M)` 도 생김).

### 4.7 `models/train_info.json` 예시

```json
{
  "trained_at": "2026-11-24T11:05:00",
  "duration_min": 42.3,
  "run_dir": ".../runs/train/raspbot_yolo11",
  "base_model": "yolo11n.pt",
  "device": "0",
  "classes": ["car", "green", "oo", "red", "xx"],
  "params": {"epochs": 100, "imgsz": 640, "batch": 16},
  "results": {
    "best": {"epoch": 87, "precision": 0.93, "recall": 0.90, "mAP50": 0.95, "mAP50-95": 0.71},
    "last": {"epoch": 100, "...": "..."},
    "epochs_run": 100
  }
}
```

(숫자는 형식 예시입니다.) 나중에 "이 모델이 어떤 데이터·설정으로 만들어졌는지" 추적할 때 사용합니다.

---

## 5. 학습 결과물 읽는 법

| 파일 (`runs/train/<name>/`) | 확인할 것 |
|---|---|
| `results.png` | train/val **loss 가 함께 감소**하는지, mAP 가 증가 후 수렴하는지 |
| `confusion_matrix.png` | 어떤 클래스끼리 헷갈리는지 (예: `red ↔ green`), background 로 놓치는 비율 |
| `labels.jpg` | 클래스 분포·박스 위치/크기 분포 (데이터 편향 확인) |
| `val_batch*_pred.jpg` | 실제 예측 결과 샘플 |
| `weights/best.pt` | val 성능이 가장 좋았던 가중치 → `models/best.pt` 로 복사됨 |
| `weights/last.pt` | 마지막 epoch → `--resume` 에 사용 |

| 증상 | 의심 원인 | 대응 |
|---|---|---|
| train loss ↓, val loss ↑ | 과적합 | 데이터 추가, 증강 강화, epochs ↓ (patience 가 자동으로 멈춤) |
| 둘 다 높게 정체 | 모델 용량/데이터 부족 | `yolo11s.pt`, epochs ↑, 라벨 품질 점검 |
| 특정 클래스만 낮음 | 해당 클래스 데이터 부족 | 3단계 리포트의 클래스 분포 확인 후 보강 |

---

## 6. 주의점

| # | 내용 | 대응 |
|---|---|---|
| 1 | `exist_ok=True` 라서 **같은 `--name` 으로 다시 학습하면 이전 결과 폴더를 덮어씀** | 비교하고 싶으면 `--name exp2` 처럼 이름을 바꿔 실행 |
| 2 | `models/best.pt`, `train_info.json` 도 매번 덮어씀 (버전 관리 없음) | 좋은 모델은 별도 이름으로 백업 |
| 3 | 요약의 "best epoch" 는 mAP50-95 최대 기준이지만, Ultralytics 의 `best.pt` 는 내부 fitness(mAP50·mAP50-95 가중 조합, 버전에 따라 다름) 기준 | 두 epoch 가 드물게 다를 수 있음 — 최종 성능은 6단계 결과를 기준으로 판단 |
| 4 | `--resume` 시 CLI 인자(epochs 등) 무시 | 설정을 바꾸려면 새 학습으로 시작 (`--model runs/.../last.pt`) |
| 5 | MPS 자동 선택 안 함 | Mac 에서 GPU 를 쓰려면 `--device mps` (불안정하면 cpu) |
| 6 | 학습 imgsz(640) ≠ 운영 imgsz(320) | 7단계에서 운영 조건으로 다시 테스트하는 이유 |

---

## 7. 연관 파일

| 파일 | 관계 |
|---|---|
| `common.py` | `load_config`, `path_of`, `data_yaml_path`, `pick_device`, `banner` |
| `04_split_dataset.py` | `data.yaml` 과 train/val/test 폴더를 생성 |
| `06_validate.py` | `models/best.pt` 를 mAP 기준으로 합격/불합격 판정 |
| `config.yaml` `train:` | 학습 파라미터와 증강 설정 |
| `docs/02_검증_테스트_가이드.md` | 지표 해석과 개선 루프 |


====================

(venv) kimjongphil@kimjongphilui-Mac-Studio scripts % python 05_train.py --config config.demo.yaml --epochs 10 --imgsz 320

  학습 설정 (그냥 엔터 → [ ] 안의 기본값 사용)
  실행 이름(name) [demo_yolo11]: 
  시작 가중치(model) [yolo11n.pt]: 
  batch (-1 = 자동) [16]: 
  device (auto/cpu/mps/0) [auto]: 

================================================================
  [5단계] YOLO11 학습
================================================================
  모델: yolo11n.pt | epochs 10 | imgsz 320 | batch 16 | device cpu
  데이터: /Users/kimjongphil/Documents/GitHub/Raspbot-v2-self-driving-car/05_yolo11_pipeline/demo/dataset/data.yaml
Ultralytics 8.4.218 🚀 Python-3.12.7 torch-2.15.0 CPU (Apple M2 Max)
engine/trainer: agnostic_nms=False, amp=True, angle=1.0, augment=False, auto_augment=randaugment, batch=16, bgr=0.0, box=7.5, cache=False, cfg=None, channels_last=None, classes=None, close_mosaic=3, cls=0.5, cls_pw=0.0, cls_remap=True, compile=False, conf=None, copy_paste=0.0, copy_paste_mode=flip, cos_lr=False,cutmix=0.0, data=/Users/kimjongphil/Documents/GitHub/Raspbot-v2-self-driving-car/05_yolo11_pipeline/demo/dataset/data.yaml, degrees=0.0, deterministic=True,device=cpu, dfl=1.5, dgrad=0.5, dis=6.0, distill_model=None, dlam=1.0, dlog=1.0, dnn=False, dropout=0.0, dynamic=False, embed=None, epochs=10, erasing=0.4, exist_ok=True, fliplr=0.0, flipud=0.0, format=torchscript, fraction=1.0, freeze=None, hsv_h=0.015, hsv_s=0.7, hsv_v=0.4, imgsz=320, iou=None, kobj=1.0, line_width=None, lr0=0.01, lrf=0.01, mask_ratio=4, max_det=300, mixup=0.0, mode=train, model=yolo11n.pt, momentum=0.937, mosaic=1.0, multi_scale=0.0, name=demo_yolo11, nbs=64, nms=None, opset=None, optimize=False, optimizer=auto, overlap_mask=True, patience=15, perspective=0.0, plots=True, pose=12.0, pretrained=True, profile=False, project=/Users/kimjongphil/Documents/GitHub/Raspbot-v2-self-driving-car/05_yolo11_pipeline/demo/runs/train, quantize=None, rect=False, resume=False, retina_masks=False, rle=1.0, save=True, save_conf=False, save_crop=False, save_dir=/Users/kimjongphil/Documents/GitHub/Raspbot-v2-self-driving-car/05_yolo11_pipeline/demo/runs/train/demo_yolo11, save_frames=False, save_json=False, save_period=-1, save_txt=False, scale=0.5, seed=42, shear=0.0, show=False, show_boxes=True, show_conf=True, show_labels=True, simplify=True, single_cls=False, source=None, split=val, stream_buffer=False, task=detect, tile=False, tile_overlap=0.2, time=None, tracker=tracktrack.yaml, translate=0.1, val=True, verbose=True, vid_stride=1, visualize=False, warmup_bias_lr=0.1, warmup_epochs=3.0, warmup_momentum=0.8, weight_decay=0.0005, workers=2, workspace=None
Overriding model.yaml nc=80 with nc=5

                   from  n    params  module                                       arguments                     
  0                  -1  1       464  ultralytics.nn.modules.conv.Conv             [3, 16, 3, 2]                 
  1                  -1  1      4672  ultralytics.nn.modules.conv.Conv             [16, 32, 3, 2]                
  2                  -1  1      6640  ultralytics.nn.modules.block.C3k2            [32, 64, 1, False, 0.25]      
  3                  -1  1     36992  ultralytics.nn.modules.conv.Conv             [64, 64, 3, 2]                
  4                  -1  1     26080  ultralytics.nn.modules.block.C3k2            [64, 128, 1, False, 0.25]     
  5                  -1  1    147712  ultralytics.nn.modules.conv.Conv             [128, 128, 3, 2]              
  6                  -1  1     87040  ultralytics.nn.modules.block.C3k2            [128, 128, 1, True]           
  7                  -1  1    295424  ultralytics.nn.modules.conv.Conv             [128, 256, 3, 2]              
  8                  -1  1    346112  ultralytics.nn.modules.block.C3k2            [256, 256, 1, True]           
  9                  -1  1    164608  ultralytics.nn.modules.block.SPPF            [256, 256, 5]                 
 10                  -1  1    249728  ultralytics.nn.modules.block.C2PSA           [256, 256, 1]                 
 11                  -1  1         0  torch.nn.modules.upsampling.Upsample         [None, 2, 'nearest']          
 12             [-1, 6]  1         0  ultralytics.nn.modules.conv.Concat           [1]                           
 13                  -1  1    111296  ultralytics.nn.modules.block.C3k2            [384, 128, 1, False]          
 14                  -1  1         0  torch.nn.modules.upsampling.Upsample         [None, 2, 'nearest']          
 15             [-1, 4]  1         0  ultralytics.nn.modules.conv.Concat           [1]                           
 16                  -1  1     32096  ultralytics.nn.modules.block.C3k2            [256, 64, 1, False]           
 17                  -1  1     36992  ultralytics.nn.modules.conv.Conv             [64, 64, 3, 2]                
 18            [-1, 13]  1         0  ultralytics.nn.modules.conv.Concat           [1]                           
 19                  -1  1     86720  ultralytics.nn.modules.block.C3k2            [192, 128, 1, False]          
 20                  -1  1    147712  ultralytics.nn.modules.conv.Conv             [128, 128, 3, 2]              
 21            [-1, 10]  1         0  ultralytics.nn.modules.conv.Concat           [1]                           
 22                  -1  1    378880  ultralytics.nn.modules.block.C3k2            [384, 256, 1, True]           
 23        [16, 19, 22]  1    431647  ultralytics.nn.modules.head.Detect           [5, 16, None, [64, 128, 256]] 
YOLO11n summary: 181 layers, 2,590,815 parameters, 2,590,799 gradients, 6.5 GFLOPs

Remapped 1/5 cls head rows from pretrained weights by class name
Transferred 499/499 items from pretrained weights
Freezing layer 'model.23.dfl.conv.weight'
train: Fast image access ✅ (ping: 0.0±0.0 ms, read: 990.4±1120.5 MB/s, size: 85.2 KB)
train: Scanning /Users/kimjongphil/Documents/GitHub/Raspbot-v2-self-driving-car/05_yolo11_pipeline/demo/dataset/l…: 100% ━━━━━━━━━━━━ 169/169 88.6Mit/s 0.0s
val: Fast image access ✅ (ping: 0.0±0.0 ms, read: 3622.1±1914.3 MB/s, size: 106.5 KB)
val: Scanning /Users/kimjongphil/Documents/GitHub/Raspbot-v2-self-driving-car/05_yolo11_pipeline/demo/dataset/label…: 100% ━━━━━━━━━━━━ 47/47 39.4Mit/s 0.0s
optimizer: 'optimizer=auto' found, ignoring 'lr0=0.01' and determining best 'optimizer' and 'lr0' automatically... 
optimizer: AdamW(lr=0.001111, momentum=0.9) with parameter groups 81 weight(decay=0.0), 88 weight(decay=0.0005), 87 bias(decay=0.0)
Plotting labels to /Users/kimjongphil/Documents/GitHub/Raspbot-v2-self-driving-car/05_yolo11_pipeline/demo/runs/train/demo_yolo11/labels.jpg... 
Using 169 train, 47 val images for fraction=1.0 at imgsz=320
Using 0 dataloader workers
Logging results to /Users/kimjongphil/Documents/GitHub/Raspbot-v2-self-driving-car/05_yolo11_pipeline/demo/runs/train/demo_yolo11
Starting training for 10 epochs...

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
       1/10         0G     0.8318       3.28      0.893         34        320: 100% ━━━━━━━━━━━━ 11/11 1.6it/s 7.0s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 3.7it/s 0.5s
                   all         47         83      0.441      0.756      0.559      0.493

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
       2/10         0G     0.6491      1.448     0.8391         25        320: 100% ━━━━━━━━━━━━ 11/11 1.6it/s 6.8s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 2.9it/s 0.7s
                   all         47         83      0.796       0.74      0.829      0.744

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
       3/10         0G     0.6214     0.9152     0.8345         37        320: 100% ━━━━━━━━━━━━ 11/11 1.6it/s 6.8s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 3.4it/s 0.6s
                   all         47         83      0.737      0.861       0.93      0.833

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
       4/10         0G     0.5595     0.7682     0.8376         31        320: 100% ━━━━━━━━━━━━ 11/11 1.6it/s 6.8s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 3.5it/s 0.6s
                   all         47         83      0.954      0.976      0.986      0.887

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
       5/10         0G      0.505     0.6069     0.8283         21        320: 100% ━━━━━━━━━━━━ 11/11 1.7it/s 6.6s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 4.0it/s 0.5s
                   all         47         83      0.979          1      0.994      0.896

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
       6/10         0G     0.4692     0.5635      0.824         22        320: 100% ━━━━━━━━━━━━ 11/11 1.6it/s 6.9s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 4.2it/s 0.5s
                   all         47         83      0.994          1      0.995      0.935

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
       7/10         0G     0.4193     0.5364     0.8173         35        320: 100% ━━━━━━━━━━━━ 11/11 1.6it/s 6.8s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 4.5it/s 0.4s
                   all         47         83      0.989          1      0.995      0.951
Closing dataloader mosaic

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
       8/10         0G     0.3642     0.5002     0.8068         19        320: 100% ━━━━━━━━━━━━ 11/11 1.6it/s 7.0s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 4.5it/s 0.4s
                   all         47         83      0.995          1      0.995      0.958

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
       9/10         0G     0.3677     0.4804     0.7905         15        320: 100% ━━━━━━━━━━━━ 11/11 1.6it/s 6.9s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 4.5it/s 0.4s
                   all         47         83      0.994          1      0.995       0.97

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
      10/10         0G     0.3088     0.4256     0.7993         14        320: 100% ━━━━━━━━━━━━ 11/11 1.6it/s 6.8s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 4.6it/s 0.4s
                   all         47         83      0.993          1      0.995      0.978

10 epochs completed in 0.021 hours.
Optimizer stripped from /Users/kimjongphil/Documents/GitHub/Raspbot-v2-self-driving-car/05_yolo11_pipeline/demo/runs/train/demo_yolo11/weights/last.pt, 5.5MB
Optimizer stripped from /Users/kimjongphil/Documents/GitHub/Raspbot-v2-self-driving-car/05_yolo11_pipeline/demo/runs/train/demo_yolo11/weights/best.pt, 5.5MB

Validating /Users/kimjongphil/Documents/GitHub/Raspbot-v2-self-driving-car/05_yolo11_pipeline/demo/runs/train/demo_yolo11/weights/best.pt...
Ultralytics 8.4.218 🚀 Python-3.12.7 torch-2.15.0 CPU (Apple M2 Max)
YOLO11n summary (fused): 101 layers, 2,598,023 parameters, 0 gradients, 6.4 GFLOPs
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 5.0it/s 0.4s
                   all         47         83      0.993          1      0.995      0.978
                   car         13         14      0.994          1      0.995      0.995
                 green         13         13      0.988          1      0.995      0.986
                    oo         14         17      0.993          1      0.995      0.976
                   red         16         18      0.993          1      0.995      0.966
                    xx         18         21          1      0.999      0.995      0.967
Speed: 0.1ms preprocess, 5.6ms inference, 0.0ms loss, 0.4ms postprocess per image
Results saved to /Users/kimjongphil/Documents/GitHub/Raspbot-v2-self-driving-car/05_yolo11_pipeline/demo/runs/train/demo_yolo11

  ── 학습 결과 ──
  소요 시간: 1.3 분 | 결과 폴더: /Users/kimjongphil/Documents/GitHub/Raspbot-v2-self-driving-car/05_yolo11_pipeline/demo/runs/train/demo_yolo11
  best epoch 10: P 0.993 | R 1.000 | mAP50 0.995 | mAP50-95 0.978
  최종 모델: /Users/kimjongphil/Documents/GitHub/Raspbot-v2-self-driving-car/05_yolo11_pipeline/demo/models/best.pt
  확인할 그래프: results.png (loss 감소 / mAP 증가), confusion_matrix.png, val_batch*_pred.jpg
  다음 단계 → python scripts/06_validate.py