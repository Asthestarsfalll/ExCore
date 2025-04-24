---
title: _json_schema
---

## TOC

- **Attributes:**
  - 🅰 [TYPE\_MAPPER](#🅰-type_mapper) - sometimes default value are not accurate
- **Functions:**
  - 🅵 [\_init\_json\_schema](#🅵-_init_json_schema) - Initialize JSON schema for ExCore configuration.
  - 🅵 [\_generate\_json\_schema\_and\_class\_mapping](#🅵-_generate_json_schema_and_class_mapping) - Generate JSON schema and class mapping for ExCore configuration.
  - 🅵 [\_check](#🅵-_check)
  - 🅵 [parse\_registry](#🅵-parse_registry) - Parse registry items to generate JSON schema properties and class mapping.
  - 🅵 [\_remove\_optional](#🅵-_remove_optional)
  - 🅵 [\_parse\_inner\_types](#🅵-_parse_inner_types)
  - 🅵 [\_parse\_typehint](#🅵-_parse_typehint)
  - 🅵 [\_try\_cast](#🅵-_try_cast)
  - 🅵 [parse\_single\_param](#🅵-parse_single_param) - Parse a single parameter to generate JSON schema property.
  - 🅵 [\_generate\_taplo\_config](#🅵-_generate_taplo_config)

## Attributes

## 🅰 TYPE\_MAPPER

```python
TYPE_MAPPER: dict[type, str] = {
    int: "number",
    str: "string",
    float: "number",
    list: "array",
    tuple: "array",
    dict: "object",
    Dict: "object",
    bool: "boolean",
} #sometimes default value are not accurate
```


## Functions

## 🅵 \_init\_json\_schema

```python
def _init_json_schema(settings: dict | None) -> dict[str, Any]:
```

Initialize JSON schema for ExCore configuration.

This function creates a default JSON schema dictionary with title,
description, type, and properties. It then updates this schema with
any provided settings. Finally, it asserts that the schema contains
exactly four keys and returns the schema.

**Parameters:**

- **settings** ([dict](https://docs.python.org/3/library/stdtypes.html#mapping-types-dict) | None): Optional settings to update the default schema.

**Returns:**

- **dict[str, Any]**: The initialized JSON schema with default values.
## 🅵 \_generate\_json\_schema\_and\_class\_mapping

```python
def _generate_json_schema_and_class_mapping(
    fields: dict,
    save_path: str | None = None,
    class_mapping_save_path: str | None = None,
    schema_settings: dict | None = None,
) -> None:
```

Generate JSON schema and class mapping for ExCore configuration.

This function loads the registries, initializes the JSON schema, and iterates
through the registry items to parse and populate the schema and class mapping.
It then writes the schema and class mapping to the specified paths and logs
success messages.

**Parameters:**

- **fields** ([dict](https://docs.python.org/3/library/stdtypes.html#mapping-types-dict)): A dictionary containing fields and their corresponding
primary fields or names.
- **save_path** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str) | None): Optional path to save the generated JSON schema.
Defaults to workspace.json\_schema\_file.
- **class_mapping_save_path** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str) | None): Optional path to save the class mapping.
Defaults to workspace.class\_mapping\_file.
- **schema_settings** ([dict](https://docs.python.org/3/library/stdtypes.html#mapping-types-dict) | None): Optional settings to update the JSON schema.
## 🅵 \_check

```python
def _check(bases) -> bool:
```
## 🅵 parse\_registry

```python
def parse_registry(
    reg: Registry,
) -> tuple[Property, dict[str, list[str | int]]]:
```

Parse registry items to generate JSON schema properties and class mapping.

This function iterates through the registry items, extracts relevant information
such as function signatures, docstrings, and source file locations, and constructs
a JSON schema property dictionary and a class mapping dictionary. It handles
exceptions and logs errors appropriately.

**Parameters:**

- **reg** ([Registry](../engine/registry#🅲-registry)): The registry containing items to be parsed.

**Returns:**

- **tuple[Property, dict[str, list[str | int]]]**: A tuple containing the generated
JSON schema properties and class mapping.
## 🅵 \_remove\_optional

```python
def _remove_optional(anno):
```
## 🅵 \_parse\_inner\_types

```python
def _parse_inner_types(prop: Property, inner_types: Sequence[type]) -> None:
```
## 🅵 \_parse\_typehint

```python
def _parse_typehint(prop: Property, anno: type) -> str | None:
```
## 🅵 \_try\_cast

```python
def _try_cast(anno) -> type | Any:
```
## 🅵 parse\_single\_param

```python
def parse_single_param(param: Parameter) -> tuple[bool, Property]:
```

Parse a single parameter to generate JSON schema property.

This function handles various cases such as optional types, default values, and
variable positional/keyword arguments. It determines the type of the parameter
and constructs a corresponding JSON schema property dictionary. If the parameter
is required or has a specific type, it updates the property dictionary
accordingly.

**Parameters:**

- **param** (Parameter): The parameter to be parsed.

**Returns:**

- **tuple[bool, Property]**: A tuple containing a boolean indicating if the parameter
is required and a dictionary representing the JSON schema property.
## 🅵 \_generate\_taplo\_config

```python
def _generate_taplo_config() -> None:
```
