---
title: parse
---

## TOC

- **Functions:**
  - 🅵 [\_dict2node](#🅵-_dict2node)
  - 🅵 [\_parse\_param\_name](#🅵-_parse_param_name)
  - 🅵 [\_flatten\_list](#🅵-_flatten_list)
  - 🅵 [set\_primary\_fields](#🅵-set_primary_fields)
- **Classes:**
  - 🅲 [ConfigDict](#🅲-configdict) - A specialized dictionary used for parsing and managing configuration data.

## Functions

## 🅵 \_dict2node

```python
def _dict2node(
    module_type: SpecialFlag, base: str, _dict: dict
) -> dict[str, ModuleNode]:
```
## 🅵 \_parse\_param\_name

```python
def _parse_param_name(name: str) -> tuple[str, list[tuple[str, str]]]:
```
## 🅵 \_flatten\_list

```python
def _flatten_list(
    lis: Sequence[ConfigNode | list[ConfigNode]],
) -> Sequence[ConfigNode]:
```
## 🅵 set\_primary\_fields

```python
def set_primary_fields(cfg) -> None:
```

## Classes

## 🅲 ConfigDict

```python
class ConfigDict(dict):
    primary_fields: list = None
    primary_to_registry: dict[str, str] = None
    registered_fields: list = None
    all_fields: set[str] = None
    scratchpads_fields: set[str] = set()
    current_field: str | None = None
    reused_caches: dict[str, ReusedNode] = None
```

A specialized dictionary used for parsing and managing configuration data.

It extends the functionality of the standard Python dictionary to
    include methods for parsing configuration nodes,
    handling special parameters, and managing primary and registered fields.

Attributes
    primary\_fields: A list of primary field names.
    primary\_to\_registry: A dictionary mapping primary field names to
        their corresponding registries.
    registered\_fields: A list of registered field names.
    all\_fields: A set containing all field names.
    scratchpads\_fields: A set containing scratchpad field names.
    current\_field: The current field being processed \(can be None\).
    reused\_caches: A dictionary for caching reused nodes.


### 🅼 \_\_new\_\_

```python
def __new__(cls) -> Self:
```
### 🅼 set\_primary\_fields

```python
@classmethod
def set_primary_fields(
    cls, primary_fields: Sequence[str], primary_to_registry: dict[str, str]
) -> None:
```

Sets the \`primary\_fields\` attribute to the specified list of module names,

and \`registered\_fields\` attributes based on the current state
    of the \`Registry\` object.

Note that \`set\_primary\_fields\` must be called before \`config.load\`.
### 🅼 parse

```python
def parse(self) -> None:
```

Parsing config into some \`ModuleNode\`s, the procedures are as following:

1. Convert config nodes in \`primary\_fields\` to \`ModuleNode\` at first,
        the field will be regarded as a set of nodes, e.g. \`self\[Model\]\`
        consists of two models.

        i. If the field is registered, the base registry is set to field;
        ii. If not, search \`Registry\` to get the base registry of each node.

    2. Convert isolated objects to \`ModuleNode\`;

        i. If the field is registered, search \`Registry\` to get the base registry
            of each node. Raising error if it cannot find;
        ii. If not, regard the field as a single node, and search \`Registry\`.
        iii. If search fail, regard the field as a scratchpads.

    3. Parse all the \`ModuleNode\` to target type of Node, e.g. \`ReusedNode\` and \`ClassNode\`.

        Visit the top level of config dict:
        i. If the name is in \`primary\_fields\` or \`scratchpads\_fields\`, parse each node of
            field;
        ii. Else if the node is instance of \`ModuleNode\`, parse it to target node.

    4. Wrap all the nodes of \`primary\_fields\` into ModuleWrapper.

    5. Clean some remain non-primary nodes. Only keep the primary nodes.

In the 3rd step, it will parse every parameter of each module node

    if its name has a special prefix, e.g. \`\!\`, \`@\` or \`$\`.
    The special parameter should be a string, a list of string or a dict of string.
    They will be parsed to target module nodes in given format\(alone, list or dict\).

According to given string parameters, e.g. \`\['ResNet', 'SegHead'\]\`,

    1. It will firstly search from the top level of config.
    2. If it dose not exist, it will search from \`primary\_fields\`,
        \`scratchpads\_fields\` and \`registered\_fields\`.
    3. If it still dose not exist, it will be regraded as a implicit module,
        which must have non-required parameters.

For the first two situations, the node will be convert to target type of node,
    then it will be set back to config for cache according to the priority.
For the last situation, it will only be set back when target module type is \`ReusedNode\`.
    But if the target module type is \`ClassNode\`, it will not be set back.

NOTE: Set converted nodes back to config is necceary for \`ReusedNode\`.

NOTE: use \`export EXCORE\_DEBUG=1\` to enable excore debug to
    get more information when parsing.
### 🅼 \_wrap

```python
def _wrap(self) -> None:
```
### 🅼 \_clean

```python
def _clean(self) -> None:
```
### 🅼 primary\_keys

```python
def primary_keys(self) -> Generator[str, None, None]:
```
### 🅼 non\_primary\_keys

```python
def non_primary_keys(self) -> Generator[str, None, None]:
```
### 🅼 \_parse\_primary\_modules

```python
def _parse_primary_modules(self) -> None:
```
### 🅼 \_parse\_isolated\_registered\_module

```python
def _parse_isolated_registered_module(self, name: str) -> None:
```
### 🅼 \_parse\_implicit\_module

```python
def _parse_implicit_module(
    self, name: str, module_type: NodeType
) -> ModuleNode:
```
### 🅼 \_parse\_isolated\_module

```python
def _parse_isolated_module(self, name: str) -> bool:
```
### 🅼 \_parse\_scratchpads

```python
def _parse_scratchpads(self, name: str) -> None:
```
### 🅼 \_parse\_isolated\_obj

```python
def _parse_isolated_obj(self) -> None:
```
### 🅼 \_contain\_module

```python
def _contain_module(self, name: str) -> bool:
```
### 🅼 \_parse\_env\_var

```python
def _parse_env_var(self, value: str) -> str:
```
### 🅼 \_get\_name\_and\_field

```python
def _get_name_and_field(
    self, name: str, ori_name: str | None = None
) -> tuple[str, str | None] | tuple[list[str], str]:
```
### 🅼 \_apply\_hooks

```python
def _apply_hooks(
    self, node: ConfigNode, hooks: list[tuple[str, str]]
) -> ConfigNode:
```
### 🅼 \_convert\_node

```python
def _convert_node(
    self,
    name: str,
    source: ConfigDict,
    target_type: NodeType,
    node_params: NodeParams | None = None,
) -> tuple[ModuleNode, NodeType]:
```
### 🅼 \_get\_node\_from\_name\_and\_field

```python
def _get_node_from_name_and_field(
    self,
    name: str,
    field: str | None,
    target_type: NodeType,
    node_params: NodeParams | None = None,
) -> tuple[ModuleNode, NodeType | None]:
```
### 🅼 \_parse\_single\_param

```python
def _parse_single_param(
    self,
    name: str,
    ori_name: str,
    field: str | None,
    target_type: NodeType,
    hooks: list[tuple[str, str]],
) -> ConfigNode:
```
### 🅼 \_parse\_params

```python
def _parse_params(
    self, ori_name: str, module_type: SpecialFlag
) -> ConfigNode | list[ConfigNode]:
```
### 🅼 \_parse\_module

```python
def _parse_module(self, node: ModuleNode) -> None:
```
### 🅼 \_parse\_inter\_modules

```python
def _parse_inter_modules(self) -> None:
```
### 🅼 \_\_str\_\_

```python
def __str__(self) -> str:
```
### 🅼 \_flatten

```python
def _flatten(self, _dict: dict, k: str, v: dict) -> None:
```
### 🅼 dump

```python
def dump(self, path: str) -> None:
```
