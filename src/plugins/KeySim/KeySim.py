import time
import keyboard
import flet as ft


class KeySim:
    def __init__(self, core):
        self.core = core
        self.click_count = 1  # 默认点击次数
        self.sleep_time = 0.1  # 默认延迟时间（秒）
        self.custom_keys = self.core.get_plugin_config("KeySim", "custom_keys", [])

        # 预设按键
        self.config = [
            {"name": "按键-播放/暂停", "entity_type": "button", "entity_id": "play_pause", "icon": "mdi:play-pause"},
            {"name": "按键-上一曲", "entity_type": "button", "entity_id": "prev_track", "icon": "mdi:skip-previous"},
            {"name": "按键-下一曲", "entity_type": "button", "entity_id": "next_track", "icon": "mdi:skip-next"},
            {"name": "按键-音量增加", "entity_type": "button", "entity_id": "volume_up", "icon": "mdi:volume-plus"},
            {"name": "按键-音量减少", "entity_type": "button", "entity_id": "volume_down", "icon": "mdi:volume-minus"},
            {"name": "按键-上", "entity_type": "button", "entity_id": "up", "icon": "mdi:arrow-up"},
            {"name": "按键-下", "entity_type": "button", "entity_id": "down", "icon": "mdi:arrow-down"},
            {"name": "按键-左", "entity_type": "button", "entity_id": "left", "icon": "mdi:arrow-left"},
            {"name": "按键-右", "entity_type": "button", "entity_id": "right", "icon": "mdi:arrow-right"},
            {"name": "按键-空格", "entity_type": "button", "entity_id": "space", "icon": "mdi:keyboard-space"},
            {"name": "按键点击次数", "entity_type": "number", "entity_id": "click_count", "icon": "mdi:counter"},
            {"name": "按键等待时长", "entity_type": "number", "entity_id": "sleep_time", "icon": "mdi:timer"}
        ]

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

        # 自定义按键发现
        for key in self.custom_keys:
            if not any(cfg.get("entity_id") == key for cfg in self.config):
                self.config.append({
                    "name": f"自定义按键-{key}",
                    "entity_type": "button",
                    "entity_id": key,
                    "icon": "mdi:keyboard-outline"
                })

        self.key_list_view = ft.ListView(spacing=8, padding=7, width=580, height=170, auto_scroll=True)

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
            self.core.log.info(f"新增自定义按键: {key}")
        else:
            self.core.log.info(f"按键 {key} 已存在或无效")

    def delete_custom_key(self, key: str):
        """删除自定义按键"""
        if key in self.custom_keys:
            self.custom_keys.remove(key)
            self.core.set_plugin_config("KeySim", "custom_keys", self.custom_keys)
            self.key_map.pop(key, None)
            self.core.log.info(f"已删除按键: {key}")

    def handle_mqtt(self, topic, data):
        """MQTT 命令分流"""
        if topic == "click_count":
            self.set_click_count(int(data))
        elif topic == "sleep_time":
            self.set_sleep_time(float(data))
        else:
            time.sleep(self.sleep_time)
            self.press_key(topic)

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
