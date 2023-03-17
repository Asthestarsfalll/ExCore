from typing import List
from enum import Enum
from pynvml import nvmlInit, nvmlShutdown
from pynvml import (
    nvmlDeviceGetName as get_device_name,
    nvmlDeviceGetHandleByIndex as get_device_handle,
    nvmlDeviceGetCount as get_device_count,
    nvmlDeviceGetMemoryInfo as _get_memory_info,
    nvmlDeviceGetTemperature as _get_device_temperature,
    nvmlDeviceGetPowerState as _get_device_powerstate,
)

__all__ = [
    "get_device_handle",
    "get_device_name",
    "get_device_count",
    "get_device",
    "get_memory_info",
    "get_device_powerstate",
    "get_device_temperature",
    "nvmlShutdown",
    "Size",
]

nvmlInit()

DEVICE_COUNTS = get_device_count()


class Size(Enum):
    B = 0
    KB = 1
    MB = 2
    GB = 3


def get_device() -> List:
    num_device = get_device_count()
    return [get_device_name(get_device_handle(i)) for i in range(num_device)]


def _format_memory(value: int, tartget_size: Size = Size.GB) -> float:
    fvalue = float(value)
    for _ in range(tartget_size.value + 1):
        fvalue /= 1024
    return fvalue


def get_memory_info(idx: int, format_size=Size.GB):
    handle = get_device_handle(idx)
    info = _get_memory_info(handle)
    memory_info = [info.total, info.free, info.used]
    memory_info = [_format_memory(i, format_size) for i in memory_info]
    return memory_info


def get_device_temperature(idx: int) -> int:
    handle = get_device_handle(idx)
    return _get_device_temperature(handle, 0)


def get_device_powerstate(idx: int) -> int:
    handle = get_device_handle(idx)
    return _get_device_powerstate(handle)
