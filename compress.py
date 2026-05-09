#!/usr/bin/env python3
"""
自动压缩src目录脚本
压缩包内直接包含所有文件，不包含src文件夹
忽略config.json文件和Python缓存文件
"""

import os
import zipfile
import datetime
import argparse
from pathlib import Path
import fnmatch

# 定义要忽略的文件和目录模式
IGNORE_PATTERNS = [
    # 配置文件
    'config.json',
    '**/config.json',

    # Python缓存
    '__pycache__',
    '**/__pycache__',
    '**/__pycache__/**',
    '*.pyc',
    '**/*.pyc',
    '*.pyo',
    '**/*.pyo',

    # IDE和编辑器
    '.idea',
    '.idea/**',
    '.vscode',
    '.vscode/**',
    '*.swp',
    '*.swo',
    '*~',
    '.DS_Store',
    'Thumbs.db',

    # Git
    '.git',
    '.git/**',
    '.gitignore',

    # 测试和文档
    '.pytest_cache',
    '.pytest_cache/**',
    '.coverage',
    'htmlcov',
    'htmlcov/**',
    '.tox',
    '.tox/**',

    # 构建目录
    'build',
    'build/**',
    'dist',
    'dist/**',
    '*.egg',

    # 日志文件
    '*.log',
    '**/*.log',

    # 临时文件
    '*.tmp',
    '**/*.tmp',
    '*.temp',
    '**/*.temp',
]


def should_ignore(file_path, base_path):
    """
    检查文件是否应该被忽略

    Args:
        file_path: 文件的完整路径
        base_path: 基础目录路径（src目录）

    Returns:
        bool: True如果应该忽略，False否则
    """
    # 获取相对路径
    try:
        rel_path = os.path.relpath(file_path, base_path)
    except ValueError:
        return True

    # 转换为使用正斜杠的路径（统一处理）
    rel_path = rel_path.replace(os.sep, '/')

    # 检查是否匹配任何忽略模式
    for pattern in IGNORE_PATTERNS:
        # 处理目录模式
        if pattern.endswith('/**'):
            dir_pattern = pattern[:-3]
            if rel_path.startswith(dir_pattern + '/') or rel_path == dir_pattern:
                return True

        # 使用fnmatch进行通配符匹配
        if fnmatch.fnmatch(rel_path, pattern):
            return True

        # 检查路径的每个部分
        path_parts = rel_path.split('/')
        for part in path_parts:
            if fnmatch.fnmatch(part, pattern.replace('**/', '').replace('**/', '').replace('/**', '')):
                return True

    return False


def compress_directory(src_dir, output_file=None, verbose=False):
    """
    压缩指定目录，忽略配置文件和缓存
    压缩包内直接包含所有文件，不包含src文件夹

    Args:
        src_dir: 源目录路径
        output_file: 输出文件名（可选）
        verbose: 是否显示详细信息

    Returns:
        str: 创建的压缩文件路径
    """
    # 确保源目录存在
    src_path = Path(src_dir).resolve()
    if not src_path.exists():
        raise FileNotFoundError(f"源目录不存在: {src_dir}")
    if not src_path.is_dir():
        raise NotADirectoryError(f"不是目录: {src_dir}")

    # 生成输出文件名
    if output_file is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{src_path.name}_{timestamp}.zip"

    # 确保输出文件有.zip扩展名
    if not output_file.endswith('.zip'):
        output_file += '.zip'

    # 统计信息
    total_files = 0
    ignored_files = 0
    compressed_files = 0

    # 创建ZIP文件
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for root, dirs, files in os.walk(src_path):
            # 过滤目录（原地修改dirs以影响os.walk的遍历）
            dirs_to_remove = []
            for d in dirs:
                dir_path = os.path.join(root, d)
                if should_ignore(dir_path, src_path):
                    dirs_to_remove.append(d)
                    if verbose:
                        print(f"忽略目录: {os.path.relpath(dir_path, src_path)}")

            for d in dirs_to_remove:
                dirs.remove(d)

            # 处理文件
            for file in files:
                total_files += 1
                file_path = os.path.join(root, file)

                if should_ignore(file_path, src_path):
                    ignored_files += 1
                    if verbose:
                        print(f"忽略文件: {os.path.relpath(file_path, src_path)}")
                    continue

                # 添加文件到压缩包（直接放入根目录）
                arcname = os.path.relpath(file_path, src_path)
                zipf.write(file_path, arcname)
                compressed_files += 1
                if verbose:
                    print(f"添加文件: {os.path.relpath(file_path, src_path)}")

    # 获取压缩文件大小
    zip_size = os.path.getsize(output_file)
    zip_size_mb = zip_size / (1024 * 1024)

    # 打印统计信息
    print("\n" + "=" * 50)
    print("压缩完成！")
    print(f"源目录: {src_dir}")
    print(f"输出文件: {output_file}")
    print(f"文件大小: {zip_size_mb:.2f} MB")
    print("-" * 50)
    print(f"总文件数: {total_files}")
    print(f"已压缩: {compressed_files}")
    print(f"已忽略: {ignored_files}")
    print("=" * 50)

    return output_file


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='压缩src目录，自动忽略config.json和Python缓存文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python compress_src.py                    # 压缩当前目录下的src目录
  python compress_src.py /path/to/src       # 压缩指定的src目录
  python compress_src.py -o backup.zip      # 指定输出文件名
  python compress_src.py -v                 # 显示详细信息
  python compress_src.py --list-ignore      # 列出所有忽略模式
        """
    )

    parser.add_argument(
        'src_dir',
        nargs='?',
        default='src',
        help='要压缩的源目录 (默认: src)'
    )

    parser.add_argument(
        '-o', '--output',
        help='输出文件名 (默认: src_YYYYMMDD_HHMMSS.zip)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='显示详细信息'
    )

    parser.add_argument(
        '--list-ignore',
        action='store_true',
        help='列出所有忽略模式并退出'
    )

    args = parser.parse_args()

    # 如果请求列出忽略模式
    if args.list_ignore:
        print("忽略模式列表:")
        print("=" * 50)
        categories = {
            '配置文件': ['config.json', '**/config.json'],
            'Python缓存': ['__pycache__', '*.pyc', '*.pyo'],
            'Python包信息': ['*.egg-info', '*.egg'],
            '虚拟环境': ['venv', 'env', '.env', '.venv'],
            'IDE文件': ['.idea', '.vscode', '*.swp', '.DS_Store'],
            'Git文件': ['.git', '.gitignore'],
            '测试相关': ['.pytest_cache', '.coverage', 'htmlcov', '.tox'],
            '构建目录': ['build', 'dist'],
            '日志文件': ['*.log'],
            '临时文件': ['*.tmp', '*.temp']
        }

        for category, patterns in categories.items():
            print(f"\n{category}:")
            for pattern in patterns:
                if pattern in IGNORE_PATTERNS:
                    print(f"  - {pattern}")
        return

    try:
        # 执行压缩
        output_file = compress_directory(
            args.src_dir,
            args.output,
            args.verbose
        )

        print(f"\n✅ 成功创建压缩文件: {output_file}")

    except FileNotFoundError as e:
        print(f"\n❌ 错误: {e}")
        print(f"请确保目录 '{args.src_dir}' 存在")
        return 1
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
