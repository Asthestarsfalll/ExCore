from __future__ import annotations

import ast
import importlib
import os
import os.path as osp
import sys
from typing import Any

import astor  # type: ignore
import typer
from typer import Argument as CArg
from typing_extensions import Annotated

from .._constants import _workspace_config_file, workspace
from .._misc import _create_table
from ..engine.logging import logger
from ..engine.registry import Registry
from ._app import app


def _has_import_excore(node) -> bool:
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
    targets = [ast.Name(name.upper(), ast.Store)]  # type: ignore
    func = ast.Name("Registry", ast.Load)  # type: ignore
    args = [ast.Constant(name)]
    value = ast.Call(func, args, [])  # type: ignore
    return ast.Assign(targets, value)  # type: ignore


def _generate_registries(entry="__init__"):
    if not workspace.primary_fields:
        return
    logger.info("Generating Registry definition code.")
    target_file = osp.join(workspace.src_dir, entry + ".py")

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

    for name in _get_registries(workspace.registries):
        if name.startswith("*"):
            name = name[1:]
        source_code.body.append(_build_ast(name))
    source_code = astor.to_source(source_code)
    with open(target_file, "w", encoding="UTF-8") as f:
        f.write(source_code)
    logger.success("Generate Registry definition in {} according to `primary_fields`", target_file)


def _detect_assign(node: ast.AST, definition: list) -> None:
    if isinstance(node, ast.Module):
        for child in node.body:
            _detect_assign(child, definition)
    elif (
        isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Call)
        and hasattr(node.value.func, "id")
        and node.value.func.id == "Registry"
    ):
        definition.append(node.value.args[0].value)  # type: ignore


def _detect_registry_definition() -> bool:
    target_file = osp.join(workspace.src_dir, "__init__.py")
    logger.info("Detect Registry definition in {}", target_file)
    definition: list[Any] = []
    with open(target_file, encoding="UTF-8") as f:
        source_code = ast.parse(f.read())
    _detect_assign(source_code, definition)
    if len(definition) > 0:
        logger.info("Find Registry definition: {}", definition)
        workspace.registries = definition
        return True
    return False


def _format(reg_and_fields: str) -> str:
    splits = reg_and_fields.split(":")
    if len(splits) == 1:
        return reg_and_fields.strip()
    fields = [i.strip() for i in splits[1].split(",")]
    return splits[0] + ": " + ", ".join(fields)


def _parse_registries(
    reg_and_fields: list[str],
) -> tuple[list[str], dict[Any, Any], dict[Any, Any]]:
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
    return list(set(targets)), rev, json_schema


def _get_registries(reg_and_fields) -> list[str]:
    return [i.split(":")[0] for i in reg_and_fields]


def _update(is_init: bool = True, entry: str = "__init__") -> None:
    os.makedirs(workspace.cache_dir, exist_ok=True)
    logger.success("Generate `.taplo.toml`")
    if is_init:
        if not _detect_registry_definition():
            if typer.confirm("Do you want to define `Registry` and `fields`?"):
                regs = []
                while True:
                    inp = input("Please input: ")
                    if inp:
                        regs.append(_format(inp))
                    else:
                        break
                workspace.registries = regs
            else:
                logger.imp("You can define fields later.")
            (
                workspace.primary_fields,
                workspace.primary_to_registry,
                workspace.json_schema_fields,
            ) = _parse_registries(workspace.registries)
            _generate_registries(entry)
        else:
            logger.imp(
                "Please modify registries in .excore.toml and "
                "run `excore update` to generate `primary_fields`"
            )
    else:
        (
            workspace.primary_fields,
            workspace.primary_to_registry,
            workspace.json_schema_fields,
        ) = _parse_registries([_format(i) for i in workspace.registries])
        logger.success("Update primary_fields")


def _get_default_module_name(base: str, target: str) -> str:
    if osp.isfile(target):
        target = osp.dirname(target)
    full_path = osp.abspath(target)
    paths = full_path.split(os.sep)
    modules = []
    for p in paths[::-1]:
        if p == base:
            break
        modules.append(p)
    return ".".join([base, *modules[::-1]])


def _auto_register(target: str, module_name: str) -> None:
    if osp.isfile(target) and target.endswith(".py") and not target.endswith("__init__.py"):
        file_name = osp.split(target)[-1]
        import_name = module_name + "." + file_name[:-3]
        try:
            importlib.import_module(import_name)
        except Exception:
            from rich.console import Console

            logger.critical("Fail to register file {}", import_name)
            Console().print_exception()
        logger.success("Register file {}", import_name)
    elif osp.isdir(target):
        for file_name in os.listdir(target):
            full_path = osp.join(target, file_name)
            if osp.isdir(full_path):
                _auto_register(full_path, module_name + "." + file_name)
            else:
                _auto_register(full_path, module_name)
    else:
        logger.ex(f"Invalid target `{target}`.")


@app.command()
def auto_register(
    target: Annotated[str, CArg(help="What to be registered")] = "",
) -> None:
    """
    Automatically import all modules in `src_dir` by default or `target`
        and register all modules, then dump to files.
    """
    if not osp.exists(_workspace_config_file):
        logger.critical("Please run `excore init` in your command line first!")
        sys.exit(0)
    update = target == ""
    target = target or osp.abspath(workspace.src_dir)
    module_name = _get_default_module_name(workspace.src_dir.split(os.sep)[-1], target)
    _auto_register(target, module_name)
    Registry.dump(update)


@app.command()
def primary_fields() -> None:
    """
    Show primary_fields.
    """
    table = _create_table("FIELDS", _parse_registries(workspace.registries)[0])
    logger.info(table)


@app.command()
def registries() -> None:
    """
    Show registries.
    """
    table = _create_table("Registry", [_format(i) for i in workspace.registries])
    logger.info(table)


@app.command()
def generate_registries(
    entry: str = CArg(
        default="__init__", help="Used for detect or generate Registry definition code"
    ),
) -> None:
    """
    Generate registries definition code according to workspace config.
    """
    _generate_registries(entry)
