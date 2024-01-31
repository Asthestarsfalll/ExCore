from typing import Any

from ._constants import _recorder_cache_file
from .logger import logger
from .registry import Registry
from .utils import _create_table

RECORDERS = Registry("__recorder")


class RecorderItem:
    def __init__(self) -> None:
        self.data = {}

    def add(self, header: str, value: Any):
        self.data[header] = value

    def reset(self):
        self.data = {}

    def __setstate__(self, state):
        state = {"data": state["data"] or {}}
        self.__dict__.update(state)

    def __str__(self) -> str:
        if not self.data:
            return "Empty Recorder."
        return _create_table(None, list(self.data.items()), False)


def create(name: str):
    if name not in RECORDERS:
        RECORDERS[name] = RecorderItem()
    else:
        logger.info(f"Recorder {name} already existed.")


def add(recorder_name: str, header: str, value: Any):
    if recorder_name not in RECORDERS:
        logger.info(f"Recorder {recorder_name} doesn't exist.")
        return
    RECORDERS[recorder_name].add(header, value)


def remove():
    RECORDERS.clear()


def dump():
    RECORDERS.dump(_recorder_cache_file, RECORDERS)


def load():
    RECORDERS.load(_recorder_cache_file, RECORDERS, True)
