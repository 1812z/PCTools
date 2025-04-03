import os
import threading
import time
from PIL import Image
import flet as ft
from Update_State_Data import discovery, send_data
from flet_core import MainAxisAlignment, CrossAxisAlignment
from web_task import FlaskAppManager
from timer import start_task, stop_task
import json
from MQTT import start_mqtt, stop_mqtt_loop
from Command import discovery as discovery_comm,subcribe
import pystray
import startup
import HA_widget_task
from Hotkey_capture import load_hotkeys, capture_hotkeys, listen_hotkeys, stop_listen, send_discovery
from Toast import show_toast
from WIndows_Listener import start_window_listener
version = "V4.4"

manager = FlaskAppManager('0.0.0.0', 5000)
page = None


def save_json_data(key, data):
    json_data[key] = data
    with open('config.json', 'w', encoding='utf-8') as file:
        json.dump(json_data, file, indent=4)


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

fun7_flag = False
def start():
    if fun1:
        if discovery() !=1:
            start_task()
        else:
            show_toast("[ERROR]PCTools","MQTT发现失败")
    if fun2:
        discovery_comm()
        if start_mqtt() == 0:
            subcribe()
        else:
            show_toast("[ERROR]PCTools","MQTT订阅失败")
    if fun3:
        manager.start()
    if fun5:
        HA_widget_task.start_ha_widget()
    if fun6:
        listen_hotkeys()
    if fun7:
        global fun7_flag
        global window_listener
        if not fun7_flag:
            window_listener = start_window_listener()
            fun7_flag = True



def save_hotkeys_to_file():
    with open('hotkeys.txt', 'w') as file:
        for hotkey in hotkeys:
            file.write(hotkey + '\n')


def close_windows():
    try:
        page.window_destroy()
    except:
        return


