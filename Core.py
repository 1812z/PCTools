import time
from time import sleep
from plyer import notification
from Timer import TimerManager
from Win_reg import WindowsRegistry
from Logger import  Logger
from Config import Config
from MQTT import MQTT
import importlib
import inspect
from pathlib import Path

class Core:
    def __init__(self, gui = None):
        self.is_initialized = False

        self.gui = gui
        # Core 提供的接口
        self.log = Logger()
        self.config = Config(self)

        self.timer_dict = {}

        self.plugin_instances = {}  # 保存已初始化的插件类的实例 {name: instance}
        self.disabled_plugins = set() # 保存被禁用的插件名
        self.plugin_paths = {}  # 保存所有插件文件路径
        self.error_plugins = [] #加载失败的插件

        self._base_path = Path(__file__).parent / "plugins"
        # self.icon_path = str(Path(__file__).parent / "img" / "logo.png")


        self._load_plugins()

    def initialize(self):
        if not self.is_initialized:
            self.mqtt = MQTT(self)
            self.reg = WindowsRegistry()
            self.timer = TimerManager(self)


            self.initialize_plugin()
            self.config_plugin()
            self.is_initialized = True

    def _load_plugins(self):
        """加载所有插件模块，但不初始化"""
        plugins_dir = Path(__file__).parent / "plugins"

        for file in plugins_dir.glob("**/*.py*"):  # 同时匹配.py和.py.disabled
            if file.name.startswith(('__init__.py', '_')) or ".pyc" in file.name:
                continue

            module_name = self._normalize_module_name(file.name)
            relative_path = file.relative_to(plugins_dir.parent)

            self.plugin_paths[module_name] = relative_path
            # 跳过.disabled文件的导入和类加载
            if file.suffix == '.disabled':
                self.disabled_plugins.add(module_name)
                self.log.info(f"✅ 成功发现禁用的插件: {module_name}")
                continue
            else:
                self.log.info(f"✅ 成功发现启用的插件: {module_name}")


    def initialize_plugin(self, plugin_name=None):
        """
          初始化插件
          :param plugin_name: 要初始化的插件名(不带.py)，None表示初始化所有可用插件
          :return: 成功初始化的数量
          """
        if not self.plugin_paths.keys():
            self._load_plugins()

        plugin_name = self._normalize_module_name(plugin_name) if plugin_name else None

        if plugin_name is None:
            # 初始化所有可用插件(未被禁用的)
            return  sum(
                self._create_instance(name) or (self.error_plugins.append(name) or 0)
                for name in self.plugin_paths.keys()
                if name not in self.disabled_plugins and name not in self.plugin_instances
            )

        # 初始化指定插件
        if plugin_name in self.disabled_plugins:
            self.log.warning(f"⚠️ 插件 {plugin_name} 已被禁用")
            return 0

        if plugin_name in self.plugin_instances.keys():
            self.log.warning(f"插件 {plugin_name} 已初始化")
            return 1

        if plugin_name not in self.plugin_instances.keys():
            self.log.error(f"❌ 插件 {plugin_name} 未加载")
            return 0

        return 1 if self._create_instance(plugin_name) else 0



    def _create_instance(self, plugin_name):
        """内部方法：创建插件实例"""
        try:
            module_path = self.plugin_paths[plugin_name]
            module_path = str(module_path.with_suffix('')).replace('\\', '.')
            module = importlib.import_module(module_path)
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if name == plugin_name:

                    instance = obj(self)
                    self.plugin_instances[plugin_name] = instance
                    setattr(self, plugin_name, instance)

                    # 调用初始化方法（如果有）
                    if hasattr(instance, 'initialize'):
                        instance.initialize()

                    self.log.info(f"✅ 成功创建插件实例: {plugin_name}")
                    return True

            self.log.warning(f"⚠️  {plugin_name} 中未找到匹配的类")
            return False
        except ImportError as e:
            self.log.error(f"❌ 导入模块 {plugin_name} 失败: {str(e)}")
            return False
        except Exception as e:
            self.log.error(f"❌ 加载插件 {plugin_name} 失败: {str(e)}")
            return False

    def get_module_status(self, module_name: str = None) -> dict:
        """
        获取模块状态信息
        return:dict{
        }
        """
        if module_name:
            # 获取指定模块状态
            if hasattr(self, module_name):
                status_method = "get_status"
                plugin = getattr(self, module_name)

                if hasattr(plugin, status_method):
                    return {
                        module_name: getattr(plugin, status_method)()
                    }
                return {module_name: "STATUS_METHOD_NOT_IMPLEMENTED"}
            return {module_name: "MODULE_NOT_FOUND"}

        # 获取所有模块状态
        status = {}
        for name in dir(self):
            if not name.startswith('_') and name[0].isupper():  # 识别插件
                status.update(self.get_module_status(name))
        return status

    def config_plugin(self):
        for module_name in list(self.plugin_instances.keys()):
            try:
                module = getattr(self, module_name)
                # 添加定时器
                if hasattr(module, 'updater'):
                    if module.updater.get("timer"):
                        self.timer_dict[module.__class__.__name__] = module.updater.get("timer")
                        self.timer.create_timer(module.__class__.__name__, module.update_state, module.updater.get("timer"))

                # 检查是否存在 config 属性
                if hasattr(module, 'config'):
                    c = module.config
                    self.log.debug(f"🔧 {module_name} 配置: {c}")

                    for entity in c:
                        icon = entity["icon"] if "icon" in entity else None
                        self.mqtt.send_mqtt_discovery(entity_type=entity["entity_type"], name=entity["name"], entity_id=f"{module_name}_{entity["entity_id"]}",icon=icon)
                        sleep(0.3)
                    self.log.debug(f"{module_name} 成功新增 {len(c)} 个主题")
                else:
                    self.log.debug(f"⚠️ {module_name} 无 config ,跳过发现")
            except Exception as e:
                self.log.error(f"❌ 读取 {module_name} 配置失败: {str(e)}")

        self.log.info(f"✅ 插件初始化完成")

    def update_module_status(self):
        """
        更新模块状态信息
        return:bool{
        }
        """
        module_name = ""
        try:
            for module_name in dir(self):
                if not module_name.startswith('_') and module_name[0].isupper():
                    if hasattr(self, module_name):
                        update_method = "update_state"
                        plugin = getattr(self, module_name)

                        if hasattr(plugin, update_method):
                            getattr(plugin, update_method)()
                            self.log.debug(f"{module_name}: 更新数据")
                    else:
                        self.log.warning(f"{module_name}: MODULE_NOT_FOUND")
            return True
        except Exception as e:
            self.log.error(f"{module_name} 更新数据失败 {e}")
            return False

    def _start_plugin(self, module_name):
        try:
            if not module_name.startswith('_') and module_name[0].isupper():
                if hasattr(self, module_name):
                    start_method = "start"
                    plugin = getattr(self, module_name)

                    if hasattr(plugin, start_method):
                        getattr(plugin, start_method)()
                        self.log.debug(f"{module_name}: 启动")
        except Exception as e:
            self.log.error(f"{module_name} 启动失败 {e}")
            return False

    def _stop_plugin(self, module_name):
        try:
            if not module_name.startswith('_') and module_name[0].isupper():
                if hasattr(self, module_name):
                    start_method = "stop"
                    plugin = getattr(self, module_name)

                    if hasattr(plugin, start_method):
                        getattr(plugin, start_method)()
                        self.log.debug(f"{module_name}: 停止")
        except Exception as e:
            self.log.error(f"{module_name} 停止失败 {e}")
            return False

    def _normalize_module_name(self, module_name):
        """规范化模块名，去除.py后缀和路径"""
        return Path(module_name).stem.replace('.py', '')

    def plugin_manage(self, module_name, status:bool):
        if status:
            self.enable_plugin(module_name)
        else:
            self.disable_plugin(module_name)

    def delattr_all_plugin(self):
        try:
            for module_name in list(self.plugin_instances.keys()):
                instance = self.plugin_instances.pop(module_name)
                if hasattr(instance, 'on_delattr'):
                    instance.on_delattr()
                delattr(self, module_name)
                self.log.info(f"⏸️ 已卸载实例: {module_name}")
            return True
        except Exception as e:
            self.log.error(f"❌ 卸载实例 {module_name} 失败: {str(e)}")
            return False

    def disable_plugin(self, module_name):
        """禁用插件：重命名文件为.py.disabled"""
        module_name = self._normalize_module_name(module_name)

        if module_name not in self.plugin_paths:
            self.log.error(f"❌ 插件 {module_name} 不存在")
            return False

        file_path = self.plugin_paths[module_name]
        if file_path.suffix == '.disabled':
            self.log.warning(f"⚠️ 插件 {module_name} 已经是禁用状态")
            return False

        # 重命名文件
        disabled_path = file_path.with_suffix('.py.disabled')
        try:
            file_path.rename(disabled_path)
            self.disabled_plugins.add(module_name)
            self.plugin_paths[module_name] = disabled_path  # 更新保存的路径

            # 清理已加载的实例
            if module_name in self.plugin_instances:
                instance = self.plugin_instances.pop(module_name)
                if hasattr(instance, 'on_delattr'):
                    instance.on_delattr()
                delattr(self, module_name)
                self.log.info(f"🛑 已禁用并卸载插件: {module_name}")
            else:
                self.log.info(f"⏸️ 已禁用插件: {module_name}")
            return True
        except Exception as e:
            self.log.error(f"❌ 禁用插件 {module_name} 失败: {str(e)}")
            return False

    def enable_plugin(self, module_name):
        """启用插件：将.py.disabled重命名回.py"""
        module_name = self._normalize_module_name(module_name)

        if module_name not in self.plugin_paths:
            self.log.error(f"❌ 插件 {module_name} 不存在")
            return False

        file_path = self.plugin_paths[module_name]
        print(file_path)
        if file_path.suffix != '.disabled':
            self.log.info(f"⚠️ 插件 {module_name} 不是禁用状态")
            return False

        # 重命名文件
        enabled_path = file_path.parent / (file_path.stem.removesuffix('.py') + '.py')
        try:
            file_path.rename(enabled_path)
            self.disabled_plugins.discard(module_name)
            self.plugin_paths[module_name] = enabled_path  # 更新保存的路径
            self.log.info(f"✅ 已启用插件: {module_name}")
            return True
        except Exception as e:
            self.log.error(f"❌ 启用插件 {module_name} 失败: {str(e)}")
            return False

    def start_plugin(self, module_name: str = '') -> bool:
        if module_name:
            self._start_plugin(module_name)
        else:
            for module_name in dir(self):
                self._start_plugin(module_name)
        return True

    def stop_plugin(self, module_name: str = '') -> bool:
        if module_name:
            self._stop_plugin(module_name)
        else:
            for module_name in dir(self):
                self._stop_plugin(module_name)
        return True

    def show_toast(self, title:str, message:str, timeout:int=5):
        notification.notify(
            title=title,
            message=message,
            app_name='PCTools',
            timeout=timeout
        )

        self.log.info("发送Toast通知{title}")

    def start_timer(self):
        for key,item in self.timer_dict.items():
            try:
                self.timer.start_timer(key)
            except Exception as e:
                self.log.error(f"{key} 启动定时器失败 : {e}")
        self.mqtt.keepalive(True)

    def stop_timer(self):
        for key,item in self.timer_dict.items():
            try:
                self.timer.stop_timer(key)
            except Exception as e:
                self.log.error(f"{key} 停止定时器失败 : {e}")
        self.mqtt.keepalive(False)

    def start(self):
        try:
            self.mqtt.start_mqtt()
            self.start_timer()
            self.start_plugin()
        except Exception as e:
            self.log.error(f"进程启动失败 : {e}")

    def stop(self):
        try:
            self.mqtt.stop_mqtt()
            self.stop_timer()
            self.stop_plugin()
        except Exception as e:
            self.log.error(f"进程停止失败 : {e}")

if __name__ == '__main__':
    core = Core()
    core.initialize()
    core.start()
    core.mqtt.mqtt_subscribe("homeassistant/switch/PC_Win_Color_APP_Dark_Mode/set")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        core.stop()






