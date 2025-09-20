import re
import time
import keyboard
import pyperclip

PLUGIN_NAME = "Toast通知"
PLUGIN_VERSION = "1.0"
PLUGIN_AUTHOR = "1812z"
PLUGIN_DESCRIPTION = "显示来自Ha输入框的通知内容"

class TextNotify:
    def __init__(self, core):
        self.core = core

        self.config = [
            {
                'name': 'Toast通知',
                'entity_type': 'text',
                'entity_id': 'TextNotify',
                'icon': 'mdi:message'
            }
        ]

    def handle_mqtt(self, topic, data):
        self.core.log.info(f"订阅通知: {data}")
        if not self.extract_and_copy_verification_code(data):
            self.core.show_toast("消息通知", data)

    def extract_and_copy_verification_code(self, text):
        # 定义匹配验证码的正则表达式
        pattern = r'(?:[Vv]erification\s*[Cc]ode|[Cc]ode|[Aa]uth\s*[Cc]ode|验证码|驗證碼)[：:\s]*?(\d{4,8})'
        match = re.search(pattern, text)

        if match:
            # 提取验证码
            verification_code = match.group(2)

            # 将验证码复制并粘贴
            pyperclip.copy(verification_code)
            self.core.log.info(f"验证码 {verification_code} 已复制到剪贴板")
            self.core.show_toast("验证码",f"验证码为{verification_code}\n3秒后自动粘贴")
            time.sleep(3)
            keyboard.write(verification_code)
            return True
        return False




