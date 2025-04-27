---
title: path_manager
sidebar_position: 3
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
- **sub_folders** ([Union](https://docs.python.org/3/library/typing.html#typing.Union)[[List](https://docs.python.org/3/library/typing.html#typing.List)[str], [DataclassProtocol](path-manager#🅲-dataclassprotocol)]]): List of sub-folders
or a dataclass representing sub-folders.
- **config_name** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): Name of the configuration directory.
- **instance_name** ([Optional](https://docs.python.org/3/library/typing.html#typing.Optional)[[str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)]): Name for the current instance directory.
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

<details>

<summary>\_\_init\_\_</summary>
```python
def __init__(
    self,
    /,
    base_path: str,
    sub_folders: list[str] | DataclassProtocol,
    config_name: str,
    instance_name: str | None = None,
    *,
    remove_if_fail: bool = False,
    sub_folder_exist_ok: bool = False,
    config_name_first: bool = False,
    return_str: bool = False,
) -> None:
    self.base_path = Path(base_path)
    self._get_sub_folders(sub_folders)
    self.config_name = Path(config_name)
    self.instance_name = Path(
        instance_name or time.strftime("%Y-%m-%d-%H-%M-%S")
    )
    self.remove_if_fail = remove_if_fail
    self.sub_exist_ok = sub_folder_exist_ok
    self.config_first = config_name_first
    self.return_str = return_str
    self._info: dict[str, Path] = {}
```

</details>

### 🅼 \_get\_sub\_folders

<details>

<summary>\_get\_sub\_folders</summary>
```python
def _get_sub_folders(self, sub_folders) -> None:
    if not isinstance(sub_folders, list):
        if not is_dataclass(sub_folders):
            raise TypeError("Only Support dataclass or list of str")
        self.sub_folders = [Path(f) for f in vars(sub_folders).values()]
    else:
        self.sub_folders = [Path(f) for f in set(sub_folders)]
```

</details>

### 🅼 mkdir

<details>

<summary>mkdir</summary>
```python
def mkdir(self) -> None:
    self.base_path.mkdir(exist_ok=True)
    for f in self.sub_folders:
        logger.ex(f"Create sub_folders {f}")
        if self.config_first:
            sub = self.base_path / self.config_name / f
        else:
            sub = self.base_path / f / self.config_name
        sub = sub / self.instance_name
        sub.mkdir(parents=True, exist_ok=self.sub_exist_ok)
        self._info[str(f)] = sub
```

</details>


Create the base directory and sub-folders according to the specified configuration.
### 🅼 get

```python
def get(self, name: str) -> Path | str | None:
    path = self._info.get(name, None)
    if self.return_str:
        return str(path)
    return path
```

Retrieve the path for a specific sub-folder by name.
### 🅼 init

```python
def init(self) -> None:
    self.mkdir()
```

Initialize the path manager by creating required directories.
### 🅼 final

```python
def final(self) -> None:
    self.remove_all()
```

Perform final actions like removing all directories when exiting the context.
### 🅼 remove\_all

```python
def remove_all(self) -> None:
    for f in self._info.values():
        logger.info(f"Remove sub_folders {f}")
        shutil.rmtree(str(f))
```

Remove all the previously created directories.
### 🅼 \_\_enter\_\_

```python
def __enter__(self) -> Self:
    return self
```
### 🅼 \_\_exit\_\_

```python
def __exit__(self, exc_type, exc_value, traceback) -> bool:
    if exc_type is not None:
        self.final()
        return False
    return True
```
