import json
import subprocess
import re


with open('config.json', 'r') as file:
    global json_data
    global device_name
    global path
    json_data = json.load(file)
    device_name = json_data.get("device_name")
    user_directory = json_data.get("user_directory")
    path = json_data.get("user_directory") + "\\AppData\\Local\\Programs\\twinkle-tray\\Twinkle Tray.exe"

def remove_ansi_escape(text):
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    return ansi_escape.sub('', text)

def run_twinkle_tray_list():
    try:
        result = subprocess.run(
            [path, "--List"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print("执行命令失败:", e)
        return None

def extract_monitors_info(info_str):
    # 先清除 ANSI 转义码
    clean_str = remove_ansi_escape(info_str)
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
def get_monitors_state():
    output = run_twinkle_tray_list()
    monitors_info = extract_monitors_info(output)
    return monitors_info

if __name__ == "__main__":
    # 运行命令，获取显示器信息
    output = run_twinkle_tray_list()
    if output:
        print("获取到的监视器信息:")
        print(output)
        monitors = get_monitors_state()
        
        for monitor_num, info in monitors.items():
            print(f"显示器 {monitor_num}:")
            print("  MonitorID:", info.get("MonitorID"))
            print("  Name:", info.get("Name"))
            print("  Brightness:", info.get("Brightness"))
    else:
        print("未能获取到监视器信息。")