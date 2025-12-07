from pycaw.pycaw import AudioUtilities
from comtypes import CoInitialize, CoUninitialize, COMError


class Volume:
    def __init__(self, core):
        self.core = core
        self.volume = None
        self.updater = {"timer": 60}
        self.config = [
            {
                "name": "音量",
                "entity_type": "number",
                "entity_id": "level",
                "icon": "mdi:volume-high"
            }
        ]

    def init(self):
        CoInitialize()
        device = AudioUtilities.GetSpeakers()   # 自动获取默认扬声器
        self.volume = device.EndpointVolume     # 新版 pycaw 官方方式

    def get_status(self):
        try:
            self.init()
            vol = self.volume.GetMasterVolumeLevelScalar()
            CoUninitialize()
            return int(vol * 100)
        except COMError:
            self.core.log.warning("找不到扬声器")
            return None

    def set_volume(self, level: int):
        try:
            self.init()
            if level == 0:
                self.volume.SetMute(1, None)
            else:
                self.volume.SetMute(0, None)
                self.volume.SetMasterVolumeLevelScalar(
                    max(0.0, min(1.0, level / 100.0)), None
                )
            CoUninitialize()
        except COMError:
            self.core.log.warning("找不到扬声器")
            return None

    def update_state(self):
        status = self.get_status()
        topic = "Volume_level"
        self.core.mqtt.update_state_data(status, topic, "number")
        return f"音量更新: {status}"

    def handle_mqtt(self, topic, data):
        self.set_volume(int(data))
