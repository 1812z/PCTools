"""
自定义命令按钮插件
"""
import base64
import hashlib
import flet as ft
import os
import subprocess
from ha_mqtt_discoverable.sensors import Button, ButtonInfo
from ha_mqtt_discoverable import Settings
from paho.mqtt.client import Client as MQTTClient


def generate_short_id(filename: str) -> str:
    '''
    生成校验id
    '''
    sha256_hash = hashlib.sha256(filename.encode()).digest()
    base64_encoded = base64.urlsafe_b64encode(sha256_hash).rstrip(b'=')
    short_id = base64_encoded.decode('utf-8')
    short_id = short_id[:16]
    return short_id


class Commands:
    def __init__(self, core):
        """
        初始化 Commands 插件
        :param core: PCTools Core 实例
        """
        self.core = core
        self.log = core.log

        current_file_path = os.path.abspath(__file__)
        # 自动处理文件夹层级，找到 plugins/Command/commands 目录
        self.current_directory = os.path.join(
            os.path.dirname(current_file_path),  # 当前文件所在目录(plugins/Command)
            "commands"  # 添加commands子目录
        )
        # 如果目录不存在则创建
        os.makedirs(self.current_directory, exist_ok=True)

        # 存储命令文件和对应的按钮实体
        self.command_data = {}  # {short_id: filename}
        self.button_entities = {}  # {short_id: Button实例}

    def setup_entities(self):
        """设置 MQTT 实体"""
        try:
            mqtt_settings = self.core.mqtt.get_mqtt_settings()
            device_info = self.core.mqtt.get_device_info()

            count = 0
            # 扫描 commands 目录中的所有文件
            for filename in os.listdir(self.current_directory):
                file_path = os.path.join(self.current_directory, filename)
                if os.path.isfile(file_path):
                    short_id = generate_short_id(filename)
                    self.command_data[short_id] = filename

                    # 根据文件类型选择图标
                    icon = "mdi:application-edit-outline"
                    if filename.endswith(".py"):
                        icon = "mdi:language-python"
                    elif filename.endswith(".bat"):
                        icon = "mdi:script-text-outline"
                    elif filename.endswith(".lnk"):
                        icon = "mdi:link-variant"

                    # 创建按钮实体
                    button_info = ButtonInfo(
                        name=short_id,
                        unique_id=f"commands_{short_id}",
                        object_id=f"commands_{short_id}",
                        device=device_info,
                        icon=icon,
                        display_name=filename
                    )

                    button_settings = Settings(
                        mqtt=mqtt_settings,
                        entity=button_info
                    )

                    # 创建按钮实体，使用 lambda 捕获当前的 short_id
                    button = Button(
                        button_settings,
                        command_callback=lambda client, user_data, message, sid=short_id:
                            self.handle_button_press(client, user_data, message, sid)
                    )

                    button.write_config()

                    self.button_entities[short_id] = button
                    count += 1

            self.log.info(f"Commands MQTT 实体创建成功，共发现 {count} 个命令")

        except Exception as e:
            self.log.error(f"创建 Commands MQTT 实体失败: {e}")

    def handle_button_press(self, client: MQTTClient, user_data, message, short_id: str):
        """
        处理按钮按下事件（由 ha-mqtt-discoverable 回调）
        :param client: MQTT 客户端
        :param user_data: 用户数据
        :param message: MQTT 消息
        :param short_id: 命令的短ID
        """
        run_file = self.command_data.get(short_id)
        if run_file is None:
            self.log.error(f"找不到命令: {short_id}")
            return

        try:
            self.log.info(f"执行命令: {run_file}")

            # 获取文件扩展名
            file_ext = run_file.split('.')[-1].lower()
            file_path = os.path.join(self.current_directory, run_file)

            if file_ext == "lnk":  # 快捷方式
                self.log.info(f"打开快捷方式: {run_file}")
                subprocess.Popen(['explorer', file_path])

            elif file_ext == "bat":  # 批处理文件
                self.log.info(f"执行批处理文件: {run_file}")
                subprocess.Popen(
                    file_path,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

            else:  # 其它文件（使用系统默认程序打开）
                self.log.info(f"使用默认程序打开: {run_file}")
                os.system(f'start "" "{file_path}"')

        except Exception as e:
            self.log.error(f"执行命令失败 ({run_file}): {e}")


    def setting_page(self, e):
        """设置页面"""
        return ft.Column(
            [
                ft.ElevatedButton("打开目录", on_click=lambda e: os.startfile(self.current_directory))
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )