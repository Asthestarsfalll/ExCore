import os
import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import toml
import yaml
from toml.decoder import _groupname_re

from .exceptions import CoreConfigBuildError, CoreConfigSupportError, ModuleBuildError
from .logger import logger
from .registry import Registry as Reg

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
        CONF.update(toml.load(filename))
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

    all_keys = list(cfg.keys())
    registried_keys = registried_keys or list(Reg.children.keys())
    global_dict = Reg.make_global()
    isolated_keys = [k for k in all_keys if k not in registried_keys]

    def _build(cls_name: str, kwargs: Dict, base: str = ""):
        if cls_name in isolated_keys:
            isolated_keys.remove(cls_name)
        if not kwargs:
            name = global_dict.find(cls_name)[1]
            kwargs = cfg[name][cls_name]
            if name in isolated_keys:
                cfg[name].pop(cls_name)

        cls = Reg.get_child(base, {}).get(cls_name, None)
        if cls is None:
            cls = global_dict.get(cls_name, None)
        if not cls or kwargs is None:
            raise CoreConfigBuildError("No such module named {}".format(cls_name))
        clean_kwargs = {}
        for k, v in kwargs.items():
            if _is_tag(k):
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
        logger.success("Build module {} with augments: {}", cls_name, kwargs)
        return module

    modules_dict = defaultdict(list)
    for k in registried_keys:
        kwargs = cfg[k]
        modules_dict[k].extend(_build(n, kwargs[n], base=k) for n in kwargs.keys())

    isolated_dict = {k: cfg[k] for k in isolated_keys if cfg[k] != {}}

    logger.success("All modules have been built successfully!")
    return modules_dict, isolated_dict
