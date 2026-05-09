"""
Windows HDR 调节插件
支持按显示器开关 HDR，以及调节 HDR 下 SDR 内容亮度
"""
import ctypes
import json
import time
from ctypes import wintypes
import flet as ft

from ha_mqtt_discoverable import Settings
from ha_mqtt_discoverable.sensors import Light, LightInfo, Switch, SwitchInfo
from paho.mqtt.client import Client as MQTTClient


user32 = ctypes.WinDLL("user32", use_last_error=True)


# QueryDisplayConfig flags
QDC_ALL_PATHS = 0x00000001
QDC_ONLY_ACTIVE_PATHS = 0x00000002

# DisplayConfig device info types
DISPLAYCONFIG_DEVICE_INFO_GET_SOURCE_NAME = 1
DISPLAYCONFIG_DEVICE_INFO_GET_TARGET_NAME = 2
DISPLAYCONFIG_DEVICE_INFO_GET_ADVANCED_COLOR_INFO = 9
DISPLAYCONFIG_DEVICE_INFO_SET_ADVANCED_COLOR_STATE = 10
DISPLAYCONFIG_DEVICE_INFO_GET_SDR_WHITE_LEVEL = 11
# 关键：SET_SDR_WHITE_LEVEL 在部分环境需使用内部常量 0xFFFFFFEE
DISPLAYCONFIG_DEVICE_INFO_SET_SDR_WHITE_LEVEL_INTERNAL = 0xFFFFFFEE


class LUID(ctypes.Structure):
    _fields_ = [
        ("LowPart", wintypes.DWORD),
        ("HighPart", wintypes.LONG),
    ]


class DISPLAYCONFIG_RATIONAL(ctypes.Structure):
    _fields_ = [
        ("Numerator", wintypes.UINT),
        ("Denominator", wintypes.UINT),
    ]


class DISPLAYCONFIG_2DREGION(ctypes.Structure):
    _fields_ = [
        ("cx", wintypes.UINT),
        ("cy", wintypes.UINT),
    ]


class DISPLAYCONFIG_PATH_SOURCE_INFO(ctypes.Structure):
    _fields_ = [
        ("adapterId", LUID),
        ("id", wintypes.UINT),
        ("modeInfoIdx", wintypes.UINT),
        ("statusFlags", wintypes.UINT),
    ]


class DISPLAYCONFIG_PATH_TARGET_INFO(ctypes.Structure):
    _fields_ = [
        ("adapterId", LUID),
        ("id", wintypes.UINT),
        ("modeInfoIdx", wintypes.UINT),
        ("outputTechnology", wintypes.UINT),
        ("rotation", wintypes.UINT),
        ("scaling", wintypes.UINT),
        ("refreshRate", DISPLAYCONFIG_RATIONAL),
        ("scanLineOrdering", wintypes.UINT),
        ("targetAvailable", wintypes.BOOL),
        ("statusFlags", wintypes.UINT),
    ]


class DISPLAYCONFIG_PATH_INFO(ctypes.Structure):
    _fields_ = [
        ("sourceInfo", DISPLAYCONFIG_PATH_SOURCE_INFO),
        ("targetInfo", DISPLAYCONFIG_PATH_TARGET_INFO),
        ("flags", wintypes.UINT),
    ]


class DISPLAYCONFIG_MODE_INFO_UNION(ctypes.Union):
    _fields_ = [("raw", ctypes.c_byte * 64)]


class DISPLAYCONFIG_MODE_INFO(ctypes.Structure):
    _fields_ = [
        ("infoType", wintypes.UINT),
        ("id", wintypes.UINT),
        ("adapterId", LUID),
        ("u", DISPLAYCONFIG_MODE_INFO_UNION),
    ]


class DISPLAYCONFIG_DEVICE_INFO_HEADER(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.UINT),
        ("size", wintypes.UINT),
        ("adapterId", LUID),
        ("id", wintypes.UINT),
    ]


class DISPLAYCONFIG_TARGET_DEVICE_NAME_FLAGS(ctypes.Structure):
    _fields_ = [("value", wintypes.UINT)]


class DISPLAYCONFIG_TARGET_DEVICE_NAME(ctypes.Structure):
    _fields_ = [
        ("header", DISPLAYCONFIG_DEVICE_INFO_HEADER),
        ("flags", DISPLAYCONFIG_TARGET_DEVICE_NAME_FLAGS),
        ("outputTechnology", wintypes.UINT),
        ("edidManufactureId", wintypes.USHORT),
        ("edidProductCodeId", wintypes.USHORT),
        ("connectorInstance", wintypes.UINT),
        ("monitorFriendlyDeviceName", wintypes.WCHAR * 64),
        ("monitorDevicePath", wintypes.WCHAR * 128),
    ]


