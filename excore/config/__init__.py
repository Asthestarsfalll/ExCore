from .action import DictAction
from .config import build_all, load, load_config
from .models import (
    ClassNode,
    ConfigArgumentHook,
    ConfigNode,
    GetAttr,
    InterNode,
    ModuleNode,
    ReusedNode,
    VariableReference,
    register_argument_hook,
    register_special_flag,
    silent,
)
from .parse import ConfigDict, set_primary_fields


def to_python(cfg: dict, path=None):
    """Convert config dictionary to python code string, optionally saving to a file."""
    def _format(obj, indent=0):
        sp = "    " * indent
        if isinstance(obj, dict):
            if not obj:
                return "{}"
            lines = []
            for k, v in obj.items():
                lines.append(f"{sp}{k} = {_format(v, indent)}")
            return "\n".join(lines)
        elif isinstance(obj, (list, tuple)):
            if not obj:
                return "[]"
            items = [_format(i, indent) for i in obj]
            if any("\n" in item for item in items):
                return "[\n" + ",\n".join(items) + "\n" + sp + "]"
            return "[" + ", ".join(items) + "]"
        elif isinstance(obj, str):
            return f'"{obj}"'
        elif isinstance(obj, bool):
            return "True" if obj else "False"
        elif obj is None:
            return "None"
        return str(obj)

    code = _format(cfg)
    if path is not None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(code + "\n")
        return None
    return code

__all__ = [
    "build_all",
    "DictAction",
    "load",
    "load_config",
    "silent",
    "to_python",
    "set_primary_fields",
    "ConfigArgumentHook",
    "ConfigDict",
    "ConfigNode",
    "GetAttr",
    "ClassNode",
    "InterNode",
    "ModuleNode",
    "ReusedNode",
    "register_argument_hook",
    "register_special_flag",
    "VariableReference",
]
