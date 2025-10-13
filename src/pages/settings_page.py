"""
设置页模块
"""

import flet as ft


class SettingsPage:
    """设置页类"""

    def __init__(self, gui):
        """初始化设置页"""
        self.gui = gui
        self.logic = gui.logic
        self.page = gui.page

    def create(self) -> ft.ListView:
        """创建设置页"""
        logo = ft.Container(
            content=ft.Image(
                src="img/home-assistant-wordmark-with-margins-color-on-light.png",
                fit=ft.ImageFit.CONTAIN,
                width=500
            )
        )

        settings = [
            logo,
            self._create_setting_item(
                ft.Icons.NETWORK_CELL,
                "MQTT设置",
                "配置MQTT连接信息",
                on_click=self._open_mqtt_setting,
                control_type="button"
            ),
            self._create_setting_item(
                ft.Icons.UPDATE,
                "检查更新",
                "启动时自动检查新版本并提示",
                toggle_value=self.logic.get_config("check_update", False),
                on_change=lambda e: self.logic.set_config("check_update", e.control.value)
            ),
            self._create_setting_item(
                ft.Icons.BROWSER_UPDATED,
                "自动更新",
                "检查到新版本时自动更新",
                toggle_value=self.logic.get_config("auto_update", False),
                on_change=lambda e: self.logic.set_config("auto_update", e.control.value)
            ),
            self._create_setting_item(
                ft.Icons.POWER_SETTINGS_NEW,
                "自启动",
                "开机后自动打开程序",
                toggle_value=self.logic.get_config("auto_start", False),
                on_change=self._on_auto_start_changed
            ),
        ]

        return ft.ListView(
            controls=settings,
            spacing=15,
            padding=ft.padding.only(left=60, right=60),
            expand=True
        )

    def _create_setting_item(
        self,
        icon: str,
        title: str,
        subtitle: str,
        toggle_value: bool = False,
        on_change=None,
        on_click=None,
        control_type: str = "switch"
    ) -> ft.Column:
        """创建设置项"""
        if control_type == "switch":
            right_control = ft.Switch(value=toggle_value, on_change=on_change)
        else:
            right_control = ft.IconButton(
                icon=ft.Icons.ARROW_FORWARD_IOS,
                icon_size=20,
                on_click=on_click
            )

        return ft.Column(
            controls=[
                ft.Divider(height=10),
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(icon, size=25),
                                    ft.Column(
                                        controls=[
                                            ft.Text(title, weight=ft.FontWeight.BOLD),
                                            ft.Text(subtitle, size=12, color=ft.Colors.GREY_600),
                                        ],
                                        spacing=2
                                    )
                                ],
                                spacing=10,
                                expand=True
                            ),
                            right_control
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    padding=ft.padding.symmetric(vertical=5, horizontal=10),
                    on_click=on_click if on_click else None
                )
            ]
        )

    def _on_auto_start_changed(self, e):
        """自启动开关变更"""
        result = self.logic.set_auto_start(e.control.value)
        self.gui.show_snackbar(result)
        self.gui.page.update()

    def _open_mqtt_setting(self, e):
        """打开MQTT设置对话框"""
        mqtt_dialog = self._create_mqtt_dialog()
        self.gui.page.open(mqtt_dialog)
        self.gui.page.update()

    def _create_mqtt_dialog(self) -> ft.AlertDialog:
        """创建MQTT设置对话框"""
        def create_text_field(label: str, config_key: str, value_type: str = "string"):
            return ft.TextField(
                label=label,
                value=str(self.logic.get_config(config_key, "")),
                on_submit=lambda e: self.logic.handle_config_change(
                    config_key, e.control.value, value_type
                )
            )

        return ft.AlertDialog(
            title=ft.Text("MQTT设置（每项输入框按回车保存）"),
            content=ft.Container(
                content=ft.Column([
                    create_text_field("HA_MQTT_Broker", "HA_MQTT"),
                    create_text_field("PORT", "HA_MQTT_port", "int"),
                    create_text_field("HA_MQTT账户", "username"),
                    create_text_field("HA_MQTT密码", "password"),
                    create_text_field("发现前缀", "ha_prefix"),
                    create_text_field("设备唯一标识符(仅支持英文字符)", "device_name"),
                ]),
                height=300,
                width=400,
                margin=10,
            ),
            actions=[
                ft.TextButton("返回", on_click=lambda e: self.gui.page.close(e.control.parent))
            ],
        )