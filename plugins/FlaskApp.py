import time
import numpy as np
import cv2
from flask import Flask, Response
import multiprocessing
import signal
import os
import mss

app = Flask(__name__)

@app.route('/screenshot.jpg')
def get_screenshot():
    with mss.mss() as sct:
        # 获取主显示器截图
        monitor = sct.monitors[1]
        screenshot = np.array(sct.grab(monitor))

        # 优化1：调整分辨率（可选）
        if screenshot.shape[1] > 1920:  # 如果宽度大于1920则缩小
            screenshot = cv2.resize(screenshot, (1920, 1080))

        # 优化2：高效JPEG编码
        _, buffer = cv2.imencode('.jpg', screenshot, [
            cv2.IMWRITE_JPEG_QUALITY, 80,  # 质量调整为80（50-100）
            cv2.IMWRITE_JPEG_OPTIMIZE, 1  # 启用JPEG优化
        ])

        # 直接返回内存中的字节数据，避免使用BytesIO
        return Response(buffer.tobytes(), mimetype='image/jpeg')

@app.route('/screen')
def get_screen():
    return Response(generate_screenshots(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


def generate_screenshots():
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # 获取主显示器
        while True:
            # 使用mss快速截图
            screenshot = np.array(sct.grab(monitor))

            # 转换为JPEG格式
            _, buffer = cv2.imencode('.jpg', screenshot,
                                     [cv2.IMWRITE_JPEG_QUALITY, 70])
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.05)

def generate_frames():
    camera = cv2.VideoCapture(2)
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
    app.run(host=host, port=port,debug=False)


class FlaskApp:
    def __init__(self, core, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.process = None
        self.core = core

    def start(self):
        if self.process is None:
            try:
                self.process = multiprocessing.Process(
                    target=run_flask_app, args=(self.host, self.port))
                self.process.start()
                self.core.log.info(f"Flask进程启动 http://{self.host}:{self.port}")
            except Exception as e:
                self.core.log.error(f"Flask进程启动失败: {e}")
                
    def stop(self):
        if self.process is not None:
            os.kill(self.process.pid, signal.SIGTERM)
            self.process.join()
            self.process = None
            self.core.log.info("Flask进程停止")


if __name__ == "__main__":
    manager = FlaskApp('0.0.0.0', 5000)
    manager.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        manager.stop()
