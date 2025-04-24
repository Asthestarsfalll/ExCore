---
title: _registry
---

## TOC

- **Functions:**
  - 🅵 [\_has\_import\_excore](#🅵-_has_import_excore)
  - 🅵 [\_build\_ast](#🅵-_build_ast)
  - 🅵 [\_generate\_registries](#🅵-_generate_registries)
  - 🅵 [\_detect\_assign](#🅵-_detect_assign)
  - 🅵 [\_detect\_registry\_definition](#🅵-_detect_registry_definition)
  - 🅵 [\_format](#🅵-_format)
  - 🅵 [\_parse\_registries](#🅵-_parse_registries)
  - 🅵 [\_get\_registries](#🅵-_get_registries)
  - 🅵 [\_update](#🅵-_update)
  - 🅵 [\_get\_default\_module\_name](#🅵-_get_default_module_name)
  - 🅵 [\_auto\_register](#🅵-_auto_register)
  - 🅵 [auto\_register](#🅵-auto_register) - Automatically import all modules in `src_dir` by default or `target`
  - 🅵 [primary\_fields](#🅵-primary_fields) - Show primary_fields.
  - 🅵 [registries](#🅵-registries) - Show registries.
  - 🅵 [generate\_registries](#🅵-generate_registries) - Generate registries definition code according to workspace config.

## Functions

## 🅵 \_has\_import\_excore

```python
def _has_import_excore(node) -> bool:
```
## 🅵 \_build\_ast

```python
def _build_ast(name: str) -> ast.Assign:
```
## 🅵 \_generate\_registries

```python
def _generate_registries(entry="__init__"):
```
## 🅵 \_detect\_assign

```python
def _detect_assign(node: ast.AST, definition: list) -> None:
```
## 🅵 \_detect\_registry\_definition

```python
def _detect_registry_definition() -> bool:
```
## 🅵 \_format

```python
def _format(reg_and_fields: str) -> str:
```
## 🅵 \_parse\_registries

```python
def _parse_registries(
    reg_and_fields: list[str],
) -> tuple[list[str], dict[Any, Any], dict[Any, Any]]:
```
## 🅵 \_get\_registries

```python
def _get_registries(reg_and_fields) -> list[str]:
```
## 🅵 \_update

```python
def _update(is_init: bool = True, entry: str = "__init__") -> None:
```
## 🅵 \_get\_default\_module\_name

```python
def _get_default_module_name(base: str, target: str) -> str:
```
## 🅵 \_auto\_register

```python
def _auto_register(target: str, module_name: str) -> None:
```
## 🅵 auto\_register

```python
def auto_register(
    target: Annotated[str, CArg(help="What to be registered")] = "",
) -> None:
```

Automatically import all modules in \`src\_dir\` by default or \`target\`

and register all modules, then dump to files.
## 🅵 primary\_fields

```python
def primary_fields() -> None:
```

Show primary\_fields.
## 🅵 registries

```python
def registries() -> None:
```

Show registries.
## 🅵 generate\_registries

```python
def generate_registries(
    entry: str = CArg(
        default="__init__",
        help="Used for detect or generate Registry definition code",
    )
) -> None:
```

Generate registries definition code according to workspace config.
