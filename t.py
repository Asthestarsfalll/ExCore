from torch import optim

from excore import Registry

OPTIM = Registry("Optimizer")


def _get_modules(name: str, module) -> bool:
    if name[0].isupper():
        return True
    return False


OPTIM.match(optim, _get_modules)
print(OPTIM)
