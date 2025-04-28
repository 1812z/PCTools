import ctypes
import winreg
from typing import Any, Union, Optional


class WindowsRegistry:
    """
    Windows 注册表操作工具类

    功能：
    - 读取注册表值
    - 写入注册表值
    - 创建注册表项
    - 删除注册表项或值
    - 枚举子项和值
    """

    HWND_BROADCAST = 0xFFFF
    WM_SETTINGCHANGE = 0x001A
    SMTO_ABORTIFHUNG = 0x0002

    # 注册表根键映射
    _ROOT_KEYS = {
        'HKEY_CLASSES_ROOT': winreg.HKEY_CLASSES_ROOT,
        'HKEY_CURRENT_USER': winreg.HKEY_CURRENT_USER,
        'HKEY_LOCAL_MACHINE': winreg.HKEY_LOCAL_MACHINE,
        'HKEY_USERS': winreg.HKEY_USERS,
        'HKEY_CURRENT_CONFIG': winreg.HKEY_CURRENT_CONFIG
    }

    # 注册表值类型映射
    _VALUE_TYPES = {
        'REG_SZ': winreg.REG_SZ,
        'REG_EXPAND_SZ': winreg.REG_EXPAND_SZ,
        'REG_BINARY': winreg.REG_BINARY,
        'REG_DWORD': winreg.REG_DWORD,
        'REG_QWORD': winreg.REG_QWORD,
        'REG_MULTI_SZ': winreg.REG_MULTI_SZ,
        'REG_NONE': winreg.REG_NONE
    }

    @staticmethod
    def get_root_key(root_key_name: str) -> int:
        """获取根键句柄"""
        root_key = WindowsRegistry._ROOT_KEYS.get(root_key_name.upper())
        if root_key is None:
            raise ValueError(f"无效的根键名称: {root_key_name}")
        return root_key

    @staticmethod
    def get_value_type(type_name: str) -> int:
        """获取值类型"""
        value_type = WindowsRegistry._VALUE_TYPES.get(type_name.upper())
        if value_type is None:
            raise ValueError(f"无效的值类型: {type_name}")
        return value_type

    @staticmethod
    def read_value(
            root_key_name: str,
            sub_key: str,
            value_name: str,
            default: Any = None
    ) -> Any:
        """
        读取注册表值

        参数:
            root_key_name: 根键名称 (如 'HKEY_CURRENT_USER')
            sub_key: 子键路径 (如 'Software\\Microsoft\\Windows')
            value_name: 值名称
            default: 如果值不存在返回的默认值

        返回:
            注册表值或默认值
        """
        try:
            root_key = WindowsRegistry.get_root_key(root_key_name)
            with winreg.OpenKey(root_key, sub_key, 0, winreg.KEY_READ) as key:
                value, value_type = winreg.QueryValueEx(key, value_name)
                return value
        except FileNotFoundError:
            return default
        except Exception as e:
            raise WindowsRegistryError(f"读取注册表失败: {e}")

    @staticmethod
    def write_value(
            root_key_name: str,
            sub_key: str,
            value_name: str,
            value: Any,
            value_type: str = 'REG_SZ'
    ) -> None:
        """
        写入注册表值

        参数:
            root_key_name: 根键名称
            sub_key: 子键路径
            value_name: 值名称
            value: 要写入的值
            value_type: 值类型 (如 'REG_DWORD')
        """
        try:
            root_key = WindowsRegistry.get_root_key(root_key_name)
            reg_type = WindowsRegistry.get_value_type(value_type)

            # 确保子键存在
            WindowsRegistry.create_key(root_key_name, sub_key)

            with winreg.OpenKey(root_key, sub_key, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, value_name, 0, reg_type, value)
        except Exception as e:
            raise WindowsRegistryError(f"写入注册表失败: {e}")

    @staticmethod
    def create_key(
            root_key_name: str,
            sub_key: str,
            force: bool = False
    ) -> None:
        """
        创建注册表项

        参数:
            root_key_name: 根键名称
            sub_key: 要创建的子键路径
            force: 如果为True，会创建路径中所有不存在的键
        """
        try:
            root_key = WindowsRegistry.get_root_key(root_key_name)

            if force:
                # 递归创建所有不存在的子键
                parts = sub_key.split('\\')
                current_path = ''
                for part in parts:
                    current_path = f"{current_path}\\{part}" if current_path else part
                    try:
                        with winreg.OpenKey(root_key, current_path, 0, winreg.KEY_READ):
                            pass
                    except FileNotFoundError:
                        with winreg.CreateKey(root_key, current_path):
                            pass
            else:
                with winreg.CreateKey(root_key, sub_key):
                    pass
        except Exception as e:
            raise WindowsRegistryError(f"创建注册表项失败: {e}")

    @staticmethod
    def delete_key(
            root_key_name: str,
            sub_key: str,
            recursive: bool = False
    ) -> None:
        """
        删除注册表项

        参数:
            root_key_name: 根键名称
            sub_key: 要删除的子键路径
            recursive: 是否递归删除子项
        """
        try:
            root_key = WindowsRegistry.get_root_key(root_key_name)

            if recursive:
                # 递归删除需要从最深层开始
                sub_keys = []
                with winreg.OpenKey(root_key, sub_key) as key:
                    try:
                        while True:
                            sub_keys.append(winreg.EnumKey(key, 0))
                    except OSError:
                        pass

                for child_key in sub_keys:
                    WindowsRegistry.delete_key(
                        root_key_name,
                        f"{sub_key}\\{child_key}",
                        True
                    )

            winreg.DeleteKey(root_key, sub_key)
        except Exception as e:
            raise WindowsRegistryError(f"删除注册表项失败: {e}")

    @staticmethod
    def delete_value(
            root_key_name: str,
            sub_key: str,
            value_name: str
    ) -> None:
        """
        删除注册表值

        参数:
            root_key_name: 根键名称
            sub_key: 子键路径
            value_name: 要删除的值名称
        """
        try:
            root_key = WindowsRegistry.get_root_key(root_key_name)
            with winreg.OpenKey(root_key, sub_key, 0, winreg.KEY_WRITE) as key:
                winreg.DeleteValue(key, value_name)
        except Exception as e:
            raise WindowsRegistryError(f"删除注册表值失败: {e}")

    @staticmethod
    def enum_keys(
            root_key_name: str,
            sub_key: str
    ) -> list[str]:
        """
        枚举子键

        参数:
            root_key_name: 根键名称
            sub_key: 子键路径

        返回:
            子键名称列表
        """
        try:
            root_key = WindowsRegistry.get_root_key(root_key_name)
            with winreg.OpenKey(root_key, sub_key) as key:
                sub_keys = []
                index = 0
                while True:
                    try:
                        sub_keys.append(winreg.EnumKey(key, index))
                        index += 1
                    except OSError:
                        break
                return sub_keys
        except Exception as e:
            raise WindowsRegistryError(f"枚举子键失败: {e}")

    @staticmethod
    def enum_values(
            root_key_name: str,
            sub_key: str
    ) -> dict[str, Any]:
        """
        枚举值

        参数:
            root_key_name: 根键名称
            sub_key: 子键路径

        返回:
            字典 {值名称: 值}
        """
        try:
            root_key = WindowsRegistry.get_root_key(root_key_name)
            with winreg.OpenKey(root_key, sub_key) as key:
                values = {}
                index = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, index)
                        values[name] = value
                        index += 1
                    except OSError:
                        break
                return values
        except Exception as e:
            raise WindowsRegistryError(f"枚举值失败: {e}")


    @staticmethod
    def notify_system(message: str = "ImmersiveColorSet", timeout: int = 1000) -> bool:
        """
        发送系统通知，通知系统设置已更改

        参数:
            message: 通知消息
            timeout: 超时时间(毫秒)

        返回:
            bool: 是否发送成功
        """
        try:
            result = ctypes.c_long()
            ctypes.windll.user32.SendMessageTimeoutW(
                WindowsRegistry.HWND_BROADCAST,
                WindowsRegistry.WM_SETTINGCHANGE,
                0,
                message,
                WindowsRegistry.SMTO_ABORTIFHUNG,
                timeout,
                ctypes.byref(result)
            )
            return True
        except Exception as e:
            raise WindowsRegistryError(f"发送系统通知失败: {e}")


class WindowsRegistryError(Exception):
    """注册表操作异常"""
    pass