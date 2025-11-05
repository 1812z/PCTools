import subprocess

class OpenURL:
    def __init__(self, core):
        self.core = core

        # 定义在前端或配置中可显示的实体
        self.config = [
            {
                'name': '打开URL',
                'entity_type': 'text',
                'entity_id': 'OpenURL',
                'icon': 'mdi:earth'
            }
        ]

    def handle_mqtt(self, key, data):
        """
        处理 MQTT 消息，根据 key 执行相应操作
        """
        if key == 'OpenURL':
            url = data.strip()
            try:
                # 方式一：使用 webbrowser
                # webbrowser.open(url)

                # 方式二（可选）：使用 Windows 的 start 命令
                subprocess.run(['start', '', url], shell=True)

                self.core.log.info(f"打开URL: {url}")
            except Exception as e:
                self.core.log.error(f"打开URL失败: {url}, 错误: {e}")
