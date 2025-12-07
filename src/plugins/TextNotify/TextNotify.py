import re
import time
import keyboard
import pyperclip
from ha_mqtt_discoverable import Settings
from ha_mqtt_discoverable.sensors import Text, TextInfo

class TextNotify:
    def __init__(self, core):
        self.core = core
        self.text_entity = None

    def setup_entities(self):
        """设置MQTT实体"""
        try:
            # 使用辅助方法获取配置
            mqtt_settings = self.core.mqtt.get_mqtt_settings()
            device_info = self.core.mqtt.get_device_info(
                plugin_name="TextNotify",
                model="PCTools TextNotify"
            )

            # 创建Text实体用于接收通知
            text_info = TextInfo(
                name="Toast",
                unique_id=f"{self.core.mqtt.device_name}_TextNotify",
                device=device_info,
                icon="mdi:message",
                display_name="Toast通知"
            )

            settings = Settings(mqtt=mqtt_settings, entity=text_info)
            self.text_entity = Text(settings, command_callback=self.handle_text_command)
            self.text_entity.set_text("请输入Toast通知")

            self.core.log.info("TextNotify MQTT实体创建成功")
        except Exception as e:
            self.core.log.error(f"TextNotify MQTT设置失败: {e}")

    def handle_text_command(self, client, user_data, message):
        """处理接收到的文本命令"""
        try:
            data = message.payload.decode()
            self.core.log.info(f"订阅通知: {data}")
            if not self.extract_and_copy_verification_code(data):
                self.core.show_toast("消息通知", data)
        except Exception as e:
            self.core.log.error(f"处理文本通知失败: {e}")

    def extract_and_copy_verification_code(self, text):
        # 定义匹配验证码的正则表达式
        pattern = r'(?:[Vv]erification\s*[Cc]ode|[Cc]ode|[Aa]uth\s*[Cc]ode|验证码|驗證碼)[：:\s]*?(\d{4,8})'
        match = re.search(pattern, text)

        if match:
            # 提取验证码
            verification_code = match.group(1)

            # 将验证码复制并粘贴
            pyperclip.copy(verification_code)
            self.core.log.info(f"验证码 {verification_code} 已复制到剪贴板")
            self.core.show_toast("验证码",f"验证码为{verification_code}\n3秒后自动粘贴")
            time.sleep(3)
            keyboard.write(verification_code)
            return True
        return False




