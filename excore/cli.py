import ast
import importlib
import os
import os.path as osp
import sys

import astor
import toml
import typer
from tabulate import tabulate
from typer import Argument as CArg
from typer import Option as COp
from typing_extensions import Annotated

from ._constants import (LOGO, _base_name, _cache_base_dir, _cache_dir,
                         _workspace_cfg, _workspace_config_file)
from ._json_schema import _generate_json_shcema, _generate_taplo_config
from .logger import logger
from .registry import Registry

app = typer.Typer(rich_markup_mode="rich")


def _dump_workspace_config():
    logger.info("Dump config to {}", _workspace_config_file)
    # TODO: Add props which can be used in config ?
    _workspace_cfg["props"] = dict()
    with open(_workspace_config_file, "w", encoding="UTF-8") as f:
        toml.dump(_workspace_cfg, f)


def _has_import_excore(node):
    if isinstance(node, ast.Module):
        for child in node.body:
            f = _has_import_excore(child)
            if f:
                return f
    elif isinstance(node, ast.ImportFrom) and node.module == "excore":
        for name in node.names:
            if name.name == "Registry":
                break
        else:
            node.names.append(type(node.names[0])("Registry"))
        return True
    return False


def _build_ast(name: str) -> ast.Assign:
    targets = [ast.Name(name.upper(), ast.Store)]
    func = ast.Name("Registry", ast.Load)
    args = [ast.Constant(name)]
    value = ast.Call(func, args, [])
    return ast.Assign(targets, value)


def _generate_registries(entry="__init__"):
    if not _workspace_cfg["target_fields"]:
        return
    logger.info("Generating Registry definition code.")
    target_file = osp.join(_workspace_cfg["src_dir"], entry + ".py")

    if not osp.exists(target_file):
        with open(target_file, "w", encoding="UTF-8") as f:
            f.write("")

    with open(target_file, "r", encoding="UTF-8") as f:
        source_code = ast.parse(f.read())
    flag = _has_import_excore(source_code)
    if flag == 1:
        logger.info("Detect excore.Registry imported.")
    else:
        name = [ast.alias("Registry", None)]
        source_code.body.insert(0, ast.ImportFrom("excore", name, 0))

    for name in _get_registries(_workspace_cfg["registries"]):
        if name.startswith("*"):
            name = name[1:]
        source_code.body.append(_build_ast(name))
    source_code = astor.to_source(source_code)
    with open(target_file, "w", encoding="UTF-8") as f:
        f.write(source_code)
    logger.success(
        "Generate Registry definition in {} according to `target_fields`", target_file
    )


def _detect_assign(node, definition):
    if isinstance(node, ast.Module):
        for child in node.body:
            _detect_assign(child, definition)
    elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
        if hasattr(node.value.func, "id") and node.value.func.id == "Registry":
            definition.append(node.value.args[0].value)


def _detect_registy_difinition() -> bool:
    target_file = osp.join(_workspace_cfg["src_dir"], "__init__.py")
    logger.info("Detect Registry definition in {}", target_file)
    definition = []
    with open(target_file, "r", encoding="UTF-8") as f:
        source_code = ast.parse(f.read())
    _detect_assign(source_code, definition)
    if len(definition) > 0:
        logger.info("Find Registry definition: {}", definition)
        _workspace_cfg["registries"] = definition
        return True
    return False


def _format(reg_and_fields: str) -> str:
    splits = reg_and_fields.split(":")
    if len(splits) == 1:
        return reg_and_fields.strip()
    fields = [i.strip() for i in splits[1].split(",")]
    return splits[0] + ": " + ", ".join(fields)


def _get_target_fields(reg_and_fields):
    fields = [i[1:].split(":") for i in reg_and_fields if i.startswith("*")]
    targets = []
    for i in fields:
        if len(i) == 1:
            targets.append(i[0])
        else:
            targets.extend([j.strip() for j in i[1].split(",")])
    return targets


def _get_registries(reg_and_fields):
    return [i.split(":")[0] for i in reg_and_fields]


def _update(is_init=True, entry="__init__"):
    target_dir = osp.join(_cache_base_dir, _workspace_cfg["name"])
    os.makedirs(target_dir, exist_ok=True)
    _generate_taplo_config(target_dir)
    logger.success("Generate `.taplo.toml`")
    if is_init:
        if not _detect_registy_difinition():
            if typer.confirm("Do you want to define `Registry` and `fields`?"):
                regs = []
                while True:
                    inp = input("Please input: ")
                    if inp:
                        regs.append(_format(inp))
                    else:
                        break
                _workspace_cfg["registries"] = regs
            else:
                logger.imp("You can define fields later.")
            _workspace_cfg["target_fields"] = _get_target_fields(
                _workspace_cfg["registries"]
            )
            _generate_registries(entry)
        else:
            logger.imp(
                "Please modify registries in .excore.toml and "
                "run `excore update` to generate `target_fields`"
            )
    else:
        _workspace_cfg["target_fields"] = _get_target_fields(
            [_format(i) for i in _workspace_cfg["registries"]]
        )
        logger.success("Update target_fields")
    _dump_workspace_config()


@app.command()
def update():
    """
    Update workspace config file.
    """
    _update(False)


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


def _build_table(header, _cache_dir):
    table = tabulate(
        [(i,) for i in _cache_dir],
        headers=[header],
        tablefmt="fancy_grid",
    )
    logger.info("\n{}", table)


@app.command()
def cache_list():
    """
    Show cache folders.
    """
    _build_table("NAMES", os.listdir(_cache_base_dir))


def _get_default_module_name(target_dir):
    assert os.path.isdir(target_dir)
    full_path = os.path.abspath(target_dir)
    # return ".".join(full_path.split(os.sep)[-2:])
    return full_path.split(os.sep)[-1]


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
    """
    Automatically import all modules in `src_dir` and register all modules, then dump to files.
    """
    if not os.path.exists(_workspace_config_file):
        logger.warning("Please run `excore init` in your command line first!")
    target_dir = osp.abspath(_workspace_cfg["src_dir"])
    module_name = _get_default_module_name(target_dir)
    sys.path.append(os.getcwd())
    _auto_register(target_dir, module_name)
    Registry.dump()


@app.command()
def config_completion():
    """
    Generate json_schema for config completion.
    """
    if not _workspace_cfg["json_schema_fields"]:
        logger.warning("You should set json_schema_fields first")
        return
    _generate_json_shcema(_workspace_cfg["json_schema_fields"])


@app.command()
def target_fields():
    """
    Show target_fields.
    """
    _build_table("FIELDS", _get_target_fields(_workspace_cfg["registries"]))


@app.command()
def registries():
    """
    Show registries.
    """
    _build_table("Registry", [_format(i) for i in _workspace_cfg["registries"]])


@app.command()
def generate_registries(
    entry: Annotated[
        str, CArg(help="Used for detect or generate Registry definition code")
    ] = "__init__"
):
    """
    Generate registries definition code according to workspace config.
    """
    _generate_registries(entry)


if __name__ == "__main__":
    app()
