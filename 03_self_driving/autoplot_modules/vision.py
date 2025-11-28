# -*- coding: utf-8 -*-
import cv2
import numpy as np


class CameraSystem:
    """카메라 초기화 및 프레임 캡처 클래스"""

    def __init__(self, device_id=0, width=320, height=240):
        self.cap = cv2.VideoCapture(device_id)

        # 해상도 설정
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        # 실제 적용된 해상도 확인
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        print(f"📷 카메라 초기화: {self.width}x{self.height}")

    def update_settings(
        self, brightness=None, contrast=None, saturation=None, gain=None
    ):
        """카메라 파라미터 업데이트"""
        if brightness is not None:
            self.cap.set(cv2.CAP_PROP_BRIGHTNESS, brightness)
        if contrast is not None:
            self.cap.set(cv2.CAP_PROP_CONTRAST, contrast)
        if saturation is not None:
            self.cap.set(cv2.CAP_PROP_SATURATION, saturation)
        if gain is not None:
            self.cap.set(cv2.CAP_PROP_GAIN, gain)

    def read(self):
        return self.cap.read()

    def release(self):
        self.cap.release()


class ImageProcessor:
    """이미지 처리 및 라인 검출 클래스"""

    def __init__(self, width, height):
        self.width = width
        self.height = height

    def weighted_gray(self, image, r_weight, g_weight, b_weight):
        """RGB 가중치를 적용한 그레이스케일 변환"""
        rw = r_weight / 100.0
        gw = g_weight / 100.0
        bw = b_weight / 100.0

        # BGR 이미지에서 각 채널 분리 및 가중합
        # cv2.addWeighted를 중첩 사용하는 것보다 numpy 연산이 명시적일 수 있으나
        # 성능을 위해 OpenCV 함수 사용 (기존 로직 유지)
        return cv2.addWeighted(
            cv2.addWeighted(image[:, :, 2], rw, image[:, :, 1], gw, 0),
            1.0,
            image[:, :, 0],
            bw,
            0,
        )

    def process(self, frame, params):
        """
        전체 이미지 처리 파이프라인
        params: 딕셔너리 형태의 파라미터 (roi_top, roi_bottom, weights, detect_value 등)
        """
        roi_top = params.get("roi_top", 0)
        roi_bottom = params.get("roi_bottom", 130)

        # ROI 좌표 변환 (0~1000 -> 0~height)
        top_y = int(roi_top * self.height / 1000)
        bottom_y = int(roi_bottom * self.height / 1000)

        top_y = max(0, min(top_y, self.height - 1))
        bottom_y = max(0, min(bottom_y, self.height - 1))

        if top_y >= bottom_y:
            top_y = max(0, bottom_y - 50)

        margin = 10

        # 투영 변환 좌표
        pts_src = np.float32(
            [
                [margin, bottom_y],  # 좌하
                [self.width - margin, bottom_y],  # 우하
                [self.width - margin, top_y],  # 우상
                [margin, top_y],  # 좌상
            ]
        )

        target_w, target_h = 320, 240
        pts_dst = np.float32(
            [[0, target_h], [target_w, target_h], [target_w, 0], [0, 0]]
        )

        # 1. ROI 시각화 (디버깅용)
        vis_frame = frame.copy()
        pts = pts_src.reshape((-1, 1, 2)).astype(np.int32)
        cv2.polylines(vis_frame, [pts], True, (0, 255, 0), 2)

        # 2. 원근 변환
        matrix = cv2.getPerspectiveTransform(pts_src, pts_dst)
        warped = cv2.warpPerspective(frame, matrix, (target_w, target_h))

        # 3. 그레이스케일
        gray = self.weighted_gray(
            warped,
            params.get("r_weight", 30),
            params.get("g_weight", 40),
            params.get("b_weight", 60),
        )

        # 4. 이진화
        _, binary = cv2.threshold(
            gray, params.get("detect_value", 120), 255, cv2.THRESH_BINARY
        )

        # 5. 모폴로지 (노이즈 제거)
        kernel = np.ones((5, 5), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

        return {
            "vis_frame": vis_frame,
            "warped": warped,
            "gray": gray,
            "binary": binary,
        }
