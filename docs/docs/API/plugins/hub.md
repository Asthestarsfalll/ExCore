---
title: hub
---

## TOC

Take and adapt from

https://github.com/MegEngine/MegEngine/blob/master/imperative/python/megengine/hub/

- **Attributes:**
  - 🅰 [DEFAULT\_BRANCH](#🅰-default_branch)
  - 🅰 [DEFAULT\_HUBCONF\_ENTRY](#🅰-default_hubconf_entry)
  - 🅰 [DEFAULT\_PROTOCOL](#🅰-default_protocol)
  - 🅰 [HUBDEPENDENCY](#🅰-hubdependency)
  - 🅰 [DEFAULT\_GIT\_HOST](#🅰-default_git_host)
  - 🅰 [HTTP\_READ\_TIMEOUT](#🅰-http_read_timeout)
  - 🅰 [HTTP\_CONNECTION\_TIMEOUT](#🅰-http_connection_timeout)
  - 🅰 [CHUNK\_SIZE](#🅰-chunk_size)
  - 🅰 [PROTOCOLS](#🅰-protocols)
- **Functions:**
  - 🅵 [cd](#🅵-cd)
  - 🅵 [download\_from\_url](#🅵-download_from_url)
  - 🅵 [\_get\_repo](#🅵-_get_repo)
  - 🅵 [\_check\_dependencies](#🅵-_check_dependencies)
  - 🅵 [load\_module](#🅵-load_module)
  - 🅵 [\_init\_hub](#🅵-_init_hub)
  - 🅵 [import\_module](#🅵-import_module)
  - 🅵 [list](#🅵-list)
  - 🅵 [load](#🅵-load)
  - 🅵 [help](#🅵-help)
- **Classes:**
  - 🅲 [RepoFetcherBase](#🅲-repofetcherbase)
  - 🅲 [GitSSHFetcher](#🅲-gitsshfetcher)
  - 🅲 [GitHTTPSFetcher](#🅲-githttpsfetcher)
  - 🅲 [pretrained](#🅲-pretrained)

## Attributes

## 🅰 DEFAULT\_BRANCH

```python
DEFAULT_BRANCH = """master"""
```

## 🅰 DEFAULT\_HUBCONF\_ENTRY

```python
DEFAULT_HUBCONF_ENTRY = """hubconf.py"""
```

## 🅰 DEFAULT\_PROTOCOL

```python
DEFAULT_PROTOCOL = """HTTPS"""
```

## 🅰 HUBDEPENDENCY

```python
HUBDEPENDENCY = """dependencies"""
```

## 🅰 DEFAULT\_GIT\_HOST

```python
DEFAULT_GIT_HOST = """github.com"""
```

## 🅰 HTTP\_READ\_TIMEOUT

```python
HTTP_READ_TIMEOUT = 120
```

## 🅰 HTTP\_CONNECTION\_TIMEOUT

```python
HTTP_CONNECTION_TIMEOUT = 5
```

## 🅰 CHUNK\_SIZE

```python
CHUNK_SIZE = 1024
```

## 🅰 PROTOCOLS

```python
PROTOCOLS = {"HTTPS": GitHTTPSFetcher, "SSH": GitSSHFetcher}
```


## Functions

## 🅵 cd

```python
def cd(target: str) -> Iterator[None]:
```
## 🅵 download\_from\_url

```python
def download_from_url(url: str, dst: str):
```
## 🅵 \_get\_repo

```python
def _get_repo(
    git_host: str,
    repo_info: str,
    use_cache: bool = False,
    commit: Optional[str] = None,
    protocol: str = DEFAULT_PROTOCOL,
) -> str:
```
## 🅵 \_check\_dependencies

```python
def _check_dependencies(module: types.ModuleType) -> None:
```
## 🅵 load\_module

```python
def load_module(name: str, path: str) -> types.ModuleType:
```
## 🅵 \_init\_hub

```python
def _init_hub(
    repo_info: str,
    git_host: str,
    hubconf_entry: str = DEFAULT_HUBCONF_ENTRY,
    use_cache: bool = True,
    commit: Optional[str] = None,
    protocol: str = DEFAULT_PROTOCOL,
):
```
## 🅵 import\_module

```python
def import_module(*args, **kwargs):
```
## 🅵 list

```python
def list(
    repo_info: str,
    git_host: str = DEFAULT_GIT_HOST,
    entry: str = DEFAULT_HUBCONF_ENTRY,
    use_cache: bool = True,
    commit: Optional[str] = None,
    protocol: str = DEFAULT_PROTOCOL,
) -> List[str]:
```
## 🅵 load

```python
def load(
    repo_info: str,
    entry: str,
    *args,
    git_host: str = DEFAULT_GIT_HOST,
    hubconf_entry: str = DEFAULT_HUBCONF_ENTRY,
    use_cache: bool = True,
    commit: Optional[str] = None,
    protocol: str = DEFAULT_PROTOCOL,
    **kwargs
) -> Any:
```
## 🅵 help

```python
def help(
    repo_info: str,
    entry: str,
    git_host: str = DEFAULT_GIT_HOST,
    hubconf_entry: str = DEFAULT_HUBCONF_ENTRY,
    use_cache: bool = True,
    commit: Optional[str] = None,
    protocol: str = DEFAULT_PROTOCOL,
) -> str:
```

## Classes

## 🅲 RepoFetcherBase

```python
class RepoFetcherBase:
```


### 🅼 fetch

```python
def fetch(
    cls,
    git_host: str,
    repo_info: str,
    use_cache: bool = False,
    commit: Optional[str] = None,
    silent: bool = True,
) -> str:
```
### 🅼 \_parse\_repo\_info

```python
def _parse_repo_info(cls, repo_info: str) -> Tuple[str, str, str]:
```
### 🅼 \_check\_git\_host

```python
def _check_git_host(cls, git_host):
```
### 🅼 \_is\_valid\_domain

```python
def _is_valid_domain(cls, s):
```
### 🅼 \_is\_valid\_host

```python
def _is_valid_host(cls, s):
```
### 🅼 \_gen\_repo\_dir

```python
def _gen_repo_dir(cls, repo_dir: str) -> str:
```
## 🅲 GitSSHFetcher

```python
class GitSSHFetcher(RepoFetcherBase):
```


### 🅼 fetch

```python
def fetch(
    cls,
    git_host: str,
    repo_info: str,
    use_cache: bool = False,
    commit: Optional[str] = None,
    silent: bool = True,
) -> str:
```
### 🅼 \_check\_clone\_pipe

```python
def _check_clone_pipe(cls, p):
```
## 🅲 GitHTTPSFetcher

```python
class GitHTTPSFetcher(RepoFetcherBase):
```


### 🅼 fetch

```python
def fetch(
    cls,
    git_host: str,
    repo_info: str,
    use_cache: bool = False,
    commit: Optional[str] = None,
    silent: bool = True,
) -> str:
```
### 🅼 \_download\_zip\_and\_extract

```python
def _download_zip_and_extract(cls, url, target_dir):
```
## 🅲 pretrained

```python
class pretrained:
```


### 🅼 \_\_init\_\_

```python
def __init__(self, url, load_func):
```
### 🅼 \_\_call\_\_

```python
def __call__(self, func):
```
