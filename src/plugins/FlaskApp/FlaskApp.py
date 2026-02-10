import time
import numpy as np
import cv2
from flask import Flask, Response, request, jsonify
import multiprocessing
import signal
import os
import mss
import requests
import flet as ft
from ha_mqtt_discoverable import Settings
from ha_mqtt_discoverable.sensors import Select, SelectInfo

app = Flask(__name__)
select_monitor = 1  # 默认选择第一个显示器
camera_index = 2


@app.route('/set_monitor/<int:monitor_index>', methods=['GET'])
def set_monitor(monitor_index):
    global select_monitor
    try:
        with mss.mss() as sct:
            if 1 <= monitor_index < len(sct.monitors):
                select_monitor = monitor_index
                return jsonify({'success': True, 'message': f'Monitor set to {monitor_index}'})
            else:
                return jsonify({'success': False, 'message': 'Invalid monitor index'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/screenshot.jpg')
def get_screenshot():
    with mss.mss() as sct:
        monitor = sct.monitors[select_monitor]
        screenshot = np.array(sct.grab(monitor))

        if screenshot.shape[1] > 1920:
            screenshot = cv2.resize(screenshot, (1920, 1080))

        _, buffer = cv2.imencode('.jpg', screenshot, [
            cv2.IMWRITE_JPEG_QUALITY, 80,
            cv2.IMWRITE_JPEG_OPTIMIZE, 1
        ])

        return Response(buffer.tobytes(), mimetype='image/jpeg')


@app.route('/screen')
def get_screen():
    return Response(generate_screenshots(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/set_camera/<int:cam_index>', methods=['GET'])
def set_camera(cam_index):
    global camera_index
    try:
        camera_index = cam_index
        return jsonify({'success': True, 'message': f'Camera set to {cam_index}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


def generate_screenshots():
    with mss.mss() as sct:
        monitor = sct.monitors[select_monitor]
        current_monitor = select_monitor
        while True:
            if current_monitor != select_monitor:
                monitor = sct.monitors[select_monitor]
            screenshot = np.array(sct.grab(monitor))
            _, buffer = cv2.imencode('.jpg', screenshot,
                                     [cv2.IMWRITE_JPEG_QUALITY, 70])
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.05)


def generate_frames():
    global camera_index
    camera = cv2.VideoCapture(camera_index)
    while True:
        success, frame = camera.read()
        if not success:
            with open(r"img/failed.jpeg", "rb") as f:
                frame = f.read()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


def run_flask_app(host, port):
    app.run(host=host, port=port, debug=False)


class FlaskApp:
    def __init__(self, core, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.process = None
        self.core = core
        self.monitor_select = None
        self.camera_select = None
        self.current_monitor = 1
        self.camera_index = 2

        # 获取可用的显示器列表
        self.monitor_options = self.get_monitor_options()

    def get_monitor_options(self):
        """获取可用的显示器选项列表"""
        try:
            with mss.mss() as sct:
                # monitors[0] 是所有显示器的组合，从1开始是真实显示器
                monitor_count = len(sct.monitors) - 1
                # 返回显示器编号列表，如 ["1", "2", "3"]
                return [str(i) for i in range(1, monitor_count + 1)]
        except Exception as e:
            self.core.log.error(f"获取显示器列表失败: {e}")
            return ["1"]  # 默认至少返回一个显示器

    def setup_entities(self):
        """设置MQTT实体"""
        try:
            # 获取MQTT配置
            mqtt_settings = self.core.mqtt.get_mqtt_settings()
            device_info = self.core.mqtt.get_device_info(
                plugin_name="FlaskApp",
                model="PCTools FlaskApp"
            )

            # 创建显示器选择下拉框
            select_info = SelectInfo(
                name="monitor_select",
                unique_id=f"{self.core.mqtt.device_name}_FlaskApp_monitor_select",
                device=device_info,
                icon="mdi:monitor",
                options=self.monitor_options
            )
            select_info.display_name = "显示器选择"

            settings = Settings(mqtt=mqtt_settings, entity=select_info)
            self.monitor_select = Select(settings, command_callback=self.handle_monitor_change)

            # 设置初始选项
            self.monitor_select.select_option(str(self.current_monitor))

            # 创建摄像头选择下拉框
            camera_options = [str(i) for i in range(10)]  # 摄像头选项 0-9

            camera_select_info = SelectInfo(
                name="camera_select",
                unique_id=f"{self.core.mqtt.device_name}_FlaskApp_camera_select",
                device=device_info,
                icon="mdi:camera",
                options=camera_options
            )
            camera_select_info.display_name = "摄像头选择"

            camera_settings = Settings(mqtt=mqtt_settings, entity=camera_select_info)
            self.camera_select = Select(camera_settings, command_callback=self.handle_camera_change)

            # 设置初始摄像头选项
            initial_camera = self.core.get_plugin_config("FlaskApp", "camera_index", 2)
            self.camera_select.select_option(str(initial_camera))

            self.core.log.info(
                f"FlaskApp MQTT实体创建成功，可用显示器: {self.monitor_options}, 摄像头: {camera_options}")
        except Exception as e:
            self.core.log.error(f"FlaskApp MQTT设置失败: {e}")

    def handle_monitor_change(self, client, user_data, message):
        """处理显示器选择变化"""
        try:
            selected_monitor = message.payload.decode()
            monitor_index = int(selected_monitor)
            self.change_monitor(monitor_index)
        except Exception as e:
            self.core.log.error(f"处理显示器选择失败: {e}")

    def handle_camera_change(self, client, user_data, message):
        """处理摄像头选择变化"""
        try:
            selected_camera = message.payload.decode()
            camera_index = int(selected_camera)
            self.change_camera(camera_index)
        except Exception as e:
            self.core.log.error(f"处理摄像头选择失败: {e}")

    def start(self):
        if self.process is None:
            try:
                # 从配置中获取主机和端口
                web_path = self.core.get_plugin_config("FlaskApp", "web_path", "0.0.0.0")
                fps = self.core.get_plugin_config("FlaskApp", "fps", 30)

                self.process = multiprocessing.Process(
                    target=run_flask_app, args=(web_path, self.port))
                self.process.start()
                self.core.log.info(f"Flask进程启动 http://{web_path}:{self.port}，帧率: {fps}")
            except Exception as e:
                self.core.log.error(f"Flask进程启动失败: {e}")

    def stop(self):
        if self.process is not None:
            os.kill(self.process.pid, signal.SIGTERM)
            self.process.join()
            self.process = None
            self.core.log.debug("Flask进程停止")

    def change_monitor(self, index):
        url = f"http://localhost:{self.port}/set_monitor/{index}"
        try:
            response = requests.get(url)
            data = response.json()
            if data['success']:
                global select_monitor
                select_monitor = index
                self.current_monitor = index
                self.core.log.info(f"成功切换到显示器 {index}")
                # 更新Select实体的当前选项
                if self.monitor_select:
                    self.monitor_select.select_option(str(index))
            else:
                self.core.log.error(f"错误: {data['message']}")
        except requests.exceptions.RequestException as e:
            self.core.log.error(f"请求失败: {e}")

    def change_camera(self, index):
        """切换摄像头"""
        url = f"http://localhost:{self.port}/set_camera/{index}"
        try:
            response = requests.get(url)
            data = response.json()
            if data['success']:
                self.camera_index = index
                self.core.log.info(f"成功切换到摄像头 {index}")
                # 更新Select实体的当前选项
                if self.camera_select:
                    self.camera_select.select_option(str(index))
            else:
                self.core.log.error(f"错误: {data['message']}")
        except requests.exceptions.RequestException as e:
            self.core.log.error(f"请求失败: {e}")

    def setting_page(self, e):
        """设置页面"""
        return ft.Column(
            [
                ft.TextField(label="网页URL", width=250,
                             on_submit=self.save_url,
                             value=self.core.get_plugin_config("FlaskApp", "web_path", "0.0.0.0")),
                ft.TextField(label="帧率(FPS)", width=250,
                             on_submit=self.save_fps,
                             value=str(self.core.get_plugin_config("FlaskApp", "fps", 30))),
                ft.Divider(),
                ft.TextField(label="显示器选择", width=250,
                             on_submit=lambda e: self.change_monitor(int(e.control.value)),
                             value=str(self.core.get_plugin_config("FlaskApp", "index", 1))),
                ft.TextField(label="摄像头索引", width=250,
                             on_submit=lambda e: self.change_camera(int(e.control.value)),
                             value=str(self.core.get_plugin_config("FlaskApp", "camera_index", 2))),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def save_url(self, e):
        """保存网页URL"""
        url = e.control.value
        self.core.set_plugin_config("FlaskApp", "web_path", url)
        self.core.log.info(f"网页URL已更新为: {url}")

    def save_secret(self, e):
        """保存网页URL"""
        url = e.control.value
        self.core.set_plugin_config("FlaskApp", "web_path", url)
        self.core.log.info(f"网页URL已更新为: {url}")

    def save_fps(self, e):
        """保存帧率设置"""
        try:
            fps = int(e.control.value)
            if fps <= 0:
                raise ValueError("帧率必须大于0")
            self.core.set_plugin_config("FlaskApp", "fps", fps)
            self.core.log.info(f"帧率已更新为: {fps}")
        except ValueError as e:
            self.core.log.error(f"无效的帧率设置: {e}")