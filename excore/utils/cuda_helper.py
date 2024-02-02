from enum import Enum
from typing import List

from pynvml import (
    nvmlDeviceGetCount,  # noqa
    nvmlInit,
    nvmlShutdown,
)
from pynvml import nvmlDeviceGetHandleByIndex as get_device_handle
from pynvml import nvmlDeviceGetMemoryInfo as _get_memory_info
from pynvml import nvmlDeviceGetName as get_device_name
from pynvml import nvmlDeviceGetPowerState as _get_device_powerstate
from pynvml import nvmlDeviceGetTemperature as _get_device_temperature

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

IS_INIT = False


def _init_nvml(func):
    global IS_INIT  # pylint: disable=global-statement
    if not IS_INIT:
        nvmlInit()
        IS_INIT = True
    return func


@_init_nvml
class Size(Enum):
    B = 0
    KB = 1
    MB = 2
    GB = 3


get_device_count = _init_nvml(nvmlDeviceGetCount)


@_init_nvml
def get_device() -> List:
    num_device = get_device_count()
    return [get_device_name(get_device_handle(i)) for i in range(num_device)]


def _format_memory(value: int, tartget_size: Size = Size.GB) -> float:
    fvalue = float(value)
    for _ in range(tartget_size.value + 1):
        fvalue /= 1024
    return fvalue


@_init_nvml
def get_memory_info(idx: int, format_size=Size.GB):
    handle = get_device_handle(idx)
    info = _get_memory_info(handle)
    memory_info = [info.total, info.free, info.used]
    memory_info = [_format_memory(i, format_size) for i in memory_info]
    return memory_info


@_init_nvml
def get_device_temperature(idx: int) -> int:
    handle = get_device_handle(idx)
    return _get_device_temperature(handle, 0)


@_init_nvml
def get_device_powerstate(idx: int) -> int:
    handle = get_device_handle(idx)
    return _get_device_powerstate(handle)
