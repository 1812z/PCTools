import time
import paho.mqtt.client as mqtt
import json
import os


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
            "sw_version": "2024.6.12",
            "configuration_url": "https://1812z.top"
        }
    }

    discovery_topic = "homeassistant/" + type + \
        "/" + device_name + type + str(id) + "/config"
    comm_topic = "homeassistant/" + type + "/" + \
        device_name + type + str(id) + "/set"
    discovery_data["command_topic"] = comm_topic

    discovery_data["name"] = name
    discovery_data["device"]["name"] = device_name
    discovery_data["device"]["identifiers"] = [device_name]
    discovery_data["object_id"] = device_name + type + str(id)
    discovery_data["unique_id"] = device_name + type + str(id)

    info = "发现主题:" + discovery_topic
    mqttc.publish(discovery_topic, json.dumps(discovery_data))
    return info


def on_message(client, userdata, message):
    userdata.append(message.payload)
    command = message.payload.decode()
    run_command(message.topic)
    print(f"Received `{command}` from `{message.topic}` topic")


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Failed to connect: {reason_code}. loop_forever() will retry connection")
    else:
        print("成功连接到:", broker)
        subcribe(client)

def run_command(command):
    key = command.split('/')[2]
    run_file = command_data.get(key)
    print("命令:",key,"运行文件:",run_file)
    run =  "start "+ current_directory + '\\' + run_file 
    print(run)
    os.system(run)

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
        global device_name
        global broker
        json_data = json.load(file)
        secret_id = json_data.get("secret_id")
        username = json_data.get("username")
        password = json_data.get("password")
        broker = json_data.get("HA_MQTT")
        port = json_data.get("HA_MQTT_port")
        device_name = json_data.get("device_name")

    global mqttc
    mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=secret_id)
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
    count = 0
    # 遍历当前目录中的文件
    for filename in os.listdir(current_directory):
        if os.path.isfile(os.path.join(current_directory, filename)):
            count += 1
            # 输出文件名，不包括后缀
            save_json_data(device_name + "button" + str(count), os.path.splitext(filename)
                           [0] + os.path.splitext(filename)[1])
            send_discovery(os.path.splitext(filename)[
                           0] + os.path.splitext(filename)[1], count)
    save_json_data("count", count)
    return count

def subcribe(client):
    if(count_entities > 0):
        for i in range(count_entities):
            subcribe_topic = "homeassistant/button/" + \
                device_name + "button" + str(i+1) + "/set"
            # print(subcribe_topic)
            client.subscribe(subcribe_topic)

def start_mqtt():
    print("MQTT服务启动中...")
    init_data()
    mqttc.loop_start()
    

def stop_mqtt_loop():
    mqttc.disconnect()
    mqttc.loop_stop()

if __name__ == '__main__':
    init_data()
    discovery()
    mqttc.loop_start()
    try:
        while True:
            print("MQTT Running")
            time.sleep(1)
    except KeyboardInterrupt:
        mqttc.disconnect()

