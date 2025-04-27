---
title: hub
sidebar_position: 3
---

Take and adapt from

https://github.com/MegEngine/MegEngine/blob/master/imperative/python/megengine/hub/

## TOC

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

<details>

<summary>cd</summary>
```python
@contextmanager
def cd(target: str) -> Iterator[None]:
    prev = os.getcwd()
    os.chdir(os.path.expanduser(target))
    try:
        yield
    finally:
        os.chdir(prev)
```

</details>

## 🅵 download\_from\_url

<details>

<summary>download\_from\_url</summary>
```python
def download_from_url(url: str, dst: str):
    resp = requests.get(url, timeout=120, stream=True)
    if resp.status_code != 200:
        raise HTTPDownloadError(
            f"An error occurred when downloading from {url}"
        )
    total_size = int(resp.headers.get("Content-Length", 0))
    _bar = tqdm(total=total_size, unit="iB", unit_scale=True)
    with open(dst, "w+b") as f:
        for chunk in resp.iter_content(CHUNK_SIZE):
            if not chunk:
                break
            _bar.update(len(chunk))
            f.write(chunk)
        _bar.close()
```

</details>

## 🅵 \_get\_repo

<details>

<summary>\_get\_repo</summary>
```python
def _get_repo(
    git_host: str,
    repo_info: str,
    use_cache: bool = False,
    commit: Optional[str] = None,
    protocol: str = DEFAULT_PROTOCOL,
) -> str:
    if protocol not in PROTOCOLS:
        raise InvalidProtocol(
            "Invalid protocol, the value should be one of {}.".format(
                ", ".join(PROTOCOLS.keys())
            )
        )
    cache_dir = os.path.expanduser(os.path.join(workspace.cache_dir, "hub"))
    with cd(cache_dir):
        fetcher = PROTOCOLS[protocol]
        repo_dir = fetcher.fetch(git_host, repo_info, use_cache, commit)
        return os.path.join(cache_dir, repo_dir)
```

</details>

## 🅵 \_check\_dependencies

<details>

<summary>\_check\_dependencies</summary>
```python
def _check_dependencies(module: types.ModuleType) -> None:
    if not hasattr(module, HUBDEPENDENCY):
        return
    dependencies = getattr(module, HUBDEPENDENCY)
    if not dependencies:
        return
    missing_deps = [m for m in dependencies if importlib.util.find_spec(m)]
    if len(missing_deps):
        raise RuntimeError(
            "Missing dependencies: {}".format(", ".join(missing_deps))
        )
```

</details>

## 🅵 load\_module

```python
def load_module(name: str, path: str) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
```
## 🅵 \_init\_hub

<details>

<summary>\_init\_hub</summary>
```python
def _init_hub(
    repo_info: str,
    git_host: str,
    hubconf_entry: str = DEFAULT_HUBCONF_ENTRY,
    use_cache: bool = True,
    commit: Optional[str] = None,
    protocol: str = DEFAULT_PROTOCOL,
):
    cache_dir = os.path.expanduser(os.path.join(workspace.cache_dir, "hub"))
    os.makedirs(cache_dir, exist_ok=True)
    absolute_repo_dir = _get_repo(
        git_host,
        repo_info,
        use_cache=use_cache,
        commit=commit,
        protocol=protocol,
    )
    sys.path.insert(0, absolute_repo_dir)
    hubmodule = load_module(
        ".".join(hubconf_entry.split(os.sep)),
        os.path.join(absolute_repo_dir, hubconf_entry),
    )
    sys.path.remove(absolute_repo_dir)
    return hubmodule
```

</details>

## 🅵 import\_module

```python
@functools.wraps(_init_hub)
def import_module(*args, **kwargs):
    return _init_hub(*args, **kwargs)
```
## 🅵 list

<details>

