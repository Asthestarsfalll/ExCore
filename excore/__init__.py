from . import hub
from ._constants import (
    __author__,
    __version__,
    _load_workspace_config,
    _workspace_cfg,
)
from .config import (
    ConfigArgumentHookProtocol,
    build_all,
    load,
    set_target_fields,
)
from .hook import Hook, HookManager
from .logger import _enable_excore_debug, add_logger, init_logger, remove_logger
from .registry import Registry, load_registries

__all__ = [
    "__author__",
    "__version__",
    "hub",
    "config",
    "hook",
    "logger",
    "registry",
    "ConfigArgumentHookProtocol",
    "build_all",
    "load",
    "Hook",
    "HookManager",
    "add_logger",
    "remove_logger",
    "Registry",
    "load_registries",
]

init_logger()
_load_workspace_config()
set_target_fields(_workspace_cfg["target_fields"])
_enable_excore_debug()
