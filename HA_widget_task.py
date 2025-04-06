import multiprocessing
from logger_manager import Logger

logger = Logger(__name__)

def run_ha_widget():
    import HA_widget
    HA_widget.main()

def start_ha_widget():
    global process
    process = multiprocessing.Process(target=run_ha_widget)
    process.start()
    logger.info(f"HA_widget.py 已启动，进程ID: {process.pid}")

def stop_ha_widget():
    if process.is_alive():
        logger.info("小部件进程强制终止。")
        process.kill()
    else:
        logger.info("小部件进程已停止。")

if __name__ == "__main__":
    start_ha_widget()

   




