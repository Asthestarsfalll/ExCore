from __future__ import annotations

import inspect
import json
import sys
from collections.abc import Sequence
from inspect import Parameter, _empty, _ParameterKind, isclass
from types import ModuleType
from typing import TYPE_CHECKING, Any, Callable, Dict, Union, get_args, get_origin

import toml

from excore import workspace

from .._exceptions import AnnotationsFutureError
from ..engine.logging import logger
from ..engine.registry import Registry, load_registries
from .models import ConfigArgumentHook, _str_to_target

if sys.version_info >= (3, 10, 0):
    from types import NoneType, UnionType  # type: ignore
else:
    NoneType = type(None)  # type: ignore

    # just a placeholder
    class UnionType:  # type: ignore
        pass


if TYPE_CHECKING:
    from typing import TypedDict

    from typing_extensions import NotRequired

    class Property(TypedDict):
        properties: NotRequired[Property]
        type: NotRequired[str]
        items: NotRequired[dict]
        value: NotRequired[str]
        description: NotRequired[str]
        required: NotRequired[list[str]]


TYPE_MAPPER: dict[type, str] = {
    int: "number",  # sometimes default value are not accurate
    str: "string",
    float: "number",
    list: "array",
    tuple: "array",
    dict: "object",
    Dict: "object",
    bool: "boolean",
}


def _init_json_schema(settings: dict | None) -> dict[str, Any]:
    """
    Initialize JSON schema for ExCore configuration.

    This function creates a default JSON schema dictionary with title,
    description, type, and properties. It then updates this schema with
    any provided settings. Finally, it asserts that the schema contains
    exactly four keys and returns the schema.

    Args:
        settings (dict | None): Optional settings to update the default schema.

    Returns:
        dict[str, Any]: The initialized JSON schema with default values.
    """
    default_schema = {
        "title": "ExCore",
        "description": "Used for ExCore config file completion",
        "type": "object",
        "properties": {},
    }
    default_schema.update(settings or {})
    assert len(default_schema) == 4
    return default_schema


def _generate_json_schema_and_class_mapping(
    fields: dict,
    save_path: str | None = None,
    class_mapping_save_path: str | None = None,
    schema_settings: dict | None = None,
) -> None:
    """
    Generate JSON schema and class mapping for ExCore configuration.

    This function loads the registries, initializes the JSON schema, and iterates
    through the registry items to parse and populate the schema and class mapping.
    It then writes the schema and class mapping to the specified paths and logs
    success messages.

    Args:
        fields (dict): A dictionary containing fields and their corresponding
                    primary fields or names.
        save_path (str | None): Optional path to save the generated JSON schema.
                                Defaults to workspace.json_schema_file.
        class_mapping_save_path (str | None): Optional path to save the class mapping.
                                            Defaults to workspace.class_mapping_file.
        schema_settings (dict | None): Optional settings to update the JSON schema.
    """
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
        # Is this too heavey?
        if name in isolated_fields:
            for name, v in props["properties"].items():
                schema["properties"][name] = v
    json_str = json.dumps(schema, indent=2)
    save_path = save_path or workspace.json_schema_file
    class_mapping_save_path = class_mapping_save_path or workspace.class_mapping_file
    with open(save_path, "w", encoding="UTF-8") as f:
        f.write(json_str)
    logger.success("json schema has been written to {}", save_path)
    with open(class_mapping_save_path, "w", encoding="UTF-8") as f:
        f.write(json.dumps(class_mapping))
    logger.success("class mapping has been written to {}", class_mapping_save_path)


def _check(bases) -> bool:
    for b in bases:
        if b is object:
            return False
        if callable(b):
            return True
    return False


