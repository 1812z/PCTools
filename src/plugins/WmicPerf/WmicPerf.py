"""WMIC 基础性能监控插件。"""
import subprocess
import threading
import time
from datetime import datetime
import flet as ft
from ha_mqtt_discoverable import Settings
from ha_mqtt_discoverable.sensors import Sensor, SensorInfo


class WmicPerf:
    RESOURCE_DEFS = {
        "cpu": {"label": "CPU", "icon": ft.Icons.MEMORY},
        "memory": {"label": "内存", "icon": ft.Icons.STORAGE},
        "disk": {"label": "磁盘", "icon": ft.Icons.SAVE},
        "network": {"label": "网络总速率", "icon": ft.Icons.NETWORK_CHECK},
        "gpu": {"label": "显卡", "icon": ft.Icons.VIDEOGAME_ASSET},
        "process": {"label": "进程数", "icon": ft.Icons.FORMAT_LIST_NUMBERED},
        "thread": {"label": "线程数", "icon": ft.Icons.ACCOUNT_TREE},
        "handle": {"label": "句柄数", "icon": ft.Icons.LINK},
        "uptime": {"label": "系统运行时长", "icon": ft.Icons.ACCESS_TIME},
    }

    def __init__(self, core):
        self.core = core
        self.log = core.log

        self.update_interval = int(self.core.get_plugin_config("WmicPerf", "update_interval", 5))
        self.disk_devices = self._normalize_disk_devices(
            self.core.get_plugin_config("WmicPerf", "disk_devices", ["C:"])
        )
        self.resource_enabled = {
            name: bool(self.core.get_plugin_config("WmicPerf", f"enable_{name}", False))
            for name in self.RESOURCE_DEFS
        }

        self.updater = {"timer": self.update_interval}
        self.sensors = {}
        self.last_metrics = {}
        self._preview_stop = None

    def _normalize_disk_device(self, value):
        text = str(value or "C").strip().upper().replace("\\", "").replace("/", "")
        if text.endswith(":"):
            text = text[:-1]
        if not text:
            text = "C"
        return f"{text[0]}:"

    def _normalize_disk_devices(self, value):
        if isinstance(value, list):
            raw_items = value
        else:
            raw_items = str(value or "C:").replace(";", ",").split(",")

        devices = []
        seen = set()
        for item in raw_items:
            disk = self._normalize_disk_device(item)
            if disk not in seen:
                seen.add(disk)
                devices.append(disk)

        if not devices:
            devices = ["C:"]
        return devices

    def _detect_available_disks(self):
        out = self._run_wmic(["logicaldisk", "where", "DriveType=3", "get", "DeviceID", "/value"])
        disks = []
        for line in out.splitlines():
            line = line.strip()
            if not line.startswith("DeviceID="):
                continue
            _, value = line.split("=", 1)
            value = value.strip()
            if value:
                disks.append(self._normalize_disk_device(value))
        return self._normalize_disk_devices(disks)

    def _disk_key_suffix(self):
        return "_".join(d.replace(":", "").lower() for d in self.disk_devices)

    def _format_network_speed(self, bytes_per_sec):
        value = float(bytes_per_sec)
        units = ["B/s", "KB/s", "MB/s", "GB/s"]
        unit = units[0]
        for next_unit in units[1:]:
            if value < 1024:
                break
            value /= 1024
            unit = next_unit
        if unit == "B/s":
            return f"{int(value)} {unit}"
        return f"{value:.1f} {unit}"

    def setup_entities(self):
        """根据配置创建 MQTT 传感器"""
        try:
            self.sensors.clear()
            mqtt_settings = self.core.mqtt.get_mqtt_settings()
            device_info = self.core.mqtt.get_device_info(
                plugin_name="WmicPerf",
                model="PCTools WMIC Perf"
            )

            if self.resource_enabled["cpu"]:
                cpu_info = SensorInfo(
                    name="wmic_cpu_usage",
                    unique_id=f"{self.core.mqtt.device_name}_wmic_cpu_usage",
                    object_id=f"{self.core.mqtt.device_name}_wmic_cpu_usage",
                    device=device_info,
                    icon="mdi:cpu-64-bit",
                    unit_of_measurement="%",
                    state_class="measurement"
                )
                cpu_info.display_name = "CPU 占用"
                self.sensors["cpu_usage"] = Sensor(Settings(mqtt=mqtt_settings, entity=cpu_info))

            if self.resource_enabled["memory"]:
                mem_usage_info = SensorInfo(
                    name="wmic_memory_usage",
                    unique_id=f"{self.core.mqtt.device_name}_wmic_memory_usage",
                    object_id=f"{self.core.mqtt.device_name}_wmic_memory_usage",
                    device=device_info,
                    icon="mdi:memory",
                    unit_of_measurement="%",
                    state_class="measurement"
                )
                mem_usage_info.display_name = "内存占用"
                self.sensors["memory_usage"] = Sensor(Settings(mqtt=mqtt_settings, entity=mem_usage_info))

                mem_used_info = SensorInfo(
                    name="wmic_memory_used_mb",
                    unique_id=f"{self.core.mqtt.device_name}_wmic_memory_used_mb",
                    object_id=f"{self.core.mqtt.device_name}_wmic_memory_used_mb",
                    device=device_info,
                    icon="mdi:memory",
                    unit_of_measurement="MB",
                    state_class="measurement"
                )
                mem_used_info.display_name = "已用内存"
                self.sensors["memory_used_mb"] = Sensor(Settings(mqtt=mqtt_settings, entity=mem_used_info))

                mem_total_info = SensorInfo(
                    name="wmic_memory_total_mb",
                    unique_id=f"{self.core.mqtt.device_name}_wmic_memory_total_mb",
                    object_id=f"{self.core.mqtt.device_name}_wmic_memory_total_mb",
                    device=device_info,
                    icon="mdi:memory",
                    unit_of_measurement="MB",
                    state_class="measurement"
                )
                mem_total_info.display_name = "总内存"
                self.sensors["memory_total_mb"] = Sensor(Settings(mqtt=mqtt_settings, entity=mem_total_info))

            if self.resource_enabled["disk"]:
                for disk in self.disk_devices:
                    suffix = disk.replace(":", "").lower()
                    disk_usage_info = SensorInfo(
                        name=f"wmic_disk_{suffix}_usage",
                        unique_id=f"{self.core.mqtt.device_name}_wmic_disk_{suffix}_usage",
                        object_id=f"{self.core.mqtt.device_name}_wmic_disk_{suffix}_usage",
                        device=device_info,
                        icon="mdi:harddisk",
                        unit_of_measurement="%",
                        state_class="measurement"
                    )
                    disk_usage_info.display_name = f"{disk} 占用"
                    self.sensors[f"disk_{suffix}_usage"] = Sensor(Settings(mqtt=mqtt_settings, entity=disk_usage_info))

                    disk_free_info = SensorInfo(
                        name=f"wmic_disk_{suffix}_free_gb",
                        unique_id=f"{self.core.mqtt.device_name}_wmic_disk_{suffix}_free_gb",
                        object_id=f"{self.core.mqtt.device_name}_wmic_disk_{suffix}_free_gb",
                        device=device_info,
                        icon="mdi:harddisk",
                        unit_of_measurement="GB",
                        state_class="measurement"
                    )
                    disk_free_info.display_name = f"{disk} 剩余"
                    self.sensors[f"disk_{suffix}_free_gb"] = Sensor(Settings(mqtt=mqtt_settings, entity=disk_free_info))

            if self.resource_enabled["network"]:
                net_info = SensorInfo(
                    name="wmic_network_bytes_per_sec",
                    unique_id=f"{self.core.mqtt.device_name}_wmic_network_bytes_per_sec",
                    object_id=f"{self.core.mqtt.device_name}_wmic_network_bytes_per_sec",
                    device=device_info,
                    icon="mdi:network",
                    unit_of_measurement="B/s",
                    state_class="measurement"
                )
                net_info.display_name = "网络总速率"
                self.sensors["network_bytes_per_sec"] = Sensor(Settings(mqtt=mqtt_settings, entity=net_info))

            if self.resource_enabled["gpu"]:
                gpu_usage_info = SensorInfo(
                    name="wmic_gpu_usage",
                    unique_id=f"{self.core.mqtt.device_name}_wmic_gpu_usage",
                    object_id=f"{self.core.mqtt.device_name}_wmic_gpu_usage",
                    device=device_info,
                    icon="mdi:expansion-card",
                    unit_of_measurement="%",
                    state_class="measurement"
                )
                gpu_usage_info.display_name = "GPU 占用"
                self.sensors["gpu_usage"] = Sensor(Settings(mqtt=mqtt_settings, entity=gpu_usage_info))

                gpu_vram_info = SensorInfo(
                    name="wmic_gpu_vram_total_mb",
                    unique_id=f"{self.core.mqtt.device_name}_wmic_gpu_vram_total_mb",
                    object_id=f"{self.core.mqtt.device_name}_wmic_gpu_vram_total_mb",
                    device=device_info,
                    icon="mdi:memory",
                    unit_of_measurement="MB",
                    state_class="measurement"
                )
                gpu_vram_info.display_name = "显存总量"
                self.sensors["gpu_vram_total_mb"] = Sensor(Settings(mqtt=mqtt_settings, entity=gpu_vram_info))

            if self.resource_enabled["process"]:
                proc_info = SensorInfo(
                    name="wmic_process_count",
                    unique_id=f"{self.core.mqtt.device_name}_wmic_process_count",
                    object_id=f"{self.core.mqtt.device_name}_wmic_process_count",
                    device=device_info,
                    icon="mdi:format-list-numbered"
                )
                proc_info.display_name = "进程数"
                self.sensors["process_count"] = Sensor(Settings(mqtt=mqtt_settings, entity=proc_info))

            if self.resource_enabled["thread"]:
                thread_info = SensorInfo(
                    name="wmic_thread_count",
                    unique_id=f"{self.core.mqtt.device_name}_wmic_thread_count",
                    object_id=f"{self.core.mqtt.device_name}_wmic_thread_count",
                    device=device_info,
                    icon="mdi:vector-polyline"
                )
                thread_info.display_name = "线程数"
                self.sensors["thread_count"] = Sensor(Settings(mqtt=mqtt_settings, entity=thread_info))

            if self.resource_enabled["handle"]:
                handle_info = SensorInfo(
                    name="wmic_handle_count",
                    unique_id=f"{self.core.mqtt.device_name}_wmic_handle_count",
                    object_id=f"{self.core.mqtt.device_name}_wmic_handle_count",
                    device=device_info,
                    icon="mdi:link-variant"
                )
                handle_info.display_name = "句柄数"
                self.sensors["handle_count"] = Sensor(Settings(mqtt=mqtt_settings, entity=handle_info))

            if self.resource_enabled["uptime"]:
                up_info = SensorInfo(
                    name="wmic_system_uptime_hours",
                    unique_id=f"{self.core.mqtt.device_name}_wmic_system_uptime_hours",
                    object_id=f"{self.core.mqtt.device_name}_wmic_system_uptime_hours",
                    device=device_info,
                    icon="mdi:clock-outline",
                    unit_of_measurement="h",
                    state_class="measurement"
                )
                up_info.display_name = "系统运行时长"
                self.sensors["system_uptime_hours"] = Sensor(Settings(mqtt=mqtt_settings, entity=up_info))

            self.log.info(f"WmicPerf 传感器创建完成: {len(self.sensors)} 个")

        except Exception as e:
            self.log.error(f"WmicPerf 创建传感器失败: {e}")

    def _run_wmic(self, args):
        try:
            result = subprocess.run(
                ["wmic"] + args,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=8,
                check=False,
                creationflags=0x08000000
            )
            if result.returncode != 0:
                self.log.warning(f"wmic 执行失败: {' '.join(args)} -> {result.stderr.strip()}")
                return ""
            return result.stdout.strip()
        except Exception as e:
            self.log.error(f"wmic 调用异常: {e}")
            return ""

    def _parse_value_output(self, text):
        values = {}
        for line in text.splitlines():
            line = line.strip()
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
        return values

    def read_metrics(self):
        metrics = {}

        if self.resource_enabled["cpu"]:
            cpu_out = self._run_wmic(["cpu", "get", "loadpercentage", "/value"])
            cpu_vals = self._parse_value_output(cpu_out)
            if "LoadPercentage" in cpu_vals and cpu_vals["LoadPercentage"] != "":
                metrics["cpu_usage"] = int(cpu_vals["LoadPercentage"])

        if self.resource_enabled["memory"]:
            mem_out = self._run_wmic(["os", "get", "FreePhysicalMemory,TotalVisibleMemorySize", "/value"])
            mem_vals = self._parse_value_output(mem_out)
            total_kb = int(mem_vals.get("TotalVisibleMemorySize", "0") or 0)
            free_kb = int(mem_vals.get("FreePhysicalMemory", "0") or 0)

            if total_kb > 0:
                used_kb = max(total_kb - free_kb, 0)
                usage_percent = round((used_kb / total_kb) * 100, 1)
                metrics["memory_usage"] = usage_percent
                metrics["memory_used_mb"] = round(used_kb / 1024, 1)
                metrics["memory_total_mb"] = round(total_kb / 1024, 1)

        if self.resource_enabled["disk"]:
            for disk in self.disk_devices:
                suffix = disk.replace(":", "").lower()
                disk_out = self._run_wmic([
                    "logicaldisk", "where", f"DeviceID='{disk}'", "get", "Size,FreeSpace", "/value"
                ])
                disk_vals = self._parse_value_output(disk_out)
                size_b = int(disk_vals.get("Size", "0") or 0)
                free_b = int(disk_vals.get("FreeSpace", "0") or 0)
                if size_b > 0:
                    usage_percent = round(((size_b - free_b) / size_b) * 100, 1)
                    metrics[f"disk_{suffix}_usage"] = usage_percent
                    metrics[f"disk_{suffix}_free_gb"] = round(free_b / (1024 ** 3), 1)

        if self.resource_enabled["network"]:
            net_out = self._run_wmic(["path", "Win32_PerfFormattedData_Tcpip_NetworkInterface", "get", "BytesTotalPersec", "/value"])
            total = 0
            for line in net_out.splitlines():
                line = line.strip()
                if not line.startswith("BytesTotalPersec="):
                    continue
                _, value = line.split("=", 1)
                value = value.strip()
                if value.isdigit():
                    total += int(value)
            metrics["network_bytes_per_sec"] = total

        if self.resource_enabled["gpu"]:
            gpu_engine_out = self._run_wmic([
                "path", "Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine", "get", "UtilizationPercentage", "/value"
            ])
            gpu_total = 0
            for line in gpu_engine_out.splitlines():
                line = line.strip()
                if not line.startswith("UtilizationPercentage="):
                    continue
                _, value = line.split("=", 1)
                value = value.strip()
                if value.isdigit():
                    gpu_total += int(value)
            if gpu_total > 100:
                gpu_total = 100
            metrics["gpu_usage"] = gpu_total

            gpu_vram_out = self._run_wmic(["path", "Win32_VideoController", "get", "AdapterRAM", "/value"])
            vram_max = 0
            for line in gpu_vram_out.splitlines():
                line = line.strip()
                if not line.startswith("AdapterRAM="):
                    continue
                _, value = line.split("=", 1)
                value = value.strip()
                if value.isdigit():
                    vram_max = max(vram_max, int(value))
            if vram_max > 0:
                metrics["gpu_vram_total_mb"] = round(vram_max / (1024 * 1024), 1)

        if self.resource_enabled["process"]:
            proc_out = self._run_wmic(["process", "get", "ProcessId", "/value"])
            count = 0
            for line in proc_out.splitlines():
                if line.strip().startswith("ProcessId="):
                    count += 1
            metrics["process_count"] = count

        if self.resource_enabled["thread"]:
            thread_out = self._run_wmic(["path", "Win32_PerfFormattedData_PerfProc_Process", "get", "ThreadCount", "/value"])
            thread_total = 0
            for line in thread_out.splitlines():
                line = line.strip()
                if not line.startswith("ThreadCount="):
                    continue
                _, value = line.split("=", 1)
                value = value.strip()
                if value.isdigit():
                    thread_total += int(value)
            metrics["thread_count"] = thread_total

        if self.resource_enabled["handle"]:
            handle_out = self._run_wmic(["path", "Win32_PerfFormattedData_PerfProc_Process", "get", "HandleCount", "/value"])
            handle_total = 0
            for line in handle_out.splitlines():
                line = line.strip()
                if not line.startswith("HandleCount="):
                    continue
                _, value = line.split("=", 1)
                value = value.strip()
                if value.isdigit():
                    handle_total += int(value)
            metrics["handle_count"] = handle_total

        if self.resource_enabled["uptime"]:
            os_out = self._run_wmic(["os", "get", "LastBootUpTime", "/value"])
            os_vals = self._parse_value_output(os_out)
            boot_raw = os_vals.get("LastBootUpTime", "")
            if len(boot_raw) >= 14:
                boot_time = datetime.strptime(boot_raw[:14], "%Y%m%d%H%M%S")
                uptime_hours = round((datetime.now() - boot_time).total_seconds() / 3600, 1)
                metrics["system_uptime_hours"] = max(uptime_hours, 0)

        self.last_metrics = metrics
        return metrics

    def update_state(self):
        """更新并发布当前性能数据"""
        try:
            if not self.core.mqtt.is_connected():
                return False

            metrics = self.read_metrics()
            if not metrics:
                return False

            for key, sensor in self.sensors.items():
                if key in metrics:
                    sensor.set_state(metrics[key])

            return True
        except Exception as e:
            self.log.error(f"WmicPerf 更新失败: {e}")
            return False

    def on_unload(self):
        if self._preview_stop is not None:
            self._preview_stop.set()
            self._preview_stop = None
        self.sensors.clear()
        self.last_metrics = {}

    def setting_page(self, e=None):
        current_interval = int(self.core.get_plugin_config("WmicPerf", "update_interval", 5))
        current_disk_devices = ",".join(self.disk_devices)

        status_text = ft.Text("", color=ft.Colors.GREEN, visible=False, size=12)
        row_previews = {
            name: ft.Text("尚未读取", size=12, color=ft.Colors.BLACK)
            for name in self.RESOURCE_DEFS
        }
        row_switches = {}

        interval_field = ft.TextField(
            label="更新间隔（秒）",
            value=str(current_interval),
            width=180,
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="1-3600"
        )
        disk_field = ft.TextField(
            label="磁盘盘符(多个用逗号)",
            value=current_disk_devices,
            width=260,
            hint_text="如 C:,D:,E:"
        )

        def show_status(msg, ok=True):
            status_text.value = msg
            status_text.color = ft.Colors.GREEN if ok else ft.Colors.RED
            status_text.visible = True
            status_text.update()

        def rebuild_entities():
            for resource, sw in row_switches.items():
                enabled = bool(sw.value)
                self.resource_enabled[resource] = enabled
                self.core.set_plugin_config("WmicPerf", f"enable_{resource}", enabled)
            self.setup_entities()

        def save_interval(_):
            try:
                value = int(interval_field.value)
                if value < 1 or value > 3600:
                    show_status("✗ 间隔需在 1-3600 秒", ok=False)
                    return
                self.core.set_plugin_config("WmicPerf", "update_interval", value)
                self.update_interval = value
                self.updater["timer"] = value
                show_status(f"✓ 间隔已保存：{value}s")
            except ValueError:
                show_status("✗ 请输入有效数字", ok=False)

        def save_disk_device(_):
            disks = self._normalize_disk_devices(disk_field.value)
            disk_field.value = ",".join(disks)
            disk_field.update()
            self.disk_devices = disks
            self.core.set_plugin_config("WmicPerf", "disk_devices", disks)
            rebuild_entities()
            refresh_preview()
            show_status(f"✓ 磁盘: {', '.join(disks)}")

        def auto_fill_disks(_):
            disks = self._detect_available_disks()
            self.disk_devices = disks
            disk_field.value = ",".join(disks)
            disk_field.update()
            self.core.set_plugin_config("WmicPerf", "disk_devices", disks)
            if self.resource_enabled["disk"]:
                rebuild_entities()
                refresh_preview()
            show_status(f"✓ 自动检测: {', '.join(disks)}")

        def on_toggle(resource, evt):
            self.resource_enabled[resource] = bool(evt.control.value)
            if resource == "disk" and evt.control.value and not self.disk_devices:
                self.disk_devices = self._detect_available_disks()
                disk_field.value = ",".join(self.disk_devices)
                disk_field.update()
                self.core.set_plugin_config("WmicPerf", "disk_devices", self.disk_devices)
            rebuild_entities()
            refresh_preview()
            show_status(f"✓ {self.RESOURCE_DEFS[resource]['label']}已{'启用' if evt.control.value else '禁用'}")

        def refresh_preview(_=None):
            metrics = self.read_metrics()
            for resource, preview in row_previews.items():
                if not self.resource_enabled[resource]:
                    preview.value = "已禁用"
                elif resource == "cpu":
                    preview.value = f"{metrics.get('cpu_usage', '--')} %"
                elif resource == "memory":
                    mem_u = metrics.get("memory_usage", "--")
                    used = metrics.get("memory_used_mb", "--")
                    total = metrics.get("memory_total_mb", "--")
                    preview.value = f"{mem_u} % ({used}/{total} MB)"
                elif resource == "disk":
                    parts = []
                    for disk in self.disk_devices:
                        suffix = disk.replace(":", "").lower()
                        usage = metrics.get(f"disk_{suffix}_usage", "--")
                        free = metrics.get(f"disk_{suffix}_free_gb", "--")
                        parts.append(f"{disk} {usage}% 剩余{free}GB")
                    preview.value = "; ".join(parts) if parts else "--"
                elif resource == "network":
                    raw = metrics.get("network_bytes_per_sec")
                    preview.value = self._format_network_speed(raw) if raw is not None else "--"
                elif resource == "gpu":
                    gpu_u = metrics.get("gpu_usage", "--")
                    vram = metrics.get("gpu_vram_total_mb", "--")
                    preview.value = f"{gpu_u}% (VRAM {vram}MB)"
                elif resource == "process":
                    preview.value = f"{metrics.get('process_count', '--')}"
                elif resource == "thread":
                    preview.value = f"{metrics.get('thread_count', '--')}"
                elif resource == "handle":
                    preview.value = f"{metrics.get('handle_count', '--')}"
                elif resource == "uptime":
                    preview.value = f"{metrics.get('system_uptime_hours', '--')} h"
            if e and getattr(e, "page", None):
                e.page.update()

        def start_preview_auto_refresh(page):
            if self._preview_stop is not None:
                self._preview_stop.set()
            stop_event = threading.Event()
            self._preview_stop = stop_event

            def worker():
                while not stop_event.is_set():
                    try:
                        if not any(self.resource_enabled.values()):
                            stop_event.wait(1)
                            continue
                        refresh_preview()
                    except Exception:
                        pass
                    wait_s = max(1, int(self.update_interval))
                    stop_event.wait(wait_s)

            threading.Thread(target=worker, daemon=True).start()

        rows = []
        for resource, meta in self.RESOURCE_DEFS.items():
            label = f"{meta['label']}({len(self.disk_devices)}盘)" if resource == "disk" else meta["label"]
            sw = ft.Switch(
                value=self.resource_enabled[resource],
                on_change=lambda evt, r=resource: on_toggle(r, evt)
            )
            row_switches[resource] = sw
            rows.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(content=ft.Icon(meta["icon"], size=18), width=28),
                        ft.Container(content=ft.Text(label, no_wrap=True), width=130),
                        ft.Container(content=sw, width=60),
                        ft.Container(content=row_previews[resource], expand=True),
                    ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.BLACK),
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=8, vertical=6),
                )
            )

        top_panel = ft.Container(
            content=ft.Column([
                ft.Text("更新与预览", weight=ft.FontWeight.BOLD),
                ft.Row([interval_field]),
                ft.Row([
                    ft.ElevatedButton("保存间隔", icon=ft.Icons.SAVE, on_click=save_interval),
                ], spacing=8),
                ft.Text("建议 3-10 秒，间隔越小系统开销越高", size=11, color=ft.Colors.GREY_700),
            ], spacing=8),
            padding=12,
            border_radius=10,
            bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.BLUE_GREY),
        )

        disk_panel = ft.Container(
            content=ft.Column([
                ft.Text("磁盘设置", weight=ft.FontWeight.BOLD),
                ft.Row([disk_field]),
                ft.Row([
                    ft.ElevatedButton("保存磁盘", icon=ft.Icons.SAVE_AS, on_click=save_disk_device),
                    ft.OutlinedButton("自动检测", icon=ft.Icons.AUTO_AWESOME, on_click=auto_fill_disks),
                ], spacing=8),
                ft.Text("支持多个盘符，使用逗号分隔（例：C:,D:）", size=11, color=ft.Colors.GREY_700),
            ], spacing=8),
            padding=12,
            border_radius=10,
            bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.BLUE_GREY),
        )

        status_bar = ft.Container(
            content=status_text,
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            border_radius=8,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.GREEN),
            visible=False,
        )

        def sync_status_bar():
            status_bar.visible = status_text.visible
            if e and getattr(e, "page", None):
                e.page.update()

        old_show_status = show_status

        def show_status(msg, ok=True):
            old_show_status(msg, ok)
            status_bar.bgcolor = ft.Colors.with_opacity(0.05, ft.Colors.GREEN if ok else ft.Colors.RED)
            sync_status_bar()

        content = ft.Column([
            ft.Text("WMIC 基础性能监控", weight=ft.FontWeight.BOLD, size=18),
            top_panel,
            disk_panel,
            status_bar,
            ft.Row([
                ft.Text("监控项", weight=ft.FontWeight.BOLD),
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    icon_size=16,
                    tooltip="刷新预览",
                    on_click=refresh_preview,
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            *rows,
            ft.Container(
                content=ft.Text(f"当前已创建传感器: {len(self.sensors)}", size=12, color=ft.Colors.BLACK),
                padding=ft.padding.only(top=4),
            ),
        ], spacing=12, scroll=ft.ScrollMode.ADAPTIVE)

        root = ft.Container(
            width=760,
            height=680,
            padding=12,
            content=content,
        )

        if e and getattr(e, "page", None):
            start_preview_auto_refresh(e.page)

        return root
