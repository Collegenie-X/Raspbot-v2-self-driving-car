"""
실시간 카메라 YOLO 객체 인식 예제
- 320x240 해상도 사용
- cv2.rectangle, putText로 박스 표시
- non-blocking 방식으로 구현

실행 방법:
    python simple_yolo_cv.py

키 조작:
    ESC 또는 'q' : 종료
    's'          : 스크린샷 저장
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2

# 프로젝트 루트를 import path에 추가
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main():
    # ========== 1. 초기화 ==========
    print("[INFO] YOLO 모델 로딩 중...")
    
    # YOLO 모델 로드
    try:
        from ultralytics import YOLO
    except ImportError:
        print("[ERROR] ultralytics 패키지가 설치되어 있지 않습니다.")
        print("설치 방법: pip install ultralytics")
        return
    
    # 모델 파일 경로
    model_path = PROJECT_ROOT / "models" / "yolo" / "best.pt"
    
    if not model_path.exists():
        print(f"[ERROR] 모델 파일을 찾을 수 없습니다: {model_path}")
        print("모델 파일을 'models/yolo/best.pt' 경로에 배치해주세요.")
        return
    
    model = YOLO(str(model_path))
    print(f"[INFO] 모델 로드 완료: {model_path}")
    
    # 모델 클래스 출력
    print("\n[INFO] 모델 클래스 목록:")
    for cls_id, cls_name in model.names.items():
        print(f"  {cls_id}: {cls_name}")
    
    # 카메라 초기화 (320x240 해상도)
    print("\n[INFO] 카메라 초기화 중...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("[ERROR] 카메라를 열 수 없습니다.")
        print("카메라가 연결되어 있는지 확인해주세요.")
        return
    
    # 카메라 해상도 설정
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    
    # 실제 설정된 해상도 확인
    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[INFO] 카메라 해상도: {actual_width}x{actual_height}")
    
    print("\n[INFO] 카메라 시작. ESC 또는 'q'로 종료합니다.")
    print("키 조작:")
    print("  ESC 또는 'q' : 프로그램 종료")
    print("  's'          : 스크린샷 저장")
    
    # 윈도우 생성
    window_name = "YOLO Real-time Detection"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 640, 480)  # 표시 크기
    
    # ========== 2. 메인 루프 ==========
    frame_count = 0
    
    try:
        while True:
            # 프레임 읽기
            ret, frame = cap.read()
            
            if not ret:
                print("[WARN] 프레임을 읽지 못했습니다.")
                break
            
            frame_count += 1
            
            # YOLO 추론 (non-blocking을 위해 verbose=False)
            results = model(
                frame,           # BGR numpy 배열 그대로 사용
                imgsz=320,       # 입력 크기 320x320
                conf=0.5,        # 신뢰도 임계값 50%
                verbose=False    # 로그 출력 끄기
            )
            
            # 결과 추출
            r0 = results[0]
            boxes = r0.boxes if r0.boxes is not None else []
            
            # ========== 3. 정보 표시 ==========
            # 프레임 번호 및 감지 개수
            info_bg = frame.copy()
            cv2.rectangle(info_bg, (0, 0), (frame.shape[1], 70), (0, 0, 0), -1)
            cv2.addWeighted(info_bg, 0.6, frame, 0.4, 0, frame)
            
            cv2.putText(
                frame,
                f"Frame: {frame_count}",
                (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )
            
            cv2.putText(
                frame,
                f"Detected: {len(boxes)} objects",
                (10, 55),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
            
            # ========== 4. 각 박스 그리기 ==========
            for box in boxes:
                # 클래스 정보
                cls_id = int(box.cls.item())
                cls_name = model.names[cls_id]
                conf = float(box.conf.item())
                
                # 박스 좌표
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                # 클래스별 색상 지정
                color_map = {
                    "red": (0, 0, 255),      # 빨간색 신호등
                    "green": (0, 255, 0),    # 녹색 신호등
                    "oo": (255, 255, 255),   # 주차 가능 (흰색)
                    "xx": (255, 0, 0),       # 주차 불가 (파란색)
                    "car": (0, 165, 255),    # 차량 (주황색)
                }
                color = color_map.get(cls_name, (200, 200, 200))  # 기본 회색
                
                # 박스 그리기
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                
                # 라벨 텍스트 (클래스명 + 신뢰도)
                label = f"{cls_name} {conf:.2f}"
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                
                # 라벨 배경 그리기
                label_y1 = max(0, y1 - label_size[1] - 10)
                label_y2 = y1
                label_x1 = x1
                label_x2 = min(frame.shape[1], x1 + label_size[0] + 5)
                
                cv2.rectangle(
                    frame,
                    (label_x1, label_y1),
                    (label_x2, label_y2),
                    color,
                    -1  # 채우기
                )
                
                # 라벨 텍스트 그리기
                cv2.putText(
                    frame,
                    label,
                    (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),  # 흰색
                    1
                )
                
                # 박스 중심에 작은 원 표시
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                cv2.circle(frame, (center_x, center_y), 3, color, -1)
            
            # ========== 5. 화면 표시 ==========
            cv2.imshow(window_name, frame)
            
            # ========== 6. 키 입력 처리 (non-blocking) ==========
            key = cv2.waitKey(1) & 0xFF  # 1ms만 대기 (non-blocking)
            
            if key == 27 or key == ord('q'):  # ESC 또는 'q'
                print("\n[INFO] 종료 키 입력.")
                break
            elif key == ord('s'):  # 's' 키: 스크린샷 저장
                filename = f"screenshot_{frame_count}.jpg"
                cv2.imwrite(filename, frame)
                print(f"[INFO] 스크린샷 저장: {filename}")
            
            # 윈도우 닫힘 감지
            try:
                if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                    print("\n[INFO] 윈도우가 닫혔습니다.")
                    break
            except cv2.error:
                break
    
    except KeyboardInterrupt:
        print("\n[INFO] Ctrl+C로 중단되었습니다.")
    
    except Exception as e:
        print(f"\n[ERROR] 예외 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # ========== 7. 정리 ==========
        print(f"\n[INFO] 총 처리 프레임: {frame_count}")
        cap.release()
        cv2.destroyAllWindows()
        print("[INFO] 정리 완료.")


if __name__ == "__main__":
    main()

