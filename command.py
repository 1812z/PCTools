import paho.mqtt.client as mqtt
import os
from windows_toasts import Toast, WindowsToaster
import threading
import time
import json


# 读取账号密码
with open('config.json', 'r') as file:
    json_data = json.load(file)
    secret_id = json_data.get("secret_id")

# MQTT服务器信息
broker = 'bemfa.com'
topic = 'dnkz005'
monitor_topic = 'monitor002'
port = 9501


# MQTT
def on_message(client, userdata, message):
    userdata.append(message.payload)
    command = message.payload.decode()
    print(f"Received `{command}` from `{message.topic}` topic")
    # 设备管理
    if message.topic == topic:
        if command == 'on':
            print("已经开啦")
        elif command == 'off':
            os.system("shutdown -s -t 10")
        # 运行命令
        elif command == 'on#1':
            print("Run 'run.bat'")
            os.system(r"C:\Users\i\Desktop\Coding\xiaoai_remote\run1.bat")
        elif command == 'on#2':
            print("重启设备")
            os.system("shutdown -r -t 10")
        elif command == 'on#3':
            print("Run 'run.bat'")
            os.system(r"C:\Users\i\Desktop\Coding\xiaoai_remote\run3.bat")

    # 显示器控制
    if message.topic == monitor_topic:
        # 关闭显示器
        if command == 'off' or command == '0':
            run = r' "C:\Program Files\WindowsApps\38002AlexanderFrangos.TwinkleTray_1.15.4.0_x64__m7qx9dzpwqaze\app\Twinkle Tray.exe" --MonitorNum=1 --VCP=0xD6:0x04 '
            os.system(run)
        elif command == 'on':
            print("自己开")
        else:  # 亮度调节
            brightness = command[3:]
            run = 'start /b cmd /c '+r' "C:\Program Files\WindowsApps\38002AlexanderFrangos.TwinkleTray_1.15.4.0_x64__m7qx9dzpwqaze\app\Twinkle Tray.exe" --MonitorNum=1 --Set=' + brightness
            os.system(run)


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Failed to connect: {reason_code}. loop_forever() will retry connection")
    else:
        print("成功连接到:", broker)
        client.subscribe(topic)
        client.subscribe(monitor_topic)  # 订阅 monitor002 主题


mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,client_id=secret_id)
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.user_data_set([])
mqttc.connect(broker, port)


def start_mqtt():
    print("MQTT服务启动中...")
    mqttc.loop_start()
    

def stop_mqtt_loop():
    mqttc.loop_stop()

if __name__ == '__main__':
    mqttc.loop_start()
    try:
        while True:
            print("MQTT Running")
            time.sleep(1)
    except KeyboardInterrupt:
        mqttc.disconnect()
