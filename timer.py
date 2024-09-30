import threading
import sched
import time
from MQTT_publish import send_data, discovery
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
        self.stop_event = threading.Event()
        self.lock = threading.Lock()

    def _run(self):
            next_run_time = time.time()
            while not self.stop_event.is_set():
                now = time.time()
                if now >= next_run_time:
                    with self.lock:
                        self.event = self.scheduler.enter(0, 1, self.function)
                    self.scheduler.run(blocking=False)
                    next_run_time = now + self.interval
                
                time.sleep(1)

    def start(self):
        if not self.thread.is_alive():
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._run)
            self.thread.start()

    def stop(self):
        self.stop_event.set()
        with self.lock:
            if self.event:
                try:
                    self.scheduler.cancel(self.event)
                except ValueError:
                    pass
        self.thread.join()

def tasks():
    result = send_data()
    # print(result)
    
periodic_task = PeriodicTask(function=tasks)

def start_task():
    periodic_task.start()

def stop_task():
    periodic_task.stop()
