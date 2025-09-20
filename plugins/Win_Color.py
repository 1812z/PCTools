import time

PLUGIN_NAME = "深色模式开关"
PLUGIN_VERSION = "1.0"
PLUGIN_AUTHOR = "1812z"
PLUGIN_DESCRIPTION = "控制系统的'应用深色模式'与'系统深色模式'"

class Win_Color:
    def __init__(self,core):
        self.core = core
        self.APP_enabled = False
        self.Sys_enabled = False
        self.updater ={
            "timer": 600
        }
        self.config = [
            {
                "name": "应用深色模式",
                "entity_type": "switch",
                "entity_id": "APP_Dark_Mode",
                "icon": "mdi:theme-light-dark"
            },
            {
                "name": "系统深色模式",
                "entity_type": "switch",
                "entity_id": "SYS_Dark_Mode",
                "icon": "mdi:theme-light-dark"
            }

        ]

    def set_dark_mode(self,APP_enabled, Sys_enabled):
        """
        启用或禁用 Windows 深色模式
        :param
        APP_enabled: True 为深色模式，False 为浅色模式
        Sys_enabled: True 为深色模式，False 为浅色模式
        """
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        try:
            # 使用self.core.reg类写入注册表值
            self.core.reg.write_value(
                "HKEY_CURRENT_USER",
                key_path,
                "AppsUseLightTheme",
                0 if APP_enabled else 1,
                "REG_DWORD"
            )

            self.core.reg.write_value(
                "HKEY_CURRENT_USER",
                key_path,
                "SystemUsesLightTheme",
                0 if Sys_enabled else 1,
                "REG_DWORD"
            )

            # 发送系统通知（这部分与注册表无关，保留原样）
            self.core.reg.notify_system("ImmersiveColorSet")
            self.core.log.info(f"Windows颜色设置成功,应用深色:{APP_enabled} 系统深色:{Sys_enabled}")
            time.sleep(0.3)
            self.update_state()
        except Exception as e:
            self.core.log.error(f"设置失败: {e}")


    def get_status(self):
        """
        获取当前 Windows 颜色模式状态
        :return: dict {
            "apps_light_theme": bool,  # True=浅色模式，False=深色模式
            "system_light_theme": bool,
            "summary": str  # 综合描述
        }
        """
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        try:
            # 使用self.core.reg类读取注册表值
            apps_light = self.core.reg.read_value(
                "HKEY_CURRENT_USER",
                key_path,
                "AppsUseLightTheme",
                1  # 默认值（浅色模式）
            )

            system_light = self.core.reg.read_value(
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
                "status": [apps_light,system_light],
                "info": summary
            }
        except Exception as e:
            return {
                "level": "error",
                "info": "无法读取主题状态:" + str(e)
            }

    def update_state(self):
        status = self.get_status()
        topic = f"Win_Color_APP_Dark_Mode"
        if status["status"][0]:
            self.APP_enabled = False
            state = "OFF"
        else:
            self.APP_enabled = True
            state = "ON"
        self.core.mqtt.update_state_data(state, topic, "switch")

        topic = f"Win_Color_SYS_Dark_Mode"
        if status["status"][1]:
            self.Sys_enabled = False
            state = "OFF"
        else:
            self.Sys_enabled = True
            state = "ON"
        self.core.mqtt.update_state_data(state, topic, "switch")

    def handle_mqtt(self, entity, payload):
        if payload == "ON":
            comm = True
        else:
            comm = False
        if entity == "APP_Dark_Mode":
            self.APP_enabled = comm
            return self.set_dark_mode(APP_enabled=self.APP_enabled, Sys_enabled=self.Sys_enabled )
        elif entity == "SYS_Dark_Mode":
            self.Sys_enabled = comm
            return self.set_dark_mode(APP_enabled=self.APP_enabled, Sys_enabled=self.Sys_enabled )
        return None
