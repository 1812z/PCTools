"""
GUI 视图层主文件
负责UI组件的创建和显示，不包含业务逻辑
"""

import time
import flet as ft
from gui_logic import GUILogic
from TrayManager import TrayManager
from Updater import UpdateChecker

# 导入页面模块
from pages.home_page import HomePage
from pages.settings_page import SettingsPage
from pages.plugin_page import PluginPage
from pages.about_page import AboutPage


class GUI:
    """GUI视图类"""

    def __init__(self, core_instance):
        """初始化GUI"""
        # 逻辑层
        self.logic = GUILogic(core_instance)
        self.core = core_instance

        # UI组件
        self.page: ft.Page = None
        self.plugins_view: ft.ListView = None

        # 外部组件
        self.tray: TrayManager = None
        self.updater: UpdateChecker = None

        # 标志
        self.show_menu_flag = False

        # 页面实例
        self.home_page = None
        self.settings_page = None
        self.plugin_page = None
        self.about_page = None

        # 设置UI回调
        self.logic.set_ui_callbacks(
            update_ui=self._update_page
        )

    def _update_page(self):
        """更新页面"""
        if self.page:
            self.page.update()

    def show_snackbar(self, message: str, duration: int = 2000):
        """显示通知条消息"""
        if not self.page:
            return

        try:
            snackbar = ft.SnackBar(
                content=ft.Text(message),
                action="OK",
                duration=duration
            )
            self.page.open(snackbar)
            self.page.update()
        except Exception as e:
            self.logic.log_debug(f"无法显示Snackbar: {e}")

    def close_windows(self):
        """关闭窗口"""
        try:
            if self.page:
                self.page.window.close()
        except RuntimeError as e:
        # 忽略事件循环相关的错误
            if "Event loop is closed" not in str(e):
                self.logic.log_error(f"关闭窗口失败: {e}")
        except Exception as e:
            self.logic.log_error(f"关闭窗口失败: {e}")

    # ===== 属性代理（为了兼容旧代码） =====

    @property
    def is_running(self):
        return self.logic.is_running

    @property
    def is_starting(self):
        return self.logic.is_starting

    @property
    def is_stopping(self):
        return self.logic.is_stopping

    # ===== 主界面 =====

    def main(self, new_page: ft.Page):
        """主界面入口"""
        self.page = new_page
        self._setup_window()

        # 初始化页面实例
        self.home_page = HomePage(self)
        self.settings_page = SettingsPage(self)
        self.plugin_page = PluginPage(self)
        self.about_page = AboutPage(self)

        # 创建标签页
        tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(text="主页", content=self.home_page.create()),
                ft.Tab(text="设置", content=self.settings_page.create()),
                ft.Tab(text="插件", content=self.plugin_page.create()),
                ft.Tab(text="关于", content=self.about_page.create()),
            ],
            on_change=self._on_tab_changed
        )

        self.page.add(tabs)

    def _setup_window(self):
        """设置窗口属性"""
        self.page.window.width = 550
        self.page.window.height = 590
        self.page.window.resizable = False
        self.page.window.maximizable = False
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.title = "PCTools"

    def _on_tab_changed(self, e):
        """标签页切换事件"""
        if e.control.selected_index == 1:  # 设置页
            self.show_snackbar("修改设置后建议重启软件")
        elif e.control.selected_index == 2:  # 插件页
            if self.logic.is_running:
                self.show_snackbar("运行时无法配置")
            self.plugin_page.update_plugin_list()

    # ===== 退出 =====

    def exit(self):
        """退出程序"""
        try:
            if self.logic.is_starting:
                self.core.show_toast("正在启动中，请稍后再试")
                return
            if self.logic.is_stopping:
                self.core.show_toast("正在停止中，请稍后再试")
                return
            if self.logic.is_running:
                self.logic.stop_service()
                self.core.show_toast("正在停止服务，即将退出")
            self.close_windows()
            if self.tray:
                self.tray.stop()
        except Exception as e:
            self.logic.log_error(f"退出异常: {e}")


# ===== 程序入口 =====

if __name__ == "__main__":
    from Core import Core

    # 初始化核心
    core = Core(None)

    # 初始化GUI
    gui = GUI(core)
    core.gui = gui

    # 初始化托盘和更新器
    gui.tray = TrayManager(gui)
    gui.updater = UpdateChecker(gui, "1812z", "PCTools", "config_example.json")
    gui.tray.start()

    # 启动方式
    if not gui.logic.get_config("auto_start", False):
        # 直接显示GUI
        ft.app(target=gui.main)
    else:
        # 后台启动
        gui.logic.start_service()
        if gui.logic.get_config("check_update", False):
            gui.updater.check_for_updates()

    # 主循环
    while gui.tray.is_running:
        try:
            if gui.show_menu_flag:
                ft.app(target=gui.main)
                gui.show_menu_flag = False
            time.sleep(1)
        except KeyboardInterrupt:
            gui.exit()