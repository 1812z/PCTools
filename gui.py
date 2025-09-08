import time
import flet as ft
import startup
from TrayManager import TrayManager
from Updater import UpdateChecker


class GUI:
    def __init__(self, core_instance):
        self.is_starting = False
        self.is_stopping = False
        self.ft = ft
        self.version = "v5.3"

        self.is_running = False
        self.show_menu_flag = False
        self.icon_flag = False
        self.core = None
        self.page = None
        self.tray = None
        self.updater = None

        self.core = core_instance

    def show_snackbar(self, message: str, duration=2000):
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
            if self.core:
                self.core.log.debug(f"窗口未找到无法显示Snackbar: {e}")

    def start(self):
        """启动服务"""
        try:
            if self.core:
                self.is_starting = True
                self.core.initialize()
                self.core.start()
                self.is_running = True
                self.is_starting = False
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
                self.page.window.close()
                return None
            return None
        except Exception as e:
            return e

    def stop(self):
        """停止服务"""
        if self.is_running and not self.is_starting and not self.is_stopping:
            self.is_stopping = True
            self.show_snackbar("停止进程中...")
            self.core.log.info("停止进程中...")
            self.core.stop()
            self.is_running = False
            self.show_snackbar("成功停止所有进程")
            self.core.log.info("成功停止所有进程")
            self.is_stopping = False
        elif not self.is_starting and not self.is_stopping:
            self.show_snackbar("都还没运行呀")
        elif not self.is_stopping:
            self.show_snackbar("启动中无法停止...")
        else:
            self.show_snackbar("如果卡死请使用任务管理器终止python进程")

    def handle_input(self, field_name, input_type="string"):
        def callback(e):
            value = e.control.value
            if input_type == "int":
                parsed_value = int(value)
            else:
                parsed_value = value
            self.core.config.set_config(field_name, parsed_value)

        return callback
    def main(self, new_page: ft.Page):
        """主要UI逻辑函数"""
        self.page = new_page
        self.page.window.width= 550
        self.page.window.height = 590
        self.page.window.resizable = False

        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.title = "PCTools"
        tab_home = ft.Tab(text="主页")
        tab_setting = ft.Tab(text="设置")
        tab_plugins = ft.Tab(text="插件")
        tab_about = ft.Tab(text="关于")

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
                self.page.open(dialog)
                self.page.update()
            else:
                self.show_snackbar("数据更新成功")
                self.page.update()

        def button_start(e):
            if self.is_running or self.is_starting:
                self.show_snackbar("请勿多次启动!")
            else:
                self.show_snackbar("启动进程...")
                if self.start():
                    self.show_snackbar("服务启动成功")

        def switch_auto_start(e):
            if e.control.value:
                self.show_snackbar(startup.add_to_startup())
                self.core.config.set_config("auto_start", True)
            else:
                self.show_snackbar(startup.remove_from_startup())
                self.core.config.set_config("auto_start", False)
            self.page.update()

        def open_repo(e):
            self.page.launch_url('https://github.com/1812z/PCTools')

        def follow(e):
            self.page.launch_url('https://space.bilibili.com/336130050')

        def tab_changed(e):
            if e.control.selected_index == 1:
                self.show_snackbar("修改设置后建议重启软件")
            elif e.control.selected_index == 2:
                if self.is_running:
                    self.show_snackbar("运行时无法配置")
                elif self.core.is_initialized is False:
                    self.show_snackbar("如需修改插件配置，请先载入插件")
                update_plugin_page()

        # 创建动态页面
        plugins_view = ft.ListView(height=450, width=450, spacing=5)

        def show_page(e, h):
            if h is None:
                self.show_snackbar("该插件没有设置页面")
                return

            try:
                bubble_page = h(e)
                dlg = ft.AlertDialog(
                    adaptive=True,
                    title=ft.Text("插件设置"),
                    content=ft.Container(
                        content=bubble_page,
                        height=300,
                        width=400,
                        margin=10,
                    ),
                    actions=[
                        ft.TextButton("返回", on_click=lambda e: e.page.close(dlg)),
                    ],
                )
                e.page.open(dlg)
                e.page.update()
            except Exception as ex:
                self.core.log.error(f"打开设置页面失败: {ex}")
                self.show_snackbar(f"打开设置失败: {ex}")

        def load_plugin_button(e):
            self.show_snackbar("初始化插件类...")
            self.core.initialize()
            update_plugin_page()

        def update_plugin_page():
            plugins_view.controls.clear()
            plugins_view.controls.append(ft.Row(
                [
                    ft.ElevatedButton("载入插件", on_click=load_plugin_button, disabled=self.core.is_initialized),
                ]
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
                    setting_disabled = False if available and handler else True
                    settings_btn = ft.IconButton(
                        icon=ft.Icons.SETTINGS,
                        icon_size=20,
                        tooltip="插件设置",
                        disabled=setting_disabled,
                        on_click=lambda e, h=handler: show_page(e, h)
                    )

                    info_btn = ft.IconButton(
                        icon=ft.Icons.INFO_OUTLINE,
                        icon_size=20,
                        tooltip=f"插件信息\n加载状态: {loaded}\n插件路径: {path}\n"
                    )

                    def create_switch_callback(plugin, settings_btn, info_btn):
                        def callback(e):
                            new_status = e.control.value
                            self.core.plugin_manage(plugin, new_status)
                            settings_btn.disabled = not new_status or setting_disabled
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
                        padding=8,
                        border=ft.border.all(2, ft.Colors.GREY),
                        border_radius=8,
                        margin=0
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

        def create_button(icon: str, text: str, on_click=None):
            return ft.ElevatedButton(
                content=ft.Row(
                    [ft.Icon(icon), ft.Text(text, weight=ft.FontWeight.W_600)],
                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                ),
                on_click=on_click,
                width=130,
                height=40
            )

        def build_setting_option(
                icon_name: str,
                title: str,
                subtitle: str,
                toggle_value: bool = False,
                on_change=None,
                control_type="switch"
        ):
            if control_type == "switch":
                right_control = ft.Switch(
                    value=toggle_value,
                    on_change=on_change,
                )
            else:
                right_control =  ft.IconButton(
                    icon=ft.Icons.ARROW_FORWARD_IOS,
                    icon_size=20,
                    on_click=on_change)

            """构建带图标的设置选项"""
            return (ft.Column(
                controls=[
                    ft.Divider(height=10),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                # 左侧图标和文字
                                ft.Row(
                                    controls=[
                                        ft.Icon(icon_name, size=25),
                                        ft.Column(
                                            controls=[
                                                ft.Text(title, weight=ft.FontWeight.BOLD),
                                                ft.Text(subtitle, size=12, color=ft.Colors.GREY_600),
                                            ],
                                            spacing=2
                                        )
                                    ],
                                    spacing=10,
                                    alignment=ft.MainAxisAlignment.START,
                                    expand=True
                                ),
                                # 右侧开关
                                right_control
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        padding=ft.padding.symmetric(vertical=5, horizontal=10),
                        on_click=on_change if on_change else None
                    )]
                )
            )



        start_button = create_button(ft.Icons.PLAY_ARROW, "开始", button_start)
        stop_button = create_button(ft.Icons.STOP_ROUNDED, "停止", lambda e: self.stop())
        send_data_button = create_button(ft.Icons.SEND_AND_ARCHIVE, "发送数据", button_send_data)
        follow_button = create_button(ft.Icons.THUMB_UP_ALT_ROUNDED, "关注我", follow)

        home_page = ft.Column(
            [
                logo,
                ft.Container(
                    content=ft.Text(
                        self.version + ' by 1812z',
                        size=20,
                    )
                ),
                ft.Container(
                    content=ft.TextButton(
                        "Github",
                        animate_size=20,
                        on_click=open_repo
                    ),
                    width=120
                ),
                            start_button,
                            stop_button,
                            send_data_button,
                            follow_button,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            run_alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            expand=True
        )

        def open_mqtt_setting(self):
            self.page.open(mqtt_setting)
            self.page.update()

        # MQTT设置
        mqtt_setting = ft.AlertDialog(
            adaptive=True,
            title=ft.Text("MQTT设置(每一项输入框按回车保存)"),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.TextField(
                            label="HA_MQTT_Broker",
                            on_submit=self.handle_input("HA_MQTT"),
                            value=self.core.config.get_config("HA_MQTT")
                        ),
                        ft.TextField(
                            label="PORT",
                            on_submit=self.handle_input("HA_MQTT_port", "int"),
                            value=self.core.config.get_config("HA_MQTT_port")
                        ),
                        ft.TextField(
                            label="HA_MQTT账户",
                            on_submit=self.handle_input("username"),
                            value=self.core.config.get_config("username")
                        ),
                        ft.TextField(
                            label="HA_MQTT密码",
                            on_submit=self.handle_input("password"),
                            value=self.core.config.get_config("password")
                        ),
                        ft.TextField(
                            label="发现前缀",
                            on_submit=self.handle_input("ha_prefix"),
                            value=self.core.config.get_config("ha_prefix")
                        ),
                        ft.TextField(
                            label="设备唯一标识符(仅支持英文字符)",
                            on_submit=self.handle_input("device_name"),
                            value=self.core.config.get_config("device_name")
                        ),
                    ]
                ),
                height=300,
                width=400,
                margin=10,
            ),
            actions=[
                ft.TextButton("返回", on_click=lambda e: e.page.close(mqtt_setting)),
            ],
        )

        setting_page = ft.ListView(
            controls=[
                logo,
                build_setting_option(
                    icon_name=ft.Icons.NETWORK_CELL,
                    title="MQTT设置",
                    subtitle="配置MQTT连接信息",
                    toggle_value=False,
                    on_change=open_mqtt_setting,
                    control_type="dialog"
                ),
                build_setting_option(
                    icon_name=ft.Icons.UPDATE,
                    title="检查更新",
                    subtitle="启动时自动检查新版本并提示",
                    toggle_value=self.core.config.get_config("check_update"),
                    on_change=lambda e: self.core.config.set_config("check_update",e.control.value)
                ),
                build_setting_option(
                    icon_name=ft.Icons.BROWSER_UPDATED,
                    title="自动更新",
                    subtitle="检查到新版本时自动更新",
                    toggle_value=self.core.config.get_config("auto_update"),
                    on_change=lambda e: self.core.config.set_config("auto_update", e.control.value)
                ),
                build_setting_option(
                    icon_name=ft.Icons.POWER_SETTINGS_NEW,
                    title="自启动",
                    subtitle="开机后自动打开程序",
                    toggle_value=self.core.config.get_config("auto_start"),
                    on_change=lambda e: switch_auto_start(e)
                ),
            ],
            spacing=15,
            padding=ft.padding.only(left=60, right=60),
            expand=True
        )

        plugin_page = ft.Column(
                [
                    ft.Container(height=10),
                    ft.Row(
                        [
                            ft.Container(width=20),
                            plugins_view,
                        ]
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )

        update_component = self.updater.create_update_ui(self.page)
        about_page = ft.Column(
            [
                update_component,
                ft.Container(
                    content=ft.Text(
                        "感谢使用,求投喂,有需要的功能也可以联系我(VX: |1812z| )，会尽快写(AI)好",
                        size=15
                    )
                ),
                ft.Container(
                    content=ft.Image(
                        src="img\\wechat.png",
                        fit=ft.ImageFit.CONTAIN,
                        width=300
                    )
                ),
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        tab_home.content = home_page
        tab_setting.content = setting_page
        tab_plugins.content = plugin_page
        tab_about.content = about_page
        tabs = ft.Tabs(
            selected_index=0,
            tabs=[tab_home, tab_setting, tab_plugins,tab_about],
            on_change=tab_changed
        )

        self.page.add(tabs)

    def exit(self):
        try:
            if self.is_running:
                self.stop()
            self.close_windows()
            self.tray.stop()
        except Exception as e:
            self.core.log.error(f"退出异常: {e}")

icon_flag = True
gui = None
core = None
if __name__ == "__main__":
    from Core import Core
    core = Core(None)
    gui = GUI(core)
    core.gui = gui
    gui.tray = TrayManager(gui)
    gui.updater = UpdateChecker(gui, "1812z", "PCTools", "config_example.json")
    gui.tray.start()

    if not gui.core.config.get_config("auto_start"):
        ft.app(target=gui.main)
    else:
        gui.start()
        if gui.core.config.get_config("check_update"):
            gui.updater.check_for_updates()

    while gui.tray.is_running:
        try:
            if gui.show_menu_flag:
                gui.show_menu_flag = False
                ft.app(target=gui.main)
            time.sleep(1)
        except KeyboardInterrupt as e:
            gui.exit()
