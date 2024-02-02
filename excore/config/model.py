import importlib
from dataclasses import dataclass
from sys import exc_info, exit
from typing import Any, List, Optional, Sequence, Tuple, Union

from .._exceptions import ModuleBuildError
from ..engine.hook import ConfigArgumentHook
from ..engine.logging import logger
from ..engine.registry import Registry
from ..utils.utils import CacheOut

__all__ = ["silent"]

REUSE_FLAG = "@"
INTER_FLAG = "!"
CLASS_FLAG = "$"
REFER_FLAG = "&"
OTHER_FLAG = ""

LOG_BUILD_MESSAGE = True


def silent():
    global LOG_BUILD_MESSAGE  # pylint: disable=global-statement
    LOG_BUILD_MESSAGE = False


def _is_special(k: str) -> Tuple[str, str]:
    """
    Determine if the given string begin with target special character.
        `@` denotes reused module, which will only be built once and cache out.
        `!` denotes intermediate module, which will be built from scratch if need.
        `$` denotes use module class itself, instead of its instance
        `&` denotes use refer a value from top level of config

    Args:
        k (str): The input string to check.

    Returns:
        Tuple[str, str]: A tuple containing the modified string and the special character.
    """
    if k.startswith(REUSE_FLAG):
        return k[1:], REUSE_FLAG
    if k.startswith(INTER_FLAG):
        return k[1:], INTER_FLAG
    if k.startswith(CLASS_FLAG):
        return k[1:], CLASS_FLAG
    if k.startswith(REFER_FLAG):
        return k[1:], REFER_FLAG
    return k, ""


# FIXME: need to handle more situations.
def _str_to_target(module_name):
    module_name = module_name.split(".")
    if len(module_name) == 1:
        return importlib.import_module(module_name[0])
    target_name = module_name.pop(-1)
    try:
        module = importlib.import_module(".".join(module_name))
        module = getattr(module, target_name)
    except ModuleNotFoundError:
        logger.critical(f"Can not import such module: {'.'.join(module_name)}")
        exit(0)
    return module


@dataclass
class ModuleNode(dict):
    name: str
    base: str

    def __setitem__(self, k, v) -> None:
        k, k_type = _is_special(k)
        if k_type == REFER_FLAG:
            v = VariableReference(v)
        elif k_type:
            _v = v
            v = _attr2module(k, k_type, k_type)
            # prevent recursion depth exceed
            # just a placeholder
            super(ModuleNode, v).__setitem__(k_type, _v)
        super().__setitem__(k, v)

    def set_funcs(self, funcs):
        self.funcs = funcs

    def add_params(self, **kwargs):
        self.update(kwargs)

    def update(self, others: dict) -> "ModuleNode":
        """
        Override native `update` method to make it use the overrode
        `__setitem__` method.
        Return self for convenience.
        """
        for k, v in others.items():
            self[k] = v
        return self

    def _get_params(self, **kwargs):
        params = {}
        for k, v in self.items():
            if isinstance(v, ModuleWrapper):
                v = v()
            params[k] = v
        params.update(kwargs)
        return params

    def _get_cls(self):
        try:
            cls_name = Registry.get_registry(self.base)[self.name]
        except Exception as exc:
            logger.critical(exc_info())
            raise ModuleBuildError(
                f"Failed to find the registered module {self.name} with base registry {self.base}"
            ) from exc
        cls = _str_to_target(cls_name)
        return cls

    def _build_instance(self, cls, params):
        try:
            module = cls(**params)
        except Exception as exc:
            logger.critical(exc_info())
            raise ModuleBuildError(
                f"Build Error with module {cls} and arguments {{**params}}"
            ) from exc
        if LOG_BUILD_MESSAGE:
            logger.success(f"Successfully build module: {self.name}, with arguments {{**params}}")
        return module

    def __call__(self, **kwargs):
        cls = self._get_cls()
        params = self._get_params(**kwargs)
        module = self._build_instance(cls, params)
        return module


class InterNode(ModuleNode):
    @property
    def target_feild(self):
        assert self.base in [REUSE_FLAG, INTER_FLAG, CLASS_FLAG]
        return self.pop(self.base)


class ConfigHookNode(ModuleNode):
    def __call__(self, **kwargs):
        cls = self._get_cls()
        if issubclass(cls, ConfigArgumentHook):
            return None
        params = self._get_params(**kwargs)
        return self._build_instance(cls, params)


class ReusedNode(InterNode):
    @CacheOut()
    def __call__(self, **kwargs):
        return super().__call__(**kwargs)


class ClassNode(InterNode):
    __call__ = ModuleNode._get_cls


@dataclass
class ChainedInvocationWrapper:
    node: ModuleNode
    attrs: Sequence[str]

    def __getattr__(self, __name):
        return getattr(self.node, __name)

    def __call__(self, **kwargs):
        target = self.node(**kwargs)
        if self.attrs:
            for attr in self.attrs:
                if attr[-2:] == "()":
                    target = getattr(target, attr[:-2])()
                else:
                    target = getattr(target, attr)
        return target


@dataclass
class VariableReference:
    value: Any

    def __call__(self):
        return self.value


class ModuleWrapper(dict):
    def __init__(self, modules: Optional[Union[List[ModuleNode], ModuleNode]] = None):
        super().__init__()
        if modules is None:
            return
        if isinstance(modules, ModuleNode):
            modules = [modules]
        elif not isinstance(modules, list):
            raise TypeError(f"Expect modules to be `list` or `ModuleNode`, but got {type(modules)}")
        for m in modules:
            self[m.name] = m

    def add_params(self, **kwargs):
        if len(self) == 1:
            self[list(self.keys())[0]].add_params(**kwargs)
        else:
            raise RuntimeError("Wrapped more than 1 ModuleNode, index first")

    def first(self):
        if len(self) == 1:
            return next(iter(self.values()))
        return self

    def __getattr__(self, __name: str) -> Any:
        if __name in self.keys():
            return self[__name]
        raise KeyError(__name)

    def __call__(self):
        res = [m() for m in self.values()]
        if len(res) == 1:
            return res[0]
        return res

    def __repr__(self) -> str:
        return f"ModuleWrapper{list(self.values())}"


def _attr2module(v, base, k_type=""):
    ModuleType = _dispatch_module_node[k_type]
    if not base:
        return v
    if isinstance(v, dict):
        # if v is {}, return {}
        return {_k: ModuleType(_k, base).update(_v) for _k, _v in v.items()}
    if isinstance(v, list):
        return [ModuleType(_k, base) for _k in v]
    if isinstance(v, str):
        return ModuleType(v, base)
    raise RuntimeError()


def _convert2module(m, k_type, ModuleType=None, return_wrapper=True):
    if isinstance(m, ModuleWrapper):
        assert len(m) == 1
        m = m.first()
    if not isinstance(m, ModuleNode):
        return m
    ModuleType = ModuleType or _dispatch_module_node[k_type]
    if return_wrapper:
        return ModuleWrapper(ModuleType(m.name, m.base).update(m))
    return ModuleType(m.name, m.base)


_dispatch_module_node = {
    OTHER_FLAG: ModuleNode,
    REUSE_FLAG: ReusedNode,
    INTER_FLAG: InterNode,
    CLASS_FLAG: ClassNode,
    REFER_FLAG: VariableReference,
}
