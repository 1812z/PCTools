import inspect
import logging
import sys
import os


class Logger:
    # 定义日志级别映射
    LEVEL_MAP = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    # 颜色代码定义
    _COLORS = {
        'DEBUG': '\033[36m',  # 青色
        'INFO': '\033[32m',  # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',  # 红色
        'CRITICAL': '\033[1;31m',  # 亮红色
        'RESET': '\033[0m'  # 重置颜色
    }

    def __init__(self, name: str = None, level: int = logging.DEBUG, log_file: str = None):
        self.base_name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        if not self.logger.handlers:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.encoding = 'utf-8'


            class CallerAwareFormatter(logging.Formatter):
                def format(self, record):
                    record.name = getattr(record, 'caller_name', record.name)
                    message = super().format(record)
                    return f"{Logger._COLORS.get(record.levelname, '')}{message}{Logger._COLORS['RESET']}"

            formatter = CallerAwareFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

            # 如果提供了日志文件路径，添加文件handler
            if log_file:
                file_handler = logging.FileHandler(log_file, mode='w',encoding='utf-8')  # mode='w'表示覆盖写入
                file_handler.setLevel(level)
                # 文件日志使用不包含颜色的格式
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                file_handler.setFormatter(file_formatter)
                self.logger.addHandler(file_handler)

    def _get_caller_name(self) -> str:
        """
        获取调用者文件名
        """
        stack = inspect.stack()
        for frame_info in stack[3:]:
            frame = frame_info.frame
            file_path = frame.f_globals.get('__file__', '')

            # 跳过日志系统本身的文件和core.py
            if not file_path or 'logging' in file_path or 'core.py' in file_path:
                continue

            filename = os.path.splitext(os.path.basename(file_path))[0]
            return filename

        return self.base_name


    def _log_with_caller(self, level: int, message: str):
        caller_name = self._get_caller_name()
        self.logger.log(level, message, extra={'caller_name': caller_name})

    def set_level(self, level: str) -> None:
        level_upper = level.upper()
        if level_upper in self.LEVEL_MAP:
            self.logger.setLevel(self.LEVEL_MAP[level_upper])
            for handler in self.logger.handlers:
                handler.setLevel(self.LEVEL_MAP[level_upper])
        else:
            self.logger.warning(f"Invalid log level: {level}. Using default level.")

    def debug(self, message: str) -> None:
        self._log_with_caller(logging.DEBUG, message)

    def info(self, message: str) -> None:
        self._log_with_caller(logging.INFO, message)

    def warning(self, message: str) -> None:
        self._log_with_caller(logging.WARNING, message)

    def error(self, message: str) -> None:
        self._log_with_caller(logging.ERROR, message)

    def critical(self, message: str) -> None:
        self._log_with_caller(logging.CRITICAL, message)