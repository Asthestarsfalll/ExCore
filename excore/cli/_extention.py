import os
import sys

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
