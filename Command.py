import json
import os
from short_id import generate_short_id
from MQTT import Send_MQTT_Discovery, MQTT_Subcribe
from Twinkle_Tray import get_monitors_state

# 运行命令
python_file = {}


# 初始化
def init_data():
    global current_directory
    current_file_path = os.path.abspath(__file__)
    current_directory = os.path.dirname(current_file_path)
    current_directory = current_directory + '\\' + "commands"
    # print(current_directory)
    # 命令映射表
    with open('commands.json', 'r') as file:
        global command_data
        global count_entities
        command_data = json.load(file)
        count_entities = command_data.get("count")
    # 读取账号密码
    with open('config.json', 'r') as file:
        global json_data
        global device_name
        global user_directory
        global monitor_supported
        json_data = json.load(file)
        device_name = json_data.get("device_name")
        user_directory = json_data.get("user_directory")
        monitor_supported = json_data.get("monitor_supported")
    if monitor_supported:
        global monitors
        monitors = get_monitors_state()


def save_json_data(key, data):
    command_data[key] = data
    with open('commands.json', 'w', encoding='utf-8') as file:
        json.dump(command_data, file, indent=4, ensure_ascii=False)


init_data()


def Send_Monitor_MQTT_Discovery():
    for monitor_num, monitor_info in monitors.items():
        Send_MQTT_Discovery(None, name=monitor_info.get("Name"), name_id=f"monitor{monitor_num}", type="light")


def discovery():
    count = 2
    info = ""

    # 发现当前目录中的可执行文件
    for filename in os.listdir(current_directory):
        if os.path.isfile(os.path.join(current_directory, filename)):
            id = generate_short_id(filename)
            save_json_data(device_name + id, filename)
            info += filename + "\n"
            count += 1
            Send_MQTT_Discovery(None, name=filename, name_id=id, type="button")
    Send_Monitor_MQTT_Discovery()
    Send_MQTT_Discovery(None, name="音量", name_id="volume", type="number", timeout=1)

    save_json_data("count", count)
    info = f"发现了{count}个命令\n" + info
    return info


def subcribe():
    # 订阅发现的命令
    if count_entities != 0:
        for filename in os.listdir(current_directory):
            if os.path.isfile(os.path.join(current_directory, filename)):
                subcribe_topic = f"homeassistant/button/{device_name}{generate_short_id(filename)}/set"
                MQTT_Subcribe(subcribe_topic)
    if monitor_supported:
        for monitor_num, monitor_info in monitors.items():
            MQTT_Subcribe(f"homeassistant/light/{device_name}monitor{monitor_num}/set")
    MQTT_Subcribe(f"homeassistant/number/{device_name}volume/set")
    MQTT_Subcribe(f"{device_name}/messages")


if __name__ == '__main__':
    discovery()
