"""
Non-blocking 방식 카메라 프로그램 (개선된 버전)

이 프로그램의 장점:
1. waitKey(1)로 1ms만 대기하고 즉시 다음 프레임
2. 키 입력 없어도 계속 프레임 업데이트
3. 실시간 동영상처럼 부드럽게 작동

실행 방법:
    python nonblocking_example.py
    
실행 후:
    - 화면이 실시간으로 계속 업데이트됨
    - 언제든 'q'를 누르면 즉시 종료
    - 부드러운 영상을 경험해보세요!
"""

import cv2
import time

def main():
    print("=" * 60)
    print("🟢 Non-blocking 방식 카메라 프로그램")
    print("=" * 60)
    print("\n[안내]")
    print("  - 화면이 실시간으로 계속 업데이트됩니다")
    print("  - 'q' 키를 누르면 즉시 종료됩니다")
    print("  - 's' 키를 누르면 스크린샷을 저장합니다")
    print("  - 부드러운 영상을 경험해보세요!\n")
    
    # 카메라 초기화
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("[ERROR] 카메라를 열 수 없습니다.")
        return
    
    # 해상도 설정
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    
    window_name = "Non-blocking Example - 실시간 영상"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    frame_count = 0
    start_time = time.time()
    last_fps_time = start_time
    fps = 0
    
    print("[시작] 카메라 작동 시작...\n")
    
    try:
        while True:
            # 프레임 읽기
            ret, frame = cap.read()
            
            if not ret:
                print("[WARN] 프레임을 읽지 못했습니다.")
                break
            
            frame_count += 1
            
            # FPS 계산 (1초마다)
            current_time = time.time()
            if current_time - last_fps_time >= 1.0:
                fps = frame_count / (current_time - start_time)
                last_fps_time = current_time
            
            # 프레임에 정보 표시
            cv2.putText(
                frame,
                f"Frame: {frame_count}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )
            
            cv2.putText(
                frame,
                f"FPS: {fps:.2f}",
                (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )
            
            cv2.putText(
                frame,
                "Press 'q' to quit | 's' to save",
                (10, 110),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 255),
                1
            )
            
            # 상태 표시
            cv2.putText(
                frame,
                "Status: RUNNING (Non-blocking)",
                (10, 140),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1
            )
            
            # 화면에 표시
            cv2.imshow(window_name, frame)
            
            # ✅ 개선된 코드: 1ms만 대기하고 바로 다음으로
            key = cv2.waitKey(1) & 0xFF  # 1ms만 대기 (NON-BLOCKING!)
            
            # 키 입력 처리
            if key == ord('q'):
                print(f"\n[종료] 'q' 키 입력 (프레임 {frame_count})")
                break
            elif key == ord('s'):
                filename = f"screenshot_frame_{frame_count}.jpg"
                cv2.imwrite(filename, frame)
                print(f"[저장] {filename} 저장 완료!")
            
            # key가 255 (0xFF)이면 키 입력 없음 → 다음 프레임으로 계속!
    
    except KeyboardInterrupt:
        print("\n[종료] Ctrl+C로 중단되었습니다.")
    
    finally:
        # 종료 처리
        elapsed_time = time.time() - start_time
        
        print("\n" + "=" * 60)
        print("📊 통계")
        print("=" * 60)
        print(f"총 프레임 수: {frame_count}")
        print(f"총 실행 시간: {elapsed_time:.2f}초")
        
        if frame_count > 0 and elapsed_time > 0:
            avg_time = elapsed_time / frame_count
            fps = frame_count / elapsed_time
            print(f"프레임당 평균 시간: {avg_time:.4f}초")
            print(f"평균 FPS: {fps:.2f}")
            print(f"\n💡 분석: Non-blocking 방식으로 부드러운 실시간 영상을 구현했습니다!")
        
        cap.release()
        cv2.destroyAllWindows()
        print("\n[완료] 프로그램 종료\n")


if __name__ == "__main__":
    main()

