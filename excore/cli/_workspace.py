import os
import os.path as osp

import toml
import typer
from typer import Argument as CArg
from typer import Option as COp
from typing_extensions import Annotated

from .._constants import (
    LOGO,
    _base_name,
    _cache_base_dir,
    _cache_dir,
    _workspace_cfg,
    _workspace_config_file,
)
from ..engine.logging import logger
from ._app import app
from ._registry import _update


def _dump_workspace_config():
    logger.info("Dump config to {}", _workspace_config_file)
    # TODO: Add props which can be used in config ?
    _workspace_cfg["props"] = dict()
    with open(_workspace_config_file, "w", encoding="UTF-8") as f:
        toml.dump(_workspace_cfg, f)


@app.command()
def update():
    """
    Update workspace config file.
    """
    _update(False)
    _dump_workspace_config()


@app.command()
def init(
    force: Annotated[bool, COp(help="Whther forcely initialize workspace")] = False,
    entry: Annotated[
        str, CArg(help="Used for detect or generate Registry definition code")
    ] = "__init__",
):
    """
    Initialize workspace and generate a config file.
    """
    if osp.exists(_cache_dir) and not force:
        logger.warning("excore.toml already existed!")
        return
    cwd = os.getcwd()
    logger.success(LOGO)
    logger.opt(colors=True).info(
        "This command will guide you to create your <cyan>excore.toml</cyan> config",
        colors=True,
    )
    logger.opt(colors=True).info(f"It will be generated in <cyan>{cwd}</cyan>\n")
    logger.opt(colors=True).info(f"WorkSpace Name [<green>{_base_name}</green>]:")
    name = typer.prompt("", default=_base_name, show_default=False, prompt_suffix="")
    if not force and os.path.exists(os.path.join(_cache_base_dir, _base_name)):
        logger.warning(f"name {name} already existed!")
        return

    logger.opt(colors=True).info("Source Code Directory(relative path):")
    src_dir = typer.prompt("", prompt_suffix="")

    _workspace_cfg["name"] = name
    _workspace_cfg["src_dir"] = src_dir

    _update(True, entry)
    _dump_workspace_config()

    logger.success("Welcome to ExCore. You can modify the `.excore.toml` file mannully.")
