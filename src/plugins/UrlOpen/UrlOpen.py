"""
URL 打开插件
"""
import subprocess
import webbrowser
from ha_mqtt_discoverable.sensors import Text, TextInfo
from ha_mqtt_discoverable import Settings
from paho.mqtt.client import Client as MQTTClient


class OpenURL:
    def __init__(self, core):
        """
        初始化 OpenURL 插件
        :param core: PCTools Core 实例
        """
        self.core = core
        self.log = core.log

        # MQTT 实体
        self.url_text = None

    def setup_entities(self):
        """设置 MQTT 实体"""
        try:
            mqtt_settings = self.core.mqtt.get_mqtt_settings()
            device_info = self.core.mqtt.get_device_info(
                plugin_name="UrlOpen",
                model="PCTools URL Opener"
            )

            # 创建 URL 文本实体
            text_info = TextInfo(
                name="open_url",
                unique_id=f"{self.core.mqtt.device_name}_open_url",
                object_id=f"{self.core.mqtt.device_name}_open_url",
                device=device_info,
                icon="mdi:earth",
                display_name="打开URL"
            )

            text_settings = Settings(
                mqtt=mqtt_settings,
                entity=text_info
            )

            self.url_text = Text(
                text_settings,
                command_callback=self.handle_url_command
            )

            # 设置初始提示文本以触发发现
            self.url_text.set_text("输入要打开的URL")

            self.log.info("UrlOpen MQTT 实体创建成功")

        except Exception as e:
            self.log.error(f"创建 UrlOpen MQTT 实体失败: {e}")

    def handle_url_command(self, client: MQTTClient, user_data, message):
        """
        处理 URL 打开命令（由 ha-mqtt-discoverable 回调）
        :param client: MQTT 客户端
        :param user_data: 用户数据
        :param message: MQTT 消息
        """
        try:
            url = message.payload.decode().strip()
            self.log.info(f"收到打开URL请求: {url}")

            # 更新文本状态
            if self.url_text:
                self.url_text.set_text(url)

            # 验证 URL 格式
            if not url:
                self.log.warning("URL 为空，忽略")
                return

            # 打开 URL
            try:
                # 使用 webbrowser 模块，更跨平台
                webbrowser.open(url)
                self.log.info(f"成功打开URL: {url}")

            except Exception as browser_err:
                # 如果 webbrowser 失败，尝试使用 Windows start 命令
                self.log.warning(f"webbrowser 打开失败，尝试 Windows start 命令: {browser_err}")
                subprocess.run(['start', '', url], shell=True, check=True)
                self.log.info(f"使用 start 命令成功打开URL: {url}")

        except subprocess.CalledProcessError as e:
            self.log.error(f"打开URL失败 ({url}): {e}")
        except Exception as e:
            self.log.error(f"处理URL命令失败: {e}")