---
title: registry
sidebar_position: 3
---

## TOC

- **Attributes:**
  - 🅰 [\_name\_re](#🅰-_name_re) - TODO: Maybe some methods need to be cleared.
  - 🅰 [\_private\_flag](#🅰-_private_flag) - TODO: Maybe some methods need to be cleared.
  - 🅰 [\_ClassType](#🅰-_classtype) - TODO: Maybe some methods need to be cleared.
- **Functions:**
  - 🅵 [\_is\_pure\_ascii](#🅵-_is_pure_ascii)
  - 🅵 [\_is\_function\_or\_class](#🅵-_is_function_or_class)
  - 🅵 [\_default\_filter\_func](#🅵-_default_filter_func)
  - 🅵 [\_default\_match\_func](#🅵-_default_match_func)
  - 🅵 [\_get\_module\_name](#🅵-_get_module_name)
  - 🅵 [load\_registries](#🅵-load_registries)
- **Classes:**
  - 🅲 [RegistryMeta](#🅲-registrymeta)
  - 🅲 [Registry](#🅲-registry) - A registry that stores functions and classes by name.

## Attributes

## 🅰 \_name\_re

```python
_name_re = re.compile("^[A-Za-z0-9_]+$") #TODO: Maybe some methods need to be cleared.
```

## 🅰 \_private\_flag

```python
_private_flag: str = "__" #TODO: Maybe some methods need to be cleared.
```

## 🅰 \_ClassType

```python
_ClassType = Type[Any] #TODO: Maybe some methods need to be cleared.
```


## Functions

## 🅵 \_is\_pure\_ascii

```python
def _is_pure_ascii(name: str) -> None:
    if not _name_re.match(name):
        raise ValueError(
            f"Unexpected name, only support ASCII letters, ASCII digits, underscores, and dashes, but got {name}."
        )
```
## 🅵 \_is\_function\_or\_class

```python
def _is_function_or_class(module: Any) -> bool:
    return inspect.isfunction(module) or inspect.isclass(module)
```
## 🅵 \_default\_filter\_func

```python
def _default_filter_func(values: Sequence[Any]) -> bool:
    return all(v for v in values)
```
## 🅵 \_default\_match\_func

<details>

<summary>\_default\_match\_func</summary>
```python
def _default_match_func(m: str, base_module: ModuleType) -> bool:
    if not m.startswith("__"):
        m = getattr(base_module, m)
        if inspect.isfunction(m) or inspect.isclass(m):
            return True
    return False
```

</details>

## 🅵 \_get\_module\_name

```python
def _get_module_name(m: ModuleType | _ClassType | FunctionType) -> str:
    return getattr(m, "__qualname__", m.__name__)
```
## 🅵 load\_registries

<details>

<summary>load\_registries</summary>
```python
def load_registries() -> None:
    message = "Please run `excore auto-register` in your command line first!"
    if not os.path.exists(workspace.registry_cache_file):
        logger.warning(message)
        return
    Registry.load()
    Registry.lock_register()
    if not Registry._registry_pool:
        logger.critical(f"No module has been registered. {message}")
        sys.exit(1)
```

</details>


## Classes

## 🅲 RegistryMeta

```python
class RegistryMeta(type):
    _registry_pool: dict[str, Registry] = {}
```


### 🅼 \_\_call\_\_

<details>

<summary>\_\_call\_\_</summary>
```python
def __call__(cls, name: str, **kwargs: Any) -> Registry:
    _is_pure_ascii(name)
    extra_field = kwargs.get("extra_field")
    if name in cls._registry_pool:
        extra_field = (
            [extra_field] if isinstance(extra_field, str) else extra_field
        )
        target = cls._registry_pool[name]
        if (
            extra_field
            and hasattr(target, "extra_field")
            and extra_field != target.extra_field
        ):
            logger.warning(
                f"{cls.__name__}: `{name}` has already existed, different arguments will be ignored"
            )
        return target
    instance = super().__call__(name, **kwargs)
    if not name.startswith(_private_flag):
        cls._registry_pool[name] = instance
    return instance
```

</details>


Assert only call \`\_\_init\_\_\` once
## 🅲 Registry

```python
class Registry(dict):
    _globals: Registry | None = None
    _prevent_register: bool = False
    extra_info: dict[str, str] = None
    __str__ = __repr__
```

A registry that stores functions and classes by name.

**Attributes:**

- **name** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): The name of the registry.
- **extra_field** (str|Sequence[str] | [None](https://docs.python.org/3/library/constants.html#None)]): A field or fields that can be
used to store additional information about each function or class in the
registry.
- **extra_info** ([dict](https://docs.python.org/3/library/stdtypes.html#mapping-types-dict)[[str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str), [list](https://docs.python.org/3/library/stdtypes.html#lists)[[Any](https://docs.python.org/3/library/typing.html#typing.Any)]]): A dictionary that maps each registered name
to a list of extra values associated with that name \(if any\).
- **_globals** ([Registry](registry#🅲-registry) | [None](https://docs.python.org/3/library/constants.html#None)): A static variable that stores a global registry
containing all functions and classes registered using Registry.

**Examples:**

```python
>>> from excore import Registry

>>> MODEL = Registry('Model', extra_field=['is_backbone'])

>>> @MODEL.registry(force=False, is_backbone=True)
... class ResNet:
...     ...
```


### 🅼 \_\_init\_\_

<details>

<summary>\_\_init\_\_</summary>
```python
def __init__(
    self, /, name: str, *, extra_field: str | Sequence[str] | None = None
) -> None:
    self.name = name
    if extra_field:
        self.extra_field = (
            [extra_field] if isinstance(extra_field, str) else extra_field
        )
    self.extra_info = {}
```

</details>

### 🅼 dump

<details>

<summary>dump</summary>
```python
@classmethod
def dump(cls, update: bool = False) -> None:
    import pickle

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
```

</details>

### 🅼 load

<details>

<summary>load</summary>
```python
@classmethod
def load(cls) -> None:
    if not os.path.exists(_workspace_config_file):
        logger.warning("Please run `excore init` in your command line first!")
        sys.exit(1)
    file_path = workspace.registry_cache_file
    if not os.path.exists(file_path):
        logger.critical(
            "Registry cache file do not exist! Please run `excore auto-register in your command line first`"
        )
        sys.exit(1)
    import pickle

    with FileLock(file_path + ".lock"), open(file_path, "rb") as f:
        data = pickle.load(f)
    cls._registry_pool.update(data)
```

</details>

### 🅼 lock\_register

```python
@classmethod
def lock_register(cls) -> None:
    cls._prevent_register = True
```
### 🅼 unlock\_register

```python
@classmethod
def unlock_register(cls) -> None:
    cls._prevent_register = False
```
### 🅼 get\_registry

```python
@classmethod
def get_registry(cls, name: str, default: Any = None) -> Registry:
    return Registry._registry_pool.get(name, default)
```

Returns the \`Registry\` instance with the given name, or \`default\` if no such

registry exists.
### 🅼 find

<details>

<summary>find</summary>
```python
@classmethod
@functools.lru_cache(32)
def find(cls, name: str) -> tuple[Any, str] | tuple[None, None]:
    for registried_name, registry in Registry._registry_pool.items():
        if name in registry:
            return registry[name], registried_name
    return None, None
```

</details>


Searches all registries for an element with the given name. If found,

returns a tuple containing the element and the name of the registry where it
was found; otherwise, returns \`\(None, None\)\`.
### 🅼 make\_global

<details>

<summary>make\_global</summary>
```python
@classmethod
def make_global(cls) -> Registry:
    if cls._globals is not None:
        return cls._globals
    reg = cls("__global")
    for member in Registry._registry_pool.values():
        reg.merge(member, force=False)
    cls._globals = reg
    return reg
```

</details>


Creates a global \`Registry\` instance that contains all elements from all

other registries. If the global registry already exists, returns it instead
of creating a new one.
### 🅼 \_\_setitem\_\_

```python
def __setitem__(self, k: str, v: Any) -> None:
    super().__setitem__(k, v)
```
### 🅼 \_\_repr\_\_

```python
def __repr__(self) -> str:
    return _create_table(["NAME", "DIR"], [(k, v) for k, v in self.items()])
```
### 🅼 register\_module

<details>

<summary>register\_module</summary>
```python
@overload
def register_module(
    self,
    module: Callable[..., Any],
    force: bool = ...,
    _is_str: bool = ...,
    **extra_info: Any
) -> Callable[..., Any]:
```

</details>

### 🅼 register\_module

<details>

<summary>register\_module</summary>
```python
@overload
def register_module(
    self,
    module: ModuleType,
    force: bool = ...,
    _is_str: bool = ...,
    **extra_info: Any
) -> ModuleType:
```

</details>

### 🅼 register\_module

<details>

<summary>register\_module</summary>
```python
@overload
def register_module(
    self,
    module: str,
    force: bool = ...,
    _is_str: Literal[True] = ...,
    **extra_info: Any
) -> str:
```

</details>

### 🅼 register\_module

<details>

<summary>register\_module</summary>
```python
def register_module(self, module, force=False, _is_str=False, **extra_info):
    if Registry._prevent_register:
        logger.ex("Registry has been locked!!!")
        return module
    if not _is_str:
        if not (
            _is_function_or_class(module) or isinstance(module, ModuleType)
        ):
            raise TypeError(
                f"Only support function or class, but got {type(module)}"
            )
        name = _get_module_name(module)
    else:
        name = module.split(".")[-1]
    if not force and name in self:
        raise ValueError(f"The name {name} exists")
    if extra_info:
        if not hasattr(self, "extra_field"):
            raise ValueError(
                f"Registry `{self.name}` does not have `extra_field`."
            )
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
    if Registry._globals is not None and not name.startswith(_private_flag):
        Registry._globals.register_module(target, force, True, **extra_info)
    return module
```

</details>

### 🅼 register

```python
def register(
    self, force: bool = False, **extra_info: Any
) -> Callable[..., Any]:
    return functools.partial(self.register_module, force=force, **extra_info)
```

Decorator that registers a function or class with the current \`Registry\`.

Any keyword arguments provided are added to the \`extra\_info\` list for the
registered element. If \`force\` is True, overwrites any existing element with
the same name.
### 🅼 register\_all

<details>

<summary>register\_all</summary>
```python
def register_all(
    self,
    modules: Sequence[Callable[..., Any]],
    extra_info: Sequence[dict[str, Any]] | None = None,
    force: bool = False,
    _is_str: bool = False,
) -> None:
    if Registry._prevent_register:
        return
    _info = extra_info if extra_info else [{}] * len(modules)
    for module, info in zip(modules, _info):
        self.register_module(module, force=force, _is_str=_is_str, **info)
```

</details>


Registers multiple functions or classes with the current \`Registry\`.

If \`force\` is True, overwrites any existing elements with the same names.
### 🅼 get\_extra\_info

<details>

<summary>get\_extra\_info</summary>
```python
def get_extra_info(self, key: str, name: str) -> Any:
    if name not in self.extra_field:
        raise ValueError(
            f"Expected name to be one of `{self.extra_field}`, but got `{name}`."
        )
    for target_name, info in zip(self.extra_field, self.extra_info[key]):
        if name == target_name:
            return info
```

</details>

### 🅼 merge

<details>

<summary>merge</summary>
```python
def merge(
    self, others: Registry | Sequence[Registry], force: bool = False
) -> None:
    if not isinstance(others, (list, tuple, Sequence)):
        others = [others]
    for other in others:
        if not isinstance(other, Registry):
            raise TypeError(f"Expect `Registry` type, but got {type(other)}")
        modules = list(other.values())
        self.register_all(modules, force=force, _is_str=True)
```

</details>


Merge the contents of one or more other registries into the current one.

If \`force\` is True, overwrites any existing elements with the same names.
### 🅼 filter

<details>

<summary>filter</summary>
```python
def filter(
    self,
    filter_field: Sequence[str] | str,
    filter_func: Callable[[Sequence[Any]], bool] = _default_filter_func,
) -> list[str]:
    filter_field = (
        [filter_field] if isinstance(filter_field, str) else filter_field
    )
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
```

</details>


Returns a sorted list of all names in the registry for which the values of

the given extra field\(s\) pass a filtering function.
### 🅼 match

<details>

<summary>match</summary>
```python
def match(
    self,
    base_module: ModuleType,
    match_func: Callable[[str, ModuleType], bool] = _default_match_func,
    force: bool = False,
) -> None:
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
```

</details>


Registers all functions or classes from the given module that pass a matching

function. If \`match\_func\` is not provided, uses \`\_default\_match\_func\`.
### 🅼 module\_table

<details>

<summary>module\_table</summary>
```python
def module_table(
    self,
    filter: Sequence[str] | str | None = None,
    select_info: Sequence[str] | str | None = None,
    module_list: Sequence[str] | None = None,
    **table_kwargs: Any,
) -> str:
    if select_info is not None:
        select_info = (
            [select_info] if isinstance(select_info, str) else select_info
        )
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
        modules = all_modules
    modules = list(sorted(modules))
    table_headers = [f"{item}" for item in [self.name, *select_info]]
    if select_info:
        select_idx = [
            idx
            for idx, name in enumerate(self.extra_field)
            if name in select_info
        ]
    else:
        select_idx = []
    table = _create_table(
        table_headers,
        [
            (i, *[self.extra_info[i][idx] for idx in select_idx])
            for i in modules
        ],
        **table_kwargs,
    )
    table = "\n" + table
    return table
```

</details>


Returns a table containing information about each registered function or

class, filtered by name and/or extra info fields. \`select\_info\` specifies
which extra info fields to include in the table, while \`module\_list\`
specifies which modules to include \(by default, includes all modules\).
### 🅼 registry\_table

<details>

<summary>registry\_table</summary>
```python
@classmethod
def registry_table(cls, **table_kwargs) -> str:
    table_headers = ["REGISTRY"]
    table = _create_table(
        table_headers,
        list(sorted([[i] for i in cls._registry_pool])),
        **table_kwargs
    )
    table = "\n" + table
    return table
```

</details>


Returns a table containing the names of all available registries.
