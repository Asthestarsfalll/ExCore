from __future__ import annotations

import inspect
import json
import os
import os.path as osp
import sys
from inspect import Parameter, _empty, _ParameterKind, isclass
from types import ModuleType
from typing import Any, Dict, Sequence, Union, get_args, get_origin

import toml

from .._constants import _cache_dir, _class_mapping_file, _json_schema_file
from ..engine.hook import ConfigArgumentHook
from ..engine.logging import logger
from ..engine.registry import Registry, load_registries
from .model import _str_to_target

if sys.version_info >= (3, 10, 0):
    from types import NoneType, UnionType
else:
    NoneType = type(None)

    # just a placeholder
    class UnionType:
        pass


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
    default_schema = {
        "title": "ExCore",
        "description": "Uesd for ExCore config file completion",
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


def _check(bases) -> bool:
    for b in bases:
        if b is object:
            return False
        if callable(b):
            return True
    return False


def parse_registry(reg: Registry) -> tuple[dict, dict[str, list[str | int]]]:
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
            try:
                is_required, item = parse_single_param(param_obj)
            except Exception:
                from rich.console import Console

                logger.error(f"Skip {param_obj.name} of {name}")
                Console().print_exception()
                continue
            items[param_name] = item
            if is_required:
                required.append(param_name)
        if items:
            param_props["properties"] = items
        if required:
            param_props["required"] = required
        props["properties"][name] = param_props
    return props, class_mapping


def _remove_optional(anno):
    origin = get_origin(anno)
    inner_types = get_args(anno)
    if origin is not Union and len(inner_types) != 2:
        return anno
    filter_types = [i for i in inner_types if i is not NoneType]
    if len(filter_types) == 1:
        return _remove_optional(filter_types[0])
    return anno


def _parse_inner_types(prop: dict, inner_types: Sequence[type]) -> None:
    first_type = inner_types[0]
    is_all_the_same = True
    for t in inner_types:
        is_all_the_same &= t == first_type
    if is_all_the_same and first_type in TYPE_MAPPER:
        prop["items"] = {"type": TYPE_MAPPER.get(first_type)}


def _parse_typehint(prop: dict, anno: type) -> str | None:
    potential_type = TYPE_MAPPER.get(anno)
    if potential_type is not None:
        return potential_type
    origin = get_origin(anno)
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


def parse_single_param(param: Parameter) -> tuple[bool, dict[str, Any]]:
    prop = {}
    anno = param.annotation
    potential_type = None

    anno = _remove_optional(anno)

    #  hardcore for torch.optim
    if param.default.__class__.__name__ == "_RequiredParameter":
        param._default = _empty

    if isinstance(anno, str):
        raise RuntimeError(
            "Use a higher version of python, e.g. 3.10, "
            "and remove `from __future__ import annotations`."
        )
    elif anno is not _empty:
        potential_type = _parse_typehint(prop, anno)
    # determine type by default value
    elif param.default is not _empty:
        potential_type = TYPE_MAPPER[type(param.default)]
        if isinstance(param.default, (list, tuple)):
            types = [type(t) for t in param.default]
            _parse_inner_types(prop, types)
    elif param._kind is _ParameterKind.VAR_POSITIONAL:
        return False, {"type": "array"}
    elif param._kind is _ParameterKind.VAR_KEYWORD:
        return False, {"type": "object"}
    if anno is _empty and param.default is _empty:
        potential_type = "number"
    if potential_type:
        prop["type"] = potential_type
    return param.default is _empty, prop


def _json_schema_path() -> str:
    return os.path.join(_cache_dir, _json_schema_file)


def _class_mapping_path() -> str:
    return os.path.join(_cache_dir, _class_mapping_file)


def _generate_taplo_config(path: str) -> None:
    cfg = dict(
        schema=dict(
            path=osp.join(osp.expanduser(path), _json_schema_file),
            enabled=True,
        ),
        formatting=dict(align_entries=False),
    )
    with open("./.taplo.toml", "w", encoding="UTF-8") as f:
        toml.dump(cfg, f)
