from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL



def init():
    global volume
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = interface.QueryInterface(IAudioEndpointVolume)

def get_volume():
    init()
    current_volume = volume.GetMasterVolumeLevelScalar()
    return current_volume * 100 //1

def set_volume(level):
    init()
    if(level == 0):
        volume.SetMute(1, None)
    else:
        volume.SetMute(0, None)
        volume.SetMasterVolumeLevelScalar(level,None)



