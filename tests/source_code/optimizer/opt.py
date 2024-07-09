from source_code import OPTIM
from torch import optim


def _get_modules(name: str, module) -> bool:
    return name[0].isupper()


OPTIM.match(optim, _get_modules)
