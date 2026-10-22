"""
系统音量控制插件
"""
from pycaw.pycaw import AudioUtilities
from comtypes import CoInitialize, CoUninitialize, COMError
from ha_mqtt_discoverable.sensors import Number, NumberInfo
from ha_mqtt_discoverable import Settings
from paho.mqtt.client import Client as MQTTClient


class Volume:
    def __init__(self, core):
        """
        初始化 Volume 插件
        :param core: PCTools Core 实例
        """
        self.core = core
        self.log = core.log
        self.volume = None
        self._com_initialized = False
        self.updater = {"timer": 60}

        # MQTT 实体
        self.volume_number = None

    def setup_entities(self):
        """设置 MQTT 实体"""
        try:
            mqtt_settings = self.core.mqtt.get_mqtt_settings()
            device_info = self.core.mqtt.get_device_info(
                plugin_name="Volume",
                model="PCTools Volume"
            )

            # 创建音量数字实体
            number_info = NumberInfo(
                name="volume",
                unique_id=f"{self.core.mqtt.device_name}_volume_level",
                object_id=f"{self.core.mqtt.device_name}_volume_level",
                device=device_info,
                icon="mdi:volume-high",
                display_name="音量",
                min=0,
                max=100,
                step=1,
                mode="slider"
            )

            number_settings = Settings(
                mqtt=mqtt_settings,
                entity=number_info
            )

            self.volume_number = Number(
                number_settings,
                command_callback=self.handle_volume_command
            )

            # 初始化时获取当前音量并更新状态
            current_volume = self.get_status()
            if current_volume is not None:
                self.volume_number.set_value(current_volume)
            else:
                # 如果获取失败，设置默认值以触发发现
                self.volume_number.set_value(50)

            self.log.info("Volume MQTT 实体创建成功")

        except Exception as e:
            self.log.error(f"创建 Volume MQTT 实体失败: {e}")

    def init(self):
        """初始化音频设备"""
        CoInitialize()
        self._com_initialized = True
        device = AudioUtilities.GetSpeakers()   # 自动获取默认扬声器
        self.volume = device.EndpointVolume     # 新版 pycaw 官方方式

    def release(self):
        """释放 COM 引用（与 init() 配对，避免泄漏）"""
        self.volume = None
        if self._com_initialized:
            self._com_initialized = False
            try:
                CoUninitialize()
            except Exception:
                pass

    def get_status(self):
        """获取当前音量（0 表示静音，其余为 1-100）"""
        try:
            self.init()
            muted = bool(self.volume.GetMute())
            vol = self.volume.GetMasterVolumeLevelScalar()
            return 0 if muted else int(round(vol * 100))
        except COMError:
            self.log.warning("找不到扬声器")
            return None
        finally:
            self.release()

    def set_volume(self, level: int):
        """
        设置音量
        :param level: 0-100，0 表示静音（不改动 master 音量）
        :return: True 成功 / False 失败
        """
        try:
            self.init()
            if level <= 0:
                self.volume.SetMute(1, None)
            else:
                self.volume.SetMute(0, None)
                self.volume.SetMasterVolumeLevelScalar(
                    max(0.0, min(1.0, level / 100.0)), None
                )
            self.log.info(f"音量设置为: {level}%")
            return True
        except COMError:
            self.log.warning("找不到扬声器")
            return False
        finally:
            self.release()

    def update_state(self):
        """更新音量状态到 MQTT"""
        status = self.get_status()
        if status is not None and self.volume_number:
            self.volume_number.set_value(status)
            return f"音量更新: {status}%"
        return "音量更新失败"

    def handle_volume_command(self, client: MQTTClient, user_data, message):
        """
        处理音量设置命令（由 ha-mqtt-discoverable 回调）
        :param client: MQTT 客户端
        :param user_data: 用户数据
        :param message: MQTT 消息
        """
        try:
            level = int(round(float(message.payload.decode())))
            level = max(0, min(100, level))
            self.log.info(f"收到音量设置命令: {level}%")

            if not self.set_volume(level):
                # COM 调用失败，不回显，让下一次 update_state 上报真实值
                self.log.error("设置音量失败，跳过状态回显")
                return

            # 回读真实状态：
            # - 静音时回读 0（master 原值不变，但对外语义为 0）
            # - 非静音时回读实际音量，避免 int 截断导致 2→1、1→0
            if self.volume_number:
                actual = self.get_status()
                self.volume_number.set_value(level if actual is None else actual)

        except ValueError as e:
            self.log.error(f"无效的音量值: {message.payload.decode()} - {e}")
        except Exception as e:
            self.log.error(f"处理音量命令失败: {e}")
