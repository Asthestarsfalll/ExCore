---
title: _constants
sidebar_position: 3
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

<details>

<summary>LOGO</summary>
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

</details>



## Classes

## 🅲 \_WorkspaceConfig

<details>

<summary>\_WorkspaceConfig</summary>
```python
@dataclass
class _WorkspaceConfig:
    name: str = field(default="")
    src_dir: str = field(default="")
    base_dir: str = field(default="")
    cache_base_dir: str = field(default=osp.expanduser("~/.cache/excore/"))
    cache_dir: str = field(default="")
    registry_cache_file: str = field(default="")
    json_schema_file: str = field(default="")
    class_mapping_file: str = field(default="")
    registries: list[str] = field(default_factory=list)
    primary_fields: list[str] = field(default_factory=list)
    primary_to_registry: dict[str, str] = field(default_factory=dict)
    json_schema_fields: dict[str, str | list[str]] = field(default_factory=dict)
    props: dict[Any, Any] = field(default_factory=dict)
    excore_validate: bool = field(default=True)
    excore_manual_set: bool = field(default=True)
    excore_log_build_message: bool = field(default=False)
```

</details>



### 🅼 base\_name

```python
@property
def base_name(self):
    return osp.split(self.cache_dir)[-1]
```
### 🅼 \_\_post\_init\_\_

<details>

<summary>\_\_post\_init\_\_</summary>
```python
def __post_init__(self) -> None:
    if not osp.exists(_workspace_config_file):
        self.base_dir = os.getcwd()
        self.cache_dir = self._get_cache_dir()
        self.registry_cache_file = osp.join(
            self.cache_dir, _registry_cache_file
        )
        self.json_schema_file = osp.join(self.cache_dir, _json_schema_file)
        self.class_mapping_file = osp.join(self.cache_dir, _class_mapping_file)
        logger.warning("Please use `excore init` in your command line first")
    else:
        self.update(toml.load(_workspace_config_file))
    if os.environ.get("EXCORE_VALIDATE", "1") == "0":
        self.excore_validate = False
    if os.environ.get("EXCORE_LOG_BUILD_MESSAGE", "0") == "1":
        self.excore_log_build_message = True
    if os.environ.get("EXCORE_MANUAL_SET", "1") == "0":
        self.excore_manual_set = False
```

</details>

### 🅼 \_get\_cache\_dir

```python
def _get_cache_dir(self) -> str:
    base_name = osp.basename(osp.normpath(os.getcwd()))
    base_name = self._update_name(base_name)
    return osp.join(self.cache_base_dir, base_name)
```
### 🅼 \_update\_name

<details>

<summary>\_update\_name</summary>
```python
def _update_name(self, base_name: str) -> str:
    name = base_name
    suffix = 1
    while osp.exists(osp.join(self.cache_base_dir, name)):
        name = f"{base_name}_{suffix}"
        suffix += 1
    return name
```

</details>

### 🅼 update

```python
def update(self, _cfg: dict[Any, Any]) -> None:
```
### 🅼 dump

```python
def dump(self, path: str) -> None:
    with open(path, "w") as f:
        cfg = self.__dict__
        cfg.pop("base_dir", None)
        toml.dump(cfg, f)
```
