"""
Wallpaper Engine 控制插件
"""
import os
import subprocess
from typing import Optional
from ha_mqtt_discoverable.sensors import Button, ButtonInfo
from ha_mqtt_discoverable import Settings
from paho.mqtt.client import Client as MQTTClient


class Wallpaper:
    def __init__(self, core=None):
        """
        初始化 Wallpaper 插件
        :param core: PCTools Core 实例
        """
        self.core = core
        self.log = core.log
        self.exe_path = self._find_wallpaper_engine_path()

        # MQTT 实体
        self.pause_button = None
        self.stop_button = None
        self.play_button = None
        self.mute_button = None
        self.unmute_button = None
        self.next_button = None

    def setup_entities(self):
        """设置 MQTT 实体"""
        try:
            mqtt_settings = self.core.mqtt.get_mqtt_settings()
            device_info = self.core.mqtt.get_device_info()

            # 检查 Wallpaper Engine 是否安装
            if not self.exe_path:
                self.log.warning("未找到 Wallpaper Engine 安装路径，按钮功能将不可用")

            # 定义按钮配置
            buttons = [
                {
                    'name': 'pause',
                    'display_name': '暂停壁纸',
                    'icon': 'mdi:pause',
                    'command': 'pause',
                    'attr': 'pause_button'
                },
                {
                    'name': 'stop',
                    'display_name': '停止壁纸',
                    'icon': 'mdi:stop',
                    'command': 'stop',
                    'attr': 'stop_button'
                },
                {
                    'name': 'play',
                    'display_name': '播放壁纸',
                    'icon': 'mdi:play',
                    'command': 'play',
                    'attr': 'play_button'
                },
                {
                    'name': 'mute',
                    'display_name': '壁纸静音',
                    'icon': 'mdi:volume-off',
                    'command': 'mute',
                    'attr': 'mute_button'
                },
                {
                    'name': 'unmute',
                    'display_name': '壁纸取消静音',
                    'icon': 'mdi:volume-high',
                    'command': 'unmute',
                    'attr': 'unmute_button'
                },
                {
                    'name': 'next',
                    'display_name': '下一个壁纸',
                    'icon': 'mdi:skip-next',
                    'command': 'nextWallpaper',
                    'attr': 'next_button'
                }
            ]

            # 创建所有按钮实体
            for btn_config in buttons:
                button_info = ButtonInfo(
                    name=btn_config['name'],
                    unique_id=f"{self.core.mqtt.device_name}_wallpaper_{btn_config['name']}",
                    object_id=f"{self.core.mqtt.device_name}_wallpaper_{btn_config['name']}",
                    device=device_info,
                    icon=btn_config['icon'],
                    display_name=btn_config['display_name']
                )

                button_settings = Settings(
                    mqtt=mqtt_settings,
                    entity=button_info
                )

                # 使用 lambda 捕获当前的 command
                button = Button(
                    button_settings,
                    command_callback=lambda client, user_data, message, cmd=btn_config['command']:
                        self.handle_button_press(client, user_data, message, cmd)
                )

                # 发送配置以触发发现
                button.write_config()

                # 设置到对应的属性
                setattr(self, btn_config['attr'], button)

            self.log.info("Wallpaper MQTT 实体创建成功，共创建 6 个按钮")

        except Exception as e:
            self.log.error(f"创建 Wallpaper MQTT 实体失败: {e}")

    def _find_wallpaper_engine_path(self) -> Optional[str]:
        """检测wallpaper.exe的安装路径"""
        common_paths = [
            r"C:\Program Files (x86)\Steam\steamapps\common\wallpaper_engine",
            r"D:\Program Files (x86)\Steam\steamapps\common\wallpaper_engine"
        ]
        if self.core.config.get_config("wallpaper_engine_path"):
            return self.core.config.get_config("wallpaper_engine_path")

        for path in common_paths:
            exe_path = os.path.join(path, "wallpaper64.exe")
            if os.path.exists(exe_path):
                return exe_path

            exe_path = os.path.join(path, "wallpaper32.exe")
            if os.path.exists(exe_path):
                return exe_path

        return None

    def launch(self) -> bool:
        """启动Wallpaper Engine"""
        if not self.exe_path:
            return False

        try:
            subprocess.Popen([self.exe_path])
            return True
        except Exception:
            return False

    def shell(self, command) -> bool:
        """执行 Wallpaper Engine 控制命令"""
        if not self.exe_path:
            self.log.error("Wallpaper Engine 未安装或路径未找到")
            return False
        try:
            subprocess.run([self.exe_path, "-control", command], check=True)
            return True
        except subprocess.CalledProcessError as e:
            self.log.error(f"执行命令失败: {command} - {e}")
            return False
        except Exception as e:
            self.log.error(f"执行命令异常: {command} - {e}")
            return False

    def handle_button_press(self, client: MQTTClient, user_data, message, command: str):
        """
        处理按钮按下事件（由 ha-mqtt-discoverable 回调）
        :param client: MQTT 客户端
        :param user_data: 用户数据
        :param message: MQTT 消息
        :param command: Wallpaper Engine 命令
        """
        try:
            self.log.info(f"收到 Wallpaper Engine 命令: {command}")

            if self.shell(command):
                self.log.info(f"Wallpaper Engine 命令执行成功: {command}")
            else:
                self.log.error(f"Wallpaper Engine 命令执行失败: {command}")

        except Exception as e:
            self.log.error(f"处理 Wallpaper Engine 命令失败: {e}")

