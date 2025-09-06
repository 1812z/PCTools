import threading
import pystray
from PIL import Image


class TrayManager:
    def __init__(self, gui):
        self.stop_event = threading.Event()
        self.icon = None
        self.thread = None
        self.gui = gui
        self.is_running = False
    def icon_task(self):
        """系统托盘图标任务"""
        image = Image.open("img\\logo.png")

        def on_clicked(icon, item):
            if str(item) == "打开主界面":
                self.gui.show_menu_flag = True
            elif str(item) == "退出":
                self.gui.exit()

        menu = (pystray.MenuItem('打开主界面', on_clicked), pystray.MenuItem('退出', on_clicked))
        self.icon = pystray.Icon("PCTools", image, "PCTools", menu)

        self.icon.run()
        self.gui.core.log.info("托盘线程已退出")

    def start(self):
        """启动托盘线程"""
        self.thread = threading.Thread(target=self.icon_task, daemon=True)
        self.thread.start()
        self.is_running = True

    def stop(self):
        """停止程序"""
        if not self.is_running:
            return
        self.stop_event.set()
        if self.icon is not None:
            self.icon.stop()
            self.thread = None
        self.is_running = False