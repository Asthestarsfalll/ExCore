from . import hub
from .config import build_all, load
from .constants import __author__, __version__, _cache_dir
from .logger import get_logger, logger, remove_logger
from .registry import Registry


@logger.catch
def clear_cache():
    import os
    import shutil

    if os.path.exists(_cache_dir):
        shutil.rmtree(_cache_dir)
        logger.info("Cache dir {} has been cleared!", _cache_dir)
    else:
        logger.info("Cache dir {} does not exist", _cache_dir)
