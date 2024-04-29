import paho.mqtt.client as mqtt
import os

# MQTT服务器信息
broker = 'bemfa.com'
topic = 'dnkz005'
monitor_topic = 'monitor002'
secret_id = 'id'
port = 9501

def on_subscribe(client, userdata, mid, reason_code_list, properties):
    for sub_result in reason_code_list:
        if sub_result >= 128:
            print("Subscribe failed")

def on_unsubscribe(client, userdata, mid, reason_code_list, properties):
    if len(reason_code_list) == 0 or not reason_code_list[0].is_failure:
        print("Unsubscribe succeeded")
    else:
        print(f"Broker replied with failure: {reason_code_list[0]}")
    client.disconnect()

def on_message(client, userdata, message):
    userdata.append(message.payload)
    command = message.payload.decode()
    print(f"Received `{command}` from `{message.topic}` topic")
    # 这里放置需要运行的命令
    if message.topic == topic:
        if command == 'off':
            os.system("shutdown -s")
        if command == 'on#1':
            print("Run 'run.bat'")
            os.system(r"C:\Users\i\Desktop\Coding\xiaoai_remote\run.bat")
    if message.topic == monitor_topic:
        if command == 'off' or command == '0':
           run = r' "C:\Program Files\WindowsApps\38002AlexanderFrangos.TwinkleTray_1.15.4.0_x64__m7qx9dzpwqaze\app\Twinkle Tray.exe" --MonitorNum=1 --VCP=0xD6:0x04 '
           os.system(run)
        elif command == 'on':
            print("自己开")
        else:
            brightness = command[3:]
            run = r' "C:\Program Files\WindowsApps\38002AlexanderFrangos.TwinkleTray_1.15.4.0_x64__m7qx9dzpwqaze\app\Twinkle Tray.exe" --MonitorNum=1 --Set='+ brightness
            os.system(run)
           
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Failed to connect: {reason_code}. loop_forever() will retry connection")
    else:
        print("Connected to", broker)
        client.subscribe(topic)
        client.subscribe(monitor_topic)  # 订阅 monitor002 主题

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.on_subscribe = on_subscribe
mqttc.on_unsubscribe = on_unsubscribe

mqttc.user_data_set([])
mqttc._client_id = secret_id
mqttc.connect(broker, port)
mqttc.loop_forever()
print(f"Received the following message: {mqttc.user_data_get()}")
