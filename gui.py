import os
import threading
import time
from PIL import Image
import flet as ft
from MQTT_publish import discovery, send_data
from flet_core import MainAxisAlignment, CrossAxisAlignment
from web_task import FlaskAppManager
from timer import start_task, stop_task
import json
from command import start_mqtt, stop_mqtt_loop
from command import discovery as discovery_comm
import pystray
import startup


version = "V3.3"
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


def start():
    if fun1:
        discovery()
        start_task()
    if fun2:
        start_mqtt()
    if fun3:
        manager.start()


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

    def button_send_discovery(e):
        result = discovery() + discovery_comm()
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
            on_action=None,
            duration=2000
        )
        page.snack_bar = snackbar
        page.snack_bar.open = True
        page.update()

    def button_start(e):
        global run_flag
        start()
        if run_flag:
            show_snackbar(page, "请勿多次启动!")
        elif fun1 == False and fun2 == False and fun3 == False:
            show_snackbar(page, "未勾选任何服务")
        else:
            run_flag = True
            show_snackbar(page, "启动进程...")

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
        if(fun4 == True):
            startup.add_to_startup()
            show_snackbar(page, "程序将在开机时后台运行")
        else:
            startup.remove_from_startup()
            show_snackbar(page, "已移除自启动")
        save_json_data("fun4", fun4)

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

    def open_repo(e):
        page.launch_url('https://github.com/1812z/PCTools')

    def follow(e):
        page.launch_url('https://space.bilibili.com/336130050')

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
                ft.ElevatedButton(
                    content=ft.Row(
                        [
                            ft.Icon(ft.icons.THUMB_UP_ALT_ROUNDED),
                            ft.Text("关注我", weight=ft.FontWeight.W_600),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_AROUND,
                    ),
                    on_click=follow,
                    width=120,
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
                        ft.Switch(label="开机自启", label_position='left', scale=1.2,
                                  value=fun4, on_change=switch_fun4, tooltip="添加gui.py为启动项"),
                        ft.Container(width=10),
                        ft.TextField(label="数据发送间隔", width=100,
                                     on_submit=input_interval, value=read_interval),
                        ft.TextField(label="设备标识符", width=90,
                                     on_submit=input_device_name, value=read_device_name)
                    ]
                )
            ], alignment=MainAxisAlignment.CENTER,
            horizontal_alignment=CrossAxisAlignment.CENTER,
        )
    ]
    home.content = ft.Column(controls=home_page)
    setting.content = ft.Column(controls=setting_page)
    tabbar = ft.Tabs()
    tabbar.tabs = [home, setting]
    page.add(tabbar)

    page.update()


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
    save_json_data("user_directory",os.path.expanduser("~")) 


show_menu_flag = False
icon_flag = True
if __name__ == "__main__":
    global run_flag
    run_flag = False
    threading.Thread(target=icon_task).start()
    with open('config.json', 'r') as file:
        json_data = json.load(file)
        fun1 = json_data.get("fun1")
        fun2 = json_data.get("fun2")
        fun3 = json_data.get("fun3")
        fun4 = json_data.get("fun4")
        read_user = json_data.get("username")
        read_password = "密码已隐藏"
        read_interval = json_data.get("interval")
        read_ha_broker = json_data.get("HA_MQTT")
        read_port = json_data.get("HA_MQTT_port")
        read_device_name = json_data.get("device_name")
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
