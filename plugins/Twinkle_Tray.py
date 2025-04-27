import ctypes
import subprocess
import re
import os
import time
import keyboard


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


class Twinkle_Tray:
    def __init__(self, core):
        self.core = core
        self.device_name = core.config.get_config("device_name")
        self.path =  os.path.expanduser("~") + "\\AppData\\Local\\Programs\\twinkle-tray\\Twinkle Tray.exe"
        self.updater = {
            "timer": 60
        }
        self.config = []
        self.generate_entity()

    def generate_entity(self):
        monitors = self.get_monitors_state()
        if monitors:
            for monitor_num, info in monitors.items():
                entity = {
                    'name': '',
                    'entity_type': 'light',
                    'entity_id': '',
                    'icon': 'mdi:monitor'
                }
                entity["name"] = info.get("Name")
                entity["entity_id"] += str(monitor_num)
                self.config.append(entity)

            entity = {
                'name': 'DDC/CI',
                'entity_type': 'text',
                'entity_id': 'DDCCI',
                'icon': 'mdi:monitor'
            }
            self.config.append(entity)

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
        monitors = self.get_monitors_state()
        for monitor_num, info in monitors.items():
            topic = f"Twinkle_Tray_{monitor_num}"
            self.core.mqtt.update_state_data(info.get("Brightness") * 255/100,topic,"light")

    def handle_mqtt(self, key, data):
        if "DDCCI" in key:
            run = [self.path] + data.split(' ')
            self.core.log.info(f"DDC/CI命令: {run}")
            subprocess.Popen(run, creationflags=subprocess.CREATE_NO_WINDOW)
            return
        if data == "OFF":
            # 显示器关机方案
            # 方案一,关闭电源:
            # run = [path, "--MonitorNum=1", "--VCP=0xD6:0x04"]
            # subprocess.Popen(run, creationflags=subprocess.CREATE_NO_WINDOW)
            # monitor_num_key = int(key[9:]) + 1
            # run = [path, "--MonitorNum=" + str(monitor_num_key), "--VCP=0xD6:0x04"]
            # subprocess.Popen(run, creationflags=subprocess.CREATE_NO_WINDOW)
            # logger.info(f"显示器{monitor_num_key}关机")
            # 方案二,仅熄灭显示器,不关闭电源,但会熄灭所有显示器
            ctypes.windll.user32.SendMessageW(0xFFFF, 0x112, 0xF170, 2)  # 0xF170 = WM_SYSCOMMAND, 2 = SC_MONITORPOWER)
        elif data == "ON":
            self.wake_up_screen()  # 模拟输入唤醒显示器
        else:
            monitor_num_key = int(key) + 1
            brightness = str(int(data) * 100 // 255)
            run = [self.path, "--MonitorNum=" + str(monitor_num_key), "--Set=" + brightness]
            subprocess.Popen(run, creationflags=subprocess.CREATE_NO_WINDOW)
            self.core.log.info(f"显示器{monitor_num_key}亮度: {brightness}")
            self.update_state()

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


