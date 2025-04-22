from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
import comtypes
from logger_manager import Logger

logger = Logger(__name__)

def init():

    global volume
    comtypes.CoInitialize()
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = interface.QueryInterface(IAudioEndpointVolume)


def get_volume():
    try:
        init()
        current_volume = volume.GetMasterVolumeLevelScalar()
        comtypes.CoUninitialize()
        return current_volume * 100 // 1
    except comtypes.COMError:
        logger.error("找不到扬声器")
        return None


def set_volume(level):
    try:
        init()
        if (level == 0):
            volume.SetMute(1, None)
        else:
            volume.SetMute(0, None)
            volume.SetMasterVolumeLevelScalar(level, None)
        comtypes.CoUninitialize()
    except comtypes.COMError:
        logger.error("找不到扬声器")
        return None


if __name__ == "__main__":
    print(get_volume())
