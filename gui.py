import threading
import time
from PIL import Image
import flet as ft
from aida64 import discovery, send_data
from flet_core import MainAxisAlignment, CrossAxisAlignment
from web_task import FlaskAppManager
from timer import start_task, stop_task
import json
from command import start_mqtt, stop_mqtt_loop
import pystray

version = "V2.0"
manager = FlaskAppManager('192.168.44.236', 5000)
run_flag = False
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


def start():
    if fun1:
        start_task()
    if fun2:
        start_mqtt()
    if fun3:
        manager.start()


def close_windows():
    if page:
        page.window_destroy()


def main(newpage: ft.Page):
    global page
    page = newpage

    page.window_width = 550
    page.window_height = 590
    page.title = "PCTools"

    home = ft.Tab(text="主页")
    setting = ft.Tab(text="设置")

    def button_send_discovery(e):
        result = discovery()
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
        result = send_data()
        print(result)
        snackbar = ft.SnackBar(
            content=ft.Text(result),
            action="OK",
            action_color=ft.colors.WHITE,
            on_action=lambda e: snackbar.close(),
            duration=2000
        )
        page.snack_bar = snackbar
        page.snack_bar.open = True
        page.update()

    def button_start(e):
        start()
        global run_flag
        if fun1 == False and fun2 == False and fun3 == False:
            show_snackbar(page, "未勾选任何服务")
        else:
            run_flag = True
            show_snackbar(page, "启动进程...")

    def button_stop(e):
        global run_flag
        if run_flag == True:
            show_snackbar(page, "停止进程中,请耐心等待..")
            if fun1:
                stop_task()
                print("停止监控反馈")
            if fun2:
                stop_mqtt_loop()
                print("停止远程命令")
            if fun3:
                manager.stop()
                print("停止画面传输")
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

    def switch_fun4(e):
        global fun4
        fun4 = e.control.value
        save_json_data("fun4", fun4)

    def input_user(e):
        save_json_data("username", e.control.value)

    def input_pass(e):
        save_json_data("password", e.control.value)

    def input_id(e):
        save_json_data("secret_id", e.control.value)

    def input_interval(e):
        save_json_data("interval", int(e.control.value))

    def open_repo(e):
        page.launch_url('https://github.com/1812z/PCTools')

    home_page = [ft.Column(
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
            ), ft.Row(
                [
                    ft.Container(width=210),
                    ft.TextButton("Github", on_click=open_repo)
                ]
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
                width=120,
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
                width=120,
                height=40
            ),
            ft.ElevatedButton(
                content=ft.Row(
                    [
                        ft.Icon(ft.icons.FIND_IN_PAGE),
                        ft.Text("发现设备", weight=ft.FontWeight.W_600),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                ),
                on_click=button_send_discovery,
                width=120,
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
                width=120,
                height=40
            ),
        ],
        alignment=MainAxisAlignment.CENTER,
        horizontal_alignment=CrossAxisAlignment.CENTER,

    )
    ]
    setting_page = [ft.Column(
        [

            ft.Container(
                    content=ft.Image(
                        src="img\\home-assistant-wordmark-with-margins-color-on-light.png",
                        fit=ft.ImageFit.CONTAIN,
                        width=500
                    ),
                    ),
        ],
        alignment=MainAxisAlignment.CENTER,
        horizontal_alignment=CrossAxisAlignment.CENTER,
    ), ft.Row(
        [
            ft.Container(width=90)
        ]
    ), ft.Row(
        [
            ft.Container(width=90),
            ft.Switch(label="监控反馈", label_position='left',
                      scale=1.2, value=fun1, on_change=switch_fun1),
            ft.Container(width=10),
            ft.TextField(label="HA_MQTT账户", width=200,
                         on_submit=input_user, value=read_user)
        ]
    ), ft.Row(
        [
            ft.Container(width=90),
            ft.Switch(label="远程命令", label_position='left',
                      scale=1.2, value=fun2, on_change=switch_fun2),
            ft.Container(width=10),
            ft.TextField(label="HA_MQTT密码", width=200,
                         on_submit=input_pass, value=read_password)
        ]

    ), ft.Row(
        [
            ft.Container(width=90),
            ft.Switch(label="画面传输", label_position='left',
                      scale=1.2, value=fun3, on_change=switch_fun3),
            ft.Container(width=10),
            ft.TextField(label="Secret_id", width=200,
                         on_submit=input_id, value=read_secret_id)
        ]

    ), ft.Row(
        [
            ft.Container(width=90),
            ft.Switch(label="自动运行", label_position='left', scale=1.2,
                      value=fun4, on_change=switch_fun4, tooltip="运行gui.py时自动运行勾选的服务"),
            ft.Container(width=10),
            ft.TextField(label="监控刷新间隔", width=200,
                         on_submit=input_interval, value=read_interval)
        ]

    )
    ]
    home.content = ft.Column(controls=home_page)
    setting.content = ft.Column(controls=setting_page)
    tabbar = ft.Tabs()
    tabbar.tabs = [home, setting]
    page.add(tabbar)

    # Update the page
    page.update()


def on_exit(icon, item):
    global icon_flag
    if (run_flag == False):
        icon_flag = False
        close_windows()
        icon.stop()
    else:
        icon.notify("服务正在运行无法关闭托盘")


def show_menu(icon, item):
    global show_menu_flag
    show_menu_flag = 1

# Run the icon in a separate thread to avoid blocking


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

    threading.Thread(target=icon_task).start()
    with open('config.json', 'r') as file:
        json_data = json.load(file)
        fun1 = json_data.get("fun1")
        fun2 = json_data.get("fun2")
        fun3 = json_data.get("fun3")
        fun4 = json_data.get("fun4")
        read_user = json_data.get("username")
        read_password = "密码已隐藏"
        read_secret_id = json_data.get("secret_id")
        read_interval = json_data.get("interval")
    if fun4:
        run_flag = True
        start()
    else:
        ft.app(target=main)
    while (icon_flag):
        time.sleep(1)
        if show_menu_flag:
            show_menu_flag = False
            ft.app(target=main)