import threading
import sched
import time
from Update_State_Data import send_data
from logger_manager import Logger
from config_manager import load_config,set_config,get_config

logger = Logger(__name__)

class PeriodicTask:
    def __init__(self, function=None):
        interval = get_config("interval")
        self.interval = interval
        logger.debug(f"定时器初始化,上报间隔 {interval} 秒")
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
    logger.debug(f"MQTT定时器上报数据\n {result}")
    
periodic_task = PeriodicTask(function=tasks)

def start_task():
    periodic_task.start()

def stop_task():
    periodic_task.stop()

if __name__ == "__main__":
    periodic_task.start()

