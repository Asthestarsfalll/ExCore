---
title: _constants
---

## TOC

- **Attributes:**
  - 🅰 [\_\_author\_\_](#🅰-__author__)
  - 🅰 [\_\_version\_\_](#🅰-__version__)
  - 🅰 [\_workspace\_config\_file](#🅰-_workspace_config_file)
  - 🅰 [\_registry\_cache\_file](#🅰-_registry_cache_file)
  - 🅰 [\_json\_schema\_file](#🅰-_json_schema_file)
  - 🅰 [\_class\_mapping\_file](#🅰-_class_mapping_file)
  - 🅰 [workspace](#🅰-workspace)
  - 🅰 [LOGO](#🅰-logo)
- **Classes:**
  - 🅲 [\_WorkspaceConfig](#🅲-_workspaceconfig)

## Attributes

## 🅰 \_\_author\_\_

```python
__author__ = """Asthestarsfalll"""
```

## 🅰 \_\_version\_\_

```python
__version__ = """0.1.1beta"""
```

## 🅰 \_workspace\_config\_file

```python
_workspace_config_file = """./.excore.toml"""
```

## 🅰 \_registry\_cache\_file

```python
_registry_cache_file = """registry_cache.pkl"""
```

## 🅰 \_json\_schema\_file

```python
_json_schema_file = """excore_schema.json"""
```

## 🅰 \_class\_mapping\_file

```python
_class_mapping_file = """class_mapping.json"""
```

## 🅰 workspace

```python
workspace = _WorkspaceConfig()
```

## 🅰 LOGO

```python
LOGO = """
▓█████ ▒██   ██▒ ▄████▄   ▒█████   ██▀███  ▓█████
▓█   ▀ ▒▒ █ █ ▒░▒██▀ ▀█  ▒██▒  ██▒▓██ ▒ ██▒▓█   ▀
▒███   ░░  █   ░▒▓█    ▄ ▒██░  ██▒▓██ ░▄█ ▒▒███
▒▓█  ▄  ░ █ █ ▒ ▒▓▓▄ ▄██▒▒██   ██░▒██▀▀█▄  ▒▓█  ▄
░▒████▒▒██▒ ▒██▒▒ ▓███▀ ░░ ████▓▒░░██▓ ▒██▒░▒████▒
░░ ▒░ ░▒▒ ░ ░▓ ░░ ░▒ ▒  ░░ ▒░▒░▒░ ░ ▒▓ ░▒▓░░░ ▒░ ░
 ░ ░  ░░░   ░▒ ░  ░  ▒     ░ ▒ ▒░   ░▒ ░ ▒░ ░ ░  ░
   ░    ░    ░  ░        ░ ░ ░ ▒    ░░   ░    ░
   ░  ░ ░    ░  ░ ░          ░ ░     ░        ░  ░
                ░
"""
```


## Classes

## 🅲 \_WorkspaceConfig

```python
class _WorkspaceConfig:
```


### 🅼 base\_name

```python
def base_name(self):
```
### 🅼 \_\_post\_init\_\_

```python
def __post_init__(self) -> None:
```
### 🅼 \_get\_cache\_dir

```python
def _get_cache_dir(self) -> str:
```
### 🅼 \_update\_name

```python
def _update_name(self, base_name: str) -> str:
```
### 🅼 update

```python
def update(self, _cfg: dict[Any, Any]) -> None:
```
### 🅼 dump

```python
def dump(self, path: str) -> None:
```
