import json
from pathlib import Path
from typing import Dict, Any, Optional

class Config:
    def __init__(self, core):
        self._config_file = Path("config.json")
        self.core = core
        self.config_data = self.load_config()

    def load_config(self) -> Optional[Dict[str, Any]]:
        """从文件加载配置数据，成功返回字典，失败返回None"""
        try:
            if self._config_file.exists():
                with open(self._config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.core.log.debug(f"⚙️成功加载配置文件: {self._config_file}")
                return data
            else:
                self.core.log.warning("配置文件不存在")
                return None
        except json.JSONDecodeError as e:
            self.core.log.error(f"配置文件格式错误: {str(e)}，请检查")
            return None
        except Exception as e:
            self.core.log.error(f"加载配置文件时出错: {str(e)}，请检查")
            return None

    def save_config(self,data: Dict[str, Any]) -> bool:
        """保存配置到文件"""
        try:
            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            self.config_data = data
            self.core.log.debug(f"⚙️配置已保存到: {self._config_file}")
            return True
        except Exception as e:
            self.core.log.error(f"保存配置时出错: {str(e)}")
            return False

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config_data.get(key, default)

    def set_config(self, key: str, value: Any, auto_save: bool = True) -> bool:
        """设置配置值"""
        self.config_data[key] = value
        if auto_save:
            return self.save_config(self.config_data)
        return True