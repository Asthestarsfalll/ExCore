import json
import os
import pprint
from dataclasses import dataclass
from sys import exc_info
from typing import Any, Dict, List, Optional, Tuple

import toml

from ._exceptions import (CoreConfigBuildError, CoreConfigSupportError,
                          ModuleBuildError)
from .hook import ConfigHookManager
from .logger import logger
from .registry import Registry
from .utils import CacheOut

__all__ = ["load"]

# TODO(Asthestarsfalll): Prune and decoupling. low priority.

REUSE_FLAG = '!'
INTER_FLAG = '@'

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


def _dict2list(v, return_list=False):
    """
    Converts a dictionary to a list of its values.

    Args:
        v (dict): The dictionary to be converted.

    Returns:
        list: A list of the values in the input dictionary. 
            If the input is not a dictionary or is an empty dictionary,
            the original input is returned. 
            If the input dictionary has only one value, 
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

    def update(self, others: dict) -> "ModuleNode":
        """
        Override native `update` method to make it use the overrode
        `__setitem__` method.
        Return self for convenience.
        """
        for k, v in others.items():
            self[k] = v
        return self

    def __call__(self):
        cls = Registry.get_registry(self.base)[self.name]
        params = {}
        for k, v in self.items():
            if isinstance(v, ModuleNode):
                v = v()
            params[k] = v
        try:
            module = cls(**params)
        except:
            logger.critical(exc_info())
            raise ModuleBuildError(
                "Build Error with module {} and arguments {}".format(cls, params)
            )
        return module


@dataclass
class InterNode(ModuleNode):
    pass


@dataclass
class ReuseNode(ModuleNode):
    @CacheOut()
    def __call__(self):
        return super()()


_dispatch_module_node = {"": ModuleNode, REUSE_FLAG: ReuseNode, INTER_FLAG: InterNode}


class AttrNode(dict):
    target_modules: List
    # remainder_modules: List
    # union_modules: List
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
            and calculates the `remainder_modules`, `union_modules`, and `registered_modules`
            attributes based on the current state of the `Registry` object.

        Note that `set_key_fields` must be called before `config.load`.

        Attributes:       
            target_modules (List[str]): Target module names that need to be built.
            registered_modules (List[str]): A list of all module names that have been registered.
            union_modules (List[str]): A list of module names that belong to both the `target_modules`
                and `registered_modules` lists.
            remainder_modules (List[str]): The complementary set of union_modules.
        """
        cls.target_modules = target_modules
        registered_modules = Registry._registry_pool.keys()
        cls.registered_modules = list(registered_modules)
        # cls.union_modules = [k for k in registered_modules if k in target_modules]
        # cls.remainder_modules = [k for k in target_modules if k not in cls.union_modules]
        # cls.remainder_modules.extend(
        #     [k for k in registered_modules if k not in cls.union_modules]
        # )

    # def isolated_items(self):
    #     """
    #         Returns an iterator over the key-value pairs in the dictionary that do not belong
    #             to the `target_modules` list. 
    #     """
    #     for k, v in self.items():
    #         if k not in self.target_modules:
    #             yield k, v

    def isolated_keys(self):
        keys = list(self.keys())
        for k in keys:
            if k not in self.target_modules:
                yield k

    def __setitem__(self, k, v) -> None:
        """
        In toml file loading stage, `AttrNode` will convert those which are in 
            `target_modules` to `ModuleNode`.
        If element of target module is special(begin with `REUSE_FLAG` or `INTER_FLAG`),
            it will be converted to ReuseNode/InterNode as a placeholder.

        Example:
            target_modules = ['Model', 'Loss']
            Config:
                [Model.FCN]
                !backbone = 'ResNet'
                !head = 'SimpleHead'

                [Model.ResNet]
                in_channel = 3
                depth = 50

                [SimpleHead]
                in_channel = 256
                num_classes = 19

                [Loss.CrossEntropyLoss]

                ...

        Result:
            {
                'Model': [ModuleNode(name='FCN', base='Model'), 
                          ModuleNode(name='ResNet', base='Model'],
                'Loss': ModuleNode(name='BoundaryLoss', base='Loss'),
                'SimpleHead': {'in_channel': 256, 'num_classes': 19},
            }

        """
        if k in self.target_modules:
            if not isinstance(v, dict):
                raise RuntimeError()
            v = _attr2module(v, k)
            v = _dict2list(v)
        super().__setitem__(k, v)

    def update(self, others: dict) -> None:
        for k, v in others.items():
            self[k] = v

    def normalize(self):
        for name in self.isolated_keys():
            modules = self[name]
            if isinstance(modules, dict):
                if name in self.registered_modules:
                    v = _attr2module(self.pop(name), name)
                    v = _dict2list(v, True)
                    for i in v:
                        assert i.base == name
                        self[i.name] = i
                else:
                    _, base = Registry.find(name)
                    if base:
                        self[name] = ModuleNode(name, base)

    # TODO(Asthestarsfalll): enhance print. low priority.
    def print(self):
        print(json.dumps(self, indent=4))


class ModuleList:
    def __init__(self, modules: List[ModuleNode]):
        self.modules = modules
        self.names = [m.name for m in modules]

    def __contain__(self, __name:str) -> bool:
        return __name in self.names

    def __getattr__(self, __name: str) -> Any:
        for idx, name in enumerate(self.names):
            if name == __name:
                return self.modules[idx]
        raise KeyError()
        # return super().__getattribute__(__name)

    def __call__(self):
        return [m() for m in self.modules]

    def __repr__(self) -> str:
        return str(self.modules)



