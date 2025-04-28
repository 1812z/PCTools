import keyboard
import time
import flet as ft


class Hotkey:
    def __init__(self, core):
        self.core = core
        self.listening = False

        self.hotkey_notify = self.core.config.get_config("Hotkey_notify")
        self.suppress = self.core.config.get_config("Hotkey_suppress")
        self.device_name = self.core.config.get_config("device_name")
        self.prefix = self.core.config.get_config("ha_prefix")
        self.hotkeys = self.load_hotkeys()

        self.hotkey_view = ft.ListView(height=320, width=600, spacing=10)
        self._page_ready = False  # 添加标志，表示控件是否已添加到页面     
                
    def show_toast(self, title, message):
        """显示通知"""
        if hasattr(self.core, 'show_toast'):
            self.core.show_toast("Hotkey", title, message)

    def send_discovery(self, hotkeys):
        info = "快捷键发现: \n"
        for hotkey in hotkeys:
            name_id = "hotkey" + hotkey.replace("+", "-")
            self.core.mqtt.send_mqtt_discovery(name=hotkey, entity_id=name_id, entity_type="binary_sensor")
            info = info + hotkey
        time.sleep(0.5)
        self.init_binary_sensor(hotkeys)
        return info

    def init_binary_sensor(self, hotkeys):
        for hotkey in hotkeys:
            hotkey: str
            topic = f"{self.prefix}/binary_sensor/{self.device_name}_Hotkey_{hotkey.replace('+', '-')}/state"
            self.core.mqtt.publish(topic, "OFF")

    def save_hotkey(self, hotkey):
        existing_hotkeys = self.load_hotkeys()
        if hotkey not in existing_hotkeys:
            with open('hotkeys.txt', 'a') as file:
                file.write(hotkey + '\n')
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

    def load_hotkeys(self):
        try:
            with open('hotkeys.txt', 'r') as file:
                hotkeys = [line.strip() for line in file.readlines()]
                return hotkeys
        except FileNotFoundError:
            self.core.log.error("hotkeys.txt加载失败")
            return []

    def save_hotkeys_to_file(self):
        """保存热键到文件"""
        try:
            with open('hotkeys.txt', 'w') as file:
                for hotkey in self.hotkeys:
                    file.write(hotkey + '\n')
        except Exception as e:
            self.core.log.error(f"保存热键文件失败: {e}")

    def command(self, h: str):
        key_list = h.split('+')
        for item in key_list:
            keyboard.release(item)
        self.core.log.info(f"触发快捷键: {h}")
        if self.hotkey_notify:
            self.show_toast("Hotkey", "触发快捷键:" + h)
        topic = f"{self.prefix}/binary_sensor/{self.device_name}_hotkey{h.replace('+', '-')}/state"
        self.core.mqtt.publish(topic, "ON")
        time.sleep(1)
        self.core.mqtt.publish(topic, "OFF")

    def start(self):
        if not self.listening:
            self.listening = True
            self.send_discovery(self.hotkeys)
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
            self.core.log.info("已停止监听快捷键")
            return 0
        return 1

    def button_add_hotkey(self, e):
        """添加新的快捷键按钮回调"""
        if not hasattr(self.core, 'is_running') or not self.core.is_running:

            self.core.show_toast("Hotkey", "将记录按下的所有按键,按ESC停止并保存")
            new_hotkey = self.capture_hotkeys()
            self.core.show_toast("Hotkey", "已添加新快捷键" + new_hotkey)
            self.hotkeys.append(new_hotkey)
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
                                ft.icons.DELETE, on_click=lambda e, h=hotkey: self.delete_hotkey(e,h)),
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
            self.hotkeys.remove(hotkey)
            self.save_hotkeys_to_file()
            self.update_hotkey_list(e)

            self.core.show_toast("Hotkey", f"已删除快捷键: {hotkey}")

    def button_switch(self, field_name):
        """开关按钮回调"""
        def callback(e):
            value = e.control.value
            self.core.config.set_config(field_name, value)

        return callback

    def setting_page(self,e):
        """设置页面"""
        # 当设置页面被加载时，标记控件已添加到页面
        self._page_ready = True

        hotkey_page = [
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Switch(label="触发通知", label_position='left',
                                      scale=1.2, value=self.hotkey_notify,
                                      on_change=self.button_switch("Hotkey_notify")),
                            ft.Container(width=20),
                            ft.Switch(label="阻断按键", label_position='left',
                                      scale=1.2, value=self.suppress, on_change=self.button_switch("Hotkey_suppress"),
                                      tooltip="阻止快捷键被其它软件响应"),
                        ], alignment=ft.MainAxisAlignment.CENTER
                    ),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                content=ft.Row(
                                    [
                                        ft.Text(
                                            "新增按键", weight=ft.FontWeight.W_600, size=17),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                                ),
                                on_click=self.button_add_hotkey,
                                width=120,
                                height=40
                            ),
                            ft.ElevatedButton(
                                content=ft.Row(
                                    [
                                        ft.Text(
                                            "开始监听", weight=ft.FontWeight.W_600, size=17),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                                ),
                                on_click=self.button_listen_hotkeys,
                                width=120,
                                height=40
                            ),
                            ft.ElevatedButton(
                                content=ft.Row(
                                    [
                                        ft.Text(
                                            "停止监听", weight=ft.FontWeight.W_600, size=17),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                                ),
                                on_click=self.button_stop_listen,
                                width=120,
                                height=40
                            )
                        ], alignment=ft.MainAxisAlignment.CENTER
                    ),
                    self.hotkey_view
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        ]

        self.update_hotkey_list(e)

        return hotkey_page
