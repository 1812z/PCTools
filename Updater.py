import os
import sys
import json
import requests
import zipfile
import subprocess
from packaging import version

# 配置信息
REPO_OWNER = "1812z"
REPO_NAME = "PCTools"
CONFIG_EXAMPLE_FILE = "config_example.json"

def load_current_version():
    try:
        with open(CONFIG_EXAMPLE_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("version", "0.0.0")
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        print(f"无法读取 {CONFIG_EXAMPLE_FILE} 或缺少版本号，默认使用 0.0.0")
        return "0.0.0"

def get_latest_release():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None


def download_asset(asset_url, save_path):
    headers = {"Accept": "application/octet-stream"}
    response = requests.get(asset_url, headers=headers, stream=True)
    if response.status_code == 200:
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    return False


def extract_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)


def main():
    print("检查更新...")
    current_version = load_current_version()
    latest_release = get_latest_release()
    if not latest_release:
        print("无法获取最新版本信息")
        return

    latest_version = latest_release["tag_name"]
    asset_name = f"PCTools_{latest_version}_Windows_x64.zip"

    # 使用packaging.version进行版本号比较
    if version.parse(latest_version) > version.parse(current_version):
        print(f"发现新版本: {latest_version} (当前版本: {current_version})")

        # 查找指定的asset
        target_asset = None
        for asset in latest_release.get("assets", []):
            if asset["name"] == asset_name:
                target_asset = asset
                break

        if target_asset:
            print(f"正在下载 {asset_name}...")
            zip_path = os.path.join(os.getcwd(), asset_name)
            if download_asset(target_asset["browser_download_url"], zip_path):
                print("下载完成，准备更新...")

                # 创建更新脚本
                update_script = f"""import os
import shutil
import time
import zipfile

zip_path = r"{zip_path}"
extract_to = os.path.dirname(zip_path)

time.sleep(2)

with zipfile.ZipFile(zip_path, "r") as zip_ref:
    zip_ref.extractall(extract_to)

os.remove(zip_path)

print("Success")
"""
                # 写入更新脚本
                with open("updater.py", "w") as f:
                    f.write(update_script)

                # 启动更新进程
                subprocess.Popen([sys.executable, "updater.py"])
                print("主进程即将退出，更新进程将在后台运行...")
                sys.exit(0)
            else:
                print("下载失败")
        else:
            print(f"未找到 {asset_name} 资源")
    else:
        print(f"当前已是最新版本,当前版本{current_version},目标版本{latest_version}")


if __name__ == "__main__":
    main()
