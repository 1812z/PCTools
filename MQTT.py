import time
import paho.mqtt.client as mqtt
import json
from Execute_Command import MQTT_Command

global mqttc,initialized
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
initialized = False

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"连接MQTT服务器失败: {reason_code} 尝试重新连接..")
    else:
        print("成功连接到:", broker)

def on_message(client, userdata, data):
    userdata.append(data.payload)
    message = data.payload.decode()
    MQTT_Command(data.topic,message)
    print(f"MQTT主题: `{data.topic}` 消息: `{message}` ")

# 初始化MQTT
def init_data():
    global json_data,device_name,initialized,broker
    initialized = True
    # 读取账号密码
    with open('config.json', 'r') as file:
        json_data = json.load(file)
        username = json_data.get("username")
        password = json_data.get("password")
        broker = json_data.get("HA_MQTT")
        port = json_data.get("HA_MQTT_port")
        device_name = json_data.get("device_name")

    mqttc.user_data_set([])
    mqttc._username = username
    mqttc._password = password
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    try:
        mqttc.connect(broker, port)
    except:
        print("MQTT连接失败")
        initialized = False
        return 1

init_data()
# device_class HA设备类型
# topic_id 数据编号，默认空
# name 实体名称
# name_id 实体唯一标识符
# type 实体类型 默认sensor
def Send_MQTT_Discovery(device_class=None, topic_id=None,name='Sensor1', name_id='', type="sensor",is_aida64=False,timeout=0):
    global device_name,initialized
    if not initialized:
        if init_data() == 1:
            return "timeout"

    # 发现示例
    discovery_data = {
        "name": "Sensor1",
        "object_id": "object_id",
        "unique_id": "unique_id",
        "device": {
            "identifiers": ["PCTools"],
            "name": "PC",
            "manufacturer": "1812z",
            "model": "PCTools",
            "sw_version": "2024.12.9",
            "configuration_url": "https://1812z.top"
        }
    }
    # 状态主题
    # discovery_data["availability_topic"] = "homeassistant/PCTools" + device_name + "/availability"

    # 超时离线
    if(timeout != 0):
        discovery_data["expire_after"] = timeout

    # 发现主题
    discovery_topic = "homeassistant/" + type + "/" + device_name + name_id + "/config"
    
    # 实体信息标记
    discovery_data["name"] = name
    discovery_data["device"]["name"] = device_name
    discovery_data["device"]["identifiers"] = [device_name]
    discovery_data["object_id"] = device_name + name_id
    discovery_data["unique_id"] = device_name + name_id
    # 数据编号处理
    if topic_id is not None:
        discovery_data["value_template"] = "{{ float(value_json." + \
            device_class + "[" + str(topic_id) + "].value) }}"
    # 主类型处理
    if type == 'sensor' and is_aida64:
        state_topic = "homeassistant/" + type + "/" + device_name  + "/state"
        discovery_data["state_topic"] = state_topic
    elif type == 'sensor' and not is_aida64:
        state_topic = "homeassistant/" + type + "/" + device_name + name_id + "/state"
        discovery_data["state_topic"] = state_topic        
    elif type == "button"  or type == "number" :
        command_topic = "homeassistant/" + type + "/" + device_name + name_id + "/set"
        discovery_data["command_topic"] = command_topic
    elif type == "light":
        command_topic = "homeassistant/" + type + "/" + device_name + name_id + "/set"
        discovery_data["command_topic"] = command_topic
        discovery_data["brightness_state_topic"] = "homeassistant/light/" + device_name + "screen"
        discovery_data["brightness_command_topic"] = "homeassistant/light/" + device_name + "screen" + "/set"
    elif type == "binary_sensor":
        state_topic = "homeassistant/" + type + "/" + device_name + name_id + "/state"
        discovery_data["state_topic"] = state_topic  
        discovery_data["payload_on"] = "ON"
        discovery_data["payload_off"] = "OFF"
    
    
    # 子类型处理
    if device_class == "pwr":
        discovery_data["device_class"] = "power"
        discovery_data["unit_of_measurement"] = "W"
    elif device_class == "fan":
        discovery_data["device_class"] = "speed"
        discovery_data["unit_of_measurement"] = "RPM"
    elif device_class == "sys":
        discovery_data.pop('device_class', None)
        discovery_data["unit_of_measurement"] = "%"
        if "Disk" in name:
            if "Activity" in name:
                discovery_data["unit_of_measurement"] = "%"
            else:
                discovery_data["unit_of_measurement"] = "KB/s"
        if "NIC" in name:
            if "Total" in name:
                discovery_data["unit_of_measurement"] = "M"
            else:
                discovery_data["unit_of_measurement"] = "KB/s"
    elif device_class == "temp":
        discovery_data["device_class"] = "temperature"
        discovery_data["unit_of_measurement"] = "°C"
    # 发送信息
    info = "发现主题:" + discovery_topic
    # print(info)
    mqttc.publish(discovery_topic, json.dumps(discovery_data))
    return info


# 发送自定义消息
def Publish_MQTT_Message(topic,message):
    if not initialized:
        init_data()
    mqttc.publish(topic, message)

# 更新状态数据
def Update_State_data(data,topic,type):
    if type == "number":
        state_topic = "homeassistant/number/" + device_name + topic + "/state"
        Publish_MQTT_Message(state_topic,str(data))
    elif type == "sensor":
        state_topic = "homeassistant/sensor/" + device_name + topic + "/state"
        Publish_MQTT_Message(state_topic,data)
        # print(state_topic,data)
    

def MQTT_Subcribe(topic):
    if mqttc.is_connected():
        mqttc.subscribe(topic)
    else:
        print("MQTT订阅服务未连接!")

# MQTT 进程管理
def start_mqtt():
    try:
        mqttc.loop_start()
        timer = 0
        while(timer<=5):
            time.sleep(1)
            timer+=1
            if mqttc.is_connected():
                return 0
            elif timer == 10:
                print("MQTT连接超时")
                return 1
        print("MQTT订阅服务运行中")
    except:
        print("MQTT订阅服务启动失败")

def stop_mqtt_loop():
    mqttc.loop_stop()


if __name__ == '__main__':
    init_data()
    mqttc.loop_start()
    input("TEST:\n")


    