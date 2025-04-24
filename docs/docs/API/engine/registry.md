---
title: registry
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
```
## 🅵 \_is\_function\_or\_class

```python
def _is_function_or_class(module: Any) -> bool:
```
## 🅵 \_default\_filter\_func

```python
def _default_filter_func(values: Sequence[Any]) -> bool:
```
## 🅵 \_default\_match\_func

```python
def _default_match_func(m: str, base_module: ModuleType) -> bool:
```
## 🅵 \_get\_module\_name

```python
def _get_module_name(m: ModuleType | _ClassType | FunctionType) -> str:
```
## 🅵 load\_registries

```python
def load_registries() -> None:
```

## Classes

## 🅲 RegistryMeta

```python
class RegistryMeta(type):
```


### 🅼 \_\_call\_\_

```python
def __call__(cls, name: str, **kwargs: Any) -> Registry:
```

Assert only call \`\_\_init\_\_\` once
## 🅲 Registry

```python
class Registry(dict):
```

A registry that stores functions and classes by name.

**Attributes:**

- **name** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): The name of the registry.
- **extra_field** (str|Sequence[str]|None): A field or fields that can be
used to store additional information about each function or class in the
registry.
- **extra_info** (dict[str, list[Any]]): A dictionary that maps each registered name
to a list of extra values associated with that name \(if any\).
- **_globals** (Registry|None): A static variable that stores a global registry
containing all functions and classes registered using Registry.


### 🅼 \_\_init\_\_

```python
def __init__(name: str, extra_field: str | Sequence[str] | None = None) -> None:
```
### 🅼 dump

```python
def dump(cls, update: bool = False) -> None:
```
### 🅼 load

```python
def load(cls) -> None:
```
### 🅼 lock\_register

```python
def lock_register(cls) -> None:
```
### 🅼 unlock\_register

```python
def unlock_register(cls) -> None:
```
### 🅼 get\_registry

```python
def get_registry(cls, name: str, default: Any = None) -> Registry:
```

Returns the \`Registry\` instance with the given name, or \`default\` if no such

registry exists.
### 🅼 find

```python
def find(cls, name: str) -> tuple[Any, str] | tuple[None, None]:
```

Searches all registries for an element with the given name. If found,

returns a tuple containing the element and the name of the registry where it
was found; otherwise, returns \`\(None, None\)\`.
### 🅼 make\_global

```python
def make_global(cls) -> Registry:
```

Creates a global \`Registry\` instance that contains all elements from all

other registries. If the global registry already exists, returns it instead
of creating a new one.
### 🅼 \_\_setitem\_\_

```python
def __setitem__(self, k: str, v: Any) -> None:
```
### 🅼 \_\_repr\_\_

```python
def __repr__(self) -> str:
```
### 🅼 register\_module

```python
def register_module(
    self,
    module: Callable[..., Any],
    force: bool = ...,
    _is_str: bool = ...,
    **extra_info: Any
) -> Callable[..., Any]:
```
### 🅼 register\_module

```python
def register_module(
    self,
    module: ModuleType,
    force: bool = ...,
    _is_str: bool = ...,
    **extra_info: Any
) -> ModuleType:
```
### 🅼 register\_module

```python
def register_module(
    self,
    module: str,
    force: bool = ...,
    _is_str: Literal[True] = ...,
    **extra_info: Any
) -> str:
```
### 🅼 register\_module

```python
def register_module(self, module, force=False, _is_str=False, **extra_info):
```
### 🅼 register

```python
def register(
    self, force: bool = False, **extra_info: Any
) -> Callable[..., Any]:
```

Decorator that registers a function or class with the current \`Registry\`.

Any keyword arguments provided are added to the \`extra\_info\` list for the
registered element. If \`force\` is True, overwrites any existing element with
the same name.
### 🅼 register\_all

```python
def register_all(
    self,
    modules: Sequence[Callable[..., Any]],
    extra_info: Sequence[dict[str, Any]] | None = None,
    force: bool = False,
    _is_str: bool = False,
) -> None:
```

Registers multiple functions or classes with the current \`Registry\`.

If \`force\` is True, overwrites any existing elements with the same names.
### 🅼 get\_extra\_info

```python
def get_extra_info(self, key: str, name: str) -> Any:
```
### 🅼 merge

```python
def merge(
    self, others: Registry | Sequence[Registry], force: bool = False
) -> None:
```

Merge the contents of one or more other registries into the current one.

If \`force\` is True, overwrites any existing elements with the same names.
### 🅼 filter

```python
def filter(
    self,
    filter_field: Sequence[str] | str,
    filter_func: Callable[[Sequence[Any]], bool] = _default_filter_func,
) -> list[str]:
```

Returns a sorted list of all names in the registry for which the values of

the given extra field\(s\) pass a filtering function.
### 🅼 match

```python
def match(
    self,
    base_module: ModuleType,
    match_func: Callable[[str, ModuleType], bool] = _default_match_func,
    force: bool = False,
) -> None:
```

Registers all functions or classes from the given module that pass a matching

function. If \`match\_func\` is not provided, uses \`\_default\_match\_func\`.
### 🅼 module\_table

```python
def module_table(
    self,
    filter: Sequence[str] | str | None = None,
    select_info: Sequence[str] | str | None = None,
    module_list: Sequence[str] | None = None,
    **table_kwargs: Any
) -> str:
```

Returns a table containing information about each registered function or

class, filtered by name and/or extra info fields. \`select\_info\` specifies
which extra info fields to include in the table, while \`module\_list\`
specifies which modules to include \(by default, includes all modules\).
### 🅼 registry\_table

```python
def registry_table(cls, **table_kwargs) -> str:
```

Returns a table containing the names of all available registries.
