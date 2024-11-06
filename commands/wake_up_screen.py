import keyboard
import time

def wake_up_screen():
    keyboard.press('shift')
    time.sleep(0.1)  
    keyboard.release('shift') 
    print("模拟输入Shift唤醒屏幕")
    
def fun():
    wake_up_screen()
