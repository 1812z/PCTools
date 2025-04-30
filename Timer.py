import asyncio
import inspect
import threading
import sched
import time


class PeriodicTask:
    def __init__(self, core,function=None, interval=None, name="UnnamedTask"):
        self.core = core
        self.interval = interval if interval is not None else self.core.config.get_config("interval")
        self.name = name
        self.core.log.debug(f"定时器 {self.name} 初始化, 上报间隔 {self.interval} 秒")
        self.function = function
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.thread = None
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.event = None
        self.core.log = self.core.log
        self.is_async = inspect.iscoroutinefunction(function)

    def _run(self):
        next_run_time = time.time()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while not self.stop_event.is_set():
            now = time.time()
            if now >= next_run_time:
                with self.lock:
                    if not self.stop_event.is_set():  # 获取锁后再次检查
                        if self.is_async:
                            # 如果是异步函数，使用特殊的包装函数
                            self.event = self.scheduler.enter(0, 1, self._run_async_function, ())
                        else:
                            # 同步函数保持原样
                            self.event = self.scheduler.enter(0, 1, self.function, ())

                self.scheduler.run(blocking=False)
                next_run_time = now + self.interval
                self.core.log.debug(
                    f"🕛定时器 {self.name} 下次执行时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(next_run_time))}")

            time.sleep(1)

        # 关闭事件循环
        loop.close()

    def _run_async_function(self):
        """运行异步函数的包装器"""
        loop = asyncio.get_event_loop()
        try:
            # 运行异步函数直到完成
            future = asyncio.ensure_future(self.function(), loop=loop)
            loop.run_until_complete(future)
        except Exception as e:
            self.core.log.error(f"❌ 异步定时任务 {self.name} 执行失败: {e}")


    def start(self):
        if self.thread is None or not self.thread.is_alive():
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._run, name=f"TimerThread-{self.name}")
            self.thread.start()
            self.core.log.info(f"🕛定时器 {self.name} 已启动")

    def stop(self):
        self.stop_event.set()
        with self.lock:
            if self.event:
                try:
                    self.scheduler.cancel(self.event)
                except ValueError:
                    pass
        if self.thread and self.thread.is_alive():
            self.thread.join()
        self.core.log.info(f"定时器 {self.name} 已停止")

    def update_interval(self, new_interval):
        with self.lock:
            self.interval = new_interval
        self.core.log.info(f"🕛定时器 {self.name} 间隔已更新为 {new_interval} 秒")


class TimerManager:
    def __init__(self, core):
        self.core = core
        self.timers = {}
        self.core.log = core.log

    def create_timer(self, name, function, interval=None ):
        if name in self.timers:
            raise ValueError(f"定时器 {name} 已存在")
        self.timers[name] = PeriodicTask(self.core, function=function, interval=interval, name=name)
        return self.timers[name]

    def get_timer(self, name):
        return self.timers.get(name)

    def start_timer(self, name):
        timer = self.timers.get(name)
        if timer:
            timer.start()
        else:
            raise ValueError(f"定时器 {name} 不存在")

    def stop_timer(self, name):
        timer = self.timers.get(name)
        if timer:
            timer.stop()
        else:
            raise ValueError(f"定时器 {name} 不存在")

    def remove_timer(self, name):
        timer = self.timers.pop(name, None)
        if timer:
            timer.stop()
        else:
            raise ValueError(f"定时器 {name} 不存在")

    def update_timer_interval(self, name, new_interval):
        timer = self.timers.get(name)
        if timer:
            timer.update_interval(new_interval)
        else:
            raise ValueError(f"定时器 {name} 不存在")


# Example usage
if __name__ == "__main__":
    def task1():
        print(f"Task 1 executed at {time.strftime('%H:%M:%S')}")


    def task2():
        print(f"Task 2 executed at {time.strftime('%H:%M:%S')}")


    manager = TimerManager()

    # Create two timers with different intervals
    manager.create_timer("fast_timer", task1, interval=3)
    manager.create_timer("slow_timer", task2, interval=1)

    # Start the timers
    manager.start_timer("fast_timer")
    manager.start_timer("slow_timer")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Stop the timers when interrupted
        manager.stop_timer("fast_timer")
        manager.stop_timer("slow_timer")