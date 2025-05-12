---
title: logging
sidebar_position: 3
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
- **Classes:**
  - 🅲 [PatchedLogger](#🅲-patchedlogger)

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
    if log_record["name"] == "__main__":
        log_record["name"] = log_record["file"].name
    if log_record["function"] == "<module>":
        log_record["function"] = "\x08"
```
## 🅵 add\_logger

<details>

<summary>add\_logger</summary>
```python
def add_logger(
    name: str,
    sink: TextIO | Writable | Callable[[Message], None] | Handler,
    *,
    level: str | int | None = None,
    format: str | FormatFunction | None = None,
    filter: str | FilterFunction | FilterDict | None = None,
    colorize: bool | None = None,
    serialize: bool | None = None,
    backtrace: bool | None = None,
    diagnose: bool | None = None,
    enqueue: bool | None = None
) -> None:
    params = {k: v for k, v in locals().items() if v is not None}
    params.pop("sink")
    params.pop("name")
    id = logger.add(sink, **params)
    LOGGERS[name] = id
```

</details>

## 🅵 remove\_logger

<details>

<summary>remove\_logger</summary>
```python
def remove_logger(name: str) -> None:
    id = LOGGERS.pop(name, None)
    if id:
        logger.remove(id)
        logger.success(f"Remove logger whose name is {name}")
    else:
        logger.warning(f"Cannot find logger with name {name}")
```

</details>

## 🅵 log\_to\_file\_only

```python
def log_to_file_only(file_name: str, *args: Any, **kwargs: Any) -> None:
    logger.add(file_name, *args, **kwargs)
    logger.success(f"Log to file {file_name} only")
```
## 🅵 debug\_only

<details>

<summary>debug\_only</summary>
```python
def debug_only(*args: Any, **kwargs: Any) -> None:

    def _debug_only(record: Record) -> bool:
        return record["level"].name == "DEBUG"

    filter = kwargs.pop("filter", None)
    if filter:
        logger.warning("Override filter!!!")
    logger.remove()
    logger.add(sys.stderr, *args, format=FORMAT, filter=_debug_only, **kwargs)
    logger.debug("DEBUG ONLY!!!")
```

</details>

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
    if os.getenv("EXCORE_DEBUG"):
        logger.remove()
        logger.add(sys.stdout, format=FORMAT, level="EXCORE")
        logger.ex("Enabled excore debug")
```
## 🅵 init\_logger

<details>

<summary>init\_logger</summary>
```python
def init_logger() -> None:
    logger.add(sys.stderr, format=FORMAT)
    logger.level("SUCCESS", color="<yellow>")
    logger.level("WARNING", color="<red>")
    logger.level("IMPORT", no=45, color="<YELLOW><red><bold>")
    logger.level("EXCORE", no=9, color="<GREEN><cyan>")
    logger.imp = _call_importance
    logger.ex = _excore_debug
```

</details>


## Classes

## 🅲 PatchedLogger

```python
class PatchedLogger(Logger):
```


### 🅼 ex

```python
def ex(self, __message: str, *args: Any, **kwargs: Any) -> None:
```
### 🅼 imp

```python
def imp(self, __message: str, *args: Any, **kwargs: Any) -> None:
```
