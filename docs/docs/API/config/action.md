---
title: action
sidebar_position: 3
---

Copy and adapt from mmengine/config/config.py

## TOC

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

<details>

<summary>\_\_init\_\_</summary>
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
    self._dict = {}
```

</details>

### 🅼 \_parse\_int\_float\_bool

<details>

<summary>\_parse\_int\_float\_bool</summary>
```python
@staticmethod
def _parse_int_float_bool(val: str) -> int | float | bool | Any:
    try:
        return int(val)
    except ValueError:

    try:
        return float(val)
    except ValueError:

    if val.lower() in ["true", "false"]:
        return val.lower() == "true"
    if val == "None":
        return None
    return val
```

</details>


parse int/float/bool value in the string.
### 🅼 \_parse\_iterable

<details>

<summary>\_parse\_iterable</summary>
```python
@staticmethod
def _parse_iterable(val: str) -> list | tuple | Any:

    def find_next_comma(string):
        """Find the position of next comma in the string.

        If no ',' is found in the string, return the string length. All
        chars inside '()' and '[]' are treated as one element and thus ','
        inside these brackets are ignored.
        """
        assert string.count("(") == string.count(")") and string.count(
            "["
        ) == string.count("]"), f"Imbalanced brackets exist in {string}"
        end = len(string)
        for idx, char in enumerate(string):
            pre = string[:idx]
            if (
                char == ","
                and pre.count("(") == pre.count(")")
                and pre.count("[") == pre.count("]")
            ):
                end = idx
                break
        return end

    val = val.strip("'\"").replace(" ", "")
    is_tuple = False
    if val.startswith("(") and val.endswith(")"):
        is_tuple = True
        val = val[1:-1]
    elif val.startswith("[") and val.endswith("]"):
        val = val[1:-1]
    elif "," not in val:
        return DictAction._parse_int_float_bool(val)
    values = []
    while len(val) > 0:
        comma_idx = find_next_comma(val)
        element = DictAction._parse_iterable(val[:comma_idx])
        values.append(element)
        val = val[comma_idx + 1 :]
    if is_tuple:
        return tuple(values)
    return values
```

</details>


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

<details>

<summary>\_set\_dict</summary>
```python
def _set_dict(self, key, value):
    keys = key.split(".")
    d = self._dict
    for k in keys[:-1]:
        if k in d:
            d = d[k]
        else:
            d[k] = {}
            d = d[k]
    d[keys[-1]] = value
```

</details>

### 🅼 \_\_call\_\_

<details>

<summary>\_\_call\_\_</summary>
```python
def __call__(
    self,
    parser: ArgumentParser,
    namespace: Namespace,
    values: str | Sequence[Any] | None,
    option_string: str | None = None,
):
    self._dict = copy.copy(getattr(namespace, self.dest, None) or {})
    if values is not None:
        for kv in values:
            key, val = kv.split("=", maxsplit=1)
            self._set_dict(key, self._parse_iterable(val))
    setattr(namespace, self.dest, self._dict)
```

</details>


Parse Variables in string and add them into argparser.

**Parameters:**

- **parser** (ArgumentParser): Argument parser.
- **namespace** (Namespace): Argument namespace.
- **values** ([Union](https://docs.python.org/3/library/typing.html#typing.Union)[[str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str), [Sequence](https://docs.python.org/3/library/typing.html#typing.Sequence)[[Any](https://docs.python.org/3/library/typing.html#typing.Any)], [None](https://docs.python.org/3/library/constants.html#None)]): Argument string.
- **option_string** ([list](https://docs.python.org/3/library/stdtypes.html#lists)[[str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)]): Option string.
Defaults to None.
