import asyncio
import sys
from time import sleep
from plyer import notification
from Timer import TimerManager
from Logger import Logger
from Config import Config
from MQTT import MQTT
import importlib
import inspect
from pathlib import Path
import json
from typing import Optional, Dict, List
from dataclasses import dataclass, field, asdict


@dataclass
class PluginConfig:
    """插件配置"""
    enabled: bool = False
    settings: Dict = field(default_factory=dict)

    def to_dict(self):
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        """从字典创建"""
        return cls(
            enabled=data.get('enabled', True),
            settings=data.get('settings', {})
        )


@dataclass
class PluginMetadata:
    """插件元数据"""
    name: str
    display_name: str = ""
    version: str = "未知"
    author: str = "未知"
    description: str = "无"
    dependencies: List[str] = field(default_factory=list)
    config: PluginConfig = field(default_factory=PluginConfig)

    def __post_init__(self):
        if not self.display_name:
            self.display_name = self.name

    @classmethod
    def from_json(cls, plugin_name: str, json_data: dict, plugin_config: PluginConfig):
        """从 JSON 数据创建元数据"""
        return cls(
            name=plugin_name,
            display_name=json_data.get('name', plugin_name),
            version=json_data.get('version', '未知'),
            author=json_data.get('author', '未知'),
            description=json_data.get('description', '无'),
            dependencies=json_data.get('dependencies', []),
            config=plugin_config
        )


