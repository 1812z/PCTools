import json
import time
import paho.mqtt.client as mqtt
from config_manager import load_config,set_config,get_config
from logger_manager import Logger

global mqttc,initialized
initialized = False
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
logger = Logger(__name__)
subscribed_topics = []


def on_connect(client, userdata, flags, reason_code, properties):
    global initialized
    if reason_code.is_failure:
        logger.error(f"连接MQTT服务器失败: {reason_code} 尝试重新连接..")    
    else:
        logger.info(f"成功连接到: {broker}")
        if subscribed_topics:
            re_subscribe()

def on_connect_fail(reason_code):
    logger.error(f"连接 {broker}:{port} 失败,错误码:{reason_code},请检查MQTT配置")

def on_message(client, userdata, data):
    userdata.append(data.payload)
    message = data.payload.decode()
    if fun2:
        from Execute_Command import MQTT_Command
        MQTT_Command(data.topic, message)
    logger.debug(f"MQTT主题: `{data.topic}` 消息: `{message}` ")


# 初始化MQTT
def init_data():
    global initialized
    if initialized:
        return
    global json_data, device_name, broker, fun2, port
    # 读取账号密码
    json_data = load_config()
    username = get_config("username")
    password = get_config("password")
    broker = get_config("HA_MQTT")
    port = get_config("HA_MQTT_port")
    device_name = get_config("device_name")
    fun2 = get_config("fun2")
    mqttc.user_data_set([])
    mqttc._username = username
    mqttc._password = password
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    mqttc.on_connect_fail = on_connect_fail
    initialized = True
    try:
        mqttc.connect(broker,port)
    except:
        logger.error(f"连接 {broker}:{port} 失败,请检查MQTT配置")



# device_class HA设备类型
# topic_id 数据编号，默认空
# name 实体名称
# name_id 实体唯一标识符
# type 实体类型 默认sensor
def Send_MQTT_Discovery(device_class=None, topic_id=None,name='Sensor1', name_id='', type="sensor",is_aida64=False):
    global device_name
    init_data()
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
            "sw_version": "2025.4.3",
            "configuration_url": "https://1812z.top"
        }
    }

    #超时时间
    timeout = 30
    # 在线主题
    discovery_data["availability_topic"] = f"homeassistant/{device_name}/availability"

    # 发现主题
    discovery_topic = f"homeassistant/{type}/{device_name}{name_id}/config"

    # 实体信息标记
    discovery_data["name"] = name
    discovery_data["device"]["name"] = device_name
    discovery_data["device"]["identifiers"] = [device_name]
    discovery_data["object_id"] = device_name + name_id
    discovery_data["unique_id"] = device_name + name_id

    # 数据编号模板处理
    if topic_id is not None:
        discovery_data["value_template"] = f"{{{{value_json.{device_class}[{topic_id}].value}}}}"

    base_topic = f"homeassistant/{type}/{device_name}"
    match (type, is_aida64):
        case ('sensor', True):
            discovery_data["state_topic"] = f"{base_topic}/state"
            discovery_data["expire_after"]= timeout

        case ('sensor', False):
            discovery_data["state_topic"] = f"{base_topic}{name_id}/state"
        
        case ('button', _):
            discovery_data["command_topic"] = f"{base_topic}{name_id}/set"
        
        case ('number', _):
            discovery_data.update({
                "command_topic": f"{base_topic}{name_id}/set",
                "state_topic": f"{base_topic}{name_id}/state"
            })
        
        case ('light', _):
            discovery_data.update({
                "command_topic": f"{base_topic}{name_id}/set",
                "brightness_state_topic": f"{base_topic}{name_id}/state",
                "brightness_command_topic": f"{base_topic}{name_id}/set"
            })
        
        case ('binary_sensor', _):
            discovery_data.update({
                "state_topic": f"{base_topic}{name_id}/state",
                "payload_on": "ON",
                "payload_off": "OFF"
            })
        
        case ('text', _):
                discovery_data["command_topic"] = f"{base_topic}{name_id}/set"
       

    
   # 子类型处理
    match device_class:
        case "pwr":
            discovery_data.update({
                "device_class": "power",
                "unit_of_measurement": "W"
            })
        
        case "fan":
            discovery_data.update({
                "device_class": "speed",
                "unit_of_measurement": "RPM"
            })
        
        case "sys":
            discovery_data.pop('device_class', None)
            if "Disk" in name:
                discovery_data["icon"] = "mdi:harddisk"
                if "Activity" in name:
                    discovery_data["unit_of_measurement"] = "%"
                else:
                    discovery_data["unit_of_measurement"] = "KB/s"
            elif "NIC" in name:
                discovery_data["icon"] = "mdi:"
                if "Total" in name:
                    discovery_data["unit_of_measurement"] = "M"
                    discovery_data["icon"] = "mdi:check-network"
                else:
                    discovery_data["unit_of_measurement"] = "KB/s"
                    if "Download" in name:
                        discovery_data["icon"] = "mdi:download-network"
                    elif "Upload" in name:
                        discovery_data["icon"] = "mdi:upload-network"
            elif "Time" in name:
                discovery_data["icon"] = "mdi:clock-outline"
            elif "Clock" in name:
                discovery_data["unit_of_measurement"] = "MHz"
            else:
                discovery_data["unit_of_measurement"] = "%"
                if "gpu" in name.lower():
                    if "momory" in name:
                        discovery_data["unit_of_measurement"] = "MB"
                    discovery_data["icon"] = "mdi:expansion-card"
                elif "memory" in name.lower():
                    discovery_data["icon"] = "mdi:memory"
                elif "cpu" in name.lower():
                    discovery_data["icon"] = "mdi:cpu-64-bit"
                                        
        case "temp":
            discovery_data.update({
                "device_class": "temperature",
                "unit_of_measurement": "°C"
            })
        
        case "volt":
            discovery_data['device_class'] = "voltage"
            discovery_data["unit_of_measurement"] = "V"

 
    # 发送信息
    info = f"发现主题: {discovery_topic}"
    mqttc.publish(discovery_topic, json.dumps(discovery_data))
    return info

  
# 发送自定义消息
def Publish_MQTT_Message(topic, message, qos=0):
    init_data()
    mqttc.publish(topic, message,qos)

# 更新状态数据
def Update_State_data(data,topic,type):
    init_data()
    if type == "number":
        state_topic = f"homeassistant/number/{device_name}{topic}/state"
        Publish_MQTT_Message(state_topic, str(data))
    elif type == "sensor":
        state_topic = f"homeassistant/sensor/{device_name}{topic}/state"
        Publish_MQTT_Message(state_topic, data)
    elif type == "light":
        state_topic = f"homeassistant/light/{device_name}{topic}/state"
        Publish_MQTT_Message(state_topic, data)


def MQTT_Subcribe(topic):
    init_data()
    mqttc.subscribe(topic)
    subscribed_topics.append(topic)


def re_subscribe():
    logger.warning("MQTT重连成功,重新订阅主题")
    for topic in subscribed_topics:
        mqttc.subscribe(topic)


# MQTT 进程管理
def start_mqtt():
    init_data()
    try:
        mqttc.loop_start()
        timer = 0
        while (timer <= 5):
            time.sleep(1)
            timer += 1
            if mqttc.is_connected():
                logger.debug("MQTT订阅进程启动成功")
                return 0
            elif timer == 5:
                return 1     
    except:
        logger.error("MQTT连接失败,请检查服务器配置")


def stop_mqtt_loop():
    mqttc.loop_stop()


if __name__ == '__main__':
    start_mqtt()
    input("TEST:\n")
