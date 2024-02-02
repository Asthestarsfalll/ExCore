import fnmatch
import functools
import inspect
import os
import re
import sys
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Sequence, Union

from excore.utils.utils import FileLock, _create_table

from .._constants import _cache_dir, _registry_cache_file, _workspace_config_file
from .logging import logger

_name_re = re.compile(r"^[A-Za-z0-9_]+$")
_private_flag: str = "__"

__all__ = ["Registry"]


# TODO: Maybe some methods need to be cleared.


def _is_pure_ascii(name: str):
    if not _name_re.match(name):
        raise ValueError(
            f"""Unexpected name, only support ASCII letters, ASCII digits,
             underscores, and dashes, but got {name}"""
        )


def _is_function_or_class(module):
    return inspect.isfunction(module) or inspect.isclass(module)


def _default_filter_func(values: Sequence[Any]) -> bool:
    return all(v for v in values)


def _default_match_func(m, base_module):
    if not m.startswith("__"):
        m = getattr(base_module, m)
        if inspect.isfunction(m) or inspect.isclass(m):
            return True
    return False


def _get_module_name(m):
    return getattr(m, "__qualname__", m.__name__)


class RegistryMeta(type):
    _registry_pool: Dict[str, "Registry"] = dict()
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

    def __call__(cls, name, **kwargs) -> "Registry":
        r"""Assert only call `__init__` once"""
        _is_pure_ascii(name)
        extra_field = kwargs.get("extra_field", None)
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
class Registry(dict, metaclass=RegistryMeta):
    _globals: Optional["Registry"] = None
    _registry_dir = "registry"
    # just a workaround for twice registry
    _prevent_register = False
    """A registry that stores functions and classes by name.

    Attributes:
        name (str): The name of the registry.
        extra_field (Optional[Union[str, Sequence[str]]]): A field or fields that can be
            used to store additional information about each function or class in the
            registry.
        extra_info (Dict[str, List[Any]]): A dictionary that maps each registered name
            to a list of extra values associated with that name (if any).
        _globals (Optional[Registry]): A static variable that stores a global registry
            containing all functions and classes registered using Registry.

    """

    def __init__(
        self, /, name: str, *, extra_field: Optional[Union[str, Sequence[str]]] = None
    ) -> None:
        super().__init__()
        self.name = name
        if extra_field:
            self.extra_field = [extra_field] if isinstance(extra_field, str) else extra_field
        self.extra_info = dict()

    @classmethod
    def dump(cls, file_name: str = _registry_cache_file, obj: Optional[Dict] = None):
        file_path = os.path.join(_cache_dir, cls._registry_dir, file_name)
        os.makedirs(os.path.join(_cache_dir, cls._registry_dir), exist_ok=True)
        import pickle  # pylint: disable=import-outside-toplevel

        with FileLock(file_path), open(file_path, "wb") as f:
            pickle.dump(obj or cls._registry_pool, f)

    @classmethod
    def load(cls, file_name: str = _registry_cache_file, obj: Optional[Dict] = None, slient=False):
        if not os.path.exists(_workspace_config_file):
            logger.warning("Please run `excore init` in your command line first!")
            sys.exit(0)
        file_path = os.path.join(_cache_dir, cls._registry_dir, file_name)
        if not os.path.exists(file_path):
            if not slient:
                # shall we need to be silent? Or raise error?
                logger.critical(
                    "Registry cache file do not exist!"
                    " Please run `excore auto-register in your command line first`"
                )
            return
        import pickle  # pylint: disable=import-outside-toplevel

        with FileLock(file_path), open(file_path, "rb") as f:
            data = pickle.load(f)
        if obj is None:
            cls._registry_pool.update(data)
        else:
            obj.update(data)

    @classmethod
    def lock_register(cls):
        cls._prevent_register = True

    @classmethod
    def unlock_register(cls):
        cls._prevent_register = False

    @classmethod
    def get_registry(cls, name: str, default: Any = None) -> Any:
        """
        Returns the `Registry` instance with the given name, or `default` if no such
        registry exists.
        """
        return Registry._registry_pool.get(name, default)

    @classmethod
    def find(cls, name: str) -> Any:
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
    def make_global(cls):
        """
        Creates a global `Registry` instance that contains all elements from all
        other registries. If the global registry already exists, returns it instead
        of creating a new one.
        """
        if cls._globals is not None:
            return cls._globals
        cls._globals = cls("__global")
        for member in Registry._registry_pool.values():
            cls._globals.merge(member, force=False)
        return cls._globals

    def __setitem__(self, k, v) -> None:
        _is_pure_ascii(k)
        super().__setitem__(k, v)

    def __repr__(self) -> str:
        return _create_table(
            None,
            [(k, v) for k, v in self.items()],
            False,
        )

    __str__ = __repr__

    def _register(
        self,
        module: Union[Callable, ModuleType],
        force: bool = False,
        name: Optional[str] = None,
        **extra_info,
    ) -> Union[Callable, ModuleType]:
        if Registry._prevent_register:
            logger.ex("Registry has been locked!!!")
            return module
        if not (_is_function_or_class(module) or isinstance(module, ModuleType)):
            raise TypeError(f"Only support function or class, but got {type(module)}")
        true_name = _get_module_name(module)
        name = name or true_name
        if not force and name in self and not self[name] == module:
            raise ValueError(f"The name {name} exists")

        if extra_info:
            if not hasattr(self, "extra_field"):
                raise ValueError(f"Registry `{self.name}` does not have `extra_field`.")
            for k in extra_info:
                if k not in self.extra_field:
                    raise ValueError(
                        f"Registry `{self.name}`: 'extra_info' does not has expected key {k}."
                    )
            self.extra_info[name] = [extra_info.get(k, None) for k in self.extra_field]
        elif hasattr(self, "extra_field"):
            self.extra_info[name] = [None] * len(self.extra_field)

        self[name] = (
            true_name
            if isinstance(module, ModuleType)
            else ".".join([module.__module__, module.__qualname__])
        )

        # update to globals
        if Registry._globals is not None and not self.name.startswith(_private_flag):
            Registry._globals._register(module, force, name, **extra_info)

        return module

    def register(self, force: bool = False, name: Optional[str] = None, **extra_info) -> Callable:
        """
        Decorator that registers a function or class with the current `Registry`.
        Any keyword arguments provided are added to the `extra_info` list for the
        registered element. If `force` is True, overwrites any existing element with
        the same name.
        """
        return functools.partial(self._register, force=force, name=name, **extra_info)

    def register_all(
        self,
        modules: Sequence[Callable],
        names: Optional[Sequence[str]] = None,
        extra_info: Optional[Sequence[Dict[str, Any]]] = None,
        force: bool = False,
    ) -> None:
        """
        Registers multiple functions or classes with the current `Registry`. Each
        element in `modules` is associated with a name from `names` (if provided) and
        extra information from the corresponding dict in `extra_info` (if provided).
        If `force` is True, overwrites any existing elements with the same names.
        """
        _names = names if names else [None] * len(modules)
        _info = extra_info if extra_info else [{}] * len(modules)
        for module, name, info in zip(modules, _names, _info):
            self._register(module, force=force, name=name, **info)

    def merge(
        self,
        others: Union["Registry", List["Registry"]],
        force: bool = False,
    ) -> None:
        """
        Merge the contents of one or more other registries into the current one.
        If `force` is True, overwrites any existing elements with the same names.
        """
        if not isinstance(others, list):
            others = [others]
        if not isinstance(others[0], Registry):
            raise TypeError(f"Expect `Registry` type, but got {type(others[0])}")
        for other in others:
            modules = list(other.values())
            names = list(other.keys())
            self.register_all(modules, force=force, names=names)

    def filter(
        self,
        filter_field: Union[Sequence[str], str],
        filter_func: Callable = _default_filter_func,
    ) -> List[str]:
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

    def match(self, base_module, match_func=_default_match_func):
        """
        Registers all functions or classes from the given module that pass a matching
        function. If `match_func` is not provided, uses `_default_match_func`.
        """
        matched_modules = [
            getattr(base_module, name)
            for name in base_module.__dict__
            if match_func(name, base_module)
        ]
        matched_modules = list(filter(_is_function_or_class, matched_modules))
        logger.ex("matched modules:{}", [i.__name__ for i in matched_modules])
        self.register_all(matched_modules)

    def module_table(
        self,
        filter: Optional[Union[Sequence[str], str]] = None,
        select_info: Optional[Union[Sequence[str], str]] = None,
        module_list: Optional[Sequence[str]] = None,
        **table_kwargs,
    ) -> Any:
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

        # TODO(Asthestarsfalll): make this colorful and suit for logging to file.
        table_headers = [f"{item}" for item in [self.name, *select_info]]

        if select_info:
            select_idx = [idx for idx, name in enumerate(self.extra_field) if name in select_info]
        else:
            select_idx = []

        table = _create_table(
            table_headers,
            [(i, *[self.extra_info[i][idx] for idx in select_idx]) for i in modules],
            False,
            **table_kwargs,
        )
        table = "\n" + table
        return table

    @classmethod
    def registry_table(cls, **table_kwargs) -> Any:
        """
        Returns a table containing the names of all available registries.
        """
        table_headers = ["COMPONMENTS"]
        table = _create_table(
            table_headers,
            list(sorted([[i] for i in cls._registry_pool])),
            False,
            **table_kwargs,
        )
        table = "\n" + table
        return table


def load_registries():
    if not os.path.exists(os.path.join(_cache_dir, Registry._registry_dir, _registry_cache_file)):
        logger.warning("Please run `excore auto-register` in your command line first!")
        return
    Registry.load()
    # We'd better to lock register to prevent
    # the inconsistency between the twice registration.
    Registry.lock_register()
    if not Registry._registry_pool:
        raise RuntimeError(
            "No module has been registered, \
                           you may need to call `excore.registry.auto_register` first"
        )
