import time

from rich import print

from excore import Registry, config
from excore.logger import add_logger, logger

Registry.load()
MODELS = Registry.get_registry("Model")
print(MODELS)


def _check_func(values):
    for v in values:
        if v:
            return True
    return False


add_logger("file_log", "./run.log")

# 打印 动态导入的 module 和 is_pretrained 的信息
logger.info(MODELS.module_table(select_info=["is_pretrained"]))
# 打印 动态导入的 module 和 is_backbone 的信息
logger.info(MODELS.module_table(select_info=["is_backbone"]))
# 打印 is_pretrained 为 true 的 module 和 is_backbone 的信息
filtered_module_name = MODELS.filter("is_pretrained")
logger.info(
    MODELS.module_table(select_info=["is_backbone"], module_list=filtered_module_name)
)
# 打印 is_pretrained 为 true 的 module 和 is_pretrained 的信息
filtered_module_name = MODELS.filter("is_pretrained", _check_func)
logger.info(
    MODELS.module_table(select_info=["is_pretrained"], module_list=filtered_module_name)
)
logger.info(Registry.registry_table())

config.set_target_fields(config.AttrNode.target_fields + ["Backbone"])
logger.info(config.AttrNode.target_fields)
config.silent()
cfg = config.load("./configs/run.toml")
# 判断是否是相同的实例
assert cfg.Optimizer == cfg.LRSche.CosDecay["optimizer"]
assert cfg.Model.FCN["backbone"] == cfg.Backbone
modules_dict, cfg_dict = config.build_all(cfg)
assert id(modules_dict["Optimizer"]) == id(modules_dict["LRSche"].optimizer)
assert id(modules_dict["Model"].backbone) == id(modules_dict["Backbone"])
assert modules_dict["Model"].head.timer == time
assert modules_dict["Optimizer"].kwargs["params"] == modules_dict["Model"].parameters()

print(modules_dict)
print(cfg_dict)
