from torch.optim import lr_scheduler

from source_code import LRCHE
from source_code.optimizer.opt import _get_modules

LRCHE.match(lr_scheduler, _get_modules)
