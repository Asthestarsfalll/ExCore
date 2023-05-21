import os
import time
from dataclasses import dataclass
from sys import exc_info
from typing import Any, Dict, List, Tuple

import toml

from ._exceptions import (CoreConfigBuildError, CoreConfigParseError,
                          CoreConfigSupportError, ModuleBuildError)
from .hook import ConfigHookManager
from .logger import logger
from .registry import Registry
from .utils import CacheOut

__all__ = ["load", "silent"]

# TODO(Asthestarsfalll): Prune and decoupling. low priority.
# TODO(Asthestarsfalll): Improve error messages. high priority.

REUSE_FLAG = "@"
INTER_FLAG = "!"
LOG_BUILD_MESSAGE = True
BASE_CONFIG_KEY = "__base__"


def _is_special(k: str) -> Tuple[str, str]:
    """
    Determine if the given string begin with target special character.
        `!` denotes reuse module, which will only be built once and cache out.
        `@` denotes intermediate module, which will be built from scratch if need.

    Args:
        k (str): The input string to check.

    Returns:
        Tuple[str, str]: A tuple containing the modified string and the special character.
    """
    if REUSE_FLAG == k[0]:
        return k[1:], REUSE_FLAG
    elif INTER_FLAG == k[0]:
        return k[1:], INTER_FLAG
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


def _convert_module(m, k_type):
    if not isinstance(m, ModuleNode):
        return m
    ModuleType = _dispatch_module_node[k_type]
    return ModuleType(m.name, m.base).update(m)


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

    def add(self, **kwargs):
        self.update(kwargs)

    def _set_base(self, base) -> None:
        assert base
        self.base = base

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
            if isinstance(v, ModuleNode):
                v = v()
            params[k] = v
        return params

    def __call__(self):
        try:
            cls = Registry.get_registry(self.base)[self.name]
            params = self._get_params()
            module = cls(**params)
        except Exception as exc:
            logger.critical(exc_info())
            raise ModuleBuildError(
                f"Build Error with module {cls} and arguments {params}"
            ) from exc
        if LOG_BUILD_MESSAGE:
            logger.success(
                f"Successfully build module: {self.name}, with arguments {params}"
            )
        return module


@dataclass
class InterNode(ModuleNode):
    @property
    def target_module(self):
        assert self.base in [REUSE_FLAG, INTER_FLAG]
        return self.pop(self.base)


@dataclass
class ReuseNode(InterNode):
    @CacheOut()
    def __call__(self):
        return super().__call__()


_dispatch_module_node = {"": ModuleNode, REUSE_FLAG: ReuseNode, INTER_FLAG: InterNode}


class ModuleList(list):
    def __init__(self, modules: List[ModuleNode]):
        super().__init__()
        assert isinstance(modules, list)
        self.extend(modules)
        self.names = [m.name for m in modules]

    def __contain__(self, __name: str) -> bool:
        return __name in self.names

    def __getattr__(self, __name: str) -> Any:
        for idx, name in enumerate(self.names):
            if name == __name:
                return self[idx]
        raise KeyError()

    def __call__(self):
        return [m() for m in self]

    def pop(self, __name: str):
        for idx, name in enumerate(self.names):
            if name == __name:
                return super().pop(idx)
        raise IndexError()

    def __repr__(self) -> str:
        return f"ModuleList{super().__repr__()}"


