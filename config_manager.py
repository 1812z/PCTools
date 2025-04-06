from typing import Dict, Any, Optional
import json
from pathlib import Path
from logger_manager import Logger


_config_file = Path("config.json")
config_data: Dict[str, Any] = {}
logger = Logger(__name__)
success = False


def init_config_manager(config_file: str = "config.json"):
    """初始化配置管理器"""
    global _config_file, config_data
    _config_file = Path(config_file)
    load_config() 

def load_config() -> Optional[Dict[str, Any]]:
    """从文件加载配置数据，成功返回字典，失败返回None"""
    global config_data,success
    try:
        if success:
            return config_data
        if  _config_file.exists():
            with open(_config_file, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                logger.debug(f"成功加载配置文件: {_config_file}")
                success = True
            return config_data
        else:
            if logger:
                logger.warning("配置文件不存在")
            return None
    except json.JSONDecodeError as e:
        if logger:
            logger.error(f"配置文件格式错误: {str(e)}，请检查")
        return None
    except Exception as e:
        if logger:
            logger.error(f"加载配置文件时出错: {str(e)}，请检查")
        return None

def save_config(data: Dict[str, Any]) -> bool:
    """保存配置到文件"""
    global config_data
    try:
        with open(_config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        config_data = data
        if logger:
            logger.debug(f"配置已保存到: {_config_file}")
        return True
    except Exception as e:
        if logger:
            logger.error(f"保存配置时出错: {str(e)}")
        return False

def get_config(key: str, default: Any = None) -> Any:
    """获取配置值"""
    return config_data.get(key, default)

def set_config(key: str, value: Any, auto_save: bool = True) -> bool:
    """设置配置值"""
    global config_data
    config_data[key] = value
    if auto_save:
        return save_config(config_data)
    return True

init_config_manager()
if __name__ == '__main__':
    init_config_manager()

