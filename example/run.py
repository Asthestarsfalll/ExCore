from prepare import MODELS

from core import Registry, config
from core.logger import logger

logger.info(MODELS.module_table())
logger.info(Registry.children_table())

cfg = config.load("./run.toml")

target_module = ["Model", "Optimizer", "Loss", "TrainData"]
modules_dict, cfg_dict = config.build_all(cfg, target_module)
