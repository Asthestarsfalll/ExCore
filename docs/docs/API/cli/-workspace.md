---
title: _workspace
---

## TOC

- **Functions:**
  - 🅵 [\_dump\_workspace\_config](#🅵-_dump_workspace_config)
  - 🅵 [update](#🅵-update) - Update workspace config file.
  - 🅵 [init](#🅵-init) - Initialize workspace and generate a config file.

## Functions

## 🅵 \_dump\_workspace\_config

```python
def _dump_workspace_config() -> None:
```
## 🅵 update

```python
@app.command()
def update() -> None:
```

Update workspace config file.
## 🅵 init

```python
@app.command()
def init(
    force: Annotated[
        bool, COp(help="Whether forcibly initialize workspace")
    ] = False,
    entry: Annotated[
        str, CArg(help="Used for detect or generate Registry definition code")
    ] = "__init__",
) -> None:
```

Initialize workspace and generate a config file.
