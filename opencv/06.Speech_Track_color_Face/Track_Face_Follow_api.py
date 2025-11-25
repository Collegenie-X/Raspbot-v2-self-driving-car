#导入Raspbot驱动库 Import the Raspbot library
from McLumk_Wheel_Sports import *
# 创建Rosmaster对象 Facebot Create the Rosmaster object Facebot
Facebot = Raspbot()

import cv2
import mediapipe as mp
import math
import PID


yservo_pid = PID.PositionalPID(0.8, 0.2, 0.01)
direction_pid = PID.PositionalPID(0.2, 0, 0.002)
speed_pid = PID.PositionalPID(0.01, 0,0.0001)
area_center = 4000 #面积大小
MIN_Speed = 5


# 控制电机运动 Control motor movement
def run_motor(M1,M2,M3,M4):  #-255~255
    Facebot.Ctrl_Muto(0, M1)
    Facebot.Ctrl_Muto(1, M2)
    Facebot.Ctrl_Muto(2, M3)
    Facebot.Ctrl_Muto(3, M4)
    
def limit_max_vlaue(a,min,max):
    if a<min:
        a=min
    if a>max:
        a=max
    return a

def limit_speed(a,min):#限制最小速度
    if a <0:
        if a> -min:
            a = -min
    elif a>0:
        if a<min:
            a = min
    return a

#传入参数 x 和 y轴
def control_motor_speed(speed_fb,speed_lr):
    speed_L1 = speed_fb + speed_lr 
    speed_L2 = speed_fb + speed_lr 
    speed_R1 = speed_fb - speed_lr 
    speed_R2 = speed_fb - speed_lr 
    #满足速度范围
    speed_L1 = limit_speed(speed_L1,MIN_Speed)
    speed_L2 = limit_speed(speed_L2,MIN_Speed)
    speed_R1 = limit_speed(speed_R1,MIN_Speed)
    speed_R2 = limit_speed(speed_R2,MIN_Speed)

    #print(speed_L1,speed_L2,speed_R1,speed_R2)
    run_motor(speed_L1,speed_L2,speed_R1,speed_R2) #控制电机转

class FaceDetector:
    def __init__(self, minDetectionCon=0.5):
        self.mpFaceDetection = mp.solutions.face_detection
        self.mpDraw = mp.solutions.drawing_utils
        self.facedetection = self.mpFaceDetection.FaceDetection(min_detection_confidence=minDetectionCon)

    def findFaces(self, frame):
        img_RGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.results = self.facedetection.process(img_RGB)
        bboxs = []
        bbox=0,0,0,0
        center_x=center_y=0
        if self.results.detections:
            for id, detection in enumerate(self.results.detections):
                bboxC = detection.location_data.relative_bounding_box
                ih, iw, ic = frame.shape
                bbox = int(bboxC.xmin * iw), int(bboxC.ymin * ih), \
                       int(bboxC.width * iw), int(bboxC.height * ih)
                #计算中心点
                center_x = bbox[0] + bbox[2] // 2
                center_y = bbox[1] + bbox[3] // 2
                bboxs.append([id, bbox, detection.score])
                frame= self.fancyDraw(frame, bbox)
                # cv2.putText(frame, f'{int(detection.score[0] * 100)}%',
                #            (bbox[0], bbox[1] - 20), cv2.FONT_HERSHEY_PLAIN,
                #            3, (255, 0, 255), 2)
        return frame, bboxs, self.results.detections, bbox, center_x

    def fancyDraw(self, frame, bbox, l=30, t=5):
        x, y, w, h = bbox
        x1, y1 = x + w, y + h
        cv2.rectangle(frame, (x, y),(x + w, y + h), (0,255,0), 2)
        # Top left x,y
        cv2.line(frame, (x, y), (x + l, y), (0,255,0), t)
        cv2.line(frame, (x, y), (x, y + l), (0,255,0), t)
        # Top right x1,y
        cv2.line(frame, (x1, y), (x1 - l, y), (0,255,0), t)
        cv2.line(frame, (x1, y), (x1, y + l), (0,255,0), t)
        # Bottom left x1,y1
        cv2.line(frame, (x, y1), (x + l, y1), (0,255,0), t)
        cv2.line(frame, (x, y1), (x, y1 - l), (0,255,0), t)
        # Bottom right x1,y1
        cv2.line(frame, (x1, y1), (x1 - l, y1), (0,255,0), t)
        cv2.line(frame, (x1, y1), (x1, y1 - l), (0,255,0), t)
        return frame





def myTrack_Face_Follow():
    global x,w,y,h,area_center
    face_detector = FaceDetector(0.75)
    imshow_num = 0
    
    Facebot.Ctrl_Servo(1,90)
    Facebot.Ctrl_Servo(2,40)
    
    
    image = cv2.VideoCapture(0)
    image_width = 320
    image_height = 240
    image.set(3, image_width)
    image.set(4, image_height)
    
    try:
        while 1:
            ret, frame = image.read()
            faces,_,descore,bbox,center_x= face_detector.findFaces(frame)
            x,y,w,h = bbox
            if descore:
                now_aera = w*h
                now_aera = limit_max_vlaue(now_aera,2000,6000)#限制下面积的最小最大
                
                # 输入Y轴方向参数PID控制输入 Input Y-axis direction parameter PID control input
                if math.fabs(int(image_height/2) - (y + h/2)) > 40:
                    yservo_pid.SystemOutput = y + h/2
                    yservo_pid.SetStepSignal(int(image_height/2))
                    yservo_pid.SetInertiaTime(0.01, 0.05)
                    target_valuey = int(850+yservo_pid.SystemOutput)
                    target_servoy = int((target_valuey-500)/10)                   
                    #print("target_servoy %d", target_servoy)  
                    if target_servoy > 100:
                        target_servoy = 100
                    if target_servoy < 0:
                        target_servoy = 0        
                    Facebot.Ctrl_Servo(2, target_servoy)

                #电机X轴pid
                direction_pid.SystemOutput = center_x
                direction_pid.SetStepSignal(int(image_width/2))
                direction_pid.SetInertiaTime(0.01, 0.1)
                target_valuex = int(direction_pid.SystemOutput)
                #print(target_valuex)
                if target_valuex > -3 and target_valuex < 3:
                    target_valuex = 0 #剔除死区
                
                
                #根据面积进行前进后退
                speed_pid.SystemOutput = now_aera
                speed_pid.SetStepSignal(area_center)
                speed_pid.SetInertiaTime(0.01, 0.1)               
                speed_value = int(speed_pid.SystemOutput)
                #print(speed_value)
                if speed_value > -10 and speed_value < 10:
                    speed_value = 0 #增加静止区
                else:
                    #剔除死区
                    if speed_value<0: 
                        speed_value = limit_max_vlaue(speed_value,-25,-15)
                    else:
                        speed_value = limit_max_vlaue(speed_value,15,25)
                
                
                control_motor_speed(speed_value,-target_valuex)
                            
            
            else:
                stop_robot()
                
            imshow_num +=1
            if imshow_num%2==0:
                cv2.imshow("face", frame)
                imshow_num = 0
                
            if cv2.waitKey(1)==ord('q'):
                stop_robot()
                Facebot.Ctrl_Servo(1,90)
                Facebot.Ctrl_Servo(2,25)
                image.release()
                cv2.destroyAllWindows()
                return
    except:
        stop_robot()
        Facebot.Ctrl_Servo(1,90)
        Facebot.Ctrl_Servo(2,25)
        cv2.destroyAllWindows()
       
       
myTrack_Face_Follow()