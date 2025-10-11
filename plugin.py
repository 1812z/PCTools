import os
import shutil
from pathlib import Path

def convert_plugin_structure(plugins_dir="plugins"):
    """
    将插件结构从旧版(使用__init__.py或main.py)转换为新版(使用插件名.py)
    参数:
        plugins_dir: 插件目录路径
    """
    plugins_path = Path(plugins_dir)
    
    if not plugins_path.exists():
        print(f"❌ 插件目录不存在: {plugins_path}")
        return
    
    print(f"🔍 正在扫描插件目录: {plugins_path}")
    
    # 遍历插件目录下的所有文件夹
    for plugin_dir in plugins_path.iterdir():
        if not plugin_dir.is_dir() or plugin_dir.name.startswith('_'):
            continue
        
        print(f"\n🔄 处理插件: {plugin_dir.name}")
        
        old_files = {
            "init": plugin_dir / "__init__.py",
            "main": plugin_dir / "main.py"
        }
        
        # 确定新文件名(插件名.py)
        new_file = plugin_dir / f"{plugin_dir.name}.py"
        
        # 检查是否已经是新结构
        if new_file.exists():
            print(f"✅ 已经是新结构: {new_file.name} 已存在")
            continue
        
        # 检查旧文件是否存在
        if old_files["init"].exists():
            source_file = old_files["init"]
            print(f"📁 找到旧结构文件: {source_file.name}")
        elif old_files["main"].exists():
            source_file = old_files["main"]
            print(f"📁 找到旧结构文件: {source_file.name}")
        else:
            print(f"⚠️ 未找到可转换的入口文件(需有__init__.py或main.py)")
            continue
        
        # 重命名文件
        try:
            source_file.rename(new_file)
            print(f"✅ 成功重命名为: {new_file.name}")
            
            # 检查并修复import语句
            fix_imports_in_plugin(new_file, plugin_dir.name)
            
            # 清理可能的__pycache__文件夹
            pycache = plugin_dir / "__pycache__"
            if pycache.exists():
                shutil.rmtree(pycache)
                print(f"🧹 已清理 __pycache__")
                
        except Exception as e:
            print(f"❌ 重命名失败: {str(e)}")

def fix_imports_in_plugin(plugin_file, plugin_name):
    """
    修复插件文件中的相对导入语句
    参数:
        plugin_file: 插件文件路径
        plugin_name: 插件名称
    """
    try:
        with open(plugin_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换从旧模块名的导入
        old_module_names = ["main", "__init__"]
        for old_name in old_module_names:
            pattern = f"from {old_name} import"
            replacement = f"from {plugin_name} import"
            content = content.replace(pattern, replacement)
            
            pattern = f"from .{old_name} import"
            content = content.replace(pattern, replacement)
            
            pattern = f"import {old_name}"
            replacement = f"import {plugin_name}"
            content = content.replace(pattern, replacement)
        
        # 保存修改后的内容
        with open(plugin_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"🔧 已修复文件内的导入语句")
    except Exception as e:
        print(f"⚠️ 修复导入语句时出错: {str(e)}")

def main():
    print("🛠️ 插件结构转换工具")
    print("将把以下文件结构:")
    print("plugins/A/__init__.py 或 plugins/A/main.py")
    print("转换为:")
    print("plugins/A/A.py")
    
    plugins_dir = input("请输入插件目录路径(默认为'plugins'): ") or "plugins"
    
    confirm = input(f"确定要转换 {plugins_dir} 下的所有插件吗? (y/n): ").lower()
    if confirm != 'y':
        print("❌ 操作已取消")
        return
    
    convert_plugin_structure(plugins_dir)
    print("\n🎉 转换完成!")

if __name__ == "__main__":
    main()
