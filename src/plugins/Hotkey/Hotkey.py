import keyboard
import time
import flet as ft
from ha_mqtt_discoverable import Settings
from ha_mqtt_discoverable.sensors import BinarySensor, BinarySensorInfo


class Hotkey:
    def __init__(self, core):
        self.core = core
        self.listening = False

        # 从配置中获取快捷键设置
        self.hotkey_notify = self.core.get_plugin_config("Hotkey", "Hotkey_notify", False)
        self.suppress = self.core.get_plugin_config("Hotkey", "Hotkey_suppress", False)
        self.hotkeys = self.core.get_plugin_config("Hotkey", "hotkeys", [])  # 从配置中读取快捷键列表

        # 存储所有MQTT二进制传感器
        self.sensors = {}

        self.hotkey_view = ft.ListView(height=320, width=600, spacing=10)
        self._page_ready = False  # 添加标志，表示控件是否已添加到页面

    def setup_entities(self):
        """设置MQTT实体"""
        try:
            # 获取MQTT配置
            mqtt_settings = self.core.mqtt.get_mqtt_settings()
            device_info = self.core.mqtt.get_device_info()

            # 为每个已保存的快捷键创建二进制传感器
            for hotkey in self.hotkeys:
                self.create_hotkey_sensor(hotkey, mqtt_settings, device_info)

            self.core.log.info(f"Hotkey MQTT实体创建成功，共 {len(self.sensors)} 个快捷键")
        except Exception as e:
            self.core.log.error(f"Hotkey MQTT设置失败: {e}")

    def create_hotkey_sensor(self, hotkey, mqtt_settings=None, device_info=None):
        """创建单个快捷键的二进制传感器"""
        try:
            # 如果没有提供配置，则获取
            if mqtt_settings is None:
                mqtt_settings = self.core.mqtt.get_mqtt_settings()
            if device_info is None:
                device_info = self.core.mqtt.get_device_info(
                    plugin_name="Hotkey",
                    model="PCTools Hotkey"
                )

            # 生成唯一ID（将+替换为-）
            safe_id = hotkey.replace("+", "_")

            sensor_info = BinarySensorInfo(
                name=f"hotkey_{safe_id}",
                unique_id=f"{self.core.mqtt.device_name}_Hotkey_{safe_id}",
                device=device_info,
                icon="mdi:keyboard"
            )
            sensor_info.display_name = f"快捷键-{hotkey}"

            settings = Settings(mqtt=mqtt_settings, entity=sensor_info)
            self.sensors[hotkey] = BinarySensor(settings)
            self.sensors[hotkey].off()  # 初始化为OFF状态

            self.core.log.info(f"创建快捷键传感器: {hotkey}")
        except Exception as e:
            self.core.log.error(f"创建快捷键传感器失败 {hotkey}: {e}")

    def show_toast(self, title, message):
        """显示通知"""
        if hasattr(self.core, 'show_toast'):
            self.core.show_toast("Hotkey", title, message)

    def save_hotkey(self, hotkey):
        """保存快捷键到配置"""
        existing_hotkeys = self.core.get_plugin_config("Hotkey", "hotkeys", [])
        if hotkey not in existing_hotkeys:
            existing_hotkeys.append(hotkey)
            self.core.set_plugin_config("Hotkey", "hotkeys", existing_hotkeys)
            self.hotkeys = existing_hotkeys  # 更新本地缓存

            # 动态创建MQTT传感器
            self.create_hotkey_sensor(hotkey)

            self.core.log.info(f"保存快捷键: {hotkey}")
        else:
            self.core.log.info(f"快捷键 '{hotkey}' 已存在，未保存。")

    def capture_hotkeys(self):
        self.core.log.info("开始捕获快捷键，按 'esc' 停止捕获...")
        captured_hotkeys = []

        def record_hotkey():
            hotkey = keyboard.read_event().name
            if hotkey != 'esc':
                captured_hotkeys.append(hotkey)
                self.core.log.info(f"捕获到快捷键: {captured_hotkeys}")

        while True:
            event = keyboard.read_event()
            if event.event_type == keyboard.KEY_DOWN:
                if event.name == 'esc':
                    break
                record_hotkey()

        hotkey_join = '+'.join(captured_hotkeys)
        self.save_hotkey(hotkey_join)
        return hotkey_join

    def command(self, h: str):
        key_list = h.split('+')
        for item in key_list:
            keyboard.release(item)
        self.core.log.info(f"触发快捷键: {h}")
        if self.hotkey_notify:
            self.show_toast("Hotkey", "触发快捷键:" + h)

        # 使用新的传感器更新状态
        if h in self.sensors:
            self.sensors[h].on()
            time.sleep(1)
            self.sensors[h].off()

    def start(self):
        if not self.listening:
            self.listening = True
            self.core.log.info(f"开始监听快捷键...{self.hotkeys}")
            for hotkey in self.hotkeys:
                keyboard.add_hotkey(hotkey, lambda h=hotkey: self.command(h), suppress=self.suppress,
                                    trigger_on_release=False)
            return 0
        return 1

    def stop(self):
        if self.listening:
            self.listening = False
            for hotkey in self.hotkeys:
                keyboard.remove_hotkey(hotkey)
            self.core.log.debug("已停止监听快捷键")
            return 0
        return 1

    def button_add_hotkey(self, e):
        """添加新的快捷键按钮回调"""
        if not hasattr(self.core, 'is_running') or not self.core.is_running:
            self.core.show_toast("Hotkey", "将记录按下的所有按键,按ESC停止并保存")
            new_hotkey = self.capture_hotkeys()
            self.core.show_toast("Hotkey", "已添加新快捷键" + new_hotkey)
            self.update_hotkey_list(e)
        else:
            self.core.show_toast("Hotkey", "请先停止服务")

    def button_listen_hotkeys(self, e):
        """开始监听快捷键按钮回调"""
        if self.start() == 0:
            self.core.show_toast("Hotkey", "开始测试快捷键监听")
        else:
            self.core.show_toast("Hotkey", "已经启动快捷键监听")

    def button_stop_listen(self, e):
        """停止监听快捷键按钮回调"""
        if self.stop() == 0:
            self.core.show_toast("Hotkey", "停止快捷键监听")
        else:
            self.core.show_toast("Hotkey", "请先启动快捷键监听")

    def update_hotkey_list(self, e):
        """更新热键列表视图"""
        self.hotkey_view.controls.clear()
        if hasattr(self, 'hotkeys') and self.hotkeys:
            for hotkey in self.hotkeys:
                self.hotkey_view.controls.append(
                    ft.Row(
                        [
                            ft.Container(width=85),
                            ft.ElevatedButton(
                                content=ft.Row(
                                    [
                                        ft.Text(
                                            hotkey, weight=ft.FontWeight.W_600, size=17),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                                ),
                                width=120,
                                height=40
                            ),
                            ft.Container(width=40),
                            ft.IconButton(
                                ft.Icons.DELETE, on_click=lambda e, h=hotkey: self.delete_hotkey(e, h)),
                        ],
                    )
                )
        else:
            self.hotkey_view.controls.append(ft.Row(
                [
                    ft.Container(width=150),
                    ft.Text("TAT..啥都木有", size=15)
                ])
            )

        e.page.update()

    def delete_hotkey(self, e, hotkey):
        """从列表中删除快捷键并更新视图"""
        if hotkey in self.hotkeys:
            updated_hotkeys = [h for h in self.hotkeys if h != hotkey]
            self.core.set_plugin_config("Hotkey", "hotkeys", updated_hotkeys)
            self.hotkeys = updated_hotkeys  # 更新本地缓存

            # 删除MQTT传感器
            if hotkey in self.sensors:
                del self.sensors[hotkey]

            self.update_hotkey_list(e)
            self.core.show_toast("Hotkey", f"已删除快捷键: {hotkey}")

    def button_switch(self, field_name):
        """开关按钮回调"""

        def callback(e):
            value = e.control.value
            self.core.set_plugin_config("Hotkey", field_name, value)

        return callback

    def setting_page(self, e):
        """优化后的设置页面"""
        # 当设置页面被加载时，标记控件已添加到页面
        self._page_ready = True

        # 创建卡片容器
        def create_card(content, title=None):
            return ft.Card(
                content=ft.Container(
                    ft.Column([
                        ft.Text(title, size=16, weight=ft.FontWeight.BOLD) if title else None,
                        content
                    ], spacing=10),
                    padding=9,
                    border_radius=10
                ),
                elevation=5,
                margin=10
            )

        # 快捷键列表控件
        self.hotkey_view = ft.ListView(
            spacing=8,
            padding=7,
            width=580,
            height=300,
            divider_thickness=1,
            auto_scroll=True
        )

        # 创建各功能区域
        instruction_card = create_card(
            ft.Text(
                "点击'新增按键'后，逐个按下所需组合键（无需同时按），按ESC结束录制并自动保存",
                size=14,
                color=ft.Colors.BLUE_800
            ),
            "操作说明"
        )

        switch_card = create_card(
            ft.Row(
                [
                    ft.Switch(
                        label="触发通知",
                        label_position='left',
                        value=self.hotkey_notify,
                        on_change=self.button_switch("Hotkey_notify"),
                        active_color=ft.Colors.GREEN
                    ),
                    ft.Switch(
                        label="阻断按键",
                        label_position='left',
                        value=self.suppress,
                        on_change=self.button_switch("Hotkey_suppress"),
                        active_color=ft.Colors.GREEN,
                        tooltip="阻止快捷键被其它软件响应"
                    ),
                ],
                spacing=30,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            "功能设置"
        )

        button_card = create_card(
            ft.Row(
                [
                    ft.ElevatedButton(
                        "新增按键",
                        icon=ft.Icons.ADD,
                        on_click=self.button_add_hotkey,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=5),
                            padding=9
                        )
                    ),
                    ft.ElevatedButton(
                        "开始监听",
                        icon=ft.Icons.PLAY_ARROW,
                        on_click=self.button_listen_hotkeys,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=5),
                            padding=9,
                            color=ft.Colors.GREEN
                        )
                    ),
                    ft.ElevatedButton(
                        "停止监听",
                        icon=ft.Icons.STOP,
                        on_click=self.button_stop_listen,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=5),
                            padding=9,
                            color=ft.Colors.RED
                        )
                    )
                ],
                spacing=15,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            "操作按钮"
        )

        # 构建主界面
        hotkey_page = ft.Column(
            [
                instruction_card,
                switch_card,
                button_card,
                create_card(
                    self.hotkey_view,
                    "已配置的快捷键"
                )
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO
        )

        self.update_hotkey_list(e)

        return ft.Container(
            hotkey_page,
            padding=1,
            margin=1
        )

    def update_hotkey_list(self, e):
        """优化后的热键列表更新函数"""
        self.hotkey_view.controls.clear()

        if hasattr(self, 'hotkeys') and self.hotkeys:
            for idx, hotkey in enumerate(self.hotkeys):
                # 创建带边框的每个快捷键条目
                self.hotkey_view.controls.append(
                    ft.Container(
                        ft.Row(
                            [
                                ft.Text(f"{idx + 1}.", width=30, size=14),
                                ft.Container(
                                    ft.Text(
                                        hotkey,
                                        size=16,
                                        weight=ft.FontWeight.W_600,
                                        selectable=True
                                    ),
                                    padding=7,
                                    border=ft.border.all(1, ft.Colors.GREY_300),
                                    border_radius=5,
                                    bgcolor=ft.Colors.GREY_100,
                                    expand=True
                                ),
                                ft.IconButton(
                                    ft.Icons.DELETE,
                                    icon_color=ft.Colors.RED,
                                    tooltip="删除该快捷键",
                                    on_click=lambda e, h=hotkey: self.delete_hotkey(e, h)
                                ),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10
                        ),
                        padding=5
                    )
                )
        else:
            # 空列表提示
            self.hotkey_view.controls.append(
                ft.Container(
                    ft.Column(
                        [
                            ft.Icon(ft.Icons.KEYBOARD_ALT, size=40, color=ft.Colors.GREY_400),
                            ft.Text("暂无快捷键配置", size=16, color=ft.Colors.GREY_600)
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10
                    ),
                    padding=20,
                    alignment=ft.alignment.center
                )
            )

        if hasattr(e, 'page'):
            e.page.update()

