import time
import keyboard
import flet as ft
from ha_mqtt_discoverable import Settings
from ha_mqtt_discoverable.sensors import Button, ButtonInfo, Number, NumberInfo


class KeySim:
    def __init__(self, core):
        self.core = core
        self.click_count = 1  # 默认点击次数
        self.sleep_time = 0.1  # 默认延迟时间（秒）
        self.custom_keys = self.core.get_plugin_config("KeySim", "custom_keys", [])

        # 固定键映射
        self.key_map = {
            "play_pause": "play/pause media",
            "prev_track": "previous track",
            "next_track": "next track",
            "volume_up": "volume up",
            "volume_down": "volume down",
            "up": "up",
            "down": "down",
            "left": "left",
            "right": "right",
            "space": "space"
        }

        # 添加自定义键到 key_map
        for k in self.custom_keys:
            self.key_map[k] = k

        # 存储所有MQTT实体
        self.buttons = {}
        self.numbers = {}

        self.key_list_view = ft.ListView(spacing=8, padding=7, width=580, height=170, auto_scroll=True)

    def setup_entities(self):
        """设置MQTT实体"""
        try:
            # 获取MQTT配置
            mqtt_settings = self.core.mqtt.get_mqtt_settings()
            device_info = self.core.mqtt.get_device_info()

            # 预设按键配置
            button_configs = [
                {"name": "play_pause", "display_name": "按键-播放/暂停", "icon": "mdi:play-pause"},
                {"name": "prev_track", "display_name": "按键-上一曲", "icon": "mdi:skip-previous"},
                {"name": "next_track", "display_name": "按键-下一曲", "icon": "mdi:skip-next"},
                {"name": "volume_up", "display_name": "按键-音量增加", "icon": "mdi:volume-plus"},
                {"name": "volume_down", "display_name": "按键-音量减少", "icon": "mdi:volume-minus"},
                {"name": "up", "display_name": "按键-上", "icon": "mdi:arrow-up"},
                {"name": "down", "display_name": "按键-下", "icon": "mdi:arrow-down"},
                {"name": "left", "display_name": "按键-左", "icon": "mdi:arrow-left"},
                {"name": "right", "display_name": "按键-右", "icon": "mdi:arrow-right"},
                {"name": "space", "display_name": "按键-空格", "icon": "mdi:keyboard-space"}
            ]

            # 创建预设按钮
            for config in button_configs:
                button_info = ButtonInfo(
                    display_name=config["display_name"],
                    name=config["name"],
                    unique_id=f"{self.core.mqtt.device_name}_KeySim_{config['name']}",
                    device=device_info,
                    icon=config["icon"]
                )

                settings = Settings(mqtt=mqtt_settings, entity=button_info)
                self.buttons[config["name"]] = Button(settings, command_callback=lambda c, u, m, key=config["name"]: self.handle_button_press(key))
                self.buttons[config["name"]].write_config()

            # 创建自定义按键
            for key in self.custom_keys:
                button_info = ButtonInfo(
                    display_name=f"自定义按键-{key}",
                    name=f"custom_{key}",
                    unique_id=f"{self.core.mqtt.device_name}_KeySim_custom_{key}",
                    device=device_info,
                    icon="mdi:keyboard-outline"
                )

                settings = Settings(mqtt=mqtt_settings, entity=button_info)
                self.buttons[key] = Button(settings, command_callback=lambda c, u, m, k=key: self.handle_button_press(k))
                self.buttons[key].write_config()

            # 创建数字输入实体 - 点击次数
            click_count_info = NumberInfo(
                display_name="按键点击次数",
                name="click_count",
                unique_id=f"{self.core.mqtt.device_name}_KeySim_click_count",
                device=device_info,
                icon="mdi:counter",
                min=1,
                max=50,
                step=1
            )

            settings = Settings(mqtt=mqtt_settings, entity=click_count_info)
            self.numbers["click_count"] = Number(settings, command_callback=self.handle_click_count)
            self.numbers["click_count"].set_value(self.click_count)

            # 创建数字输入实体 - 等待时长
            sleep_time_info = NumberInfo(
                display_name="按键等待时长",
                name="sleep_time",
                unique_id=f"{self.core.mqtt.device_name}_KeySim_sleep_time",
                device=device_info,
                icon="mdi:timer",
                min=0.0,
                max=10.0,
                step=0.1
            )

            settings = Settings(mqtt=mqtt_settings, entity=sleep_time_info)
            self.numbers["sleep_time"] = Number(settings, command_callback=self.handle_sleep_time)
            self.numbers["sleep_time"].set_value(self.sleep_time)

            self.core.log.info("KeySim MQTT实体创建成功")
        except Exception as e:
            self.core.log.error(f"KeySim MQTT设置失败: {e}")

    def handle_button_press(self, key_name):
        """处理按钮按下"""
        self.core.log.info(f"按键触发: {key_name}")
        time.sleep(self.sleep_time)
        self.press_key(key_name)

    def handle_click_count(self, client, user_data, message):
        """处理点击次数变化"""
        try:
            count = int(float(message.payload.decode()))
            self.set_click_count(count)
        except Exception as e:
            self.core.log.error(f"处理点击次数失败: {e}")

    def handle_sleep_time(self, client, user_data, message):
        """处理等待时长变化"""
        try:
            time_val = float(message.payload.decode())
            self.set_sleep_time(time_val)
        except Exception as e:
            self.core.log.error(f"处理等待时长失败: {e}")

    # --- 核心功能 ---
    def press_key(self, key_name: str) -> bool:
        """模拟按键，重复 self.click_count 次"""
        if key_name not in self.key_map:
            return False
        try:
            for i in range(self.click_count):
                keyboard.send(self.key_map[key_name])
                time.sleep(self.sleep_time)
            return True
        except Exception as e:
            if self.core and hasattr(self.core, "log"):
                self.core.log.error(f"按键 {key_name} 执行失败: {e}")
            return False

    def set_click_count(self, count: int):
        self.click_count = max(1, min(50, count))
        self.core.log.info(f"更新点击次数为: {self.click_count}")

    def set_sleep_time(self, t: float):
        self.sleep_time = max(0.0, min(10, t))
        self.core.set_plugin_config("KeySim", "sleep_time", self.sleep_time)
        self.core.log.info(f"更新按键间隔时长为: {self.sleep_time}s")

    def add_custom_key(self, key: str):
        """添加自定义按键"""
        if key and key not in self.custom_keys:
            self.custom_keys.append(key)
            self.core.set_plugin_config("KeySim", "custom_keys", self.custom_keys)
            self.key_map[key] = key

            # 动态创建MQTT按钮实体
            try:
                mqtt_settings = self.core.mqtt.get_mqtt_settings()
                device_info = self.core.mqtt.get_device_info(
                    plugin_name="KeySim",
                    model="PCTools KeySim"
                )

                button_info = ButtonInfo(
                    display_name=f"自定义按键-{key}",
                    name=f"custom_{key}",
                    unique_id=f"{self.core.mqtt.device_name}_KeySim_custom_{key}",
                    device=device_info,
                    icon="mdi:keyboard-outline"
                )

                settings = Settings(mqtt=mqtt_settings, entity=button_info)
                self.buttons[key] = Button(settings, command_callback=lambda c, u, m, k=key: self.handle_button_press(k))

                self.core.log.info(f"新增自定义按键: {key}")
            except Exception as e:
                self.core.log.error(f"创建自定义按键MQTT实体失败: {e}")
        else:
            self.core.log.info(f"按键 {key} 已存在或无效")

    def delete_custom_key(self, key: str):
        """删除自定义按键"""
        if key in self.custom_keys:
            self.custom_keys.remove(key)
            self.core.set_plugin_config("KeySim", "custom_keys", self.custom_keys)
            self.key_map.pop(key, None)

            # 删除MQTT实体
            if key in self.buttons:
                del self.buttons[key]

            self.core.log.info(f"已删除按键: {key}")

    # --- UI 页面 ---
    def setting_page(self, e):
        """Flet 设置页面"""

        # 延迟时间设置
        slider_section = ft.Column([
            ft.Row([
                ft.Text("延迟时长(s):", width=80),
                ft.Slider(
                    value=self.sleep_time,
                    min=0.0,
                    max=10,
                    divisions=50,
                    label="{value}",
                    on_change=lambda e: self.set_sleep_time(float(e.control.value))
                )
            ])
        ])

        # 自定义按键区
        add_key_field = ft.TextField(label="新增按键", width=250)
        add_key_btn = ft.ElevatedButton(
            "添加按键",
            icon=ft.Icons.ADD,
            on_click=lambda ev: self._ui_add_key(ev, add_key_field)
        )

        key_list_section = ft.Column([
            ft.Text("自定义按键", size=16, weight=ft.FontWeight.BOLD),
            ft.Row([add_key_field, add_key_btn]),
            self.key_list_view
        ])

        self.update_key_list(e)

        # 保留原来的整体布局结构，只移除了 Card
        return ft.Container(
            ft.Column([
                slider_section,
                key_list_section
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def _ui_add_key(self, e, input_field):
        key = input_field.value.strip()
        if key:
            self.add_custom_key(key)
            self.update_key_list(e)
            self.core.show_toast("KeySim", f"已添加自定义按键: {key}")
            input_field.value = ""
            e.page.update()

    def update_key_list(self, e):
        """刷新自定义按键列表"""
        self.key_list_view.controls.clear()
        if self.custom_keys:
            for idx, k in enumerate(self.custom_keys):
                self.key_list_view.controls.append(
                    ft.Row([
                        ft.Text(f"{idx + 1}. {k}", size=16),
                        ft.IconButton(
                            ft.Icons.DELETE,
                            icon_color=ft.Colors.RED,
                            on_click=lambda ev, key=k: self._ui_delete_key(ev, key)
                        )
                    ])
                )
        else:
            self.key_list_view.controls.append(
                ft.Text("暂无自定义按键", color=ft.Colors.GREY_600)
            )
        if hasattr(e, "page"):
            e.page.update()

    def _ui_delete_key(self, e, key):
        self.delete_custom_key(key)
        self.update_key_list(e)
        self.core.show_toast("KeySim", f"已删除按键: {key}")
