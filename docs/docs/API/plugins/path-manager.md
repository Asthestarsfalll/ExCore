---
title: path_manager
---

## TOC

- **Classes:**
  - 🅲 [DataclassProtocol](#🅲-dataclassprotocol)
  - 🅲 [PathManager](#🅲-pathmanager) - Manage paths in a structured manner for creating directories, if the scoped functions fail,

## Classes

## 🅲 DataclassProtocol

```python
class DataclassProtocol(Protocol):
    __dataclass_fields__: dict = None
    __dataclass_params__: dict = None
    __post_init__: Callable | None = None
```
## 🅲 PathManager

```python
class PathManager:
```

Manage paths in a structured manner for creating directories, if the scoped functions fail,

it can automatically delete the created directories.

**Parameters:**

- **base_path** (Path): The base path under which sub-folders will be created.
- **sub_folders** (Union[List[str], DataclassProtocol]): List of sub-folders
or a dataclass representing sub-folders.
- **config_name** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): Name of the configuration directory.
- **instance_name** (Optional[str]): Name for the current instance directory.
Defaults to the current timestamp.
- **remove_if_fail** ([bool](https://docs.python.org/3/library/stdtypes.html#boolean-values)): Flag to indicate whether to remove directories if creation fails.
Defaults to False.
- **sub_folder_exist_ok** ([bool](https://docs.python.org/3/library/stdtypes.html#boolean-values)): Flag to specify if existing sub-folders are allowed.
Defaults to False.
- **config_name_first** ([bool](https://docs.python.org/3/library/stdtypes.html#boolean-values)): Flag to determine if config name should be placed first in
the directory path. Defaults to False.
- **return_str** ([bool](https://docs.python.org/3/library/stdtypes.html#boolean-values)) (default to `False`): Flag to indicate if string paths should be returned. Defaults to False.

**Examples:**

```python
# Create a PathManager instance
with PathManager("/path/to/root", ["folder1", "folder2"], "config_dir") as pm:
    folder1_path = pm.get("folder1")
    folder2_path = pm.get("folder2")
    do_sth(folder1_path, folder2_path)
    train()

# Use dataclass
@dataclass
class SubPath:
    tensorboard: str = "tensorboard"
    ckpt: str = "checkpoints"
    logs: str = "logs"
path_info = SubPath()
with PathManager("/path/to/root", ["folder1", "folder2"], "config_dir") as pm:
    do_sth(path_info.logs)
    train()
```


### 🅼 \_\_init\_\_

```python
def __init__(
    base_path: str,
    sub_folders: list[str] | DataclassProtocol,
    config_name: str,
    instance_name: str | None = None,
    remove_if_fail: bool = False,
    sub_folder_exist_ok: bool = False,
    config_name_first: bool = False,
    return_str: bool = False,
) -> None:
```
### 🅼 \_get\_sub\_folders

```python
def _get_sub_folders(self, sub_folders) -> None:
```
### 🅼 mkdir

```python
def mkdir(self) -> None:
```

Create the base directory and sub-folders according to the specified configuration.
### 🅼 get

```python
def get(self, name: str) -> Path | str | None:
```

Retrieve the path for a specific sub-folder by name.
### 🅼 init

```python
def init(self) -> None:
```

Initialize the path manager by creating required directories.
### 🅼 final

```python
def final(self) -> None:
```

Perform final actions like removing all directories when exiting the context.
### 🅼 remove\_all

```python
def remove_all(self) -> None:
```

Remove all the previously created directories.
### 🅼 \_\_enter\_\_

```python
def __enter__(self) -> Self:
```
### 🅼 \_\_exit\_\_

```python
def __exit__(self, exc_type, exc_value, traceback) -> bool:
```
