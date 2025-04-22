import threading
import time
from PIL import Image
import flet as ft
from Update_State_Data import discovery_aida64, send_data
from flet_core import MainAxisAlignment, CrossAxisAlignment
from web_task import FlaskAppManager
from timer import start_task, stop_task
from MQTT import start_mqtt, stop_mqtt_loop
from Command import discovery as discovery_comm,subcribe
import pystray
import startup
import HA_widget_task
from Hotkey_capture import load_hotkeys, capture_hotkeys, listen_hotkeys, stop_listen, send_discovery
from Toast import show_toast
from WIndows_Listener import listener as window_listener
from config_manager import load_config,set_config,get_config
from logger_manager import Logger

version = "V4.5"

manager = FlaskAppManager('0.0.0.0', 5000)
page = None
logger = Logger("Gui")

def show_snackbar(page: ft.Page, message: str):
    snackbar = ft.SnackBar(
        content=ft.Text(message),
        action="OK",
        action_color=ft.colors.WHITE,
        duration=2000
    )
    page.snack_bar = snackbar
    page.snack_bar.open = True
    page.update()

def start():
    try:
        if fun2:
            discovery_comm()
            if start_mqtt() == 0:
                subcribe()
            else:
                show_toast("MQTT订阅失败,请检查MQTT配置")
                return
        if fun1 or fun2:
            discovery_aida64()
            start_task()
        if fun3:
            manager.start()
        if fun5:
            HA_widget_task.start_ha_widget()
        if fun6:
            listen_hotkeys()
        if fun7:
            window_listener.start()
    except:
        logger.error("服务启动失败，请检查日志")
        show_toast("服务启动失败，请检查日志")


def save_hotkeys_to_file():
    with open('hotkeys.txt', 'w') as file:
        for hotkey in hotkeys:
            file.write(hotkey + '\n')


def close_windows():
    try:
        page.window_destroy()
    except:
        return
    

def stop():
    global run_flag
    if run_flag == True:
        if page.window_visible:
            show_snackbar(page, "停止进程中...")
        logger.info("停止进程中...")
        if fun1:
            stop_task()
        if fun2:
            stop_mqtt_loop()
        if fun3:
            manager.stop()
        if fun5:
            HA_widget_task.stop_ha_widget()
        if fun6:
            stop_listen()
        if fun7:
            window_listener.stop()

        run_flag = False
        show_snackbar(page, "成功停止所有进程")
        logger.info("成功停止所有进程")
    else:
        show_snackbar(page, "都还没运行呀")

