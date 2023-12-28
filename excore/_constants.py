import os
import os.path as osp

__author__ = "Asthestarsfalll"
__version__ = "0.1.3"

_cache_base_dir = osp.expanduser("~/.cache/excore/")
_workspace_config_file = "./.excore.toml"
_registry_cache_file = "registry_cache.pkl"
_json_schema_file = "excore_schema.json"


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

_workspace_cfg = dict(
    target_fields=[],
    json_schema_fields=dict(),
    isolated_fields=dict(),
    props=dict(),
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
