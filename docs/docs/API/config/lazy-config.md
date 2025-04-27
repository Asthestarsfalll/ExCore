---
title: lazy_config
---

## TOC

- **Classes:**
  - 🅲 [LazyConfig](#🅲-lazyconfig)

## Classes

## 🅲 LazyConfig

```python
class LazyConfig:
    hook_key: str = "ExcoreHook"
    modules_dict: dict[str, ModuleWrapper] = None
    isolated_dict: dict[str, Any] = None
```


### 🅼 \_\_init\_\_

```python
def __init__(self, config: ConfigDict) -> None:
```
### 🅼 parse

```python
def parse(self) -> None:
```
### 🅼 config

```python
@property
def config(self) -> ConfigDict:
```
### 🅼 update

```python
def update(self, cfg: LazyConfig) -> None:
```
### 🅼 build\_config\_hooks

```python
def build_config_hooks(self) -> None:
```
### 🅼 \_\_getattr\_\_

```python
def __getattr__(self, __name: str) -> Any:
```
### 🅼 build\_all

```python
def build_all(self) -> tuple[ModuleWrapper, dict[str, Any]]:
```
### 🅼 dump

```python
def dump(self, dump_path: str) -> None:
```
### 🅼 \_\_str\_\_

```python
def __str__(self) -> str:
```
