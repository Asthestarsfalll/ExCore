from __future__ import annotations

import time
from copy import deepcopy
from typing import Any

from ..engine.hook import ConfigHookManager, Hook
from ..engine.logging import logger
from ..engine.registry import Registry
from . import models
from .models import ConfigHookNode, InterNode, ModuleWrapper
from .parse import ConfigDict


class LazyConfig:
    hook_key: str = "ExcoreHook"
    modules_dict: dict[str, ModuleWrapper]
    isolated_dict: dict[str, Any]

    def __init__(self, config: ConfigDict) -> None:
        self.modules_dict, self.isolated_dict = {}, {}
        self.target_modules = config.primary_fields
        config.registered_fields = list(Registry._registry_pool.keys())
        config.all_fields = set([*config.registered_fields, *config.primary_fields])
        self._config = deepcopy(config)
        self._original_config = deepcopy(config)
        self.__is_parsed__ = False

    def parse(self) -> None:
        st = time.time()
        self.build_config_hooks()
        self._config.parse()
        logger.success("Config parsing cost {:.4f}s!", time.time() - st)
        self.__is_parsed__ = True
        logger.ex(str(self._config))

    @property
    def config(self) -> ConfigDict:
        return self._original_config

    def update(self, cfg: LazyConfig) -> None:
        self._config.update(cfg._config)

    def build_config_hooks(self) -> None:
        hook_cfgs = self._config.pop(LazyConfig.hook_key, [])
        hooks = []
        if hook_cfgs:
            _, base = Registry.find(list(hook_cfgs.keys())[0])
            assert base is not None, hook_cfgs
            reg = Registry.get_registry(base)
            for name, params in hook_cfgs.items():
                hook: Hook = ConfigHookNode.from_str(reg[name], params)()  # type: ignore
                if hook:
                    hooks.append(hook)
                else:
                    self._config[name] = InterNode.from_str(reg[name], params)
        self.hooks = ConfigHookManager(hooks)

    def __getattr__(self, __name: str) -> Any:
        if __name in self._config:
            if not hasattr(self, "hooks"):
                self.build_config_hooks()
            return self._config[__name]
        raise AttributeError(__name)

    def build_all(self) -> tuple[ModuleWrapper, dict[str, Any]]:
        if not self.__is_parsed__:
            self.parse()
        module_dict = ModuleWrapper()
        isolated_dict: dict[str, Any] = {}

        self.hooks.call_hooks("pre_build", self, module_dict, isolated_dict)
        for name in self.target_modules:
            if name not in self._config:
                continue
            self.hooks.call_hooks("every_build", self, module_dict, isolated_dict)
            out = self._config[name]()
            if isinstance(out, list):
                out = ModuleWrapper(out)
            module_dict[name] = out
        for name in self._config.non_primary_keys():
            isolated_dict[name] = self._config[name]
        self.hooks.call_hooks("after_build", self, module_dict, isolated_dict)
        models.IS_PARSING = False

        return module_dict, isolated_dict

    def dump(self, dump_path: str) -> None:
        self._original_config.dump(dump_path)

    def __str__(self) -> str:
        return str(self._config)
