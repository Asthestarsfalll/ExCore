from __future__ import annotations

import importlib
import inspect
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from inspect import Parameter, isclass, ismodule
from typing import TYPE_CHECKING, Type, Union, final, overload

from .._constants import workspace
from .._exceptions import (
    CoreConfigParseError,
    CoreConfigSupportError,
    EnvVarParseError,
    ModuleBuildError,
    ModuleValidateError,
    StrToClassError,
)
from .._misc import CacheOut
from ..engine.logging import logger
from ..engine.registry import Registry
from .action import DictAction

if TYPE_CHECKING:
    from types import FunctionType, ModuleType
    from typing import Any, Callable, Dict, Literal

    from typing_extensions import Self

    from ..engine.hook import Hook
    from .parse import ConfigDict

    NodeClassType = Type[Any]
    NodeParams = Dict[str, Any]
    NodeInstance = object

    NoCallSkipFlag = Self

    SpecialFlag = Literal["@", "!", "$", "&", ""]


__all__ = ["silent"]

REUSE_FLAG: Literal["@"] = "@"
INTER_FLAG: Literal["!"] = "!"
CLASS_FLAG: Literal["$"] = "$"
REFER_FLAG: Literal["&"] = "&"
OTHER_FLAG: Literal[""] = ""

FLAG_PATTERN = re.compile(r"^([@!$&])(.*)$")
DO_NOT_CALL_KEY = "__no_call__"
SPECIAL_FLAGS = [OTHER_FLAG, INTER_FLAG, REUSE_FLAG, CLASS_FLAG, REFER_FLAG]
HOOK_FLAGS = ["@", "."]


def silent() -> None:
    workspace.excore_log_build_message = False


def _is_special(k: str) -> tuple[str, SpecialFlag]:
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
    match = FLAG_PATTERN.match(k)
    if match:
        logger.ex(f"Find match `{match}`.")
        return match.group(2), match.group(1)  # type: ignore
    logger.ex("No Match.")
    return k, ""


def _str_to_target(module_name: str) -> ModuleType | NodeClassType | FunctionType:
    module_names = module_name.split(".")
    if len(module_names) == 1:
        return importlib.import_module(module_names[0])
    target_name = module_names.pop(-1)
    try:
        module = importlib.import_module(".".join(module_names))
    except ModuleNotFoundError as exc:
        raise StrToClassError(f"Cannot import such module: `{'.'.join(module_names)}`") from exc
    try:
        module = getattr(module, target_name)
    except AttributeError as exc:
        raise StrToClassError(
            f"Cannot find such module `{target_name}` form `{'.'.join(module_names)}`"
        ) from exc
    return module


@dataclass
class ModuleNode(dict):
    cls: Any
    _no_call: bool = field(default=False, repr=False)
    priority: int = field(default=0, repr=False)

    def _update_params(self, **params: NodeParams) -> None:
        return_params = {}
        for k, v in self.items():
            if isinstance(v, (ModuleWrapper, ModuleNode)):
                v = v()
            return_params[k] = v
        self.update(params)
        self.update(return_params)

    @property
    def name(self) -> str:
        return self.cls.__name__

    def add(self, **params: NodeParams) -> Self:
        self.update(params)
        return self

    def _instantiate(self) -> NodeInstance:
        try:
            if ismodule(self.cls):
                return self.cls
            module = self.cls(**self)
        except Exception as exc:
            raise ModuleBuildError(
                f"Instantiate Error with module {self.cls} and arguments {self.items()}"
            ) from exc
        if workspace.excore_log_build_message:
            logger.success(
                f"Successfully instantiated: {self.cls.__name__} with arguments {self.items()}"
            )
        return module

    def __call__(self, **params: NodeParams) -> NoCallSkipFlag | NodeInstance:  # type: ignore
        if self._no_call:
            return self
        self._update_params(**params)
        self.validate()
        module = self._instantiate()
        return module

    def __lshift__(self, params: NodeParams) -> Self:
        if not isinstance(params, dict):
            raise TypeError(f"Expect type is dict, but got {type(params)}")
        self.update(params)
        return self

    def __rshift__(self, __other: ModuleNode) -> Self:
        if not isinstance(__other, ModuleNode):
            raise TypeError(f"Expect type is `ModuleNode`, but got {type(__other)}")
        __other.update(self)
        return self

    @classmethod
    def __excore_check_target_type__(cls, target_type: type[ModuleNode]) -> bool:
        return False

    @classmethod
    def __excore_should_convert__(cls, target_type: type[ModuleNode]) -> bool:
        return False

    @classmethod
    def from_str(cls, str_target: str, params: NodeParams | None = None) -> ModuleNode:
        node = cls(_str_to_target(str_target))
        if params:
            node.update(params)
        if node.pop(DO_NOT_CALL_KEY, False):
            node._no_call = True
        return node

    @classmethod
    def from_base_name(cls, base: str, name: str, params: NodeParams | None = None) -> ModuleNode:
        try:
            cls_name = Registry.get_registry(base)[name]
        except KeyError as exc:
            raise ModuleBuildError(
                f"Failed to find the registered module `{name}` with base registry `{base}`"
            ) from exc
        return cls.from_str(cls_name, params)

    @classmethod
    def from_node(cls, _other: ModuleNode) -> ModuleNode:
        if _other.__class__.__name__ == cls.__name__:
            return _other
        node = cls(_other.cls) << _other
        node._no_call = _other._no_call
        return node

    @staticmethod
    def _get_params(cls: type) -> list[inspect.Parameter]:
        signature = inspect.signature(cls.__init__ if isclass(cls) else cls)
        params = list(signature.parameters.values())
        if isclass(cls):  # skip self
            params = params[1:]
        return params

    def validate(self) -> None:
        if not workspace.excore_validate:
            return
        if ismodule(self.cls):
            return

        missing = []
        defaults = []
        params = ModuleNode._get_params(self.cls)

        for param in params:
            if (
                param.default == param.empty
                and param.kind
                not in [
                    Parameter.VAR_POSITIONAL,
                    Parameter.VAR_KEYWORD,
                ]
                and param.name not in self
            ):
                missing.append(param.name)
            else:
                defaults.append(param.name)

        message = (
            f"Validating `{self.cls.__name__}` , "
            f"finding missing parameters: `{missing}` without default values."
        )
        if not workspace.excore_manual_set and missing:
            raise ModuleValidateError(message)
        if missing:
            logger.info(message)
        for param_name in missing:
            logger.info(f"Input value of parameter `{param_name}`:")
            value = input()
            self[param_name] = DictAction._parse_iterable(value)