def main(newpage: ft.Page):
    global page
    page = newpage

    page.window_width = 600
    page.window_height = 590
    page.theme_mode = ft.ThemeMode.LIGHT
    page.title = "PCTools"
    page.window_resizable = True
    home = ft.Tab(text="主页")
    setting = ft.Tab(text="设置")
    tab_hotkey = ft.Tab(text="快捷键")
    
    def button_send_data(e):
        try: 
            discovery_aida64()
            result = send_data()    
        except :
            dialog = ft.AlertDialog(
            title=ft.Text("错误"),
            content=ft.Text(value="数据更新失败"),
            scrollable=True
            )
            page.dialog = dialog
            dialog.open = True
            page.update()
        else:
            dialog = ft.AlertDialog(
            title=ft.Text("数据更新成功"),
            content=ft.Text(value=result),
            scrollable=True
            )
            page.dialog = dialog
            dialog.open = True
            page.update()

    def button_start(e):
        global run_flag
        if run_flag:
            show_snackbar(page, "请勿多次启动!")
        elif fun1 == False and fun2 == False and fun3 == False and fun5 == False:
            show_snackbar(page, "未勾选任何服务")
        else:
            run_flag = True
            show_snackbar(page, "启动进程...")
            start()
            show_snackbar(page, "服务启动成功")

    def switch_fun4(e,button):
        global fun4
        if fun4:
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
        fun4 = not fun4
        set_config("fun4", fun4)
        page.update()

    def handle_input(field_name):
        def callback(e):
            value = e.control.value
            if value.isdigit():
                parsed_value = int(value)
            else:
                parsed_value = value  
            set_config(field_name, parsed_value)
        return callback

    def button_switch(field_name):
        def callback(e):
            value = e.control.value
            set_config(field_name, value)
        return callback
    
    def open_repo(e):
        page.launch_url('https://github.com/1812z/PCTools')

    def follow(e):
        page.launch_url('https://space.bilibili.com/336130050')

    def button_add_hotkey(e):
        if run_flag == False:
            show_snackbar(page, "将记录按下的所有按键,按ESC停止并保存")
            new_hotkey = capture_hotkeys()
            show_snackbar(page, "已添加新快捷键" + new_hotkey)
            hotkeys.append(new_hotkey)
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
        hotkeys.remove(hotkey)
        save_hotkeys_to_file()
        update_hotkey_list()
        
    def tab_changed(e):
        if e.control.selected_index == 1:
            show_snackbar(page,"输入每一项数据后，请使用回车键保存")

    def update_hotkey_list():
        # 更新列表视图
        hotkey_view.controls.clear()
        if hotkeys:
            for hotkey in hotkeys:
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

    # 创建快捷键页面
    hotkey_view = ft.ListView(height=320, width=600, spacing=10)

    fun4_button = ft.ElevatedButton(
        content=ft.Row(
            [
                ft.Icon(ft.icons.AUTO_AWESOME),
                ft.Text("自启动", weight=ft.FontWeight.W_600),
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
        ),
        on_click=lambda e: switch_fun4(e,fun4_button),
        width=130,
        height=40
    )
    
    home_page = [

        ft.Column(
            [
                ft.Container(
                    content=ft.Image(
                        src="img\\home-assistant-wordmark-with-margins-color-on-light.png",
                        fit=ft.ImageFit.CONTAIN,
                        width=500
                    ),
                ),
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
                ft.Row(
                    []
                ),
                ft.ElevatedButton(
                    content=ft.Row(
                        [
                            ft.Icon(ft.icons.PLAY_ARROW_ROUNDED),
                            ft.Text("运行", weight=ft.FontWeight.W_600),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_AROUND,
                    ),
                    on_click=button_start,
                    width=130,
                    height=40
                ),
                ft.ElevatedButton(
                    content=ft.Row(
                        [
                            ft.Icon(ft.icons.STOP_ROUNDED),
                            ft.Text("停止", weight=ft.FontWeight.W_600),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_AROUND,
                    ),
                    on_click=lambda e: stop(),
                    width=130,
                    height=40
                ),
                ft.ElevatedButton(
                    content=ft.Row(
                        [
                            ft.Icon(ft.icons.SEND_AND_ARCHIVE),
                            ft.Text("发送数据", weight=ft.FontWeight.W_600),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_AROUND,
                    ),
                    on_click=button_send_data,
                    width=130,
                    height=40
                ),
                fun4_button,
                ft.ElevatedButton(
                    content=ft.Row(
                        [
                            ft.Icon(ft.icons.THUMB_UP_ALT_ROUNDED),
                            ft.Text("关注我", weight=ft.FontWeight.W_600),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_AROUND,
                    ),
                    on_click=follow,
                    width=130,
                    height=40
                ),
            ],
            alignment=MainAxisAlignment.CENTER,
            horizontal_alignment=CrossAxisAlignment.CENTER,
        )
    ]

    setting_page = [
        ft.Column(
            [
                ft.Container(
                    content=ft.Image(
                        src="img\\home-assistant-wordmark-with-margins-color-on-light.png",
                        fit=ft.ImageFit.CONTAIN,
                        width=500
                    ),
                ),
                ft.Row(
                    [
                        ft.Container(width=90),
                        ft.Column(
                        [
                            ft.Switch(label="监控反馈", label_position='left',
                                    scale=1.2, value=fun1, on_change=button_switch("fun1")),
                            ft.Switch(label="远程命令", label_position='left',
                                    scale=1.2, value=fun2, on_change=button_switch("fun2")),
                            ft.Switch(label="画面传输", label_position='left',
                                    scale=1.2, value=fun3, on_change=button_switch("fun3")),
                            ft.Switch(label="网页部件", label_position='left', scale=1.2,
                                    value=fun5, on_change=button_switch("fun5")),
                            ft.Switch(label="前台监听", label_position='left', scale=1.2,
                                    value=fun7, on_change=button_switch("fun7"),tooltip="实时反馈前台应用名称"),
                            ft.Switch(label="  显示器  ", label_position='left', scale=1.2,
                                    value=fun7, on_change=button_switch("monitor_supported"),tooltip="开启后支持读取/控制显示器亮度等")
                            ]
                            ),
                            ft.Container(width=10),
                        ft.Column(
                            [
                                ft.Row([
                                    ft.TextField(label="HA_MQTT_Broker", width=130,
                                                on_submit=handle_input("HA_MQTT"), value=read_ha_broker),
                                    ft.TextField(label="PORT", width=60,
                                                on_submit=handle_input("HA_MQTT_port"), value=read_port)
                                    ]),
                                ft.TextField(label="HA_MQTT账户", width=200,
                                            on_submit=handle_input("username"), value=read_user),
                                ft.TextField(label="HA_MQTT密码", width=200,
                                            on_submit=handle_input("password"), value=read_password),
                                ft.TextField(label="侧边栏网址(https://)", width=200,
                                            on_submit=handle_input("url"), value=read_url),
                                ft.Row([
                                    ft.TextField(label="数据发送间隔", width=100,
                                                on_submit=handle_input("interval"), value=read_interval),
                                    ft.TextField(label="设备标识符", width=90,
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
                ft.Container(
                    content=ft.Image(
                        src="img\\home-assistant-wordmark-with-margins-color-on-light.png",
                        fit=ft.ImageFit.CONTAIN,
                        width=500
                    ),
                ),
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
    home.content = ft.Column(controls=home_page)
    setting.content = ft.Column(controls=setting_page)
    tab_hotkey.content = ft.Column(controls=hotkey_page)
    tabbar = ft.Tabs(on_change=tab_changed)
    tabbar.tabs = [home, setting, tab_hotkey]
    page.add(tabbar)
    page.update()
    update_hotkey_list()


def on_exit(icon, item):
    global icon_flag
    global run_flag
    if run_flag == False:
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
    global run_flag
    global hotkeys
    run_flag = False
    threading.Thread(target=icon_task).start()
    hotkeys = load_hotkeys()

    fun1 = get_config("fun1")
    fun2 = get_config("fun2")
    fun3 = get_config("fun3")
    fun4 = get_config("fun4")
    fun5 = get_config("fun5")
    fun6 = get_config("fun6")
    fun7 = get_config("fun7")
  
    suppress = get_config("suppress")
    hotkey_notify = get_config("hotkey_notify")
    read_user = get_config("username")
    read_password = get_config("password")
    read_interval = get_config("interval")
    read_ha_broker = get_config("HA_MQTT")
    read_port = get_config("HA_MQTT_port")
    read_device_name = get_config("device_name")
    read_url = get_config("url")

    if fun4:
        run_flag = True
        start()
    else:
        ft.app(target=main)
    while icon_flag:
        time.sleep(1)
        if show_menu_flag:
            show_menu_flag = False
            ft.app(target=main)
