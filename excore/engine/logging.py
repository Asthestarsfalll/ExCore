from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

from loguru import logger as _logger

if TYPE_CHECKING:
    from typing import Any, Callable, TextIO

    from loguru import FilterDict, FilterFunction, FormatFunction, Message, Record, Writable
    from loguru._handler import Handler
    from loguru._logger import Logger

    class PatchedLogger(Logger):
        def ex(self, __message: str, *args: Any, **kwargs: Any) -> None:
            pass

        def imp(self, __message: str, *args: Any, **kwargs: Any) -> None:
            pass


__all__ = ["logger", "add_logger", "remove_logger", "debug_only", "log_to_file_only"]

LOGGERS: dict[str, int] = {}

FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>"
)


def _trace_patcher(log_record):
    if log_record["name"] == "__main__":
        log_record["name"] = log_record["file"].name
    if log_record["function"] == "<module>":
        # FIXME: This will cause log file some garbled characters.
        log_record["function"] = "\b"


logger: PatchedLogger = _logger.patch(_trace_patcher)  # type: ignore


def add_logger(
    name: str,
    sink: TextIO | Writable | Callable[[Message], None] | Handler,
    *,
    level: str | int | None = None,  # pylint: disable=unused-argument
    format: str | FormatFunction | None = None,  # pylint: disable=unused-argument
    filter: str | FilterFunction | FilterDict | None = None,  # pylint: disable=unused-argument
    colorize: bool | None = None,  # pylint: disable=unused-argument
    serialize: bool | None = None,  # pylint: disable=unused-argument
    backtrace: bool | None = None,  # pylint: disable=unused-argument
    diagnose: bool | None = None,  # pylint: disable=unused-argument
    enqueue: bool | None = None,  # pylint: disable=unused-argument
) -> None:
    params = {k: v for k, v in locals().items() if v is not None}
    params.pop("sink")
    params.pop("name")
    id = logger.add(sink, **params)
    LOGGERS[name] = id


def remove_logger(name: str) -> None:
    id = LOGGERS.pop(name, None)
    if id:
        logger.remove(id)
        logger.success(f"Remove logger whose name is {name}")
    else:
        logger.warning(f"Cannot find logger with name {name}")


def log_to_file_only(file_name: str, *args: Any, **kwargs: Any) -> None:
    logger.remove(None)
    logger.add(file_name, *args, **kwargs)
    logger.success(f"Log to file {file_name} only")


def debug_only(*args: Any, **kwargs: Any) -> None:
    def _debug_only(record: Record) -> bool:
        return record["level"].name == "DEBUG"

    filter = kwargs.pop("filter", None)
    if filter:
        logger.warning("Override filter!!!")
    logger.remove()
    logger.add(sys.stderr, *args, format=FORMAT, filter=_debug_only, **kwargs)
    logger.debug("DEBUG ONLY!!!")


def _call_importance(__message: str, *args: Any, **kwargs: Any) -> None:
    logger.log("IMPORT", __message, *args, **kwargs)


def _excore_debug(__message: str, *args: Any, **kwargs: Any) -> None:
    logger._log("EXCORE", False, logger._options, __message, args, kwargs)


def _enable_excore_debug() -> None:
    if os.getenv("EXCORE_DEBUG"):
        logger.remove()
        logger.add(sys.stdout, format=FORMAT, level="EXCORE")
        logger.ex("Enabled excore debug")


def init_logger() -> None:
    logger.remove()
    logger.add(sys.stderr, format=FORMAT)
    logger.level("SUCCESS", color="<yellow>")
    logger.level("WARNING", color="<red>")
    logger.level("IMPORT", no=45, color="<YELLOW><red><bold>")
    logger.level("EXCORE", no=9, color="<GREEN><cyan>")
    logger.imp = _call_importance  # type: ignore
    logger.ex = _excore_debug  # type: ignore
