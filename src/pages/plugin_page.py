"""
插件页模块
"""

from typing import Dict
import flet as ft


class PluginPage:
    """插件页类"""

    def __init__(self, gui):
        """初始化插件页"""
        self.gui = gui
        self.logic = gui.logic
        self.page = gui.page
        self.plugins_view = None

    def create(self) -> ft.Column:
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

    def update_plugin_list(self):
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
            self.gui.page.update()
            return

        # 按名称排序
        sorted_plugins = self.logic.get_sorted_plugins()

        # 创建插件卡片
        for plugin_name, plugin_info in sorted_plugins:
            card = self._create_plugin_card(plugin_name, plugin_info)
            self.plugins_view.controls.append(card)

        self.gui.page.update()

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
            self.gui.show_snackbar("该插件没有设置页面")
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
                    ft.TextButton("返回", on_click=lambda e: self.gui.page.close(e.control.parent))
                ],
            )
            self.gui.page.open(dialog)
            self.gui.page.update()
        except Exception as ex:
            self.logic.log_error(f"打开设置页面失败: {ex}")
            self.gui.show_snackbar(f"打开设置失败: {ex}")

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
                ft.TextButton("关闭", on_click=lambda e: self.gui.page.close(e.control.parent))
            ]
        )

        self.gui.page.open(dialog)
        self.gui.page.update()

    def _toggle_plugin(self, e, plugin_name: str):
        """切换插件启用状态"""
        new_status = e.control.value
        success = self.logic.toggle_plugin(plugin_name, new_status)

        if success:
            self.update_plugin_list()
        else:
            # 操作失败，恢复开关状态
            e.control.value = not new_status
            self.gui.page.update()

    def _reload_plugin(self, e, plugin_name: str):
        """重载插件"""
        if self.logic.reload_plugin(plugin_name):
            self.update_plugin_list()