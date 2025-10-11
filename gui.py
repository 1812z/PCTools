"""
GUI 视图层
负责UI组件的创建和显示，不包含业务逻辑
"""

import time
from typing import Dict

import flet as ft
from gui_logic import GUILogic
from TrayManager import TrayManager
from Updater import UpdateChecker


class GUI:
    """GUI视图类"""

    def __init__(self, core_instance):
        """初始化GUI"""
        # 逻辑层
        self.logic = GUILogic(core_instance)
        self.core = core_instance

        # UI组件
        self.page: ft.Page = None
        self.plugins_view: ft.ListView = None

        # 外部组件
        self.tray: TrayManager = None
        self.updater: UpdateChecker = None

        # 标志
        self.show_menu_flag = False

        # 设置UI回调
        self.logic.set_ui_callbacks(
            show_snackbar=self.show_snackbar,
            update_ui=self._update_page
        )

    def _update_page(self):
        """更新页面"""
        if self.page:
            self.page.update()

    def show_snackbar(self, message: str, duration: int = 2000):
        """显示通知条消息"""
        if not self.page:
            return

        try:
            snackbar = ft.SnackBar(
                content=ft.Text(message),
                action="OK",
                duration=duration
            )
            self.page.open(snackbar)
            self.page.update()
        except Exception as e:
            self.logic.log_debug(f"无法显示Snackbar: {e}")

    def close_windows(self):
        """关闭窗口"""
        try:
            if self.page:
                self.page.window.close()
        except Exception as e:
            self.logic.log_error(f"关闭窗口失败: {e}")

    # ===== 属性代理（为了兼容旧代码） =====

    @property
    def is_running(self):
        return self.logic.is_running

    @property
    def is_starting(self):
        return self.logic.is_starting

    @property
    def is_stopping(self):
        return self.logic.is_stopping

    # ===== 主界面 =====

    def main(self, new_page: ft.Page):
        """主界面入口"""
        self.page = new_page
        self._setup_window()

        # 创建标签页
        tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(text="主页", content=self._create_home_page()),
                ft.Tab(text="设置", content=self._create_setting_page()),
                ft.Tab(text="插件", content=self._create_plugin_page()),
                ft.Tab(text="关于", content=self._create_about_page()),
            ],
            on_change=self._on_tab_changed
        )

        self.page.add(tabs)

    def _setup_window(self):
        """设置窗口属性"""
        self.page.window.width = 550
        self.page.window.height = 590
        self.page.window.resizable = False
        self.page.window.maximizable = False
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.title = "PCTools"

    def _on_tab_changed(self, e):
        """标签页切换事件"""
        if e.control.selected_index == 1:  # 设置页
            self.show_snackbar("修改设置后建议重启软件")
        elif e.control.selected_index == 2:  # 插件页
            if self.logic.is_running:
                self.show_snackbar("运行时无法配置")
            self._update_plugin_page()

    # ===== 主页 =====

    def _create_home_page(self) -> ft.Column:
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
                on_click=lambda e: self.page.launch_url('https://github.com/1812z/PCTools')
            ),
            width=120
        )

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
                lambda e: self.page.launch_url('https://space.bilibili.com/336130050')
            ),
        ]

        return ft.Column(
            [logo, version_text, github_link] + buttons,
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
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

    # ===== 设置页 =====

    def _create_setting_page(self) -> ft.ListView:
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
        self.show_snackbar(result)
        self.page.update()

    def _open_mqtt_setting(self, e):
        """打开MQTT设置对话框"""
        mqtt_dialog = self._create_mqtt_dialog()
        self.page.open(mqtt_dialog)
        self.page.update()

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
                ft.TextButton("返回", on_click=lambda e: self.page.close(e.control.parent))
            ],
        )

    # ===== 插件页 =====

    def _create_plugin_page(self) -> ft.Column:
        """创建插件页"""
        self.plugins_view = ft.ListView(
            height=450,
            width=450,
            spacing=5
        )

        return ft.Column(
            [
                ft.Container(height=10),
                ft.Row([
                    ft.Container(width=20),
                    self.plugins_view,
                ])
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _update_plugin_page(self):
        """更新插件列表"""
        if not self.plugins_view:
            return

        self.plugins_view.controls.clear()

        # 获取所有插件
        all_plugins = self.logic.get_all_plugins()

        if not all_plugins:
            self.plugins_view.controls.append(
                ft.Row([
                    ft.Container(width=180),
                    ft.Text("TAT..啥都木有", size=15)
                ])
            )
            self.page.update()
            return

        # 按名称排序
        sorted_plugins = self.logic.get_sorted_plugins()

        # 创建插件卡片
        for plugin_name, plugin_info in sorted_plugins:
            card = self._create_plugin_card(plugin_name, plugin_info)
            self.plugins_view.controls.append(card)

        self.page.update()

    def _create_plugin_card(self, plugin_name: str, plugin_info: Dict) -> ft.Container:
        """创建插件卡片"""
        # 获取状态
        enabled = plugin_info["enabled"]
        loaded = plugin_info["loaded"]
        has_error = plugin_info["error"] is not None

        # 状态信息
        status_icon, status_color_name, status_text = self.logic.get_plugin_status_info(plugin_info)
        status_color = getattr(ft.Colors, status_color_name.upper())

        # 插件名称
        name_text = ft.Text(
            f"{status_icon} {plugin_info['display_name']}",
            size=16,
            weight=ft.FontWeight.BOLD,
            color=status_color,
            width=200
        )

        # 版本信息
        meta_text = ft.Text(
            f"v{plugin_info['version']} by {plugin_info['author']}",
            size=11,
            color=ft.Colors.GREY_600,
            width=200
        )

        # 按钮组
        buttons = self._create_plugin_buttons(plugin_name, plugin_info)

        # 组装
        left_col = ft.Column([name_text, meta_text], spacing=2, tight=True)
        right_row = ft.Row(buttons, spacing=5, tight=True)

        main_row = ft.Row(
            controls=[left_col, right_row],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10
        )

        return ft.Container(
            content=main_row,
            padding=12,
            border=ft.border.all(2, status_color),
            border_radius=8,
            margin=ft.margin.only(bottom=5),
            bgcolor=ft.Colors.WHITE if enabled else ft.Colors.GREY_100
        )

    def _create_plugin_buttons(self, plugin_name: str, plugin_info: Dict) -> list:
        """创建插件按钮组"""
        enabled = plugin_info["enabled"]
        loaded = plugin_info["loaded"]
        available = self.logic.is_plugin_available(plugin_info)

        # 设置按钮
        has_settings = self.logic.has_plugin_settings(plugin_name)
        settings_btn = ft.IconButton(
            icon=ft.Icons.SETTINGS,
            icon_size=20,
            tooltip="插件设置",
            disabled=not (available and has_settings),
            on_click=lambda e, name=plugin_name: self._open_plugin_settings(e, name),
            icon_color=ft.Colors.BLUE if (available and has_settings) else ft.Colors.GREY
        )

        # 信息按钮
        info_btn = ft.IconButton(
            icon=ft.Icons.INFO_OUTLINE,
            icon_size=20,
            tooltip="查看详情",
            on_click=lambda e, name=plugin_name, info=plugin_info:
                self._show_plugin_info(e, name, info)
        )

        # 重载按钮
        reload_btn = ft.IconButton(
            icon=ft.Icons.REFRESH,
            icon_size=20,
            tooltip="重载插件",
            disabled=not (loaded and self.logic.can_modify_plugins()),
            on_click=lambda e, name=plugin_name: self._reload_plugin(e, name),
            icon_color=ft.Colors.GREEN if (loaded and self.logic.can_modify_plugins()) else ft.Colors.GREY
        )

        # 启用/禁用开关
        switch = ft.Switch(
            value=enabled,
            tooltip="启用/禁用插件",
            on_change=lambda e, name=plugin_name: self._toggle_plugin(e, name),
            disabled=self.logic.is_running
        )

        return [settings_btn, info_btn, reload_btn, switch]

    def _open_plugin_settings(self, e, plugin_name: str):
        """打开插件设置"""
        handler = self.logic.get_plugin_settings_handler(plugin_name)

        if not handler:
            self.show_snackbar("该插件没有设置页面")
            return

        try:
            content = handler(e)
            dialog = ft.AlertDialog(
                title=ft.Text("插件设置"),
                content=ft.Container(
                    content=content,
                    height=300,
                    width=400,
                    margin=5,
                ),
                actions=[
                    ft.TextButton("返回", on_click=lambda e: self.page.close(e.control.parent))
                ],
            )
            self.page.open(dialog)
            self.page.update()
        except Exception as ex:
            self.logic.log_error(f"打开设置页面失败: {ex}")
            self.show_snackbar(f"打开设置失败: {ex}")

    def _show_plugin_info(self, e, plugin_name: str, plugin_info: Dict):
        """显示插件详细信息"""
        _, _, status_text = self.logic.get_plugin_status_info(plugin_info)

        # 创建信息内容
        info_controls = [
            # 标题区域
            ft.Text("插件信息", size=18, weight=ft.FontWeight.BOLD),

            # 分隔线
            ft.Divider(height=1, color=ft.Colors.BLUE_200),

            # 状态指示器
            ft.Container(
                content=ft.Row([
                    ft.Icon(
                        ft.Icons.CHECK_CIRCLE if plugin_info['loaded'] else ft.Icons.ERROR,
                        size=18,
                        color=ft.Colors.GREEN if plugin_info['loaded'] else ft.Colors.RED
                    ),
                    ft.Text(
                        status_text,
                        size=14,
                        weight=ft.FontWeight.W_500,
                        color=ft.Colors.GREEN_800 if plugin_info['loaded'] else ft.Colors.RED_800
                    ),
                ], spacing=8),
                bgcolor=ft.Colors.GREEN_50 if plugin_info['loaded'] else ft.Colors.RED_50,
                padding=10,
                border_radius=8,
                margin=ft.margin.only(bottom=5)
            ),

            # 基本信息卡片
            ft.Container(
                content=ft.Column([
                    # 版本和作者 - 水平布局
                    ft.Row([
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.TAG, size=16, color=ft.Colors.BLUE_700),
                                ft.Text(f"v{plugin_info['version']}", size=14, weight=ft.FontWeight.W_500)
                            ], spacing=5),
                            padding=5
                        ),
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.PERSON, size=16, color=ft.Colors.BLUE_700),
                                ft.Text(plugin_info['author'], size=14, weight=ft.FontWeight.W_500)
                            ], spacing=5),
                            padding=5
                        ),
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.FOLDER, size=16, color=ft.Colors.BLUE_700),
                                ft.Text(
                                    self.logic.get_plugin_path(plugin_name),
                                    size=14,
                                    color=ft.Colors.GREY_700,
                                    italic=True
                                ),
                            ], spacing=5),
                            padding=5
                        ),
                    ], spacing=15),

                    # 描述
                    ft.Container(
                        content=ft.Text(
                            plugin_info['description'],
                            size=13,
                            color=ft.Colors.GREY_800,
                            weight=ft.FontWeight.W_400
                        ),
                        padding=ft.padding.only(top=5, bottom=5)
                    ),
                ]),
                bgcolor=ft.Colors.BLUE_50,
                padding=14,
                border_radius=8,
                margin=ft.margin.only(top=5, bottom=5)
            ),
        ]

        # 显示依赖
        if plugin_info['dependencies']:
            info_controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.ACCOUNT_TREE, size=16, color=ft.Colors.INDIGO_700),
                            ft.Text("依赖插件", size=13, weight=ft.FontWeight.W_500, color=ft.Colors.INDIGO_900)
                        ], spacing=5),
                        ft.Container(
                            content=ft.Text(
                                ', '.join(plugin_info['dependencies']),
                                size=12,
                                color=ft.Colors.INDIGO_800
                            ),
                            padding=ft.padding.only(left=21, top=5)
                        )
                    ], spacing=5),
                    bgcolor=ft.Colors.BLUE_50,
                    padding=12,
                    border_radius=8,
                    margin=ft.margin.only(top=8, bottom=8),
                )
            )

        dialog = ft.AlertDialog(
            title=ft.Text(f"{plugin_info['display_name']} 详细信息"),
            content=ft.Container(
                content=ft.Column(info_controls, spacing=8, tight=True),
                width=400,
                height=300
            ),
            scrollable=True,
            actions=[
                ft.TextButton("关闭", on_click=lambda e: self.page.close(e.control.parent))
            ]
        )

        self.page.open(dialog)
        self.page.update()

    def _toggle_plugin(self, e, plugin_name: str):
        """切换插件启用状态"""
        new_status = e.control.value
        success = self.logic.toggle_plugin(plugin_name, new_status)

        if success and not new_status:
            # 禁用成功，刷新页面
            self._update_plugin_page()
        elif not success:
            # 操作失败，恢复开关状态
            e.control.value = not new_status
            self.page.update()

    def _reload_plugin(self, e, plugin_name: str):
        """重载插件"""
        if self.logic.reload_plugin(plugin_name):
            self._update_plugin_page()

    # ===== 关于页 =====

    def _create_about_page(self) -> ft.Column:
        """创建关于页"""
        update_component = self.updater.create_update_ui(self.page) if self.updater else ft.Container()

        return ft.Column(
            [
                update_component,
                ft.Container(
                    content=ft.Text(
                        "感谢使用，求投喂，有需要的功能也可以联系我(VX: 1812z)，会尽快写(AI)好",
                        size=15
                    )
                ),
                ft.Container(
                    content=ft.Image(
                        src="img/wechat.png",
                        fit=ft.ImageFit.CONTAIN,
                        width=300
                    )
                ),
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    # ===== 退出 =====

    def exit(self):
        """退出程序"""
        try:
            if self.logic.is_running:
                self.logic.stop_service()
            self.close_windows()
            if self.tray:
                self.tray.stop()
        except Exception as e:
            self.logic.log_error(f"退出异常: {e}")


# ===== 程序入口 =====

if __name__ == "__main__":
    from Core import Core

    # 初始化核心
    core = Core(None)

    # 初始化GUI
    gui = GUI(core)
    core.gui = gui

    # 初始化托盘和更新器
    gui.tray = TrayManager(gui)
    gui.updater = UpdateChecker(gui, "1812z", "PCTools", "config_example.json")
    gui.tray.start()

    # 启动方式
    if not gui.logic.get_config("auto_start", False):
        # 直接显示GUI
        ft.app(target=gui.main)
    else:
        # 后台启动
        gui.logic.start_service()
        if gui.logic.get_config("check_update", False):
            gui.updater.check_for_updates()

    # 主循环
    while gui.tray.is_running:
        try:
            if gui.show_menu_flag:
                ft.app(target=gui.main)
                gui.show_menu_flag = False
            time.sleep(1)
        except KeyboardInterrupt:
            gui.exit()