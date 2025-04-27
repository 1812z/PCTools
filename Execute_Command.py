import importlib
import json
import os
import subprocess
import sys
from Toast import show_toast
from plugins.Volume import set_volume
from plugins.Twinkle_Tray import get_monitors_state
from Update_State_Data import send_data
from logger_manager import Logger

logger = Logger(__name__)

def init_data():
    global current_directory
    current_file_path = os.path.abspath(__file__)
    current_directory = os.path.dirname(current_file_path)
    current_directory = os.path.join(current_directory, "commands")
    # print(current_directory)
    # 命令映射表
    with open('commands.json', 'r', encoding='utf-8') as file:
        global command_data
        global count_entities
        command_data = json.load(file)
        count_entities = command_data.get("count")
    # 读取账号密码
    with open('config.json', 'r') as file:
        global json_data
        global device_name
        json_data = json.load(file)
        device_name = json_data.get("device_name")


init_data()


def MQTT_Command(command, data):
    if command == device_name + "/messages":
        show_toast("HA通知", data)
        return
    key = command.split('/')[2]
    run_file = command_data.get(key)


    if key == device_name + "volume":  # 音量控制
        volume = int(data) / 100
        set_volume(volume)
        send_data(False, True, False)
        logger.info(f"设置音量至: {volume}")
    else:                              # 运行程序
        file_type = run_file.split('.')[1]
        if file_type == "lnk":  # 快捷方式
            logger.info("命令:" + key + "打开快捷方式:" + run_file)
            run = current_directory + '\\' + run_file
            # os.system(f'start "" "{run}"')
            subprocess.Popen(['explorer', run])
        elif file_type == "bat":  # 批处理文件
            bat_file = current_directory + '\\' + run_file
            subprocess.Popen(
                bat_file, creationflags=subprocess.CREATE_NO_WINDOW)
        elif file_type == "py":
            Python_File(current_directory + '\\' + run_file)
        else:  # 其它文件
            run = current_directory + '\\' + run_file
            os.system(f'start "" "{run}"')
    

def Python_File(run_file):
    logger.info("执行PY文件:" + run_file)

    file_path = os.path.join(os.path.dirname(
        __file__), 'commands', f'{run_file}')

    # 动态加载文件
    spec = importlib.util.spec_from_file_location(run_file, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[run_file] = module
    spec.loader.exec_module(module)

    if hasattr(module, 'fun'):
        module.fun()
    else:
        logger.info(f"模块 {run_file} 中没有名为 'fun' 的函数")
