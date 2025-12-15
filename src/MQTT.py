import paho.mqtt.client as mqtt
from ha_mqtt_discoverable import Settings, DeviceInfo
from ha_mqtt_discoverable.sensors import SensorInfo, Sensor


class MQTT:
    def __init__(self, core):
        """
        初始化MQTT连接管理器
        :param core: Core实例
        """
        self.core = core
        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.subscribed_topics = {}

        # 读取配置
        self.device_name = self.core.config.get_config("device_name")
        self.broker = self.core.config.get_config("HA_MQTT")
        self.username = self.core.config.get_config("username")
        self.port = self.core.config.get_config("HA_MQTT_port")
        self.password = self.core.config.get_config("password")
        self.prefix = self.core.config.get_config("ha_prefix")

        # 设置回调
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_connect_fail = self.on_connect_fail
        self.mqtt_client.on_disconnect = self.on_disconnect

        self.status = [-1, "init"]
        self.version_entity = None
        self.version_timer = None  # 版本实体心跳定时器

    def get_mqtt_settings(self):
        """
        获取 MQTT 配置（用于 ha-mqtt-discoverable）
        :return: Settings.MQTT 对象
        """
        return Settings.MQTT(
            client=self.mqtt_client,
            discovery_prefix=self.prefix,
            state_prefix=self.prefix,
        )

    def get_device_info(self, **kwargs):
        """
        获取设备信息（用于 ha-mqtt-discoverable）
        :param kwargs: 可选参数覆盖默认值
            - manufacturer: 制造商
            - model: 型号
            - sw_version: 软件版本
            - configuration_url: 配置URL
        :return: DeviceInfo 对象
        """
        # 默认值
        defaults = {
            "manufacturer": "1812z",
            "model": "PCTools",
            "sw_version": "7.0.0",
            "configuration_url": "https://github.com/1812z/PCTools"
        }

        # 合并用户提供的参数
        defaults.update(kwargs)

        return DeviceInfo(
            identifiers=[self.device_name],
            name=self.device_name,
            manufacturer=defaults["manufacturer"],
            model=defaults["model"],
            sw_version=defaults["sw_version"],
            configuration_url=defaults.get("configuration_url"),
        )

    def on_connect(self, client, userdata, flags, reason_code, properties):
        """连接成功回调"""
        if reason_code.is_failure:
            self.core.log.error(f"连接MQTT服务器失败: {reason_code} 尝试重新连接..")
            self.status = [1, f"连接失败: {reason_code}"]
        else:
            self.core.log.info(f"MQTT成功连接到: {self.broker}:{self.port}")
            self.status = [0, f"connected to {self.broker}:{self.port}"]

            # 更新GUI状态（如果存在）
            if hasattr(self.core, 'gui') and self.core.gui is not None:
                self.core.gui.logic.update_home_status()

            # 配置插件实体
            self.core.config_plugin_entities()

            # 创建并启动版本实体
            self.create_version_entity()
            self.start_version_heartbeat()

    def on_connect_fail(self, client, userdata):
        """连接失败回调"""
        self.core.log.error(f"连接 {self.broker}:{self.port} 失败，请检查MQTT配置")
        self.status = [1, f"连接 {self.broker}:{self.port} 失败"]

        # 更新GUI状态（如果存在）
        if hasattr(self.core, 'gui') and self.core.gui is not None:
            self.core.gui.logic.update_home_status()

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        """断开连接回调"""
        if reason_code == 0 or str(reason_code) == "Normal disconnection":
            self.core.log.info(f"MQTT断开连接")
            self.status = [0, f"MQTT断开连接"]
        else:
            self.core.log.error(f"MQTT断开连接 | 原因: {reason_code}")
            self.status = [1, f"MQTT断开连接| 原因: {reason_code}"]

        # 更新GUI状态（如果存在）
        if hasattr(self.core, 'gui') and self.core.gui is not None:
            self.core.gui.logic.update_home_status()

    def on_message(self, client, userdata, msg):
        """
        接收到MQTT消息时的回调
        将消息路由到对应的订阅回调函数
        """
        topic = msg.topic
        payload = msg.payload.decode()

        self.core.log.debug(f"MQTT主题: `{topic}` 消息: `{payload}`")

    def publish(self, topic, payload, qos=0, retain=False):
        """
        发布MQTT消息
        :param topic: 主题
        :param payload: 消息内容（支持str, bytes, dict, list）
        :param qos: QoS等级 (0, 1, 2)
        :param retain: 是否保留消息
        :return: 是否发布成功
        """
        try:
            if not self.mqtt_client or not self.mqtt_client.is_connected():
                self.core.log.error(f"MQTT未连接，无法发布消息到 {topic}")
                return False

            # 处理不同类型的payload
            if isinstance(payload, (dict, list)):
                import json
                payload = json.dumps(payload)
            elif not isinstance(payload, (str, bytes)):
                payload = str(payload)

            result = self.mqtt_client.publish(topic, payload, qos, retain)

            if result.rc == 0:
                self.core.log.debug(f"MQTT消息发送成功: {topic}")
                return True
            else:
                self.core.log.error(f"MQTT消息发送失败: {topic}, rc={result.rc}")
                return False

        except Exception as e:
            self.core.log.error(f"MQTT发布异常: {topic}, 错误: {e}")
            return False

    def subscribe(self, topic, callback=None, qos=0):
        """
        订阅MQTT主题
        :param topic: 主题（支持通配符 + 和 #）
        :param callback: 回调函数，接收参数 (topic, payload)
        :param qos: QoS等级
        :return: 是否订阅成功
        """
        try:
            result = self.mqtt_client.subscribe(topic, qos)

            if result[0] == 0:
                if callback:
                    self.subscribed_topics[topic] = callback
                self.core.log.debug(f"订阅MQTT主题成功: {topic}")
                return True
            else:
                self.core.log.error(f"订阅MQTT主题失败: {topic}, rc={result[0]}")
                return False

        except Exception as e:
            self.core.log.error(f"订阅MQTT主题异常: {topic}, 错误: {e}")
            return False

    def unsubscribe(self, topic):
        """
        取消订阅MQTT主题
        :param topic: 主题
        :return: 是否取消成功
        """
        try:
            result = self.mqtt_client.unsubscribe(topic)

            if result[0] == 0:
                if topic in self.subscribed_topics:
                    del self.subscribed_topics[topic]
                self.core.log.debug(f"取消订阅MQTT主题成功: {topic}")
                return True
            else:
                self.core.log.error(f"取消订阅MQTT主题失败: {topic}, rc={result[0]}")
                return False

        except Exception as e:
            self.core.log.error(f"取消订阅MQTT主题异常: {topic}, 错误: {e}")
            return False

    def re_subscribe(self):
        """重新订阅所有主题"""
        self.core.log.info("MQTT连接成功，重新订阅主题")
        for topic in self.subscribed_topics.keys():
            self.mqtt_client.subscribe(topic)

    def connect_broker(self):
        """连接到MQTT broker"""
        try:
            if not self.mqtt_client.is_connected():
                self.mqtt_client.user_data_set([])
                self.mqtt_client.username_pw_set(self.username, self.password)
                self.mqtt_client.connect(self.broker, self.port)
                self.core.log.info(f"正在连接MQTT broker: {self.broker}:{self.port}")
            else:
                self.core.log.warning("MQTT已连接")
        except ValueError as e:
            self.core.log.error(f"MQTT配置信息错误: {e}")
        except TimeoutError:
            self.core.log.error("MQTT连接超时，请检查网络连接")
        except OSError as e:
            self.core.log.error(f"MQTT连接失败，无法访问目标服务器: {e}")

    def start_mqtt(self):
        """启动MQTT服务"""
        if not self.mqtt_client.is_connected():
            self.connect_broker()
        self.mqtt_client.loop_start()
        self.core.log.info("MQTT服务已启动")

    def stop_mqtt(self):
        """停止MQTT服务"""
        # 停止版本心跳定时器
        self.stop_version_heartbeat()

        # 设置版本实体为不可用
        if self.version_entity:
            try:
                self.version_entity.set_availability(False)
                self.core.log.info("版本实体已设置为不可用")
            except Exception as e:
                self.core.log.error(f"设置版本实体不可用失败: {e}")

        self.mqtt_client.loop_stop()
        self.core.log.info("MQTT服务已停止")

    def reconnect(self):
        """重新连接MQTT broker"""
        self.core.log.info(f"MQTT重连配置: {self.broker}:{self.port}")
        self.mqtt_client.disconnect()
        self.connect_broker()

    def is_connected(self):
        """检查MQTT是否已连接"""
        return self.mqtt_client.is_connected()

    def create_version_entity(self):
        """创建版本实体"""
        if self.version_entity is not None:
            self.core.log.debug("版本实体已存在，跳过创建")
            return

        version_info = SensorInfo(
            name="online_version",
            unique_id=f"{self.core.mqtt.device_name}_PCTools",
            object_id=f"{self.core.mqtt.device_name}_PCTools",
            device=self.get_device_info(),
            expire_after=30  # 30秒后自动不可用
        )

        version_settings = Settings(
            mqtt=self.get_mqtt_settings(),
            entity=version_info,
            manual_availability=True
        )

        self.version_entity = Sensor(version_settings)
        self.version_entity.set_availability(True)
        self.version_entity.set_state(self.core.config.version)
        self.core.log.info(f"版本实体已创建: {self.core.config.version}")

    def update_version_state(self):
        """更新版本实体状态（心跳）"""
        if self.version_entity and self.mqtt_client.is_connected():
            try:
                self.version_entity.set_availability(True)
                self.version_entity.set_state(self.core.config.version)
                self.core.log.debug(f"版本实体心跳更新: {self.core.config.version}")
            except Exception as e:
                self.core.log.error(f"更新版本实体失败: {e}")

    def start_version_heartbeat(self):
        """启动版本实体心跳定时器"""
        if self.version_timer is None:
            self.version_timer = self.core.timer.create_timer(
                name="version_heartbeat",
                function=self.update_version_state,
                interval=20
            )
            self.version_timer.start()

    def stop_version_heartbeat(self):
        """停止版本实体心跳定时器"""
        if self.version_timer:
            try:
                self.core.timer.stop_timer("version_heartbeat")
                self.core.timer.remove_timer("version_heartbeat")
                self.version_timer = None
                self.core.log.info("版本实体心跳定时器已停止")
            except Exception as e:
                self.core.log.error(f"停止版本实体心跳定时器失败: {e}")