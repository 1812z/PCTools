import mmap
from xml.etree import ElementTree as ET
import sys


def _readRawData(length):
    with mmap.mmap(
            -1, length,  # anonymous file
            tagname='AIDA64_SensorValues',
            access=mmap.ACCESS_READ) as mm:
        return mm.read()


def _decode(b):
    for encoding in (sys.getdefaultencoding(), 'utf-8', 'gbk'):
        try:
            return b.decode(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return b.decode()


def getXmlRawData() -> str:
    options = [100 * i for i in range(20, 100)]
    low = 0
    high = len(options) - 1
    result = None

    while low <= high:  # 改为 <=
        mid = (low + high) // 2
        try:
            length = options[mid]
            raw = _readRawData(length)
            if raw[-1] == 0:  # 找到有效长度
                decoded = _decode(raw.rstrip(b'\x00'))
                result = '<root>{}</root>'.format(decoded)
                high = mid - 1  # 继续寻找更小的有效长度
            else:  # 不够长
                low = mid + 1  # ✅ 修复
        except (PermissionError, OSError):  # 处理更多异常
            high = mid - 1

    if result is None:
        raise RuntimeError("无法读取AIDA64共享内存数据")
    return result


def getData() -> dict:
    data = {}
    tree = ET.fromstring(getXmlRawData())

    for item in tree:
        if item.tag not in data:
            data[item.tag] = []
        data[item.tag].append({
            key: item.find(key).text
            for key in ('id', 'label', 'value')
        })
    return data


__all__ = [
    'getXmlRawData',
    'getData'
]
