"""
插件模板
这是一个标准的插件示例，展示了所有可用的方法和配置
适配新版 MQTT 架构 (ha-mqtt-discoverable)
"""
import flet as ft
from ha_mqtt_discoverable import Settings
from ha_mqtt_discoverable.sensors import Sensor, SensorInfo, Switch, SwitchInfo, Button, ButtonInfo

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
        self.interval = core.get_plugin_config('Example', 'interval', 60)
        self.enabled = core.get_plugin_config('Example', 'custom_enabled', True)

        # 插件内部状态
        self.status = "未初始化"
        self.data = {}

        # MQTT实体存储
        self.sensor = None
        self.switch = None
        self.button = None

        # 设置MQTT实体
        self.setup_entities()

    def initialize(self):
        """
        插件初始化方法（可选）
        在插件实例创建后自动调用
        """
        self.log.info("Example 初始化完成")
        self.status = "已初始化"

    # ===== MQTT 实体配置 (新架构) =====

    def setup_entities(self):
        """
        设置MQTT实体 (使用 ha-mqtt-discoverable)
        这是新架构的标准方法名，替代旧的 config 和 discovery
        """
        try:
            # 获取MQTT配置和设备信息
            mqtt_settings = self.core.mqtt.get_mqtt_settings()
            device_info = self.core.mqtt.get_device_info(
                plugin_name="Example",
                model="PCTools Example Plugin"
            )

            # 1. 创建传感器实体
            sensor_info = SensorInfo(
                name="example_sensor",
                unique_id=f"{self.core.mqtt.device_name}_Example_sensor",
                device=device_info,
                icon="mdi:information"
            )
            sensor_info.display_name = "示例传感器"

            settings = Settings(mqtt=mqtt_settings, entity=sensor_info)
            self.sensor = Sensor(settings)
            self.sensor.set_state(0)  # 初始化状态

            # 2. 创建开关实体
            switch_info = SwitchInfo(
                name="example_switch",
                unique_id=f"{self.core.mqtt.device_name}_Example_switch",
                device=device_info,
                icon="mdi:toggle-switch"
            )
            switch_info.display_name = "示例开关"

            settings = Settings(mqtt=mqtt_settings, entity=switch_info)
            self.switch = Switch(settings, command_callback=self.handle_switch)
            self.switch.off()  # 初始化为关闭状态

            # 3. 创建按钮实体
            button_info = ButtonInfo(
                name="example_button",
                unique_id=f"{self.core.mqtt.device_name}_Example_button",
                device=device_info,
                icon="mdi:gesture-tap-button"
            )
            button_info.display_name = "示例按钮"

            settings = Settings(mqtt=mqtt_settings, entity=button_info)
            self.button = Button(settings, command_callback=self.handle_button)

            self.log.info("Example MQTT实体创建成功")

        except Exception as e:
            self.log.error(f"Example MQTT设置失败: {e}")

    def handle_switch(self, client, user_data, message):
        """
        处理开关命令回调
        :param client: MQTT客户端
        :param user_data: 用户数据
        :param message: MQTT消息
        """
        try:
            payload = message.payload.decode()
            self.log.info(f"收到开关命令: {payload}")

            if payload == "ON":
                self.log.info("示例开关已打开")
                # 在这里执行开启操作
                # 例如：启动某个服务、打开某个功能等
            elif payload == "OFF":
                self.log.info("示例开关已关闭")
                # 在这里执行关闭操作

        except Exception as e:
            self.log.error(f"处理开关命令失败: {e}")

    def handle_button(self, client, user_data, message):
        """
        处理按钮点击回调
        :param client: MQTT客户端
        :param user_data: 用户数据
        :param message: MQTT消息
        """
        try:
            self.log.info("示例按钮被点击")
            # 在这里执行按钮点击的操作
            self.custom_action("button_pressed")

            # 可以显示通知
            self.core.show_toast("Example", "按钮被点击了！")

        except Exception as e:
            self.log.error(f"处理按钮点击失败: {e}")

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

            # 使用新架构更新传感器状态
            if self.sensor:
                self.sensor.set_state(self.data['value'])

            self.log.debug(f"Example 状态已更新: {self.data}")

        except Exception as e:
            self.log.error(f"Example 更新状态失败: {e}")

    # ===== 生命周期方法 =====

    def start(self):
        """
        插件启动方法（可选）
        在core.start()时调用
        """
        self.log.info("Example 已启动")
        self.status = "运行中"

    def stop(self):
        """
        插件停止方法（可选）
        在core.stop()时调用
        """
        self.log.info("Example 已停止")
        self.status = "已停止"

    def on_unload(self):
        """
        插件卸载方法（可选）
        在禁用或重载插件时调用，用于清理资源
        """
        self.log.info("Example 正在卸载")
        # 清理资源、关闭连接等
        self.data.clear()
        # ha-mqtt-discoverable 会自动处理MQTT连接清理

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
        可以通过core实例调用：core.Example.custom_action("test")
        """
        self.log.info(f"执行自定义操作: {param}")
        return f"处理完成: {param}"

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



