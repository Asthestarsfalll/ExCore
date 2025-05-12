---
title: _misc
sidebar_position: 3
---

## TOC

- **Functions:**
  - 🅵 [\_create\_table](#🅵-_create_table) - Create a formatted table from the given header and contents.
- **Classes:**
  - 🅲 [CacheOut](#🅲-cacheout) - A decorator class to cache the output of a method.

## Functions

## 🅵 \_create\_table

<details>

<summary>\_create\_table</summary>
```python
def _create_table(
    header: str | list[str] | tuple[str, ...] | None,
    contents: Sequence[str] | Sequence[Sequence[str]],
    prefix: str = "\n",
    **table_kwargs: Any
) -> str:
    if len(contents) > 0 and isinstance(contents[0], str):
        contents = [(i,) for i in contents]
    if header is None:
        header = ()
    if not isinstance(header, (list, tuple)):
        header = [header]
    table = tabulate(
        contents, headers=header, tablefmt="fancy_grid", **table_kwargs
    )
    return prefix + table
```

</details>


Create a formatted table from the given header and contents.

This function takes a header and contents, optionally a prefix, and additional
keyword arguments for table formatting. It then creates a table using the
tabulate library and prepends the specified prefix.

**Parameters:**

- **header** (str | list[str] | tuple[[str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str), ...] | [None](https://docs.python.org/3/library/constants.html#None)]]): The header for the table.
Can be a string, list of strings, tuple of strings, or None.
- **contents** ([Sequence](https://docs.python.org/3/library/typing.html#typing.Sequence)[str] | Sequence[[Sequence](https://docs.python.org/3/library/typing.html#typing.Sequence)[[str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)]]]): The contents of the table.
Can be a sequence of strings or a sequence of sequences of strings.
- **prefix** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): A prefix to prepend to the table. Default is a newline character.
- ****table_kwargs** ([Any](https://docs.python.org/3/library/typing.html#typing.Any)): Additional keyword arguments to pass to the tabulate function.

**Returns:**

- **[str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)**: A formatted string representing the table with the specified prefix.

## Classes

## 🅲 CacheOut

```python
class CacheOut:
```

A decorator class to cache the output of a method.

This class is designed to be used as a decorator for methods. It caches the
output of the decorated method in the instance's \`cached\_elem\` attribute.
If the cached value is not equal to the instance itself, it sets the cached
value and returns it. Otherwise, it simply returns the cached value.

Methods:
    \_\_call\_\_: Decorates a method to cache its output.


### 🅼 \_\_call\_\_

<details>

<summary>\_\_call\_\_</summary>
```python
def __call__(self, func: Callable[..., Any]):

    @functools.wraps(func)
    def _cache(self) -> Any:
        if not hasattr(self, "cached_elem"):
            cached_elem = func(self)
            if cached_elem != self:
                self.cached_elem = cached_elem
            return cached_elem
        return self.cached_elem

    return _cache
```

</details>


Decorates a method to cache its output.

**Parameters:**

- **func** ([Callable](https://docs.python.org/3/library/typing.html#typing.Callable)[..., [Any](https://docs.python.org/3/library/typing.html#typing.Any)]): The method to be decorated.

**Returns:**

- **[Callable](https://docs.python.org/3/library/typing.html#typing.Callable)[..., [Any](https://docs.python.org/3/library/typing.html#typing.Any)]**: The decorated method.
