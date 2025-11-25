import cv2
import os,socket,sys,time
import PID,math
import numpy as np

from McLumk_Wheel_Sports import *
colorbot = Raspbot()

g_mode=1
red=(0,0,255)
green=(0,255,0)
blue=(255,0,0)
yellow=(0,255,255)

color_lower = np.array([26, 43, 46])
color_upper = np.array([34, 255, 255])
mode=4

yservo_pid = PID.PositionalPID(0.8, 0.2, 0.01)
direction_pid = PID.PositionalPID(0.2, 0, 0.002)
speed_pid = PID.PositionalPID(3, 0,0.0001)

area_center = 30 #面积大小
MIN_Speed = 5


# 控制电机运动 Control motor movement
def run_motor(M1,M2,M3,M4):  #-255~255
    colorbot.Ctrl_Muto(0, M1)
    colorbot.Ctrl_Muto(1, M2)
    colorbot.Ctrl_Muto(2, M3)
    colorbot.Ctrl_Muto(3, M4)
    
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



def change_color(colorfollow = 'red'):
    global color_lower,color_upper,mode
    if colorfollow == 'red':  #red
        mode =1
        color_lower = np.array([156, 70, 72]) #0
        color_upper = np.array([180, 255, 255]) #7
    elif colorfollow == 'green': #green
        mode =2
        color_lower = np.array([35, 43, 46])
        color_upper = np.array([77, 255, 255])
    elif colorfollow == 'blue':   #blue
        mode =3
        color_lower = np.array([100, 43, 46])
        color_upper = np.array([124, 255, 255])
    elif colorfollow == 'yellow':   #yellow
        mode =4
        color_lower = np.array([26, 43, 46])
        color_upper = np.array([34, 255, 255])


#-----------------------COMMON INIT-----------------------
def myTrack_Follow_color(strcolor='red'):
    global colorbot
    if change_color(strcolor)==1: #如果不是红黄蓝绿的一种颜色直接返回
        return
    
    colorbot.Ctrl_Servo(1,90)
    colorbot.Ctrl_Servo(2,40)
    stop_robot()
    t_start = time.time()
    fps = 0
    color_x = 0
    color_y = 0
    color_radius = 0
    imshow_num = 0

    cap=cv2.VideoCapture(0)
    cap.set(3,320)
    cap.set(4,240)
    if(not cap.isOpened()):
        print("[camera.py:cam]:can't open this camera")
    try:
        while 1:
            ret, frame = cap.read()
            frame_ = cv2.GaussianBlur(frame,(5,5),0)                    
            hsv = cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv,color_lower,color_upper)  
            mask = cv2.erode(mask,None,iterations=2)
            mask = cv2.dilate(mask,None,iterations=2)
            mask = cv2.GaussianBlur(mask,(3,3),0)     
            cnts = cv2.findContours(mask.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[-2] 
            if g_mode == 1:
                if len(cnts) > 0:
                    cnt = max (cnts, key = cv2.contourArea)
                    (color_x,color_y),color_radius = cv2.minEnclosingCircle(cnt)
                    
                    if color_radius > 6:
                        cv2.circle(frame,(int(color_x),int(color_y)),int(color_radius),(255,0,255),2)  
                    
                        ####sport
                        # 输入Y轴方向参数PID控制输入 Input Y-axis direction parameter PID control input
                        if math.fabs(120 - (color_y)) > 20:#40
                            yservo_pid.SystemOutput = color_y
                            yservo_pid.SetStepSignal(120)
                            yservo_pid.SetInertiaTime(0.01, 0.05)
                            target_valuey = int(850+yservo_pid.SystemOutput)
                            target_servoy = int((target_valuey-500)/10)                    
                            if target_servoy > 100:
                                target_servoy = 100
                            if target_servoy < 0:
                                target_servoy = 0        
                            colorbot.Ctrl_Servo(2, target_servoy)
                        
                        #电机X轴pid
                        direction_pid.SystemOutput = color_x
                        direction_pid.SetStepSignal(160)
                        direction_pid.SetInertiaTime(0.01, 0.1)
                        target_valuex = int(direction_pid.SystemOutput)
                        #print(target_valuex)
                        if target_valuex > -3 and target_valuex < 3:
                            target_valuex = 0 #静止区
                        
                        
                        #根据面积进行前进后退
                        speed_pid.SystemOutput = color_radius
                        speed_pid.SetStepSignal(area_center)
                        speed_pid.SetInertiaTime(0.01, 0.1)               
                        speed_value = int(speed_pid.SystemOutput)
                        #print(color_radius,speed_value)
                        if color_radius > 24 and color_radius < 45:
                            speed_value = 0 #增加静止区
                        else:
                            #剔除死区
                            if speed_value<0: 
                                speed_value = limit_max_vlaue(speed_value,-25,-15)
                            else:
                                speed_value = limit_max_vlaue(speed_value,15,25)
                        control_motor_speed(speed_value,-target_valuex)     
                else:
                    color_x = 0
                    color_y = 0
                    stop_robot()
                    
                cv2.putText(frame, "X:%d, Y%d" % (int(color_x), int(color_y)), (40,40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 3)
                t_start = time.time()
                fps = 0
            else:
                fps = fps + 1
                mfps = fps / (time.time() - t_start)
                cv2.putText(frame, "FPS " + str(int(mfps)), (40,40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 3)

            
            imshow_num +=1
            if imshow_num%2==0:
                if mode==1:
                    cv2.rectangle(frame, (290, 10), (320, 40), red, -1)
                elif mode==2:
                    cv2.rectangle(frame, (290, 10), (320, 40), green, -1)
                elif mode==3:
                    cv2.rectangle(frame, (290, 10), (320, 40), blue, -1)
                elif mode==4:
                    cv2.rectangle(frame, (290, 10), (320, 40), yellow, -1)
                cv2.imshow("line", frame)
                imshow_num = 0
                
            if cv2.waitKey(1)==ord('q'):
                stop_robot()
                colorbot.Ctrl_Servo(1,90)
                colorbot.Ctrl_Servo(2,25)
                colorbot.Ctrl_Servo(1,90)
                colorbot.Ctrl_Servo(2,25)
                cap.release()
                cv2.destroyAllWindows()
                return

        cap.release()
        cv2.destroyAllWindows() 
    except:
        stop_robot()
        colorbot.Ctrl_Servo(1,90)
        colorbot.Ctrl_Servo(2,25)
        cap.release()
        cv2.destroyAllWindows()
 

colorstr = sys.argv[1]      
myTrack_Follow_color(colorstr)