---
title: _cache
sidebar_position: 3
---

## TOC

- **Functions:**
  - 🅵 [\_clear\_cache](#🅵-_clear_cache)
  - 🅵 [clear\_cache](#🅵-clear_cache) - Remove the cache folder which belongs to current workspace.
  - 🅵 [clear\_all\_cache](#🅵-clear_all_cache) - Remove the whole cache folder.
  - 🅵 [cache\_list](#🅵-cache_list) - Show cache folders.
  - 🅵 [cache\_dir](#🅵-cache_dir) - Show current cache folders.

## Functions

## 🅵 \_clear\_cache

<details>

<summary>\_clear\_cache</summary>
```python
def _clear_cache(cache_dir: str) -> None:
    if os.path.exists(cache_dir):
        import shutil

        shutil.rmtree(cache_dir)
        logger.info("Cache dir {} has been cleared!", cache_dir)
    else:
        logger.warning("Cache dir {} does not exist", cache_dir)
```

</details>

## 🅵 clear\_cache

<details>

<summary>clear\_cache</summary>
```python
@app.command()
def clear_cache() -> None:
    if not typer.confirm(
        f"Are you sure you want to clear cache of {workspace.name}? Cache dir is {workspace.cache_dir}."
    ):
        return
    _clear_cache(workspace.cache_dir)
```

</details>


Remove the cache folder which belongs to current workspace.
## 🅵 clear\_all\_cache

<details>

<summary>clear\_all\_cache</summary>
```python
@app.command()
def clear_all_cache() -> None:
    if not os.path.exists(workspace.cache_base_dir):
        logger.warning("Cache dir {} does not exist", workspace.cache_base_dir)
        return
    print(_create_table("Cache Names", os.listdir(workspace.cache_base_dir)))
    if not typer.confirm("Are you sure you want to clear all cache?"):
        return
    _clear_cache(workspace.cache_base_dir)
```

</details>


Remove the whole cache folder.
## 🅵 cache\_list

```python
@app.command()
def cache_list() -> None:
    table = _create_table("Cache Names", os.listdir(workspace.cache_base_dir))
    logger.info(table)
```

Show cache folders.
## 🅵 cache\_dir

```python
@app.command()
def cache_dir() -> None:
    print(workspace.cache_dir)
```

Show current cache folders.
