from __future__ import annotations

import os
import time
from typing import Any

import toml

from .._exceptions import CoreConfigSupportError
from ..engine.logging import logger
from ..engine.registry import load_registries
from .lazy_config import LazyConfig
from .models import ModuleWrapper
from .parse import ConfigDict

__all__ = ["load", "build_all", "load_config"]


BASE_CONFIG_KEY = "__base__"


def load_config(filename: str, base_key: str = "__base__") -> ConfigDict:
    """
    Load a configuration file and merge its base configurations.

    Args:
        filename (str): The path to the TOML configuration file.
        base_key (str, optional): The key to identify base configurations.
            Defaults to "__base__".

    Returns:
        ConfigDict: The merged configuration dictionary.

    Raises:
        CoreConfigSupportError: If the file extension is not ".toml".
    """
    logger.info(f"load_config {filename}")
    ext = os.path.splitext(filename)[-1]
    path = os.path.dirname(filename)

    if ext != ".toml":
        raise CoreConfigSupportError(f"Only support `toml` files for now, but got {filename}")
    config = toml.load(filename, ConfigDict)

    base_cfgs = [load_config(os.path.join(path, i), base_key) for i in config.pop(base_key, [])]
    base_cfg = ConfigDict()
    for c in base_cfgs:
        _merge_config(base_cfg, c)
    _merge_config(base_cfg, config)

    return base_cfg


def _merge_config(base_cfg: ConfigDict, new_cfg: dict) -> None:
    for k, v in new_cfg.items():
        if k in base_cfg and isinstance(v, dict):
            _merge_config(base_cfg[k], v)
        else:
            base_cfg[k] = v


def load(
    filename: str,
    *,
    dump_path: str | None = None,
    update_dict: dict[str, Any] | None = None,
    base_key: str = BASE_CONFIG_KEY,
    parse_config: bool = True,
) -> LazyConfig:
    """
    Load a configuration file and optionally updates it with a dictionary,
    dumps it to a specified path.

    Args:
        filename (str): The path to the configuration file to load.
        dump_path (str, optional): The path to dump the loaded configuration.
            Defaults to None.
        update_dict (dict, optional): A dictionary with values to update in
            the loaded configuration. Defaults to None.
        base_key (str, optional): The base key to use for loading the configuration.
            Defaults to `BASE_CONFIG_KEY`.
        parse_config (bool, optional): Whether to parse the configuration immediately.
            Defaults to True.

    Returns:
        LazyConfig: A LazyConfig object representing the loaded configuration.
    """
    st = time.time()
    load_registries()
    config = load_config(filename, base_key)
    if update_dict:
        _merge_config(config, update_dict)
    logger.success("Config loading cost {:.4f}s!", time.time() - st)
    if dump_path:
        config.dump(dump_path)
    logger.info("Loaded configs:")
    logger.info(config)
    lazy_config = LazyConfig(config)
    if parse_config:
        lazy_config.parse()
    return lazy_config


def build_all(cfg: LazyConfig) -> tuple[ModuleWrapper, dict[str, Any]]:
    """
    Build all modules from the given LazyConfig object.

    Args:
        cfg (LazyConfig): The LazyConfig object containing the configuration.

    Returns:
        tuple: A tuple containing a ModuleWrapper and a dictionary of additional data.
    """
    st = time.time()
    modules = cfg.build_all()
    logger.success("Modules building costs {:.4f}s!", time.time() - st)
    return modules
