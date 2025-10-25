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

        # 存储所有输入框的引用
        text_fields = {}

        def create_text_field(label: str, config_key: str, value_type: str = "string", input_filter=None, icon=None,
                              password=False):

            text_field = ft.TextField(
                label=label,
                value=str(self.logic.get_config(config_key, "")),
                input_filter=input_filter,
                prefix_icon=icon,
                password=password,  # 是否隐藏密码
                can_reveal_password=password,  # 如果是密码字段，显示切换按钮
            )

            # 保存到字典中，用于后续保存
            text_fields[config_key] = {
                'field': text_field,
                'value_type': value_type
            }

            return text_field

        # 为 ha_prefix 和 device_name 创建字母数字过滤器
        alphanumeric_filter = ft.InputFilter(
            allow=True,  # 允许匹配模式
            regex_string=r"[a-zA-Z0-9]",  # 仅允许大小写字母和数字
            replacement_string="",
        )

        # 保存所有配置的函数
        def save_all_configs(e):
            # 遍历所有输入框并保存
            for config_key, field_data in text_fields.items():
                value = field_data['field'].value
                value_type = field_data['value_type']
                self.logic.handle_config_change(config_key, value, value_type)

            # 关闭对话框
            self.gui.page.close(e.control.parent)

            # 显示保存成功提示
            self.gui.show_snackbar("MQTT设置已保存")

        return ft.AlertDialog(
            title=ft.Text("MQTT设置"),
            content=ft.Container(
                content=ft.Column([
                    create_text_field(
                        "MQTT服务器地址",
                        "HA_MQTT",
                        icon=ft.Icons.CLOUD_OUTLINED
                    ),
                    create_text_field(
                        "端口",
                        "HA_MQTT_port",
                        "int",
                        ft.NumbersOnlyInputFilter(),
                        icon=ft.Icons.SETTINGS_ETHERNET
                    ),
                    create_text_field(
                        "MQTT账户",
                        "username",
                        icon=ft.Icons.PERSON_OUTLINE
                    ),
                    create_text_field(
                        "MQTT密码",
                        "password",
                        icon=ft.Icons.LOCK_OUTLINE,
                        password=True  # 隐藏密码
                    ),
                    create_text_field(
                        "发现前缀",
                        "ha_prefix",
                        input_filter=alphanumeric_filter,
                        icon=ft.Icons.TAG
                    ),
                    create_text_field(
                        "设备唯一标识符",
                        "device_name",
                        input_filter=alphanumeric_filter,
                        icon=ft.Icons.DEVICES
                    ),
                ]),
                height=400,
                width=400,
                margin=10,
            ),
            actions=[
                ft.ElevatedButton(
                    "返回",
                    on_click=lambda e: self.gui.page.close(e.control.parent),
                    icon=ft.Icons.ARROW_BACK,
                    bgcolor=ft.Colors.GREY_700,
                    color=ft.Colors.WHITE
                ),
                ft.ElevatedButton(
                    "保存",
                    on_click=save_all_configs,
                    icon=ft.Icons.SAVE,
                    bgcolor=ft.Colors.BLUE,
                    color=ft.Colors.WHITE
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )