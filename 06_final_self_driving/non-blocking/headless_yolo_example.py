"""
Headless YOLO 예제
디스플레이 없는 환경에서 YOLO를 실행하는 완전한 예제

특징:
- cv2.imshow() 사용하지 않음
- 결과를 파일로 저장
- 실시간 통계 출력
- 안전한 종료 처리

실행 방법:
    python headless_yolo_example.py
    
종료 방법:
    - Ctrl+C
    - 또는 다른 터미널에서: touch stop.txt
"""

import cv2
import os
import time
from datetime import datetime

# YOLO 모델 임포트 시도
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    print("[WARN] ultralytics 라이브러리가 설치되지 않았습니다.")
    print("       pip install ultralytics")
    YOLO_AVAILABLE = False


class HeadlessYOLO:
    """
    Headless 환경에서 YOLO를 실행하는 클래스
    """
    
    def __init__(self, model_path='yolov8n.pt', camera_id=0):
        """
        초기화
        
        Args:
            model_path: YOLO 모델 파일 경로
            camera_id: 카메라 ID (0, 1, 2, ...)
        """
        print("=" * 70)
        print("🤖 Headless YOLO 시작")
        print("=" * 70)
        
        # 모델 로드
        if YOLO_AVAILABLE:
            print(f"\n[1/3] YOLO 모델 로딩: {model_path}")
            try:
                self.model = YOLO(model_path)
                print("      ✅ 모델 로드 완료")
            except Exception as e:
                print(f"      ❌ 모델 로드 실패: {e}")
                print(f"      → 기본 모델(yolov8n.pt)을 다운로드합니다...")
                self.model = YOLO('yolov8n.pt')
        else:
            self.model = None
            print("      ⚠️  YOLO 모델 없이 실행 (테스트 모드)")
        
        # 카메라 초기화
        print(f"\n[2/3] 카메라 초기화: ID {camera_id}")
        self.cap = cv2.VideoCapture(camera_id)
        
        if not self.cap.isOpened():
            print(f"      ❌ 카메라를 열 수 없습니다.")
            raise RuntimeError("카메라 초기화 실패")
        
        # 해상도 설정
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        print("      ✅ 카메라 준비 완료")
        
        # 출력 디렉토리 생성
        print("\n[3/3] 출력 디렉토리 설정")
        self.output_dir = 'headless_output'
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"      ✅ 출력 폴더: {self.output_dir}/")
        
        # 통계 변수
        self.frame_count = 0
        self.start_time = time.time()
        self.last_save_time = time.time()
        
        print("\n" + "=" * 70)
        print("✅ 초기화 완료!")
        print("=" * 70)
    
    def process_frame(self, frame):
        """
        프레임 처리 (YOLO 추론)
        
        Args:
            frame: OpenCV 이미지 (BGR)
            
        Returns:
            annotated_frame: 결과가 그려진 이미지
            detections: 감지된 객체 수
        """
        if self.model is None:
            # YOLO 없이 테스트
            annotated = frame.copy()
            cv2.putText(
                annotated,
                'TEST MODE (No YOLO)',
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )
            return annotated, 0
        
        # YOLO 추론
        results = self.model(frame, verbose=False)
        
        # 결과 그리기
        annotated = results[0].plot()
        
        # 감지된 객체 수
        detections = len(results[0].boxes)
        
        return annotated, detections
    
    def add_info_overlay(self, frame):
        """
        프레임에 정보 오버레이 추가
        
        Args:
            frame: OpenCV 이미지
            
        Returns:
            frame: 정보가 추가된 이미지
        """
        # FPS 계산
        elapsed = time.time() - self.start_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0
        
        # 현재 시각
        current_time = datetime.now().strftime('%H:%M:%S')
        
        # 배경 (반투명 검은색 상자)
        overlay = frame.copy()
        cv2.rectangle(overlay, (5, 5), (350, 120), (0, 0, 0), -1)
        frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
        
        # 텍스트 추가
        y_offset = 30
        infos = [
            f'Frame: {self.frame_count}',
            f'FPS: {fps:.2f}',
            f'Time: {current_time}',
            f'Mode: HEADLESS'
        ]
        
        for i, info in enumerate(infos):
            cv2.putText(
                frame,
                info,
                (10, y_offset + i * 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )
        
        return frame
    
    def save_frame(self, frame, prefix='frame'):
        """
        프레임을 파일로 저장
        
        Args:
            frame: OpenCV 이미지
            prefix: 파일명 접두사
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{prefix}_{timestamp}_{self.frame_count:06d}.jpg'
        filepath = os.path.join(self.output_dir, filename)
        
        cv2.imwrite(filepath, frame)
        return filename
    
    def should_stop(self):
        """
        종료 조건 확인
        
        Returns:
            True: 종료해야 함
            False: 계속 실행
        """
        # stop.txt 파일이 있으면 종료
        if os.path.exists('stop.txt'):
            print("\n[INFO] stop.txt 파일 감지")
            return True
        
        return False
    
    def run(self, save_interval=30, max_frames=None):
        """
        메인 루프 실행
        
        Args:
            save_interval: 프레임 저장 간격 (프레임 수)
            max_frames: 최대 프레임 수 (None이면 무제한)
        """
        print("\n💡 사용 방법:")
        print("   - 현재 프레임: headless_output/current_frame.jpg")
        print("   - 저장 간격: 30프레임마다 별도 저장")
        print("   - 종료: Ctrl+C 또는 'touch stop.txt'")
        print("\n[시작] 처리 시작...\n")
        
        try:
            while True:
                # 프레임 읽기
                ret, frame = self.cap.read()
                
                if not ret:
                    print("[WARN] 프레임을 읽을 수 없습니다.")
                    break
                
                self.frame_count += 1
                
                # YOLO 처리
                annotated, detections = self.process_frame(frame)
                
                # 정보 오버레이
                annotated = self.add_info_overlay(annotated)
                
                # 현재 프레임 저장 (덮어쓰기)
                current_path = os.path.join(self.output_dir, 'current_frame.jpg')
                cv2.imwrite(current_path, annotated)
                
                # 주기적으로 별도 저장
                if self.frame_count % save_interval == 0:
                    filename = self.save_frame(annotated, 'detection')
                    
                    # 통계 출력
                    elapsed = time.time() - self.start_time
                    fps = self.frame_count / elapsed
                    
                    print(f"[프레임 {self.frame_count:06d}] "
                          f"FPS: {fps:.2f} | "
                          f"감지: {detections}개 | "
                          f"저장: {filename}")
                
                # 종료 조건 체크
                if self.should_stop():
                    print("[종료] 종료 조건 감지")
                    break
                
                if max_frames and self.frame_count >= max_frames:
                    print(f"[종료] 최대 프레임 수({max_frames}) 도달")
                    break
                
                # CPU 부담 감소
                time.sleep(0.01)
        
        except KeyboardInterrupt:
            print("\n[종료] Ctrl+C로 중단")
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """정리 작업"""
        print("\n" + "=" * 70)
        print("📊 최종 통계")
        print("=" * 70)
        
        elapsed = time.time() - self.start_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0
        
        print(f"총 프레임: {self.frame_count}")
        print(f"실행 시간: {elapsed:.2f}초")
        print(f"평균 FPS: {fps:.2f}")
        print(f"출력 폴더: {self.output_dir}/")
        
        self.cap.release()
        
        # stop.txt 삭제
        if os.path.exists('stop.txt'):
            os.remove('stop.txt')
            print("\nstop.txt 파일 삭제됨")
        
        print("\n✅ 종료 완료")


def main():
    """메인 함수"""
    # stop.txt 파일 삭제 (이전 실행 잔여물)
    if os.path.exists('stop.txt'):
        os.remove('stop.txt')
    
    # Headless YOLO 실행
    try:
        # 모델 경로 확인 (없으면 자동 다운로드)
        yolo = HeadlessYOLO(
            model_path='yolov8n.pt',  # 또는 'best.pt' 등
            camera_id=0
        )
        
        # 실행
        yolo.run(
            save_interval=30,   # 30프레임마다 저장
            max_frames=None     # 무제한 (None) 또는 숫자 (예: 300)
        )
        
    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