class InterNode(ModuleNode):
    priority: int = 2

    @classmethod
    def __excore_check_target_type__(cls, target_type: type[ModuleNode]) -> bool:
        return target_type is ReusedNode


class ConfigHookNode(ModuleNode):
    priority: int = 1

    def validate(self) -> None:
        if "node" in self:
            raise ModuleValidateError(
                f"Parameter `node:{self['node']}` should not exist in `ConfigHookNode`."
            )
        super().validate()

    @overload
    def __call__(self, **params: NodeParams) -> NodeInstance | Hook | ConfigArgumentHook: ...

    @overload
    def __call__(self, **params: dict[str, ModuleNode]) -> ConfigHookNode: ...

    def __call__(self, **params: NodeParams) -> NodeInstance | Hook | ConfigArgumentHook:
        self._update_params(**params)
        return self._instantiate()


class ReusedNode(InterNode):
    priority: int = 3

    @CacheOut()
    def __call__(self, **params: NodeParams) -> NodeInstance | NoCallSkipFlag:  # type: ignore
        return super().__call__(**params)

    @classmethod
    def __excore_check_target_type__(cls, target_type: type[ModuleNode]) -> bool:
        return target_type is InterNode


class ClassNode(ModuleNode):
    priority: int = 1

    def validate(self) -> None:
        return  # Do nothing

    def __call__(self) -> NodeClassType | FunctionType:  # type: ignore
        return self.cls

    @classmethod
    def __excore_should_convert__(cls, target_type: type[ModuleNode]) -> bool:
        return True


class ConfigArgumentHook(ABC):
    flag: str = "@"

    def __init__(
        self,
        node: Callable,
        enabled: bool = True,
    ) -> None:
        self.node = node
        self.enabled = enabled
        if not hasattr(node, "name"):
            raise ValueError("The `node` must have name attribute.")
        self.name = node.name
        self._is_initialized = True

    @abstractmethod
    def hook(self, **kwargs: Any) -> Any:
        raise NotImplementedError(f"`{self.__class__.__name__}` do not implement `hook` method.")

    @final
    def __call__(self, **kwargs: Any) -> Any:
        if not getattr(self, "_is_initialized", False):
            raise CoreConfigSupportError(
                f"Call super().__init__(node) in class `{self.__class__.__name__}`"
            )
        if self.enabled:
            return self.hook(**kwargs)
        return self.node(**kwargs)

    @classmethod
    def __excore_prepare__(cls, node: ConfigNode, hook_info: str, config: ConfigDict) -> ConfigNode:
        hook_name, field = config._get_name_and_field(hook_info)
        if not isinstance(hook_name, str):
            raise CoreConfigParseError(
                f"More than one or none of hooks are found with `{hook_info}`."
            )
        hook_node = config._get_node_from_name_and_field(hook_name, field, ConfigHookNode)[0]
        node = hook_node(node=node)  # type:ignore
        return node


