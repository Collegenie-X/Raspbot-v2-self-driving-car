#!/usr/bin/env python3
# coding: utf-8
import os
import time, sys
import cv2 as cv
import numpy as np
import tensorflow as tf
from numpy import random
from timeit import default_timer as timer
from tensorflow.compat.v1.keras import backend as K
from tensorflow.keras.layers import Input
from tensorflow.keras.layers import Lambda
from tensorflow.keras.models import Model
from PIL import ImageFont, ImageDraw, Image
from nets.yolo4_tiny import yolo_body, yolo_eval
from utils.utils import letterbox_image
from fps import FPS

gpus = tf.config.experimental.list_physical_devices(device_type="GPU")
for gpu in gpus:
    tf.config.experimental.set_memory_growth(gpu, True)
sys.path.append("/home/pi/software/oled_yahboom/")
from yahboom_oled import *


class garbage_identify:
    def __init__(self):
        # OLED 객체 생성
        self.oled = Yahboom_OLED(debug=False)
        self.oled.init_oled_process()  # OLED 프로세스 초기화
        self.oled.clear()
        self.oled.add_line("garbage_type:", 1)
        self.oled.add_line("None", 3)
        self.oled.refresh()
        self.score = 0.5
        self.iou = 0.3
        self.eager = False
        # 프레임레이트 통계 객체
        self.fps = FPS()
        self.anchors_path = "/home/pi/project_demo/08.AI_Visual_Interaction_Course/07.Garbage_identification_yolov4tiny/model_data/yolo_anchors.txt"
        self.classes_path = "/home/pi/project_demo/08.AI_Visual_Interaction_Course/07.Garbage_identification_yolov4tiny/model_data/garbage.txt"
        self.model_path = "/home/pi/project_demo/08.AI_Visual_Interaction_Course/07.Garbage_identification_yolov4tiny/model_data/garbage.h5"
        self.font_path = "/home/pi/project_demo/08.AI_Visual_Interaction_Course/07.Garbage_identification_yolov4tiny/font/Block_Simplified.TTF"
        self.class_names = self._get_class()
        self.anchors = self._get_anchors()
        self.model_image_size = (416, 416)
        if not self.eager:
            tf.compat.v1.disable_eager_execution()
            self.sess = K.get_session()
        self.generate()
        # 박스 그리기 위한 색상 설정
        self.colors = [
            [random.randint(0, 255) for _ in range(3)]
            for _ in range(len(self.class_names))
        ]
        self.garbage_index = 0

    def _get_class(self):
        """모든 분류 클래스 가져오기"""
        # 파일 경로 확장
        classes_path = os.path.expanduser(self.classes_path)
        # 파일을 열고 한 줄씩 읽기
        with open(classes_path) as f:
            class_names = f.readlines()
        # 라벨을 리스트에 저장
        class_names = [c.strip() for c in class_names]
        return class_names

    def _get_anchors(self):
        """모든 앵커 박스(선험적 박스) 가져오기"""
        anchors_path = os.path.expanduser(self.anchors_path)
        with open(anchors_path) as f:
            anchors = f.readline()
        anchors = [float(x) for x in anchors.split(",")]
        return np.array(anchors).reshape(-1, 2)

    def generate(self):
        """YOLO 모델 생성 및 가중치 로드"""
        model_path = os.path.expanduser(self.model_path)
        assert model_path.endswith(".h5"), "Keras model or weights must be a .h5 file."
        # 앵커 개수 계산
        num_anchors = len(self.anchors)
        num_classes = len(self.class_names)
        # 모델 로드: 기존 모델에 구조가 포함되어 있으면 직접 로드
        # 그렇지 않으면 먼저 모델을 구축한 후 로드
        self.yolo_model = yolo_body(
            Input(shape=(None, None, 3)), num_anchors // 2, num_classes
        )
        self.yolo_model.load_weights(self.model_path)
        print("{} model, anchors, and classes loaded.".format(model_path))
        if self.eager:
            self.input_image_shape = Input(
                [
                    2,
                ],
                batch_size=1,
            )
            inputs = [*self.yolo_model.output, self.input_image_shape]
            outputs = Lambda(
                yolo_eval,
                output_shape=(1,),
                name="yolo_eval",
                arguments={
                    "anchors": self.anchors,
                    "num_classes": len(self.class_names),
                    "frame_shape": self.model_image_size,
                    "score_threshold": self.score,
                    "eager": True,
                },
            )(inputs)
            self.yolo_model = Model(
                [self.yolo_model.input, self.input_image_shape], outputs
            )
        else:
            self.input_image_shape = K.placeholder(shape=(2,))
            self.boxes, self.scores, self.classes = yolo_eval(
                self.yolo_model.output,
                self.anchors,
                num_classes,
                self.input_image_shape,
                score_threshold=self.score,
                iou_threshold=self.iou,
            )

    def detect_image(self, image):
        """이미지에서 쓰레기 객체 검출"""
        # 이미지 포맷 변환: BGR to RGB
        image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
        # PIL Image 형식으로 변환
        image = Image.fromarray(np.uint8(image))
        # 입력 요구사항에 맞게 이미지 조정
        new_image_size = self.model_image_size
        boxed_image = letterbox_image(image, new_image_size)
        image_data = np.array(boxed_image, dtype="float32")
        image_data /= 255.0
        image_data = np.expand_dims(image_data, 0)  # 배치 차원 추가
        if self.eager:
            # 예측 수행 (Eager 모드)
            input_image_shape = np.expand_dims(
                np.array([image.size[1], image.size[0]], dtype="float32"), 0
            )
            out_boxes, out_scores, out_classes = self.yolo_model.predict(
                [image_data, input_image_shape]
            )
        else:
            # 예측 수행 (Graph 모드)
            out_boxes, out_scores, out_classes = self.sess.run(
                [self.boxes, self.scores, self.classes],
                feed_dict={
                    self.yolo_model.input: image_data,
                    self.input_image_shape: [image.size[1], image.size[0]],
                    #                     K.learning_phase(): 0
                },
            )
        msg = {}
        a = b = 0
        for i, c in list(enumerate(out_classes)):
            predicted_class = self.class_names[c]
            box = out_boxes[i]
            score = out_scores[i]
            top, left, bottom, right = box
            top = top - 5
            left = left - 5
            bottom = bottom + 5
            right = right + 5
            top = max(0, np.floor(top + 0.5).astype("int32"))
            left = max(0, np.floor(left + 0.5).astype("int32"))
            bottom = min(image.size[1], np.floor(bottom + 0.5).astype("int32"))
            right = min(image.size[0], np.floor(right + 0.5).astype("int32"))
            label = "{}: {:.2f}".format(predicted_class, score)
            label = label.encode("utf-8")
            # 바운딩 박스 중심점 계산
            x = (right + left) / 2
            y = (bottom + top) / 2
            r = 5
            # 그리기 객체 생성
            draw = ImageDraw.Draw(image)
            # 중심점에 원 그리기
            draw.ellipse((x - r, y - r, x + r, y + r), fill=tuple(self.colors[int(-i)]))
            # 바운딩 박스 그리기
            draw.rectangle(
                (left, top, right, bottom), outline=tuple(self.colors[int(i)]), width=10
            )
            # 폰트 설정
            fontStyle = ImageFont.truetype(self.font_path, size=35, encoding="utf-8")
            # 라벨 텍스트 그리기
            draw.text(
                (left, top - 40), str(label, "UTF-8"), fill=(255, 0, 0), font=fontStyle
            )
            labelstr = str(label, "UTF-8")
            self.oled.clear()
            self.oled.add_line("garbage_type:", 1)
            self.oled.add_line(labelstr, 3)
            self.oled.refresh()
            # 이미지 내 객체의 위치 계산
            #                 (a, b) = (round(((x - 320) / 4000), 5), round(((240 - y) / 3000 + 0.265) * 0.95, 5))
            (a, b) = (
                round(((x - 320) / 4000), 5),
                round(((480 - y) / 3000) * 0.8 + 0.19, 5),
            )
            msg[predicted_class] = (a, b)
            del draw
        if a == 0:
            self.oled.clear()
            self.oled.add_line("garbage_type:", 1)
            self.oled.add_line("None", 3)
            self.oled.refresh()
        end = timer()
        # print(end - start)
        image = cv.cvtColor(np.array(image), cv.COLOR_RGB2BGR)
        return image, msg

    def garbage_run(self, img):
        """
        쓰레기 인식 실행 함수
        :param img: 원본 이미지
        :return: 인식 후 이미지, 인식 정보(name, pos)
        """
        # 입력 이미지 크기 정규화
        img = cv.resize(img, (640, 480))
        txt0 = "Model-Loading..."
        msg = {}
        self.fps.update()
        self.fps.show_fps(img)
        if self.garbage_index < 3:
            cv.putText(img, txt0, (190, 50), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            self.garbage_index += 1
            return img, msg
        if self.garbage_index >= 3:
            # 메시지 컨테이너 생성
            try:
                img, msg = self.detect_image(img)  # 인식 메시지 획득
            except Exception:
                None  # print("get_pos NoneType")
            return img, msg
