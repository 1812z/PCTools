import time
from Twinkle_Tray import get_monitors_state
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

# 发送显示器数据
def send_monitor_state():
    monitors = get_monitors_state()
    for monitor_num, monitor_info in monitors.items():
        Update_State_data(monitor_info.get("Brightness")*255/100,"monitor" + str(monitor_num) ,"light")

# 发送传感器信息
def send_data(aida64=True,volume=True,monitor=True):
    info = "发送数据成功"
    # 音量数据
    if volume:
        send_volume()
    # Aida64数据
    if aida64:
        send_aida64()
    # 显示器亮度数据
    if monitor:
        send_monitor_state()
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
                info += Send_MQTT_Discovery(category, id1, name, name_id,is_aida64=True,timeout=30)+"\n"
                id1 = id1 + 1
        if category == "pwr":
            for item in items:
                name = item["label"]
                name_id = item["id"]
                info += Send_MQTT_Discovery(category, id2, name, name_id,is_aida64=True,timeout=30)+"\n"
                id2 = id2 + 1
        if category == "fan":
            for item in items:
                name = item["label"]
                name_id = item["id"]
                info += Send_MQTT_Discovery(category, id3, name, name_id,is_aida64=True,timeout=30)+"\n"
                id3 = id3 + 1
        if category == "sys":
            for item in items:
                name = item["label"]
                name_id = item["id"]
                info += Send_MQTT_Discovery(category, id4, name, name_id,is_aida64=True,timeout=30) + "\n"
                id4 = id4 + 1
    
    info = "发现了" + str(id1 + id2 + id3 + id4) + "个实体\n" + info
    return info



if __name__ == "__main__":
    get_aida64_data()
    discovery()
    pprint(aida64_data)
    print("音量:",get_volume())
    time.sleep(1)
    send_data()
