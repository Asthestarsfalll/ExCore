import os
import re
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple

import toml
import yaml
from toml.decoder import _groupname_re

from .exceptions import CoreConfigBuildError, CoreConfigSupportError, ModuleBuildError
from .logger import logger
from .registry import Registry as Reg
from .hook import ConfigHookManager

_groupname_re = re.compile(r"^[A-Za-z0-9_-]+$")  # noqa

CONF = Reg("__configs")


@logger.catch
def load(filename: str):
    ext = os.path.splitext(filename)[-1]
    path = os.path.dirname(filename)

    if ext in [".yml", ".yaml"]:
        with open(filename) as f:
            CONF.update(yaml.load(f, yaml.Loader))
    elif ext in [".toml"]:
        CONF.update(toml.load(filename, OrderedDict))
    else:
        raise CoreConfigSupportError("Only support `yaml` or `toml` files, but got {}".format(ext))
    base_cfgs = [load(os.path.join(path, i)) for i in CONF.pop("__base__", [])]
    [CONF.update(c) for c in base_cfgs]
    return CONF


def _is_tag(k: str) -> bool:
    return "!" == k[0]


def build_all(  # noqa
    cfg,
    registried_keys: Optional[List[str]] = None,
) -> Tuple[Dict, Dict]:
    logger.info("Begin to build modules!")
    logger.info(cfg)

    hooks = cfg.pop("ConfigHook", None)

    all_keys = list(cfg.keys())
    registried_keys = registried_keys or list(Reg.children.keys())
    global_dict = Reg.make_global()
    isolated_keys = [k for k in all_keys if k not in registried_keys]
    config_hooks = None

    def _build(cls_name: str, kwargs: Dict, base: str = ""):
        if cls_name in isolated_keys:
            isolated_keys.remove(cls_name)
        if kwargs is None:
            name = global_dict.find(cls_name)[1]
            kwargs = cfg.get(name, {}).get(cls_name, {})
            if name in isolated_keys and kwargs:
                cfg[name].pop(cls_name)

        cls = Reg.get_child(base, {}).get(cls_name, None)
        if cls is None:
            cls = global_dict.get(cls_name, None)
        if not cls or kwargs is None:
            raise CoreConfigBuildError("No such module named {}".format(cls_name))

        clean_kwargs = {}
        for k, v in kwargs.items():
            if _is_tag(k):
                k = k[1:]
                if isinstance(v, list):
                    v = [_build(i, cfg.get(i, None)) for i in v]
                else:
                    v = _build(v, cfg.get(v, None))
            clean_kwargs[k] = v
        try:
            module = cls(**clean_kwargs)
        except BaseException:
            raise ModuleBuildError(
                "Build Error with module {} and augments {}".format(cls, clean_kwargs)
            )
        logger.success("Build module {} with augments: {}", cls_name, clean_kwargs)
        return module

    modules_dict = dict()

    if hooks:
        key = list(hooks.keys())[0]
        base_name = key[1:] if _is_tag(key) else key
        hooks = [_build(v, cfg.get(v, None), base_name) for v in hooks[key]]
        config_hooks = ConfigHookManager(hooks)
        if config_hooks.exist("pre_build"):
            config_hooks.call_hooks("pre_build", cfg, modules_dict)

    for k in registried_keys:
        kwargs = cfg[k]
        modules = [_build(n, kwargs[n], base=k) for n in kwargs.keys()]
        modules_dict[k] = modules[0] if len(modules) == 1 else modules
        if config_hooks and config_hooks.exist("every_build"):
            config_hooks.call_hooks("every_build", cfg, modules_dict)

    if config_hooks and config_hooks.exist("after_build"):
        config_hooks.call_hooks("after_build", cfg, modules_dict)

    isolated_dict = {k: cfg[k] for k in isolated_keys if cfg[k] != {}}

    logger.success("All modules have been built successfully!")

    return modules_dict, isolated_dict
