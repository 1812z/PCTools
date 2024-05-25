import flet as ft
from aida64 import discovery,send_data
from flet_core import MainAxisAlignment, CrossAxisAlignment
from web_task import FlaskAppManager 
from timer import start_task, stop_task
import json
from command import start_mqtt,stop_mqtt_loop

version = "V1.0"
manager = FlaskAppManager('192.168.44.236', 5000)
run_flag = False

def save_json_data(key,data):
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

def main(page: ft.Page):
    page.window_width = 550
    page.window_height = 590
    page.title = "PCTools"

    home = ft.Tab(text="主页")
    setting = ft.Tab(text="设置")
 

    def button_send_discovery(e):
        result = discovery()
        print(result)
        dialog = ft.AlertDialog(
            title = ft.Text("信息"),
            content = ft.Text(value=result),
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
            show_snackbar(page,"未勾选任何服务")  
        else:
            run_flag = True
            show_snackbar(page,"启动进程...")  

    def button_stop(e):
        global run_flag
        if run_flag == True:
            if fun1:
                stop_task()
            if fun2:
                stop_mqtt_loop()
            if fun3:
                manager.stop()
            run_flag = False
            show_snackbar(page,"停止进程...")  
        else:
           show_snackbar(page,"都还没运行呀")

    def switch_fun1(e):
        fun1 = e.control.value
        save_json_data("fun1",fun1)
    def switch_fun2(e):
        fun2 = e.control.value
        save_json_data("fun2",fun2)
    def switch_fun3(e):
        fun3 = e.control.value
        save_json_data("fun3",fun3)
    def switch_fun4(e):
        fun4 = e.control.value
        save_json_data("fun4",fun4)

        
        
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
        ),ft.Row(
            [
                ft.Container(width=210),
                ft.Switch(
                    label="监控反馈", label_position='rifht', scale=1.1,value=fun1,on_change=switch_fun1
                ),
            ]
           
        ),ft.Row(
            [
                ft.Container(width=210),
                ft.Switch(
                    label="MQTT命令", label_position='rifht', scale=1.1,value=fun2,on_change=switch_fun2
                ),
            ]
           
        ),ft.Row(
            [
                ft.Container(width=210),
                ft.Switch(
                    label="画面传输", label_position='rifht', scale=1.1,value=fun3,on_change=switch_fun3
                ),
            ]
           
        ),ft.Row(
            [
                ft.Container(width=210),
                ft.Switch(
                    label="自启动", label_position='rifht', scale=1.1,value=fun4,on_change=switch_fun4
                ),
                
                
            ]
           
        )
    ]
    home.content = ft.Column(controls=home_page)
    setting.content =ft.Column(controls=setting_page)
    tabbar = ft.Tabs()
    tabbar.tabs = [home, setting]
    page.add(tabbar)

    # Update the page
    page.update()

if __name__ == "__main__":
    with open('config.json', 'r') as file:
        json_data = json.load(file)
        fun1 = json_data.get("fun1")
        fun2 = json_data.get("fun2")
        fun3 = json_data.get("fun3")
        fun4 = json_data.get("fun4")
    if fun4:
        start()
    ft.app(target=main)
