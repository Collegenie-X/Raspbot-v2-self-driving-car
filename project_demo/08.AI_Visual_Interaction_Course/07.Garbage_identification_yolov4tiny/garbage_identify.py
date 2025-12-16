#!/usr/bin/env python3
# coding: utf-8
"""
YOLO v4 Tiny를 이용한 쓰레기 객체 인식 시스템

이 모듈은 실시간으로 카메라 영상에서 쓰레기를 감지하고 분류합니다.
- YOLOv4-Tiny 모델을 사용하여 빠른 추론 속도 제공
- OLED 디스플레이에 인식 결과 표시
- 바운딩 박스와 신뢰도 점수를 이미지에 표시
"""

# 기본 라이브러리
import os
import time, sys
import cv2 as cv
import numpy as np

# 딥러닝 프레임워크
import tensorflow as tf
from tensorflow.compat.v1.keras import backend as K
from tensorflow.keras.layers import Input, Lambda
from tensorflow.keras.models import Model

# 유틸리티 라이브러리
from numpy import random
from timeit import default_timer as timer
from PIL import ImageFont, ImageDraw, Image

# 커스텀 모듈
from nets.yolo4_tiny import yolo_body, yolo_eval
from utils.utils import letterbox_image
from fps import FPS

# GPU 메모리 동적 할당 설정 (OOM 에러 방지)
gpus = tf.config.experimental.list_physical_devices(device_type="GPU")
for gpu in gpus:
    tf.config.experimental.set_memory_growth(gpu, True)

# OLED 디스플레이 라이브러리 import
sys.path.append("/home/pi/software/oled_yahboom/")
from yahboom_oled import *