# TODO(Asthestarsfalll): automatically generate pyi file 
#   according to config files for type hinting. high priority.
class LazyConfig:
    globals: Registry
    hook_key = "ConfigHook"

    # def __new__(cls, config):
    #     class LazyConfigImpl(LazyConfig):
    #         pass
    #     return super().__new__(LazyConfigImpl)

    def __init__(self, config: AttrNode) -> None:
        LazyConfig.globals = Registry.make_global()
        # buffer reuse_names modules
        self.reuse_modules = {}
        self.modules_dict, self.isolated_dict = {}, {}
        self._config = self.parse_config(config)

    def parse_config(self, config: AttrNode) -> Dict:
        self.build_config_hooks(config)
        self.parse_target_modules(config)
        _config = {**config}
        for k, v in config.isolated_items():
            if isinstance(v, AttrNode):
                _, base = Registry.find(k)
                if base:
                    _config[k] = ModuleNode(k, base).update(v)
        return _config
    
    @staticmethod
    def parse_target_modules(config: AttrNode) -> None:
        for name in config.target_modules:
            modules = config[name]
            if isinstance(modules, dict):
                pass

    def build_config_hooks(self, config):
        self.hooks = config.pop(LazyConfig.hook_key, [])
        # self.config_hooks = [LazyConfig.globals[h]() for ]

    def __getattr__(self, __name: str) -> Any:
        if __name in self.target_modules:
            return self._config[__name]
        # return super().__getattribute__(__name)
        raise KeyError()

    def build_all(self) -> Tuple[Dict, Dict]:
        if self.target_modules is None:
            raise CoreConfigBuildError(
                "`target_modules` can't be None when calling `LazyConfig.build_all`"
            )
        raise NotImplementedError()

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
    filename: str, target_modules: List[str], base_key: str = "__base__"
) -> LazyConfig:
    AttrNode.set_key_fields(target_modules)
    config = load_config(filename, base_key)
    config.normalize()
    pprint.pprint(config)
    config.print()
    breakpoint()

    lazy_config = LazyConfig(config)
    print()
    for k, v in lazy_config._config.items():
        print(k, "\n\t", v)
    return lazy_config


def build_all(cfg: LazyConfig) -> Tuple[dict, dict]:
    raise NotImplemented
    return cfg.build_all()


# def build_all(  # noqa  pylint: disable=too-many-statements
#     cfg,
#     registried_keys: Optional[List[str]] = None,
# ) -> Tuple[Dict, Dict]:
#     logger.info("Begin to build modules!")
#     logger.info(cfg)

#     hooks = cfg.pop("ConfigHook", None)

#     all_keys = list(cfg.keys())
#     registried_keys = registried_keys or list(Reg._registry_pool.keys())
#     global_dict = Reg.make_global()
#     isolated_keys = [k for k in all_keys if k not in registried_keys]
#     config_hooks = None

#     def _build(cls_name: str, kwargs: Dict, base: str = ""):
#         if cls_name in isolated_keys:
#             isolated_keys.remove(cls_name)
#         if kwargs is None:
#             name = global_dict.find(cls_name)[1]
#             kwargs = cfg.get(name, {}).get(cls_name, {})
#             if name in isolated_keys and kwargs:
#                 cfg[name].pop(cls_name)

#         cls = Reg.get_registry(base, {}).get(cls_name, None)
#         if cls is None:
#             cls = global_dict.get(cls_name, None)
#         if not cls or kwargs is None:
#             raise CoreConfigBuildError("No such module named {}".format(cls_name))

#         clean_kwargs = {}
#         for k, v in kwargs.items():
#             if _is_tag(k):
#                 k = k[1:]
#                 if isinstance(v, list):
#                     v = [_build(i, cfg.get(i, None)) for i in v]
#                 else:
#                     v = _build(v, cfg.get(v, None))
#             clean_kwargs[k] = v
#         try:
#             module = cls(**clean_kwargs)
#         except BaseException as exc:
#             logger.critical(exc_info())
#             raise ModuleBuildError(
#                 "Build Error with module {} and augments {}".format(cls, clean_kwargs)
#             ) from exc
#         logger.success("Build module {} with augments: {}", cls_name, clean_kwargs)
#         return module

#     modules_dict = dict()

#     if hooks:
#         key = list(hooks.keys())[0]
#         # TODO: make this pythonic
#         base_name = key[1:] if _is_tag(key) else key
#         hooks = [_build(v, cfg.get(v, None), base_name) for v in hooks[key]]
#         config_hooks = ConfigHookManager(hooks)
#         if config_hooks.exist("pre_build"):
#             config_hooks.call_hooks("pre_build", cfg, modules_dict)

#     for k in registried_keys:
#         kwargs = cfg[k]
#         modules = [_build(n, kwargs[n], base=k) for n in kwargs.keys()]
#         modules_dict[k] = modules[0] if len(modules) == 1 else modules
#         if config_hooks and config_hooks.exist("every_build"):
#             config_hooks.call_hooks("every_build", cfg, modules_dict)

#     if config_hooks and config_hooks.exist("after_build"):
#         config_hooks.call_hooks("after_build", cfg, modules_dict)

#     isolated_dict = {k: cfg[k] for k in isolated_keys if cfg[k] != {}}

#     logger.success("All modules have been built successfully!")

#     return modules_dict, isolated_dict
