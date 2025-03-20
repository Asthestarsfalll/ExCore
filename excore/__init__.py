import sys

from rich.traceback import install

from . import config, plugins
from ._constants import __author__, __version__, workspace
from .config.action import DictAction
from .config.config import build_all, load
from .config.models import ConfigArgumentHook
from .config.parse import set_primary_fields
from .engine import hook, logging, registry
from .engine.hook import Hook, HookManager
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
    "add_logger",
    "build_all",
    "config",
    "ConfigArgumentHook",
    "debug_only",
    "DictAction",
    "load",
    "load_registries",
    "logging",
    "logger",
    "hook",
    "Hook",
    "HookManager",
    "registry",
    "remove_logger",
    "plugins",
    "Registry",
]

install()
init_logger()
set_primary_fields(workspace)
_enable_excore_debug()
sys.path.append(workspace.base_dir)
