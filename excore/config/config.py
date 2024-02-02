import os
import sys
import time
from typing import Tuple

import toml

from .._exceptions import CoreConfigSupportError
from ..engine.logging import logger
from ..engine.registry import load_registries
from .lazy_config import LazyConfig
from .parse import AttrNode

__all__ = ["load", "build_all", "load_config"]


# TODO: Prune and decoupling. low priority.
# TODO: Improve error messages. high priority.
# TODO: Support multiple same module parse.
# TODO: Add UnitTests. high priority.

sys.path.append(os.getcwd())

BASE_CONFIG_KEY = "__base__"


def load_config(filename: str, base_key: str = "__base__") -> AttrNode:
    logger.info(f"load_config {filename}")
    ext = os.path.splitext(filename)[-1]
    path = os.path.dirname(filename)

    if ext != ".toml":
        raise CoreConfigSupportError(f"Only support `toml` files for now, but got {filename}")
    config = toml.load(filename, AttrNode)

    base_cfgs = [load_config(os.path.join(path, i), base_key) for i in config.pop(base_key, [])]
    base_cfg = AttrNode()
    for c in base_cfgs:
        _merge_config(base_cfg, c)
    _merge_config(base_cfg, config)

    return base_cfg


def _merge_config(base_cfg, new_cfg):
    for k, v in new_cfg.items():
        if k in base_cfg and isinstance(v, dict):
            _merge_config(base_cfg[k], v)
        else:
            base_cfg[k] = v


def load(filename: str, base_key: str = BASE_CONFIG_KEY) -> LazyConfig:
    st = time.time()
    load_registries()
    config = load_config(filename, base_key)
    logger.info("Loaded configs:")
    logger.info(config)
    lazy_config = LazyConfig(config)
    logger.success("Config loading and parsing cost {:.4f}s!", time.time() - st)
    return lazy_config


def build_all(cfg: LazyConfig) -> Tuple[dict, dict]:
    st = time.time()
    modules = cfg.build_all()
    logger.success("Modules building costs {:.4f}s!", time.time() - st)
    return modules
