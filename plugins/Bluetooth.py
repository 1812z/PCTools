from winsdk.windows.devices import radios


class Bluetooth:
    def __init__(self, core):
        self.core = core
        self.updater = {
            "timer": 600
        }
        self.config =  [
            {
                "name": "蓝牙",
                "entity_type": "switch",
                "entity_id": "Power",
                "icon": "mdi:bluetooth"
            }
        ]
    # 蓝牙电源管理
    async def bluetooth_power(self, turn_on):
        all_radios = await radios.Radio.get_radios_async()
        for this_radio in all_radios:
            if this_radio.kind == radios.RadioKind.BLUETOOTH:
                if turn_on:
                    self.core.mqtt.update_state_data("ON", "Bluetooth_Power", "switch")
                    return await this_radio.set_state_async(radios.RadioState.ON)
                else:
                    self.core.mqtt.update_state_data("OFF", "Bluetooth_Power", "switch")
                    return await this_radio.set_state_async(radios.RadioState.OFF)


    async def handle_mqtt(self, entity, payload):
        if payload == "ON":
            result = await self.bluetooth_power(True)
            self.core.log.info(f"蓝牙设备: ON {result}")
        else:
            result = await self.bluetooth_power(False)
            self.core.log.info(f"蓝牙设备: OFF {result}")

    # 更新蓝牙状态
    async def update_state(self):
        all_radios = await radios.Radio.get_radios_async()
        for this_radio in all_radios:
            if this_radio.kind == radios.RadioKind.BLUETOOTH:
                state =  "ON" if this_radio.state == radios.RadioState.ON else "OFF"
                self.core.mqtt.update_state_data(state, "Bluetooth_Power", "switch")
                return
        self.core.log.error("找不到蓝牙设备")



