import json
import keyboard
import time
from Toast import show_toast
from MQTT import Send_MQTT_Discovery,Publish_MQTT_Message
listening = False


def send_discovery(hotkeys):
    info = "快捷键发现: \n"
    for hotkey in hotkeys:
        name_id = "hotkey" + hotkey.replace("+", "-")
        Send_MQTT_Discovery(name=hotkey,name_id=name_id,type="binary_sensor")
        info = info + hotkey
    
    init_binary_sensor(hotkeys)
    return info

def init_binary_sensor(hotkeys):
    for hotkey in hotkeys:
        topic = "homeassistant/binary_sensor/" + device_name + hotkey.replace("+", "-") + "/state"
        Publish_MQTT_Message(topic,"OFF")

# 初始化
def init_data():
    with open('config.json', 'r') as file:
        global json_data
        global hotkey_notify
        global suppress
        global device_name
        json_data = json.load(file)
        hotkey_notify = json_data.get("hotkey_notify")
        suppress = json_data.get("suppress")
        device_name = json_data.get("device_name")
    load_hotkeys()

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
    key_list = h.split('+')
    for item in key_list:
        keyboard.release(item)
        print(item)
    print("触发了快捷键:", h)
    if hotkey_notify == True:
        show_toast("PCTools" ,"触发了快捷键:" + h)
    topic = "homeassistant/binary_sensor/" + device_name + h.replace("+", "-") + "/state"
    Publish_MQTT_Message(topic,"ON")
    time.sleep(1)
    Publish_MQTT_Message(topic,"OFF")


def listen_hotkeys():
    global listening
    if listening == False:
        listening = True
        init_data()
        send_discovery(hotkeys)
        print("开始监听快捷键...", hotkeys)
        for hotkey in hotkeys:
            keyboard.add_hotkey(hotkey, lambda h=hotkey: command(h),suppress=suppress,trigger_on_release=False)
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
            load_hotkeys()
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
