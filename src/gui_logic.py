"""
GUI 逻辑层
负责业务逻辑处理，不包含UI组件
"""

from typing import Optional, Dict, List, Callable


class GUILogic:
    """GUI业务逻辑处理类"""

    def __init__(self, core_instance):
        """
        初始化GUI逻辑层
        :param core_instance: Core实例
        """
        self.core = core_instance
        self.version = "v6.0.2"

        # 状态标志
        self.is_running = False
        self.is_starting = False
        self.is_stopping = False

        # UI回调（由UI层设置）
        self._show_snackbar_callback: Optional[Callable] = None
        self._update_ui_callback: Optional[Callable] = None

    def set_ui_callbacks(self, update_ui: Callable):
        """
        设置UI回调函数
        :param update_ui: 更新UI的回调
        """
        self._update_ui_callback = update_ui

    def _update_ui(self):
        """更新UI（内部方法）"""
        if self._update_ui_callback:
            self._update_ui_callback()

    def update_home_status(self):
        """更新主页状态"""
        try:
            if (self.core.gui and hasattr(self.core.gui, 'home_page') and
                    self.core.gui.home_page is not None):
                self.core.gui.home_page.update_status()
        except Exception as e:
            self.log_debug(f"更新主页状态失败: {e}")

    # ===== 服务控制 =====

    def start_service(self) -> bool:
        """启动服务"""
        if self.is_running or self.is_starting:
            self.core.gui.show_snackbar("请勿多次启动!")
            return False

        try:
            self.is_starting = True
            self.update_home_status()
            self.core.gui.show_snackbar("启动进程...")

            if self.core:
                self.core.start()
                self.is_running = True
                self.is_starting = False
                self.update_home_status()
                self.core.gui.show_snackbar("服务启动成功")
                return True

            self.is_starting = False
            return False

        except Exception as e:
            self.is_starting = False
            if self.core:
                self.core.log.error(f"服务启动失败: {e}")
            self.core.gui.show_snackbar(f"服务启动失败: {e}", duration=3000)
            return False

    def stop_service(self) -> bool:
        """停止服务"""
        if self.is_running and not self.is_starting and not self.is_stopping:
            self.is_stopping = True
            self.update_home_status()
            self.core.gui.show_snackbar("停止进程中...")

            try:
                self.core.stop()
                self.is_running = False
                self.core.gui.show_snackbar("成功停止所有进程")
                self.core.log.info("成功停止所有进程")
                self.is_stopping = False
                self.update_home_status()
                return True
            except Exception as e:
                self.core.log.error(f"停止服务失败: {e}")
                self.is_stopping = False
                self.update_home_status()
                return False

        elif not self.is_starting and not self.is_stopping:
            self.core.gui.show_snackbar("都还没运行呀")
            return False
        elif not self.is_stopping:
            self.core.gui.show_snackbar("启动中无法停止...")
            return False
        else:
            self.core.gui.show_snackbar("如果卡死请使用任务管理器终止python进程")
            return False

    def send_data(self) -> bool:
        """发送数据更新"""
        try:
            self.core.update_module_status()
            self.core.gui.show_snackbar("数据更新成功")
            return True
        except Exception as e:
            self.core.log.error(f"数据更新失败: {e}")
            self.core.gui.show_snackbar(f"数据更新失败: {e}", duration=3000)
            return False

    # ===== 配置管理 =====

    def get_config(self, key: str, default=None):
        """获取配置"""
        return self.core.config.get_config(key, default)

    def set_config(self, key: str, value):
        """设置配置"""
        self.core.config.set_config(key, value)

    def handle_config_change(self, field_name: str, value, value_type: str = "string"):
        """处理配置变更"""
        try:
            if value_type == "int":
                parsed_value = int(value)
            elif value_type == "bool":
                parsed_value = bool(value)
            else:
                parsed_value = value

            self.core.config.set_config(field_name, parsed_value)
            return True
        except Exception as e:
            self.core.log.error(f"配置变更失败: {e}")
            return False

    # ===== 插件管理 =====

    def get_all_plugins(self) -> Dict:
        """获取所有插件信息"""
        return self.core.get_plugin_info()

    def get_plugin_info(self, plugin_name: str) -> Dict:
        """获取单个插件信息"""
        return self.core.get_plugin_info(plugin_name)

    def enable_plugin(self, plugin_name: str) -> bool:
        """启用插件"""
        try:
            if self.core.enable_plugin(plugin_name):
                return True
            else:
                self.core.gui.show_snackbar(f"启用插件失败", duration=3000)
                return False
        except Exception as e:
            self.core.log.error(f"启用插件失败: {e}")
            self.core.gui.show_snackbar(f"启用失败: {e}", duration=3000)
            return False

    def disable_plugin(self, plugin_name: str) -> bool:
        """禁用插件"""
        try:
            if self.core.disable_plugin(plugin_name):
                self.core.gui.show_snackbar(f"插件 {plugin_name} 已禁用")
                return True
            else:
                self.core.gui.show_snackbar(f"禁用插件失败", duration=3000)
                return False
        except Exception as e:
            self.core.log.error(f"禁用插件失败: {e}")
            self.core.gui.show_snackbar(f"禁用失败: {e}", duration=3000)
            return False

    def reload_plugin(self, plugin_name: str) -> bool:
        """重载插件"""
        try:
            if self.core.reload_plugin(plugin_name):
                self.core.gui.show_snackbar(f"插件 {plugin_name} 重载成功")
                return True
            else:
                self.core.gui.show_snackbar(f"重载插件失败", duration=3000)
                return False
        except Exception as e:
            self.core.log.error(f"重载插件失败: {e}")
            self.core.gui.show_snackbar(f"重载失败: {e}", duration=3000)
            return False

    def toggle_plugin(self, plugin_name: str, enabled: bool) -> bool:
        """切换插件启用状态"""
        if enabled:
            return self.enable_plugin(plugin_name)
        else:
            return self.disable_plugin(plugin_name)

    def get_plugin_settings_handler(self, plugin_name: str):
        """获取插件设置处理器"""
        if plugin_name not in self.core.plugins["instances"]:
            return None

        plugin_instance = self.core.plugins["instances"][plugin_name]
        return getattr(plugin_instance, "setting_page", None)

    def has_plugin_settings(self, plugin_name: str) -> bool:
        """检查插件是否有设置页面"""
        return self.get_plugin_settings_handler(plugin_name) is not None

    def get_plugin_path(self, plugin_name: str) -> str:
        """获取插件路径"""
        return str(self.core.plugins["paths"].get(plugin_name, "未知"))

    def get_sorted_plugins(self) -> List[tuple]:
        """获取排序后的插件列表"""
        all_plugins = self.get_all_plugins()
        return sorted(all_plugins.items(), key=lambda x: x[1]["display_name"])

    # ===== 插件配置管理 =====

    def get_plugin_config(self, plugin_name: str, key: str = None, default=None):
        """获取插件配置"""
        return self.core.get_plugin_config(plugin_name, key, default)

    def set_plugin_config(self, plugin_name: str, key: str, value) -> bool:
        """设置插件配置"""
        try:
            return self.core.set_plugin_config(plugin_name, key, value)
        except Exception as e:
            self.core.log.error(f"设置插件配置失败: {e}")
            return False

    # ===== 状态查询 =====

    def can_modify_plugins(self) -> bool:
        """是否可以修改插件（未运行时）"""
        return not self.is_running

    def is_plugin_available(self, plugin_info: Dict) -> bool:
        """插件是否可用"""
        return (
                plugin_info["enabled"]
                and plugin_info["loaded"]
                and not self.is_running
        )

    def get_plugin_status_info(self, plugin_info: Dict) -> tuple:
        """
        获取插件状态信息
        :return: (status_icon, status_color, status_text)
        """
        loaded = plugin_info["loaded"]
        enabled = plugin_info["enabled"]
        has_error = plugin_info["error"] is not None

        if loaded:
            return ("✅", "green", "已加载")
        elif has_error:
            return ("❌", "red", f"加载失败: {plugin_info['error']}")
        elif not enabled:
            return ("⏸️", "grey", "已禁用")
        else:
            return ("⚠️", "orange", "未加载")

    # ===== 自启动管理 =====

    def set_auto_start(self, enabled: bool) -> str:
        """设置自启动"""
        import startup

        try:
            if enabled:
                result = startup.add_to_startup()
                self.set_config("auto_start", True)
            else:
                result = startup.remove_from_startup()
                self.set_config("auto_start", False)
            return result
        except Exception as e:
            self.core.log.error(f"设置自启动失败: {e}")
            return f"设置失败: {e}"

    # ===== 工具方法 =====

    def get_version(self) -> str:
        """获取版本号"""
        return self.version

    def log_info(self, message: str):
        """记录信息日志"""
        self.core.log.info(message)

    def log_error(self, message: str):
        """记录错误日志"""
        self.core.log.error(message)

    def log_debug(self, message: str):
        """记录调试日志"""
        self.core.log.debug(message)