<summary>list</summary>
```python
def list(
    repo_info: str,
    git_host: str = DEFAULT_GIT_HOST,
    entry: str = DEFAULT_HUBCONF_ENTRY,
    use_cache: bool = True,
    commit: Optional[str] = None,
    protocol: str = DEFAULT_PROTOCOL,
) -> List[str]:
    hubmodule = _init_hub(
        repo_info, git_host, entry, use_cache, commit, protocol
    )
    return [
        _
        for _ in dir(hubmodule)
        if not _.startswith("__") and callable(getattr(hubmodule, _))
    ]
```

</details>

## 🅵 load

<details>

<summary>load</summary>
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
    **kwargs,
) -> Any:
    hubmodule = _init_hub(
        repo_info, git_host, hubconf_entry, use_cache, commit, protocol
    )
    if not hasattr(hubmodule, entry) or not callable(getattr(hubmodule, entry)):
        raise RuntimeError(f"Cannot find callable {entry} in {hubconf_entry}")
    _check_dependencies(hubmodule)
    module = getattr(hubmodule, entry)(*args, **kwargs)
    return module
```

</details>

## 🅵 help

<details>

<summary>help</summary>
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
    hubmodule = _init_hub(
        repo_info, git_host, hubconf_entry, use_cache, commit, protocol
    )
    if not hasattr(hubmodule, entry) or not callable(getattr(hubmodule, entry)):
        raise RuntimeError(f"Cannot find callable {entry} in hubconf.py")
    doc = getattr(hubmodule, entry).__doc__
    return doc
```

</details>


## Classes

## 🅲 RepoFetcherBase

```python
class RepoFetcherBase:
    pattern = re.compile(
        "^(?:[a-z0-9](?:[a-z0-9-_]{0,61}[a-z0-9])?\\.)+[a-z0-9][a-z0-9-_]{0,61}[a-z]$"
    )
```


### 🅼 fetch

<details>

<summary>fetch</summary>
```python
@classmethod
def fetch(
    cls,
    git_host: str,
    repo_info: str,
    use_cache: bool = False,
    commit: Optional[str] = None,
    silent: bool = True,
) -> str:
    raise NotImplementedError()
```

</details>

### 🅼 \_parse\_repo\_info

<details>

<summary>\_parse\_repo\_info</summary>
```python
@classmethod
def _parse_repo_info(cls, repo_info: str) -> Tuple[str, str, str]:
    try:
        branch_info = DEFAULT_BRANCH
        if ":" in repo_info:
            prefix_info, branch_info = repo_info.split(":")
        else:
            prefix_info = repo_info
        repo_owner, repo_name = prefix_info.split("/")
        return repo_owner, repo_name, branch_info
    except ValueError as exc:
        raise InvalidRepo(f"repo_info: '{repo_info}' is invalid.") from exc
```

</details>

### 🅼 \_check\_git\_host

```python
@classmethod
def _check_git_host(cls, git_host):
    return cls._is_valid_domain(git_host) or cls._is_valid_host(git_host)
```
### 🅼 \_is\_valid\_domain

<details>

<summary>\_is\_valid\_domain</summary>
```python
@classmethod
def _is_valid_domain(cls, s):
    try:
        return cls.pattern.match(s.encode("idna").decode("ascii"))
    except UnicodeError:
        return False
```

</details>

### 🅼 \_is\_valid\_host

<details>

<summary>\_is\_valid\_host</summary>
```python
@classmethod
def _is_valid_host(cls, s):
    nums = s.split(".")
    if len(nums) != 4 or any(not _.isdigit() for _ in nums):
        return False
    return all(0 <= int(_) < 256 for _ in nums)
```

</details>

### 🅼 \_gen\_repo\_dir

```python
@classmethod
def _gen_repo_dir(cls, repo_dir: str) -> str:
    return hashlib.sha1(repo_dir.encode()).hexdigest()[:16]
```
## 🅲 GitSSHFetcher

```python
class GitSSHFetcher(RepoFetcherBase):
```


### 🅼 fetch

<details>

<summary>fetch</summary>
```python
@classmethod
def fetch(
    cls,
    git_host: str,
    repo_info: str,
    use_cache: bool = False,
    commit: Optional[str] = None,
    silent: bool = True,
) -> str:
```

