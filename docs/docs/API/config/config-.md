---
title: config
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

```python
def load_config(filename: str, base_key: str = "__base__") -> ConfigDict:
```

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

```python
def _merge_config(base_cfg: ConfigDict, new_cfg: dict) -> None:
```
## 🅵 load

```python
def load(
    filename: str,
    dump_path: str | None = None,
    update_dict: dict[str, Any] | None = None,
    base_key: str = BASE_CONFIG_KEY,
    parse_config: bool = True,
) -> LazyConfig:
```

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
```

Build all modules from the given LazyConfig object.

**Parameters:**

- **cfg** ([LazyConfig](lazy-config#🅲-lazyconfig)): The LazyConfig object containing the configuration.

**Returns:**

- **[tuple](https://docs.python.org/3/library/stdtypes.html#tuples)**: A tuple containing a ModuleWrapper and a dictionary of additional data.
