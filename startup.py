import os
import sys
import win32com.client

def add_to_startup(script_name='gui.py'):
    # 获取当文件夹路径
    startup_folder = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
    pythonw_executable = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
    script_path = os.path.abspath(script_name)

    # 获取快捷方式保存路径
    shortcut_path = os.path.join(startup_folder, f'{os.path.splitext("PCTools")[0]}.lnk')

    # 创建快捷方式
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortcut(shortcut_path)

    # 设置快捷方式
    shortcut.TargetPath = pythonw_executable
    shortcut.Arguments = f'"{script_path}"'
    shortcut.WorkingDirectory = os.path.dirname(script_path)

    # 保存快捷方式
    shortcut.Save()

    print(f"{script_name} 已成功加入开机启动项")


def remove_from_startup(script_name='gui.py'):
    # 获取文件夹路径
    startup_folder = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
    shortcut_path = os.path.join(startup_folder, f'{os.path.splitext("PCTools")[0]}.lnk')

    # 检查快捷方式是否存在
    if os.path.exists(shortcut_path):
        os.remove(shortcut_path)
        print(f"{script_name} 已成功从开机启动项移除")
    else:
        print(f"未找到 {script_name} 的启动项")


if __name__ == "__main__":
    add_to_startup()