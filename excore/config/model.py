import importlib
from dataclasses import dataclass
from sys import exc_info, exit
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from .._exceptions import ModuleBuildError
from ..engine.hook import ConfigArgumentHook
from ..engine.logging import logger
from ..engine.registry import Registry
from ..utils.misc import CacheOut

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
        `@` denotes reused module, which will only be built once and cached out.
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
    cls: Any

    def _get_params(self, **kwargs):
        params = {}
        for k, v in self.items():
            if isinstance(v, ModuleWrapper):
                v = v()
            params[k] = v
        params.update(kwargs)
        return params

    @property
    def name(self):
        return self.cls.__name__

    def add_params(self, **kwargs):
        self.update(kwargs)
        return self

    def update(self, _other):
        super().update(_other)
        return self

    def _build_instance(self, params):
        try:
            module = self.cls(**params)
        except Exception as exc:
            logger.critical(exc_info())
            raise ModuleBuildError(
                f"Build Error with module {self.cls} and arguments {params}"
            ) from exc
        if LOG_BUILD_MESSAGE:
            logger.success(
                f"Successfully build module: {self.cls.__name__}, with arguments {params}"
            )
        return module

    def __call__(self, **kwargs):
        params = self._get_params(**kwargs)
        module = self._build_instance(params)
        return module

    @classmethod
    def from_str(cls, str_target, **params):
        node = cls(_str_to_target(str_target))
        node.update(params)
        return node

    @classmethod
    def from_base_name(cls, base, name, **params):
        try:
            cls_name = Registry.get_registry(base)[name]
        except Exception as exc:
            logger.critical(exc_info())
            raise ModuleBuildError(
                f"Failed to find the registered module {name} with base registry {base}"
            ) from exc
        return cls.from_str(cls_name, **params)

    @classmethod
    def from_node(cls, _other: "ModuleNode") -> "ModuleNode":
        if _other.__class__.__name__ == cls.__name__:
            return _other
        return cls(_other.cls).update(_other)


class InterNode(ModuleNode):
    pass


class ConfigHookNode(ModuleNode):
    def __call__(self, **kwargs):
        if issubclass(self.cls, ConfigArgumentHook):
            return None
        params = self._get_params(**kwargs)
        return self._build_instance(params)


class ReusedNode(InterNode):
    @CacheOut()
    def __call__(self, **kwargs):
        return super().__call__(**kwargs)


class ClassNode(InterNode):
    def __call__(self):
        return self.cls


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
    def __init__(
        self, modules: Optional[Union[Dict[str, ModuleNode], List[ModuleNode], ModuleNode]] = None
    ):
        super().__init__()
        if modules is None:
            return
        if isinstance(modules, (ModuleNode, ConfigArgumentHook, ChainedInvocationWrapper)):
            self[modules.name] = modules
        elif isinstance(modules, dict):
            for k, m in modules.items():
                self[k] = m
        elif isinstance(modules, list):
            for m in modules:
                self[self._get_name(m)] = m
        else:
            raise TypeError(
                f"Expect modules to be `list`, `dict` or `ModuleNode`, but got {type(modules)}"
            )

    def _get_name(self, m):
        if hasattr(m, "name"):
            return m.name
        return m.__class__.__name__

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


_dispatch_module_node = {
    OTHER_FLAG: ModuleNode,
    REUSE_FLAG: ReusedNode,
    INTER_FLAG: InterNode,
    CLASS_FLAG: ClassNode,
    REFER_FLAG: VariableReference,
}
