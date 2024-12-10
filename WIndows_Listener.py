import ctypes
from ctypes import wintypes
import threading
from MQTT import Send_MQTT_Discovery,Update_State_data

# 定义常量
EVENT_SYSTEM_FOREGROUND = 0x0003
WINEVENT_OUTOFCONTEXT = 0x0000
WINEVENT_SKIPOWNPROCESS = 0x0002
WINEVENT_FLAGS = WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNPROCESS

# 加载必要的 DLL
user32 = ctypes.WinDLL('user32', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

# 定义回调函数类型
WinEventProcType = ctypes.WINFUNCTYPE(
    None,
    ctypes.c_void_p,  # hWinEventHook
    ctypes.c_uint,    # event
    ctypes.c_void_p,  # hwnd
    ctypes.c_long,    # idObject
    ctypes.c_long,    # idChild
    ctypes.c_uint,    # dwEventThread
    ctypes.c_uint     # dwmsEventTime
)

# 定义回调函数
def win_event_proc(hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
    # 使用 GetForegroundWindow 获取当前前台窗口
    current_hwnd = user32.GetForegroundWindow()
    if current_hwnd:
        # 获取窗口标题
        length = user32.GetWindowTextLengthW(current_hwnd)
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(current_hwnd, buffer, length + 1)
        window_title = buffer.value

        # 获取窗口类名
        class_buffer = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(current_hwnd, class_buffer, 256)
        class_name = class_buffer.value

        print(f"前台窗口变化到 HWND={current_hwnd}, 标题='{window_title}', 类名='{class_name}'")
        Update_State_data(str(window_title),"ForegroundWindow","sensor")

# 将 Python 函数转换为 C 回调函数
WinEventProc = WinEventProcType(win_event_proc)

def discovery():
    info = Send_MQTT_Discovery(None,None,"前台应用","ForegroundWindow","sensor")
    print(info)

# 设置事件钩子
def window_listener():
    discovery()
    global hook, is_listening, stop_event
    hook = user32.SetWinEventHook(
        EVENT_SYSTEM_FOREGROUND,  # eventMin
        EVENT_SYSTEM_FOREGROUND,  # eventMax
        0,                        # hmodWinEventProc, HMODULE.NULL
        WinEventProc,             # pfnWinEventProc
        0,                        # idProcess, 0 表示所有进程
        0,                        # idThread, 0 表示所有线程
        WINEVENT_FLAGS            # dwFlags
    )

    if not hook:
        raise ctypes.WinError(ctypes.get_last_error())

    print("正在监听前台窗口变化")
    # 消息循环
    msg = wintypes.MSG()
    
    bRet = user32.GetMessageW(ctypes.byref(msg), 0, 0, 0)
    if bRet == 0:
        pass
    elif bRet == -1:
        raise ctypes.WinError(ctypes.get_last_error())
    else:
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))
        
def start_window_listener():
    listener_thread = threading.Thread(target=window_listener)
    listener_thread.daemon = True  # 设置为守护线程，程序退出时会自动结束
    listener_thread.start()

if __name__ == "__main__":
    window_listener()

 