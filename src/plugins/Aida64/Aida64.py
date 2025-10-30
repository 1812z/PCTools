import json
import time
import flet as ft
import python_aida64


class Aida64:
    def __init__(self, core):
        self.core = core
        self.updater = {
            "timer": self.core.get_plugin_config("Aida64", "aida64_updater", 5),
        }
        self.last_data = None  # 缓存上次的数据
        self.last_item_count = {}  # 记录上次各类别的数据项数量
        self.auto_rediscovery = self.core.get_plugin_config("Aida64", "auto_rediscovery", False)  # 自动重新discovery开关
        self.last_discovery_time = 0  # 上次discovery的时间戳
        self.min_discovery_interval = 30  # 最小discovery间隔（秒）

    def get_aida64_data(self):
        """获取AIDA64数据，带异常处理"""
        try:
            aida64_data = python_aida64.getData()
            if not aida64_data:
                self.core.log.error("Aida64数据读取失败：返回空数据")
                return None

            self.last_data = aida64_data  # 缓存数据

            # 检查数据项数量变化（仅在自动重新discovery开启时）
            if self.auto_rediscovery:
                self.check_item_count_change(aida64_data)

            return aida64_data

        except Exception as e:
            self.core.log.error(f"Aida64数据读取异常: {e}")
            return None

    def check_item_count_change(self, data):
        """检查数据项数量是否变化，如果变化则触发discovery"""
        current_count = {}
        total_items = 0

        # 统计当前各类别的数据项数量
        for category, items in data.items():
            if isinstance(items, list):
                current_count[category] = len(items)
                total_items += len(items)

        # 比较数量是否变化
        if current_count != self.last_item_count and self.last_item_count:
            current_time = time.time()

            # 检查是否超过最小间隔时间
            if current_time - self.last_discovery_time >= self.min_discovery_interval:
                # 详细记录变化
                changes = []
                for cat in set(list(current_count.keys()) + list(self.last_item_count.keys())):
                    old = self.last_item_count.get(cat, 0)
                    new = current_count.get(cat, 0)
                    if old != new:
                        changes.append(f"{cat}: {old} -> {new}")

                self.core.log.info(f"检测到数据项数量变化: {', '.join(changes)}")
                self.core.log.info(f"总数据项: {sum(self.last_item_count.values())} -> {total_items}")
                self.core.log.info("自动触发重新discovery...")

                # 执行discovery
                if self.discovery():
                    self.last_discovery_time = current_time
                    self.last_item_count = current_count.copy()
                    self.core.log.info("自动discovery完成")
            else:
                remaining_time = self.min_discovery_interval - (current_time - self.last_discovery_time)
                self.core.log.debug(f"数据项变化但未到最小间隔时间，还需等待 {remaining_time:.1f} 秒")
        elif not self.last_item_count:
            # 第一次记录数量
            self.last_item_count = current_count.copy()
            self.core.log.debug(f"初始数据项数量: {self.last_item_count}, 总计: {total_items}")

    def get_item_count_summary(self):
        """获取数据项数量摘要"""
        if not self.last_item_count:
            return "未读取数据"

        parts = []
        for cat, count in self.last_item_count.items():
            parts.append(f"{cat}:{count}")

        total = sum(self.last_item_count.values())
        return f"{', '.join(parts)} (总计:{total})"

    def discovery(self):
        """发送MQTT发现消息"""
        category_counters = {
            'temp': 0,  # 温度
            'pwr': 0,  # 功率
            'fan': 0,  # 风扇
            'sys': 0,  # 系统信息
            'volt': 0,  # 电压
            'curr': 0,  # 电流
            'duty': 0,  # 占空比
        }

        aida64_data = self.get_aida64_data()
        if not aida64_data:
            self.core.log.error("Discovery失败：无法获取Aida64数据")
            return False

        success_count = 0
        failed_count = 0

        for category, items in aida64_data.items():
            if category not in category_counters:
                self.core.log.warning(f"未知的类别: {category}")
                continue

            for item in items:
                try:
                    name = item["label"]
                    entity_id = f"Aida64_{item['id']}"

                    # 发送MQTT发现信息
                    result = self.core.mqtt.send_mqtt_discovery(
                        device_class=category,
                        num=category_counters[category],
                        name=name,
                        entity_id=entity_id,
                        is_aida64=True
                    )

                    if result:
                        success_count += 1
                    else:
                        failed_count += 1

                    category_counters[category] += 1

                except KeyError as e:
                    self.core.log.error(f"数据格式错误: {e}, item: {item}")
                    failed_count += 1
                except Exception as e:
                    self.core.log.error(f"发送Discovery失败: {e}")
                    failed_count += 1

        total_entities = sum(category_counters.values())
        self.core.log.info(
            f"Aida64 Discovery完成: 成功{success_count}个, "
            f"失败{failed_count}个, 共{total_entities}个实体"
        )

        # 打印各类别数量
        for category, count in category_counters.items():
            if count > 0:
                self.core.log.debug(f"  {category}: {count}个")

        # 更新discovery时间
        self.last_discovery_time = time.time()

        return success_count > 0

    def update_state(self):
        """更新状态 - 发送整个JSON"""
        aida64_data = self.get_aida64_data()
        if not aida64_data:
            self.core.log.warning("状态更新失败：无法获取Aida64数据")
            return False

        try:
            data = json.dumps(aida64_data)
            result = self.core.mqtt.update_state_data(data, "Aida64", "sensor")

            if result:
                self.core.log.debug("Aida64状态更新成功")
            else:
                self.core.log.warning("Aida64状态更新失败")

            return result

        except Exception as e:
            self.core.log.error(f"状态更新异常: {e}")
            return False

    def save_updater(self, e):
        """保存更新间隔设置"""
        try:
            value = int(e.control.value)
            if value < 1:
                self.core.log.error("更新间隔必须大于0秒")
                e.control.error_text = "必须大于0秒"
                e.control.update()
                return

            self.core.set_plugin_config("Aida64", "aida64_updater", value)
            self.updater["timer"] = value

            self.core.log.info(f"Aida64更新间隔已设置为{value}秒")
            e.control.error_text = None

        except ValueError:
            self.core.log.error("更新间隔必须是数字")
            e.control.error_text = "请输入有效数字"
            e.control.update()
        except Exception as ex:
            self.core.log.error(f"保存设置失败: {ex}")

    def setting_page(self, e=None):
        """设置页面"""
        current_interval = self.core.get_plugin_config("Aida64", "aida64_updater", 5)
        auto_rediscovery_enabled = self.core.get_plugin_config("Aida64", "auto_rediscovery", False)

        # 状态文本
        status_text = ft.Text("", color=ft.Colors.GREEN, visible=False)

        # 保存设置
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

        # 输入框
        interval_field = ft.TextField(
            label="秒",
            value=str(current_interval),
            width=100,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_submit=save_setting,
            hint_text="1-3600"
        )

        # 自动重新discovery开关
        def toggle_auto_rediscovery(e):
            self.auto_rediscovery = e.control.value
            self.core.set_plugin_config("Aida64", "auto_rediscovery", self.auto_rediscovery)

            status_text.value = f"✓ 自动重新Discovery已{'启用' if self.auto_rediscovery else '禁用'}"
            status_text.color = ft.Colors.GREEN
            status_text.visible = True
            status_text.update()

            # 如果开启，立即记录当前数据项数量
            if self.auto_rediscovery and self.last_data:
                self.last_item_count = {}
                for category, items in self.last_data.items():
                    if isinstance(items, list):
                        self.last_item_count[category] = len(items)
                self.core.log.info(f"自动Discovery已启用，当前数据项: {self.get_item_count_summary()}")

        auto_rediscovery_switch = ft.Switch(
            label="自动重新Discovery",
            value=auto_rediscovery_enabled,
            on_change=toggle_auto_rediscovery,
            tooltip="当检测到数据项数量变化时自动触发Discovery"
        )

        # 测试读取
        def test_read_data(e):
            data = self.get_aida64_data()
            if data:
                e.control.text = "✓ 读取成功"
                e.control.bgcolor = ft.Colors.GREEN
                e.control.update()

                # 格式化JSON数据
                json_str = json.dumps(data, indent=2, ensure_ascii=False)

                # 统计数据
                stats_text = "数据统计:\n"
                for category, items in data.items():
                    if isinstance(items, list):
                        stats_text += f"  {category}: {len(items)} 项\n"

                # 创建显示JSON数据的对话框
                dlg = ft.AlertDialog(
                    title=ft.Text("Aida64 数据", weight=ft.FontWeight.BOLD),
                    content=ft.Container(
                        content=ft.Column(
                            [
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
                            ],
                        ),
                        width=650,
                        height=450,
                    ),
                    actions=[
                        ft.TextButton(
                            "复制",
                            on_click=lambda _: e.page.set_clipboard(json_str)
                        ),
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

        # 手动更新按钮
        def manual_update(e):
            result = self.update_state()
            if result:
                e.control.text = "✓ 更新成功"
                e.control.bgcolor = ft.Colors.GREEN
            else:
                e.control.text = "✗ 更新失败"
                e.control.bgcolor = ft.Colors.RED
            e.control.update()

        # 重新发现按钮
        def rediscover(e):
            result = self.discovery()
            if result:
                e.control.text = "✓ 发现完成"
                e.control.bgcolor = ft.Colors.GREEN
            else:
                e.control.text = "✗ 发现失败"
                e.control.bgcolor = ft.Colors.RED
            e.control.update()

        # 重置数据计数按钮
        def reset_count(e):
            self.last_item_count = {}
            self.last_discovery_time = 0
            status_text.value = "✓ 数据计数已重置"
            status_text.color = ft.Colors.GREEN
            status_text.visible = True
            status_text.update()
            e.control.text = "✓ 已重置"
            e.control.update()

        return ft.Column(
            [
                ft.Divider(),

                # 更新间隔设置
                ft.Row(
                    [
                        ft.Text("数据更新间隔:", width=120),
                        interval_field,
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),

                # 自动重新Discovery设置
                ft.Row(
                    [
                        auto_rediscovery_switch,
                        ft.Text(
                            "新增/删除数据项时自动重新Discovery",
                            size=12,
                            color=ft.Colors.GREY_700
                        ),
                    ],
                    spacing=10,
                ),

                # 状态提示
                status_text,

                ft.Divider(),

                # 测试和操作按钮
                ft.Row(
                    [
                        ft.ElevatedButton(
                            "测试读取",
                            icon=ft.Icons.CABLE,
                            on_click=test_read_data
                        ),
                        ft.ElevatedButton(
                            "手动更新",
                            icon=ft.Icons.REFRESH,
                            on_click=manual_update
                        ),
                    ],
                    spacing=10,
                ),
                ft.Row(
                    [
                        ft.ElevatedButton(
                            "重新发现",
                            icon=ft.Icons.SEARCH,
                            on_click=rediscover
                        ),
                        ft.ElevatedButton(
                            "重置计数",
                            icon=ft.Icons.RESTART_ALT,
                            on_click=reset_count,
                            tooltip="重置数据项计数器"
                        ),
                    ],
                    spacing=10,
                ),
                # 状态显示
                ft.Divider(),
                ft.Text("当前状态:", weight=ft.FontWeight.BOLD),
                ft.Text(f"更新间隔: {current_interval}秒"),
                ft.Text(f"自动同步: {'启用' if auto_rediscovery_enabled else '禁用'}"),
                ft.Text(f"最小Discovery间隔: {self.min_discovery_interval}秒"),
                ft.Text(f"上次数据: {'有' if self.last_data else '无'}"),
                ft.Text(f"数据项统计: {self.get_item_count_summary()}"),

                # 说明信息
                ft.Divider(),
                ft.Text("使用说明:", weight=ft.FontWeight.BOLD, size=14),
                ft.Text(
                    "• 自动同步：当启用后，系统会在每次读取数据时检查数据项数量的变化\n"
                    "• 如果数据项数量发生变化（如新增传感器），会自动触发重新Discovery\n"
                    "• 如果开机出现数据项加载异常可尝试开启\n"
                    "• 为避免频繁Discovery，设置了30秒的最小间隔\n"
                    "• 重置计数：清空数据项计数器，用于强制下次检测时触发Discovery",
                    size=12,
                    color=ft.Colors.GREY_700,
                ),
            ],
            spacing=15,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.START,
            scroll=ft.ScrollMode.ADAPTIVE,
        )