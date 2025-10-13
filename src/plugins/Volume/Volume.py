from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
import comtypes

class Volume:
    def __init__(self, core):
        self.core = core
        self.volume = None
        self.updater = {
            "timer": 60
        }
        self.config = [
            {
                "name": "音量",
                "entity_type": "number",
                "entity_id": "level",
                "icon": "mdi:volume-high"
            }]

    def init(self):
        comtypes.CoInitialize()
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = interface.QueryInterface(IAudioEndpointVolume)

    def get_status(self):
        try:
            self.init()
            current_volume = self.volume.GetMasterVolumeLevelScalar()
            comtypes.CoUninitialize()
            return current_volume * 100 // 1
        except comtypes.COMError:
            self.core.log.warning("找不到扬声器")
            return None

    def set_volume(self, level:int):
        try:
            self.init()
            if level == 0:
                self.volume.SetMute(1, None)
            else:
                self.volume.SetMute(0, None)
                self.volume.SetMasterVolumeLevelScalar(max(0.0, min(1.0, level / 100.0)), None)
            comtypes.CoUninitialize()
        except comtypes.COMError:
            self.core.log.warning("找不到扬声器")
            return None

    def update_state(self):
        status = self.get_status()
        topic = f"Volume_level"
        self.core.mqtt.update_state_data(status, topic, "number")
        return f"音量更新: {status}"

    def handle_mqtt(self, topic, data):
        self.set_volume(int(data))
