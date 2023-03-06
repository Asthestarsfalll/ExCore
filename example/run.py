from prepare import MODELS

from excore import Registry, config
from excore.logger import logger

logger.info(MODELS.module_table())
logger.info(Registry.children_table())

cfg = config.load("./run.toml")

target_module = ["Model", "Optimizer", "Loss", "TrainData"]
modules_dict, cfg_dict = config.build_all(cfg, target_module)
logger.debug(modules_dict)
logger.debug(cfg_dict)