class DISPLAYCONFIG_GET_ADVANCED_COLOR_INFO(ctypes.Structure):
    _fields_ = [
        ("header", DISPLAYCONFIG_DEVICE_INFO_HEADER),
        ("value", wintypes.UINT),
        ("colorEncoding", wintypes.UINT),
        ("bitsPerColorChannel", wintypes.UINT),
    ]


class DISPLAYCONFIG_SET_ADVANCED_COLOR_STATE(ctypes.Structure):
    _fields_ = [
        ("header", DISPLAYCONFIG_DEVICE_INFO_HEADER),
        ("enableAdvancedColor", wintypes.UINT),
    ]


class DISPLAYCONFIG_SDR_WHITE_LEVEL(ctypes.Structure):
    _fields_ = [
        ("header", DISPLAYCONFIG_DEVICE_INFO_HEADER),
        ("SDRWhiteLevel", wintypes.UINT),
    ]


class DISPLAYCONFIG_SET_SDR_WHITE_LEVEL_INTERNAL(ctypes.Structure):
    _fields_ = [
        ("header", DISPLAYCONFIG_DEVICE_INFO_HEADER),
        ("SDRWhiteLevel", wintypes.UINT),
        ("finalValue", ctypes.c_ubyte),
    ]


GetDisplayConfigBufferSizes = user32.GetDisplayConfigBufferSizes
GetDisplayConfigBufferSizes.argtypes = [wintypes.UINT, ctypes.POINTER(wintypes.UINT), ctypes.POINTER(wintypes.UINT)]
GetDisplayConfigBufferSizes.restype = wintypes.LONG

QueryDisplayConfig = user32.QueryDisplayConfig
QueryDisplayConfig.argtypes = [
    wintypes.UINT,
    ctypes.POINTER(wintypes.UINT),
    ctypes.POINTER(DISPLAYCONFIG_PATH_INFO),
    ctypes.POINTER(wintypes.UINT),
    ctypes.POINTER(DISPLAYCONFIG_MODE_INFO),
    ctypes.c_void_p,
]
QueryDisplayConfig.restype = wintypes.LONG

DisplayConfigGetDeviceInfo = user32.DisplayConfigGetDeviceInfo
DisplayConfigGetDeviceInfo.argtypes = [ctypes.POINTER(DISPLAYCONFIG_DEVICE_INFO_HEADER)]
DisplayConfigGetDeviceInfo.restype = wintypes.LONG

DisplayConfigSetDeviceInfo = user32.DisplayConfigSetDeviceInfo
DisplayConfigSetDeviceInfo.argtypes = [ctypes.POINTER(DISPLAYCONFIG_DEVICE_INFO_HEADER)]
DisplayConfigSetDeviceInfo.restype = wintypes.LONG