</details>

### 🅼 \_check\_clone\_pipe

<details>

<summary>\_check\_clone\_pipe</summary>
```python
@classmethod
def _check_clone_pipe(cls, p):
    _, err = p.communicate()
    if p.returncode:
        raise GitPullError(
            "Repo pull error, please check repo info.\n" + err.decode()
        )
```

</details>

## 🅲 GitHTTPSFetcher

```python
class GitHTTPSFetcher(RepoFetcherBase):
    HTTP_TIMEOUT = (HTTP_CONNECTION_TIMEOUT, HTTP_READ_TIMEOUT)
```


### 🅼 fetch

<details>

<summary>fetch</summary>
```python
@classmethod
def fetch(
    cls,
    git_host: str,
    repo_info: str,
    use_cache: bool = False,
    commit: Optional[str] = None,
    silent: bool = True,
) -> str:
    if not cls._check_git_host(git_host):
        raise InvalidGitHost(f"git_host: '{git_host}' is malformed.")
    repo_owner, repo_name, branch_info = cls._parse_repo_info(repo_info)
    normalized_branch_info = branch_info.replace("/", "_")
    repo_dir_raw = f"{repo_owner}_{repo_name}_{normalized_branch_info}" + (
        f"_{commit}" if commit else ""
    )
    repo_dir = (
        "_".join(__version__.split(".")) + "_" + cls._gen_repo_dir(repo_dir_raw)
    )
    archive_url = f"https://{git_host}/{repo_owner}/{repo_name}/archive/{commit or branch_info}.zip"
    if use_cache and os.path.exists(repo_dir):
        logger.debug("Cache Found in {}", repo_dir)
        return repo_dir
    shutil.rmtree(repo_dir, ignore_errors=True)
    logger.debug(f"Downloading from {archive_url} to {repo_dir}")
    cls._download_zip_and_extract(archive_url, repo_dir)
    return repo_dir
```

</details>

### 🅼 \_download\_zip\_and\_extract

<details>

<summary>\_download\_zip\_and\_extract</summary>
```python
@classmethod
def _download_zip_and_extract(cls, url, target_dir):
    resp = requests.get(url, timeout=cls.HTTP_TIMEOUT, stream=True)
    if resp.status_code != 200:
        raise HTTPDownloadError(
            f"An error occurred when downloading from {url}"
        )
    total_size = int(resp.headers.get("Content-Length", 0))
    _bar = tqdm(total=total_size, unit="iB", unit_scale=True)
    with NamedTemporaryFile("w+b") as f:
        for chunk in resp.iter_content(CHUNK_SIZE):
            if not chunk:
                break
            _bar.update(len(chunk))
            f.write(chunk)
        _bar.close()
        f.seek(0)
        with ZipFile(f) as temp_zip_f:
            zip_dir_name = temp_zip_f.namelist()[0].split("/")[0]
            temp_zip_f.extractall(".")
            shutil.move(zip_dir_name, target_dir)
```

</details>

## 🅲 pretrained

```python
class pretrained:
```


### 🅼 \_\_init\_\_

```python
def __init__(self, url, load_func):
    self.url = url
    self.load_func = load_func
```
### 🅼 \_\_call\_\_

<details>

<summary>\_\_call\_\_</summary>
```python
def __call__(self, func):

    @functools.wraps(func)
    def pretrained_model_func(pretrained=False, **kwargs):
        model = func(**kwargs)
        if pretrained:
            parts = urlparse(self.url)
            filename = os.path.basename(parts.path)
            sha256 = hashlib.sha256()
            sha256.update(self.url.encode())
            digest = sha256.hexdigest()[:6]
            filename = digest + "_" + filename
            cached_file = os.path.join(workspace.cache_dir, filename)
            download_from_url(self.url, cached_file)
            self.load_func(cached_file, model)
        return model

    return pretrained_model_func
```

</details>
