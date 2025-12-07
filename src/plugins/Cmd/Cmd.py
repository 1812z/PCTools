"""
CMD和PowerShell命令执行插件
"""
import subprocess
from ha_mqtt_discoverable.sensors import Text, TextInfo
from ha_mqtt_discoverable import Settings
from paho.mqtt.client import Client as MQTTClient


class Cmd:
    def __init__(self, core):
        """
        初始化 Cmd 插件
        :param core: PCTools Core 实例
        """
        self.core = core
        self.log = core.log

        # MQTT 实体
        self.cmd_text = None
        self.powershell_text = None

    def setup_entities(self):
        """设置 MQTT 实体"""
        try:
            mqtt_settings = self.core.mqtt.get_mqtt_settings()
            device_info = self.core.mqtt.get_device_info(
                plugin_name="Cmd",
                model="PCTools Command"
            )

            # 创建 CMD 文本实体
            cmd_info = TextInfo(
                name="cmd",
                unique_id=f"{self.core.mqtt.device_name}_cmd",
                object_id=f"{self.core.mqtt.device_name}_cmd",
                device=device_info,
                icon="mdi:console",
                display_name="CMD命令"
            )

            cmd_settings = Settings(
                mqtt=mqtt_settings,
                entity=cmd_info
            )

            self.cmd_text = Text(
                cmd_settings,
                command_callback=self.handle_cmd_command
            )
            self.cmd_text.set_text("输入自定义CMD命令")

            # 创建 PowerShell 文本实体
            ps_info = TextInfo(
                name="powershell",
                unique_id=f"{self.core.mqtt.device_name}_powershell",
                object_id=f"{self.core.mqtt.device_name}_powershell",
                device=device_info,
                icon="mdi:powershell",
                display_name="PowerShell命令"
            )

            ps_settings = Settings(
                mqtt=mqtt_settings,
                entity=ps_info
            )

            self.powershell_text = Text(
                ps_settings,
                command_callback=self.handle_powershell_command
            )
            self.powershell_text.set_text("输入自定义PowerShell命令")
            self.log.info("Cmd MQTT 实体创建成功")

        except Exception as e:
            self.log.error(f"创建 Cmd MQTT 实体失败: {e}")

    def handle_cmd_command(self, client: MQTTClient, user_data, message):
        """
        处理 CMD 命令（由 ha-mqtt-discoverable 回调）
        :param client: MQTT 客户端
        :param user_data: 用户数据
        :param message: MQTT 消息
        """
        try:
            command = message.payload.decode()
            self.log.info(f"收到 CMD 命令: {command}")
            self.cmd_text.set_text(command)
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30  # 添加超时保护
            )

            if result.returncode == 0:
                self.log.info(f"CMD命令执行成功: {command}")
                if result.stdout:
                    self.log.info(f"输出: {result.stdout.strip()}")
            else:
                self.log.warning(f"CMD命令执行失败 (返回码: {result.returncode}): {command}")
                if result.stderr:
                    self.log.warning(f"错误: {result.stderr.strip()}")

        except subprocess.TimeoutExpired:
            self.log.error(f"CMD命令执行超时: {command}")
        except Exception as e:
            self.log.error(f"执行 CMD 命令失败: {e}")

    def handle_powershell_command(self, client: MQTTClient, user_data, message):
        """
        处理 PowerShell 命令（由 ha-mqtt-discoverable 回调）
        :param client: MQTT 客户端
        :param user_data: 用户数据
        :param message: MQTT 消息
        """
        try:
            command = message.payload.decode()
            self.log.info(f"收到 PowerShell 命令: {command}")
            self.powershell_text.set_text(command)
            result = subprocess.run(
                ["powershell", "-Command", command],
                capture_output=True,
                text=True,
                timeout=30  # 添加超时保护
            )

            if result.returncode == 0:
                self.log.info(f"PowerShell命令执行成功: {command}")
                if result.stdout:
                    self.log.info(f"输出: {result.stdout.strip()}")
            else:
                self.log.warning(f"PowerShell命令执行失败 (返回码: {result.returncode}): {command}")
                if result.stderr:
                    self.log.warning(f"错误: {result.stderr.strip()}")

        except subprocess.TimeoutExpired:
            self.log.error(f"PowerShell命令执行超时: {command}")
        except Exception as e:
            self.log.error(f"执行 PowerShell 命令失败: {e}")