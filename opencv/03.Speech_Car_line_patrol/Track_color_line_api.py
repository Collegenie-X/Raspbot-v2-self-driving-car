import cv2,sys,threading
import os,sys,time,threading
sys.path.append('/home/pi/project_demo/lib')
from McLumk_Wheel_Sports import *
import HSV_Config_Two
import PID
import time


line_color = 'blue' #yellow  blue  green  red black 
linebot = Raspbot()
MAX_Speed = 100 #最大的速度 -看情况加大

odisb = 0
exit_flag = 0
DIS_AVOID_Crisis = 200 #200mm

#障碍物距离检测
def decect_dis():
    linebot.Ctrl_Ulatist_Switch(1)
    time.sleep(0.1)
    global odisb
    while True:
        diss_H =linebot.read_data_array(0x1b,1)[0]
        diss_L =linebot.read_data_array(0x1a,1)[0]
        odisb = diss_H << 8 | diss_L 
        time.sleep(0.05) 
        if exit_flag==1:
            linebot.Ctrl_Ulatist_Switch(0) #关闭测距
            linebot.Ctrl_BEEP_Switch(0)
            break

def change_color(colorline = 'red'):
    global line_color
    if colorline=='red':  #red
        line_color = 'red'
        return 0
    elif colorline=='green': #green
        line_color = 'green'
        return 0
    elif colorline=='blue':   #blue
       line_color = 'blue'
       return 0
    elif colorline=='yellow':   #yellow
        line_color = 'yellow'
        return 0
    # elif colorline=='black':   
    #     line_color = 'black'
    #     return 0

    return 1

def limit_fun(input,min,max):
    if input < min:
        input = min
    elif input > max:
        input = max
    return input

def Find_color(colors_dict,num_len):
    if num_len == 0:
        return -1 #没找到 no find
    for i in range(num_len):
        if colors_dict[i] == line_color:
            return i #找到了 find!
    return -1 #没找到 no find


# 控制电机运动 Control motor movement
def run_motor(M1,M2,M3,M4):  #-255~255
    linebot.Ctrl_Muto(0, M1)
    linebot.Ctrl_Muto(1, M2)
    linebot.Ctrl_Muto(2, M3)
    linebot.Ctrl_Muto(3, M4)

def limin_speed(speed,max,min):
    if speed > max:
        return max
    
    elif speed<min:
        return min

    return speed

#传入参数 x 和 y轴
def control_motor_speed(speed_fb,speed_lr):
    speed_L1 = speed_fb + speed_lr 
    speed_L2 = speed_fb + speed_lr 
    speed_R1 = speed_fb - speed_lr 
    speed_R2 = speed_fb - speed_lr 
    #满足速度范围
    speed_L1 = limin_speed(speed_L1,MAX_Speed,-MAX_Speed)
    speed_L2 = limin_speed(speed_L2,MAX_Speed,-MAX_Speed)
    speed_R1 = limin_speed(speed_R1,MAX_Speed,-MAX_Speed)
    speed_R2 = limin_speed(speed_R2,MAX_Speed,-MAX_Speed)

    run_motor(speed_L1,speed_L2,speed_R1,speed_R2) #控制电机转


def myTrack_line(colorline = 'red'):
    try:
        
        cv2.destroyAllWindows() 
        
        global color_hsv,odisb,exit_flag
        display_counter = 0
        
        if change_color(colorline)==1: #如果不是红黄蓝绿的一种颜色直接返回
            return
        
        line_speed = 20 #巡线的速度 Speed of patrol line
        #初始化pid Init pid
        Px_line = 0.5 
        Ix_line = 0.001
        Dx_line = 0.0001
        X_line_Middle_error = 160 #图像X轴中心  Image X-axis center
        X_line_track_PID = PID.PositionalPID(Px_line, Ix_line, Dx_line) 

        linebot.Ctrl_Servo(1,90)
        linebot.Ctrl_Servo(2,0)
        
        #开启测距线程
        dis_thread = threading.Thread(target=decect_dis)
        dis_thread.daemon = True  
        dis_thread.start()
        time.sleep(1)
        

        #要识别的颜色阈值 Color threshold to be recognized
        color_hsv  = {"red"   : ((0, 43, 46), (10, 255, 255)),
                    "green" : ((35, 43, 46), (77, 255, 255)),
                    "blue"  : ((92, 100, 62), (121, 251, 255)),
                    "yellow": ((26, 43, 46), (34, 255, 255)),
                    "black":((0, 0, 0), (180, 255, 46))
                    }


        image=cv2.VideoCapture(0)
        image.set(3,320)
        image.set(4,240)
        update_hsv = HSV_Config_Two.update_hsv()
        
        
        
        while True:
            ret, frame = image.read() #usb摄像头 usb camera
            frame, binary,hsvname,xylist=update_hsv.get_contours(frame,color_hsv)
            unique_colors = list(dict.fromkeys(hsvname))
            
            # 根据列表的长度来决定如何分割字符串  Determine how to split the string based on the length of the list
            num_colors = len(unique_colors)

            if line_color == 'blue':
                cv2.putText(frame, line_color, (40,40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 2)
            elif line_color == 'green':
                cv2.putText(frame, line_color, (40,40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
            elif line_color == 'red':
                cv2.putText(frame, line_color, (40,40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
            elif line_color == 'yellow':
                cv2.putText(frame, line_color, (40,40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,255), 2)
            elif line_color == 'black':
                cv2.putText(frame, line_color, (40,40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
            else:
                cv2.putText(frame, line_color, (40,40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,255), 2)



            index = Find_color(unique_colors,num_colors)
            
            if odisb < DIS_AVOID_Crisis: 
                stop_robot()  #小车停止
                #蜂鸣器鸣叫
                linebot.Ctrl_BEEP_Switch(1)
                time.sleep(0.3)
                linebot.Ctrl_BEEP_Switch(0)
                time.sleep(0.3)
            elif index >= 0:
                # print(line_color,xylist[index]) 

                color_x = xylist[index][0]
                #print(color_x)

                #### X的方向(控制左右) Direction of X (control left and right)
                X_line_track_PID.SystemOutput = color_x  #X 
                X_line_track_PID.SetStepSignal(X_line_Middle_error)
                X_line_track_PID.SetInertiaTime(0.01, 0.1)               
                x_line_real_value = int(X_line_track_PID.SystemOutput)
                control_motor_speed(line_speed,-x_line_real_value)
   
            else:
                stop_robot()  #小车停止
                

            display_counter += 1
            
            # 实时传回图像数据进行显示 Real-time image data transmission for display
            if display_counter %2 == 0:
                cv2.imshow("color_image", frame)
                display_counter = 0

            
            if cv2.waitKey(1)==ord('q'):
                stop_robot()
                linebot.Ctrl_BEEP_Switch(0)
                linebot.Ctrl_Servo(1,90)
                linebot.Ctrl_Servo(2,25)
                exit_flag = 1
                image.release()
                cv2.destroyAllWindows() 
                return
    except:
        exit_flag = 1
        linebot.Ctrl_BEEP_Switch(0)
        stop_robot()
        linebot.Ctrl_Servo(1,90)
        linebot.Ctrl_Servo(2,15)
        image.release()
        cv2.destroyAllWindows() 

           
colorstr = sys.argv[1]      
myTrack_line(colorstr)
