"""
插件模板
这是一个标准的插件示例，展示了所有可用的方法和配置
"""
import flet as ft

class Example:
    """插件模板类(需要确保类名和文件夹名一致，只会加载同名py文件)"""

    def __init__(self, core):
        """
        插件初始化
        :param core: Core实例，提供日志、配置、MQTT等功能
        """
        self.core = core
        self.log = core.log

        # 从插件配置中读取设置
        self.interval = core.get_plugin_config('PluginTemplate', 'interval', 60)
        self.enabled = core.get_plugin_config('PluginTemplate', 'custom_enabled', True)

        # 插件内部状态
        self.status = "未初始化"
        self.data = {}

    def initialize(self):
        """
        插件初始化方法（可选）
        在插件实例创建后自动调用
        """
        self.log.info("PluginTemplate 初始化完成")
        self.status = "已初始化"

    # ===== MQTT 实体配置 =====

    @property
    def config(self):
        """
        定义要在Home Assistant中创建的实体，会在程序启动时候自动添加到HA
        """
        return [
            {
                "entity_type": "sensor",
                "name": "示例传感器",
                "entity_id": "example_sensor",
                "icon": "mdi:information"
            },
            {
                "entity_type": "switch",
                "name": "示例开关",
                "entity_id": "example_switch",
                "icon": "mdi:toggle-switch"
            },
            {
                "entity_type": "button",
                "name": "示例按钮",
                "entity_id": "example_button",
                "icon": "mdi:gesture-tap-button"
            }
        ]

    def discovery(self):
        """
        自定义实体发现方法（可选）
        如果需要更复杂的实体配置，可以在这里手动发送MQTT发现消息
        需要确保前缀和插件名一致，如Example_custom_sensor中的Example和文件夹，类名一致
        """
        # 示例：发送自定义实体
        # self.core.mqtt.send_mqtt_discovery(
        #     entity_type="sensor",
        #     name="自定义传感器",
        #     entity_id="Example_custom_sensor",
        #     icon="mdi:gauge"
        # )
        pass

    # ===== 定时更新配置 =====

    @property
    def updater(self):
        """
        定义定时更新配置，添加定时器后会调用update_state自动更新数据
        """
        return {
            "timer": self.interval  # 更新间隔（秒）
        }

    def update_state(self):
        """
        定时更新方法
        按照updater中配置的间隔自动调用
        用于更新传感器状态、采集数据等
        """
        try:
            # 示例：采集数据
            self.data['timestamp'] = self.core.timer.get_current_time()
            self.data['value'] = 42

            # 发送状态到MQTT
            self.core.mqtt.publish_state(
                entity_id="PluginTemplate_example_sensor",
                state=self.data['value']
            )

            self.log.debug(f"PluginTemplate 状态已更新: {self.data}")

        except Exception as e:
            self.log.error(f"PluginTemplate 更新状态失败: {e}")

    # ===== 生命周期方法 =====

    def start(self):
        """
        插件启动方法（可选）
        在core.start()时调用
        """
        self.log.info("PluginTemplate 已启动")
        self.status = "运行中"

    def stop(self):
        """
        插件停止方法（可选）
        在core.stop()时调用
        """
        self.log.info("PluginTemplate 已停止")
        self.status = "已停止"

    def on_unload(self):
        """
        插件卸载方法（可选）
        在禁用或重载插件时调用，用于清理资源
        """
        self.log.info("PluginTemplate 正在卸载")
        # 清理资源、关闭连接等
        self.data.clear()

    # ===== 状态查询 =====

    def get_status(self):
        """
        获取插件状态（可选）
        返回插件当前状态信息
        """
        return {
            "status": self.status,
            "data": self.data,
            "enabled": self.enabled
        }

    # ===== 自定义方法 =====

    def custom_action(self, param):
        """
        自定义方法示例
        可以通过core实例调用：core.PluginTemplate.custom_action("test")
        """
        self.log.info(f"执行自定义操作: {param}")
        return f"处理完成: {param}"

    # ===== MQTT消息回调 =====

    def handle_mqtt_message(self, topic, payload):
        """
        处理MQTT消息（可选）
        如果需要响应MQTT消息，可以实现此方法
        需要在MQTT模块中注册订阅
        """
        self.log.debug(f"收到MQTT消息 - Topic: {topic}, Payload: {payload}")

        # 示例：处理开关命令
        if "example_switch" in topic:
            if payload == "ON":
                self.log.info("开关已打开")
                # 执行开启操作
            elif payload == "OFF":
                self.log.info("开关已关闭")
                # 执行关闭操作

        # 示例：处理按钮点击
        elif "example_button" in topic:
            self.log.info("按钮被点击")
            self.custom_action("button_pressed")

    # ===== 插件设置页面(可选) =====

    def setting_page(self, e):
        """设置页面"""

        return ft.Column(
                [
                    ft.Text("将你的flet组件放在这里", size=20),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )

    # ===== 其他 =====

    def test(self):
        self.core.show_toast('标题', '消息内容') # 显示Toast通知



