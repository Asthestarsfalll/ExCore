import inspect
import json
import os
import os.path as osp
from collections.abc import Sequence
from inspect import Parameter, _empty, isclass
from types import ModuleType
from typing import Dict, Optional, Union, _GenericAlias

import toml

from .._constants import _cache_dir, _class_mapping_file, _json_schema_file
from ..engine.hook import ConfigArgumentHook
from ..engine.logging import logger
from ..engine.registry import Registry, load_registries
from .model import _str_to_target

NoneType = type(None)

TYPE_MAPPER = {
    int: "number",  # sometimes default value are not accurate
    str: "string",
    float: "number",
    list: "array",
    tuple: "array",
    dict: "object",
    bool: "boolean",
}

SPECIAL_KEYS = {"kwargs": "object", "args": "array"}


def _get_type(t):
    if isinstance(t, _GenericAlias):
        if isinstance(t.__args__[0], _GenericAlias):
            return None
        return TYPE_MAPPER.get(t, None)
    potential_type = TYPE_MAPPER.get(t, None)
    if potential_type is None:
        return "string"
    return potential_type


def _init_json_schema(settings: Optional[Dict]) -> Dict:
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


def _generate_json_schema_and_class_mapping(
    fields: Dict,
    save_path: Optional[str] = None,
    class_mapping_save_path: Optional[str] = None,
    schema_settings: Optional[Dict] = None,
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
        # Is this too heavey?
        if name in isolated_fields:
            for name, v in props["properties"].items():
                schema["properties"][name] = v
    json_str = json.dumps(schema, indent=2)
    save_path = save_path or _json_schema_path()
    class_mapping_save_path = class_mapping_save_path or _class_mapping_path()
    with open(save_path, "w", encoding="UTF-8") as f:
        f.write(json_str)
    logger.success("json schema has been written to {}", save_path)
    with open(class_mapping_save_path, "w", encoding="UTF-8") as f:
        f.write(json.dumps(class_mapping))
    logger.success("class mapping has been written to {}", class_mapping_save_path)


def _check(bases):
    for b in bases:
        if b is object:
            return False
        if callable(b):
            return True
    return False


def parse_registry(reg: Registry):
    props = {
        "type": "object",
        "properties": {},
    }
    class_mapping = {}
    for name, item_dir in reg.items():
        func = _str_to_target(item_dir)
        if isinstance(func, ModuleType):
            continue
        class_mapping[name] = [inspect.getfile(func), inspect.getsourcelines(func)[1]]
        doc_string = func.__doc__
        is_hook = isclass(func) and issubclass(func, ConfigArgumentHook)
        if isclass(func) and _check(func.__bases__):
            func = func.__init__
        params = inspect.signature(func).parameters
        param_props = {"type": "object", "properties": {}}
        if doc_string:
            # TODO: parse doc string to each parameters
            param_props["description"] = doc_string
        items = {}
        required = []
        for param_name, param_obj in params.items():
            if param_name == "self" or (is_hook and param_name == "node"):
                continue
            is_required, item = parse_single_param(param_obj)
            items[param_name] = item
            if is_required:
                required.append(param_name)
        if items:
            param_props["properties"] = items
        if required:
            param_props["required"] = required
        props["properties"][name] = param_props
    return props, class_mapping


def _clean(anno):
    if not hasattr(anno, "__origin__"):
        return anno
    # Optional
    if anno.__origin__ == type or (anno.__origin__ == Union and anno.__args__[1] == NoneType):
        return _clean(anno.__args__[0])
    return anno


def _parse_generic_alias(prop, anno) -> Optional[str]:
    potential_type = None
    if anno.__origin__ in (Sequence, list, tuple):
        potential_type = "array"
        # Do not support like `List[ResNet]`.
        inner_type = _get_type(anno.__args__[0])
        if inner_type:
            prop["items"] = {"type": inner_type}
    elif anno.__origin__ == Union:
        potential_type = None
    elif len(anno.__args__) > 0:
        potential_type = _get_type(anno.__args__[0])
    return potential_type


def parse_single_param(p: Parameter):
    prop = {}
    anno = p.annotation
    potential_type = None

    anno = _clean(anno)

    #  hardcore for torch.optim
    if p.default.__class__.__name__ == "_RequiredParameter":
        p._default = _empty

    if isinstance(anno, _GenericAlias):
        potential_type = _parse_generic_alias(prop, anno)
    elif anno is not _empty:
        potential_type = _get_type(anno)
    # determine type by default value
    elif p.default is not _empty:
        potential_type = _get_type(type(p.default))
    if p.name in SPECIAL_KEYS:
        return False, SPECIAL_KEYS[p.name]
    if p.default is _empty:
        potential_type = "number"
    if potential_type:
        prop["type"] = potential_type
    return p.default is _empty, prop


def _json_schema_path():
    return os.path.join(_cache_dir, _json_schema_file)


def _class_mapping_path():
    return os.path.join(_cache_dir, _class_mapping_file)


def _generate_taplo_config(path):
    cfg = dict(
        schema=dict(
            path=osp.join(osp.expanduser(path), _json_schema_file),
            enabled=True,
        ),
        formatting=dict(align_entries=False),
    )
    with open("./.taplo.toml", "w", encoding="UTF-8") as f:
        toml.dump(cfg, f)
