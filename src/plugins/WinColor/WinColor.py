"""
Windows颜色模式管理插件
支持应用和系统深色模式切换
"""
import time
from ha_mqtt_discoverable.sensors import Switch, SwitchInfo
from ha_mqtt_discoverable import Settings
from paho.mqtt.client import Client as MQTTClient


class WinColor:
    def __init__(self, core):
        """
        初始化Windows颜色模式管理
        :param core: PCTools Core 实例
        """
        self.core = core
        self.log = core.log

        # MQTT 实体
        self.app_dark_mode_switch = None
        self.sys_dark_mode_switch = None

        # 状态记录
        self.APP_enabled = False
        self.Sys_enabled = False

        # 配置信息（保留原有接口兼容性）
        self.updater = {
            "timer": 600
        }

    def setup_entities(self):
        """设置 MQTT 实体"""
        try:
            mqtt_settings = self.core.mqtt.get_mqtt_settings()
            device_info = self.core.mqtt.get_device_info()

            # 创建应用深色模式开关
            app_dark_info = SwitchInfo(
                name="app_dark_mode",
                unique_id=f"app_dark_mode",
                object_id=f"app_dark_mode",
                device=device_info,
                icon="mdi:theme-light-dark",
                display_name="应用深色模式"
            )

            app_dark_settings = Settings(
                mqtt=mqtt_settings,
                entity=app_dark_info
            )

            self.app_dark_mode_switch = Switch(
                app_dark_settings,
                command_callback=self.handle_app_dark_command
            )

            # 创建系统深色模式开关
            sys_dark_info = SwitchInfo(
                name="sys_dark_mode",
                unique_id=f"sys_dark_mode",
                object_id=f"sys_dark_mode",
                device=device_info,
                icon="mdi:theme-light-dark",
                display_name="系统深色模式"
            )

            sys_dark_settings = Settings(
                mqtt=mqtt_settings,
                entity=sys_dark_info
            )

            self.sys_dark_mode_switch = Switch(
                sys_dark_settings,
                command_callback=self.handle_sys_dark_command
            )

            self.update_state()
            self.log.info("Windows颜色模式 MQTT 实体创建成功")

        except Exception as e:
            self.log.error(f"创建 MQTT 实体失败: {e}")

    def set_dark_mode(self, APP_enabled, Sys_enabled):
        """
        启用或禁用 Windows 深色模式
        :param APP_enabled: True 为深色模式，False 为浅色模式
        :param Sys_enabled: True 为深色模式，False 为浅色模式
        """
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        try:
            # 使用self.core.WinReg类写入注册表值
            self.core.WinReg.write_value(
                "HKEY_CURRENT_USER",
                key_path,
                "AppsUseLightTheme",
                0 if APP_enabled else 1,
                "REG_DWORD"
            )

            self.core.WinReg.write_value(
                "HKEY_CURRENT_USER",
                key_path,
                "SystemUsesLightTheme",
                0 if Sys_enabled else 1,
                "REG_DWORD"
            )

            # 发送系统通知
            self.core.WinReg.notify_system("ImmersiveColorSet")
            self.log.info(f"Windows颜色设置成功,应用深色:{APP_enabled} 系统深色:{Sys_enabled}")
            time.sleep(0.3)

            # 更新状态到MQTT
            self.update_state()

        except Exception as e:
            self.log.error(f"设置失败: {e}")

    def get_status(self):
        """
        获取当前 Windows 颜色模式状态
        :return: dict {
            "apps_light_theme": bool,
            "system_light_theme": bool,
            "summary": str
        }
        """
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        try:
            # 使用self.core.WinReg类读取注册表值
            apps_light = self.core.WinReg.read_value(
                "HKEY_CURRENT_USER",
                key_path,
                "AppsUseLightTheme",
                1  # 默认值（浅色模式）
            )

            system_light = self.core.WinReg.read_value(
                "HKEY_CURRENT_USER",
                key_path,
                "SystemUsesLightTheme",
                1  # 默认值（浅色模式）
            )

            # 转换为布尔值（0=深色，1=浅色）
            apps_light = bool(apps_light)
            system_light = bool(system_light)

            # 综合描述
            summary = (
                "当前模式：\n"
                f"- 应用程序主题: {'浅色' if apps_light else '深色'}\n"
                f"- 系统主题: {'浅色' if system_light else '深色'}"
            )

            return {
                "level": "info",
                "status": [apps_light, system_light],
                "info": summary
            }
        except Exception as e:
            return {
                "level": "error",
                "info": "无法读取主题状态:" + str(e)
            }

    def update_state(self):
        """
        更新所有开关状态到MQTT
        """
        try:
            status = self.get_status()

            # 更新应用深色模式状态
            # 注意：status[0] 是 apps_light (True=浅色, False=深色)
            # 所以深色模式 = NOT apps_light
            if status["status"][0]:  # apps_light = True (浅色模式)
                self.APP_enabled = False
                state = "OFF"
            else:  # apps_light = False (深色模式)
                self.APP_enabled = True
                state = "ON"

            if self.app_dark_mode_switch:
                if state == "ON":
                    self.app_dark_mode_switch.on()
                else:
                    self.app_dark_mode_switch.off()
                self.log.debug(f"应用深色模式状态更新: {state}")

            # 更新系统深色模式状态
            if status["status"][1]:  # system_light = True (浅色模式)
                self.Sys_enabled = False
                state = "OFF"
            else:  # system_light = False (深色模式)
                self.Sys_enabled = True
                state = "ON"

            if self.sys_dark_mode_switch:
                if state == "ON":
                    self.sys_dark_mode_switch.on()
                else:
                    self.sys_dark_mode_switch.off()
                self.log.debug(f"系统深色模式状态更新: {state}")

        except Exception as e:
            self.log.error(f"更新状态失败: {e}")

    def handle_app_dark_command(self, client: MQTTClient, user_data, message):
        """
        处理应用深色模式命令（由 ha-mqtt-discoverable 回调）
        :param client: MQTT 客户端
        :param user_data: 用户数据
        :param message: MQTT 消息
        """
        try:
            payload = message.payload.decode()
            self.log.info(f"收到应用深色模式命令: {payload}")

            if payload == "ON":
                self.APP_enabled = True
            else:
                self.APP_enabled = False

            self.set_dark_mode(APP_enabled=self.APP_enabled, Sys_enabled=self.Sys_enabled)

        except Exception as e:
            self.log.error(f"处理应用深色模式命令失败: {e}")

    def handle_sys_dark_command(self, client: MQTTClient, user_data, message):
        """
        处理系统深色模式命令（由 ha-mqtt-discoverable 回调）
        :param client: MQTT 客户端
        :param user_data: 用户数据
        :param message: MQTT 消息
        """
        try:
            payload = message.payload.decode()
            self.log.info(f"收到系统深色模式命令: {payload}")

            if payload == "ON":
                self.Sys_enabled = True
            else:
                self.Sys_enabled = False

            self.set_dark_mode(APP_enabled=self.APP_enabled, Sys_enabled=self.Sys_enabled)

        except Exception as e:
            self.log.error(f"处理系统深色模式命令失败: {e}")

    def handle_mqtt(self, entity, payload):
        """
        保留原有接口兼容性（可选）
        新代码应使用回调函数处理命令
        """
        if payload == "ON":
            comm = True
        else:
            comm = False

        if entity == "APP_Dark_Mode":
            self.APP_enabled = comm
            return self.set_dark_mode(APP_enabled=self.APP_enabled, Sys_enabled=self.Sys_enabled)
        elif entity == "SYS_Dark_Mode":
            self.Sys_enabled = comm
            return self.set_dark_mode(APP_enabled=self.APP_enabled, Sys_enabled=self.Sys_enabled)

        return None

    def on_unload(self):
        """
        插件卸载时清理资源
        """
        try:
            # 清空引用
            self.app_dark_mode_switch = None
            self.sys_dark_mode_switch = None
            self.log.info("Windows颜色模式插件已卸载")

        except Exception as e:
            self.log.error(f"卸载插件失败: {e}")