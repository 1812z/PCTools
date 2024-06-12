import threading
import sched
import time
from aida64 import send_data,discovery
import json

def read_config():
    with open('config.json', 'r') as file:
        config = json.load(file)
    return config.get('interval', 10)  # 默认间隔为10秒

class PeriodicTask:
    def __init__(self, interval=None, function=None):
        self.interval = interval or read_config()
        self.function = function
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.thread = threading.Thread(target=self._run)
        self.event = None
        self.stop_event = threading.Event()

    def _run(self):
        while not self.stop_event.is_set():
            self.event = self.scheduler.enter(self.interval, 1, self.function)
            self.scheduler.run()

    def start(self):
        if not self.thread.is_alive():
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._run)
            self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.event:
            self.scheduler.cancel(self.event)
        self.thread.join()

def tasks():
    send_data()
    
periodic_task = PeriodicTask(function=tasks)

def start_task():
    print("启动监控服务..")
    periodic_task.start()

def stop_task():
    periodic_task.stop()
