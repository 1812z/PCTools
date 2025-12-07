"""
蓝牙管理插件
"""
from winsdk.windows.devices import radios
from ha_mqtt_discoverable.sensors import Switch, SwitchInfo
from ha_mqtt_discoverable import Settings
from paho.mqtt.client import Client as MQTTClient
import asyncio


class Bluetooth:
    def __init__(self, core):
        """
        初始化蓝牙插件
        :param core: PCTools Core 实例
        """
        self.core = core
        self.log = core.log

        # MQTT 实体
        self.bluetooth_switch = None

        # 蓝牙设备引用
        self.bluetooth_radio = None

        # 事件监听令牌（用于取消监听）
        self.state_changed_token = None

        # 启动蓝牙状态监听
        self.start_bluetooth_listener()

    def setup_entities(self):
        """设置 MQTT 实体"""
        try:
            mqtt_settings = self.core.mqtt.get_mqtt_settings()
            device_info = self.core.mqtt.get_device_info()

            switch_info = SwitchInfo(
                name="bluetooth",
                unique_id=f"{self.core.mqtt.device_name}_bluetooth_power",
                object_id=f"{self.core.mqtt.device_name}_bluetooth_power",
                device=device_info,
                icon="mdi:bluetooth",
                display_name="蓝牙"
            )

            switch_settings = Settings(
                mqtt=mqtt_settings,
                entity=switch_info
            )

            self.bluetooth_switch = Switch(
                switch_settings,
                command_callback=self.handle_switch_command
            )
            self.bluetooth_switch.update_state(self.bluetooth_radio.state == radios.RadioState.ON)

            self.log.info("蓝牙 MQTT 实体创建成功")

        except Exception as e:
            self.log.error(f"创建蓝牙 MQTT 实体失败: {e}")

    def start_bluetooth_listener(self):
        """开始监听蓝牙状态变化"""
        try:
            async def get_bluetooth_and_listen():
                """获取蓝牙设备并注册监听"""
                all_radios = await radios.Radio.get_radios_async()

                for this_radio in all_radios:
                    if this_radio.kind == radios.RadioKind.BLUETOOTH:
                        self.bluetooth_radio = this_radio

                        # 注册状态变化监听
                        self.state_changed_token = self.bluetooth_radio.add_state_changed(
                            self.on_bluetooth_state_changed
                        )

                        # 立即同步当前状态
                        self.sync_current_state()

                        self.log.info("蓝牙状态监听已启动")
                        return

                self.log.error("找不到蓝牙设备")

            # 在新的事件循环中执行
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(get_bluetooth_and_listen())
            loop.close()

        except Exception as e:
            self.log.error(f"启动蓝牙监听失败: {e}")

    def sync_current_state(self):
        """同步当前蓝牙状态到 Home Assistant"""
        if self.bluetooth_radio and self.bluetooth_switch:
            if self.bluetooth_radio.state == radios.RadioState.ON:
                self.bluetooth_switch.on()
                self.log.info("蓝牙初始状态: ON")
            else:
                self.bluetooth_switch.off()
                self.log.info("蓝牙初始状态: OFF")

    def on_bluetooth_state_changed(self, radio, event_args):
        """
        蓝牙状态变化回调
        :param radio: 蓝牙设备对象
        :param event_args: 事件参数
        """
        try:
            if self.bluetooth_switch:
                if radio.state == radios.RadioState.ON:
                    self.bluetooth_switch.on()
                    self.log.info("蓝牙状态变化 -> ON")
                else:
                    self.bluetooth_switch.off()
                    self.log.info("蓝牙状态变化 -> OFF")
        except Exception as e:
            self.log.error(f"处理蓝牙状态变化失败: {e}")

    def handle_switch_command(self, client: MQTTClient, user_data, message):
        """
        处理开关命令（由 ha-mqtt-discoverable 回调）
        :param client: MQTT 客户端
        :param user_data: 用户数据
        :param message: MQTT 消息
        """
        try:
            payload = message.payload.decode()
            self.log.info(f"收到蓝牙开关命令: {payload}")

            # 创建新的事件循环来执行异步操作
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            if payload == "ON":
                result = loop.run_until_complete(self.bluetooth_power(True))
                self.log.info(f"蓝牙设备已开启: {result}")
            elif payload == "OFF":
                result = loop.run_until_complete(self.bluetooth_power(False))
                self.log.info(f"蓝牙设备已关闭: {result}")

            loop.close()

        except Exception as e:
            self.log.error(f"处理蓝牙开关命令失败: {e}")

    async def bluetooth_power(self, turn_on: bool):
        """
        蓝牙电源管理
        :param turn_on: True 开启，False 关闭
        :return: 操作结果
        """
        try:
            if self.bluetooth_radio:
                # 使用已有的蓝牙设备引用
                if turn_on:
                    result = await self.bluetooth_radio.set_state_async(radios.RadioState.ON)
                    self.log.debug("蓝牙设置为 ON")
                    return result
                else:
                    result = await self.bluetooth_radio.set_state_async(radios.RadioState.OFF)
                    self.log.debug("蓝牙设置为 OFF")
                    return result
            else:
                # 如果没有引用，重新获取
                all_radios = await radios.Radio.get_radios_async()
                for this_radio in all_radios:
                    if this_radio.kind == radios.RadioKind.BLUETOOTH:
                        if turn_on:
                            return await this_radio.set_state_async(radios.RadioState.ON)
                        else:
                            return await this_radio.set_state_async(radios.RadioState.OFF)

            self.log.error("找不到蓝牙设备")
            return None

        except Exception as e:
            self.log.error(f"蓝牙电源控制失败: {e}")
            return None

    def on_unload(self):
        """
        插件卸载时清理资源
        """
        try:
            # 取消蓝牙状态监听
            if self.bluetooth_radio and self.state_changed_token:
                self.bluetooth_radio.remove_state_changed(self.state_changed_token)
                self.log.info("蓝牙状态监听已取消")

            # 清空引用
            self.bluetooth_radio = None
            self.state_changed_token = None
            self.bluetooth_switch = None

            self.log.info("蓝牙插件已卸载")

        except Exception as e:
            self.log.error(f"卸载蓝牙插件失败: {e}")
