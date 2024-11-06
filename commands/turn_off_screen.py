import ctypes
import time

# 调用 Windows 系统 API 让显示器进入省电模式
def turn_off_screen():
    ctypes.windll.user32.SendMessageW(0xFFFF, 0x112, 0xF170, 2)  # 0xF170 = WM_SYSCOMMAND, 2 = SC_MONITORPOWER


def fun():
    print("休眠显示器")
    turn_off_screen()

