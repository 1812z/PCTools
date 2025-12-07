"""
TwinkleTray 显示器亮度控制插件
"""
import ctypes
import json
import subprocess
import re
import os
import time
import keyboard
import flet as ft
from ha_mqtt_discoverable.sensors import Light, LightInfo, Text, TextInfo
from ha_mqtt_discoverable import Settings
from paho.mqtt.client import Client as MQTTClient


def _remove_ansi_escape(text):
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    return ansi_escape.sub('', text)


def extract_monitors_info(info_str):
    # 先清除 ANSI 转义码
    clean_str = _remove_ansi_escape(info_str)
    # 按空行分割为多个块
    blocks = re.split(r'\n\s*\n', clean_str.strip())
    monitors = {}

    for block in blocks:
        # 提取 MonitorNum
        monitor_num_match = re.search(r'MonitorNum:\s*(\d+)', block)
        if monitor_num_match:
            monitor_num = int(monitor_num_match.group(1))
        else:
            continue  # 如果没有 MonitorNum 行，则跳过该块

        # 提取 MonitorID、Name 和 Brightness
        monitor_id_match = re.search(r'MonitorID:\s*(.+)', block)
        name_match = re.search(r'Name:\s*(.+)', block)
        brightness_match = re.search(r'Brightness:\s*(\d+)', block)

        monitors[monitor_num] = {
            "MonitorID": monitor_id_match.group(1).strip() if monitor_id_match else None,
            "Name": name_match.group(1).strip() if name_match else None,
            "Brightness": int(brightness_match.group(1)) if brightness_match else None
        }
    return monitors


