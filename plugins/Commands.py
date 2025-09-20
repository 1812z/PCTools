import base64
import hashlib
import flet as ft
import os
import subprocess

PLUGIN_NAME = "程序启动器"
PLUGIN_VERSION = "1.0"
PLUGIN_AUTHOR = "1812z"
PLUGIN_DESCRIPTION = "同步commands文件夹程序到Ha，方便快速打开程序，支持快捷方式和bat文件等"
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
        self.core = core
        current_file_path = os.path.abspath(__file__)
        self.current_directory =  os.path.join(os.path.dirname(os.path.dirname(current_file_path)), "commands")

        self.command_data = {}

    def discovery(self):
        count = 0
        info = ""
        for filename in os.listdir(self.current_directory):
            if os.path.isfile(os.path.join(self.current_directory, filename)):
                id = generate_short_id(filename)
                topic = f"Commands_{id}"
                self.command_data[id] = filename
                info += filename + "\n"
                count += 1
                icon = "mdi:application-edit-outline"
                if filename.endswith(".py"):
                    icon = "mdi:language-python"
                elif filename.endswith(".bat"):
                    icon = "mdi:script-text-outline"
                self.core.mqtt.send_mqtt_discovery(None, name=filename, entity_id=topic, entity_type="button",icon=icon)

        info = f"发现了{count}个命令\n" + info
        return info

    def handle_mqtt(self, key, payload):
        run_file = self.command_data.get(key)
        if run_file is None:
            self.core.log.error(f"找不到命令: {key}")
            return False
        else:
            file_type = run_file.split('.')[1]
            if file_type == "lnk":  # 快捷方式
                self.core.log.info("命令:" + key + "打开快捷方式:" + run_file)
                run = self.current_directory + '\\' + run_file
                # os.system(f'start "" "{run}"')
                subprocess.Popen(['explorer', run])
            elif file_type == "bat":  # 批处理文件
                bat_file = self.current_directory + '\\' + run_file
                subprocess.Popen(
                    bat_file, creationflags=subprocess.CREATE_NO_WINDOW)
            else:  # 其它文件
                run = self.current_directory + '\\' + run_file
                os.system(f'start "" "{run}"')

    def setting_page(self, e):
        """设置页面"""
        return ft.Column(
            [
                ft.ElevatedButton("打开目录", on_click=lambda e: os.startfile(self.current_directory))
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )