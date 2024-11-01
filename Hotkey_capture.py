import keyboard
import json
import paho.mqtt.client as mqtt
import time

listening = False


def send_discovery(hotkeys):
    info = "快捷键发现: \n"
    for hotkey in hotkeys:
        discovery_data = {
            "name": "hotkey",
            "state_topic": "homeassistant/binary_sensor/ctrl1/state",
            "payload_on": "ON",
            "payload_off": "OFF",
            "object_id": "ctrl1",
            "unique_id": "ctrl1",
            "device": {
                    "identifiers": ["PCTools"],
                    "name": "PC",
                    "manufacturer": "1812z",
                    "model": "PCTools",
                    "sw_version": "2024.10.31",
                    "configuration_url": "https://1812z.top"
            }
        }
        discovery_data["name"] = hotkey
        discovery_data["object_id"] = discovery_data["unique_id"] = hotkey
        discovery_data["state_topic"] = "homeassistant/binary_sensor/" + \
            device_name + hotkey.replace("+", "-") + "/state"

        discovery_data["device"]["identifiers"] = [device_name]
        discovery_data["device"]["name"] = device_name
        discovery_data["object_id"] = device_name + "hotkey-" + hotkey
        discovery_data["unique_id"] = device_name + "hotkey-" + hotkey
        # 发现并初始化为关
        discovery_topic = "homeassistant/binary_sensor/" + \
            device_name + hotkey.replace("+", "-") + "/config"
        info = info + "发现主题:" + discovery_topic + "\n"
        mqttc.publish(discovery_topic, json.dumps(discovery_data))
        mqttc.publish("homeassistant/binary_sensor/" +
                      device_name + hotkey.replace("+", "-") + "/state", "OFF")
    return info


# 初始化
def init_data():
    load_hotkeys()
    # 读取账号密码
    with open('config.json', 'r') as file:
        global json_data
        global device_name
        global broker
        json_data = json.load(file)
        username = json_data.get("username")
        password = json_data.get("password")
        broker = json_data.get("HA_MQTT")
        port = json_data.get("HA_MQTT_port")
        device_name = json_data.get("device_name")

    global mqttc
    mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqttc.user_data_set([])
    mqttc._username = username
    mqttc._password = password
    mqttc.connect(broker, port)


def save_hotkey(hotkey):
    existing_hotkeys = load_hotkeys()
    if hotkey not in existing_hotkeys:
        with open('hotkeys.txt', 'a') as file:
            file.write(hotkey + '\n')
            print(f"保存快捷键: {hotkey}")
    else:
        print(f"快捷键 '{hotkey}' 已存在，未保存。")


def capture_hotkeys():
    print("开始捕获快捷键，按 'esc' 停止捕获...")
    captured_hotkeys = []

    def record_hotkey():
        hotkey = keyboard.read_event().name
        if hotkey != 'esc':
            captured_hotkeys.append(hotkey)
            print(f"捕获到快捷键: {captured_hotkeys}")

    while True:
        event = keyboard.read_event()
        if event.event_type == keyboard.KEY_DOWN:
            if event.name == 'esc':
                break
            record_hotkey()

    hotkey_join = '+'.join(captured_hotkeys)
    save_hotkey(hotkey_join)
    return hotkey_join


def load_hotkeys():
    try:
        with open('hotkeys.txt', 'r') as file:
            global hotkeys
            hotkeys = [line.strip() for line in file.readlines()]
            return hotkeys
    except FileNotFoundError:
        return []


def command(h):
    print("触发了快捷键:", h)
    mqttc.publish("homeassistant/binary_sensor/" + device_name +
                  h.replace("+", "-") + "/state", "ON")
    time.sleep(1)
    mqttc.publish("homeassistant/binary_sensor/" + device_name +
                  h.replace("+", "-") + "/state", "OFF")


def listen_hotkeys():
    global listening
    if listening == False:
        listening = True
        init_data()
        send_discovery(hotkeys)
        print("开始监听快捷键...", hotkeys)
        for hotkey in hotkeys:
            keyboard.add_hotkey(hotkey, lambda h=hotkey: command(h))
        # keyboard.wait('esc')
        return 0
    return 1


def stop_listen():
    global listening
    if listening == True:
        listening = False
        for hotkey in hotkeys:
            keyboard.remove_hotkey(hotkey)
        print("已停止监听快捷键")
        return 0
    return 1


def menu():
    while True:
        print("按键监听:", listening, "请选择")
        print("1. 捕获快捷键并保存")
        print("2. 开启监听")
        print("3. 发送Discovery MQTT")
        print("4. 退出")
        choice = input("请输入选项: ")

        if choice == '1':
            capture_hotkeys()
        elif choice == '2':
            listen_hotkeys()
        elif choice == '3':
            init_data()
            print(send_discovery(hotkeys))
        elif choice == '4':
            break
        else:
            print("无效选项，请重试。")


if __name__ == '__main__':
    menu()