class GetAttr(ConfigArgumentHook):
    flag: str = "."

    def __init__(self, node: ConfigNode, attr: str) -> None:
        super().__init__(node)
        self.attr = attr

    def hook(self, **params: NodeParams) -> Any:
        target = self.node(**params)
        if isinstance(target, ModuleNode):
            raise ModuleBuildError(f"Do not support `{DO_NOT_CALL_KEY}`")
        return eval("target." + self.attr)

    @classmethod
    def from_list(cls, node: ConfigNode, attrs: list[str]) -> ConfigNode:
        for attr in attrs:
            node = cls(node, attr)
        return node

    @classmethod
    def __excore_prepare__(cls, node: ConfigNode, hook_info: str, config: ConfigDict) -> ConfigNode:
        return cls(node, hook_info)


@dataclass
class VariableReference:
    def __init__(self, value: str) -> None:
        env_names = re.findall(r"\$\{([^}]+)\}", value)
        self.has_env = len(env_names) > 0
        for env in env_names:
            if not (env_value := os.environ.get(env, None)):
                raise EnvVarParseError(f"Can not get environment variable {env}.")
            value = re.sub(r"\$\{" + re.escape(env) + r"\}", env_value, value)
        self.value = value

    def __call__(self) -> str:
        return self.value


ConfigNode = Union[ModuleNode, ConfigArgumentHook]
NodeType = Type[ModuleNode]


class ModuleWrapper(dict):
    def __init__(
        self,
        modules: (
            dict[str, ConfigNode] | list[ConfigNode] | ConfigNode | VariableReference | None
        ) = None,
        is_dict: bool = False,
    ) -> None:
        super().__init__()
        if modules is None:
            return
        self.is_dict = is_dict
        if isinstance(modules, (ModuleNode, ConfigArgumentHook)):
            self[modules.name] = modules
        elif isinstance(modules, dict):
            for k, m in modules.items():
                if isinstance(m, list):
                    m = ModuleWrapper(m)
                self[k] = m
        elif isinstance(modules, list):
            for m in modules:
                self[self._get_name(m)] = m
            if len(self) != len(modules):
                raise ValueError("Currently not support for the same class name")
        else:
            raise TypeError(
                f"Expect modules to be `list`, `dict` or `ModuleNode`, but got {type(modules)}"
            )

    def _get_name(self, m) -> Any:
        if hasattr(m, "name"):
            return m.name
        return m.__class__.__name__

    def __lshift__(self, params: NodeParams) -> None:
        if len(self) == 1:
            self[list(self.keys())[0]] << params
        else:
            raise RuntimeError("Wrapped more than 1 ModuleNode, index first")

    def first(self):
        if len(self) == 1:
            return next(iter(self.values()))
        return self

    def __getattr__(self, __name: str) -> Any:
        if __name in self.keys():
            return self[__name]
        raise KeyError(f"Invalid key `{__name}`, must be one of `{list(self.keys())}`")

    def __call__(self):
        if self.is_dict:
            return {k: v() for k, v in self.items()}
        res = [m() for m in self.values()]
        if len(res) == 1:
            return res[0]
        return res

    def __repr__(self) -> str:
        return f"ModuleWrapper{list(self.values())}"


_dispatch_module_node: dict[SpecialFlag, NodeType] = {
    OTHER_FLAG: ModuleNode,
    REUSE_FLAG: ReusedNode,
    INTER_FLAG: InterNode,
    CLASS_FLAG: ClassNode,
}

_dispatch_argument_hook: dict[str, Type[ConfigArgumentHook]] = {
    "@": ConfigArgumentHook,  # type:ignore
    ".": GetAttr,
}


def register_special_flag(flag: str, node_type: NodeType, force: bool = False) -> None:
    if not force and flag in SPECIAL_FLAGS:
        raise ValueError(f"Special flag `{flag}` already exist.")
    SPECIAL_FLAGS.append(flag)
    global FLAG_PATTERN
    FLAG_PATTERN = re.compile(rf"^([{''.join(SPECIAL_FLAGS)}])(.*)$")
    _dispatch_module_node[flag] = node_type  # type: ignore
    logger.ex(f"Register new module node `{node_type}` with special flag `{flag}.`")


def register_argument_hook(
    flag: str, node_type: Type[ConfigArgumentHook], force: bool = False
) -> None:
    if not force and flag in HOOK_FLAGS:
        raise ValueError(f"Special flag `{flag}` already exist.")
    HOOK_FLAGS.append(flag)
    _dispatch_argument_hook[flag] = node_type
    logger.ex(f"Register new hook node `{node_type}` with special flag `{flag}.`")
