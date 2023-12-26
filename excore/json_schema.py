import inspect
import json
import os
from inspect import Parameter, _empty
from typing import Dict, List, Optional, _GenericAlias

from ._constants import _cache_dir, _json_schema_file
from .config import _str_to_target
from .registry import Registry, load_registries

__all__ = ["generate_json_shcema", "json_schema_path"]

TYPE_MAPPER = {
    int: "integer",
    str: "string",
    float: "number",
    list: "array",
    tuple: "array",
    dict: "object",
}

SPECIAL_KEYS = {"kwargs": "object", "args": "array"}


def get_type(t):
    potential_type = TYPE_MAPPER.get(t, None)
    if potential_type is None:
        return "string"
    return potential_type


def init_json_schema(settings: Optional[Dict]) -> Dict:
    default_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://example.com/product.schema.json",
        "title": "ExCore",
        "description": "Uesd for ExCore config file completion",
        "type": "object",
        "properties": {},
    }
    default_schema.update(settings or {})
    assert len(default_schema) == 6
    return default_schema


# TODO(Asthestarsfalll): Add workspace config file to define fields
def generate_json_shcema(
    fields: Dict,
    save_path: Optional[str] = None,
    schema_settings: Optional[Dict] = None,
    isolated_fields: Optional[List[str]] = None,
) -> None:
    load_registries()
    schema = init_json_schema(schema_settings)
    isolated_fields = isolated_fields or []
    for name, reg in Registry._registry_pool.items():
        target_fields = fields.get(name, name)
        if isinstance(target_fields, str):
            target_fields = [target_fields]
        elif not isinstance(target_fields, (list, tuple)):
            raise TypeError("Unexpected type of elements of fields")
        props = parse_registry(reg)
        for f in target_fields:
            schema["properties"][f] = props
        # Is this too heavey?
        if name in isolated_fields:
            for name, v in props["properties"].items():
                schema["properties"][name] = v
    json_str = json.dumps(schema, indent=2)
    save_path = save_path or json_schema_path()
    with open(save_path, "w", encoding="UTF-8") as f:
        f.write(json_str)


def parse_registry(reg: Registry):
    props = {
        "type": "object",
        "properties": {},
    }
    for name, item_dir in reg.items():
        cls_or_func = _str_to_target(item_dir)
        doc_string = cls_or_func.__doc__
        params = inspect.signature(cls_or_func).parameters
        param_props = {"type": "object", "properties": {}}
        if doc_string:
            # TODO(Asthestarsfalll): parse doc string to each parameters
            param_props["description"] = doc_string
        items = {}
        required = []
        for param_name, param_obj in params.items():
            is_required, item = parse_single_param(param_obj)
            items[param_name] = item
            if is_required:
                required.append(param_name)
        if items:
            param_props["properties"] = items
        if required:
            param_props["required"] = required
        props["properties"][name] = param_props
    return props


def parse_single_param(p: Parameter):
    required = True
    prop = {}
    anno = p.annotation
    potential_type = None
    if isinstance(anno, _GenericAlias):
        potential_type = "array"
        # Do not support like `List[ResNet]`.
        prop["items"] = {"type": get_type(anno.__args__[0])}
    elif anno is not _empty:
        potential_type = get_type(anno)
    # determine type by default value
    elif p.default is not _empty:
        potential_type = get_type(type(p.default))
        required = False
    if p.name in SPECIAL_KEYS:
        potential_type = SPECIAL_KEYS[p.name]
    # Default to integer
    prop["type"] = potential_type if potential_type else "integer"
    return required, prop


def json_schema_path():
    return os.path.join(_cache_dir, _json_schema_file)