def parse_registry(reg: Registry) -> tuple[Property, dict[str, list[str | int]]]:
    """
    Parse registry items to generate JSON schema properties and class mapping.

    This function iterates through the registry items, extracts relevant information
    such as function signatures, docstrings, and source file locations, and constructs
    a JSON schema property dictionary and a class mapping dictionary. It handles
    exceptions and logs errors appropriately.

    Args:
        reg (Registry): The registry containing items to be parsed.

    Returns:
        tuple[Property, dict[str, list[str | int]]]: A tuple containing the generated
            JSON schema properties and class mapping.
    """
    props: Property = {
        "type": "object",
        "properties": {},
    }
    class_mapping: dict[str, list[str | int]] = {}
    for name, item_dir in reg.items():
        func = _str_to_target(item_dir)  # type: ignore
        if isinstance(func, ModuleType):
            continue
        class_mapping[name] = [inspect.getfile(func), inspect.getsourcelines(func)[1]]
        doc_string = func.__doc__
        is_hook = isclass(func) and issubclass(func, ConfigArgumentHook)
        if isclass(func) and _check(func.__bases__):
            func = func.__init__
        params = inspect.signature(func).parameters  # type: ignore
        param_props = {"type": "object", "properties": {}}
        if doc_string:
            # TODO: parse doc string to each parameters
            param_props["description"] = doc_string
        items = {}
        required = []
        for param_name, param_obj in params.items():
            if param_name == "self" or (is_hook and param_name == "node"):
                continue
            try:
                is_required, item = parse_single_param(param_obj)
            except Exception as e:
                from rich.console import Console

                Console().print_exception()
                if isinstance(e, AnnotationsFutureError):
                    logger.error(
                        f"Skip {name} due to mismatch of python version and annotations future."
                    )
                    break
                logger.error(f"Skip parameter {param_obj.name} of {name}")
                continue
            items[param_name] = item
            if is_required:
                required.append(param_name)
        if items:
            param_props["properties"] = items
        if required:
            param_props["required"] = required
        props["properties"][name] = param_props  # type: ignore
    return props, class_mapping


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


def _parse_inner_types(prop: Property, inner_types: Sequence[type]) -> None:
    first_type = inner_types[0]
    is_all_the_same = True
    for t in inner_types:
        is_all_the_same &= t == first_type
    if is_all_the_same and first_type in TYPE_MAPPER:
        prop["items"] = {"type": TYPE_MAPPER.get(first_type)}


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


def _try_cast(anno) -> type | Any:
    try:
        return eval(anno)
    except Exception:
        return anno


def parse_single_param(param: Parameter) -> tuple[bool, Property]:
    """
    Parse a single parameter to generate JSON schema property.

    This function handles various cases such as optional types, default values, and
    variable positional/keyword arguments. It determines the type of the parameter
    and constructs a corresponding JSON schema property dictionary. If the parameter
    is required or has a specific type, it updates the property dictionary
    accordingly.

    Args:
        param (inspect.Parameter): The parameter to be parsed.

    Returns:
        tuple[bool, Property]: A tuple containing a boolean indicating if the parameter
            is required and a dictionary representing the JSON schema property.
    """
    prop: Property = {}
    anno = param.annotation
    potential_type = None

    anno = _remove_optional(anno)
    anno = _try_cast(anno)

    #  hardcore for torch.optim
    if param.default.__class__.__name__ == "_RequiredParameter":
        param._default = _empty  # type: ignore

    if isinstance(anno, str):
        raise AnnotationsFutureError(
            "Use a higher version of python, e.g. 3.10, "
            "and remove `from __future__ import annotations`."
        )
    elif anno is not _empty:
        potential_type = _parse_typehint(prop, anno)
    # determine type by default value
    elif param.default is not _empty and param.default is not None:
        # TODO: Allow user to add more type mapper.
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


def _generate_taplo_config() -> None:
    cfg = dict(
        schema=dict(
            path=workspace.json_schema_file,
            enabled=True,
        ),
        formatting=dict(align_entries=False),
    )
    with open("./.taplo.toml", "w", encoding="UTF-8") as f:
        toml.dump(cfg, f)
