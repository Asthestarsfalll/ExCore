import fnmatch
import functools
import inspect
import json
import re
from typing import Any, Callable, Dict, List, Optional, Sequence, Union

from tabulate import tabulate

_name_re = re.compile(r"^[A-Za-z0-9_]+$")


def _check_name(name: str):
    if not _name_re.match(name):
        raise ValueError(
            """Unexpected name, only support ASCII letters, ASCII digits,
             underscores, and dashes, but got {}""".format(
                name
            )
        )


def _default_filter_func(values: Sequence[Any]) -> bool:
    for v in values:
        if not v:
            return False
    return True


def _default_match_func(m, base_module):
    if not m.startswith("__"):
        m = getattr(base_module, m)
        if inspect.isfunction(m) or inspect.isclass(m):
            return True
    return False


class Registry(dict):
    children: Dict[str, "Registry"] = dict()

    def __new__(cls, name: str, extra_field: Any = None) -> "Registry":
        _check_name(name)
        if name in Registry.children:
            return Registry.children[name]
        instance = dict.__new__(cls)
        if not name.startswith("__"):
            Registry.children[name] = instance
        return instance

    def __init__(
        self, name: str, *, extra_field: Optional[Union[str, Sequence[str]]] = None
    ) -> None:
        super().__init__()
        self.name = name
        if extra_field:
            self.extra_field = (
                [extra_field] if isinstance(extra_field, str) else extra_field
            )
            self.extra_info = dict()

    @classmethod
    def get_child(cls, name: str, default: Any = None) -> Any:
        return Registry.children.get(name, default)

    @classmethod
    def find(cls, name: str) -> Any:
        for registried_name, child in Registry.children.items():
            if name in child:
                return (child[name], registried_name)
        return (None, None)

    @classmethod
    def make_global(cls):
        cls.GLOBAL = cls("__global")
        for member in Registry.children.values():
            cls.GLOBAL.merge(member, force=False)
        return cls.GLOBAL

    def __setitem__(self, k, v) -> None:
        _check_name(k)
        super().__setitem__(k, v)

    def __repr__(self) -> str:
        s = json.dumps(
            self, indent=4, ensure_ascii=False, sort_keys=False, separators=(",", ":")
        )
        return "\n" + s

    __str__ = __repr__

    def _register(
        self,
        module: Callable,
        force: bool = False,
        name: Optional[str] = None,
        **extra_info,
    ) -> Callable:
        if not (inspect.isfunction(module) or inspect.isclass(module)):
            raise TypeError(
                "Only support function or class, but got {}".format(type(module))
            )

        name = name or module.__name__
        if not force and name in self.keys():
            raise ValueError("The name {} exists".format(name))

        if extra_info:
            if not hasattr(self, "extra_field"):
                raise ValueError(
                    "Registry `{}` does not have `extra_field`.".format(self.name)
                )
            for k in extra_info.keys():
                if k not in self.extra_field:
                    raise ValueError(
                        "Registry `{}`: 'extra_info' does not has expected key {}.".format(
                            self.name, k
                        )
                    )
            self.extra_info[name] = [extra_info.get(k, None) for k in self.extra_field]
        elif hasattr(self, "extra_field"):
            self.extra_info[name] = [None] * len(self.extra_field)

        self[name] = module
        return module

    def register(
        self, force: bool = False, name: Optional[str] = None, **extra_info
    ) -> Callable:
        return functools.partial(self._register, force=force, name=name, **extra_info)

    def register_all(
        self,
        modules: Sequence[Callable],
        names: Optional[Sequence[str]] = None,
        extra_info: Optional[Sequence[Dict[str, Any]]] = None,
        force: bool = False,
    ) -> None:
        _names = names if names else [None] * len(modules)
        _info = extra_info if extra_info else [{}] * len(modules)
        for module, name, info in zip(modules, _names, _info):
            self._register(module, force=force, name=name, **info)

    def merge(
        self,
        others: Union["Registry", List["Registry"]],
        force: bool = False,
    ) -> None:
        if not isinstance(others, list):
            others = [others]
        if not isinstance(others[0], Registry):
            raise TypeError("Expect `Registry` type, but got {}".format(type(others[0])))
        for other in others:
            modules = list(other.values())
            names = list(other.keys())
            self.register_all(modules, force=force, names=names)

    def filter(
        self,
        filter_field: Union[Sequence[str], str],
        filter_func: Callable = _default_filter_func,
    ) -> List[str]:
        filter_field = [filter_field] if isinstance(filter_field, str) else filter_field
        filter_idx = [
            i for i, name in enumerate(self.extra_field) if name in filter_field
        ]
        out = []
        for name in self.keys():
            info = self.extra_info[name]
            filter_values = [info[idx] for idx in filter_idx]
            if filter_func(filter_values):
                out.append(name)
        out = list(sorted(out))
        return out

    def fuzzy_match(self, base_module, match_func=_default_match_func):
        matched_modules = [
            getattr(base_module, name)
            for name in base_module.__dict__.keys()
            if match_func(name, base_module)
        ]
        self.register_all(matched_modules)

    def module_table(
        self,
        filter: Optional[Union[Sequence[str], str]] = None,
        select_info: Optional[Union[Sequence[str], str]] = None,
        module_list: Optional[Sequence[str]] = None,
        **table_kwargs,
    ) -> Any:
        if select_info is not None:
            select_info = [select_info] if isinstance(select_info, str) else select_info
            for info_key in select_info:
                if info_key not in self.extra_field:
                    raise ValueError("Got unexpected info key {}".format(info_key))
        else:
            select_info = []

        all_modules = module_list if module_list else self.keys()
        if filter:
            modules = set()
            filters = [filter] if isinstance(filter, str) else filter
            for f in filters:
                include_models = fnmatch.filter(all_modules, f)
                if len(include_models):
                    modules = modules.union(include_models)
        else:
            modules = all_modules

        modules = list(sorted(modules))

        # TODO: make colorful and suit for logging to file.
        table_headers = ["{}".format(item) for item in [self.name, *select_info]]

        if select_info:
            select_idx = [
                idx for idx, name in enumerate(self.extra_field) if name in select_info
            ]
        else:
            select_idx = []

        table = tabulate(
            [(i, *[self.extra_info[i][idx] for idx in select_idx]) for i in modules],
            headers=table_headers,
            tablefmt="fancy_grid",
            **table_kwargs,
        )
        table = "\n" + table
        return table

    @classmethod
    def children_table(cls, **table_kwargs) -> Any:
        table_headers = ["{}".format("COMPONMENTS")]
        table = tabulate(
            list(sorted([[i] for i in cls.children.keys()])),
            headers=table_headers,
            tablefmt="fancy_grid",
            **table_kwargs,
        )
        table = "\n" + table
        return table
