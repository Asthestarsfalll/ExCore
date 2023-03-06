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


class Registry(dict):
    children: Dict[str, "Registry"] = dict()

    def __new__(cls, name: str) -> "Registry":
        _check_name(name)
        if name in Registry.children:
            return Registry.children[name]
        instance = dict.__new__(cls)
        if not name.startswith("__"):
            Registry.children[name] = instance
        return instance

    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name

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

    def __getattr__(self, attr: str) -> Callable:
        return self[attr]

    def __repr__(self) -> str:
        s = json.dumps(self, indent=4, ensure_ascii=False, sort_keys=False, separators=(",", ":"))
        return "\n" + s

    __str__ = __repr__

    def _register(
        self, module: Callable, force: bool = False, name: Optional[str] = None
    ) -> Callable:
        if not (inspect.isfunction(module) or inspect.isclass(module)):
            raise TypeError("Only support function or class, but got {}".format(type(module)))

        name = name or module.__name__
        if not force and name in self.keys():
            raise ValueError("The name {} exists".format(name))

        self[name] = module
        return module

    def register(self, force: bool = False, name: Optional[str] = None) -> Callable:
        return functools.partial(self._register, force=force, name=name)

    def register_all(
        self,
        modules: Sequence[Callable],
        names: Optional[Sequence[str]] = None,
        force: bool = False,
    ) -> None:
        _names = names if names else [None] * len(modules)
        for module, name in zip(modules, _names):
            self._register(module, force=force, name=name)

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

    def module_table(self, filter: Optional[Union[Sequence, str]] = None, **table_kwargs) -> Any:
        all_modules = self.keys()
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

        table_headers = ["\033[36m{}\033[0m".format(self.name)]
        table = tabulate(
            [(i,) for i in modules], headers=table_headers, tablefmt="fancy_grid", **table_kwargs
        )
        table = "\n" + table
        return table

    @classmethod
    def children_table(cls, **table_kwargs):
        table_headers = ["\033[36m{}\033[0m".format("COMPNMENTS")]
        table = tabulate(
            list(sorted([[i] for i in cls.children.keys()])),
            headers=table_headers,
            tablefmt="fancy_grid",
            **table_kwargs,
        )
        table = "\n" + table
        return table


HOOKS = Registry("hooks")
