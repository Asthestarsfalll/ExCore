from __future__ import annotations

import os
import os.path as osp
from dataclasses import dataclass, field
from typing import Any

import toml

from .engine.logging import logger

__author__ = "Asthestarsfalll"
__version__ = "0.1.1beta"

_cache_base_dir = osp.expanduser("~/.cache/excore/")
_workspace_config_file = "./.excore.toml"
_registry_cache_file = "registry_cache.pkl"
_json_schema_file = "excore_schema.json"
_class_mapping_file = "class_mapping.json"


def _load_workspace_config() -> None:
    if osp.exists(_workspace_config_file):
        _workspace_cfg.update(toml.load(_workspace_config_file))
        logger.ex("load `.excore.toml`")
    else:
        logger.warning("Please use `excore init` in your command line first")


def _update_name(base_name: str) -> str:
    name = base_name

    suffix = 1
    while osp.exists(osp.join(_cache_base_dir, name)):
        name = f"{_base_name}_{suffix}"
        suffix += 1

    return name


if not osp.exists(_workspace_config_file):
    _base_name = osp.basename(osp.normpath(os.getcwd()))
    _base_name = _update_name(_base_name)
else:
    cfg = toml.load(_workspace_config_file)
    _base_name = cfg["name"]

_cache_dir = osp.join(_cache_base_dir, _base_name)


@dataclass
class _WorkspaceConfig:
    name: str = field(default="")
    src_dir: str = field(default="")
    base_dir: str = field(default_factory=os.getcwd)
    registries: list[str] = field(default_factory=list)
    primary_fields: list[str] = field(default_factory=list)
    primary_to_registry: dict[str, str] = field(default_factory=dict)
    json_schema_fields: dict[str, str | list[str]] = field(default_factory=dict)
    props: dict[Any, Any] = field(default_factory=dict)

    def update(self, _cfg: dict[Any, Any]) -> None:
        self.__dict__.update(_cfg)

    def dump(self, path: str) -> None:
        with open(path, "w") as f:
            d = self.__dict__
            d.pop("base_dir", None)
            toml.dump(d, f)


_workspace_cfg = _WorkspaceConfig()

LOGO = r"""
▓█████ ▒██   ██▒ ▄████▄   ▒█████   ██▀███  ▓█████
▓█   ▀ ▒▒ █ █ ▒░▒██▀ ▀█  ▒██▒  ██▒▓██ ▒ ██▒▓█   ▀
▒███   ░░  █   ░▒▓█    ▄ ▒██░  ██▒▓██ ░▄█ ▒▒███
▒▓█  ▄  ░ █ █ ▒ ▒▓▓▄ ▄██▒▒██   ██░▒██▀▀█▄  ▒▓█  ▄
░▒████▒▒██▒ ▒██▒▒ ▓███▀ ░░ ████▓▒░░██▓ ▒██▒░▒████▒
░░ ▒░ ░▒▒ ░ ░▓ ░░ ░▒ ▒  ░░ ▒░▒░▒░ ░ ▒▓ ░▒▓░░░ ▒░ ░
 ░ ░  ░░░   ░▒ ░  ░  ▒     ░ ▒ ▒░   ░▒ ░ ▒░ ░ ░  ░
   ░    ░    ░  ░        ░ ░ ░ ▒    ░░   ░    ░
   ░  ░ ░    ░  ░ ░          ░ ░     ░        ░  ░
                ░
"""
