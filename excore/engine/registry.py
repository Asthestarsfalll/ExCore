from __future__ import annotations

import fnmatch
import functools
import inspect
import os
import re
import sys
from collections.abc import Sequence
from types import FunctionType, ModuleType
from typing import Any, Callable, Literal, Type, overload

from filelock import FileLock

from .._constants import _workspace_config_file, workspace
from .._misc import _create_table
from .logging import logger

_name_re = re.compile(r"^[A-Za-z0-9_]+$")
_private_flag: str = "__"

__all__ = ["Registry"]

_ClassType = Type[Any]


# TODO: Maybe some methods need to be cleared.


def _is_pure_ascii(name: str) -> None:
    if not _name_re.match(name):
        raise ValueError(
            "Unexpected name, only support ASCII letters, ASCII digits, "
            f"underscores, and dashes, but got {name}."
        )


def _is_function_or_class(module: Any) -> bool:
    return inspect.isfunction(module) or inspect.isclass(module)


def _default_filter_func(values: Sequence[Any]) -> bool:
    return all(v for v in values)


def _default_match_func(m: str, base_module: ModuleType) -> bool:
    if not m.startswith("__"):
        m = getattr(base_module, m)
        if inspect.isfunction(m) or inspect.isclass(m):
            return True
    return False


def _get_module_name(m: ModuleType | _ClassType | FunctionType) -> str:
    return getattr(m, "__qualname__", m.__name__)


class RegistryMeta(type):
    _registry_pool: dict[str, Registry] = {}
    """Metaclass that governs the creation of instances of its subclasses, which are
    `Registry` objects.

    Attributes:
        _registry_pool (dict): A dictionary that maps registry names to `Registry`
            instances.

    Methods:
        __call__(name, **kwargs) -> Registry:
            Creates an instance of `Registry` with the given `name`. If an instance with
            the same name already exists, returns that instance instead. If additional
            keyword arguments are provided and the instance already exists, a warning
            message is logged indicating that the extra arguments will be ignored.
    """

    def __call__(cls, name: str, **kwargs: Any) -> Registry:
        r"""Assert only call `__init__` once"""
        _is_pure_ascii(name)
        extra_field = kwargs.get("extra_field")
        if name in cls._registry_pool:
            extra_field = [extra_field] if isinstance(extra_field, str) else extra_field
            target = cls._registry_pool[name]
            if extra_field and hasattr(target, "extra_field") and extra_field != target.extra_field:
                logger.warning(
                    f"{cls.__name__}: `{name}` has already existed,"
                    " different arguments will be ignored"
                )
            return target
        instance = super().__call__(name, **kwargs)
        if not name.startswith(_private_flag):
            cls._registry_pool[name] = instance
        return instance


