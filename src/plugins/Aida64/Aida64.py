import json
import flet as ft
import python_aida64

class Aida64:
    def __init__(self, core):
        self.core = core
        self.updater = {
            "timer": self.core.get_plugin_config("Aida64", "aida64_updater", 5),
        }
        self.last_data = None  # 缓存上次的数据

    def get_aida64_data(self):
        """获取AIDA64数据，带异常处理"""
        try:
            aida64_data = python_aida64.getData()
            if not aida64_data:
                self.core.log.error("Aida64数据读取失败：返回空数据")
                return None

            self.last_data = aida64_data  # 缓存数据
            return aida64_data

        except Exception as e:
            self.core.log.error(f"Aida64数据读取异常: {e}")
            return None

    def discovery(self):
        """发送MQTT发现消息"""
        category_counters = {
            'temp': 0,  # 温度
            'pwr': 0,   # 功率
            'fan': 0,   # 风扇
            'sys': 0,   # 系统信息
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

        # 测试读取
        def test_read_data(e):
            data = self.get_aida64_data()
            if data:
                e.control.text = "✓ 读取成功"
                e.control.bgcolor = ft.Colors.GREEN
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

        return ft.Column(
            [
                ft.Text("Aida64 设置", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(),

                # 更新间隔设置
                ft.Row(
                    [
                        ft.Text("数据更新间隔:", width=120),
                        interval_field,
                    ],
                    alignment=ft.MainAxisAlignment.START,
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
                        ft.ElevatedButton(
                            "重新发现",
                            icon=ft.Icons.SEARCH,
                            on_click=rediscover
                        ),
                    ],
                    spacing=10,
                ),

                # 状态显示
                ft.Divider(),
                ft.Text("当前状态:", weight=ft.FontWeight.BOLD),
                ft.Text(f"更新间隔: {current_interval}秒"),
                ft.Text(f"上次数据: {'有' if self.last_data else '无'}"),
            ],
            spacing=15,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )