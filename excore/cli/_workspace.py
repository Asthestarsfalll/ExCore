import os
import os.path as osp

import typer
from typer import Argument as CArg
from typer import Option as COp
from typing_extensions import Annotated

from .._constants import LOGO, _workspace_config_file, workspace
from ..engine.logging import logger
from ._app import app
from ._registry import _update


def _dump_workspace_config() -> None:
    logger.info("Dump config to {}", _workspace_config_file)
    workspace.dump(_workspace_config_file)


@app.command()
def update() -> None:
    """
    Update workspace config file.
    """
    _update(False)
    _dump_workspace_config()


@app.command()
def init(
    force: Annotated[bool, COp(help="Whether forcibly initialize workspace")] = False,
    entry: Annotated[
        str, CArg(help="Used for detect or generate Registry definition code")
    ] = "__init__",
) -> None:
    """
    Initialize workspace and generate a config file.
    """
    if osp.exists(_workspace_config_file) and not force:
        logger.warning("excore.toml already existed!")
        return
    cwd = os.getcwd()
    logger.success(LOGO)
    logger.opt(colors=True).info(
        "This command will guide you to create your <cyan>excore.toml</cyan> config",
        colors=True,
    )
    logger.opt(colors=True).info(f"It will be generated in <cyan>{cwd}</cyan>\n")
    logger.opt(colors=True).info(f"WorkSpace Name [<green>{workspace.base_name}</green>]:")
    name = typer.prompt("", default=workspace.base_name, show_default=False, prompt_suffix="")
    if not force and os.path.exists(workspace.cache_dir):
        logger.warning(f"name {name} already existed!")
        return

    logger.opt(colors=True).info("Source Code Directory(relative path):")
    src_dir = typer.prompt("", prompt_suffix="")

    workspace.name = name
    workspace.src_dir = src_dir

    _update(True, entry)
    _dump_workspace_config()

    logger.success("Welcome to ExCore. You can modify the `.excore.toml` file mannully.")