# Maybe someday we can get rid of Registry?
class Registry(dict, metaclass=RegistryMeta):  # type: ignore
    """A registry that stores functions and classes by name.

    Attributes:
        name (str): The name of the registry.
        extra_field (str|Sequence[str]|None): A field or fields that can be
            used to store additional information about each function or class in the
            registry.
        extra_info (dict[str, list[Any]]): A dictionary that maps each registered name
            to a list of extra values associated with that name (if any).
        _globals (Registry|None): A static variable that stores a global registry
            containing all functions and classes registered using Registry.

    Examples:
        >>> from excore import Registry

        >>> MODEL = Registry('Model', extra_field=['is_backbone'])

        >>> @MODEL.registry(force=False, is_backbone=True)
        ... class ResNet:
        ...     ...
    """

    _globals: Registry | None = None
    # just a workaround for twice registry
    _prevent_register: bool = False
    extra_info: dict[str, str]

    def __init__(self, /, name: str, *, extra_field: str | Sequence[str] | None = None) -> None:
        super().__init__()
        self.name = name
        if extra_field:
            self.extra_field = [extra_field] if isinstance(extra_field, str) else extra_field
        self.extra_info = {}

    @classmethod
    def dump(cls, update: bool = False) -> None:
        import pickle  # pylint: disable=import-outside-toplevel

        file_path = workspace.registry_cache_file

        if update and os.path.exists(file_path):
            with open(file_path, "rb") as f:
                cache_to_dump = pickle.load(f)

            cache_to_dump.update(cls._registry_pool)
        else:
            cache_to_dump = cls._registry_pool

        with FileLock(file_path + ".lock", timeout=5), open(file_path, "wb") as f:
            pickle.dump(cache_to_dump, f)

        logger.success(f"Dump registry cache to {workspace.registry_cache_file}!")

    @classmethod
    def load(cls) -> None:
        if not os.path.exists(_workspace_config_file):
            logger.warning("Please run `excore init` in your command line first!")
            sys.exit(1)
        file_path = workspace.registry_cache_file
        if not os.path.exists(file_path):
            # shall we need to be silent? Or raise error?
            logger.critical(
                "Registry cache file do not exist!"
                " Please run `excore auto-register in your command line first`"
            )
            sys.exit(1)
        import pickle  # pylint: disable=import-outside-toplevel

        with FileLock(file_path + ".lock"), open(file_path, "rb") as f:
            data = pickle.load(f)
        cls._registry_pool.update(data)

    @classmethod
    def lock_register(cls) -> None:
        cls._prevent_register = True

    @classmethod
    def unlock_register(cls) -> None:
        cls._prevent_register = False

    @classmethod
    def get_registry(cls, name: str, default: Any = None) -> Registry:
        """
        Returns the `Registry` instance with the given name, or `default` if no such
        registry exists.
        """
        return Registry._registry_pool.get(name, default)

    @classmethod
    @functools.lru_cache(32)
    def find(cls, name: str) -> tuple[Any, str] | tuple[None, None]:
        """
        Searches all registries for an element with the given name. If found,
        returns a tuple containing the element and the name of the registry where it
        was found; otherwise, returns `(None, None)`.
        """
        for registried_name, registry in Registry._registry_pool.items():
            if name in registry:
                return (registry[name], registried_name)
        return (None, None)

    @classmethod
    def make_global(cls) -> Registry:
        """
        Creates a global `Registry` instance that contains all elements from all
        other registries. If the global registry already exists, returns it instead
        of creating a new one.
        """
        if cls._globals is not None:
            return cls._globals
        reg = cls("__global")
        for member in Registry._registry_pool.values():
            reg.merge(member, force=False)
        cls._globals = reg
        return reg

    def __setitem__(self, k: str, v: Any) -> None:
        _is_pure_ascii(k)
        super().__setitem__(k, v)

    def __repr__(self) -> str:
        return _create_table(
            ["NAME", "DIR"],
            [(k, v) for k, v in self.items()],
        )

    __str__ = __repr__

    @overload
    def register_module(
        self,
        module: Callable[..., Any],
        force: bool = ...,
        _is_str: bool = ...,
        **extra_info: Any,
    ) -> Callable[..., Any]:
        pass

    @overload
    def register_module(
        self,
        module: ModuleType,
        force: bool = ...,
        _is_str: bool = ...,
        **extra_info: Any,
    ) -> ModuleType:
        pass

    @overload
    def register_module(
        self,
        module: str,
        force: bool = ...,
        _is_str: Literal[True] = ...,
        **extra_info: Any,
    ) -> str:
        pass

    def register_module(
        self,
        module,
        force=False,
        _is_str=False,
        **extra_info,
    ):
        if Registry._prevent_register:
            logger.ex("Registry has been locked!!!")
            return module
        if not _is_str:
            if not (_is_function_or_class(module) or isinstance(module, ModuleType)):
                raise TypeError(f"Only support function or class, but got {type(module)}")
            name = _get_module_name(module)
        else:
            name = module.split(".")[-1]

        if not force and name in self:
            raise ValueError(f"The name {name} exists")

        if extra_info:
            if not hasattr(self, "extra_field"):
                raise ValueError(f"Registry `{self.name}` does not have `extra_field`.")
            for k in extra_info:
                if k not in self.extra_field:
                    raise ValueError(
                        f"Registry `{self.name}`: 'extra_info' does not has expected key {k}."
                    )
            self.extra_info[name] = [extra_info.get(k) for k in self.extra_field]
        elif hasattr(self, "extra_field"):
            self.extra_info[name] = [None] * len(self.extra_field)
        if not _is_str:
            target = (
                name
                if isinstance(module, ModuleType)
                else ".".join([module.__module__, module.__qualname__])
            )
        else:
            target = module

        logger.ex(f"Register {name} with {target}.")
        self[name] = target

        # update to globals
        if Registry._globals is not None and not name.startswith(_private_flag):
            Registry._globals.register_module(target, force, True, **extra_info)

        return module

    def register(self, force: bool = False, **extra_info: Any) -> Callable[..., Any]:
        """
        Decorator that registers a function or class with the current `Registry`.
        Any keyword arguments provided are added to the `extra_info` list for the
        registered element. If `force` is True, overwrites any existing element with
        the same name.
        """
        return functools.partial(self.register_module, force=force, **extra_info)

    def register_all(
        self,
        modules: Sequence[Callable[..., Any]],
        extra_info: Sequence[dict[str, Any]] | None = None,
        force: bool = False,
        _is_str: bool = False,
    ) -> None:
        """
        Registers multiple functions or classes with the current `Registry`.
        If `force` is True, overwrites any existing elements with the same names.
        """
        if Registry._prevent_register:
            return
        _info = extra_info if extra_info else [{}] * len(modules)
        for module, info in zip(modules, _info):
            self.register_module(module, force=force, _is_str=_is_str, **info)

    def get_extra_info(self, key: str, name: str) -> Any:
        if name not in self.extra_field:
            raise ValueError(f"Expected name to be one of `{self.extra_field}`, but got `{name}`.")
        for target_name, info in zip(self.extra_field, self.extra_info[key]):
            if name == target_name:
                return info

    def merge(
        self,
        others: Registry | Sequence[Registry],
        force: bool = False,
    ) -> None:
        """
        Merge the contents of one or more other registries into the current one.
        If `force` is True, overwrites any existing elements with the same names.
        """
        if not isinstance(others, (list, tuple, Sequence)):
            others = [others]
        for other in others:
            if not isinstance(other, Registry):
                raise TypeError(f"Expect `Registry` type, but got {type(other)}")
            modules = list(other.values())
            self.register_all(modules, force=force, _is_str=True)

    def filter(
        self,
        filter_field: Sequence[str] | str,
        filter_func: Callable[[Sequence[Any]], bool] = _default_filter_func,
    ) -> list[str]:
        """
        Returns a sorted list of all names in the registry for which the values of
        the given extra field(s) pass a filtering function.
        """

        filter_field = [filter_field] if isinstance(filter_field, str) else filter_field
        filter_idx = [i for i, name in enumerate(self.extra_field) if name in filter_field]
        out = []
        for name in self.keys():
            info = self.extra_info[name]
            filter_values = [info[idx] for idx in filter_idx]
            if filter_func(filter_values):
                out.append(name)
        out = list(sorted(out))
        return out

    def match(
        self,
        base_module: ModuleType,
        match_func: Callable[[str, ModuleType], bool] = _default_match_func,
        force: bool = False,
    ) -> None:
        """
        Registers all functions or classes from the given module that pass a matching
        function. If `match_func` is not provided, uses `_default_match_func`.
        """
        if Registry._prevent_register:
            return
        matched_modules = [
            getattr(base_module, name)
            for name in base_module.__dict__
            if match_func(name, base_module)
        ]
        matched_modules = list(filter(_is_function_or_class, matched_modules))
        logger.ex("matched modules:{}", [i.__name__ for i in matched_modules])
        self.register_all(matched_modules, force=force)

    def module_table(
        self,
        filter: Sequence[str] | str | None = None,
        select_info: Sequence[str] | str | None = None,
        module_list: Sequence[str] | None = None,
        **table_kwargs: Any,
    ) -> str:
        """
        Returns a table containing information about each registered function or
        class, filtered by name and/or extra info fields. `select_info` specifies
        which extra info fields to include in the table, while `module_list`
        specifies which modules to include (by default, includes all modules).
        """
        if select_info is not None:
            select_info = [select_info] if isinstance(select_info, str) else select_info
            for info_key in select_info:
                if info_key not in self.extra_field:
                    raise ValueError(f"Got unexpected info key {info_key}")
        else:
            select_info = []

        all_modules = module_list if module_list else list(self.keys())
        if filter:
            set_modules: set[str] = set()
            filters = [filter] if isinstance(filter, str) else filter
            for f in filters:
                include_models = fnmatch.filter(all_modules, f)
                if len(include_models):
                    modules = list(set_modules.union(include_models))
        else:
            modules = all_modules  # type: ignore

        modules = list(sorted(modules))

        # TODO(Asthestarsfalll): make this colorful and suit for logging to file.
        table_headers = [f"{item}" for item in [self.name, *select_info]]

        if select_info:
            select_idx = [idx for idx, name in enumerate(self.extra_field) if name in select_info]
        else:
            select_idx = []

        table = _create_table(
            table_headers,
            [(i, *[self.extra_info[i][idx] for idx in select_idx]) for i in modules],
            **table_kwargs,
        )
        table = "\n" + table
        return table

    @classmethod
    def registry_table(cls, **table_kwargs) -> str:
        """
        Returns a table containing the names of all available registries.
        """
        table_headers = ["REGISTRY"]
        table = _create_table(
            table_headers,
            list(sorted([[i] for i in cls._registry_pool])),
            **table_kwargs,
        )
        table = "\n" + table
        return table


def load_registries() -> None:
    message = "Please run `excore auto-register` in your command line first!"
    if not os.path.exists(workspace.registry_cache_file):
        logger.warning(message)
        return
    Registry.load()
    # We'd better to lock register to prevent the inconsistency between the twice registration.
    Registry.lock_register()
    if not Registry._registry_pool:
        logger.critical(f"No module has been registered. {message}")
        sys.exit(1)
