import os

import typer

from .._constants import _base_name, _cache_base_dir, _cache_dir
from ..engine.logging import logger
from ..utils.misc import _create_table
from ._app import app


def _clear_cache(cache_dir):
    if os.path.exists(cache_dir):
        import shutil  # pylint: disable=import-outside-toplevel

        shutil.rmtree(cache_dir)
        logger.info("Cache dir {} has been cleared!", cache_dir)
    else:
        logger.warning("Cache dir {} does not exist", cache_dir)


@app.command()
def clear_cache():
    """
    Remove the cache folder which belongs to current workspace.
    """
    if not typer.confirm(f"Are you sure you want to clear cache of {_base_name}?"):
        return

    target = os.path.join(_cache_dir, _base_name)
    _clear_cache(target)


@app.command()
def clear_all_cache():
    """
    Remove the whole cache folder.
    """
    if not typer.confirm("Are you sure you want to clear all cache?"):
        return
    _clear_cache(_cache_base_dir)


@app.command()
def cache_list():
    """
    Show cache folders.
    """
    tabel = _create_table("NAMES", os.listdir(_cache_base_dir))
    logger.info(tabel)


@app.command()
def cache_dir():
    # if not os.path.exists(_workspace_config_file):
    #     raise RuntimeError("Not in ExCore project")
    print(_cache_dir)
