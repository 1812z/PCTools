import win32gui
import win32process
import threading
import time
import psutil
import requests
import flet as ft

PLUGIN_NAME = "前台软件显示"
PLUGIN_VERSION = "1.0"
PLUGIN_AUTHOR = "1812z"
PLUGIN_DESCRIPTION = "同步显示前台运行的应用，支持接入到Runtime Tracker统计面板"

last_app = None

class Window_Listener:
    def __init__(self, core):
        self.core = core
        self.stop_event = threading.Event()
        self.thread = None

        self.config = [
            {
                "name": "前台应用窗口",
                "entity_type": "sensor",
                "entity_id": "Foreground_Window",
                "icon": "mdi:application-edit-outline"
            },
            {
                "name": "前台应用进程",
                "entity_type": "sensor",
                "entity_id": "Foreground_Window_exe",
                "icon": "mdi:application-edit-outline"
            },
            {
                "name": "前台应用路径",
                "entity_type": "sensor",
                "entity_id": "Foreground_Window_path",
                "icon": "mdi:application-edit-outline"
            }
        ]

    def start(self):
        if self.thread and self.thread.is_alive():
            self.core.log.info("监听已在运行")
            return False

        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run_listener, daemon=True)
        self.thread.start()
        self.core.log.debug("窗口监听已启动")
        return True

    def stop(self):
        if not self.thread or not self.thread.is_alive():
            self.core.log.info("监听未运行")
            return False

        self.stop_event.set()
        self.thread.join(timeout=1)
        self.core.log.debug("窗口监听已停止")
        return True

    def _run_listener(self):
        last_window = None
        while not self.stop_event.is_set():
            try:
                current_hwnd = win32gui.GetForegroundWindow()
                if current_hwnd != last_window:
                    last_window = current_hwnd
                    window_info = self._get_window_info(current_hwnd)
                    if window_info:
                        self.core.log.debug(f"前台应用: {window_info}")
                        if self.core.config.get_config("post_enabled"):
                            self.report_app_change(window_info["exe_name"])
                        self.core.mqtt.update_state_data(window_info["window_title"],"Window_Listener_Foreground_Window","sensor")
                        self.core.mqtt.update_state_data(window_info["exe_path"],"Window_Listener_Foreground_Window_path","sensor")
                        self.core.mqtt.update_state_data(window_info["exe_name"],"Window_Listener_Foreground_Window_exe","sensor")
                time.sleep(0.1)
            except Exception as e:
                self.core.log.error(f"窗口监听错误: {e}")
                time.sleep(1)

    def _get_window_info(self, hwnd):
        try:
            # 获取窗口标题
            window_title = win32gui.GetWindowText(hwnd)

            # 获取窗口类名
            class_name = win32gui.GetClassName(hwnd)

            # 获取进程ID
            _, pid = win32process.GetWindowThreadProcessId(hwnd)

            # 获取进程信息
            process = psutil.Process(pid)

            # 获取EXE路径
            exe_path = process.exe()

            # 获取EXE名称
            exe_name = process.name()

            return {
                "hwnd": hwnd,
                "window_title": window_title,
                "class_name": class_name,
                "pid": pid,
                "exe_path": exe_path,
                "exe_name": exe_name
            }
        except Exception as e:
            self.core.log.error(f"获取窗口信息错误: {e}")
            return None

    def report_app_change(self, current_app):
        """上报应用程序变化"""
        global last_app

        if current_app != last_app:
            try:
                payload = {
                    "secret": self.core.config.get_config("post_secret_key"),
                    "device": self.core.config.get_config("post_device_id"),
                    "app_name": current_app,
                    "running": True
                }

                response = requests.post(self.core.config.get_config("post_api_url"), json=payload)

                if response.status_code == 200:
                    self.core.log.info(f"成功上报: {current_app}")
                    last_app = current_app
                else:
                    self.core.log.error(f"上报失败: {response.text}")

            except Exception as e:
                self.core.log.error(f"发生错误: {str(e)}")

    def handle_url_input(self, field_name, input_type="string"):
        def callback(e):
            parsed_value = e.control.value
            self.core.config.set_config(field_name, parsed_value)

        return callback
    def setting_page(self, e):
        def handle_switch_change(e):
            # 获取开关状态并保存配置
            is_enabled = e.control.value
            self.core.config.set_config("post_enabled", is_enabled)


        """设置页面"""
        return ft.Column(
            [
                ft.Row(
                    [ft.Switch(label="应用数据上报", value=self.core.config.get_config("post_enabled"),
                          on_change=handle_switch_change)]
                ),
                ft.TextField(label="上报API_URL", width=250, on_submit=self.handle_url_input("post_api_url"), value=self.core.config.get_config("post_api_url")),
                ft.TextField(label="设备名称", width=250, on_submit=self.handle_url_input("post_device_id"), value=self.core.config.get_config("post_device_id")),
                ft.TextField(label="Secret密钥", width=250, on_submit=self.handle_url_input("post_secret_key"), value=self.core.config.get_config("post_secret_key"))
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

