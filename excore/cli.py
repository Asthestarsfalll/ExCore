import importlib
import os
import os.path as osp

import toml
import typer
from loguru import logger
from typer import Option as COp
from typing_extensions import Annotated

from ._constants import (LOGO, _base_name, _cache_base_dir, _cache_dir,
                         _workspace_cfg, _workspace_config_file)
from ._json_schema import _generate_json_shcema, _generate_taplo_config
from .registry import Registry

app = typer.Typer(rich_markup_mode="rich")


def _dump_workspace_config(name, src_dir):
    _workspace_cfg["name"] = name
    _workspace_cfg["src_dir"] = src_dir
    _workspace_cfg["base_dir"] = os.getcwd()
    _workspace_cfg["fields"] = dict()
    _workspace_cfg["props"] = dict()
    with open(_workspace_config_file, "w", encoding="UTF-8") as f:
        toml.dump(_workspace_cfg, f)


def _load_workspace_config():
    if osp.exists(_workspace_config_file):
        _workspace_cfg.update(toml.load(_workspace_config_file))
        logger.success("load `.excore.toml`")
    else:
        logger.warning("Please use `excore init` in your command line first")


@app.command()
def init(force: Annotated[bool, COp()] = False):
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
    os.makedirs(osp.join(_cache_base_dir, name), exist_ok=True)
    _generate_taplo_config(osp.join(_cache_base_dir, _base_name))

    if typer.confirm("Do you want to define fields?"):
        fields = []
        while True:
            inp = input("Please input field:")
            if inp:
                fields.append(inp)
            else:
                break
        _workspace_cfg["target_fields"] = fields
    else:
        logger.info("You can define fields later.")

    _dump_workspace_config(name, src_dir)

    logger.success(
        "Welcome to ExCore. You can modify the `.excore.toml` file mannully."
    )


def _clear_cache(cache_dir):
    if os.path.exists(cache_dir):
        import shutil  # pylint: disable=import-outside-toplevel

        shutil.rmtree(cache_dir)
        logger.info("Cache dir {} has been cleared!", cache_dir)
    else:
        logger.warning("Cache dir {} does not exist", cache_dir)


@app.command()
def clear_cache():
    if not typer.confirm(f"Are you sure you want to clear cache of {_base_name}?"):
        return

    target = os.path.join(_cache_dir, _base_name)
    _clear_cache(target)


@app.command()
def clear_all_cache():
    if not typer.confirm("Are you sure you want to clear all cache?"):
        return
    _clear_cache(_cache_base_dir)


@app.command()
def cache_list():
    from tabulate import tabulate  # pylint: disable=import-outside-toplevel

    caches = os.listdir(_cache_dir)
    table = tabulate(
        [(i,) for i in caches],
        headers=["NAMES"],
        tablefmt="fancy_grid",
    )
    logger.info("\n{}", table)


def _get_default_module_name(target_dir):
    assert os.path.isdir(target_dir)
    full_path = os.path.abspath(target_dir)
    return ".".join(full_path.split(os.sep)[-2:])


def _auto_register(target_dir, module_name):
    for file_name in os.listdir(target_dir):
        full_path = os.path.join(target_dir, file_name)
        if os.path.isdir(full_path):
            _auto_register(full_path, module_name + "." + file_name)
        elif file_name.endswith(".py") and file_name != "__init__.py":
            import_name = module_name + "." + file_name[:-3]
            logger.info("Register file {}", import_name)
            importlib.import_module(import_name)


@app.command()
def auto_register():
    if not os.path.exists(_workspace_config_file):
        logger.warning("Please run `excore init` in your command line first!")
    target_dir = _workspace_cfg["src_dir"]
    module_name = _get_default_module_name(target_dir)
    _auto_register(osp.abspath(target_dir), module_name)
    Registry.dump()


@app.command()
def config_completion():
    if not _workspace_cfg["json_schema_fields"]:
        logger.warning("You should set json_schema_fields first")
        return
    _generate_json_shcema(_workspace_cfg["json_schema_fields"])


if __name__ == "__main__":
    app()