class AttrNode(dict):
    target_modules: List
    registered_modules: List

    def __new__(cls):
        if not hasattr(cls, "target_modules"):
            raise RuntimeError("Call `set_key_fields` before `load`")

        # make key fields unique when multiple load.
        class AttrNodeImpl(AttrNode):
            pass

        inst = super().__new__(AttrNodeImpl)
        return inst

    @classmethod
    def set_key_fields(cls, target_modules):
        """
        Sets the `target_modules` attribute to the specified list of module names,
            and `registered_modules` attributes based on the current state
            of the `Registry` object.

        Note that `set_key_fields` must be called before `config.load`.

        Attributes:
            target_modules (List[str]): Target module names that need to be built.
            registered_modules (List[str]): A list of all module names that have been registered.
        """
        cls.target_modules = target_modules
        registered_modules = Registry._registry_pool.keys()
        cls.registered_modules = list(registered_modules)

    def isolated_keys(self):
        keys = list(self.keys())
        for k in keys:
            if k not in self.target_modules:
                yield k

    def _parse_target_modules(self):
        for name in self.target_modules:
            if name in self.registered_modules:
                base = name
            else:
                m = next(iter(self[name].keys()))
                _, base = Registry.find(m)
                if base is None:
                    raise CoreConfigParseError(f"Unregistered module `{name}`")
            v = _attr2module(self.pop(name), base)
            v = _dict2list(v)
            if isinstance(v, list):
                v = ModuleList(v)
            self[name] = v

    def _parse_isolated_registerd_module(self, name):
        v = _attr2module(self.pop(name), name)
        v = _dict2list(v, True)
        for i in v:
            assert i.base == name
            self[i.name] = i
            _, _ = Registry.find(i.name)
            if _ is None:
                raise CoreConfigParseError(f"Unregistered module `{i.name}`")

    def _parse_implicit_module(self, name, module_type=ModuleNode):
        _, base = Registry.find(name)
        if base:
            self[name] = module_type(name, base)

    def _parse_isolated_obj(self):
        for name in self.isolated_keys():
            modules = self[name]
            if isinstance(modules, dict):
                if name in self.registered_modules:
                    self._parse_isolated_registerd_module(name)
                else:
                    self._parse_implicit_module(name)

    def _contain_module(self, name):

        for k in self.target_modules:
            v = self[k]
            if not isinstance(v, ModuleList):
                v = [v]
            for i in v:
                if i.name == name:
                    self.__route__ = k
                    return True
        return False

    def _parse_single_param(self, name, params):
        if name in self:
            converted = _convert_module(self[name], params.base)
            # for shared modules
            self[name] = converted
        elif self._contain_module(name):
            # once the hiddn module was added to config
            # this branch is unreachable.
            wrapper = self[self.__route__]
            if isinstance(wrapper, ModuleList):
                wrapper = getattr(wrapper, name)
            converted = _convert_module(wrapper, params.base)
            self[name] = converted
            if self.__route__ not in self.target_modules:
                self[self.__route__].pop(name)
                if len(self[self.__route__]) == 1:
                    self[self.__route__] = self.pop(self.__route__)[0]
            else:
                self[self.__route__] = converted
        else:
            # once the implicit module was added to config
            # this branch is unreachable.
            self._parse_implicit_module(name, InterNode)
            converted = self.get(name, False)
            if converted:
                raise CoreConfigParseError(f"Unregistered module `{name}`")
        return converted

    def _parse_module_node(self, node):
        to_pop = []
        param_names = list(node.keys())
        for param_name in param_names:
            params = node[param_name]
            if isinstance(params, InterNode):
                target_module_names = params.target_module
                if not isinstance(target_module_names, list):
                    target_module_names = [target_module_names]
                converted_modules = [
                    self._parse_single_param(name, params)
                    for name in target_module_names
                ]
                to_pop.extend(target_module_names)
                if len(converted_modules) == 1:
                    converted_modules = converted_modules[0]
                else:
                    converted_modules = ModuleList(converted_modules)
                node[param_name] = converted_modules
        if hasattr(self, "__route__"):
            delattr(self, "__route__")
        return to_pop

    def _parse_module_list(self, lis):
        to_pop = []
        for m in lis:
            to_pop.extend(self._parse_module_node(m))
        return to_pop

    def _parse_single_inter_module(self, module: ModuleList) -> List:
        to_pop = []
        if isinstance(module, ModuleNode):
            to_pop.extend(self._parse_module_node(module))
        elif isinstance(module, ModuleList):
            to_pop.extend(self._parse_module_list(module))
        return to_pop

    def _parse_inter_modules(self):
        to_pop = []
        for name in list(self.keys()):
            to_pop.extend(self._parse_single_inter_module(self[name]))
        self._clean(to_pop)

    def _clean(self, to_pop):
        to_pop = set(to_pop)
        for i in to_pop:
            self.pop(i)

    def parse(self):
        self._parse_target_modules()
        self._parse_isolated_obj()
        self._parse_inter_modules()

    # TODO(Asthestarsfalll): enhance print. low priority.


# TODO(Asthestarsfalll): automatically generate pyi file
#   according to config files for type hinting. high priority.
class LazyConfig:
    globals: Registry
    hook_key = "ConfigHook"

    def __init__(self, config: AttrNode) -> None:
        self.modules_dict, self.isolated_dict = {}, {}
        self.target_modules = config.target_modules
        self.parse_config(config)
        self._config = config

    def parse_config(self, config: AttrNode):
        config.parse()
        self.build_config_hooks(config)

    def build_config_hooks(self, config):
        hooks = config.pop(LazyConfig.hook_key, [])
        if hooks:
            _, base = Registry.find(hooks[0])
            hooks = [InterNode(h, base)() for h in hooks]
        self.hooks = ConfigHookManager(hooks)

    def __getattr__(self, __name: str) -> Any:
        if __name in self._config:
            return self._config[__name]
        raise KeyError()

    def build_all(self) -> Tuple[Dict, Dict]:
        if self.target_modules is None:
            raise CoreConfigBuildError(
                "`target_modules` can't be None when calling `LazyConfig.build_all`"
            )
        module_dict, isolated_dict = {}, {}
        self.hooks.call_hooks("pre_build", self, module_dict, isolated_dict)
        for name in self.target_modules:
            self.hooks.call_hooks("every_build", self, module_dict, isolated_dict)
            module_dict[name] = self._config[name]()
        for name in self._config.isolated_keys():
            self.hooks.call_hooks("every_build", self, module_dict, isolated_dict)
            module = self._config[name]
            if isinstance(module, ModuleNode):
                module = module()
            isolated_dict[name] = module
        self.hooks.call_hooks("every_build", self, module_dict, isolated_dict)
        return module_dict, isolated_dict

    def __str__(self):
        return str(self._config)


def set_target_modules(target_modules):
    AttrNode.set_key_fields(target_modules)


def load_config(filename: str, base_key: str = "__base__") -> AttrNode:
    ext = os.path.splitext(filename)[-1]
    path = os.path.dirname(filename)

    # TODO(Asthestarsfalll): support more config file format. low priority.
    if ext in [".toml"]:
        config = toml.load(filename, AttrNode)
    else:
        raise CoreConfigSupportError(
            "Only support `toml` files for now, but got {}".format(filename)
        )

    base_cfgs = [
        load_config(os.path.join(path, i), base_key) for i in config.pop(base_key, [])
    ]
    # TODO(Asthestarsfalll): support inherit mechanism of config. high priority.
    [config.update(c) for c in base_cfgs]  # pylint: disable=expression-not-assigned
    return config


def load(
    filename: str, target_modules: List[str], base_key: str = BASE_CONFIG_KEY
) -> LazyConfig:
    st = time.time()
    AttrNode.set_key_fields(target_modules)
    config = load_config(filename, base_key)
    lazy_config = LazyConfig(config)
    logger.success("Config loading and parsing cost {}s!", time.time() - st)
    return lazy_config


def silent():
    global LOG_BUILD_MESSAGE
    LOG_BUILD_MESSAGE = False


def build_all(cfg: LazyConfig) -> Tuple[dict, dict]:
    return cfg.build_all()
