import paho.mqtt.client as mqtt
import os
from windows_toasts import Toast, WindowsToaster
import time
import psutil
import threading
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from flask import Flask, send_file ,Response
import cv2
import pyautogui
from PIL import Image
import io
import json
import subprocess

#Windows通知注册
toaster = WindowsToaster('Python')
newToast = Toast()
info = 'Loading...'
newToast.text_fields = [info]
newToast.on_activated = lambda _: print('Toast clicked!')

#读取账号密码
with open('config.json', 'r') as file:
        json_data = json.load(file)
        secret_id = json_data.get("secret_id")

# MQTT服务器信息
broker = 'bemfa.com'
topic = 'dnkz005'
monitor_topic = 'monitor002'
port = 9501
 

#发布通知函数
def toast(info):
    newToast.text_fields = [info]
    toaster.show_toast(newToast)

#MQTT
def on_message(client, userdata, message):
    userdata.append(message.payload)
    command = message.payload.decode()
    print(f"Received `{command}` from `{message.topic}` topic")
    # 设备管理
    if message.topic == topic:
        if command == 'on':
            toast("电脑已经开着啦")
        elif command == 'off':
            os.system("shutdown -s -t 10")
        #运行命令
        elif command == 'on#1':
            print("Run 'run.bat'")
            os.system(r"C:\Users\i\Desktop\Coding\xiaoai_remote\run1.bat")
        elif command == 'on#2':
            print("重启设备")
            os.system("shutdown -r -t 10")
        elif command == 'on#3':
            print("Run 'run.bat'")
            os.system(r"C:\Users\i\Desktop\Coding\xiaoai_remote\run3.bat")

    #显示器控制
    if message.topic == monitor_topic:
        #关闭显示器
        if command == 'off' or command == '0':
           run = r' "C:\Program Files\WindowsApps\38002AlexanderFrangos.TwinkleTray_1.15.4.0_x64__m7qx9dzpwqaze\app\Twinkle Tray.exe" --MonitorNum=1 --VCP=0xD6:0x04 '
           os.system(run)
        elif command == 'on':
            print("自己开")
        else: #亮度调节
            brightness = command[3:]
            run = 'start /b cmd /c '+r' "C:\Program Files\WindowsApps\38002AlexanderFrangos.TwinkleTray_1.15.4.0_x64__m7qx9dzpwqaze\app\Twinkle Tray.exe" --MonitorNum=1 --Set='+ brightness
            os.system(run)  
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        toast("连接MQTT失败: {reason_code}. 重新连接中...")
        print(f"Failed to connect: {reason_code}. loop_forever() will retry connection")
    else:
        toast("MQTT成功连接至"+broker)
        print("Connected to", broker)
        client.subscribe(topic)
        client.subscribe(monitor_topic)  # 订阅 monitor002 主题

def on_publish(client, userdata, mid, reason_codes, properties):
    if reason_codes.is_failure:
        print('消息发布失败')

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.on_publish = on_publish
mqttc.user_data_set([])
mqttc._client_id = secret_id
mqttc.connect(broker, port)


# MQTT反馈传感器数据
def sensors():
    while (1):
        try:
            result = subprocess.run(['python', 'aida64.py'], capture_output=True, text=True)
            print(result.stdout)
            time.sleep(15)
        except Exception as e:
            print(f"An error occurred: {e}")

def run_flask_app():
    app.run(host='192.168.44.236', port=5000)


# 传感器数据反馈线程
def loop_task():
    sensors()
    time.sleep(15)

loop_thread = threading.Thread(target=loop_task)
loop_thread.start()


# Web网页返回截图
app = Flask(__name__)

def generate_screenshots():
    while True:
        # 截取屏幕
        screenshot = pyautogui.screenshot()
        img_byte_array = io.BytesIO()
        screenshot.save(img_byte_array, format='JPEG',quality=50)
        img_byte_array.seek(0)
        # 返回JPEG画面
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + img_byte_array.read() + b'\r\n')
        time.sleep(0.3)  # 画面速率

@app.route('/screenshot.jpg')
def get_screenshot():
    return Response(generate_screenshots(), mimetype='multipart/x-mixed-replace; boundary=frame')

#摄像头画面
def generate_frames():
    camera = cv2.VideoCapture(2)  
    while True:
        success, frame = camera.read()
        if not success:
            with open(r"failed.jpeg","rb") as f:
                frame = f.read()
                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.start()

    mqttc.loop_forever()



