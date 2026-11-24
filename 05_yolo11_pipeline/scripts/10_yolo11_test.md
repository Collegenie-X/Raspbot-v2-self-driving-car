경로를 고쳤고, 중간에 물어보신 config 질문에도 답변드립니다.

## 경로 수정 ([10_yolo11_test.py](05_yolo11_pipeline/scripts/10_yolo11_test.py))

| 항목 | 이전 | 수정 후 |
|---|---|---|
| 기본 모델 | `scripts/models/best.onnx` (없는 경로) | **`05_yolo11_pipeline/models/best.onnx`** (9단계 결과가 저장되는 곳) |
| Raspbot 라이브러리 | `05_yolo11_pipeline/lib/raspbot` | 저장소 최상위의 `lib/raspbot` (`final_08`과 같은 위치) |
| `s` 키로 저장하는 화면 | `scripts/tmp/` | `05_yolo11_pipeline/runs/camera_test/` |

**모델이 없을 때:** 어떤 파일을 만들어야 하는지, 데모 모델은 어떻게 지정하는지 오류 메시지로 안내합니다.

**확인한 것:** 데모 모델로 실행하면 정상적으로 탐지합니다. Pi에서는 아직 돌려보지 않았습니다.

```bash
python 10_yolo11_test.py --model ../demo/models/best.onnx
```

**지금 바로 기본값으로 실행하면 오류가 납니다.** `05_yolo11_pipeline/models/best.onnx`는 실제 데이터로 학습한 뒤 9단계를 돌려야 생깁니다. 그 전까지는 위처럼 `--model`을 지정하세요.

## config 파일은 필요 없습니다. 모델 파일만 있으면 됩니다

이 스크립트는 `config.yaml`도, `common.py`도 읽지 않습니다. 필요한 값은 이렇게 해결합니다.

| 필요한 값 | 가져오는 곳 |
|---|---|
| 클래스 이름 (car/green/oo/red/xx) | 모델 파일 안 |
| 입력 크기 320 | 모델 파일 안에 고정 + 스크립트의 `YOLO_IMGSZ = 320` |
| conf 0.5 | 스크립트의 `YOLO_CONF = 0.5` (config와 같은 값을 직접 적어 둠) |

그래서 **Pi에는 이것만 있으면 됩니다.**
1. `10_yolo11_test.py` 파일 1개
2. `best.onnx` 모델 파일 1개
3. 설치할 패키지:
   ```bash
   pip install ultralytics onnxruntime
   ```
   `opencv-python`은 ultralytics를 설치할 때 함께 설치됩니다.
4. (선택) 저장소의 `lib/raspbot`: 카메라 서보 각도를 맞출 때만 씁니다. 없으면 서보 제어를 건너뛰고 탐지만 합니다.

**Pi에 폴더 구조를 그대로 두지 않는다면,** 모델 경로를 직접 지정하면 됩니다. 이렇게 하면 폴더 구조와 상관없이 실행됩니다.

```bash
python3 10_yolo11_test.py --model ~/best.onnx
```

**주의할 점:** config에서 conf나 imgsz를 바꿔도 이 스크립트에는 반영되지 않습니다. 필요하면 `--conf` 옵션을 주거나, 파일 위쪽의 `YOLO_CONF` 값을 고치세요. imgsz는 모델을 변환할 때 정한 값(320)과 같아야 합니다.