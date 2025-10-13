import asyncio
import inspect
import threading
import time


class PeriodicTask:
    def __init__(self, core, function=None, interval=None, name="UnnamedTask"):
        self.core = core
        self.interval = interval if interval is not None else self.core.config.get_config("interval")
        self.name = name
        self.core.log.debug(f"定时器 {self.name} 初始化, 上报间隔 {self.interval} 秒")
        self.function = function
        self.thread = None
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.is_async = inspect.iscoroutinefunction(function)
        self.loop = None  # 保存事件循环引用

    def _run(self):
        """定时器主循环"""
        next_run_time = time.time()

        # 如果是异步函数，创建事件循环
        if self.is_async:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

        while not self.stop_event.is_set():
            now = time.time()

            if now >= next_run_time:
                try:
                    if self.is_async:
                        # 异步函数
                        self.loop.run_until_complete(self.function())
                    else:
                        # 同步函数
                        self.function()

                    next_run_time = now + self.interval
                    self.core.log.debug(
                        f"🕛定时器 {self.name} 下次执行时间: "
                        f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(next_run_time))}"
                    )
                except Exception as e:
                    self.core.log.error(f"❌ 定时任务 {self.name} 执行失败: {e}")
                    next_run_time = now + self.interval  # 即使失败也要设置下次执行时间

            # 使用更短的休眠时间以提高响应性，但避免过度占用CPU
            sleep_time = min(0.1, max(0.01, next_run_time - time.time()))
            if sleep_time > 0:
                time.sleep(sleep_time)

        # 清理事件循环
        if self.is_async and self.loop:
            self.loop.close()

    def start(self):
        """启动定时器"""
        if self.thread is None or not self.thread.is_alive():
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._run, name=f"TimerThread-{self.name}", daemon=True)
            self.thread.start()
            self.core.log.info(f"🕛定时器 {self.name} 已启动")
        else:
            self.core.log.warning(f"⚠️ 定时器 {self.name} 已在运行")

    def stop(self):
        """停止定时器"""
        if not self.stop_event.is_set():
            self.stop_event.set()
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5)  # 添加超时避免无限等待
                if self.thread.is_alive():
                    self.core.log.warning(f"⚠️ 定时器 {self.name} 停止超时")
            self.core.log.info(f"🕛定时器 {self.name} 已停止")

    def update_interval(self, new_interval):
        """更新定时器间隔"""
        with self.lock:
            self.interval = new_interval
        self.core.log.info(f"🕛定时器 {self.name} 间隔已更新为 {new_interval} 秒")


class TimerManager:
    def __init__(self, core):
        self.core = core
        self.timers = {}
        self.core.log = core.log

    def create_timer(self, name, function, interval=None):
        """创建定时器"""
        if name in self.timers:
            self.core.log.warning(f"⚠️ 定时器 {name} 已存在，将被覆盖")
            self.remove_timer(name)

        self.timers[name] = PeriodicTask(self.core, function=function, interval=interval, name=name)
        return self.timers[name]

    def get_timer(self, name):
        """获取定时器"""
        return self.timers.get(name)

    def start_timer(self, name):
        """启动指定定时器"""
        timer = self.timers.get(name)
        if timer:
            timer.start()
        else:
            self.core.log.error(f"❌ 定时器 {name} 不存在")
            raise ValueError(f"定时器 {name} 不存在")

    def start_all_timers(self):
        """批量启动所有定时器（并行）"""
        threads = []
        for name, timer in self.timers.items():
            thread = threading.Thread(target=timer.start, name=f"Start-{name}")
            thread.start()
            threads.append(thread)

        # 等待所有启动完成
        for thread in threads:
            thread.join(timeout=1)

        self.core.log.info(f"✅ 已启动 {len(self.timers)} 个定时器")

    def stop_timer(self, name):
        """停止指定定时器"""
        timer = self.timers.get(name)
        if timer:
            timer.stop()
        else:
            self.core.log.error(f"❌ 定时器 {name} 不存在")
            raise ValueError(f"定时器 {name} 不存在")

    def stop_all_timers(self):
        """批量停止所有定时器（并行）"""
        threads = []
        for name, timer in self.timers.items():
            thread = threading.Thread(target=timer.stop, name=f"Stop-{name}")
            thread.start()
            threads.append(thread)

        # 等待所有停止完成
        for thread in threads:
            thread.join(timeout=2)

        self.core.log.info(f"✅ 已停止 {len(self.timers)} 个定时器")

    def remove_timer(self, name):
        """移除定时器"""
        timer = self.timers.pop(name, None)
        if timer:
            timer.stop()
            self.core.log.info(f"✅ 定时器 {name} 已移除")
        else:
            self.core.log.warning(f"⚠️ 定时器 {name} 不存在")

    def update_timer_interval(self, name, new_interval):
        """更新定时器间隔"""
        timer = self.timers.get(name)
        if timer:
            timer.update_interval(new_interval)
        else:
            self.core.log.error(f"❌ 定时器 {name} 不存在")
            raise ValueError(f"定时器 {name} 不存在")

    def get_all_timers_status(self):
        """获取所有定时器状态"""
        status = {}
        for name, timer in self.timers.items():
            status[name] = {
                "running": timer.thread and timer.thread.is_alive(),
                "interval": timer.interval,
                "is_async": timer.is_async
            }
        return status
