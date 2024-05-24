import python_aida64
from pprint import pprint
import paho.mqtt.client as mqtt
import json

device_name = "PCmonitor"

#读取账号密码
with open('config.json', 'r') as file:
        json_data = json.load(file)
        secret_id = json_data.get("secret_id")
        username = json_data.get("username")
        password = json_data.get("password")
        discovery_flag = json_data.get("discovery")
        global_id = json_data.get("count")
broker = 'ha.1812z.top'
topic = 'homeassistant/sensor/sensorBedroom/state'
port = 1883


def send_discovery(device_class,topic_id,name,name_id):
    global global_id 
    discovery_data = {
        "name": "Sensor1",
        "device_class": "temperature",
        "state_topic": "homeassistant/sensor/aida64/state",
        "unit_of_measurement": "°C",
        "value_template": "{{ float(value_json.temp[1].value) }}",
        "unique_id": "temp01ae",
        "device": {
            "identifiers": ["aida64"],
            "name": "PC",
            "manufacturer": "1812z",
            "model": "aida64",
            "sw_version": "2024.5.24",
            "configuration_url": "https://1812z.top"
        }
    }
    state_topic = "homeassistant/sensor/" + device_name + "/state"
    discovery_topic = "homeassistant/sensor/" + device_name + name_id + "/config"
    discovery_data["state_topic"] = state_topic
    discovery_data["name"] = name
    discovery_data["unique_id"] = str(global_id)
    discovery_data["value_template"] = "{{ float(value_json."+ device_class + "["+ str(topic_id) + "].value) }}" 

    global_id += 1
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


    print("消息主题：",discovery_topic)    
    mqttc.publish(discovery_topic,json.dumps(discovery_data))
          
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.user_data_set([])
mqttc._client_id = secret_id
mqttc._username = username
mqttc._password = password
mqttc.connect(broker, port) 
aida64_data = python_aida64.getData()
pprint(python_aida64.getData())

#发现设备
if discovery_flag == 1: # 请编辑config.json中的discovery_flag，1则配置发现设备
    global_id = 0
    id1 = 0
    id2 = 0
    id3 = 0
    id4 = 0
    json_data['discovery']  = 0
    with open("config.json", 'w') as file:
        json.dump(json_data, file, indent=4)
    print("发送discovery MQTT信息")
    for category, items in aida64_data.items():
        if category == "temp":
            for item in items:
                name = item["label"]
                name_id = item["id"]
                send_discovery(category,id1,name,name_id)
                id1 = id1 + 1
        if category == "pwr":
            for item in items:
                name = item["label"]
                name_id = item["id"]
                send_discovery(category,id2,name,name_id)
                id2 = id2 + 1
        if category == "fan":
            for item in items:
                name = item["label"]
                name_id = item["id"]
                send_discovery(category,id3,name,name_id)
                id3 = id3 + 1
        if category == "sys":
             for item in items:
                name = item["label"]
                name_id = item["id"]
                send_discovery(category,id4,name,name_id)
                id4 = id4 + 1

    json_data['count']  = global_id
    with open("config.json", 'w') as file:
        json.dump(json_data, file, indent=4)

#发送传感器信息
state_topic = "homeassistant/sensor/" + device_name + "/state"
mqttc.publish(state_topic,json.dumps(aida64_data))
print("发送数据：", state_topic)

mqttc.disconnect()
