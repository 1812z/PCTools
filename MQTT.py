import asyncio
import inspect
import json

import paho.mqtt.client as mqtt

class MQTT:
    def __init__(self, core):
        self.core = core
        self.mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.subscribed_topics = []

        self.read_config()

        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_message = self.on_message
        self.mqttc.on_connect_fail = self.on_connect_fail
        self.mqttc.on_disconnect = self.on_disconnect

        self.connect_broker()

    def on_disconnect(self, *args):
        if args[3] == "Normal disconnection":
            self.core.log.info(f"MQTT断开连接")
        else:
            self.core.log.error(f"MQTT断开连接 | 原因: {args[3]}")

    def read_config(self):
        self.device_name = self.core.config.get_config("device_name")
        self.broker = self.core.config.get_config("HA_MQTT")
        self.username = self.core.config.get_config("username")
        self.port = self.core.config.get_config("HA_MQTT_port")
        self.password = self.core.config.get_config("password")
        self.prefix = self.core.config.get_config("ha_prefix")

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            self.core.log.error(f"连接MQTT服务器失败: {reason_code} 尝试重新连接..")
        else:
            self.core.log.info(f"MQTT成功连接到: {self.broker}:{self.port}")
            if self.subscribed_topics:
                self.re_subscribe()

    def on_connect_fail(self, reason_code):
        self.core.log.error(f"连接 {self.broker}:{self.port} 失败,错误码:{reason_code},请检查MQTT配置")


    def on_message(self, client, userdata, data):
        message = data.payload.decode()
        self.handle_mqtt_message(data.topic,message)
        self.core.log.debug(f"MQTT主题: `{data.topic}` 消息: `{message}` ")


    # device_class HA子设备类型
    # num 数据编号，默认空
    # name 实体名称
    # entity_id 实体唯一标识符
    # entity_type 实体类型 默认sensor
    def send_mqtt_discovery(self, device_class=None, num=None, name='Sensor1', entity_id='', entity_type="sensor", is_aida64=False, icon = None):
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
                "sw_version": "2025.4.26",
                "configuration_url": "https://1812z.top"
            }
        }

        # 超时时间
        timeout = 30
        # 在线主题
        discovery_data["availability_topic"] = f"{self.prefix}/{self.device_name}/availability"

        # 发现主题
        discovery_topic = f"{self.prefix}/{entity_type}/{self.device_name}_{entity_id}/config"

        # 实体信息标记
        discovery_data["name"] = name
        discovery_data["device"]["name"] = self.device_name
        discovery_data["device"]["identifiers"] = [self.device_name]
        discovery_data["object_id"] = f"{self.device_name}_{entity_id}"
        discovery_data["unique_id"] = f"{self.device_name}_{entity_id}"
        if icon:
            discovery_data["icon"] = icon

        # 数据编号模板处理
        if num is not None:
            discovery_data["value_template"] = f"{{{{value_json.{device_class}[{num}].value}}}}"

        base_topic = f"{self.prefix}/{entity_type}/{self.device_name}"
        match (entity_type, is_aida64):
            case ('sensor', True):
                discovery_data["state_topic"] = f"{base_topic}_Aida64/state"
                discovery_data["expire_after"] = timeout

            case ('sensor', False):
                discovery_data["state_topic"] = f"{base_topic}_{entity_id}/state"

            case ('button', _):
                discovery_data["command_topic"] = f"{base_topic}_{entity_id}/set"
                self.mqtt_subscribe(discovery_data["command_topic"])

            case ('switch', _):
                discovery_data.update({
                    "command_topic": f"{base_topic}_{entity_id}/set",
                    "state_topic": f"{base_topic}_{entity_id}/state",
                    "payload_on": "ON",
                    "payload_off": "OFF"
                })
                self.mqtt_subscribe(discovery_data["command_topic"])

            case ('number', _):
                discovery_data.update({
                    "command_topic": f"{base_topic}_{entity_id}/set",
                    "state_topic": f"{base_topic}_{entity_id}/state"
                })
                self.mqtt_subscribe(discovery_data["command_topic"])

            case ('light', _):
                discovery_data.update({
                    "command_topic": f"{base_topic}_{entity_id}/set",
                    "brightness_state_topic": f"{base_topic}_{entity_id}/state",
                    "brightness_command_topic": f"{base_topic}_{entity_id}/set"
                })
                self.mqtt_subscribe(discovery_data["command_topic"])
                self.mqtt_subscribe(discovery_data["brightness_command_topic"])

            case ('binary_sensor', _):
                discovery_data.update({
                    "state_topic": f"{base_topic}_{entity_id}/state",
                    "payload_on": "ON",
                    "payload_off": "OFF"
                })

            case ('text', _):
                discovery_data["command_topic"] = f"{base_topic}_{entity_id}/set"
                self.mqtt_subscribe(discovery_data["command_topic"])

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
                if "Utilization" in name:
                    discovery_data["unit_of_measurement"] = "%"
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
                elif "Volume" in name:
                    discovery_data["unit_of_measurement"] = "%"
                    discovery_data["icon"] = "mdi:volume-high"
                else:
                    if "GPU" in name:
                        if "Memory" in name:
                            discovery_data["unit_of_measurement"] = "MB"
                        discovery_data["icon"] = "mdi:expansion-card"
                    elif "Memory" in name:
                        discovery_data["unit_of_measurement"] = "%"
                        discovery_data["icon"] = "mdi:memory"
                    elif "CPU" in name:
                        discovery_data["unit_of_measurement"] = "%"
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
        info = f"实体: {name} 发现主题: {discovery_topic}"
        self.core.log.debug(info)
        self.mqttc.publish(discovery_topic, json.dumps(discovery_data))
        return info


    # 发送自定义消息
    def publish(self, topic, message, qos=0):
        self.mqttc.publish(topic, message, qos)

    def keepalive(self, state: bool = True):
        if state:
            if self.core.timer.get_timer("keepalive") is None:
                self.core.timer.create_timer("keepalive",self.keepalive,29)
            self.core.timer.start_timer("keepalive")
            self.mqttc.publish(f"{self.prefix}/{self.device_name}/availability","online")
        else:
            self.core.timer.stop_timer("keepalive")
            self.mqttc.publish(f"{self.prefix}/{self.device_name}/availability", "offline")

    # 更新状态数据
    def update_state_data(self, data, topic, type):
        match type:
            case "number":
                state_topic = f"{self.prefix}/number/{self.device_name}_{topic}/state"
                self.publish(state_topic, str(data))
            case "sensor":
                state_topic = f"{self.prefix}/sensor/{self.device_name}_{topic}/state"
                self.publish(state_topic, data)
            case "light":
                state_topic = f"{self.prefix}/light/{self.device_name}_{topic}/state"
                self.publish(state_topic, data)
            case "switch":
                state_topic = f"{self.prefix}/switch/{self.device_name}_{topic}/state"
                self.publish(state_topic, data)


    def mqtt_subscribe(self, topic):
        self.mqttc.subscribe(topic)
        self.subscribed_topics.append(topic)


    def re_subscribe(self):
        self.core.log.info("MQTT连接成功,重新订阅主题")
        for topic in self.subscribed_topics:
            self.mqttc.subscribe(topic)

    def handle_mqtt_message(self, topic: str, payload: dict):
        """
        处理MQTT消息并路由到对应模块
        :param topic: MQTT主题 (如 "homeassistant/light/PC_Twinkle_Tray_0/set")
        :param payload: 消息内容 (字典格式)
        """
        # 提取模块名（匹配loaded_plugins中的模块）
        module_name = None
        for plugin in self.core.plugin_instances.keys():
            # 查找主题中是否包含插件名（如 "Twinkle_Tray"）
            if f"_{plugin}_" in topic or topic.endswith(f"_{plugin}"):
                module_name = plugin
                s = topic.split('/')
                entity = '_'.join(s[2].split('_')[1:])
                entity = entity.replace(f"{module_name}_","")
                break

        if not module_name:
            self.core.log.warning(f"⚠️ 未找到匹配的模块: {module_name}")
            return

        # 获取模块实例
        module_instance = getattr(self.core, module_name, None)
        if not module_instance:
            self.core.log.warning(f"⚠️ 模块未加载: {module_name}")
            return

        # 构建处理方法名（如 "Twinkle_Tray_handle_mqtt"）
        handler_name = "handle_mqtt"
        handler = getattr(module_instance, handler_name, None)

        if not handler:
            self.core.log.warning(f"⚠️ 模块 {module_name} 未实现处理方法 {handler_name}")
            return

        # 调用处理方法
        try:
            # 检查是否为协程函数
            if inspect.iscoroutinefunction(handler):
                # 如果是异步函数，使用协程方式调用
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(handler(entity, payload))
            else:
                # 如果是同步函数，直接调用
                handler(entity, payload)

            self.core.log.info(f"📦 {module_name} 实体: {entity} 状态: {payload}")
        except Exception as e:
            self.core.log.error(f"❌ 处理MQTT消息失败: {str(e)}")

    def connect_broker(self):
        try:
            if not self.mqttc.is_connected():
                self.mqttc.user_data_set([])
                self.mqttc._username = self.username
                self.mqttc._password = self.password
                self.mqttc.connect(self.broker, self.port)
            else:
                self.core.log.warning("MQTT已连接")
        except ValueError:
            self.core.log.error("MQTT配置信息错误，请检查地址端口是否正确")
        except TimeoutError:
            self.core.log.error("MQTT连接超时，请检查网络连接")
        except OSError:
            self.core.log.error("MQTT连接失败，无法访问目标服务器")

    # MQTT 进程管理
    def start_mqtt(self):
        if not self.mqttc.is_connected():
            self.connect_broker()
        self.mqttc.loop_start()


    def stop_mqtt(self):
        self.mqttc.loop_stop()


    def reconnect(self):
        self.read_config()
        self.core.log.info(f"MQTT重连配置: {self.broker}:{self.port}")
        self.mqttc.disconnect()
        self.connect_broker()

