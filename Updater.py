# update_checker.py
import os
import sys
import json
import requests
import subprocess
from packaging import version
import flet as ft
from typing import Tuple, Optional


class UpdateChecker:
    def __init__(self, gui, repo_owner: str, repo_name: str, config_file: str):
        self.REPO_OWNER = repo_owner
        self.REPO_NAME = repo_name
        self.CONFIG_FILE = config_file
        self.current_version = "0.0.0"
        self.latest_version = "0.0.0"
        self.update_available = False
        self.latest_release = None
        self.gui = gui

    def load_current_version(self) -> str:
        try:
            with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                self.current_version = config.get("version", "0.0.0")
                return self.current_version
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            print(f"无法读取 {self.CONFIG_FILE} 或缺少版本号，默认使用 0.0.0")
            self.current_version = "0.0.0"
            return self.current_version

    def check_for_updates(self) -> Tuple[bool, Optional[str]]:
        """检查更新并返回是否有更新和最新版本号"""
        self.current_version = self.load_current_version()
        self.latest_release = self.get_latest_release()

        if not self.latest_release:
            return False, None

        self.latest_version = self.latest_release["tag_name"]
        self.update_available = version.parse(self.latest_version) > version.parse(self.current_version)
        self.gui.core.log.info(f"当前版本: {self.current_version}，最新版本: {self.latest_version} 更新状态: {self.update_available}")
        if self.update_available:

            if self.gui.core.config.get_config("auto_update"):
                self.gui.core.show_toast("PCTools更新中",f"最新版本: {self.latest_version}")
                self._perform_update()
            else:
                self.gui.show_snackbar(f"新版本{self.latest_version}可用，转到关于以更新", 4000)
                self.gui.core.show_toast("PCTools新版本可用",f"当前版本: {self.current_version}，最新版本: {self.latest_version}")

        return self.update_available, self.latest_version

    def get_latest_release(self):
        url = f"https://api.github.com/repos/{self.REPO_OWNER}/{self.REPO_NAME}/releases/latest"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None

    def download_asset(self, asset_url: str, save_path: str) -> bool:
        headers = {"Accept": "application/octet-stream"}
        response = requests.get(asset_url, headers=headers, stream=True)
        if response.status_code == 200:
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        return False

    def create_update_ui(self, page: ft.Page) -> ft.Column:
        """创建更新检查UI组件"""
        has_update, latest_ver = self.check_for_updates()

        version_info = ft.Column(
            controls=[
                ft.Text("版本信息", size=18, weight=ft.FontWeight.BOLD),
                ft.Text(f"当前版本: {self.current_version}", size=15),
                ft.Text(f"最新版本: {latest_ver if latest_ver else '未知'}", size=15),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=7
        )

        status_row = ft.Row(alignment=ft.MainAxisAlignment.CENTER)

        if has_update:
            update_btn = ft.ElevatedButton(
                "立即更新",
                icon=ft.Icons.UPDATE,
                on_click=lambda _: self._perform_update()
            )
            status_row.controls.append(update_btn)
        else:
            status_text = ft.Text("当前已是最新版本", color=ft.Colors.BLUE, size=16)
            status_row.controls.append(status_text)

        return ft.Column(
            controls=[version_info, status_row],
            spacing=20,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

    def _perform_update(self):
        if not self.latest_release:
            self.gui.show_snackbar("无法获取发布信息")
            return

        asset_name = f"{self.REPO_NAME}_{self.latest_version}_Windows_x64.zip"
        target_asset = None

        for asset in self.latest_release.get("assets", []):
            if asset["name"] == asset_name:
                target_asset = asset
                break

        if not target_asset:
            self.gui.show_snackbar(f"未找到 {asset_name} 资源")
            return

        self.gui.show_snackbar("正在下载更新...")

        zip_path = os.path.join(os.getcwd(), asset_name)
        if not self.download_asset(target_asset["browser_download_url"], zip_path):
            self.gui.show_snackbar("下载失败")
            return

        self.gui.core.show_toast("下载完成", "即将退出以更新")
        # 创建更新脚本
        update_script = f"""import os
import time
import zipfile

zip_path = r"{zip_path}"
extract_to = os.path.dirname(zip_path)

time.sleep(2)

with zipfile.ZipFile(zip_path, "r") as zip_ref:
    zip_ref.extractall(extract_to)

os.remove(zip_path)
"""
        with open("updater.py", "w") as f:
            f.write(update_script)

        # 启动更新进程
        subprocess.Popen([sys.executable, "updater.py"])
        self.gui.exit()

    def create_update_component(self, page: ft.Page) -> ft.Column:
        """创建并返回更新检查组件"""
        return self.create_update_ui(page)
