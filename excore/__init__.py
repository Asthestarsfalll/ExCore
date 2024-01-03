from . import hub
from ._constants import (__author__, __version__, _load_workspace_config,
                         _workspace_cfg)
from .config import build_all, load_config, set_target_fields
from .logger import add_logger, init_logger, logger, remove_logger
from .registry import Registry

init_logger()
_load_workspace_config()
set_target_fields(_workspace_cfg["target_fields"])
