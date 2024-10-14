import multiprocessing


def run_ha_widget():
    import HA_widget
    HA_widget.main()

def start_ha_widget():
    global process
    process = multiprocessing.Process(target=run_ha_widget)
    process.start()
    print(f"HA_widget.py 已启动，进程ID: {process.pid}")

def stop_ha_widget():
    if process.is_alive():
        print("小部件进程强制终止。")
        process.kill()
    else:
        print("小部件进程已停止。")

if __name__ == "__main__":
    start_ha_widget()

   




