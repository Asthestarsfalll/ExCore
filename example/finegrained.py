from excore import config
from excore.plugins.finegrained_config import enable_finegrained_config

enable_finegrained_config()

cfg = config.load("./configs/finegrained.toml")

module_dict, info = cfg.build_all()
print(module_dict)
print(info)
