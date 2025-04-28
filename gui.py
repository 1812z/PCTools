import threading
import time
from PIL import Image
import flet as ft
from flet_core import MainAxisAlignment, CrossAxisAlignment
import pystray
import startup


class GUI:
    def __init__(self, core_instance):
        self.ft = ft
        self.version = "V5.0"
        self.page = None

        self.show_menu_flag = False
        self.icon_flag = False
        self.core = None
        self.is_running = False

        self.auto_start = core.config.get_config("auto_start")
        self.read_user = core.config.get_config("username")
        self.read_password = core.config.get_config("password")
        self.read_ha_broker = core.config.get_config("HA_MQTT")
        self.read_port = core.config.get_config("HA_MQTT_port")
        self.read_device_name = core.config.get_config("device_name")
        self.core = core_instance


    def show_snackbar(self, message: str):
        """显示通知条消息"""
        if not self.page:
            return
        try:
            snackbar = ft.SnackBar(
                content=ft.Text(message),
                action="OK",
                duration=2000
            )
            self.page.snack_bar = snackbar
            snackbar.open = True
            self.page.update()
        except Exception as e:
            if self.core:
                self.core.log.debug(f"窗口未找到无法显示Snackbar: {e}")

    def start(self):
        """启动服务"""
        try:
            if self.core:
                self.core.initialize()
                self.core.start()
                self.is_running = True
                return True
            return False
        except Exception as e:
            if self.core:
                self.core.log.error(f"服务启动失败: {e}")
                self.core.show_toast(f"错误", "服务启动失败: {e}")
            return False


    def close_windows(self):
        """关闭窗口"""
        try:
            if self.page:
                self.page.window_destroy()
        except Exception as e:
            return e

    def stop(self):
        """停止服务"""
        if self.is_running:
            self.show_snackbar("停止进程中...")
            if self.core:
                self.core.log.info("停止进程中...")
                self.core.stop()
            self.is_running = False
            self.show_snackbar("成功停止所有进程")
            if self.core:
                self.core.log.info("成功停止所有进程")
        else:
            self.show_snackbar("都还没运行呀")

    def main(self, new_page: ft.Page):
        """主要UI逻辑函数"""
        self.page = new_page
        self.page.window_width = 550
        self.page.window_height = 590
        self.page.window_resizable = False

        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.title = "PCTools"
        tab_home = ft.Tab(text="主页")
        tab_setting = ft.Tab(text="设置")
        tab_plugins = ft.Tab(text="插件")

        def button_send_data(e):
            try:
                self.core.initialize()
                self.core.update_module_status()
            except Exception as e:
                dialog = ft.AlertDialog(
                    title=ft.Text("错误"),
                    content=ft.Text(value=f"数据更新失败:{e}"),
                    scrollable=True
                )
                self.page.dialog = dialog
                dialog.open = True
                self.page.update()
            else:
                self.show_snackbar("数据更新成功")
                self.page.update()

        def button_start(e):
            if self.is_running:
                self.show_snackbar("请勿多次启动!")
            else:
                self.show_snackbar("启动进程...")
                if self.start():
                    self.show_snackbar("服务启动成功")

        def switch_auto_start(e, button):
            if self.auto_start:
                button.content = ft.Row(
                    [
                        ft.Icon(ft.icons.AUTO_AWESOME),
                        ft.Text("自启动OFF", weight=ft.FontWeight.W_600),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                )
                self.show_snackbar(startup.remove_from_startup())
            else:
                button.content = ft.Row(
                    [
                        ft.Icon(ft.icons.AUTO_AWESOME),
                        ft.Text("自启动ON", weight=ft.FontWeight.W_600),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                )
                self.show_snackbar(startup.add_to_startup())
            self.auto_start = not self.auto_start
            self.core.config.set_config("auto_start", self.auto_start)
            self.page.update()

        def handle_input(field_name):
            def callback(e):
                value = e.control.value
                if value.isdigit():
                    parsed_value = int(value)
                else:
                    parsed_value = value
                self.core.config.set_config(field_name, parsed_value)
                if self.core.mqtt:
                    self.core.mqtt.reconnect()

            return callback


        def open_repo(e):
            self.page.launch_url('https://github.com/1812z/PCTools')

        def follow(e):
            self.page.launch_url('https://space.bilibili.com/336130050')

        def tab_changed(e):
            if e.control.selected_index == 1:
                self.show_snackbar("输入每一项数据后，请使用回车键保存")
            elif e.control.selected_index == 2:
                if self.is_running:
                    self.show_snackbar("运行时无法配置插件")
                update_plugin_page()

        # 创建动态页面
        plugins_view = ft.ListView(height=450, width=450, spacing=5)


        def show_page(e,h):
            bubble_page = h(e)

            def close_dialog(e):
                dlg.open = False
                e.page.update()

            dlg = ft.AlertDialog(
                title=ft.Text("设置"),
                content=bubble_page[0],
                actions=[
                    ft.TextButton("确定", on_click=close_dialog),
                ],
            )

            e.page.dialog = dlg
            dlg.open = True
            e.page.update()

        def load_plugin_button(e):
            self.show_snackbar("初始化插件类...")
            self.core.initialize()
            update_plugin_page()

        def update_plugin_page():
            plugins_view.controls.clear()
            plugins_view.controls.append(ft.Row(
                [ft.ElevatedButton("载入插件", on_click=load_plugin_button)]
            ))

            if self.core.plugin_paths:
                for plugin in list(self.core.plugin_paths.keys()):
                    status = False if plugin in self.core.disabled_plugins else True
                    loaded = plugin in self.core.plugin_instances.keys()

                    available = status and loaded and not self.is_running
                    path = self.core.plugin_paths.get(plugin)

                    # 创建控件
                    plugin_name = plugin
                    if plugin in self.core.plugin_instances.keys():
                        plugin_name = "✅" + plugin
                    elif plugin in self.core.error_plugins:
                        plugin_name = "❌" + plugin
                    name_text = ft.Text(plugin_name, size=16, weight=ft.FontWeight.BOLD, width=250)

                    handler = getattr(self.core.plugin_instances.get(plugin), "setting_page", None)
                    settings_btn = ft.IconButton(
                        icon=ft.icons.SETTINGS,
                        icon_size=20,
                        tooltip="插件设置",
                        disabled=False if available and handler else True,
                        on_click=lambda e, h=handler: show_page(e,h)
                    )

                    info_btn = ft.IconButton(
                        icon=ft.icons.INFO_OUTLINE,
                        icon_size=20,
                        tooltip=f"插件信息\n加载状态: {loaded}\n插件路径: {path}\n"
                    )

                    def create_switch_callback(plugin, settings_btn, info_btn):
                        def callback(e):
                            new_status = e.control.value
                            self.core.plugin_manage(plugin, new_status)
                            settings_btn.disabled = not new_status
                            info_btn.disabled = not new_status
                            e.page.update()

                        return callback

                    switch = ft.Switch(
                        value=status,
                        tooltip="启用/禁用插件",
                        on_change=create_switch_callback(plugin, settings_btn, info_btn),
                        disabled=self.is_running
                    )

                    # 将控件组合成一行
                    row = ft.Row(
                        controls=[
                            name_text,
                            settings_btn,
                            info_btn,
                            switch
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10
                    )

                    # 添加边框和边距
                    container = ft.Container(
                        content=row,
                        padding=10,
                        border=ft.border.all(1, ft.colors.GREY_300),
                        border_radius=5,
                        margin=ft.margin.only(bottom=10)
                    )

                    plugins_view.controls.append(container)
            else:
                info_row = ft.Row(
                    [
                        ft.Container(width=180),
                        ft.Text("TAT..啥都木有", size=15)
                    ])
                plugins_view.controls.append(info_row)
            self.page.update()
            return

        logo = ft.Container(
            content=ft.Image(
                src="img\\home-assistant-wordmark-with-margins-color-on-light.png",
                fit=ft.ImageFit.CONTAIN,
                width=500
            )
        )

        auto_start_button = ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(ft.icons.AUTO_AWESOME),
                    ft.Text("自启动", weight=ft.FontWeight.W_600),
                ],
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
            ),
            on_click=lambda e: switch_auto_start(e, auto_start_button),
            width=130,
            height=40
        )

        def create_button(icon, text, on_click):
            return ft.ElevatedButton(
                content=ft.Row(
                    [ft.Icon(icon), ft.Text(text, weight=ft.FontWeight.W_600)],
                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                ),
                on_click=on_click,
                width=130,
                height=40
            )

        start_button = create_button(ft.icons.PLAY_ARROW, "开始", button_start)
        stop_button = create_button(ft.icons.STOP_ROUNDED, "停止", lambda e: self.stop())
        send_data_button = create_button(ft.icons.SEND_AND_ARCHIVE, "发送数据", button_send_data)
        follow_button = create_button(ft.icons.THUMB_UP_ALT_ROUNDED, "关注我", follow)

        home_page = [
            ft.Column(
                [
                    logo,
                    ft.Container(
                        content=ft.Text(
                            self.version + ' by 1812z',
                            size=20,
                            ),
                    ),
                    ft.Container(
                        content=ft.TextButton(
                            "Github",
                            animate_size=20, on_click=open_repo
                        ),
                    ),
                    start_button,
                    stop_button,
                    send_data_button,
                    auto_start_button,
                    follow_button,
                ],
                alignment=MainAxisAlignment.CENTER,
                horizontal_alignment=CrossAxisAlignment.CENTER,
            )
        ]

        setting_page = [
            ft.Column(
                [
                    logo,
                    ft.Row(
                        [
                            ft.Container(width=80),
                            ft.Column(
                                [
                                ]
                            ),
                            ft.Container(width=10),
                            ft.Column(
                                [
                                    ft.Row([
                                        ft.TextField(label="HA_MQTT_Broker", width=160,
                                                     on_submit=handle_input("HA_MQTT"), value=self.read_ha_broker),
                                        ft.TextField(label="PORT", width=80,
                                                     on_submit=handle_input("HA_MQTT_port"), value=self.read_port)
                                    ]),
                                    ft.TextField(label="HA_MQTT账户", width=250,
                                                 on_submit=handle_input("username"), value=self.read_user),
                                    ft.TextField(label="HA_MQTT密码", width=250,
                                                 on_submit=handle_input("password"), value=self.read_password),
                                    ft.Row([
                                        ft.TextField(label="设备标识符", width=250,
                                                     on_submit=handle_input("device_name"), value=self.read_device_name)
                                    ]

                                )],
                            ),
                        ]
                    ),
                ],
                alignment=MainAxisAlignment.CENTER,
                horizontal_alignment=CrossAxisAlignment.CENTER,
            )
        ]



        plugin_page = [
            ft.Column(
                [
                    ft.Container(height=10),
                    ft.Row(
                        [
                            ft.Container(width=20),
                            plugins_view,
                        ]
                    )
                ],
                alignment=MainAxisAlignment.CENTER,
                horizontal_alignment=CrossAxisAlignment.CENTER,
            )
        ]
        tab_home.content = ft.Column(controls=home_page)
        tab_setting.content = ft.Column(controls=setting_page)
        tab_plugins.content = ft.Column(controls=plugin_page)
        tabs = ft.Tabs(
            selected_index=0,
            tabs=[tab_home, tab_setting, tab_plugins],
            on_change=tab_changed,
        )

        self.page.add(tabs)


    def on_exit(self):
        """退出前执行的函数"""
        global icon_flag
        try:
            if icon_flag:
                icon_flag = False
            if self.is_running:
                self.stop()
            self.close_windows()
        except Exception as e:
            if self.core:
                self.core.log.error(f"退出异常: {e}")

def show_menu():
    global show_menu_flag
    show_menu_flag = True

def icon_task():
    """系统托盘图标任务"""
    global icon_flag
    icon_flag = True
    image = Image.open("img\\logo.png")

    def on_clicked(icon, item):
        if str(item) == "打开主界面":
            show_menu()
        elif str(item) == "退出":
            icon.stop()
            gui.on_exit()

    menu = (pystray.MenuItem('打开主界面', on_clicked), pystray.MenuItem('退出', on_clicked))
    icon = pystray.Icon("PCTools", image, "PCTools", menu)
    icon.run()



def main(page):
    gui.main(page)


icon_flag = True
show_menu_flag = False
gui = None
core = None
if __name__ == "__main__":
    threading.Thread(target=icon_task).start()
    from Core import Core
    core = Core(gui)
    gui = GUI(core)

    if not gui.auto_start:
        ft.app(target=main)
    else:
        gui.start()

    while icon_flag:
        try:
            time.sleep(1)
            if show_menu_flag:
                show_menu_flag = False
                ft.app(target=main)
        except KeyboardInterrupt as e:
            gui.on_exit()