class Core:
    def __init__(self, gui=None):
        self.timer = None
        self.mqtt = None

        self.is_initialized = False

        self.gui = gui
        self.log = Logger(log_file="app.log")
        self.config = Config(self)

        self.timer_dict = {}

        self.plugins = {
            "instances": {},  # {name: instance}
            "metadata": {},  # {name: PluginMetadata}
            "modules": {},  # {name: module_object}
            "paths": {},  # {name: path}
            "errors": {},  # {name: error_message}
        }

        self._base_path = Path(__file__).parent / "plugins"

        # 扫描并加载插件
        self._scan_plugins()
        self.initialize()

    def initialize(self):
        """初始化核心组件和插件"""
        if not self.is_initialized:
            self.mqtt = MQTT(self)
            self.timer = TimerManager(self)

            self.initialize_all_plugins()
            self.config_plugin_timer()
            self.is_initialized = True

    def _scan_plugins(self):
        """
        扫描插件目录，只支持文件夹插件
        每个插件必须是一个文件夹，包含：
        - [插件名].py (插件主文件，如A文件夹下需要A.py)
        - config.json (插件配置文件)
        - plugin.json (插件元数据文件)
        """
        if not self._base_path.exists():
            self.log.error(f"❌ 插件目录不存在: {self._base_path}")
            return

        # 只扫描文件夹
        for folder_path in self._base_path.iterdir():
            if not folder_path.is_dir() or folder_path.name.startswith('_'):
                continue

            plugin_name = folder_path.name
            entry_file = folder_path / f"{plugin_name}.py"

            if entry_file.exists():
                self._register_plugin(folder_path, entry_file)
            else:
                self.log.warning(f"⚠️ 插件文件夹 {folder_path.name} 缺少入口文件 ({plugin_name}.py)")

    def _register_plugin(self, plugin_folder: Path, entry_file: Path):
        """注册插件"""
        plugin_name = plugin_folder.name

        # 构建模块路径 - 现在直接从与文件夹同名的.py文件加载
        module_path = f"plugins.{plugin_name}.{plugin_name}"  # 格式: plugins.A.A
        relative_path = plugin_folder.relative_to(self._base_path.parent)
        self.plugins["paths"][plugin_name] = relative_path

        # 加载插件配置
        plugin_config = self._load_plugin_config(plugin_folder)

        # 加载插件元数据（从 plugin.json）
        self._load_plugin_metadata(plugin_name, plugin_folder, module_path, plugin_config)
        status = "✅启用" if plugin_config.enabled else "⏸️禁用"
        self.log.info(f"📦 发现插件: {plugin_name} ({status})")

    def _load_plugin_config(self, plugin_folder: Path) -> PluginConfig:
        """加载插件配置文件"""
        config_file = plugin_folder / "config.json"

        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return PluginConfig.from_dict(data)
            except Exception as e:
                self.log.warning(f"⚠️ 加载 {plugin_folder.name} 配置失败: {e}，使用默认配置")

        # 如果配置文件不存在，创建默认配置
        default_config = PluginConfig()
        self._save_plugin_config(plugin_folder, default_config)
        return default_config

    def _save_plugin_config(self, plugin_folder: Path, plugin_config: PluginConfig) -> bool:
        """保存插件配置文件"""
        config_file = plugin_folder / "config.json"

        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(plugin_config.to_dict(), f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            self.log.error(f"❌ 保存 {plugin_folder.name} 配置失败: {e}")
            return False

    def _load_plugin_metadata(self, plugin_name: str, plugin_folder: Path,
                              module_path: str, plugin_config: PluginConfig):
        """加载插件元数据（从 plugin.json 文件）"""
        metadata_file = plugin_folder / "plugin.json"

        # 尝试从 plugin.json 读取元数据
        metadata_dict = {}
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata_dict = json.load(f)
                self.log.debug(f"✅ 从 plugin.json 加载元数据: {plugin_name}")
            except Exception as e:
                self.log.warning(f"⚠️ 读取 {plugin_name}/plugin.json 失败: {e}")
        else:
            self.log.warning(f"⚠️ 插件 {plugin_name} 缺少 plugin.json 文件")

        # 创建元数据对象
        metadata = PluginMetadata.from_json(plugin_name, metadata_dict, plugin_config)
        self.plugins["metadata"][plugin_name] = metadata

        # 只有启用的插件才导入模块
        if plugin_config.enabled:
            try:
                module = importlib.import_module(module_path)
                self.plugins["modules"][plugin_name] = module
                self.log.debug(f"✅ 导入插件模块: {plugin_name}")
            except Exception as e:
                self.log.error(f"❌ 导入插件 {plugin_name} 模块失败: {str(e)}")
                self.plugins["errors"][plugin_name] = str(e)
        else:
            self.log.debug(f"⏸️ 插件 {plugin_name} 已禁用，跳过模块导入")

    def initialize_all_plugins(self):
        """初始化所有启用的插件（按依赖顺序）"""
        # 获取所有需要初始化的插件
        to_initialize = [
            name for name in self.plugins["metadata"].keys()
            if self.plugins["metadata"][name].config.enabled
               and name not in self.plugins["instances"]
               and name not in self.plugins["errors"]
        ]

        # 拓扑排序：处理依赖关系
        initialized = set()

        def init_with_deps(plugin_name: str):
            if plugin_name in initialized or plugin_name in self.plugins["instances"]:
                return True

            metadata = self.plugins["metadata"].get(plugin_name)
            if not metadata or not metadata.config.enabled:
                return False

            # 先初始化依赖
            for dep in metadata.dependencies:
                if dep not in initialized:
                    if not init_with_deps(dep):
                        self.log.error(f"❌ 插件 {plugin_name} 的依赖 {dep} 初始化失败")
                        return False

            # 初始化当前插件
            success = self._create_instance(plugin_name)
            if success:
                initialized.add(plugin_name)
            return success

        # 初始化所有插件
        for name in to_initialize:
            init_with_deps(name)

        self.log.info(f"✅ 插件初始化完成: {len(initialized)}/{len(to_initialize)}")

    def _create_instance(self, plugin_name: str) -> bool:
        """创建插件实例"""
        try:
            if plugin_name in self.plugins["instances"]:
                self.log.warning(f"⚠️ 插件 {plugin_name} 已经初始化")
                return True

            if plugin_name not in self.plugins["modules"]:
                self.log.error(f"❌ 插件模块 {plugin_name} 未加载")
                return False

            module = self.plugins["modules"][plugin_name]

            # 更加灵活的类查找方法
            plugin_class = None
            # 方式1：尝试查找与插件名完全相同的类
            if hasattr(module, plugin_name):
                plugin_class = getattr(module, plugin_name)
                if inspect.isclass(plugin_class):
                    self.log.debug(f"✅ 找到与插件名相同的类: {plugin_name}")

            # 方式2：查找继承自特定基类的类
            if plugin_class is None:
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # 检查类是否在插件模块中定义
                    if obj.__module__ == module.__name__:
                        plugin_class = obj
                        self.log.debug(f"✅ 找到候选类: {name}")
                        break

            if not plugin_class:
                self.log.error(f"❌ 插件 {plugin_name} 中未找到有效的类")
                self.plugins["errors"][plugin_name] = "未找到有效的类"
                return False

            # 创建实例
            instance = plugin_class(self)
            self.plugins["instances"][plugin_name] = instance
            setattr(self, plugin_name, instance)

            # 调用初始化方法
            if hasattr(instance, 'initialize'):
                instance.initialize()

            metadata = self.plugins["metadata"][plugin_name]
            self.log.info(f"✅ 成功创建插件实例: {metadata.display_name} v{metadata.version}")
            return True

        except Exception as e:
            self.log.error(f"❌ 加载插件 {plugin_name} 失败: {str(e)}")
            self.plugins["errors"][plugin_name] = str(e)
            return False

    def reload_plugin(self, plugin_name: str) -> bool:
        """重载插件（热重载）"""
        plugin_name = self._normalize_module_name(plugin_name)
        self.log.info(f"🔄 重载插件模块: {plugin_name}")

        # 卸载旧实例
        if plugin_name in self.plugins["instances"]:
            instance = self.plugins["instances"].pop(plugin_name)
            if hasattr(instance, 'on_unload'):
                instance.on_unload()
            delattr(self, plugin_name)

        # 重新加载配置和元数据
        plugin_folder = self._base_path / plugin_name
        plugin_config = self._load_plugin_config(plugin_folder)

        # 重新导入模块
        module_path = f"plugins.{plugin_name}.{plugin_name}"  # 确保路径正确
        try:
            if plugin_name in sys.modules:
                del sys.modules[module_path]  # 确保从sys.modules中删除旧模块
            module = importlib.import_module(module_path)
            self.plugins["modules"][plugin_name] = module
            self.log.debug(f"✅ 重新导入插件模块: {plugin_name}")
        except Exception as e:
            self.log.error(f"❌ 重导入插件 {plugin_name} 模块失败: {str(e)}")
            return False

        # 重新加载元数据
        self._load_plugin_metadata(plugin_name, plugin_folder, module_path, plugin_config)

        # 创建新实例
        return self._create_instance(plugin_name)

    def enable_plugin(self, plugin_name: str) -> bool:
        """启用插件"""
        plugin_name = self._normalize_module_name(plugin_name)

        if plugin_name not in self.plugins["metadata"]:
            self.log.error(f"❌ 插件 {plugin_name} 不存在")
            return False

        metadata = self.plugins["metadata"][plugin_name]
        if metadata.config.enabled:
            self.log.warning(f"⚠️ 插件 {plugin_name} 已经是启用状态")
            return False

        # 更新配置
        metadata.config.enabled = True

        # 保存配置文件
        plugin_folder = self._base_path / plugin_name
        if not self._save_plugin_config(plugin_folder, metadata.config):
            return False

        self.log.info(f"✅ 已启用插件: {plugin_name}")

        # 立即加载插件模块和实例
        try:
            # 如果模块还未导入，先导入
            if plugin_name not in self.plugins["modules"]:
                module_path = f"plugins.{plugin_name}.{plugin_name}"
                module = importlib.import_module(module_path)
                self.plugins["modules"][plugin_name] = module
                self.log.debug(f"✅ 导入插件模块: {plugin_name}")

            # 创建插件实例
            if self._create_instance(plugin_name):
                self.log.info(f"🚀 插件 {plugin_name} 已载入实例")

                if self.gui:
                    self.gui.show_snackbar(f"插件 {plugin_name} 已启用并载入")

                return True
            else:
                self.log.error(f"❌ 插件 {plugin_name} 实例创建失败")
                # 回滚配置
                metadata.config.enabled = False
                self._save_plugin_config(plugin_folder, metadata.config)
                return False

        except Exception as e:
            self.log.error(f"❌ 启用插件 {plugin_name} 时发生错误: {str(e)}")
            # 回滚配置
            metadata.config.enabled = False
            self._save_plugin_config(plugin_folder, metadata.config)
            return False

    def disable_plugin(self, plugin_name: str) -> bool:
        """禁用插件"""
        plugin_name = self._normalize_module_name(plugin_name)

        if plugin_name not in self.plugins["metadata"]:
            self.log.error(f"❌ 插件 {plugin_name} 不存在")
            return False

        metadata = self.plugins["metadata"][plugin_name]
        if not metadata.config.enabled:
            self.log.warning(f"⚠️ 插件 {plugin_name} 已经是禁用状态")
            return False

        # 更新配置
        metadata.config.enabled = False

        # 保存配置文件
        plugin_folder = self._base_path / plugin_name
        if self._save_plugin_config(plugin_folder, metadata.config):
            # 卸载实例
            if plugin_name in self.plugins["instances"]:
                instance = self.plugins["instances"].pop(plugin_name)
                if hasattr(instance, 'on_unload'):
                    instance.on_unload()
                delattr(self, plugin_name)

            self.log.info(f"🛑 已禁用插件: {plugin_name}")
            return True

        return False

    def get_plugin_config(self, plugin_name: str, key: str = None, default=None):
        """
        获取插件配置
        :param plugin_name: 插件名称
        :param key: 配置键，如果为None则返回整个settings字典
        :param default: 默认值
        """
        plugin_name = self._normalize_module_name(plugin_name)

        if plugin_name not in self.plugins["metadata"]:
            self.log.warning(f"⚠️ 获取配置出错，插件 {plugin_name} 不存在")
            return default

        metadata = self.plugins["metadata"][plugin_name]

        if key is None:
            return metadata.config.settings

        return metadata.config.settings.get(key, default)

    def set_plugin_config(self, plugin_name: str, key: str, value) -> bool:
        """
        设置插件配置
        :param plugin_name: 插件名称
        :param key: 配置键
        :param value: 配置值
        """
        plugin_name = self._normalize_module_name(plugin_name)

        if plugin_name not in self.plugins["metadata"]:
            self.log.warning(f"⚠️ 获取配置出错，插件 {plugin_name} 不存在")
            return False

        metadata = self.plugins["metadata"][plugin_name]
        metadata.config.settings[key] = value

        # 保存配置文件
        plugin_folder = self._base_path / plugin_name
        return self._save_plugin_config(plugin_folder, metadata.config)

    def get_plugin_info(self, plugin_name: Optional[str] = None) -> Dict:
        """获取插件信息"""
        if plugin_name:
            plugin_name = self._normalize_module_name(plugin_name)
            if plugin_name not in self.plugins["metadata"]:
                return {"error": "插件不存在"}

            metadata = self.plugins["metadata"][plugin_name]
            return {
                "name": metadata.name,
                "display_name": metadata.display_name,
                "version": metadata.version,
                "author": metadata.author,
                "description": metadata.description,
                "dependencies": metadata.dependencies,
                "enabled": metadata.config.enabled,
                "loaded": plugin_name in self.plugins["instances"],
                "error": self.plugins["errors"].get(plugin_name, None),
                "settings": metadata.config.settings
            }

        # 返回所有插件信息
        return {
            name: self.get_plugin_info(name)
            for name in self.plugins["metadata"].keys()
        }

    def _normalize_module_name(self, module_name: str) -> str:
        """规范化模块名"""
        if not module_name:
            return ""
        return Path(module_name).stem.replace('.py', '')

    # ===== 以下保留原有方法 =====

    def get_module_status(self, module_name: str = None) -> dict:
        """获取模块状态信息"""
        if module_name:
            if module_name in self.plugins["instances"]:
                plugin = self.plugins["instances"][module_name]
                if hasattr(plugin, 'get_status'):
                    return {module_name: plugin.get_status()}
                return {module_name: "STATUS_METHOD_NOT_IMPLEMENTED"}
            return {module_name: "MODULE_NOT_FOUND"}

        status = {}
        for name in self.plugins["instances"].keys():
            status.update(self.get_module_status(name))
        return status

    def config_plugin_entities(self):
        """配置插件实体到MQTT"""
        for module_name in list(self.plugins["instances"].keys()):
            try:
                module = self.plugins["instances"][module_name]

                if hasattr(module, 'setup_entities'):
                    module.setup_entities()
                    self.log.info(f"{module_name} 执行实体发现")

            except Exception as e:
                self.log.error(f"❌ 插件 {module_name} 实体新增失败: {str(e)}")

        self.log.info(f"✅ 插件实体发现完成")

    def config_plugin_timer(self):
        """配置插件定时器"""
        for module_name in list(self.plugins["instances"].keys()):
            try:
                module = self.plugins["instances"][module_name]

                if hasattr(module, 'updater') and module.updater.get("timer"):
                    self.timer_dict[module_name] = module.updater["timer"]
                    self.timer.create_timer(
                        module_name,
                        module.update_state,
                        module.updater["timer"]
                    )
            except Exception as e:
                self.log.error(f"❌ 配置 {module_name} 定时器失败: {str(e)}")

        self.log.info(f"✅ 插件定时器初始化完成")

    def update_module_status(self):
        """更新所有模块状态"""
        for module_name in list(self.plugins["instances"].keys()):
            try:
                plugin = self.plugins["instances"][module_name]

                if hasattr(plugin, 'update_state'):
                    handler = plugin.update_state
                    if inspect.iscoroutinefunction(handler):
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(handler())
                    else:
                        handler()
                    self.log.debug(f"{module_name}: 更新数据")
            except Exception as e:
                self.log.error(f"{module_name} 更新数据失败: {e}")

        return True

    def start_plugin(self, module_name: str = '') -> bool:
        """启动插件"""
        if module_name:
            return self._start_plugin(module_name)

        for name in self.plugins["instances"].keys():
            self._start_plugin(name)
        return True

    def _start_plugin(self, module_name: str) -> bool:
        """启动单个插件"""
        try:
            if module_name in self.plugins["instances"]:
                plugin = self.plugins["instances"][module_name]
                if hasattr(plugin, 'start'):
                    plugin.start()
                    self.log.debug(f"{module_name}: 启动")
                    return True
        except Exception as e:
            self.log.error(f"{module_name} 启动失败: {e}")
            return False
        return False

    def stop_plugin(self, module_name: str = '') -> bool:
        """停止插件"""
        if module_name:
            return self._stop_plugin(module_name)

        for name in self.plugins["instances"].keys():
            self._stop_plugin(name)
        return True

    def _stop_plugin(self, module_name: str) -> bool:
        """停止单个插件"""
        try:
            if module_name in self.plugins["instances"]:
                plugin = self.plugins["instances"][module_name]
                if hasattr(plugin, 'stop'):
                    plugin.stop()
                    self.log.debug(f"{module_name}: 停止")
                    return True
        except Exception as e:
            self.log.error(f"{module_name} 停止失败: {e}")
            return False
        return False

    def show_toast(self, title: str, message: str, timeout: int = 5):
        """显示Toast通知"""
        notification.notify(
            title=title,
            message=message,
            app_name='PCTools',
            timeout=timeout
        )
        self.log.info(f"发送Toast通知: {title}")

    def start(self):
        """启动核心服务"""
        try:
            self.mqtt.start_mqtt()
            self.timer.start_all_timers()
            self.start_plugin()
        except Exception as e:
            self.log.error(f"进程启动失败: {e}")

    def stop(self):
        """停止核心服务"""
        try:
            self.mqtt.stop_mqtt()
            self.timer.stop_all_timers()
            self.stop_plugin()
        except Exception as e:
            self.log.error(f"进程停止失败: {e}")


if __name__ == '__main__':
    core = Core()
    core.start()
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        core.stop()