"""
前台窗口监听插件
"""
import win32gui
import win32process
import threading
import time
import psutil
import requests
import flet as ft
from ha_mqtt_discoverable.sensors import Sensor, SensorInfo
from ha_mqtt_discoverable import Settings

last_app = None


class WindowListener:
    def __init__(self, core):
        """
        初始化 WindowListener 插件
        :param core: PCTools Core 实例
        """
        self.core = core
        self.log = core.log
        self.stop_event = threading.Event()
        self.thread = None

        # MQTT 实体
        self.window_title_sensor = None
        self.window_exe_sensor = None
        self.window_path_sensor = None

    def setup_entities(self):
        """设置 MQTT 实体"""
        try:
            mqtt_settings = self.core.mqtt.get_mqtt_settings()
            device_info = self.core.mqtt.get_device_info()

            # 创建窗口标题传感器
            title_info = SensorInfo(
                name="foreground_window",
                unique_id=f"{self.core.mqtt.device_name}_foreground_window",
                object_id=f"{self.core.mqtt.device_name}_foreground_window",
                device=device_info,
                icon="mdi:window-maximize",
                display_name="前台应用窗口"
            )

            title_settings = Settings(
                mqtt=mqtt_settings,
                entity=title_info
            )

            self.window_title_sensor = Sensor(title_settings)
            self.window_title_sensor.set_state("启动中...")

            # 创建进程名称传感器
            exe_info = SensorInfo(
                name="foreground_window_exe",
                unique_id=f"{self.core.mqtt.device_name}_foreground_window_exe",
                object_id=f"{self.core.mqtt.device_name}_foreground_window_exe",
                device=device_info,
                icon="mdi:application",
                display_name="前台应用进程"
            )

            exe_settings = Settings(
                mqtt=mqtt_settings,
                entity=exe_info
            )

            self.window_exe_sensor = Sensor(exe_settings)
            self.window_exe_sensor.set_state("启动中...")

            # 创建路径传感器
            path_info = SensorInfo(
                name="foreground_window_path",
                unique_id=f"{self.core.mqtt.device_name}_foreground_window_path",
                object_id=f"{self.core.mqtt.device_name}_foreground_window_path",
                device=device_info,
                icon="mdi:folder-open",
                display_name="前台应用路径"
            )

            path_settings = Settings(
                mqtt=mqtt_settings,
                entity=path_info
            )

            self.window_path_sensor = Sensor(path_settings)
            self.window_path_sensor.set_state("启动中...")

            self.log.info("WindowListener MQTT 实体创建成功")

            # 创建实体后自动启动监听
            self.start()

        except Exception as e:
            self.log.error(f"创建 WindowListener MQTT 实体失败: {e}")

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
        """后台监听线程"""
        last_window = None
        while not self.stop_event.is_set():
            try:
                current_hwnd = win32gui.GetForegroundWindow()
                if current_hwnd != last_window:
                    last_window = current_hwnd
                    window_info = self._get_window_info(current_hwnd)
                    if window_info:
                        self.log.debug(f"前台应用: {window_info['exe_name']}")

                        # 上报应用变化（如果启用）
                        if self.core.get_plugin_config("WindowListener.py", "post_enabled", False):
                            self.report_app_change(window_info["exe_name"])

                        # 更新 MQTT 传感器状态
                        if self.window_title_sensor:
                            self.window_title_sensor.set_state(window_info["window_title"])
                        if self.window_exe_sensor:
                            self.window_exe_sensor.set_state(window_info["exe_name"])
                        if self.window_path_sensor:
                            self.window_path_sensor.set_state(window_info["exe_path"])

                time.sleep(0.1)
            except Exception as e:
                self.log.error(f"窗口监听错误: {e}")
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
                    "secret": self.core.get_plugin_config("WindowListener.py", "post_secret_key", ''),
                    "device": self.core.get_plugin_config("WindowListener.py", "post_device_id", '电脑'),
                    "app_name": current_app,
                    "running": True
                }

                response = requests.post(
                    self.core.get_plugin_config("WindowListener.py", "post_api_url", False),
                    json=payload
                )

                if response.status_code == 200:
                    self.log.info(f"成功上报: {current_app}")
                    last_app = current_app
                else:
                    self.log.error(f"上报失败: {response.text}")

            except Exception as e:
                self.log.error(f"发生错误: {str(e)}")

    def handle_url_input(self, field_name, input_type="string"):
        def callback(e):
            parsed_value = e.control.value
            if input_type == "bool":
                parsed_value = bool(parsed_value)
            self.core.set_plugin_config("WindowListener.py", field_name, parsed_value)
            self.core.log.info(f"已更新配置: {field_name} = {parsed_value}")

        return callback

    def setting_page(self, e):
        """设置页面"""
        return ft.Column(
            [
                ft.Row(
                    [ft.Switch(
                        label="应用数据上报",
                        value=self.core.get_plugin_config("WindowListener.py", "post_enabled", False),
                        on_change=self.handle_url_input("post_enabled", "bool")
                    )]
                ),
                ft.TextField(
                    label="上报API_URL",
                    width=250,
                    on_submit=self.handle_url_input("post_api_url"),
                    value=self.core.get_plugin_config("WindowListener.py", "post_api_url", "")
                ),
                ft.TextField(
                    label="设备名称",
                    width=250,
                    on_submit=self.handle_url_input("post_device_id"),
                    value=self.core.get_plugin_config("WindowListener.py", "post_device_id", "电脑")
                ),
                ft.TextField(
                    label="Secret密钥",
                    width=250,
                    on_submit=self.handle_url_input("post_secret_key"),
                    value=self.core.get_plugin_config("WindowListener.py", "post_secret_key", "")
                ),
                ft.Text("应用数据上报功能使用说明:", weight=ft.FontWeight.BOLD, size=14),
                ft.Text(
                    "• 用于接入Runtime Tracker\n"
                    "• 自动同步软件名称到后端\n",
                    size=12,
                    color=ft.Colors.GREY_700,
                ),
                ft.TextButton(
                    "Runtime Tracker",
                    animate_size=20,
                    on_click=lambda e: self.core.gui.page.launch_url('https://github.com/1812z/RunTime_Tracker')
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