def main(newpage: ft.Page):
    global page
    page = newpage

    page.window_width = 600
    page.window_height = 590
    page.title = "PCTools"
    page.window_resizable = True
    home = ft.Tab(text="主页")
    setting = ft.Tab(text="设置")
    tab_hotkey = ft.Tab(text="快捷键")
    
    def button_send_discovery(e):
        result = discovery() + discovery_comm() + send_discovery(hotkeys)
        print(result)
        dialog = ft.AlertDialog(
            title=ft.Text("信息"),
            content=ft.Text(value=result),
            scrollable=True
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    def button_send_data(e):
        try: 
            discovery()
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

    def button_stop(e):
        global run_flag
        if run_flag == True:
            show_snackbar(page, "停止进程中...")
            if fun1:
                stop_task()
                print("停止监控反馈")
            if fun2:
                stop_mqtt_loop()
                print("停止远程命令")
            if fun3:
                manager.stop()
                print("停止画面传输")
            if fun5:
                HA_widget_task.stop_ha_widget()
                print("停止小部件")
            if fun6:
                stop_listen()
                print("停止按键捕获")
            if fun7:
                print("停止前台应用反馈")
                window_listener.set()

            run_flag = False
            show_snackbar(page, "已经停止进程")
        else:
            show_snackbar(page, "都还没运行呀")

    def switch_fun1(e):
        global fun1
        fun1 = e.control.value
        save_json_data("fun1", fun1)

    def switch_fun2(e):
        global fun2
        fun2 = e.control.value
        save_json_data("fun2", fun2)

    def switch_fun3(e):
        global fun3
        fun3 = e.control.value
        save_json_data("fun3", fun3)


    def switch_fun5(e):
        global fun5
        fun5 = e.control.value
        save_json_data("fun5", fun5)

    def switch_fun6(e):
        global fun6
        fun6 = e.control.value
        save_json_data("fun6", fun6)

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
        save_json_data("fun4", fun4)
        page.update()

    def switch_fun7(e):
        global fun7
        fun7 = e.control.value
        save_json_data("fun7", fun7)

    def switch_hotkey_notify(e):
        global hotkey_notify
        hotkey_notify = e.control.value
        save_json_data("hotkey_notify", hotkey_notify)

    def switch_suppress(e):
        global suppress
        suppress = e.control.value
        save_json_data("suppress", suppress)


    def input_user(e):
        save_json_data("username", e.control.value)

    def input_pass(e):
        save_json_data("password", e.control.value)

    def input_interval(e):
        save_json_data("interval", int(e.control.value))

    def input_ha_broker(e):
        save_json_data("HA_MQTT", e.control.value)

    def input_port(e):
        save_json_data("HA_MQTT_port", int(e.control.value))

    def input_device_name(e):
        save_json_data("device_name", e.control.value)

    def input_url(e):
        save_json_data("url", e.control.value)

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
                    on_click=button_stop,
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
                        ft.Switch(label="监控反馈", label_position='left',
                                  scale=1.2, value=fun1, on_change=switch_fun1),
                        ft.Container(width=10),
                        ft.TextField(label="HA_MQTT_Broker", width=130,
                                     on_submit=input_ha_broker, value=read_ha_broker),
                        ft.TextField(label="PORT", width=60,
                                     on_submit=input_port, value=read_port)
                    ]
                ), ft.Row(
                    [
                        ft.Container(width=90),
                        ft.Switch(label="远程命令", label_position='left',
                                  scale=1.2, value=fun2, on_change=switch_fun2),
                        ft.Container(width=10),
                        ft.TextField(label="HA_MQTT账户", width=200,
                                     on_submit=input_user, value=read_user)
                    ]

                ), ft.Row(
                    [
                        ft.Container(width=90),
                        ft.Switch(label="画面传输", label_position='left',
                                  scale=1.2, value=fun3, on_change=switch_fun3),
                        ft.Container(width=10),
                        ft.TextField(label="HA_MQTT密码", width=200,
                                     on_submit=input_pass, value=read_password)
                    ]

                ), ft.Row(
                    [
                        ft.Container(width=90),
                        ft.Switch(label="网页部件", label_position='left', scale=1.2,
                                  value=fun5, on_change=switch_fun5),
                        ft.Container(width=10),
                        ft.TextField(label="侧边栏网址(https://)", width=200,
                                     on_submit=input_url, value=read_url),

                    ]
                ), ft.Row(
                    [
                        ft.Container(width=90),
                        ft.Switch(label="前台监听", label_position='left', scale=1.2,
                                  value=fun7, on_change=switch_fun7,tooltip="实时反馈前台应用名称"),
                        ft.Container(width=10),
                        ft.TextField(label="数据发送间隔", width=100,
                                     on_submit=input_interval, value=read_interval),
                        ft.TextField(label="设备标识符", width=90,
                                     on_submit=input_device_name, value=read_device_name),
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
                                  scale=1.2, value=fun6, on_change=switch_fun6,tooltip="开启后随服务启动"),
                        ft.Container(width=20),
                        ft.Switch(label="触发通知", label_position='left',
                                scale=1.2, value=hotkey_notify, on_change=switch_hotkey_notify),
                        ft.Container(width=20),
                        ft.Switch(label="阻断按键", label_position='left',
                                scale=1.2, value=suppress, on_change=switch_suppress,tooltip="阻止快捷键被其它软件响应"),
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
    tabbar = ft.Tabs()
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
        if fun1:
            stop_task()
            print("停止监控反馈")
        if fun2:
            stop_mqtt_loop()
            print("停止远程命令")
        if fun3:
            manager.stop()
            print("停止画面传输")
        if fun5:
            HA_widget_task.stop_ha_widget()
            print("停止小部件")
        if fun6:
            print("停止快捷键捕获")
        if fun7:
            print("停止前台应用反馈")
            window_listener.set()
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


def user_directory():
    save_json_data("user_directory", os.path.expanduser("~"))


show_menu_flag = False
icon_flag = True
if __name__ == "__main__":
    global run_flag
    global hotkeys
    run_flag = False
    threading.Thread(target=icon_task).start()
    hotkeys = load_hotkeys()
    with open('config.json', 'r') as file:
        json_data = json.load(file)
        fun1 = json_data.get("fun1")
        fun2 = json_data.get("fun2")
        fun3 = json_data.get("fun3")
        fun4 = json_data.get("fun4")
        fun5 = json_data.get("fun5")
        fun6 = json_data.get("fun6")
        fun7 = json_data.get("fun7")
        suppress = json_data.get("suppress")
        hotkey_notify = json_data.get("hotkey_notify")
        read_user = json_data.get("username")
        read_password = "密码已隐藏"
        read_interval = json_data.get("interval")
        read_ha_broker = json_data.get("HA_MQTT")
        read_port = json_data.get("HA_MQTT_port")
        read_device_name = json_data.get("device_name")
        read_url = json_data.get("url")
        user_directory()
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
