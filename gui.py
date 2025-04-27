import threading
import time
from PIL import Image
import flet as ft
from flet_core import MainAxisAlignment, CrossAxisAlignment
import pystray

import startup

from Core import Core

version = "V5.0"

page = None


def show_snackbar(page: ft.Page, message: str):
    if not page:
        return
    try:
        snackbar = ft.SnackBar(
            content=ft.Text(message),
            action="OK",
            duration=2000
        )
        page.snack_bar = snackbar
        snackbar.open = True
        page.update()
    except Exception as e:
        core.log.debug(f"窗口未找到无法显示Snackbar: {e}")

def start():
    try:
        core.initialize()
        core.start()
        return True
    except Exception as e:
        core.log.error(f"服务启动失败: {e}")
        core.show_toast(f"错误", "服务启动失败: {e}")
        return False

def save_hotkeys_to_file():
    with open('hotkeys.txt', 'w') as file:
        for hotkey in core.Hotkey.hotkeys:
            file.write(hotkey + '\n')


def close_windows():
    try:
        page.window_destroy()
    except Exception as e:
        return e


def stop():
    global is_running
    if is_running:
        show_snackbar(page, "停止进程中...")
        core.log.info("停止进程中...")
        core.stop()
        is_running = False
        show_snackbar(page, "成功停止所有进程")
        core.log.info("成功停止所有进程")
    else:
        show_snackbar(page, "都还没运行呀")

