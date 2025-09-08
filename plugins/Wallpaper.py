import os
import subprocess
from typing import Optional


class Wallpaper:
    def __init__(self, core=None):
        self.core = core
        self.exe_path = self._find_wallpaper_engine_path()

        self.config = [{
                'name': '暂停壁纸',
                'entity_type': 'button',
                'entity_id': 'pause',
                'icon': 'mdi:wallpaper'
            },
            {
                'name': '停止壁纸',
                'entity_type': 'button',
                'entity_id': 'stop',
                'icon': 'mdi:wallpaper'
            },
            {
                'name': '播放壁纸',
                'entity_type': 'button',
                'entity_id': 'play',
                'icon': 'mdi:wallpaper'
            },
            {
                'name': '壁纸静音',
                'entity_type': 'button',
                'entity_id': 'mute',
                'icon': 'mdi:wallpaper'
            },
            {
                'name': '壁纸取消静音',
                'entity_type': 'button',
                'entity_id': 'unmute',
                'icon': 'mdi:wallpaper'
            }
        ]


    def _find_wallpaper_engine_path(self) -> Optional[str]:
        """检测wallpaper.exe的安装路径"""
        common_paths = [
            r"C:\Program Files (x86)\Steam\steamapps\common\wallpaper_engine",
            r"D:\Program Files (x86)\Steam\steamapps\common\wallpaper_engine"
        ]
        if self.core.config.get_config("wallpaper_engine_path"):
            return self.core.config.get_config("wallpaper_engine_path")

        for path in common_paths:
            exe_path = os.path.join(path, "wallpaper64.exe")
            if os.path.exists(exe_path):
                return exe_path

            exe_path = os.path.join(path, "wallpaper32.exe")
            if os.path.exists(exe_path):
                return exe_path

        return None

    def launch(self) -> bool:
        """启动Wallpaper Engine"""
        if not self.exe_path:
            return False

        try:
            subprocess.Popen([self.exe_path])
            return True
        except Exception:
            return False

    def shell(self, command) -> bool:
        if not self.exe_path:
            return False
        try:
            subprocess.run([self.exe_path, "-control", command])
            return True
        except Exception:
            return False

    def handle_mqtt(self, key, data):
        if self.shell(key):
            self.core.log.info(f"Wallpaper_Engine命令: {key} 执行成功")
        else:
            self.core.log.error(f"Wallpaper_Engine命令: {key} 执行失败")

