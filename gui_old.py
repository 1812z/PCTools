import flet as ft
from aida64 import discovery,send_data
from flet_core import MainAxisAlignment, CrossAxisAlignment
from web_task import FlaskAppManager 
from timer import start_task, stop_task

version = "V1.0"
manager = FlaskAppManager('192.168.44.236', 5000)

def load_data:
    

def main(page: ft.Page):
    page.window_width = 580
    page.window_height = 590
    page.title = "PCTools"
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
        #Web启动
        manager.start()
        start_task()
        snackbar = ft.SnackBar(
            content=ft.Text("启动进程..."),
            action="OK",
            action_color=ft.colors.WHITE,
            on_action=lambda e: snackbar.close(),
            duration=2000  
        )
        page.snack_bar = snackbar
        page.snack_bar.open = True
        page.update()   

    def button_stop(e):
        manager.stop()
        stop_task()
        snackbar = ft.SnackBar(
            content=ft.Text("停止进程..."),
            action="OK",
            action_color=ft.colors.WHITE,
            on_action=lambda e: snackbar.close(),
            duration=2000  
        )
        page.snack_bar = snackbar
        page.snack_bar.open = True
        page.update()      

    def switch_changed(e):
        print(f"开关状态: {e.control.value}")
    def go_setting(e):
        page.go("/setting")
    page.add(
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
                ft.ElevatedButton(
                    content=ft.Row(
                        [
                            ft.Icon(ft.icons.START_ROUNDED),
                            ft.Text("运行", weight=ft.FontWeight.W_600),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_AROUND,
                    ),
                    on_click=button_start,
                    width=120,
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
                ),
                ft.ElevatedButton(
                    content=ft.Row(
                        [
                            ft.Icon(ft.icons.SETTINGS_ROUNDED),
                            ft.Text("设置", weight=ft.FontWeight.W_600),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_AROUND,
                    ),
                    on_click=go_setting,
                    width=120,
                )
            ],
            alignment=MainAxisAlignment.CENTER,
            horizontal_alignment=CrossAxisAlignment.CENTER,      
        ),ft.Row(
            [
                ft.Container(width=210),
                ft.Switch(
                    label="仅监控", label_position='rifht', scale=1.1
                ),
            ]
           
        )

    )

    # Update the page
    page.update()

if __name__ == "__main__":
    load_data()
    ft.app(target=main)
