---
title: lazy_config
sidebar_position: 3
---

## TOC

- **Classes:**
  - 🅲 [LazyConfig](#🅲-lazyconfig)

## Classes

## 🅲 LazyConfig

```python
class LazyConfig:
    hook_key: str = "ExcoreHook"
    modules_dict: dict[str, ModuleWrapper] = None
    isolated_dict: dict[str, Any] = None
```


### 🅼 \_\_init\_\_

<details>

<summary>\_\_init\_\_</summary>
```python
def __init__(self, config: ConfigDict) -> None:
    self.modules_dict, self.isolated_dict = {}, {}
    self.target_modules = config.primary_fields
    config.registered_fields = list(Registry._registry_pool.keys())
    config.all_fields = set([*config.registered_fields, *config.primary_fields])
    self._config = deepcopy(config)
    self._original_config = deepcopy(config)
    self.__is_parsed__ = False
```

</details>

### 🅼 parse

<details>

<summary>parse</summary>
```python
def parse(self) -> None:
    st = time.time()
    self.build_config_hooks()
    self._config.parse()
    logger.success("Config parsing cost {:.4f}s!", time.time() - st)
    self.__is_parsed__ = True
    logger.ex(str(self._config))
```

</details>

### 🅼 config

```python
@property
def config(self) -> ConfigDict:
    return self._original_config
```
### 🅼 update

```python
def update(self, cfg: LazyConfig) -> None:
```
### 🅼 build\_config\_hooks

<details>

<summary>build\_config\_hooks</summary>
```python
def build_config_hooks(self) -> None:
    hook_cfgs = self._config.pop(LazyConfig.hook_key, [])
    hooks = []
    if hook_cfgs:
        _, base = Registry.find(list(hook_cfgs.keys())[0])
        assert base is not None, hook_cfgs
        reg = Registry.get_registry(base)
        for name, params in hook_cfgs.items():
            hook: Hook = ConfigHookNode.from_str(reg[name], params)()
            if hook:
                hooks.append(hook)
            else:
                self._config[name] = InterNode.from_str(reg[name], params)
    self.hooks = ConfigHookManager(hooks)
```

</details>

### 🅼 \_\_getattr\_\_

<details>

<summary>\_\_getattr\_\_</summary>
```python
def __getattr__(self, __name: str) -> Any:
    if __name in self._config:
        if not hasattr(self, "hooks"):
            self.build_config_hooks()
        return self._config[__name]
    raise AttributeError(__name)
```

</details>

### 🅼 build\_all

<details>

<summary>build\_all</summary>
```python
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
```

</details>

### 🅼 dump

```python
def dump(self, dump_path: str) -> None:
```
### 🅼 \_\_str\_\_

```python
def __str__(self) -> str:
    return str(self._config)
```
