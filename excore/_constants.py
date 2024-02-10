import os
import os.path as osp

from .engine.logging import logger

__author__ = "Asthestarsfalll"
__version__ = "0.1.1beta"

_cache_base_dir = osp.expanduser("~/.cache/excore/")
_workspace_config_file = "./.excore.toml"
_registry_cache_file = "registry_cache.pkl"
_json_schema_file = "excore_schema.json"
_class_mapping_file = "class_mapping.json"


def _load_workspace_config():
    if osp.exists(_workspace_config_file):
        _workspace_cfg.update(toml.load(_workspace_config_file))
        logger.ex("load `.excore.toml`")
    else:
        logger.warning("Please use `excore init` in your command line first")


def _update_name(base_name):
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
    import toml  # pylint: disable=import-outside-toplevel

    cfg = toml.load(_workspace_config_file)
    _base_name = cfg["name"]

_cache_dir = osp.join(_cache_base_dir, _base_name)

# TODO: Use a data class to store this
_workspace_cfg = dict(
    name="",
    src_dir="",
    base_dir=os.getcwd(),
    registries=[],
    primary_fields=[],
    primary_to_registry={},
    json_schema_fields={},
    props={},
)

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
