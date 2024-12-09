import ctypes
import time
import python_aida64
from pprint import pprint
import json
from volume import get_volume
from MQTT import Send_MQTT_Discovery,Update_State_data

debug = False


# 发送音量信息
def send_volume():
    volume = get_volume()
    Update_State_data(volume,"volume","number")



# 初始化Aida64数据
def get_aida64_data():
    global aida64_data
    aida64_data = python_aida64.getData()
    if aida64_data == None:
        print("11")


# 发送Aida64传感器数据
def send_aida64():
    get_aida64_data()
    Update_State_data(json.dumps(aida64_data),"","sensor")


# 发送传感器信息
def send_data():
    info = "发送数据成功"
    # 音量数据
    try:
        send_volume()
    except:
        print("找不到扬声器")
        info = "扬声器获取错误"
    # Aida64数据
    send_aida64()
    return info



# 发现设备
def discovery():
    get_aida64_data()

    info = ""
    id1 = 0
    id2 = 0
    id3 = 0
    id4 = 0

    print("发送Discovery MQTT信息")
    for category, items in aida64_data.items():
        if category == "temp":
            for item in items:
                name = item["label"]
                name_id = item["id"]
                info += Send_MQTT_Discovery(category, id1, name, name_id,is_aida64=True)+"\n"
                id1 = id1 + 1
        if category == "pwr":
            for item in items:
                name = item["label"]
                name_id = item["id"]
                info += Send_MQTT_Discovery(category, id2, name, name_id,is_aida64=True)+"\n"
                id2 = id2 + 1
        if category == "fan":
            for item in items:
                name = item["label"]
                name_id = item["id"]
                info += Send_MQTT_Discovery(category, id3, name, name_id,is_aida64=True)+"\n"
                id3 = id3 + 1
        if category == "sys":
            for item in items:
                name = item["label"]
                name_id = item["id"]
                info += Send_MQTT_Discovery(category, id4, name, name_id,is_aida64=True) + "\n"
                id4 = id4 + 1
    
    info = "发现了" + str(id1 + id2 + id3 + id4) + "个实体\n" + info
    return info



if __name__ == "__main__":
    get_aida64_data()
    pprint(aida64_data)
    discovery()
    time.sleep(1)
    send_data()
