from prepare import MODELS

from excore import Registry, config
from excore.logger import logger


def _check_func(values):
    for v in values:
        if v:
            return True
    return False


# 打印 所有注册的 module 和 is_pretrained 的信息
logger.info(MODELS.module_table(select_info=["is_pretrained"]))
# 打印 所有注册的 module 和 is_backbone 的信息
logger.info(MODELS.module_table(select_info=["is_backbone"]))
# 打印 is_pretrained 为 true 的 module 和 is_backbone 的信息
filtered_module_name = MODELS.filter("is_pretrained")
logger.info(MODELS.module_table(select_info=["is_backbone"], module_list=filtered_module_name))
# 打印 is_pretrained 为 true 的 module 和 is_pretrained 的信息
filtered_module_name = MODELS.filter("is_pretrained", _check_func)
logger.info(MODELS.module_table(select_info=["is_pretrained"], module_list=filtered_module_name))
logger.info(Registry.children_table())

cfg = config.load("./run.toml")

target_module = ["Model", "Optimizer", "Loss", "TrainData"]
modules_dict, cfg_dict = config.build_all(cfg, target_module)
logger.debug(modules_dict)
logger.debug(cfg_dict)
