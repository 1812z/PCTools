import multiprocessing
import os
import sys
import flet as ft

PLUGIN_NAME = "Ha侧边栏"
PLUGIN_VERSION = "1.0"
PLUGIN_AUTHOR = "1812z"
PLUGIN_DESCRIPTION = "按下快捷键(默认Menu)快速开启Ha网页，需要自定义网页Url"

def run_ha_widget():
    from Widget import _HA_widget
    _HA_widget.main()

class HA_widget_task:
    def __init__(self, core):
        self.core = core
        self.process = None

        self.read_Widget_url = self.core.config.get_config("Widget_url")

        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)

    def start(self):
        try:
            self.process = multiprocessing.Process(target=run_ha_widget)
            self.process.start()
            self.core.log.info(f"HA_widget.py 已启动，进程ID: {self.process.pid}")
        except Exception as e:
            self.core.log.error(f"❌ 加载 HA_widget.py  失败: {str(e)}")

    def stop(self):
        if self.process.is_alive():
            self.core.log.debug("小部件进程强制终止。")
            self.process.kill()
        else:
            self.core.log.debug("小部件进程已停止。")

    def save_url(self):
        def callback(e):
            value = e.control.value
            self.core.config.set_config("Widget_url", str(value))
        return callback

    def setting_page(self, e):
        """设置页面"""
        return ft.Column(
            [
                ft.TextField(label="网页URL", width=250,
                             on_submit=self.save_url(), value=self.read_Widget_url),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )




