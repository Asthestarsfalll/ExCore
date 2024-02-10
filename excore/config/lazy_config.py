from copy import deepcopy
from typing import Any, Dict, Tuple

from ..engine.hook import ConfigHookManager
from ..engine.registry import Registry
from .model import ConfigHookNode, InterNode, ModuleWrapper
from .parse import ConfigDict


# TODO: automatically generate pyi file
#   according to config files for type hinting. high priority.
# TODO: Add dump method to generate toml config files.
class LazyConfig:
    hook_key = "ConfigHook"

    def __init__(self, config: ConfigDict) -> None:
        self.modules_dict, self.isolated_dict = {}, {}
        self.target_modules = config.primary_fields
        config.registered_fields = list(Registry._registry_pool.keys())
        config.all_fields = set([*config.registered_fields, *config.primary_fields])
        self._config = deepcopy(config)
        self.build_config_hooks()
        self._config.parse()

    def update(self, cfg: "LazyConfig"):
        self._config.update(cfg._config)

    def build_config_hooks(self):
        hook_cfgs = self._config.pop(LazyConfig.hook_key, [])
        hooks = []
        if hook_cfgs:
            _, base = Registry.find(list(hook_cfgs.keys())[0])
            reg = Registry.get_registry(base)
            for name, params in hook_cfgs.items():
                hook = ConfigHookNode.from_str(reg[name], **params)()
                if hook:
                    hooks.append(hook)
                else:
                    self._config[name] = InterNode.from_str(reg[name], **params)
        self.hooks = ConfigHookManager(hooks)

    def __getattr__(self, __name: str) -> Any:
        if __name in self._config:
            if not hasattr(self, "hooks"):
                self.build_config_hooks()
            return self._config[__name]
        raise AttributeError(__name)

    # TODO: refine output
    def build_all(self) -> Tuple[ModuleWrapper, Dict]:
        module_dict, isolated_dict = ModuleWrapper(), {}
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
        return ModuleWrapper(module_dict), isolated_dict

    def __str__(self):
        return str(self._config)
