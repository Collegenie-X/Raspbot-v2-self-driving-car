import sys,os
import time
import subprocess
import threading
from Speech_Lib import Speech
sys.path.append('/home/pi/project_demo/lib')
from McLumk_Wheel_Sports import *

class ColorLineTracker:
    def __init__(self):
        self.process = None
        self._monitor_thread = None
        self._stop_event = threading.Event()

    def start(self, colorline='red'):
        # 如果已有进程在运行，先停止 If there is already a process running, stop it first
        self.stop()
        
        # 重置停止事件 Reset stop event
        self._stop_event.clear()
        
        # 启动子进程 Start monitoring thread
        self.process = subprocess.Popen(['python', './Track_color_Follow_api.py', colorline])
        
        # 启动监控线程 Start monitoring thread
        self._monitor_thread = threading.Thread(target=self._monitor_process)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        print(f"start {colorline} Track...")
        
    def start_Face(self):
        # 如果已有进程在运行，先停止 If there is already a process running, stop it first
        self.stop()
        
        # 重置停止事件 Reset stop event
        self._stop_event.clear()
        
        # 启动子进程 Start monitoring thread
        self.process = subprocess.Popen(['python', './Track_Face_Follow_api.py'])
        
        # 启动监控线程 Start monitoring thread
        self._monitor_thread = threading.Thread(target=self._monitor_process)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        print(f"start Face Track...")

    def _monitor_process(self):
        while not self._stop_event.is_set():
            time.sleep(0.5)  # 更频繁地检查状态 Check the status more frequently
            
            # 检查进程是否已结束 Check if the process has ended
            if self.process.poll() is not None:
                print("line color end")
                return
                
        # 如果收到停止信号，终止进程 If a stop signal is received, terminate the process
        if self.process and self.process.poll() is None:
            self.process.terminate()  
            try:
                self.process.wait(timeout=2)  
            except subprocess.TimeoutExpired:
                self.process.kill()  
            print("The patrol program has been manually terminated")
    
    
    def car_reset(self):
        #小车复位操作
        bot.Ctrl_WQ2812_ALL(0,7)
        bot.Ctrl_Ulatist_Switch(0) #关闭测距
        bot.Ctrl_Servo(1, 90) #恢复中位
        bot.Ctrl_Servo(2, 25) #恢复中位
        stop_robot()
        
        
    def stop(self):
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._stop_event.set()  # 通知监控线程停止 Notify the monitoring thread to stop
            self._monitor_thread.join(timeout=3)  # 等待线程结束 Waiting for thread to end
            
        # 确保进程已被终止 Ensure that the process has been terminated
        if self.process and self.process.poll() is None:
            self.process.kill()
            
        self.process = None
        self._monitor_thread = None
        self.car_reset()


if __name__ == "__main__":
    tracker = ColorLineTracker()
    mySpeech = Speech()
    
    try:
        while True:
            time.sleep(0.2)
            
            num = mySpeech.speech_read()
            if num !=999 :
                #print(num)
                if num == 0:
                    mySpeech.void_write(num)
                if num == 71:
                    mySpeech.void_write(num)
                    print('Face')
                    tracker.start_Face()
                elif num == 72:
                    mySpeech.void_write(num)
                    print('yellow')
                    tracker.start('yellow')
                elif num == 73:
                    mySpeech.void_write(num)
                    print('red')
                    tracker.start('red')
                    
                elif num == 74:
                    mySpeech.void_write(num)
                    print('green')
                    tracker.start('green')
                    
                elif num == 75:
                    mySpeech.void_write(num)
                    print('blue')
                    tracker.start('blue')
                    
                elif num == 76:
                    mySpeech.void_write(num)
                    print('stop!')
                    tracker.stop()
 
                
                    
                    
    except KeyboardInterrupt:
        tracker.stop()
        print('Speech Track end!')
