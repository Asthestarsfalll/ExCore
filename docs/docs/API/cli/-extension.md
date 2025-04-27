---
title: _extension
---

## TOC

- **Functions:**
  - 🅵 [config\_extension](#🅵-config_extension) - Generate json_schema for onfig completion and class_mapping for class navigation.
  - 🅵 [\_generate\_typehints](#🅵-_generate_typehints)
  - 🅵 [generate\_typehints](#🅵-generate_typehints) - Generate type hints for modules and isolated objects.
  - 🅵 [\_quote](#🅵-_quote)
  - 🅵 [quote](#🅵-quote) - Quote all special keys in target config files.

## Functions

## 🅵 config\_extension

```python
@app.command()
def config_extension() -> None:
```

Generate json\_schema for onfig completion and class\_mapping for class navigation.
## 🅵 \_generate\_typehints

```python
def _generate_typehints(
    entry: str, class_name: str, info_class_name: str, config: str = ""
) -> None:
```
## 🅵 generate\_typehints

```python
@app.command()
def generate_typehints(
    entry: str = CArg(default="module_types", help="The file to generate."),
    class_name: Annotated[
        str, COp(help="The class name of type hints.")
    ] = "TypedModules",
    info_class_name: Annotated[
        str, COp(help="The class name of run_info.")
    ] = "RunInfo",
    config: Annotated[
        str, COp(help="Used generate type hints for isolated objects.")
    ] = "",
) -> None:
```

Generate type hints for modules and isolated objects.
## 🅵 \_quote

```python
def _quote(config: str, override: bool) -> None:
```
## 🅵 quote

```python
@app.command()
def quote(
    config: Annotated[str, CArg(help="Target config file or folder.")],
    override: Annotated[bool, COp(help="Whether to override configs.")] = False,
) -> None:
```

Quote all special keys in target config files.
