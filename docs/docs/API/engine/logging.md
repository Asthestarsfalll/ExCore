---
title: logging
---

## TOC

- **Attributes:**
  - 🅰 [LOGGERS](#🅰-loggers)
  - 🅰 [FORMAT](#🅰-format)
  - 🅰 [logger](#🅰-logger) - type: ignore
- **Functions:**
  - 🅵 [\_trace\_patcher](#🅵-_trace_patcher)
  - 🅵 [add\_logger](#🅵-add_logger)
  - 🅵 [remove\_logger](#🅵-remove_logger)
  - 🅵 [log\_to\_file\_only](#🅵-log_to_file_only)
  - 🅵 [debug\_only](#🅵-debug_only)
  - 🅵 [\_call\_importance](#🅵-_call_importance)
  - 🅵 [\_excore\_debug](#🅵-_excore_debug)
  - 🅵 [\_enable\_excore\_debug](#🅵-_enable_excore_debug)
  - 🅵 [init\_logger](#🅵-init_logger)

## Attributes

## 🅰 LOGGERS

```python
LOGGERS: dict[str, int] = {}
```

## 🅰 FORMAT

```python
FORMAT = """<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>"""
```

## 🅰 logger

```python
logger: PatchedLogger = _logger.patch(_trace_patcher) #type: ignore
```


## Functions

## 🅵 \_trace\_patcher

```python
def _trace_patcher(log_record):
```
## 🅵 add\_logger

```python
def add_logger(
    name: str,
    sink: TextIO | Writable | Callable[[Message], None] | Handler,
    level: str | int | None = None,
    format: str | FormatFunction | None = None,
    filter: str | FilterFunction | FilterDict | None = None,
    colorize: bool | None = None,
    serialize: bool | None = None,
    backtrace: bool | None = None,
    diagnose: bool | None = None,
    enqueue: bool | None = None,
) -> None:
```
## 🅵 remove\_logger

```python
def remove_logger(name: str) -> None:
```
## 🅵 log\_to\_file\_only

```python
def log_to_file_only(file_name: str, *args: Any, **kwargs: Any) -> None:
```
## 🅵 debug\_only

```python
def debug_only(*args: Any, **kwargs: Any) -> None:
```
## 🅵 \_call\_importance

```python
def _call_importance(__message: str, *args: Any, **kwargs: Any) -> None:
```
## 🅵 \_excore\_debug

```python
def _excore_debug(__message: str, *args: Any, **kwargs: Any) -> None:
```
## 🅵 \_enable\_excore\_debug

```python
def _enable_excore_debug() -> None:
```
## 🅵 init\_logger

```python
def init_logger() -> None:
```
