---
title: action
---

## TOC

Copy and adapt from mmengine/config/config.py

- **Classes:**
  - 🅲 [DictAction](#🅲-dictaction) - argparse action to split an argument into KEY=VALUE form

## Classes

## 🅲 DictAction

```python
class DictAction(Action):
```

argparse action to split an argument into KEY=VALUE form

on the first = and append to a dictionary. List options can
be passed as comma separated values, i.e 'KEY=V1,V2,V3', or with explicit
brackets, i.e. 'KEY=\[V1,V2,V3\]'. It also support nested brackets to build
list/tuple values. e.g. 'KEY=\[\(V1,V2\),\(V3,V4\)\]'


### 🅼 \_\_init\_\_

```python
def __init__(
    self,
    option_strings,
    dest,
    nargs=None,
    const=None,
    default=None,
    type=None,
    choices=None,
    required=False,
    help=None,
    metavar=None,
):
```
### 🅼 \_parse\_int\_float\_bool

```python
@staticmethod
def _parse_int_float_bool(val: str) -> int | float | bool | Any:
```

parse int/float/bool value in the string.
### 🅼 \_parse\_iterable

```python
@staticmethod
def _parse_iterable(val: str) -> list | tuple | Any:
```

Parse iterable values in the string.

All elements inside '\(\)' or '\[\]' are treated as iterable values.

**Parameters:**

- **val** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): Value string.

**Returns:**

- **[list](https://docs.python.org/3/library/stdtypes.html#lists) | [tuple](https://docs.python.org/3/library/stdtypes.html#tuples) | [Any](https://docs.python.org/3/library/typing.html#typing.Any)**: The expanded list or tuple from the string,
or single value if no iterable values are found.

**Examples:**

```python
>>> DictAction._parse_iterable('1,2,3')
[1, 2, 3]
>>> DictAction._parse_iterable('[a, b, c]')
['a', 'b', 'c']
>>> DictAction._parse_iterable('[(1, 2, 3), [a, b], c]')
[(1, 2, 3), ['a', 'b'], 'c']
```
### 🅼 \_set\_dict

```python
def _set_dict(self, key, value):
```
### 🅼 \_\_call\_\_

```python
def __call__(
    self,
    parser: ArgumentParser,
    namespace: Namespace,
    values: str | Sequence[Any] | None,
    option_string: str | None = None,
):
```

Parse Variables in string and add them into argparser.

**Parameters:**

- **parser** (ArgumentParser): Argument parser.
- **namespace** (Namespace): Argument namespace.
- **values** (Union[str, Sequence[Any], None]): Argument string.
- **option_string** (list[str]): Option string.
Defaults to None.