class garbage_identify:
    """
    YOLO v4 Tiny 기반 쓰레기 객체 인식 클래스

    주요 기능:
    - 실시간 쓰레기 객체 감지 및 분류
    - OLED 디스플레이에 인식 결과 표시
    - 바운딩 박스 및 신뢰도 점수 시각화
    - FPS(초당 프레임 수) 측정 및 표시

    알고리즘 흐름:
    1. 초기화: 모델 로드 및 설정
    2. 이미지 전처리: 크기 조정 및 정규화
    3. YOLO 추론: 객체 감지 실행
    4. 후처리: NMS(Non-Maximum Suppression) 적용
    5. 결과 시각화: 바운딩 박스 및 라벨 표시
    """

    def __init__(self):
        """
        쓰레기 인식 시스템 초기화

        초기화 단계:
        1. OLED 디스플레이 설정
        2. 모델 파라미터 설정 (신뢰도 임계값, IoU 임계값)
        3. 클래스 및 앵커 박스 로드
        4. YOLO 모델 생성 및 가중치 로드
        5. 시각화를 위한 색상 팔레트 생성
        """
        # ========== OLED 디스플레이 초기화 ==========
        # OLED 객체 생성 (디버그 모드 비활성화)
        self.oled = Yahboom_OLED(debug=False)
        self.oled.init_oled_process()  # OLED 프로세스 초기화
        self.oled.clear()  # 화면 초기화
        # 초기 메시지 표시
        self.oled.add_line("garbage_type:", 1)  # 1번째 줄: 타이틀
        self.oled.add_line("None", 3)  # 3번째 줄: 현재 상태
        self.oled.refresh()  # 화면 업데이트

        # ========== YOLO 모델 파라미터 설정 ==========
        # 객체 감지 신뢰도 임계값 (0.5 이상일 때만 객체로 인식)
        self.score = 0.5
        # IoU(Intersection over Union) 임계값 (NMS에 사용)
        # 두 박스의 겹침이 0.3 이상이면 중복으로 판단
        self.iou = 0.3
        # Eager Execution 모드 설정 (False: Graph 모드 사용)
        self.eager = False

        # ========== FPS 측정 객체 초기화 ==========
        # 프레임레이트 통계를 위한 객체
        self.fps = FPS()

        # ========== 모델 파일 경로 설정 ==========
        # 앵커 박스 좌표 파일 경로
        self.anchors_path = "/home/pi/project_demo/08.AI_Visual_Interaction_Course/07.Garbage_identification_yolov4tiny/model_data/yolo_anchors.txt"
        # 객체 클래스 이름 파일 경로
        self.classes_path = "/home/pi/project_demo/08.AI_Visual_Interaction_Course/07.Garbage_identification_yolov4tiny/model_data/garbage.txt"
        # 학습된 모델 가중치 파일 경로
        self.model_path = "/home/pi/project_demo/08.AI_Visual_Interaction_Course/07.Garbage_identification_yolov4tiny/model_data/garbage.h5"
        # 한글 폰트 파일 경로 (라벨 표시용)
        self.font_path = "/home/pi/project_demo/08.AI_Visual_Interaction_Course/07.Garbage_identification_yolov4tiny/font/Block_Simplified.TTF"

        # ========== 클래스 및 앵커 로드 ==========
        # 감지할 객체 클래스 목록 로드
        self.class_names = self._get_class()
        # YOLO 앵커 박스 좌표 로드
        self.anchors = self._get_anchors()

        # ========== 모델 입력 이미지 크기 설정 ==========
        # YOLO 모델의 입력 이미지 크기 (정사각형)
        self.model_image_size = (416, 416)

        # ========== TensorFlow 세션 설정 ==========
        if not self.eager:
            # Graph 모드 사용 시 Eager Execution 비활성화
            tf.compat.v1.disable_eager_execution()
            # Keras 백엔드 세션 가져오기
            self.sess = K.get_session()

        # ========== YOLO 모델 생성 ==========
        # 모델 구조 생성 및 가중치 로드
        self.generate()

        # ========== 시각화 색상 팔레트 생성 ==========
        # 각 클래스마다 고유한 색상 할당 (랜덤 RGB 값)
        self.colors = [
            [random.randint(0, 255) for _ in range(3)]
            for _ in range(len(self.class_names))
        ]

        # ========== 초기화 카운터 ==========
        # 모델 로딩 완료를 위한 카운터 (초기 3프레임 대기)
        self.garbage_index = 0

    def _get_class(self):
        """
        객체 분류 클래스 목록 로드

        이 메서드는 텍스트 파일에서 인식할 객체의 클래스 이름을 읽어옵니다.
        예: cardboard(골판지), glass(유리), metal(금속), paper(종이), plastic(플라스틱) 등

        처리 과정:
        1. 파일 경로 확장 (~를 홈 디렉토리로 변환)
        2. 파일을 열고 모든 줄 읽기
        3. 각 줄의 공백 제거 (strip)
        4. 클래스 이름 리스트 반환

        Returns:
            list: 객체 클래스 이름 리스트 (예: ['cardboard', 'glass', 'metal', ...])
        """
        # 파일 경로 확장 (틸다 기호 등을 실제 경로로 변환)
        classes_path = os.path.expanduser(self.classes_path)

        # 파일을 열고 한 줄씩 읽기
        with open(classes_path) as f:
            class_names = f.readlines()

        # 각 줄에서 불필요한 공백 및 개행 문자 제거
        class_names = [c.strip() for c in class_names]

        return class_names

    def _get_anchors(self):
        """
        YOLO 앵커 박스 좌표 로드

        앵커 박스(Anchor Box)란?
        - YOLO가 객체를 감지할 때 사용하는 사전 정의된 박스 크기
        - 학습 데이터의 객체 크기 분포를 기반으로 K-means 클러스터링으로 생성
        - 다양한 크기와 비율의 객체를 효율적으로 감지하기 위해 사용

        처리 과정:
        1. 앵커 파일 경로 확장
        2. 파일에서 앵커 좌표 읽기 (형식: w1,h1,w2,h2,...)
        3. 문자열을 float 배열로 변환
        4. (N, 2) 형태로 재구성 (각 행이 [width, height])

        Returns:
            numpy.ndarray: 앵커 박스 좌표 배열 (shape: [num_anchors, 2])
                          예: [[10, 13], [16, 30], [33, 23], ...]
        """
        # 파일 경로 확장
        anchors_path = os.path.expanduser(self.anchors_path)

        # 파일의 첫 번째 줄 읽기 (앵커 좌표는 한 줄에 저장됨)
        with open(anchors_path) as f:
            anchors = f.readline()

        # 쉼표로 구분된 문자열을 float 리스트로 변환
        anchors = [float(x) for x in anchors.split(",")]

        # 1차원 배열을 (N, 2) 형태로 재구성
        # -1은 자동으로 행 개수 계산, 2는 [width, height] 쌍
        return np.array(anchors).reshape(-1, 2)

    def generate(self):
        """
        YOLO v4 Tiny 모델 생성 및 가중치 로드

        이 메서드는 객체 감지를 위한 신경망 모델을 구축합니다.

        모델 구조:
        - YOLOv4-Tiny: 경량화된 YOLO 버전 (라즈베리파이에서 실행 가능)
        - 입력: (416, 416, 3) RGB 이미지
        - 출력: 바운딩 박스, 신뢰도 점수, 클래스 확률

        처리 과정:
        1. 모델 파일 경로 검증 (.h5 파일인지 확인)
        2. YOLO 모델 구조 생성
        3. 사전 학습된 가중치 로드
        4. 실행 모드에 따라 후처리 레이어 구성
           - Eager 모드: 즉시 실행 (디버깅 용이)
           - Graph 모드: 그래프 최적화 (속도 향상)
        5. yolo_eval 함수로 후처리 파이프라인 구성
           (NMS, 신뢰도 필터링 등)

        Raises:
            AssertionError: 모델 파일이 .h5 형식이 아닌 경우
        """
        # ========== 모델 경로 검증 ==========
        model_path = os.path.expanduser(self.model_path)
        # Keras 모델은 반드시 .h5 형식이어야 함
        assert model_path.endswith(".h5"), "Keras model or weights must be a .h5 file."

        # ========== 모델 파라미터 계산 ==========
        # 앵커 박스 개수 계산
        num_anchors = len(self.anchors)
        # 감지할 객체 클래스 개수
        num_classes = len(self.class_names)

        # ========== YOLO 모델 구조 생성 ==========
        # yolo_body: YOLOv4-Tiny의 신경망 구조 생성
        # Input(shape=(None, None, 3)): 가변 크기 입력 지원 (높이, 너비, 채널)
        # num_anchors // 2: Tiny 버전은 앵커를 절반만 사용
        self.yolo_model = yolo_body(
            Input(shape=(None, None, 3)), num_anchors // 2, num_classes
        )

        # ========== 사전 학습된 가중치 로드 ==========
        # 쓰레기 데이터셋으로 학습된 가중치 파일 로드
        self.yolo_model.load_weights(self.model_path)
        print("{} model, anchors, and classes loaded.".format(model_path))

        # ========== 실행 모드별 후처리 구성 ==========
        if self.eager:
            # ===== Eager Execution 모드 =====
            # 즉시 실행 모드: 디버깅과 프로토타이핑에 유용

            # 입력 이미지 크기를 위한 플레이스홀더
            self.input_image_shape = Input(
                [
                    2,
                ],  # [height, width]
                batch_size=1,
            )

            # 모델 출력과 이미지 크기를 결합
            inputs = [*self.yolo_model.output, self.input_image_shape]

            # Lambda 레이어로 yolo_eval 함수 래핑
            # yolo_eval: YOLO 출력을 해석하고 후처리 수행
            outputs = Lambda(
                yolo_eval,
                output_shape=(1,),
                name="yolo_eval",
                arguments={
                    "anchors": self.anchors,  # 앵커 박스 좌표
                    "num_classes": len(self.class_names),  # 클래스 개수
                    "frame_shape": self.model_image_size,  # 모델 입력 크기
                    "score_threshold": self.score,  # 신뢰도 임계값
                    "eager": True,  # Eager 모드 활성화
                },
            )(inputs)

            # 전체 모델 재구성 (입력부터 출력까지)
            self.yolo_model = Model(
                [self.yolo_model.input, self.input_image_shape], outputs
            )
        else:
            # ===== Graph Execution 모드 (기본값) =====
            # 그래프 실행 모드: 최적화된 성능, 프로덕션 환경에 적합

            # 이미지 크기를 위한 플레이스홀더 생성
            self.input_image_shape = K.placeholder(shape=(2,))

            # yolo_eval 함수 직접 호출하여 후처리 수행
            # 반환값: (boxes, scores, classes)
            # - boxes: 바운딩 박스 좌표 [y1, x1, y2, x2]
            # - scores: 각 박스의 신뢰도 점수
            # - classes: 각 박스의 클래스 인덱스
            self.boxes, self.scores, self.classes = yolo_eval(
                self.yolo_model.output,  # YOLO 모델의 원시 출력
                self.anchors,  # 앵커 박스 좌표
                num_classes,  # 클래스 개수
                self.input_image_shape,  # 원본 이미지 크기
                score_threshold=self.score,  # 신뢰도 임계값 (낮은 점수 제거)
                iou_threshold=self.iou,  # IoU 임계값 (NMS에 사용)
            )

    def detect_image(self, image):
        """
        이미지에서 쓰레기 객체 검출 및 시각화

        이 메서드는 YOLO 모델을 사용하여 이미지에서 쓰레기를 감지하고
        바운딩 박스와 라벨을 그려 결과를 시각화합니다.

        알고리즘 단계:
        1. 전처리: 이미지 색상 변환 및 크기 조정
        2. 정규화: 픽셀 값을 [0, 1] 범위로 변환
        3. 추론: YOLO 모델로 객체 감지 수행
        4. 후처리: 바운딩 박스 좌표 계산 및 조정
        5. 시각화: 박스, 라벨, 신뢰도 점수 표시
        6. OLED 업데이트: 감지된 객체 정보 표시

        Args:
            image: OpenCV 형식의 입력 이미지 (BGR)

        Returns:
            tuple: (처리된 이미지, 감지 정보 딕셔너리)
                  - 이미지: 바운딩 박스가 그려진 BGR 이미지
                  - 딕셔너리: {클래스명: (x_norm, y_norm)} 형태
        """
        # ========== 1단계: 이미지 전처리 ==========
        # OpenCV는 BGR, YOLO는 RGB를 사용하므로 변환 필요
        image = cv.cvtColor(image, cv.COLOR_BGR2RGB)

        # PIL Image 형식으로 변환 (letterbox_image 함수 호환성)
        image = Image.fromarray(np.uint8(image))

        # ========== 2단계: 이미지 크기 조정 ==========
        # letterbox_image: 종횡비를 유지하며 패딩 추가
        # (416, 416) 크기로 조정하되 이미지 왜곡 방지
        new_image_size = self.model_image_size
        boxed_image = letterbox_image(image, new_image_size)

        # NumPy 배열로 변환 (모델 입력 형식)
        image_data = np.array(boxed_image, dtype="float32")

        # ========== 3단계: 정규화 ==========
        # 픽셀 값을 [0, 255] 범위에서 [0, 1] 범위로 변환
        # 신경망 학습 시 사용한 정규화 방식과 동일하게 적용
        image_data /= 255.0

        # 배치 차원 추가: (416, 416, 3) -> (1, 416, 416, 3)
        image_data = np.expand_dims(image_data, 0)

        # ========== 4단계: YOLO 추론 실행 ==========
        if self.eager:
            # ===== Eager 모드 추론 =====
            # 원본 이미지 크기 정보 준비
            input_image_shape = np.expand_dims(
                np.array([image.size[1], image.size[0]], dtype="float32"), 0
            )
            # 모델 예측 수행
            out_boxes, out_scores, out_classes = self.yolo_model.predict(
                [image_data, input_image_shape]
            )
        else:
            # ===== Graph 모드 추론 (기본값) =====
            # TensorFlow 세션을 통해 그래프 실행
            # feed_dict: 입력 텐서에 실제 데이터 전달
            out_boxes, out_scores, out_classes = self.sess.run(
                [self.boxes, self.scores, self.classes],  # 출력 텐서
                feed_dict={
                    self.yolo_model.input: image_data,  # 모델 입력
                    self.input_image_shape: [image.size[1], image.size[0]],  # 원본 크기
                    # K.learning_phase(): 0  # 추론 모드 (학습 모드 아님)
                },
            )
        # ========== 5단계: 후처리 및 시각화 ==========
        # 감지 결과를 저장할 딕셔너리
        msg = {}
        # 객체 감지 여부 확인용 변수 초기화
        a = b = 0

        # 감지된 모든 객체에 대해 반복
        for i, c in list(enumerate(out_classes)):
            # ===== 5-1. 감지 정보 추출 =====
            # 클래스 이름 가져오기 (예: 'plastic', 'paper')
            predicted_class = self.class_names[c]
            # 바운딩 박스 좌표 [top, left, bottom, right]
            box = out_boxes[i]
            # 신뢰도 점수 (0.0 ~ 1.0)
            score = out_scores[i]

            # ===== 5-2. 바운딩 박스 좌표 조정 =====
            # YOLO 출력 좌표 분리
            top, left, bottom, right = box

            # 박스를 약간 확장 (시각적 여유 공간)
            top = top - 5
            left = left - 5
            bottom = bottom + 5
            right = right + 5

            # 정수 좌표로 변환 및 이미지 경계 내로 제한
            # max(0, ...): 음수 좌표 방지
            # min(image.size, ...): 이미지 범위 초과 방지
            top = max(0, np.floor(top + 0.5).astype("int32"))
            left = max(0, np.floor(left + 0.5).astype("int32"))
            bottom = min(image.size[1], np.floor(bottom + 0.5).astype("int32"))
            right = min(image.size[0], np.floor(right + 0.5).astype("int32"))

            # ===== 5-3. 라벨 텍스트 생성 =====
            # 형식: "클래스명: 신뢰도점수"
            # 예: "plastic: 0.95"
            label = "{}: {:.2f}".format(predicted_class, score)
            # UTF-8 인코딩 (한글 폰트 지원)
            label = label.encode("utf-8")

            # ===== 5-4. 바운딩 박스 중심점 계산 =====
            # 객체의 중심 좌표 (로봇 제어에 사용 가능)
            x = (right + left) / 2
            y = (bottom + top) / 2
            r = 5  # 중심점 원의 반지름

            # ===== 5-5. 시각화 그리기 =====
            # PIL ImageDraw 객체 생성
            draw = ImageDraw.Draw(image)

            # 중심점에 원 그리기 (객체 중심 표시)
            draw.ellipse(
                (x - r, y - r, x + r, y + r),
                fill=tuple(self.colors[int(-i)]),  # 클래스별 고유 색상
            )

            # 바운딩 박스 사각형 그리기
            draw.rectangle(
                (left, top, right, bottom),
                outline=tuple(self.colors[int(i)]),  # 클래스별 고유 색상
                width=10,  # 선 두께
            )

            # ===== 5-6. 라벨 텍스트 그리기 =====
            # 한글 폰트 로드 (크기: 35)
            fontStyle = ImageFont.truetype(self.font_path, size=35, encoding="utf-8")

            # 바운딩 박스 위에 라벨 텍스트 표시
            draw.text(
                (left, top - 40),  # 박스 위쪽에 위치
                str(label, "UTF-8"),  # 디코딩
                fill=(255, 0, 0),  # 빨간색 텍스트
                font=fontStyle,
            )

            # ===== 5-7. OLED 디스플레이 업데이트 =====
            # 감지된 객체 정보를 OLED에 표시
            labelstr = str(label, "UTF-8")
            self.oled.clear()  # 화면 초기화
            self.oled.add_line("garbage_type:", 1)  # 타이틀
            self.oled.add_line(labelstr, 3)  # 감지 정보
            self.oled.refresh()  # 화면 업데이트

            # ===== 5-8. 객체 위치 정규화 =====
            # 로봇 팔 제어를 위한 정규화된 좌표 계산
            # (x, y) -> (a, b): 이미지 좌표를 로봇 좌표계로 변환
            #
            # 변환 공식 설명:
            # a: 수평 위치 정규화
            #    - (x - 320): 이미지 중심(320)을 기준으로 상대 좌표
            #    - / 4000: 스케일링 팩터
            # b: 수직 위치 정규화
            #    - (480 - y): Y축 반전 (이미지는 위에서 아래, 로봇은 아래에서 위)
            #    - / 3000 * 0.8 + 0.19: 스케일링 및 오프셋 조정
            (a, b) = (
                round(((x - 320) / 4000), 5),  # 수평 위치
                round(((480 - y) / 3000) * 0.8 + 0.19, 5),  # 수직 위치
            )

            # 감지 결과를 딕셔너리에 저장
            # 키: 클래스 이름, 값: 정규화된 좌표
            msg[predicted_class] = (a, b)

            # 메모리 절약을 위해 draw 객체 삭제
            del draw

        # ========== 6단계: 객체 미감지 처리 ==========
        # a가 0이면 객체가 감지되지 않음
        if a == 0:
            self.oled.clear()
            self.oled.add_line("garbage_type:", 1)
            self.oled.add_line("None", 3)  # "None" 표시
            self.oled.refresh()

        # ========== 7단계: 처리 시간 측정 (선택적) ==========
        end = timer()
        # print(end - start)  # 추론 시간 출력 (디버깅용)

        # ========== 8단계: 이미지 포맷 복원 ==========
        # PIL Image -> NumPy 배열 변환
        # RGB -> BGR 변환 (OpenCV 형식으로 복원)
        image = cv.cvtColor(np.array(image), cv.COLOR_RGB2BGR)

        # 처리된 이미지와 감지 정보 반환
        return image, msg

    def garbage_run(self, img):
        """
        쓰레기 인식 실행 메인 함수

        이 메서드는 외부에서 호출되는 메인 인터페이스입니다.
        카메라로부터 받은 프레임을 처리하고 객체 감지 결과를 반환합니다.

        동작 방식:
        1. 이미지 크기를 표준 해상도로 조정
        2. FPS 정보 업데이트 및 표시
        3. 초기 로딩 단계 (3프레임) 처리
        4. 모델 로딩 완료 후 실제 객체 감지 수행

        초기 로딩 단계가 필요한 이유:
        - 첫 추론 시 GPU/모델 초기화 시간 소요
        - 안정적인 추론을 위한 워밍업 기간
        - 사용자에게 로딩 상태 피드백 제공

        Args:
            img (numpy.ndarray): 입력 이미지 (OpenCV BGR 형식)

        Returns:
            tuple: (처리된 이미지, 감지 정보)
                  - img: 바운딩 박스와 FPS가 표시된 이미지
                  - msg: {클래스명: (x, y)} 형태의 감지 정보 딕셔너리
        """
        # ========== 1단계: 이미지 크기 정규화 ==========
        # 모든 입력을 표준 해상도 (640x480)로 조정
        # 이유: 일관된 처리 성능 및 좌표 계산의 정확성
        img = cv.resize(img, (640, 480))

        # ========== 2단계: 초기화 ==========
        # 로딩 메시지 텍스트
        txt0 = "Model-Loading..."
        # 감지 결과를 저장할 빈 딕셔너리
        msg = {}

        # ========== 3단계: FPS 업데이트 및 표시 ==========
        # FPS 카운터 업데이트
        self.fps.update()
        # 이미지에 현재 FPS 정보 표시
        self.fps.show_fps(img)

        # ========== 4단계: 초기 로딩 단계 처리 ==========
        if self.garbage_index < 3:
            # 첫 3프레임 동안은 모델 로딩 메시지만 표시
            # 이유: 모델의 첫 추론은 초기화 시간이 필요하므로
            #      안정화를 위해 대기
            cv.putText(
                img,  # 대상 이미지
                txt0,  # 표시할 텍스트
                (190, 50),  # 텍스트 위치 (x, y)
                cv.FONT_HERSHEY_SIMPLEX,  # 폰트 종류
                1,  # 폰트 크기
                (0, 0, 255),  # 빨간색 (BGR)
                2,  # 선 두께
            )
            # 로딩 카운터 증가
            self.garbage_index += 1
            # 빈 결과 반환 (아직 감지 안 함)
            return img, msg

        # ========== 5단계: 실제 객체 감지 수행 ==========
        if self.garbage_index >= 3:
            # 로딩 완료 후 실제 감지 실행
            try:
                # detect_image 호출하여 객체 감지 수행
                # 반환값: 바운딩 박스가 그려진 이미지, 감지 정보
                img, msg = self.detect_image(img)
            except Exception:
                # 예외 발생 시 무시 (예: 프레임 손실, 메모리 부족 등)
                # 프로덕션 환경에서는 로깅 추가 권장
                None  # print("get_pos NoneType")  # 디버깅용 (주석 처리됨)

            # 처리된 이미지와 감지 정보 반환
            return img, msg
