import importlib
import os
import sys
import time
from copy import deepcopy
from dataclasses import dataclass
from sys import exc_info, exit
from typing import Any, Dict, List, Sequence, Tuple, Union

import toml

from ._exceptions import (CoreConfigBuildError, CoreConfigParseError,
                          CoreConfigSupportError, ModuleBuildError)
from .hook import ConfigHookManager
from .logger import logger
from .registry import Registry, load_registries
from .utils import CacheOut

__all__ = ["load", "silent"]


# TODO: Prune and decoupling. low priority.
# TODO: Improve error messages. high priority.
# TODO: Support multiple same module parse.
# TODO: Add UnitTests. high priority.

sys.path.append(os.getcwd())

REUSE_FLAG = "@"
INTER_FLAG = "!"
CLASS_FLAG = "$"
OTHER_FLAG = ""
LOG_BUILD_MESSAGE = True
BASE_CONFIG_KEY = "__base__"


def _is_special(k: str) -> Tuple[str, str]:
    """
    Determine if the given string begin with target special character.
        `@` denotes reuse module, which will only be built once and cache out.
        `!` denotes intermediate module, which will be built from scratch if need.
        `*` denotes use module class itself, instead of its instance

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
    return k, ""


def _attr2module(v, base, k_type=""):
    ModuleType = _dispatch_module_node[k_type]
    if not base:
        return v
    if isinstance(v, dict):
        # if v is {}, return {}
        return {_k: ModuleType(_k, base).update(_v) for _k, _v in v.items()}
    elif isinstance(v, list):
        return [ModuleType(_k, base) for _k in v]
    elif isinstance(v, str):
        return ModuleType(v, base)
    else:
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


def _dict2list(v, return_list=False):
    """
    Converts a dictionary to a list of its values.

    Args:
        v (dict): The dictionary to be converted.
        return_list (bool): Enforce to return list.

    Returns:
        list: A list of the values in the input dictionary.
            If the input is not a dictionary or is an empty dictionary,
            the original input is returned.
            If the input dictionary has only one value and return_list is False,
            the value itself is returned.
    """
    if v:
        v = list(v.values())
        if not return_list and len(v) == 1:
            v = v[0]
    return v


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


def _parse_param(name):
    attrs = name.split(".")
    attrs = [i for i in attrs if i]
    name = attrs.pop(0)
    return name, attrs


@dataclass
class ModuleNode(dict):
    name: str
    base: str

    def __setitem__(self, k, v) -> None:
        k, k_type = _is_special(k)
        if k_type:
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

    def _get_params(self):
        params = {}
        for k, v in self.items():
            if isinstance(v, ModuleWrapper):
                v = v()
            params[k] = v
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

    def __call__(self):
        cls = self._get_cls()
        params = self._get_params()
        try:
            module = cls(**params)
        except Exception as exc:
            logger.critical(exc_info())
            raise ModuleBuildError(
                f"Build Error with module {cls} and arguments {dict(**params)}"
            ) from exc
        if LOG_BUILD_MESSAGE:
            logger.success(
                f"Successfully build module: {self.name}, with arguments {dict(**params)}"
            )
        return module


class InterNode(ModuleNode):
    @property
    def target_feild(self):
        assert self.base in [REUSE_FLAG, INTER_FLAG, CLASS_FLAG]
        return self.pop(self.base)


class ReusedNode(InterNode):
    @CacheOut()
    def __call__(self):
        return super().__call__()


class ClassNode(InterNode):
    __call__ = ModuleNode._get_cls


@dataclass
class ChainedInvocationWrapper:
    node: ModuleNode
    attrs: Sequence[str]

    def __getattr__(self, __name):
        return getattr(self.node, __name)

    def __call__(self):
        target = self.node()
        if self.attrs:
            for attr in self.attrs:
                if attr[-2:] == "()":
                    target = getattr(target, attr[:-2])()
                else:
                    target = getattr(target, attr)
        return target


_dispatch_module_node = {
    OTHER_FLAG: ModuleNode,
    REUSE_FLAG: ReusedNode,
    INTER_FLAG: InterNode,
    CLASS_FLAG: ClassNode,
}


class ModuleWrapper(dict):
    def __init__(self, modules: Union[List[ModuleNode], ModuleNode]):
        super().__init__()
        if isinstance(modules, ModuleNode):
            modules = [modules]
        elif not isinstance(modules, list):
            raise TypeError(
                f"Expect modules to be `list` or `ModuleNode`, but got {type(modules)}"
            )
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


class AttrNode(dict):
    target_fields: List
    registered_fields: List

    def __new__(cls):
        if not hasattr(cls, "target_fields"):
            raise RuntimeError("Call `set_target_fields` before `load`")

        # make target fields unique when multiple load.
        class AttrNodeImpl(AttrNode):
            # otherwise it will share the same class variable with father class.
            target_fields = AttrNode.target_fields

        inst = super().__new__(AttrNodeImpl)
        return inst

    @classmethod
    def set_target_fields(cls, target_fields):
        """
        Sets the `target_modules` attribute to the specified list of module names,
            and `registered_modules` attributes based on the current state
            of the `Registry` object.

        Note that `set_key_fields` must be called before `config.load`.

        Attributes:
            target_modules (List[str]): Target module names that need to be built.
            registered_modules (List[str]): A list of all module names that have been registered.
        """
        cls.target_fields = target_fields

    def isolated_keys(self):
        keys = list(self.keys())
        for k in keys:
            if k not in self.target_fields:
                yield k

    def _parse_target_modules(self):
        for name in self.target_fields:
            if name not in self:
                continue
            if name in self.registered_fields:
                base = name
            else:
                # m = next(iter(self[name].keys()))
                _, base = Registry.find(list(self[name].keys())[0])
                if base is None:
                    raise CoreConfigParseError(f"Unregistered module `{name}`")
            v = _attr2module(self.pop(name), base)
            v = _dict2list(v)
            self[name] = ModuleWrapper(v)

    def _parse_isolated_registered_module(self, name):
        v = _attr2module(self.pop(name), name)
        v = _dict2list(v, True)
        for i in v:
            assert i.base == name
            self[i.name] = ModuleWrapper(i)
            _, _ = Registry.find(i.name)
            if _ is None:
                raise CoreConfigParseError(f"Unregistered module `{i.name}`")

    def _parse_implicit_module(self, name, module_type=ModuleNode) -> ModuleWrapper:
        _, base = Registry.find(name)
        converted = ModuleWrapper(module_type(name, base))
        if not base:
            raise CoreConfigParseError(f"Unregistered module `{name}`")
        if module_type == ReusedNode:
            self[name] = converted
        return converted

    def _parse_isolated_module(self, name, module_type=ModuleNode):
        _, base = Registry.find(name)
        if base:
            self[name] = ModuleWrapper(module_type(name, base).update(self[name]))

    def _parse_isolated_obj(self):
        for name in self.isolated_keys():
            modules = self[name]
            if isinstance(modules, dict):
                if name in self.registered_fields:
                    self._parse_isolated_registered_module(name)
                else:
                    self._parse_isolated_module(name)

    def _contain_module(self, name):
        for k in self.target_fields:
            if k not in self:
                continue
            wrapper = self[k]
            if not isinstance(wrapper, ModuleWrapper):
                wrapper = ModuleWrapper(wrapper)
            for i in wrapper.values():
                if i.name == name:
                    self.__base__ = k
                    return True
        return False

    def _get_name(self, name, ori_name):
        if not name.startswith("$"):
            return name
        base = name[1:]
        wrapper = self.get(base, False)
        if not wrapper:
            raise CoreConfigParseError(
                f"Cannot find field {base} with `{ori_name}`,"
                "please adjust module definition order in config files."
            )
        if len(wrapper) == 1:
            return wrapper.first().name
        raise CoreConfigParseError(
            f"More than one candidates are found: {[k.name for k in wrapper.values()]}"
            f" with `{ori_name}`, please redifine the field `{base}` in config files."
        )

    # FIXME: Maybe ReusedNode should firstly search in hidden modules?
    def _parse_single_param(self, ori_name, params):
        name, attrs = _parse_param(ori_name)
        name = self._get_name(name, ori_name)
        ModuleType = _dispatch_module_node[params.base]
        if name in self:
            converted = _convert2module(self[name], params.base, ModuleType)
            self[name] = converted
        elif self._contain_module(name):
            # once the hiddn module was added to config
            # this branch is unreachable.
            wrapper = self[self.__base__]
            converted = _convert2module(getattr(wrapper, name), params.base, ModuleType)
            self[name] = converted
            if self.__base__ not in self.target_fields:
                wrapper.pop(name)
                if len(wrapper) == 0:
                    self.pop(self.__base__)
                self[self.__base__] = wrapper.first()
            else:
                wrapper.update(converted)
        else:
            # once the implicit module was added to config
            # this branch is unreachable.
            converted = self._parse_implicit_module(name, ModuleType)
        converted = converted.first()

        if not isinstance(converted, ModuleType):
            raise CoreConfigParseError(
                f"Error when parse params {params.name}, \
                  target_type is {ModuleType}, but got {type(converted)}"
            )
        if attrs:
            converted = ChainedInvocationWrapper(converted, attrs)
        return converted

    def _parse_module_node(self, node):
        to_pop = []
        param_names = list(node.keys())
        for param_name in param_names:
            params = node[param_name]
            if isinstance(params, InterNode):
                target_module_names = params.target_feild
                if not isinstance(target_module_names, list):
                    target_module_names = [target_module_names]
                converted_modules = [
                    self._parse_single_param(name, params)
                    for name in target_module_names
                ]
                to_pop.extend(target_module_names)
                node[param_name] = ModuleWrapper(converted_modules)
        if hasattr(self, "__route__"):
            delattr(self, "__route__")
        return to_pop

    def _parse_module_wrapper(self, wrapper):
        to_pop = []
        for m in wrapper.values():
            to_pop.extend(self._parse_module_node(m))
        return to_pop

    def _parse_inter_modules(self):
        to_pop = []
        for name in list(self.keys()):
            module = self[name]
            if isinstance(module, ModuleWrapper):
                to_pop.extend(self._parse_module_wrapper(module))
        self._clean(to_pop)

    def _clean(self, to_pop):
        for i in to_pop:
            self.pop(i, None)

    def parse(self):
        self._parse_target_modules()
        self._parse_isolated_obj()
        self._parse_inter_modules()

    # TODO: enhance print. low priority.


# TODO: automatically generate pyi file
#   according to config files for type hinting. high priority.
# TODO: Add dump method to generate toml config files.
class LazyConfig:
    globals: Registry
    hook_key = "ConfigHook"

    def __init__(self, config: AttrNode) -> None:
        self.modules_dict, self.isolated_dict = {}, {}
        self.target_modules = config.target_fields
        config.registered_fields = list(Registry._registry_pool.keys())
        self._config = deepcopy(config)
        self.build_config_hooks()
        self._config.parse()

    def update(self, cfg: "LazyConfig"):
        self._config.update(cfg._config)

    def build_config_hooks(self):
        hooks = self._config.pop(LazyConfig.hook_key, [])
        if hooks:
            _, base = Registry.find(list(hooks.keys())[0])
            hooks = [
                InterNode(name, base).update(params)() for name, params in hooks.items()
            ]
        self.hooks = ConfigHookManager(hooks)

    def __getattr__(self, __name: str) -> Any:
        if __name in self._config:
            if not self.hooks:
                self.build_config_hooks()
            return self._config[__name]
        raise KeyError(__name)

    # TODO: refine output
    def build_all(self) -> Tuple[Dict, Dict]:
        if self.target_modules is None:
            raise CoreConfigBuildError(
                "`target_modules` can't be None when calling `LazyConfig.build_all`"
            )
        module_dict, isolated_dict = {}, {}
        self.hooks.call_hooks("pre_build", self, module_dict, isolated_dict)
        for name in self.target_modules:
            if name not in self._config:
                continue
            self.hooks.call_hooks("every_build", self, module_dict, isolated_dict)
            module_dict[name] = self._config[name]()
        for name in self._config.isolated_keys():
            self.hooks.call_hooks("every_build", self, module_dict, isolated_dict)
            module = self._config[name]
            if isinstance(module, ModuleNode):
                module = module()
            isolated_dict[name] = module
        self.hooks.call_hooks("after_build", self, module_dict, isolated_dict)
        return module_dict, isolated_dict

    def __str__(self):
        return str(self._config)


def set_target_fields(target_fields):
    if hasattr(AttrNode, "target_fields"):
        logger.ex("`target_fields` will be set to {}", target_fields)
    if target_fields:
        AttrNode.set_target_fields(target_fields)


def load_config(filename: str, base_key: str = "__base__") -> AttrNode:
    logger.info(f"load_config {filename}")
    ext = os.path.splitext(filename)[-1]
    path = os.path.dirname(filename)

    # TODO: support more config file format. low priority.
    if ext in [".toml"]:
        config = toml.load(filename, AttrNode)
    else:
        raise CoreConfigSupportError(
            "Only support `toml` files for now, but got {}".format(filename)
        )

    base_cfgs = [
        load_config(os.path.join(path, i), base_key) for i in config.pop(base_key, [])
    ]
    base_cfg = AttrNode()
    for c in base_cfgs:
        base_cfg.update(c)
    base_cfg.update(config)

    return base_cfg


def load(filename: str, base_key: str = BASE_CONFIG_KEY) -> LazyConfig:
    st = time.time()
    load_registries()
    config = load_config(filename, base_key)
    lazy_config = LazyConfig(config)
    logger.success("Config loading and parsing cost {:.4f}s!", time.time() - st)
    return lazy_config


def silent():
    global LOG_BUILD_MESSAGE  # pylint: disable=global-statement
    LOG_BUILD_MESSAGE = False


def build_all(cfg: LazyConfig) -> Tuple[dict, dict]:
    st = time.time()
    modules = cfg.build_all()
    logger.success("Modules building costs {:.4f}s!", time.time() - st)
    return modules