class HDRAdjust:
    def __init__(self, core):
        self.core = core
        self.log = core.log
        self.updater = {"timer": int(self.core.get_plugin_config("HDRAdjust", "update_interval", 20))}
        self.monitor_lights = {}
        self.hdr_switches = {}
        self.monitor_power_type = int(self.core.get_plugin_config("HDRAdjust", "monitor_power_type", 0))

    def wake_up_screen(self):
        try:
            ctypes.windll.user32.mouse_event(0x0001, 1, 0, 0, 0)
            time.sleep(0.05)
            ctypes.windll.user32.mouse_event(0x0001, -1, 0, 0, 0)
        except Exception:
            pass

    def _turn_off_screen(self):
        ctypes.windll.user32.SendMessageW(0xFFFF, 0x112, 0xF170, 2)

    def _monitor_key(self, adapter_id: LUID, target_id: int):
        return f"{adapter_id.HighPart}_{adapter_id.LowPart}_{target_id}"

    def _enum_active_paths(self):
        path_count = wintypes.UINT(0)
        mode_count = wintypes.UINT(0)
        ret = GetDisplayConfigBufferSizes(QDC_ONLY_ACTIVE_PATHS, ctypes.byref(path_count), ctypes.byref(mode_count))
        if ret != 0:
            raise OSError(f"GetDisplayConfigBufferSizes failed: {ret}")

        paths = (DISPLAYCONFIG_PATH_INFO * path_count.value)()
        modes = (DISPLAYCONFIG_MODE_INFO * mode_count.value)()

        ret = QueryDisplayConfig(
            QDC_ONLY_ACTIVE_PATHS,
            ctypes.byref(path_count),
            paths,
            ctypes.byref(mode_count),
            modes,
            None,
        )
        if ret != 0:
            raise OSError(f"QueryDisplayConfig failed: {ret}")

        return [paths[i] for i in range(path_count.value)]

    def _get_target_name(self, adapter_id: LUID, target_id: int):
        info = DISPLAYCONFIG_TARGET_DEVICE_NAME()
        info.header.type = DISPLAYCONFIG_DEVICE_INFO_GET_TARGET_NAME
        info.header.size = ctypes.sizeof(DISPLAYCONFIG_TARGET_DEVICE_NAME)
        info.header.adapterId = adapter_id
        info.header.id = target_id

        ret = DisplayConfigGetDeviceInfo(ctypes.byref(info.header))
        if ret != 0:
            return f"Display {target_id + 1}"

        name = info.monitorFriendlyDeviceName.strip()
        return name or f"Display {target_id + 1}"

    def _get_hdr_info(self, adapter_id: LUID, target_id: int):
        info = DISPLAYCONFIG_GET_ADVANCED_COLOR_INFO()
        info.header.type = DISPLAYCONFIG_DEVICE_INFO_GET_ADVANCED_COLOR_INFO
        info.header.size = ctypes.sizeof(DISPLAYCONFIG_GET_ADVANCED_COLOR_INFO)
        info.header.adapterId = adapter_id
        info.header.id = target_id

        ret = DisplayConfigGetDeviceInfo(ctypes.byref(info.header))
        if ret != 0:
            return None

        return {
            "advanced_color_supported": bool(info.value & 0x1),
            "advanced_color_enabled": bool(info.value & 0x2),
            "wide_color_enforced": bool(info.value & 0x4),
        }

    def _get_sdr_white_level(self, adapter_id: LUID, target_id: int):
        info = DISPLAYCONFIG_SDR_WHITE_LEVEL()
        info.header.type = DISPLAYCONFIG_DEVICE_INFO_GET_SDR_WHITE_LEVEL
        info.header.size = ctypes.sizeof(DISPLAYCONFIG_SDR_WHITE_LEVEL)
        info.header.adapterId = adapter_id
        info.header.id = target_id

        ret = DisplayConfigGetDeviceInfo(ctypes.byref(info.header))
        if ret != 0:
            return None

        raw = int(info.SDRWhiteLevel)
        # 不同驱动/实现返回值范围不一致，做兼容映射
        if 80 <= raw <= 480:
            level = int((raw - 80) / 4)
        elif 1000 <= raw <= 6000:
            level = int((raw - 1000) / 50)
        else:
            level = raw
        return max(0, min(100, int(level)))

    def _set_hdr_enabled(self, adapter_id: LUID, target_id: int, enabled: bool):
        data = DISPLAYCONFIG_SET_ADVANCED_COLOR_STATE()
        data.header.type = DISPLAYCONFIG_DEVICE_INFO_SET_ADVANCED_COLOR_STATE
        data.header.size = ctypes.sizeof(DISPLAYCONFIG_SET_ADVANCED_COLOR_STATE)
        data.header.adapterId = adapter_id
        data.header.id = target_id
        data.enableAdvancedColor = 1 if enabled else 0

        ret = DisplayConfigSetDeviceInfo(ctypes.byref(data.header))
        if ret != 0:
            raise OSError(f"DisplayConfigSetDeviceInfo HDR failed: {ret}")

    def _set_sdr_white_level_raw(self, adapter_id: LUID, target_id: int, raw_value: int):
        data = DISPLAYCONFIG_SET_SDR_WHITE_LEVEL_INTERNAL()
        data.header.type = DISPLAYCONFIG_DEVICE_INFO_SET_SDR_WHITE_LEVEL_INTERNAL
        data.header.size = ctypes.sizeof(DISPLAYCONFIG_SET_SDR_WHITE_LEVEL_INTERNAL)
        data.header.adapterId = adapter_id
        data.header.id = target_id
        data.SDRWhiteLevel = int(raw_value)
        data.finalValue = 1

        ret = DisplayConfigSetDeviceInfo(ctypes.byref(data.header))
        return ret

    def _set_sdr_white_level(self, target_adapter_id: LUID, target_id: int, level_percent: int):
        value = int(max(0, min(100, level_percent)))
        # 兼容多个可能的驱动映射
        # A: 0..100 -> 1000..6000
        raw_a = 1000 + value * 50
        # B: 0..100 -> 0..100
        raw_b = value
        # C: Twinkle Tray/windows-hdr 常见：0..100 -> 80..480 (nits)
        raw_c = 80 + value * 4
        # D: 某些实现可能要求毫尼特
        raw_d = raw_c * 1000

        # 优先 source id（官方文档），失败则回退 target id
        for raw in (raw_c, raw_a, raw_b, raw_d):
            ret = self._set_sdr_white_level_raw(target_adapter_id, target_id, raw)
            if ret == 0:
                self.log.debug(
                    f"SDR white level set success: adapter={target_adapter_id.HighPart}_{target_adapter_id.LowPart}, "
                    f"id={target_id}, raw={raw}"
                )
                return

        raise OSError("DisplayConfigSetDeviceInfo SDR white level failed: 87")

    def get_hdr_displays(self):
        displays = {}
        paths = self._enum_active_paths()

        for path in paths:
            adapter_id = path.targetInfo.adapterId
            target_id = int(path.targetInfo.id)
            hdr_info = self._get_hdr_info(adapter_id, target_id)
            if not hdr_info or not hdr_info["advanced_color_supported"]:
                continue

            key = self._monitor_key(adapter_id, target_id)
            displays[key] = {
                "adapter_id": adapter_id,
                "target_id": target_id,
                "name": self._get_target_name(adapter_id, target_id),
                "hdr_enabled": hdr_info["advanced_color_enabled"],
                "sdr_brightness": self._get_sdr_white_level(adapter_id, target_id),
            }

        return displays

    def setup_entities(self):
        try:
            mqtt_settings = self.core.mqtt.get_mqtt_settings()
            device_info = self.core.mqtt.get_device_info(
                plugin_name="HDRAdjust",
                model="PCTools HDR Adjust"
            )

            displays = self.get_hdr_displays()
            if not displays:
                self.log.warning("未找到支持 HDR 的显示器")
                return

            for index, (monitor_key, display) in enumerate(displays.items(), start=1):
                safe_key = monitor_key.replace("-", "_")
                light_info = LightInfo(
                    name=f"hdr_display_{index}",
                    unique_id=f"{self.core.mqtt.device_name}_hdr_adjust_{safe_key}",
                    object_id=f"{self.core.mqtt.device_name}_hdr_adjust_{safe_key}",
                    device=device_info,
                    icon="mdi:brightness-6",
                    display_name=f"{display['name']} HDR",
                    brightness=True,
                    retain=False,
                )

                settings = Settings(mqtt=mqtt_settings, entity=light_info)
                light = Light(
                    settings,
                    command_callback=lambda client, user_data, message, key=monitor_key:
                    self.handle_light_command(client, user_data, message, key)
                )
                light.write_config()
                self.monitor_lights[monitor_key] = light

                switch_info = SwitchInfo(
                    name=f"hdr_switch_{index}",
                    unique_id=f"{self.core.mqtt.device_name}_hdr_switch_{safe_key}",
                    object_id=f"{self.core.mqtt.device_name}_hdr_switch_{safe_key}",
                    device=device_info,
                    icon="mdi:high-definition-box",
                    display_name=f"{display['name']} HDR开关",
                )

                switch_settings = Settings(mqtt=mqtt_settings, entity=switch_info)
                hdr_switch = Switch(
                    switch_settings,
                    command_callback=lambda client, user_data, message, key=monitor_key:
                    self.handle_hdr_switch_command(client, user_data, message, key)
                )
                self.hdr_switches[monitor_key] = hdr_switch

            self.update_state()
            self.log.info(f"HDRAdjust MQTT 实体创建成功，共创建 {len(self.monitor_lights)} 个 HDR 显示器实体")

        except Exception as e:
            self.log.error(f"创建 HDRAdjust MQTT 实体失败: {e}")

    def update_state(self):
        try:
            displays = self.get_hdr_displays()
            for monitor_key, light in self.monitor_lights.items():
                display = displays.get(monitor_key)
                if not display:
                    continue

                # Light 开关表示“显示器画面状态”，插件侧默认保持 ON
                light.on()

                brightness = display.get("sdr_brightness")
                if brightness is not None:
                    light.brightness(int(brightness * 255 / 100))

                hdr_switch = self.hdr_switches.get(monitor_key)
                if hdr_switch:
                    if display["hdr_enabled"]:
                        hdr_switch.on()
                    else:
                        hdr_switch.off()
        except Exception as e:
            self.log.error(f"更新 HDR 状态失败: {e}")

    def handle_light_command(self, client: MQTTClient, user_data, message, monitor_key: str):
        try:
            payload = message.payload.decode()
            self.log.info(f"收到 HDR 命令 {monitor_key}: {payload}")
            data = json.loads(payload)

            displays = self.get_hdr_displays()
            display = displays.get(monitor_key)
            if not display:
                self.log.warning(f"显示器不存在或不支持 HDR: {monitor_key}")
                return

            adapter_id = display["adapter_id"]
            target_id = display["target_id"]
            if "state" in data:
                is_on = data["state"] == "ON"
                if is_on:
                    self.wake_up_screen()
                    self.log.info(f"显示器 {display['name']} 画面开启")
                else:
                    # 无 DDC/CI 时仅支持系统层息屏
                    self._turn_off_screen()
                    self.log.info(f"显示器 {display['name']} 画面关闭（系统层）")
                time.sleep(0.2)

            if "brightness" in data:
                brightness_255 = int(data.get("brightness", 128))
                brightness_pct = int(brightness_255 * 100 / 255)
                latest = self.get_hdr_displays().get(monitor_key)
                if latest and latest.get("hdr_enabled"):
                    self._set_sdr_white_level(adapter_id, target_id, brightness_pct)
                    self.log.info(f"显示器 {display['name']} HDR 亮度设置为: {brightness_pct}%")
                else:
                    self.log.warning(f"显示器 {display['name']} HDR 未开启，跳过 HDR 亮度设置")

            time.sleep(0.2)
            self.update_state()

        except json.JSONDecodeError as e:
            self.log.error(f"解析 HDR 命令失败: {e}")
        except Exception as e:
            self.log.error(f"处理 HDR 命令失败: {e}")

    def handle_hdr_switch_command(self, client: MQTTClient, user_data, message, monitor_key: str):
        try:
            payload = message.payload.decode().strip().upper()
            displays = self.get_hdr_displays()
            display = displays.get(monitor_key)
            if not display:
                self.log.warning(f"显示器不存在或不支持 HDR: {monitor_key}")
                return

            adapter_id = display["adapter_id"]
            target_id = display["target_id"]
            is_on = payload == "ON"
            self._set_hdr_enabled(adapter_id, target_id, is_on)
            self.log.info(f"显示器 {display['name']} HDR {'开启' if is_on else '关闭'}")
            time.sleep(0.3)
            self.update_state()
        except Exception as e:
            self.log.error(f"处理 HDR 开关命令失败: {e}")

    def get_status(self):
        try:
            displays = self.get_hdr_displays()
            if not displays:
                return {
                    "level": "info",
                    "info": "未找到支持 HDR 的显示器",
                }

            status_list = []
            details = {}
            for key, display in displays.items():
                status_list.append(display["sdr_brightness"] if display["sdr_brightness"] is not None else 0)
                details[key] = {
                    "name": display["name"],
                    "hdr_enabled": display["hdr_enabled"],
                    "sdr_brightness": display["sdr_brightness"],
                }

            return {
                "level": "info",
                "status": status_list,
                "info": details,
            }
        except Exception as e:
            return {
                "level": "error",
                "info": f"读取 HDR 状态失败: {e}",
            }

    def on_option_changed(self, e):
        self.monitor_power_type = int(e.control.value)
        self.core.set_plugin_config("HDRAdjust", "monitor_power_type", self.monitor_power_type)

    def setting_page(self, e):
        radio0 = ft.Radio(value="0", label="系统层关闭画面(推荐，无DDC/CI)")
        radio1 = ft.Radio(value="1", label="模拟显示器休眠(当前同系统层关闭)")
        radio2 = ft.Radio(value="2", label="模拟显示器关机(当前同系统层关闭)")
        radio_group = ft.RadioGroup(
            content=ft.Column([radio0, radio1, radio2], spacing=10),
            on_change=self.on_option_changed,
            value=str(self.monitor_power_type),
        )

        return ft.Column(
            [
                ft.Text("请选择亮度组件开关的关屏方式：", size=20),
                radio_group,
                ft.Text("说明：当前插件不使用 DDC/CI，关屏操作将采用系统层息屏。", size=12),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
