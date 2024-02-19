import ast
import importlib
import os
import os.path as osp
import sys

import astor
import typer
from typer import Argument as CArg
from typing_extensions import Annotated

from .._constants import _cache_base_dir, _workspace_cfg, _workspace_config_file
from ..engine.logging import logger
from ..engine.registry import Registry
from ..utils.misc import _create_table
from ._app import app


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
    if not _workspace_cfg["primary_fields"]:
        return
    logger.info("Generating Registry definition code.")
    target_file = osp.join(_workspace_cfg["src_dir"], entry + ".py")

    if not osp.exists(target_file):
        with open(target_file, "w", encoding="UTF-8") as f:
            f.write("")

    with open(target_file, encoding="UTF-8") as f:
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
    logger.success("Generate Registry definition in {} according to `primary_fields`", target_file)


def _detect_assign(node, definition):
    if isinstance(node, ast.Module):
        for child in node.body:
            _detect_assign(child, definition)
    elif (
        isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Call)
        and hasattr(node.value.func, "id")
        and node.value.func.id == "Registry"
    ):
        definition.append(node.value.args[0].value)


def _detect_registy_difinition() -> bool:
    target_file = osp.join(_workspace_cfg["src_dir"], "__init__.py")
    logger.info("Detect Registry definition in {}", target_file)
    definition = []
    with open(target_file, encoding="UTF-8") as f:
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


def _parse_registries(reg_and_fields):
    fields = [i[1:].split(":") for i in reg_and_fields if i.startswith("*")]
    targets = []
    rev = {}
    json_schema = {}
    isolated_fields = []
    for i in fields:
        if len(i) == 1:
            targets.append(i[0])
            isolated_fields.append(i[0])
        else:
            tar = [j.strip() for j in i[1].split(",")]
            json_schema[i[0]] = tar
            for j in tar:
                rev[j] = i[0]
            targets.extend(tar)
    json_schema["isolated_fields"] = isolated_fields
    return targets, rev, json_schema


def _get_registries(reg_and_fields):
    return [i.split(":")[0] for i in reg_and_fields]


def _update(is_init=True, entry="__init__"):
    target_dir = osp.join(_cache_base_dir, _workspace_cfg["name"])
    os.makedirs(target_dir, exist_ok=True)
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
            (
                _workspace_cfg["primary_fields"],
                _workspace_cfg["primary_to_registry"],
                _workspace_cfg["json_schema_fields"],
            ) = _parse_registries(_workspace_cfg["registries"])
            _generate_registries(entry)
        else:
            logger.imp(
                "Please modify registries in .excore.toml and "
                "run `excore update` to generate `primary_fields`"
            )
    else:
        (
            _workspace_cfg["primary_fields"],
            _workspace_cfg["primary_to_registry"],
            _workspace_cfg["json_schema_fields"],
        ) = _parse_registries([_format(i) for i in _workspace_cfg["registries"]])
        logger.success("Update primary_fields")


def _get_default_module_name(target_dir):
    assert os.path.isdir(target_dir)
    full_path = os.path.abspath(target_dir)
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
        logger.critical("Please run `excore init` in your command line first!")
        sys.exit(0)
    target_dir = osp.abspath(_workspace_cfg["src_dir"])
    module_name = _get_default_module_name(target_dir)
    sys.path.append(os.getcwd())
    _auto_register(target_dir, module_name)
    Registry.dump()


@app.command()
def primary_fields():
    """
    Show primary_fields.
    """
    table = _create_table("FIELDS", _parse_registries(_workspace_cfg["registries"])[0])
    logger.info(table)


@app.command()
def registries():
    """
    Show registries.
    """
    table = _create_table("Registry", [_format(i) for i in _workspace_cfg["registries"]])
    logger.info(table)


@app.command()
def generate_registries(
    entry: Annotated[
        str, CArg(help="Used for detect or generate Registry definition code")
    ] = "__init__",
):
    """
    Generate registries definition code according to workspace config.
    """
    _generate_registries(entry)
