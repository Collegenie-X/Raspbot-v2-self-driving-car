# 참고 코드 예시    (autoplot_print.py)

import random
import time


# 충돌 여부 체크 함수
def check_collision(collisions):
    pass
    return collisions


# 차량 방향 결정 함수 (랜덤으로 직진, 좌회전, 우회전 중 선택)
def decide_direction(direction):
    pass


# 표지판 인식 함수 (랜덤으로 정지, 위험, 정상 중 하나 선택)
def recognize_sign(sign):
    pass


# 주행 상태 출력 함수 (현재 상태 출력)
def print_current_status(direction, sign, collisions):
    pass


# 차량 주행을 시작하는 함수
def car_mission():
    directions = ["up", "left", "right", "random"]  # 차량의 가능한 방향
    signs = ["stop", "danger", "no_sign", "o_sign"]  # 표지판 종류
    collisions = 0  # 충돌 횟수 초기화

    print("자율주행차 미션 시작!\n")

    # 20번의 주행 반복
    for i in range(20):
        time.sleep(0.5)  # 0.5초 간격으로 상태를 출력

        direction = random.choice(directions)  # 랜덤으로 방향을 결정
        sign = random.choice(signs)  # 랜덤으로 표지판을 인식

        # 10% 확률로 충돌 발생
        if random.random() < 0.1:
            collisions = check_collision(collisions)  # 충돌 체크

        # 충돌 횟수가 2번 이상이면 게임 종료
        if collisions >= 2:
            print("충돌이 2번 발생했습니다! 미션 종료!")
            break

        # 표지판에 따른 반응
        recognize_sign(sign)  # 표지판에 따른 반응

        # 차량 방향 결정 함수
        decide_direction(direction)  # 주행 방향 결정

        # 주행 상태 출력
        print_current_status(direction, sign, collisions)  # 주행 상태 출력

    else:
        # 20번의 주행을 마친 후 미션 완료
        print("\n미션 완료! 목적지에 도달했습니다.")


# 자율주행차 게임 시작
car_mission()
