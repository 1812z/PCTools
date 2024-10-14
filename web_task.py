import io
import time
import pyautogui
import cv2
from flask import Flask, Response
import multiprocessing
import signal
import os

app = Flask(__name__)


@app.route('/screenshot.jpg')
def get_screenshot():
    return Response(generate_screenshots(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


def generate_screenshots():
    while True:
        screenshot = pyautogui.screenshot()
        img_byte_array = io.BytesIO()
        screenshot.save(img_byte_array, format='JPEG', quality=50)
        img_byte_array.seek(0)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + img_byte_array.read() + b'\r\n')
        time.sleep(0.3)


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
    app.run(host=host, port=port)


class FlaskAppManager:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.process = None

    def start(self):
        if self.process is None:
            self.process = multiprocessing.Process(
                target=run_flask_app, args=(self.host, self.port))
            self.process.start()
            print(f"Flask进程启动 http://{self.host}:{self.port}")

    def stop(self):
        if self.process is not None:
            os.kill(self.process.pid, signal.SIGTERM)
            self.process.join()
            self.process = None
            print("Flask进程停止")


if __name__ == "__main__":
    manager = FlaskAppManager('192.168.44.236', 5000)
    manager.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        manager.stop()
