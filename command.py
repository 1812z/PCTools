import paho.mqtt.client as mqtt
import json
import os
from volume import set_volume
from short_id import generate_short_id
from Toast import show_toast
import importlib
import sys

def send_discovery(name, id, type="button"):
    global device_name
    global comm_topic
    # 发现示例
    discovery_data = {
        "name": "button",
        "command_topic": "homeassistant/button/irrigation/set",
        "object_id": "object_id",
        "unique_id": "unique_id",
        "device": {
            "identifiers": ["PCTools"],
            "name": "PC",
            "manufacturer": "1812z",
            "model": "PCTools",
            "sw_version": "2024.10.31",
            "configuration_url": "https://1812z.top"
        }
    }

    discovery_topic = "homeassistant/" + type + \
        "/" + device_name + type + str(id) + "/config"

    if type == "button":
        discovery_topic = "homeassistant/" + type + \
            "/" + device_name + id + "/config"
        comm_topic = "homeassistant/" + type + "/" + \
            device_name + id + "/set"
        discovery_data["command_topic"] = comm_topic
    elif type == "light":
        comm_topic = "homeassistant/" + type + "/" + \
            device_name + str(id) + "/set"
        discovery_data["command_topic"] = comm_topic

        discovery_data["brightness_state_topic"] = "homeassistant/light/" + \
            device_name + "screen"
        discovery_data["brightness_command_topic"] = "homeassistant/light/" + \
            device_name + "screen" + "/set"
    elif type == "number":
        comm_topic = "homeassistant/" + type + "/" + \
            device_name + str(id) + "/set"
        discovery_data["command_topic"] = comm_topic
        discovery_data["state_topic"] = "homeassistant/number/" + \
            device_name + "volume/state"

    discovery_data["name"] = name
    discovery_data["device"]["name"] = device_name
    discovery_data["device"]["identifiers"] = [device_name]
    discovery_data["object_id"] = device_name + type + str(id)
    discovery_data["unique_id"] = device_name + type + str(id)

    info = "发现主题:" + discovery_topic
    mqttc.publish(discovery_topic, json.dumps(discovery_data))
    print(info)
    return info


def on_message(client, userdata, message):
    userdata.append(message.payload)
    command = message.payload.decode()
    if(message.topic == device_name + "/messages"):
        show_toast("HA通知",command)
    else:
        if (command != "ON"):
            run_command(message.topic, command)

    print(f"Received `{command}` from `{message.topic}` topic")


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Failed to connect: {
              reason_code}. loop_forever() will retry connection")
    else:
        print("成功连接到:", broker)
        subcribe(client)


# 运行命令
python_file = {}
def run_command(command, data):
    path = json_data.get("user_directory") + "\\AppData\\Local\\Programs\\twinkle-tray\\Twinkle Tray.exe"
    print("快捷命令目录: ",path)
    key = command.split('/')[2]
    if key == device_name + "screen":  # 显示器控制
        if data == "OFF":
            run = 'start /b cmd /c "'+ path + '" --MonitorNum=1 --VCP=0xD6:0x04'
            os.system(run)
        else:
            brightness = str(int(data) * 100 // 255)
            run = 'start /b cmd /c "'+ path + '" --MonitorNum=1 --Set=' + brightness
            print(run)
            os.system(run)
            print("显示器亮度:", brightness)
    elif key == device_name + "volume":
        set_volume(int(data) / 100)
    else:  # 运行文件
        run_file = command_data.get(key)
        if run_file.split('.')[1] == "py" :
            print("命令:", key, "执行PY文件:", run_file)

            file_path = os.path.join(os.path.dirname(__file__), 'commands', f'{run_file}')

            # 动态加载文件
            spec = importlib.util.spec_from_file_location(run_file, file_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[run_file] = module  
            spec.loader.exec_module(module)  

            if hasattr(module, 'fun'):
                module.fun()
            else:
                print(f"模块 {run_file} 中没有名为 'fun' 的函数")
        else:
            print("命令:", key, "运行文件:", run_file)
            run =  current_directory + '\\' + run_file  
            os.system(f'start "" "{run}"')


# 初始化
def init_data():
    global current_directory
    current_file_path = os.path.abspath(__file__)
    current_directory = os.path.dirname(current_file_path)
    current_directory = current_directory + '\\' + "commands"
    print(current_directory)
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
        global broker
        global user_directory
        json_data = json.load(file)
        username = json_data.get("username")
        password = json_data.get("password")
        broker = json_data.get("HA_MQTT")
        port = json_data.get("HA_MQTT_port")
        device_name = json_data.get("device_name")
        user_directory = json_data.get("user_directory")

    global mqttc
    mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqttc.user_data_set([])
    mqttc._username = username
    mqttc._password = password
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    mqttc.connect(broker, port)


def save_json_data(key, data):
    command_data[key] = data
    with open('commands.json', 'w', encoding='utf-8') as file:
        json.dump(command_data, file, indent=4)


def discovery():
    init_data()
    count = 2
    info = ""
    # 遍历当前目录中的文件
    for filename in os.listdir(current_directory):
        if os.path.isfile(os.path.join(current_directory, filename)):
            id = generate_short_id(filename)
            save_json_data(device_name + id, filename)
            info += filename +"\n"
            count += 1
            # 发现
            send_discovery(filename, id, "button")
    send_discovery("显示器", "screen", "light")
    send_discovery("音量", "volume", "number")
    save_json_data("count",count)
    info = "发现了"+ str(count) +"个命令\n" + info
    return info


def subcribe(client):
    if (count_entities != None):
        for filename in os.listdir(current_directory):
            if os.path.isfile(os.path.join(current_directory, filename)):
                subcribe_topic = "homeassistant/button/" + \
                    device_name + generate_short_id(filename) + "/set"
                client.subscribe(subcribe_topic)
                
    client.subscribe("homeassistant/light/" + device_name + "screen" + "/set")
    client.subscribe("homeassistant/number/" + device_name + "volume" + "/set")
    client.subscribe( device_name + "/messages")

def start_mqtt():
    try:
        discovery()
        mqttc.loop_start()
        print("MQTT订阅服务运行中")
    except:
        print("MQTT订阅服务启动失败")


def stop_mqtt_loop():
    mqttc.loop_stop()


if __name__ == '__main__':
    start_mqtt()
