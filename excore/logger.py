import sys

from loguru import logger

__all__ = ["logger", "add_logger", "remove_logger"]

LOGGERS = {}

FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)


def add_logger(
    name,
    sink,
    *,
    level=None,
    format=None,
    filter=None,
    colorize=None,
    serialize=None,
    backtrace=None,
    diagnose=None,
    enqueue=None,
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
        logger.success("Remove logger whose name is {}".format(name))
    else:
        logger.warning("Cannot find logger with name {}".format(name))


def log_to_file_only(file_name: str, *args, **kwargs) -> None:
    logger.remove(None)
    logger.add(file_name, *args, **kwargs)
    logger.success("Log to file {} only".format(file_name))


def debug_only(*args, **kwargs) -> None:
    def _debug_only(record):
        return record["level"].name == "DEBUG"

    logger.remove(None)
    filter = kwargs.pop("filter", None)
    if filter:
        logger.warning("Override filter")
    logger.add(sys.stderr, *args, filter=_debug_only, **kwargs)
    logger.debug("DEBUG ONLY!!!")


def init_logger():
    logger.remove(None)
    logger.add(sys.stderr, format=FORMAT)
    logger.level("SUCCESS", color="<yellow>")


init_logger()
