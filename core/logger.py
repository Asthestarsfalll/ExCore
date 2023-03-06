import sys

from loguru import logger

__all__ = ["logger", "get_logger", "remove_logger"]

LOGGERS = {}

FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)


def get_logger(
    name, sink, *, level, format, filter, colorize, serialize, backtrace, diagnose, enqueue
):
    id = logger.add(
        sink,
        level=level,
        format=format,
        filter=filter,
        colorize=colorize,
        serialize=serialize,
        backtrace=backtrace,
        diagnose=diagnose,
        enqueue=enqueue,
    )
    LOGGERS[name] = id


def remove_logger(name):
    id = LOGGERS.pop(name, None)
    if id:
        logger.remove(id)
        logger.success("Remove logger whose id is {}".format(id))
    else:
        logger.warning("Cannot find logger with id {}".format(id))


def log_to_file_only(file_name: str, *args, **kwargs) -> None:
    logger.remove(None)
    logger.add(file_name, *args, **kwargs)
    logger.success("Log to file {} only".format(file_name))


def debug_only(*args, **kwargs):
    def _debug_only(record):
        return record["level"].name == "DEBUG"

    logger.remove(None)
    logger.add(sys.stderr, *args, filter=_debug_only, **kwargs)


def init_logger():
    logger.remove(None)
    logger.add(sys.stderr, format=FORMAT)
    logger.level("SUCCESS", color="<yellow>")


init_logger()
