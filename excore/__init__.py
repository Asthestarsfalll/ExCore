from . import config, hub
from ._constants import __author__, __version__, _load_workspace_config, _workspace_cfg
from .config.config import build_all, load
from .config.parse import set_target_fields
from .engine import hook, logging, registry
from .engine.hook import ConfigArgumentHook, Hook, HookManager
from .engine.logging import (
    _enable_excore_debug,
    add_logger,
    debug_only,
    init_logger,
    logger,
    remove_logger,
)
from .engine.registry import Registry, load_registries

__all__ = [
    "__author__",
    "__version__",
    "hub",
    "config",
    "hook",
    "logger",
    "registry",
    "ConfigArgumentHook",
    "build_all",
    "load",
    "Hook",
    "HookManager",
    "add_logger",
    "remove_logger",
    "Registry",
    "load_registries",
    "debug_only",
    "logging",
]

init_logger()
_load_workspace_config()
set_target_fields(_workspace_cfg["target_fields"])
_enable_excore_debug()
