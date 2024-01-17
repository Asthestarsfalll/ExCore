from . import hub
from ._constants import (__author__, __version__, _load_workspace_config,
                         _workspace_cfg)
from .config import (ConfigArgumentHookProtocol, build_all, load_config,
                     set_target_fields)
from .hook import Hook, HookManager
from .logger import (add_logger, enable_excore_debug, init_logger, logger,
                     remove_logger)
from .registry import Registry, load_registries

init_logger()
_load_workspace_config()
set_target_fields(_workspace_cfg["target_fields"])
enable_excore_debug()
