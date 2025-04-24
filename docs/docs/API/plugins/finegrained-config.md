---
title: finegrained_config
---

## TOC

- **Attributes:**
  - 🅰 [ArgType](#🅰-argtype)
- **Functions:**
  - 🅵 [\_get\_info\_dict](#🅵-_get_info_dict) - Retrieve configuration dictionary based on index.
  - 🅵 [\_check\_info](#🅵-_check_info) - Validate configuration info dictionary.
  - 🅵 [\_get\_rcv\_snd](#🅵-_get_rcv_snd) - Retrieve receive and send parameter configurations for a module.
  - 🅵 [\_to\_list](#🅵-_to_list)
  - 🅵 [\_construct\_kwargs](#🅵-_construct_kwargs) - Construct keyword arguments for module initialization.
  - 🅵 [enable\_finegrained\_config](#🅵-enable_finegrained_config) - Enable fine-grained configuration functionality.
- **Classes:**
  - 🅲 [FinegrainedConfig](#🅲-finegrainedconfig) - Fine-grained configuration hook for handling parameter passing and hierarchical config.

## Attributes

## 🅰 ArgType

```python
ArgType = Union[int, float, bool, str, list, dict]
```


## Functions

## 🅵 \_get\_info\_dict

```python
def _get_info_dict(index: str, config: ConfigDict) -> dict | None:
```

Retrieve configuration dictionary based on index.

This function checks if the index starts with "$", indicating a hierarchical path.
If so, it splits the index and traverses the configuration dictionary accordingly.
If the index does not start with "$", it directly attempts to retrieve the value
from the configuration dictionary.

**Parameters:**

- **index** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): The index key to retrieve the configuration.
- **config** ([ConfigDict](../config/parse#🅲-configdict)): The configuration dictionary to search within.

**Returns:**

- **[dict](https://docs.python.org/3/library/stdtypes.html#mapping-types-dict) | None**: The retrieved configuration dictionary or None if not found.

**Raises:**

- **[CoreConfigParseError](../-exceptions#🅲-coreconfigparseerror)**: If the indexed configuration path does not exist.

**Examples:**

```python
>>> config = {"a": {"b": {"c": 42}}}  # Loaded toml config
>>> _get_info_dict("$a::b::c", config)
42
```
## 🅵 \_check\_info

```python
def _check_info(info: dict) -> None:
```

Validate configuration info dictionary.

This function checks if the info dictionary contains all the expected keys:
"$class\_mapping", "info", and "args". If any of these keys are missing, it raises
a CoreConfigParseError with an appropriate error message.

**Parameters:**

- **info** ([dict](https://docs.python.org/3/library/stdtypes.html#mapping-types-dict)): The configuration info dictionary to validate.

**Raises:**

- **[CoreConfigParseError](../-exceptions#🅲-coreconfigparseerror)**: If any of the expected keys are missing from the info dictionary.
## 🅵 \_get\_rcv\_snd

```python
def _get_rcv_snd(module: type) -> list[str | list[str]]:
```

Retrieve receive and send parameter configurations for a module.

**Parameters:**

- **module** ([type](https://docs.python.org/3/library/functions.html#type)): The module class to get configurations for.

**Returns:**

- **list[str | list[str]]**: A list containing receive and send parameters \[receive, send\].

**Raises:**

- **[CoreConfigParseError](../-exceptions#🅲-coreconfigparseerror)**: If required configuration fields are missing in the registry.
## 🅵 \_to\_list

```python
def _to_list(item: str | list[str]) -> list[str]:
```
## 🅵 \_construct\_kwargs

```python
def _construct_kwargs(
    by_args: list[ArgType],
    args: list[ArgType],
    param_names: list[str],
    receive: list[str],
) -> dict[str, ArgType]:
```

Construct keyword arguments for module initialization.

**Parameters:**

- **passby_args** (list[ArgType]): List of arguments passed from the previous layer.
- **args** (list[ArgType]): List of arguments for the current layer.
- **param_names** (list[str]): List of parameter names.
- **receive** (list[str]): List of parameter names to receive.

**Returns:**

- **dict[str, ArgType]**: Dictionary of constructed keyword arguments.

**Raises:**

- **[RuntimeError](https://docs.python.org/3/library/exceptions.html#RuntimeError)**: If the length of \`args\` exceeds the length of \`param\_names\` that are not in \`receive\`.
## 🅵 enable\_finegrained\_config

```python
def enable_finegrained_config(
    hook_flag: str = "*",
    rcv_key: str = "receive",
    snd_key: str = "send",
    force: bool = False,
) -> None:
```

Enable fine-grained configuration functionality.

This function registers FinegrainedConfig as a global argument hook and sets the
receive and send key names for the configuration. It also allows for specifying
a hook flag and enabling force registration.

**Parameters:**

- **hook_flag** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)) (default to `'*'`): The hook flag to use for registration. Defaults to '\*'.
- **rcv_key** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)) (default to `"receive"`): Key name for receiving parameters. Defaults to "receive".
- **snd_key** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)) (default to `"send"`): Key name for sending parameters. Defaults to "send".
- **force** ([bool](https://docs.python.org/3/library/stdtypes.html#boolean-values)) (default to `False`): Whether to force the registration of the hook. Defaults to False.

**Examples:**

```python
>>> from excore.plugins.finegrained_config import enable_finegrained_config
>>> enable_finegrained_config()
```

:::note
This function registers `FinegrainedConfig` as a global argument hook.

:::

## Classes

## 🅲 FinegrainedConfig

```python
class FinegrainedConfig(ConfigArgumentHook):
```

Fine-grained configuration hook for handling parameter passing and hierarchical config.

This class implements a configuration system that allows parameter passing between modules
and supports hierarchical module construction.

More details can be found in the documentation of the \`ConfigArgumentHook\` class.

**Parameters:**

- **node** ([ModuleNode](../config/models#🅲-modulenode)): Module node object.
- **class_mapping** (list[type]): List of class mappings.
- **info** (list[list[int]]): List of module configuration information.
Each element should contain the number and module index in class\_mapping.
- **args** (list[list[ArgType]]): List of module arguments.
- **unpack** ([bool](https://docs.python.org/3/library/stdtypes.html#boolean-values)): Whether to unpack the layers list when calling container.
Defaults to False. If True, layers will be passed as \*layers, otherwise as a list.
- **enabled** ([bool](https://docs.python.org/3/library/stdtypes.html#boolean-values)) (default to `True`): Whether to enable this hook. Defaults to True.

**Attributes:**

- **rcv_key** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): Key name for receiving parameters.
- **snd_key** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): Key name for sending parameters.

**Examples:**

```python
>>> # Example can be found in `example/finegrained.py`.
```


### 🅼 \_\_init\_\_

```python
def __init__(
    self,
    node: ModuleNode,
    class_mapping: list[type],
    info: list[list[int]],
    args: list[list[ArgType]],
    unpack: bool = False,
    enabled: bool = True,
) -> None:
```

Initialize the fine-grained configuration hook.
### 🅼 hook

```python
def hook(self, **kwargs: Any) -> Any:
```

Execute the configuration hook logic.

This method builds the module hierarchy according to the configuration info
and handles parameter passing between modules. It checks the compatibility
of passby arguments with receive parameters and ensures that the lengths
of receive and send parameters match between consecutive modules. It then
constructs the keyword arguments for module initialization, creates the
module instances, and returns the built module container.

**Parameters:**

- ****kwargs**: Additional keyword arguments.

**Returns:**

- **[Any](https://docs.python.org/3/library/typing.html#typing.Any)**: Built module container.

**Raises:**

- **[RuntimeError](https://docs.python.org/3/library/exceptions.html#RuntimeError)**: When parameter passing is incompatible.
### 🅼 \_\_excore\_prepare\_\_

```python
def __excore_prepare__(
    cls, node: ConfigNode, hook_info: str, config: ConfigDict
) -> ConfigNode:
```

Prepare the configuration node.

**Parameters:**

- **node** ([ConfigNode](../config/models#🅰-confignode)): Configuration node.
- **hook_info** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): Hook information string.
- **config** ([ConfigDict](../config/parse#🅲-configdict)): Configuration dictionary.

**Returns:**

- **[ConfigNode](../config/models#🅰-confignode)**: Processed configuration node.

**Raises:**

- **[CoreConfigParseError](../-exceptions#🅲-coreconfigparseerror)**: When no hook\_info is found.
