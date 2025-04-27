---
title: _json_schema
sidebar_position: 3
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
- **Classes:**
  - 🅲 [Property](#🅲-property)

## Attributes

## 🅰 TYPE\_MAPPER

<details>

<summary>TYPE\_MAPPER</summary>
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

</details>



## Functions

## 🅵 \_init\_json\_schema

<details>

<summary>\_init\_json\_schema</summary>
```python
def _init_json_schema(settings: dict | None) -> dict[str, Any]:
    default_schema = {
        "title": "ExCore",
        "description": "Used for ExCore config file completion",
        "type": "object",
        "properties": {},
    }
    default_schema.update(settings or {})
    assert len(default_schema) == 4
    return default_schema
```

</details>


Initialize JSON schema for ExCore configuration.

This function creates a default JSON schema dictionary with title,
description, type, and properties. It then updates this schema with
any provided settings. Finally, it asserts that the schema contains
exactly four keys and returns the schema.

**Parameters:**

- **settings** ([dict](https://docs.python.org/3/library/stdtypes.html#mapping-types-dict) | [None](https://docs.python.org/3/library/constants.html#None)): Optional settings to update the default schema.

**Returns:**

- **[dict](https://docs.python.org/3/library/stdtypes.html#mapping-types-dict)[[str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str), [Any](https://docs.python.org/3/library/typing.html#typing.Any)]**: The initialized JSON schema with default values.
## 🅵 \_generate\_json\_schema\_and\_class\_mapping

<details>

<summary>\_generate\_json\_schema\_and\_class\_mapping</summary>
```python
def _generate_json_schema_and_class_mapping(
    fields: dict,
    save_path: str | None = None,
    class_mapping_save_path: str | None = None,
    schema_settings: dict | None = None,
) -> None:
    load_registries()
    schema = _init_json_schema(schema_settings)
    class_mapping = {}
    isolated_fields = fields.pop("isolated_fields", [])
    for name, reg in Registry._registry_pool.items():
        primary_fields = fields.get(name, name)
        if isinstance(primary_fields, str):
            primary_fields = [primary_fields]
        elif not isinstance(primary_fields, (list, tuple)):
            raise TypeError("Unexpected type of elements of fields")
        props, mapping = parse_registry(reg)
        class_mapping.update(mapping)
        for f in primary_fields:
            schema["properties"][f] = props
        if name in isolated_fields:
            for name, v in props["properties"].items():
                schema["properties"][name] = v
    json_str = json.dumps(schema, indent=2)
    save_path = save_path or workspace.json_schema_file
    class_mapping_save_path = (
        class_mapping_save_path or workspace.class_mapping_file
    )
    with open(save_path, "w", encoding="UTF-8") as f:
        f.write(json_str)
    logger.success("json schema has been written to {}", save_path)
    with open(class_mapping_save_path, "w", encoding="UTF-8") as f:
        f.write(json.dumps(class_mapping))
    logger.success(
        "class mapping has been written to {}", class_mapping_save_path
    )
```

</details>


Generate JSON schema and class mapping for ExCore configuration.

This function loads the registries, initializes the JSON schema, and iterates
through the registry items to parse and populate the schema and class mapping.
It then writes the schema and class mapping to the specified paths and logs
success messages.

**Parameters:**

- **fields** ([dict](https://docs.python.org/3/library/stdtypes.html#mapping-types-dict)): A dictionary containing fields and their corresponding
primary fields or names.
- **save_path** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str) | [None](https://docs.python.org/3/library/constants.html#None)): Optional path to save the generated JSON schema.
Defaults to workspace.json\_schema\_file.
- **class_mapping_save_path** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str) | [None](https://docs.python.org/3/library/constants.html#None)): Optional path to save the class mapping.
Defaults to workspace.class\_mapping\_file.
- **schema_settings** ([dict](https://docs.python.org/3/library/stdtypes.html#mapping-types-dict) | [None](https://docs.python.org/3/library/constants.html#None)): Optional settings to update the JSON schema.
## 🅵 \_check

<details>

<summary>\_check</summary>
```python
def _check(bases) -> bool:
    for b in bases:
        if b is object:
            return False
        if callable(b):
            return True
    return False
```

</details>

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

- **[tuple](https://docs.python.org/3/library/stdtypes.html#tuples)[[Property](-json-schema#🅲-property), [dict](https://docs.python.org/3/library/stdtypes.html#mapping-types-dict)[[str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)], [list](https://docs.python.org/3/library/stdtypes.html#lists)[[str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)] | [int](https://docs.python.org/3/library/stdtypes.html#numeric-types-int-float-complex)]**: A tuple containing the generated
JSON schema properties and class mapping.
## 🅵 \_remove\_optional

<details>

<summary>\_remove\_optional</summary>
```python
def _remove_optional(anno):
    origin = get_origin(anno)
    if origin is not Union:
        return anno
    inner_types = get_args(anno)
    if len(inner_types) != 2:
        return anno
    filter_types = [i for i in inner_types if i is not NoneType]
    if len(filter_types) == 1:
        return _remove_optional(filter_types[0])
    return anno
```

</details>

## 🅵 \_parse\_inner\_types

<details>

<summary>\_parse\_inner\_types</summary>
```python
def _parse_inner_types(prop: Property, inner_types: Sequence[type]) -> None:
    first_type = inner_types[0]
    is_all_the_same = True
    for t in inner_types:
        is_all_the_same &= t == first_type
    if is_all_the_same and first_type in TYPE_MAPPER:
        prop["items"] = {"type": TYPE_MAPPER.get(first_type)}
```

</details>

## 🅵 \_parse\_typehint

<details>

<summary>\_parse\_typehint</summary>
```python
def _parse_typehint(prop: Property, anno: type) -> str | None:
    potential_type = TYPE_MAPPER.get(anno)
    if potential_type is not None:
        return potential_type
    origin = get_origin(anno)
    if anno is Callable:
        return "string"
    inner_types = get_args(anno)
    if origin in (Sequence, list, tuple):
        potential_type = "array"
        _parse_inner_types(prop, inner_types)
    elif origin in (Union, UnionType) and len(inner_types) == 2:
        filter_types = [i for i in inner_types if i is not NoneType]
        if len(filter_types) == 1:
            return _parse_typehint(prop, filter_types[0])
        return None
    elif origin in (Union, UnionType):
        return None
    return potential_type or "string"
```

</details>

## 🅵 \_try\_cast

```python
def _try_cast(anno) -> type | Any:
    try:
        return eval(anno)
    except Exception:
        return anno
```
## 🅵 parse\_single\_param

<details>

<summary>parse\_single\_param</summary>
```python
def parse_single_param(param: Parameter) -> tuple[bool, Property]:
    prop: Property = {}
    anno = param.annotation
    potential_type = None
    anno = _remove_optional(anno)
    anno = _try_cast(anno)
    if param.default.__class__.__name__ == "_RequiredParameter":
        param._default = _empty
    if isinstance(anno, str):
        raise AnnotationsFutureError(
            "Use a higher version of python, e.g. 3.10, and remove `from __future__ import annotations`."
        )
    elif anno is not _empty:
        potential_type = _parse_typehint(prop, anno)
    elif param.default is not _empty and param.default is not None:
        potential_type = TYPE_MAPPER.get(type(param.default), "number")
        if isinstance(param.default, (list, tuple)):
            types = [type(t) for t in param.default]
            _parse_inner_types(prop, types)
    elif param.kind is _ParameterKind.VAR_POSITIONAL:
        return False, {"type": "array"}
    elif param.kind is _ParameterKind.VAR_KEYWORD:
        return False, {"type": "object"}
    if anno is _empty and param.default is _empty:
        potential_type = "number"
    if potential_type:
        prop["type"] = potential_type
    return param.default is _empty, prop
```

</details>


Parse a single parameter to generate JSON schema property.

This function handles various cases such as optional types, default values, and
variable positional/keyword arguments. It determines the type of the parameter
and constructs a corresponding JSON schema property dictionary. If the parameter
is required or has a specific type, it updates the property dictionary
accordingly.

**Parameters:**

- **param** ([inspect.Parameter](https://docs.python.org/3/library/inspect.html#inspect.Parameter)): The parameter to be parsed.

**Returns:**

- **[tuple](https://docs.python.org/3/library/stdtypes.html#tuples)[[bool](https://docs.python.org/3/library/stdtypes.html#boolean-values), [Property](-json-schema#🅲-property)]**: A tuple containing a boolean indicating if the parameter
is required and a dictionary representing the JSON schema property.
## 🅵 \_generate\_taplo\_config

<details>

<summary>\_generate\_taplo\_config</summary>
```python
def _generate_taplo_config() -> None:
    cfg = dict(
        schema=dict(path=workspace.json_schema_file, enabled=True),
        formatting=dict(align_entries=False),
    )
    with open("./.taplo.toml", "w", encoding="UTF-8") as f:
        toml.dump(cfg, f)
```

</details>


## Classes

## 🅲 Property

<details>

<summary>Property</summary>
```python
class Property(TypedDict):
    properties: NotRequired[Property] = None
    type: NotRequired[str] = None
    items: NotRequired[dict] = None
    value: NotRequired[str] = None
    description: NotRequired[str] = None
    required: NotRequired[list[str]] = None
```

</details>
