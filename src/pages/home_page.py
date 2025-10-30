"""
主页模块
"""

import flet as ft


class HomePage:
    """主页类"""

    def __init__(self, gui):
        """初始化主页"""
        self.gui = gui
        self.logic = gui.logic
        self.page = gui.page

        # 状态组件
        self.running_dot = None
        self.running_text = None
        self.mqtt_dot = None
        self.mqtt_text = None

    def create(self) -> ft.Column:
        """创建主页"""
        logo = ft.Container(
            content=ft.Image(
                src="img/home-assistant-wordmark-with-margins-color-on-light.png",
                fit=ft.ImageFit.CONTAIN,
                width=500
            )
        )

        version_text = ft.Container(
            content=ft.Text(
                f"{self.logic.get_version()} by 1812z",
                size=20,
            )
        )

        github_link = ft.Container(
            content=ft.TextButton(
                "Github",
                animate_size=20,
                on_click=lambda e: self.gui.page.launch_url('https://github.com/1812z/PCTools')
            ),
            width=120
        )

        # 添加状态显示组件
        status_panel = self._create_status_panel()

        # 按钮
        buttons = [
            self._create_action_button(
                ft.Icons.PLAY_ARROW, "开始",
                lambda e: self.logic.start_service()
            ),
            self._create_action_button(
                ft.Icons.STOP_ROUNDED, "停止",
                lambda e: self.logic.stop_service()
            ),
            self._create_action_button(
                ft.Icons.SEND_AND_ARCHIVE, "发送数据",
                lambda e: self.logic.send_data()
            ),
            self._create_action_button(
                ft.Icons.THUMB_UP_ALT_ROUNDED, "关注我",
                lambda e: self.gui.page.launch_url('https://space.bilibili.com/336130050')
            ),
        ]

        return ft.Column(
            [logo, version_text, github_link] + buttons + [status_panel],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def update_status(self):
        # 更新运行状态点
        if self.gui.is_starting:
            self.running_dot.color = ft.Colors.ORANGE
            self.running_text.value = "启动中..."
        elif self.gui.is_stopping:
            self.running_dot.color = ft.Colors.YELLOW
            self.running_text.value = "停止中..."
        elif self.gui.is_running:
            self.running_dot.color = ft.Colors.GREEN
            self.running_text.value = "运行中"
        else:
            self.running_dot.color = ft.Colors.GREY
            self.running_text.value = "未运行"


        # 更新MQTT状态点
        if hasattr(self.gui.core, 'mqtt') and self.gui.core.mqtt and hasattr(self.gui.core.mqtt, 'mqttc'):
            if self.gui.core.mqtt.mqttc.is_connected():
                self.mqtt_dot.color = ft.Colors.GREEN
                self.mqtt_text.value = "MQTT: 已连接"
            elif self.gui.is_running:
                self.mqtt_dot.color = ft.Colors.RED
                self.mqtt_text.value = "MQTT: 连接失败"
            else:
                self.mqtt_dot.color = ft.Colors.GREY
                self.mqtt_text.value = "MQTT: 未连接"
            self.mqtt_text.tooltip = f"MQTT: {self.gui.core.mqtt.status}"
        else:
            self.mqtt_dot.color = ft.Colors.GREY
            self.mqtt_text.value = "MQTT: 未初始化"

        self.gui.page.update()


    def _create_status_panel(self) -> ft.Container:
        """创建状态显示面板(两行布局，带状态点)"""
        # 运行状态点
        self.running_dot = ft.Icon(
            name=ft.Icons.CIRCLE,
            size=10,
            color=ft.Colors.GREY
        )

        # 运行状态文本
        self.running_text = ft.Text(
            "未运行",
            size=12,
        )

        # MQTT状态点
        self.mqtt_dot = ft.Icon(
            name=ft.Icons.CIRCLE,
            size=10,
            color=ft.Colors.GREY
        )

        # MQTT状态文本
        self.mqtt_text = ft.Text(
            "MQTT: 未连接",
            size=12,
            tooltip="",
            selection_cursor_color=ft.Colors.GREY
        )

        # 设置定时更新
        self.gui.page.on_resize = lambda e: self.update_status()
        self.gui.page.on_scroll = lambda e: self.update_status()

        # 初始更新
        self.update_status()

        return ft.Container(
            content=ft.Row(
                [ft.Column(
                    [
                        # 第一行：运行状态
                        ft.Row(
                            [
                                self.running_dot,
                                ft.Container(width=5),
                                self.running_text
                            ],
                            spacing=0
                        ),

                        # 第二行：MQTT状态
                        ft.Row(
                            [
                                self.mqtt_dot,
                                ft.Container(width=5),
                                self.mqtt_text
                            ],
                            spacing=0
                        )
                    ],
                    spacing=5,
                    horizontal_alignment=ft.CrossAxisAlignment.START
                )],
                alignment=ft.MainAxisAlignment.END,
                spacing=10
            ),
            padding=ft.padding.only(top=10, bottom=10),
            alignment=ft.alignment.bottom_right,
            width=500
        )

    def _create_action_button(self, icon: str, text: str, on_click) -> ft.ElevatedButton:
        """创建操作按钮"""
        return ft.ElevatedButton(
            content=ft.Row(
                [ft.Icon(icon), ft.Text(text, weight=ft.FontWeight.W_600)],
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
            ),
            on_click=on_click,
            width=130,
            height=40
        )