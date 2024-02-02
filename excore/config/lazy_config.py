from copy import deepcopy
from typing import Any, Dict, Tuple

from .._exceptions import CoreConfigBuildError
from ..engine.hook import ConfigHookManager
from ..engine.registry import Registry
from .model import ConfigHookNode, InterNode, ModuleNode, ModuleWrapper
from .parse import AttrNode


# TODO: automatically generate pyi file
#   according to config files for type hinting. high priority.
# TODO: Add dump method to generate toml config files.
class LazyConfig:
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
        hook_cfgs = self._config.pop(LazyConfig.hook_key, [])
        hooks = []
        if hook_cfgs:
            _, base = Registry.find(list(hook_cfgs.keys())[0])
            for name, params in hook_cfgs.items():
                hook = ConfigHookNode(name, base).update(params)()
                if hook:
                    hooks.append(hook)
                else:
                    self._config[name] = InterNode(name, base).update(params)
        self.hooks = ConfigHookManager(hooks)

    def __getattr__(self, __name: str) -> Any:
        if __name in self._config:
            if not hasattr(self, "hooks"):
                self.build_config_hooks()
            return self._config[__name]
        raise AttributeError(__name)

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
        for k in list(isolated_dict.keys()):
            obj = isolated_dict[k]
            if isinstance(obj, ModuleWrapper):
                isolated_dict.pop(k)
        return module_dict, isolated_dict

    def __str__(self):
        return str(self._config)
