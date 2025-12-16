# 🚀 YOLO11 하이브리드 자율주행 - 빠른 시작 가이드

## ⚡ 3분 안에 실행하기

### 1단계: 패키지 설치 (30초)

```bash
pip install ultralytics opencv-python numpy
```

### 2단계: 디렉토리 이동

```bash
cd /Users/kimjongphil/Documents/GitHub/Raspbot-v2-self-driving-car/06_final_self_driving
```

### 3단계: 실행 방법 선택

#### 방법 A: YOLO 모델만 테스트 (추천)

```bash
python3 test_yolo_model.py
```

**실행 화면**:
```
✅ Ultralytics YOLO 로드 성공
📦 사전 학습 모델 다운로드 중: yolo11n.pt
✅ 사전 학습 모델 로드 완료 (COCO dataset)
📷 카메라 초기화 완료
```

**키보드 단축키**:
- `q` 또는 `ESC`: 종료
- `s`: 스크린샷 저장

#### 방법 B: 전체 자율주행 시스템 실행

```bash
python3 yolo_final_autoplot.py
```

**실행 화면**:
```
⚠️  Custom model not found: ./models/traffic_light_yolo11.pt
📦 Downloading pretrained YOLO11 model: yolo11n.pt
✅ Pretrained YOLO model loaded successfully
   ⚠️  Note: Cannot distinguish red/green lights
```

**7개 윈도우 표시**:
1. Camera Settings - 트랙바 제어판
2. 1_Frame - 원본 + ROI
3. 2_frame_transformed - 원근 변환
4. 3_gray_frame - RGB 가중치
5. 4_Processed Frame - 이진화
6. 5_YOLO_Traffic_Light - YOLO 감지 (⭐ 여기 주목!)
7. 6_Sign_Detection - Haar 표지판

---

## 📊 실행 결과

### 사전 학습 모델 사용 시

| 기능 | 상태 | 설명 |
|------|------|------|
| 신호등 감지 | ✅ 작동 | 노란색 박스로 표시 |
| 빨간/초록 구분 | ❌ 불가 | Class 9만 감지 |
| 신호등 제어 | ❌ 미작동 | 빨간불 감지 못함 |
| 표지판 감지 | ✅ 작동 | Haar Cascade |
| 자율주행 | ✅ 작동 | Line Tracing |

### 커스텀 모델 사용 시 (완전한 기능)

| 기능 | 상태 | 설명 |
|------|------|------|
| 신호등 감지 | ✅ 작동 | 빨간/초록/일반 구분 |
| 빨간/초록 구분 | ✅ 가능 | Class 0, 1 감지 |
| 신호등 제어 | ✅ 작동 | 빨간불→정지, 초록불→재개 |
| 표지판 감지 | ✅ 작동 | Haar Cascade |
| 자율주행 | ✅ 작동 | Line Tracing |

---

## 🎯 다음 단계

### 테스트만 하려면

현재 상태로 충분합니다! 사전 학습 모델로 신호등 감지를 확인할 수 있습니다.

### 완전한 기능을 원하면

1. **신호등 이미지 수집**
   - 빨간불 사진 200장 이상
   - 초록불 사진 200장 이상
   - 다양한 각도/조명/거리에서 촬영

2. **라벨링**
   ```bash
   # labelImg 설치
   pip install labelImg
   
   # 라벨링 시작
   labelImg
   ```

3. **모델 학습**
   ```python
   from ultralytics import YOLO
   
   # YOLO11 nano 모델로 시작
   model = YOLO('yolo11n.pt')
   
   # 학습
   model.train(
       data='traffic_light.yaml',
       epochs=100,
       imgsz=640,
       batch=16
   )
   ```

4. **모델 배치**
   ```bash
   # 학습된 모델을 models/ 폴더로 복사
   cp runs/detect/train/weights/best.pt ./models/traffic_light_yolo11.pt
   
   # 재실행
   python3 yolo_final_autoplot.py
   ```

---

## 🐛 문제 해결

### 문제: "Import 'ultralytics' could not be resolved"

```bash
pip install ultralytics
```

### 문제: 카메라를 열 수 없음

```bash
# 카메라 권한 확인
ls -l /dev/video*

# 다른 프로그램에서 카메라 사용 중인지 확인
lsof /dev/video0
```

### 문제: 모델 다운로드가 너무 느림

```bash
# 다운로드 위치 확인
ls ~/.cache/ultralytics/

# 수동 다운로드 (선택)
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolo11n.pt
mv yolo11n.pt ~/.cache/ultralytics/
```

### 문제: FPS가 너무 낮음 (< 20)

```bash
# CPU 성능 모드 설정 (Raspberry Pi)
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# 불필요한 프로세스 종료
pkill -f python
```

---

## 📚 더 자세한 정보

- 전체 문서: [README_YOLO_FINAL_AUTOPLOT.md](./README_YOLO_FINAL_AUTOPLOT.md)
- 알고리즘 가이드: [2단계_알고리즘_및_구현_가이드.md](./2단계_알고리즘_및_구현_가이드.md)
- YOLO 공식 문서: https://docs.ultralytics.com/

---

## 🎓 학습 경로

### 입문자
```
1. test_yolo_model.py 실행 → YOLO 이해
2. yolo_final_autoplot.py 실행 → 전체 시스템 이해
3. 트랙바 조정 → 파라미터 영향 확인
4. 코드 분석 → 알고리즘 학습
```

### 중급자
```
1. 사전 학습 모델로 프로토타입 완성
2. 신호등 데이터 수집 및 라벨링
3. YOLO 모델 학습
4. 커스텀 모델 배치 및 Fine-tuning
```

### 고급자
```
1. 멀티스레딩 도입 → 성능 향상
2. TensorRT 최적화 → 추론 속도 2배
3. 센서 퓨전 (초음파, IMU)
4. 클라우드 연동 및 OTA 업데이트
```

---

**작성일**: 2025-12-15  
**버전**: v3.0  
**작성자**: Raspbot v2 Project

