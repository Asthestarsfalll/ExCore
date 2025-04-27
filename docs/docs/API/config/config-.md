---
title: config
sidebar_position: 3
---

## TOC

- **Attributes:**
  - 🅰 [BASE\_CONFIG\_KEY](#🅰-base_config_key)
- **Functions:**
  - 🅵 [load\_config](#🅵-load_config) - Load a configuration file and merge its base configurations.
  - 🅵 [\_merge\_config](#🅵-_merge_config)
  - 🅵 [load](#🅵-load) - Load a configuration file and optionally updates it with a dictionary,
  - 🅵 [build\_all](#🅵-build_all) - Build all modules from the given LazyConfig object.

## Attributes

## 🅰 BASE\_CONFIG\_KEY

```python
BASE_CONFIG_KEY = """__base__"""
```


## Functions

## 🅵 load\_config

<details>

<summary>load\_config</summary>
```python
def load_config(filename: str, base_key: str = "__base__") -> ConfigDict:
    logger.info(f"load_config {filename}")
    ext = os.path.splitext(filename)[-1]
    path = os.path.dirname(filename)
    if ext != ".toml":
        raise CoreConfigSupportError(
            f"Only support `toml` files for now, but got {filename}"
        )
    config = toml.load(filename, ConfigDict)
    base_cfgs = [
        load_config(os.path.join(path, i), base_key)
        for i in config.pop(base_key, [])
    ]
    base_cfg = ConfigDict()
    for c in base_cfgs:
        _merge_config(base_cfg, c)
    _merge_config(base_cfg, config)
    return base_cfg
```

</details>


Load a configuration file and merge its base configurations.

**Parameters:**

- **filename** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): The path to the TOML configuration file.
- **base_key** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): The key to identify base configurations.
Defaults to "\_\_base\_\_".

**Returns:**

- **[ConfigDict](parse#🅲-configdict)**: The merged configuration dictionary.

**Raises:**

- **[CoreConfigSupportError](../-exceptions#🅲-coreconfigsupporterror)**: If the file extension is not ".toml".
## 🅵 \_merge\_config

<details>

<summary>\_merge\_config</summary>
```python
def _merge_config(base_cfg: ConfigDict, new_cfg: dict) -> None:
    for k, v in new_cfg.items():
        if k in base_cfg and isinstance(v, dict):
            _merge_config(base_cfg[k], v)
        else:
            base_cfg[k] = v
```

</details>

## 🅵 load

<details>

<summary>load</summary>
```python
def load(
    filename: str,
    *,
    dump_path: str | None = None,
    update_dict: dict[str, Any] | None = None,
    base_key: str = BASE_CONFIG_KEY,
    parse_config: bool = True
) -> LazyConfig:
    st = time.time()
    load_registries()
    config = load_config(filename, base_key)
    if update_dict:
        _merge_config(config, update_dict)
    logger.success("Config loading cost {:.4f}s!", time.time() - st)
    if dump_path:
        config.dump(dump_path)
    logger.info("Loaded configs:")
    logger.info(config)
    lazy_config = LazyConfig(config)
    if parse_config:
        lazy_config.parse()
    return lazy_config
```

</details>


Load a configuration file and optionally updates it with a dictionary,

dumps it to a specified path.

**Parameters:**

- **filename** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): The path to the configuration file to load.
- **dump_path** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): The path to dump the loaded configuration.
Defaults to None.
- **update_dict** ([dict](https://docs.python.org/3/library/stdtypes.html#mapping-types-dict)): A dictionary with values to update in
the loaded configuration. Defaults to None.
- **base_key** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): The base key to use for loading the configuration.
Defaults to \`BASE\_CONFIG\_KEY\`.
- **parse_config** ([bool](https://docs.python.org/3/library/stdtypes.html#boolean-values)): Whether to parse the configuration immediately.
Defaults to True.

**Returns:**

- **[LazyConfig](lazy-config#🅲-lazyconfig)**: A LazyConfig object representing the loaded configuration.
## 🅵 build\_all

```python
def build_all(cfg: LazyConfig) -> tuple[ModuleWrapper, dict[str, Any]]:
    st = time.time()
    modules = cfg.build_all()
    logger.success("Modules building costs {:.4f}s!", time.time() - st)
    return modules
```

Build all modules from the given LazyConfig object.

**Parameters:**

- **cfg** ([LazyConfig](lazy-config#🅲-lazyconfig)): The LazyConfig object containing the configuration.

**Returns:**

- **[tuple](https://docs.python.org/3/library/stdtypes.html#tuples)**: A tuple containing a ModuleWrapper and a dictionary of additional data.
