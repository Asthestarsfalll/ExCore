import os
import sys

from typer import Argument as CArg
from typer import Option as COp
from typing_extensions import Annotated

from .._constants import _cache_base_dir, _workspace_cfg
from ..config._json_schema import _generate_json_schema_and_class_mapping, _generate_taplo_config
from ..engine.logging import logger
from ._app import app


@app.command()
def config_extention():
    """
    Generate json_schema for onfig completion and class_mapping for class navigation.
    """
    target_dir = os.path.join(_cache_base_dir, _workspace_cfg["name"])
    os.makedirs(target_dir, exist_ok=True)
    _generate_taplo_config(target_dir)
    if not _workspace_cfg["json_schema_fields"]:
        logger.warning("You should set json_schema_fields first")
        sys.exit()
    _generate_json_schema_and_class_mapping(_workspace_cfg["json_schema_fields"])


def _generate_typehints(entry: str, class_name: str, info_class_name: str, config: str):
    if not _workspace_cfg["primary_fields"]:
        logger.critical("Please initialize the workspace first.")
        return
    target_file = os.path.join(_workspace_cfg["src_dir"], entry + ".py")
    logger.info(f"Generating module type hints in {target_file}.")
    with open(target_file, "w", encoding="UTF-8") as f:
        f.write(f"from typing import Union{', Any' if config else ''}\n")
        f.write("from excore.config.model import ModuleNode, ModuleWrapper\n\n")
        f.write(f"class {class_name}:\n")
        for i in _workspace_cfg["primary_fields"]:
            f.write(f"    {i}: Union[ModuleNode, ModuleWrapper]\n")
    logger.info(f"Generating isolated objects type hints in {target_file}.")
    if config:
        from .. import config as cfg

        c = cfg.load(config)
        cfg.silent()
        run_info = c.build_all()[1]
        with open(target_file, "a", encoding="UTF-8") as f:
            f.write(f"\nclass {info_class_name}:\n")
            for key in run_info:
                f.write(f"    {key}: Any\n")


@app.command()
def generate_typehints(
    entry: Annotated[str, CArg(help="The file to generate.")] = "types",
    class_name: Annotated[str, COp(help="The class name of type hints.")] = "TypedModules",
    info_class_name: Annotated[str, COp(help="The class name of run_info.")] = "RunInfo",
    config: Annotated[str, COp(help="Used generate type hints for isolated objects.")] = None,
):
    """
    Generate type hints for modules and isolated objects.
    """
    _generate_typehints(entry, class_name, info_class_name, config)
