import ctypes
import python_aida64
from pprint import pprint
import paho.mqtt.client as mqtt
import json
from volume import get_volume

count = 0
debug = False


def send_discovery(device_class, topic_id, name, name_id, type="sensor"):
    global count
    count += 1

    # 发现示例
    discovery_data = {
        "name": "Sensor1",
        "device_class": "temperature",
        "state_topic": "homeassistant/sensor/aida64/state",
        "unit_of_measurement": "°C",
        "value_template": "{{ float(value_json.temp[1].value) }}",
        "object_id": "object_id",
        "unique_id": "unique_id",
        "device": {
            "identifiers": ["PCTools"],
            "name": "PC",
            "manufacturer": "1812z",
            "model": "PCTools",
            "sw_version": "2024.12.2",
            "configuration_url": "https://1812z.top"
        }
    }
    state_topic = "homeassistant/" + type + "/" + device_name + "/state"
    discovery_topic = "homeassistant/" + type + \
        "/" + device_name + name_id + "/config"
    if (debug):
        print("状态主题:", state_topic, "发现主题:", discovery_topic)
    discovery_data["state_topic"] = state_topic
    discovery_data["name"] = name
    discovery_data["device"]["name"] = device_name
    discovery_data["device"]["identifiers"] = [device_name]
    discovery_data["object_id"] = device_name + name_id
    discovery_data["unique_id"] = device_name + name_id
    discovery_data["value_template"] = "{{ float(value_json." + \
        device_class + "[" + str(topic_id) + "].value) }}"

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
 
    info = "发现主题:" + discovery_topic
    mqttc.publish(discovery_topic, json.dumps(discovery_data))
    return info


# 初始化MQTT
def init_data():
    # 读取账号密码
    with open('config.json', 'r') as file:
        global json_data
        global device_name
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
    try:
        mqttc.connect(broker, port)
    except:
        print("MQTT连接失败")
        return 1

    



# 发送自定义消息
def publish_message(topic,message):
    init_data()
    mqttc.publish(topic, message)


# 发送音量信息
def send_volume():
    volume = get_volume()
    state_topic = "homeassistant/number/" + device_name + "volume" + "/state"
    mqttc.publish(state_topic, volume)


# 初始化Aida64数据
def get_aida64_data():
    global aida64_data
    aida64_data = python_aida64.getData()


# 发送Aida64传感器数据
def send_aida64():
    get_aida64_data()
    state_topic = "homeassistant/sensor/" + device_name + "/state"
    if (debug):
        pprint(python_aida64.getData())
    mqttc.publish(state_topic, json.dumps(aida64_data))


# 发送传感器信息
def send_data():
    if init_data() != 1:
        try:
            send_volume()
        except ctypes.COMError:
            print("找不到扬声器")
        #discovery()
        send_aida64()


        mqttc.disconnect()
        state_topic = "homeassistant/sensor/" + device_name + "/state"
        info = "发送数据：" + state_topic
        return info


# 发现设备
def discovery():
    get_aida64_data()

    if init_data() != 1:
        info = ""
        id1 = 0
        id2 = 0
        id3 = 0
        id4 = 0

        print("发送discovery MQTT信息")
        for category, items in aida64_data.items():
            if category == "temp":
                for item in items:
                    name = item["label"]
                    name_id = item["id"]
                    info += send_discovery(category, id1, name, name_id)+"\n"
                    id1 = id1 + 1
            if category == "pwr":
                for item in items:
                    name = item["label"]
                    name_id = item["id"]
                    info += send_discovery(category, id2, name, name_id)+"\n"
                    id2 = id2 + 1
            if category == "fan":
                for item in items:
                    name = item["label"]
                    name_id = item["id"]
                    info += send_discovery(category, id3, name, name_id)+"\n"
                    id3 = id3 + 1
            if category == "sys":
                for item in items:
                    name = item["label"]
                    name_id = item["id"]
                    info += send_discovery(category, id4, name, name_id) + "\n"
                    id4 = id4 + 1
        info = "发现了" + str(count) + "个实体\n" + info
        return info
    return 1


if __name__ == "__main__":
    get_aida64_data()
    discovery()
    send_data()
