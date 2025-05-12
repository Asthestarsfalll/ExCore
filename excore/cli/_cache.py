from __future__ import annotations

import os

import typer

from excore import workspace

from .._misc import _create_table
from ..engine.logging import logger
from ._app import app


def _clear_cache(cache_dir: str) -> None:
    if os.path.exists(cache_dir):
        import shutil  # pylint: disable=import-outside-toplevel

        shutil.rmtree(cache_dir)
        logger.info("Cache dir {} has been cleared!", cache_dir)
    else:
        logger.warning("Cache dir {} does not exist", cache_dir)


@app.command()
def clear_cache() -> None:
    """
    Remove the cache folder which belongs to current workspace.
    """
    if not typer.confirm(
        f"Are you sure you want to clear cache of {workspace.name}?"
        f" Cache dir is {workspace.cache_dir}."
    ):
        return
    _clear_cache(workspace.cache_dir)


@app.command()
def clear_all_cache() -> None:
    """
    Remove the whole cache folder.
    """
    if not os.path.exists(workspace.cache_base_dir):
        logger.warning("Cache dir {} does not exist", workspace.cache_base_dir)
        return
    print(_create_table("Cache Names", os.listdir(workspace.cache_base_dir)))
    if not typer.confirm("Are you sure you want to clear all cache?"):
        return
    _clear_cache(workspace.cache_base_dir)


@app.command()
def cache_list() -> None:
    """
    Show cache folders.
    """
    table = _create_table("Cache Names", os.listdir(workspace.cache_base_dir))
    logger.info(table)


@app.command()
def cache_dir() -> None:
    """
    Show current cache folders.
    """
    print(workspace.cache_dir)
