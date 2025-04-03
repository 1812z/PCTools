import ctypes
from ctypes import wintypes
import threading
import time
from MQTT import Send_MQTT_Discovery, Update_State_data

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
    ctypes.c_void_p,
    ctypes.c_uint,
    ctypes.c_void_p,
    ctypes.c_long,
    ctypes.c_long,
    ctypes.c_uint,
    ctypes.c_uint
)

def discovery():
    info = Send_MQTT_Discovery(None, None, "前台应用", "ForegroundWindow", "sensor")
    print(info)

def win_event_proc(hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
    current_hwnd = user32.GetForegroundWindow()
    if current_hwnd:
        length = user32.GetWindowTextLengthW(current_hwnd)
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(current_hwnd, buffer, length + 1)
        window_title = buffer.value

        class_buffer = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(current_hwnd, class_buffer, 256)
        class_name = class_buffer.value

        print(f"HWND={current_hwnd}, Title='{window_title}', Class='{class_name}'")
        if window_title:
            Update_State_data(str(window_title), "ForegroundWindow", "sensor")

class WindowListener:
    def __init__(self):
        self.hook = None
        self.stop_event = threading.Event()
        self.thread = None
        self.win_event_proc = WinEventProcType(win_event_proc)

    def start(self):
        if self.thread and self.thread.is_alive():
            print("监听已在运行")
            return

        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run_listener, daemon=True)
        self.thread.start()
        print("窗口监听已启动")

    def stop(self):
        if not self.thread or not self.thread.is_alive():
            print("监听未运行")
            return

        self.stop_event.set()
        if self.hook:
            user32.UnhookWinEvent(self.hook)
            self.hook = None
        self.thread.join(timeout=1)
        print("窗口监听已停止")

    def _run_listener(self):
        discovery()
        
        self.hook = user32.SetWinEventHook(
            EVENT_SYSTEM_FOREGROUND,
            EVENT_SYSTEM_FOREGROUND,
            0,
            self.win_event_proc,
            0,
            0,
            WINEVENT_FLAGS
        )
        
        if not self.hook:
            raise ctypes.WinError(ctypes.get_last_error())

        try:
            msg = wintypes.MSG()
            while not self.stop_event.is_set():
                if user32.PeekMessageW(ctypes.byref(msg), 0, 0, 0, 0x0001):
                    if msg.message == 0x0012:
                        break
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))
                else:
                    time.sleep(0.05)
        finally:
            if self.hook:
                user32.UnhookWinEvent(self.hook)
                self.hook = None
# 创建监听器实例
listener = WindowListener()

def start_window_listener():
    print("启动窗口变化监听")
    listener.start()

def stop_window_listener():
    print("停止窗口变化监听")
    listener.stop()

if __name__ == "__main__":
    start_window_listener()
    
    try:
        while True:
            time.sleep(3)
            stop_window_listener()
            time.sleep(3)
            start_window_listener()
    except KeyboardInterrupt:
        stop_window_listener()