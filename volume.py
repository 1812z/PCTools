from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
import comtypes


def init():
    global volume
    comtypes.CoInitialize()
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = interface.QueryInterface(IAudioEndpointVolume)

init()
def get_volume():

    current_volume = volume.GetMasterVolumeLevelScalar()
    comtypes.CoUninitialize()
    return current_volume * 100 //1

def set_volume(level):
    if(level == 0):
        volume.SetMute(1, None)
    else:
        volume.SetMute(0, None)
        volume.SetMasterVolumeLevelScalar(level,None)
    comtypes.CoUninitialize()

if __name__ == "__main__":
    print(get_volume())




