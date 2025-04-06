import time
from Twinkle_Tray import get_monitors_state
import python_aida64
import json
from volume import get_volume
from MQTT import Send_MQTT_Discovery,Update_State_data,Publish_MQTT_Message
from logger_manager import Logger
from config_manager import load_config,set_config,get_config

debug = False
logger = Logger(__name__)

def init():
        global device_name
        device_name = get_config("device_name")

        
# 发送音量信息
def send_volume():
    volume = get_volume()
    Update_State_data(volume, "volume", "number")
    return volume


# 初始化Aida64数据
def get_aida64_data():
    global aida64_data
    aida64_data = python_aida64.getData()
    if aida64_data == None:
        logger.error("Aida64数据读取失败")


# 发送Aida64传感器数据
def send_aida64():
    get_aida64_data()
    data = json.dumps(aida64_data)
    Update_State_data(data, "", "sensor")
    return data
    
# 发送显示器数据
def send_monitor_state():
    monitors = get_monitors_state()
    for monitor_num, monitor_info in monitors.items():
        Update_State_data(monitor_info.get("Brightness")*255/100, "monitor" + str(monitor_num), "light")
    return monitor_info

# 发送传感器信息
def send_data(aida64=True, volume=True, monitor=True):
    info = "发送数据成功"
    # 音量数据
    if volume:
        info += f"音量:{send_volume()}\n"
    # Aida64数据
    if aida64:
        info += f"Aida64:{send_aida64()}\n"
    # 显示器亮度数据
    if monitor:
        try:
            info += f"显示器:{send_monitor_state()}\n"
        except:
            logger.error("显示器数据读取失败")
    # 心跳包
    Publish_MQTT_Message(f"homeassistant/{device_name}/availability","online")
    logger.debug(info)
    return info


# 发现设备
def discovery_aida64():
    get_aida64_data()
    if aida64_data is None:
        logger.error("Aida64数据读取失败")
        return "Aida64数据读取失败"
    # 使用字典管理各类别的计数器
    category_counters = {
        'temp': 0,
        'pwr': 0,
        'fan': 0,
        'sys': 0,
        'volt': 0
    }
    
    info_lines = []
  
    for category, items in aida64_data.items():
        if category not in category_counters:
            continue
            
        for item in items:
            name = item["label"]
            name_id = item["id"]
            
            # 发送MQTT发现信息并记录结果
            discovery_msg = Send_MQTT_Discovery(
                device_class=category,
                topic_id=category_counters[category],
                name=name,
                name_id=name_id,
                is_aida64=True
            )
            info_lines.append(discovery_msg)
            category_counters[category] += 1

    total_entities = sum(category_counters.values())
    summary = f"发现了{total_entities}个实体"
    logger.info(f"发送Aida64实体 Discovery MQTT信息,共{total_entities}个实体")
    return f"{summary}\n" + "\n".join(info_lines)

init()

if __name__ == "__main__":
    discovery_aida64()
    time.sleep(1)
    print(send_data())

