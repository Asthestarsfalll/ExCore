from . import hub
from ._constants import __author__, __version__, _cache_dir
from .config import build_all, load_config
from .logger import add_logger, logger, remove_logger
from .registry import Registry, auto_register


@logger.catch
def clear_cache():
    import os  # pylint: disable=import-outside-toplevel
    import shutil  # pylint: disable=import-outside-toplevel

    if os.path.exists(_cache_dir):
        shutil.rmtree(_cache_dir)
        logger.info("Cache dir {} has been cleared!", _cache_dir)
    else:
        logger.info("Cache dir {} does not exist", _cache_dir)
