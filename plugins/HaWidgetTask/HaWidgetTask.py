import multiprocessing
import os
import sys
import flet as ft

def run_ha_widget():
    from HaWidgetTask import HA_widget
    HA_widget.main()

class HaWidgetTask:
    def __init__(self, core):
        self.core = core
        self.process = None

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
            self.core.set_plugin_config("HaWidgetTask", "Widget_url", str(value))
        return callback

    def setting_page(self, e):
        """设置页面"""
        return ft.Column(
            [
                ft.TextField(label="网页URL", width=250,
                             on_submit=self.save_url(), value=self.core.get_plugin_config("HaWidgetTask", "Widget_url", "https://bing.com")),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )




