# -*- coding: utf-8 -*-
import numpy as np
import random


class DrivingLogic:
    """자율주행 판단 로직 클래스"""

    def decide_direction(self, binary_image, threshold, up_threshold):
        """
        이진화 이미지를 기반으로 주행 방향 결정
        """
        histogram = np.sum(binary_image, axis=0)
        length = len(histogram)

        # 6구역 분할
        divide = 6
        section_len = length // divide

        # 좌/우 영역 합계
        # 좌측 1/6
        left_sum = int(np.sum(histogram[:section_len]))
        # 우측 1/6
        right_sum = int(np.sum(histogram[(divide - 1) * section_len :]))

        # 중앙 영역 (1/6 ~ 3/6, 3/6 ~ 5/6)
        center_left = int(np.sum(histogram[1 * section_len : 3 * section_len]))
        center_right = int(np.sum(histogram[3 * section_len : 5 * section_len]))

        # 1. 좌우 차이가 큰 경우 (급커브)
        if abs(right_sum - left_sum) > threshold:
            return "LEFT" if right_sum > left_sum else "RIGHT"

        # 2. 전방이 막힌 경우 (라인 유실/끊김) -> 대체 경로 탐색 필요
        center_diff = abs(center_left - center_right)
        if center_diff < up_threshold:
            return "BLOCKED"

        return "UP"

    def analyze_alternative_path(self, binary_image):
        """
        막다른 길에서 180도 회전 후(또는 주변 탐색 후) 경로 분석
        """
        histogram = np.sum(binary_image, axis=0)
        length = len(histogram)

        # 3구역으로 단순화
        one_third = length // 3
        left = int(np.sum(histogram[:one_third]))
        center = int(np.sum(histogram[one_third : 2 * one_third]))
        right = int(np.sum(histogram[2 * one_third :]))

        # 중앙이 가장 비어있으면(값이 작으면 - 검은색이면?)
        # 아니, 여기서는 라인을 따라가야 함. 흰색이 라인임.
        # 값이 크면 라인이 있다는 것.
        # 원본 로직: left > center and right > center -> RIGHT
        # 즉 중앙보다 좌우에 라인이 많으면 RIGHT? (조금 이상하지만 원본 로직 따름)
        # 원본 주석: "중앙이 가장 비어있으면 (값이 작으면) 직진 가능" -> 이 코드는 라인이 흰색(255)이라고 가정.
        # 따라서 sum이 작으면 검은색(라인 없음).
        # 라인 트레이싱은 라인을 따라가는 것.
        # 원본 코드는 `process_frame`에서 threshold를 적용하므로 흰색이 라인.

        if left > center and right > center:
            return "RIGHT"

        return "LEFT"
