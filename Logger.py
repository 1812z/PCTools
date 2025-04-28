import logging
import sys


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
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[1;31m', # 亮红色
        'RESET': '\033[0m'      # 重置颜色
    }

    def __init__(self, name: str = 'root', level: int = logging.DEBUG):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # 防止重复添加handler
        if not self.logger.handlers:
            # 创建控制台handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)

            # 设置日志格式
            class ColoredFormatter(logging.Formatter):
                def format(self, record):
                    message = super().format(record)
                    return f"{Logger._COLORS.get(record.levelname, '')}{message}{Logger._COLORS['RESET']}"

            formatter = ColoredFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)

            self.logger.addHandler(console_handler)

    def set_level(self, level: str) -> None:
        level_upper = level.upper()
        if level_upper in self.LEVEL_MAP:
            self.logger.setLevel(self.LEVEL_MAP[level_upper])
            for handler in self.logger.handlers:
                handler.setLevel(self.LEVEL_MAP[level_upper])
        else:
            self.logger.warning(f"Invalid log level: {level}. Using default level.")


    def debug(self, message: str) -> None:
        self.logger.debug(message)

    def info(self, message: str) -> None:
        self.logger.info(message)

    def warning(self, message: str) -> None:
        self.logger.warning(message)

    def error(self, message: str) -> None:
        self.logger.error(message)

    def critical(self, message: str) -> None:
        self.logger.critical(message)