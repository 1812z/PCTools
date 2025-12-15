"""
Aida64 硬件监控插件
使用 ha-mqtt-discoverable 管理 Home Assistant 实体
使用 JSON 模板方式批量更新传感器数据
"""
import json
import time
import flet as ft
import python_aida64
from ha_mqtt_discoverable.sensors import Sensor, SensorInfo
from ha_mqtt_discoverable import Settings


class Aida64:
    def __init__(self, core):
        self.core = core
        self.log = core.log

        # 定时更新配置
        self.update_interval = self.core.get_plugin_config("Aida64", "aida64_updater", 5)
        self.updater = {
            "timer": self.update_interval,
        }

        # 数据缓存
        self.last_data = None
        self.last_item_count = {}

        # 自动重新discovery配置
        self.auto_rediscovery = self.core.get_plugin_config("Aida64", "auto_rediscovery", False)
        self.last_discovery_time = 0
        self.min_discovery_interval = 30

        # 存储所有传感器实体
        self.sensors = {}

        # 统一的更新主题
        self.state_topic = f"{self.core.mqtt.prefix}/sensor/{self.core.mqtt.device_name}/aida64/state"

    def setup_entities(self):
        """设置所有传感器实体"""
        try:
            # 获取初始数据以确定要创建哪些传感器
            aida64_data = self.get_aida64_data()
            if not aida64_data:
                self.log.warning("无法获取 Aida64 数据，稍后将重试")
                return

            mqtt_settings = self.core.mqtt.get_mqtt_settings()
            device_info = self.core.mqtt.get_device_info()

            # 分类计数器
            category_counters = {
                'temp': 0, 'pwr': 0, 'fan': 0, 'sys': 0,
                'volt': 0, 'curr': 0, 'duty': 0
            }

            created_count = 0

            # 遍历所有数据项创建传感器
            for category, items in aida64_data.items():
                if category not in category_counters:
                    continue

                for idx, item in enumerate(items):
                    try:
                        sensor_name = item["label"]
                        sensor_id = item["id"]
                        unique_id = f"{self.core.mqtt.device_name}_aida64_{sensor_id}"
                        # 使用 value_template 从 JSON 中提取值
                        value_template = f"{{{{ value_json.{category}[{idx}].value }}}}"

                        # 创建传感器信息
                        sensor_info = SensorInfo(
                            name=sensor_name,
                            unique_id=unique_id,
                            object_id=unique_id,
                            device=device_info,
                            value_template=value_template,
                            icon=self._get_icon(category, sensor_name),
                            unit_of_measurement=self._get_unit(category, sensor_name),
                            device_class=self._get_device_class(category),
                            expire_after=self.update_interval
                        )

                        # 创建传感器
                        sensor = Sensor(Settings(mqtt=mqtt_settings, entity=sensor_info))

                        # 创建后手动设置 state_topic 并重写配置
                        sensor.state_topic = self.state_topic
                        sensor.write_config()

                        # 存储传感器引用
                        key = f"{category}_{idx}"
                        self.sensors[key] = {
                            "sensor": sensor,
                            "category": category,
                            "index": idx,
                            "id": sensor_id,
                            "name": sensor_name
                        }

                        created_count += 1
                        category_counters[category] += 1
                    except (KeyError, IndexError) as e:
                        self.log.error(f"创建传感器失败: {e}, item: {item}")

            self.log.info(f"Aida64 传感器创建完成: 共 {created_count} 个")

            # 打印各类别统计
            for category, count in category_counters.items():
                if count > 0:
                    self.log.debug(f"  {category}: {count} 个")

        except Exception as e:
            self.log.error(f"设置 Aida64 传感器失败: {e}")

    def _get_icon(self, category, name):
        """根据类别和名称获取图标"""
        name_lower = name.lower()

        # 系统类别特殊处理
        if category == "sys":
            if "disk" in name_lower:
                return "mdi:harddisk"
            elif "network" in name_lower or "nic" in name_lower:
                return "mdi:network"
            elif "gpu" in name_lower:
                return "mdi:expansion-card"
            elif "memory" in name_lower or "ram" in name_lower:
                return "mdi:memory"
            elif "cpu" in name_lower:
                return "mdi:cpu-64-bit"
            elif "clock" in name_lower:
                return "mdi:clock-outline"

        # 其他类别
        icon_map = {
            "temp": "mdi:thermometer",
            "pwr": "mdi:flash",
            "fan": "mdi:fan",
            "volt": "mdi:lightning-bolt",
            "curr": "mdi:current-ac",
            "duty": "mdi:gauge"
        }

        return icon_map.get(category, "mdi:information")

    def _get_unit(self, category, name):
        """根据类别和名称获取单位"""
        name_lower = name.lower()

        # 系统类别特殊处理
        if category == "sys":
            if "utilization" in name_lower or "usage" in name_lower or "activity" in name_lower:
                return "%"
            elif "clock" in name_lower and "mhz" not in name_lower:
                return "MHz"
            elif "memory" in name_lower and "total" not in name_lower:
                return "MB"
            elif "disk" in name_lower and "activity" not in name_lower:
                return "KB/s"
            elif "network" in name_lower or "nic" in name_lower:
                if "total" in name_lower:
                    return "MB"
                else:
                    return "KB/s"
            return None

        # 其他类别
        unit_map = {
            "temp": "°C",
            "pwr": "W",
            "fan": "RPM",
            "volt": "V",
            "curr": "A",
            "duty": "%"
        }

        return unit_map.get(category)

    def _get_device_class(self, category):
        """根据类别获取设备类型"""
        class_map = {
            "temp": "temperature",
            "pwr": "power",
            "volt": "voltage",
            "curr": "current"
        }
        return class_map.get(category)

    def get_aida64_data(self):
        """获取 AIDA64 数据"""
        try:
            aida64_data = python_aida64.getData()
            if not aida64_data:
                self.log.error("Aida64 数据读取失败：返回空数据")
                return None

            self.last_data = aida64_data

            # 检查数据项数量变化（仅在自动重新discovery开启时）
            if self.auto_rediscovery:
                self.check_item_count_change(aida64_data)

            return aida64_data

        except Exception as e:
            self.log.error(f"Aida64 数据读取异常: {e}")
            return None

    def check_item_count_change(self, data):
        """检查数据项数量是否变化"""
        current_count = {}
        total_items = 0

        for category, items in data.items():
            if isinstance(items, list):
                current_count[category] = len(items)
                total_items += len(items)

        # 比较数量变化
        if current_count != self.last_item_count and self.last_item_count:
            current_time = time.time()

            if current_time - self.last_discovery_time >= self.min_discovery_interval:
                changes = []
                for cat in set(list(current_count.keys()) + list(self.last_item_count.keys())):
                    old = self.last_item_count.get(cat, 0)
                    new = current_count.get(cat, 0)
                    if old != new:
                        changes.append(f"{cat}: {old} -> {new}")

                self.log.info(f"检测到数据项数量变化: {', '.join(changes)}")
                self.log.info("需要重新创建传感器...")

                # 重新创建传感器
                self.sensors.clear()
                self.setup_entities()

                self.last_discovery_time = current_time
                self.last_item_count = current_count.copy()
        elif not self.last_item_count:
            self.last_item_count = current_count.copy()
            self.log.debug(f"初始数据项数量: 总计 {total_items}")

    def update_state(self):
        """更新状态 - 发送整个 JSON 到统一主题"""
        if not self.core.mqtt.is_connected():
            return False

        aida64_data = self.get_aida64_data()
        if not aida64_data:
            self.log.warning("状态更新失败：无法获取 Aida64 数据")
            return False

        try:
            # 发布 JSON 数据到统一的状态主题
            payload = json.dumps(aida64_data)

            # 使用第一个传感器的 MQTT 客户端发布（所有传感器共享同一个客户端）
            if self.sensors:
                first_sensor = next(iter(self.sensors.values()))["sensor"]
                result = first_sensor.mqtt_client.publish(self.state_topic, payload, retain=True)

                if result.rc == 0:  # MQTT_ERR_SUCCESS
                    self.log.debug(f"Aida64 状态更新成功 ({len(self.sensors)} 个传感器)")
                    return True
                else:
                    self.log.warning(f"Aida64 状态更新失败，MQTT 错误码: {result.rc}")
                    return False
            else:
                # 如果没有传感器，直接使用核心 MQTT 客户端
                result = self.core.mqtt.publish(self.state_topic, payload)
                if result:
                    self.log.debug("Aida64 状态更新成功（无传感器情况）")
                else:
                    self.log.warning("Aida64 状态更新失败（无传感器情况）")
                return result

        except Exception as e:
            self.log.error(f"状态更新异常: {e}")
            return False

    def get_item_count_summary(self):
        """获取数据项数量摘要"""
        if not self.last_item_count:
            return "未读取数据"

        parts = [f"{cat}:{count}" for cat, count in self.last_item_count.items()]
        total = sum(self.last_item_count.values())
        return f"{', '.join(parts)} (总计:{total})"

    def on_unload(self):
        """插件卸载时清理资源"""
        try:
            self.log.info("Aida64 插件正在卸载")
            self.sensors.clear()
            self.last_data = None
            self.log.info("Aida64 插件已卸载")
        except Exception as e:
            self.log.error(f"卸载 Aida64 插件失败: {e}")

    # ===== GUI 设置页面 =====

    def setting_page(self, e=None):
        """设置页面"""
        current_interval = self.core.get_plugin_config("Aida64", "aida64_updater", 5)
        auto_rediscovery_enabled = self.core.get_plugin_config("Aida64", "auto_rediscovery", False)

        status_text = ft.Text("", color=ft.Colors.GREEN, visible=False)

        def save_setting(e):
            try:
                value = int(interval_field.value)
                if value < 1:
                    status_text.value = "✗ 更新间隔必须大于0秒"
                    status_text.color = ft.Colors.RED
                    status_text.visible = True
                    status_text.update()
                    return

                self.core.set_plugin_config("Aida64", "aida64_updater", value)
                self.updater["timer"] = value

                status_text.value = f"✓ 设置已保存：{value}秒"
                status_text.color = ft.Colors.GREEN
                status_text.visible = True
                status_text.update()

            except ValueError:
                status_text.value = "✗ 请输入有效数字"
                status_text.color = ft.Colors.RED
                status_text.visible = True
                status_text.update()

        interval_field = ft.TextField(
            label="秒",
            value=str(current_interval),
            width=100,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_submit=save_setting,
            hint_text="1-3600"
        )

        def toggle_auto_rediscovery(e):
            self.auto_rediscovery = e.control.value
            self.core.set_plugin_config("Aida64", "auto_rediscovery", self.auto_rediscovery)

            status_text.value = f"✓ 自动重新创建传感器已{'启用' if self.auto_rediscovery else '禁用'}"
            status_text.color = ft.Colors.GREEN
            status_text.visible = True
            status_text.update()

            if self.auto_rediscovery and self.last_data:
                self.last_item_count = {}
                for category, items in self.last_data.items():
                    if isinstance(items, list):
                        self.last_item_count[category] = len(items)
                self.log.info(f"自动重建已启用，当前数据项: {self.get_item_count_summary()}")

        auto_rediscovery_switch = ft.Switch(
            label="自动重新创建传感器",
            value=auto_rediscovery_enabled,
            on_change=toggle_auto_rediscovery,
            tooltip="当检测到数据项数量变化时自动重新创建传感器"
        )

        def test_read_data(e):
            data = self.get_aida64_data()
            if data:
                e.control.text = "✓ 读取成功"
                e.control.bgcolor = ft.Colors.GREEN
                e.control.update()

                json_str = json.dumps(data, indent=2, ensure_ascii=False)

                stats_text = "数据统计:\n"
                for category, items in data.items():
                    if isinstance(items, list):
                        stats_text += f"  {category}: {len(items)} 项\n"

                dlg = ft.AlertDialog(
                    title=ft.Text("Aida64 数据", weight=ft.FontWeight.BOLD),
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(stats_text, weight=ft.FontWeight.BOLD),
                            ft.Divider(),
                            ft.Text("JSON数据:", weight=ft.FontWeight.BOLD),
                            ft.Container(
                                content=ft.TextField(
                                    value=json_str,
                                    multiline=True,
                                    read_only=True,
                                    min_lines=10,
                                    max_lines=20,
                                    text_size=12,
                                ),
                                width=600,
                                height=330,
                            ),
                        ]),
                        width=650,
                        height=450,
                    ),
                    actions=[
                        ft.TextButton("复制", on_click=lambda _: e.page.set_clipboard(json_str)),
                        ft.TextButton("关闭", on_click=lambda _: close_dlg()),
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                )

                def close_dlg():
                    dlg.open = False
                    e.page.update()

                e.page.overlay.append(dlg)
                dlg.open = True
                e.page.update()
            else:
                e.control.text = "✗ 读取失败"
                e.control.bgcolor = ft.Colors.RED
                e.control.update()

        def manual_update(e):
            result = self.update_state()
            if result:
                e.control.text = "✓ 更新成功"
                e.control.bgcolor = ft.Colors.GREEN
            else:
                e.control.text = "✗ 更新失败"
                e.control.bgcolor = ft.Colors.RED
            e.control.update()

        def recreate_sensors(e):
            try:
                self.sensors.clear()
                self.setup_entities()
                e.control.text = "✓ 重建完成"
                e.control.bgcolor = ft.Colors.GREEN
            except Exception as ex:
                self.log.error(f"重建传感器失败: {ex}")
                e.control.text = "✗ 重建失败"
                e.control.bgcolor = ft.Colors.RED
            e.control.update()

        def reset_count(e):
            self.last_item_count = {}
            self.last_discovery_time = 0
            status_text.value = "✓ 数据计数已重置"
            status_text.color = ft.Colors.GREEN
            status_text.visible = True
            status_text.update()

        return ft.Column([
            ft.Divider(),
            ft.Row([
                ft.Text("数据更新间隔:", width=120),
                interval_field,
            ], alignment=ft.MainAxisAlignment.START),
            ft.Row([
                auto_rediscovery_switch,
                ft.Text("新增/删除数据项时自动重新创建传感器", size=12, color=ft.Colors.GREY_700),
            ], spacing=10),
            status_text,
            ft.Divider(),
            ft.Row([
                ft.ElevatedButton("测试读取", icon=ft.Icons.CABLE, on_click=test_read_data),
                ft.ElevatedButton("手动更新", icon=ft.Icons.REFRESH, on_click=manual_update),
            ], spacing=10),
            ft.Row([
                ft.ElevatedButton("重新创建传感器", icon=ft.Icons.AUTORENEW, on_click=recreate_sensors),
                ft.ElevatedButton("重置计数", icon=ft.Icons.RESTART_ALT, on_click=reset_count),
            ], spacing=10),
            ft.Divider(),
            ft.Text("当前状态:", weight=ft.FontWeight.BOLD),
            ft.Text(f"更新间隔: {current_interval}秒"),
            ft.Text(f"自动重建: {'启用' if auto_rediscovery_enabled else '禁用'}"),
            ft.Text(f"传感器数量: {len(self.sensors)}"),
            ft.Text(f"数据项统计: {self.get_item_count_summary()}"),
            ft.Divider(),
            ft.Text("使用说明:", weight=ft.FontWeight.BOLD, size=14),
            ft.Text(
                "• 使用 JSON 模板方式批量管理传感器\n"
                "• 所有传感器共享同一个状态主题，减少 MQTT 流量\n"
                "• 自动重建：检测到数据项变化时自动重新创建传感器\n"
                "• 最小重建间隔：30秒",
                size=12,
                color=ft.Colors.GREY_700,
            ),
        ], spacing=15, scroll=ft.ScrollMode.ADAPTIVE)