class TwinkleTray:
    def __init__(self, core):
        """
        初始化 TwinkleTray 插件
        :param core: PCTools Core 实例
        """
        self.core = core
        self.log = core.log
        self.path = os.path.expanduser("~") + "\\AppData\\Local\\Programs\\twinkle-tray\\Twinkle Tray.exe"
        self.updater = {"timer": 5}

        # MQTT 实体存储
        self.monitor_lights = {}  # {monitor_num: Light实例}
        self.ddcci_text = None

        self.read_monitor_power_type = self.core.get_plugin_config("TwinkleTray", "read_monitor_power_type", 2)

    def setup_entities(self):
        """设置 MQTT 实体"""
        try:
            mqtt_settings = self.core.mqtt.get_mqtt_settings()
            device_info = self.core.mqtt.get_device_info(
                plugin_name="TwinkleTray",
                model="PCTools TwinkleTray"
            )

            # 获取所有显示器信息
            monitors = self.get_monitors_state()

            if not monitors:
                self.log.warning("未找到兼容的显示器")
                return

            # 为每个显示器创建 Light 实体
            for monitor_num, info in monitors.items():
                monitor_name = info.get("Name", f"Monitor {monitor_num}")

                light_info = LightInfo(
                    name=f"monitor_{monitor_num}",
                    unique_id=f"{self.core.mqtt.device_name}_twinkletray_{monitor_num}",
                    object_id=f"{self.core.mqtt.device_name}_twinkletray_{monitor_num}",
                    device=device_info,
                    icon="mdi:monitor",
                    display_name=monitor_name,
                    brightness=True  # 支持亮度控制
                )

                light_settings = Settings(
                    mqtt=mqtt_settings,
                    entity=light_info
                )

                # 使用 lambda 捕获当前的 monitor_num
                light = Light(
                    light_settings,
                    command_callback=lambda client, user_data, message, num=monitor_num:
                        self.handle_light_command(client, user_data, message, num)
                )

                # 设置当前亮度状态
                brightness = info.get("Brightness", 50)
                brightness_255 = int(brightness * 255 / 100)
                light.brightness(brightness_255)

                self.monitor_lights[monitor_num] = light

            # 创建 DDC/CI 命令文本实体
            ddcci_info = TextInfo(
                name="ddcci_command",
                unique_id=f"{self.core.mqtt.device_name}_twinkletray_ddcci",
                object_id=f"{self.core.mqtt.device_name}_twinkletray_ddcci",
                device=device_info,
                icon="mdi:console",
                display_name="DDC/CI命令"
            )

            ddcci_settings = Settings(
                mqtt=mqtt_settings,
                entity=ddcci_info
            )

            self.ddcci_text = Text(
                ddcci_settings,
                command_callback=self.handle_ddcci_command
            )

            self.ddcci_text.set_text("输入DDC/CI命令")

            self.log.info(f"TwinkleTray MQTT 实体创建成功，共创建 {len(self.monitor_lights)} 个显示器和 1 个命令实体")

        except Exception as e:
            self.log.error(f"创建 TwinkleTray MQTT 实体失败: {e}")

    def wake_up_screen(self):
        keyboard.press('shift')
        time.sleep(0.1)
        keyboard.release('shift')
        self.core.log.info("模拟输入Shift唤醒屏幕")

    def run_twinkle_tray_list(self):
        try:
            result = subprocess.run(
                [self.path, "--List"],
                capture_output=True,
                encoding='UTF-8',
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            self.core.log.error("执行命令失败:", e)
            return None

    def get_status(self):
        monitors = self.get_monitors_state()
        if monitors:
            status = {
                "level": "info",
                "status": [],
                "info": monitors
            }
            for monitor_num, info in monitors.items():
                status["status"].append(info.get("Brightness"))

            return status
        else:
            self.core.log.info("找不到兼容显示器")
            return {
                "level": "info",
                "info": "找不到兼容显示器"
            }


    def update_state(self):
        """更新所有显示器的状态到 MQTT"""
        monitors = self.get_monitors_state()
        if not monitors:
            return

        for monitor_num, info in monitors.items():
            if monitor_num in self.monitor_lights:
                brightness = info.get("Brightness", 0)
                brightness_255 = int(brightness * 255 / 100)
                self.monitor_lights[monitor_num].brightness(brightness_255)

    def handle_light_command(self, client: MQTTClient, user_data, message, monitor_num: int):
        """
        处理显示器灯光命令（由 ha-mqtt-discoverable 回调）
        :param client: MQTT 客户端
        :param user_data: 用户数据
        :param message: MQTT 消息
        :param monitor_num: 显示器编号
        """
        try:
            payload = message.payload.decode()
            self.log.info(f"收到显示器 {monitor_num} 命令: {payload}")
            monitor_num_key = monitor_num + 1  # TwinkleTray 使用从 1 开始的编号
            try:
                data = json.loads(payload)

                if "state" in data and data["state"] == "OFF":
                    # 显示器关机方案
                    power_type = self.read_monitor_power_type
                    match power_type:
                        case 0:
                            # 方案一，仅熄灭显示器，不关闭电源
                            ctypes.windll.user32.SendMessageW(0xFFFF, 0x112, 0xF170, 2)
                            self.log.info("系统层关闭画面")
                        case 1:
                            # 方案二，休眠显示器
                            run = [self.path, "--MonitorNum=" + str(monitor_num_key), "--VCP=0xD6:0x04"]
                            subprocess.Popen(run, creationflags=subprocess.CREATE_NO_WINDOW)
                            self.log.info(f"显示器 {monitor_num_key} 待机")
                        case 2:
                            # 方案三，显示器关机
                            run = [self.path, "--MonitorNum=" + str(monitor_num_key), "--VCP=0xD6:0x05"]
                            subprocess.Popen(run, creationflags=subprocess.CREATE_NO_WINDOW)
                            self.log.info(f"显示器 {monitor_num_key} 关机")
                elif "state" in data and data["state"] == "ON":
                    # 唤醒显示器
                    self.wake_up_screen()
                    self.log.info(f"唤醒显示器 {monitor_num_key}")
                if "brightness" in data:
                    brightness_255 = data.get("brightness", 128)
                    brightness = int(brightness_255 * 100 / 255)
                    run = [self.path, "--MonitorNum=" + str(monitor_num_key), "--Set=" + str(brightness)]
                    subprocess.Popen(run, creationflags=subprocess.CREATE_NO_WINDOW)
                    self.log.info(f"显示器 {monitor_num_key} 亮度设置为: {brightness}%")
                    # 更新状态
                    if monitor_num in self.monitor_lights:
                        self.monitor_lights[monitor_num].brightness(brightness_255)
            except (json.JSONDecodeError, KeyError) as e:
                self.log.error(f"解析亮度命令失败: {e}")
        except Exception as e:
            self.log.error(f"处理显示器命令失败: {e}")

    def handle_ddcci_command(self, client: MQTTClient, user_data, message):
        """
        处理 DDC/CI 命令（由 ha-mqtt-discoverable 回调）
        :param client: MQTT 客户端
        :param user_data: 用户数据
        :param message: MQTT 消息
        """
        try:
            command = message.payload.decode().strip()
            self.log.info(f"收到 DDC/CI 命令: {command}")

            if self.ddcci_text:
                self.ddcci_text.set_text(command)

            if not command:
                self.log.warning("DDC/CI 命令为空，忽略")
                return

            # 执行命令
            run = [self.path] + command.split(' ')
            subprocess.Popen(run, creationflags=subprocess.CREATE_NO_WINDOW)
            self.log.info(f"执行 DDC/CI 命令: {run}")

        except Exception as e:
            self.log.error(f"处理 DDC/CI 命令失败: {e}")

    def get_monitors_state(self):
        output = self.run_twinkle_tray_list()
        if output:
            monitors_info = extract_monitors_info(output)
            return monitors_info
        else:
            self.core.log.info("找不到兼容显示器")
            return None


    def print_monitors(self):
        try:
            output = self.run_twinkle_tray_list()
            print("获取到的监视器信息:")
            print(output)
            monitors = self.get_monitors_state()
            print(monitors.items())
            for monitor_num, info in monitors.items():
                print(f"显示器 {monitor_num}:")
                print("  MonitorID:", info.get("MonitorID"))
                print("  Name:", info.get("Name"))
                print("  Brightness:", info.get("Brightness"))
        except:
            print("未能获取到监视器信息。")

    def on_option_changed(self, e):
        self.read_monitor_power_type = e.control.value
        self.core.set_plugin_config("TwinkleTray", "monitor_power_type", int(e.control.value))

    def setting_page(self, e):
        """设置页面"""
        radio0 = ft.Radio(value="0", label="系统层关闭画面")
        radio1 = ft.Radio(value="1", label="显示器休眠")
        radio2 = ft.Radio(value="2", label="显示器关机(默认)")
        # 将按钮放入RadioGroup管理
        radio_group = ft.RadioGroup(
            content=ft.Column([radio0, radio1, radio2], spacing=10),
            on_change=self.on_option_changed,
            value=str(self.read_monitor_power_type)  # 设置默认选中项
        )
        # 构建页面布局

        return ft.Column(
                [
                    ft.Text("请选择显示器关闭方式：", size=20),
                    radio_group
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )


