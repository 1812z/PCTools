"""
关于页模块
"""

import flet as ft


class AboutPage:
    """关于页类"""

    def __init__(self, gui):
        """初始化关于页"""
        self.gui = gui
        self.logic = gui.logic
        self.page = gui.page

    def create(self) -> ft.Column:
        """创建关于页"""
        update_component = self.gui.updater.create_update_ui(self.gui.page) if self.gui.updater else ft.Container()

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