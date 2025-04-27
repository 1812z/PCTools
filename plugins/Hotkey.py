import json
import keyboard
import time

class Hotkey:
    def __init__(self, core):
        self.core = core
        self.listening = False

        self.hotkey_notify = self.core.config.get_config("hotkey_notify")
        self.suppress = self.core.config.get_config("suppress")
        self.device_name = self.core.config.get_config("device_name")
        self.prefix = self.core.config.get_config("ha_prefix")
        self.load_hotkeys()


    def send_discovery(self, hotkeys):
        info = "快捷键发现: \n"
        for hotkey in hotkeys:
            name_id = "hotkey" + hotkey.replace("+", "-")
            self.core.mqtt.send_mqtt_discovery(name=hotkey, entity_id=name_id, entity_type="binary_sensor")
            info = info + hotkey
        time.sleep(0.5)
        self.init_binary_sensor(hotkeys)
        return info
    
    
    def init_binary_sensor(self, hotkeys):
        for hotkey in hotkeys:
            hotkey: str
            topic = f"{self.prefix}/binary_sensor/{self.device_name}_Hotkey_{hotkey.replace("+", "-")}/state"
            self.core.mqtt.publish(topic, "OFF")

    
    def save_hotkey(self, hotkey):
        existing_hotkeys = self.load_hotkeys()
        if hotkey not in existing_hotkeys:
            with open('hotkeys.txt', 'a') as file:
                file.write(hotkey + '\n')
                self.core.log.info(f"保存快捷键: {hotkey}")
        else:
            self.core.log.info(f"快捷键 '{hotkey}' 已存在，未保存。")
    
    
    def capture_hotkeys(self):
        self.core.log.info("开始捕获快捷键，按 'esc' 停止捕获...")
        captured_hotkeys = []
    
        def record_hotkey():
            hotkey = keyboard.read_event().name
            if hotkey != 'esc':
                captured_hotkeys.append(hotkey)
                self.core.log.info(f"捕获到快捷键: {captured_hotkeys}")
    
        while True:
            event = keyboard.read_event()
            if event.event_type == keyboard.KEY_DOWN:
                if event.name == 'esc':
                    break
                record_hotkey()
    
        hotkey_join = '+'.join(captured_hotkeys)
        self.save_hotkey(hotkey_join)
        return hotkey_join
    
    
    def load_hotkeys(self):
        try:
            with open('hotkeys.txt', 'r') as file:
                self.hotkeys = [line.strip() for line in file.readlines()]
                return self.hotkeys
        except FileNotFoundError:
            self.core.log.error("hotkeys.txt加载失败")
            return []
    
    
    def command(self,h: str):
        key_list = h.split('+')
        for item in key_list:
            keyboard.release(item)
        self.core.log.debug("触发了快捷键:", h)
        if self.hotkey_notify:
            self.show_toast("PCTools", "触发了快捷键:" + h)
        topic = f"homeassistant/binary_sensor/{self.device_name}hotkey{h.replace("+", "-")}/state"
        self.core.mqtt.publish(topic, "ON")
        time.sleep(1)
        self.core.mqtt.publish(topic, "OFF")
    
    
    def start(self):
        if not self.listening:
            listening = True
            self.send_discovery(self.hotkeys)
            self.core.log.info(f"开始监听快捷键...{self.hotkeys}")
            for hotkey in self.hotkeys:
                keyboard.add_hotkey(hotkey, lambda h=hotkey: self.command(h), suppress=self.suppress, trigger_on_release=False)
            # keyboard.wait('esc')
            return 0
        return 1
    
    
    def stop(self):
        if self.listening:
            self.listening = False
            for hotkey in self.hotkeys:
                keyboard.remove_hotkey(hotkey)
            self.core.log.info("已停止监听快捷键")
            return 0
        return 1