def main(new_page: ft.Page):
    global page
    page = new_page
    page.window_width = 600
    page.window_height = 590
    page.window_resizable = False

    page.theme_mode = ft.ThemeMode.LIGHT
    page.title = "PCTools"
    tab_home = ft.Tab(text="主页")
    tab_setting = ft.Tab(text="设置")
    tab_hotkey = ft.Tab(text="快捷键")
    tab_plugins = ft.Tab(text="插件")


    def button_send_data(e):
        try:
            core.initialize()
            core.update_module_status()
        except Exception as e:
            dialog = ft.AlertDialog(
            title=ft.Text("错误"),
            content=ft.Text(value=f"数据更新失败:{e}"),
            scrollable=True
            )
            page.dialog = dialog
            dialog.open = True
            page.update()
        else:
            show_snackbar(page, "数据更新成功")
            page.update()

    def button_start(e):
        global is_running
        if is_running:
            show_snackbar(page, "请勿多次启动!")
        else:
            show_snackbar(page, "启动进程...")
            if start():
                is_running = True
                show_snackbar(page, "服务启动成功")


    def switch_auto_start(e,button):
        global auto_start
        if auto_start :
            button.content=ft.Row(
            [
                ft.Icon(ft.icons.AUTO_AWESOME),
                ft.Text("自启动OFF", weight=ft.FontWeight.W_600),
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
            )
            show_snackbar(page, startup.remove_from_startup())
        else:
            button.content=ft.Row(
            [
                ft.Icon(ft.icons.AUTO_AWESOME),
                ft.Text("自启动ON", weight=ft.FontWeight.W_600),
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
            )
            show_snackbar(page, startup.add_to_startup())
        auto_start  = not auto_start
        core.config.set_config("auto_start", auto_start )
        page.update()

    def handle_input(field_name):
        def callback(e):
            value = e.control.value
            if value.isdigit():
                parsed_value = int(value)
            else:
                parsed_value = value
            core.config.set_config(field_name, parsed_value)
            if core.mqtt:
                core.mqtt.reconnect()
        return callback

    def button_switch(field_name):
        def callback(e):
            value = e.control.value
            core.config.set_config(field_name, value)
        return callback

    def open_repo(e):
        page.launch_url('https://github.com/1812z/PCTools')

    def follow(e):
        page.launch_url('https://space.bilibili.com/336130050')

    def button_add_hotkey(e):
        if is_running == False:
            show_snackbar(page, "将记录按下的所有按键,按ESC停止并保存")
            new_hotkey = core.Hotkey.capture_hotkeys()
            show_snackbar(page, "已添加新快捷键" + new_hotkey)
            core.Hotkey.hotkeys.append(new_hotkey)
            update_hotkey_list()
        else:
            show_snackbar(page, "请先停止服务")

    def button_listen_hotkeys(e):
        if listen_hotkeys() == 0:
            show_snackbar(page, "开始测试快捷键监听")
        else:
            show_snackbar(page, "已经启动快捷键监听")

    def button_stop_listen(e):
        if stop_listen() == 0:
            show_snackbar(page, "停止快捷键监听")
        else:
            show_snackbar(page, "请先启动快捷键监听")

    def delete_hotkey(hotkey):
        # 从列表中删除快捷键并更新视图
        core.Hotkey.hotkeys.remove(hotkey)
        save_hotkeys_to_file()
        update_hotkey_list()

    def tab_changed(e):
        if e.control.selected_index == 1:
            show_snackbar(page,"输入每一项数据后，请使用回车键保存")
        elif e.control.selected_index == 2:
            update_hotkey_list()
        elif e.control.selected_index == 3:
            if is_running:
                show_snackbar(page, "运行时无法配置插件")
            update_plugin_page()

    # 创建动态页面
    hotkey_view = ft.ListView(height=320, width=600, spacing=10)
    plugins_view = ft.ListView(height=400, width=500, spacing=5)

    def update_hotkey_list():
        # 更新列表视图
        hotkey_view.controls.clear()
        if core.is_initialized and core.Hotkey.hotkeys:
            for hotkey in core.Hotkey.hotkeys:
                hotkey_view.controls.append(
                    ft.Row(
                        [
                            ft.Container(width=85),
                            ft.ElevatedButton(
                                content=ft.Row(
                                    [
                                        ft.Text(
                                            hotkey, weight=ft.FontWeight.W_600, size=17),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                                ),
                                width=120,
                                height=40
                            ),
                            ft.Container(width=40),
                            ft.IconButton(
                                ft.icons.DELETE, on_click=lambda e, h=hotkey: delete_hotkey(h)),
                        ],
                    )
                )
        else:
            hotkey_view.controls.append(ft.Row(
                [
                    ft.Container(width=150),
                    ft.Text("TAT..啥都木有", size=15)
                ])
            )
        hotkey_view.update()

    def update_plugin_page():
        plugins_view.controls.clear()
        if core.plugin_paths:
            for plugin in list(core.plugin_paths.keys()):
                status = False if plugin in core.disabled_plugins else True
                available = not (status and not is_running)

                # 创建控件
                plugin_name = plugin
                if plugin in core.plugin_instances.keys():
                    plugin_name = "✅" + plugin
                elif plugin in core.error_plugins:
                    plugin_name = "❌" + plugin
                name_text = ft.Text(plugin_name, size=16, weight=ft.FontWeight.BOLD, width=250)

                settings_btn = ft.IconButton(
                    icon=ft.icons.SETTINGS,
                    icon_size=20,
                    tooltip="插件设置",
                    disabled=available
                )

                info_btn = ft.IconButton(
                    icon=ft.icons.INFO_OUTLINE,
                    icon_size=20,
                    tooltip="插件信息",
                    on_click=lambda e, p=plugin: print(f"查看 {p} 信息"),
                    disabled=available
                )

                def create_switch_callback(plugin, settings_btn, info_btn):
                    def callback(e):
                        new_status = e.control.value
                        core.plugin_manage(plugin, new_status)
                        settings_btn.disabled = not new_status
                        info_btn.disabled = not new_status
                        e.page.update()

                    return callback

                switch = ft.Switch(
                    value=status,
                    tooltip="启用/禁用插件",
                    on_change=create_switch_callback(plugin, settings_btn, info_btn),
                    disabled=is_running
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
        page.update()
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
        on_click=lambda e: switch_auto_start(e,auto_start_button),
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

    start_button = create_button(ft.icons.PLAY_ARROW, "开始", lambda e: start())
    stop_button = create_button(ft.icons.STOP_ROUNDED, "停止", lambda e: stop())
    send_data_button = create_button(ft.icons.SEND_AND_ARCHIVE, "发送数据", button_send_data)
    follow_button = create_button(ft.icons.THUMB_UP_ALT_ROUNDED, "关注我", follow)

    home_page = [

        ft.Column(
            [
                logo,
                ft.Container(
                    content=ft.Text(
                        version+' by 1812z',
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
                        ft.Container(width=120),
                        ft.Column(
                        [
                        ]
                            ),
                            ft.Container(width=10),
                        ft.Column(
                            [
                                ft.Row([
                                    ft.TextField(label="HA_MQTT_Broker", width=180,
                                                on_submit=handle_input("HA_MQTT"), value=read_ha_broker),
                                    ft.TextField(label="PORT", width=60,
                                                on_submit=handle_input("HA_MQTT_port"), value=read_port)
                                    ]),
                                ft.TextField(label="HA_MQTT账户", width=250,
                                            on_submit=handle_input("username"), value=read_user),
                                ft.TextField(label="HA_MQTT密码", width=250,
                                            on_submit=handle_input("password"), value=read_password),
                                ft.Row([
                                    ft.TextField(label="设备标识符", width=250,
                                                on_submit=handle_input("device_name"), value=read_device_name)
                                    ]),
                            ]
                            )
                    ]
                    )
            ], alignment=MainAxisAlignment.CENTER,
            horizontal_alignment=CrossAxisAlignment.CENTER,
        )
    ]

    hotkey_page = [
        ft.Column(
            [
                logo,
                ft.Row(
                    [
                        ft.Switch(label="快捷键", label_position='left',
                                  scale=1.2, value=fun6, on_change=button_switch("fun6"),tooltip="开启后随服务启动"),
                        ft.Container(width=20),
                        ft.Switch(label="触发通知", label_position='left',
                                scale=1.2, value=hotkey_notify, on_change=button_switch("hotkey_notify")),
                        ft.Container(width=20),
                        ft.Switch(label="阻断按键", label_position='left',
                                scale=1.2, value=suppress, on_change=button_switch("false"),tooltip="阻止快捷键被其它软件响应"),
                    ], alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Row(
                    [
                        ft.ElevatedButton(
                            content=ft.Row(
                                [
                                    # ft.Icon(ft.icons.PLUS_ONE_ROUNDED),
                                    ft.Text(
                                        "新增按键", weight=ft.FontWeight.W_600, size=17),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_AROUND,
                            ),
                            on_click=button_add_hotkey,
                            width=120,
                            height=40
                        ),

                        ft.ElevatedButton(
                            content=ft.Row(
                                [
                                    # ft.Icon(ft.icons.PLUS_ONE_ROUNDED),
                                    ft.Text(
                                        "开始监听", weight=ft.FontWeight.W_600, size=17),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_AROUND,
                            ),
                            on_click=button_listen_hotkeys,
                            width=120,
                            height=40
                        ),
                        ft.ElevatedButton(
                            content=ft.Row(
                                [
                                    # ft.Icon(ft.icons.PLUS_ONE_ROUNDED),
                                    ft.Text(
                                        "停止监听", weight=ft.FontWeight.W_600, size=17),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_AROUND,
                            ),
                            on_click=button_stop_listen,
                            width=120,
                            height=40
                        )
                    ], alignment=ft.MainAxisAlignment.CENTER
                ),
                hotkey_view
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    ]

    plugins_page = [
        ft.Container(height=10),
        ft.Row([
            ft.Container(width=10),
            ft.Text(f"插件列表", size=24, weight=ft.FontWeight.BOLD)
        ]),
        ft.Divider(height=20, color=ft.colors.BLACK),
        ft.Row([
            ft.Container(width=20),
            plugins_view
        ])
    ]

    tab_home.content = ft.Column(controls=home_page)
    tab_setting.content = ft.Column(controls=setting_page)
    tab_hotkey.content = ft.Column(controls=hotkey_page)
    tab_plugins.content = ft.Column(controls=plugins_page)

    tabbar = ft.Tabs(on_change=tab_changed)
    tabbar.tabs = [tab_home, tab_setting, tab_hotkey, tab_plugins]
    page.add(tabbar)
    page.update()
    update_hotkey_list()


def on_exit(icon, item):
    global icon_flag
    global is_running
    if is_running == False:
        icon_flag = False
        close_windows()
        time.sleep(1)
        icon.stop()
    else:
        stop()
        icon_flag = False
        close_windows()
        icon.stop()


def show_menu(icon, item):
    global show_menu_flag
    show_menu_flag = 1


def icon_task():
    image = Image.open("img/logo.png")
    icon = pystray.Icon("test_icon")
    icon.icon = image
    icon.title = "PCTools"
    icon.menu = pystray.Menu(
        pystray.MenuItem("打开主菜单", show_menu),
        pystray.MenuItem("退出托盘", on_exit)
    )
    icon.run()


show_menu_flag = False
icon_flag = True

if __name__ == "__main__":
    core = Core()
    global is_running
    is_running = False
    threading.Thread(target=icon_task).start()


    fun1 = True
    fun2 = True
    fun3 = True
    auto_start  = core.config.get_config("auto_start")
    fun5 = True
    fun6 = True
    fun7 = True

    suppress = core.config.get_config("suppress")
    hotkey_notify = core.config.get_config("hotkey_notify")
    read_user = core.config.get_config("username")
    read_password = core.config.get_config("password")
    read_interval = core.config.get_config("interval")
    read_ha_broker = core.config.get_config("HA_MQTT")
    read_port = core.config.get_config("HA_MQTT_port")
    read_device_name = core.config.get_config("device_name")
    read_url = core.config.get_config("url")
    if auto_start :
        is_running = True
        start()
    else:
        ft.app(target=main)
    while icon_flag:
        time.sleep(1)
        if show_menu_flag:
            show_menu_flag = False
            ft.app(target=main)
