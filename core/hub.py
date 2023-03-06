"""
Take and adapt from
    https://github.com/MegEngine/MegEngine/blob/master/imperative/python/megengine/hub/
"""
import functools
import hashlib
import importlib
import os
import re
import shutil
import subprocess
import sys
import types
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from typing import Any, Iterator, List, Optional, Tuple
from urllib.parse import urlparse
from zipfile import ZipFile

import requests
from tqdm import tqdm

from .constants import __version__, _cache_dir
from .exceptions import (
    GitCheckoutError,
    GitPullError,
    HTTPDownloadError,
    InvalidGitHost,
    InvalidProtocol,
    InvalidRepo,
)
from .logger import logger

__all__ = [
    "list",
    "load",
    "help",
    "pretrained",
    "import_module",
    "download_from_url",
]

DEFAULT_BRANCH = "master"
DEFAULT_HUBCONF_ENTRY = "hubconf.py"
DEFAULT_PROTOCOL = "HTTPS"
HUBDEPENDENCY = "dependencies"
DEFAULT_GIT_HOST = "github.com"
HTTP_READ_TIMEOUT = 120
HTTP_CONNECTION_TIMEOUT = 5
CHUNK_SIZE = 1024


@contextmanager
def cd(target: str) -> Iterator[None]:
    prev = os.getcwd()
    os.chdir(os.path.expanduser(target))
    try:
        yield
    finally:
        os.chdir(prev)


class RepoFetcherBase:
    pattern = re.compile(
        r"^(?:[a-z0-9]"  # First character of the domain
        r"(?:[a-z0-9-_]{0,61}[a-z0-9])?\.)"  # Sub domain + hostname
        r"+[a-z0-9][a-z0-9-_]{0,61}"  # First 61 characters of the gTLD
        r"[a-z]$"  # Last character of the gTLD
    )

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
        except ValueError:
            raise InvalidRepo("repo_info: '{}' is invalid.".format(repo_info))

    @classmethod
    def _check_git_host(cls, git_host):
        return cls._is_valid_domain(git_host) or cls._is_valid_host(git_host)

    @classmethod
    def _is_valid_domain(cls, s):
        try:
            return cls.pattern.match(s.encode("idna").decode("ascii"))
        except UnicodeError:
            return False

    @classmethod
    def _is_valid_host(cls, s):
        nums = s.split(".")
        if len(nums) != 4 or any(not _.isdigit() for _ in nums):
            return False
        return all(0 <= int(_) < 256 for _ in nums)

    @classmethod
    def _gen_repo_dir(cls, repo_dir: str) -> str:
        return hashlib.sha1(repo_dir.encode()).hexdigest()[:16]


class GitSSHFetcher(RepoFetcherBase):
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
            raise InvalidGitHost("git_host: '{}' is malformed.".format(git_host))

        repo_owner, repo_name, branch_info = cls._parse_repo_info(repo_info)
        normalized_branch_info = branch_info.replace("/", "_")
        repo_dir_raw = "{}_{}_{}".format(repo_owner, repo_name, normalized_branch_info) + (
            "_{}".format(commit) if commit else ""
        )
        repo_dir = "_".join(__version__.split(".")) + "_" + cls._gen_repo_dir(repo_dir_raw)
        git_url = "git@{}:{}/{}.git".format(git_host, repo_owner, repo_name)

        if use_cache and os.path.exists(repo_dir):  # use cache
            logger.debug("Cache Found in {}", repo_dir)
            return repo_dir

        shutil.rmtree(repo_dir, ignore_errors=True)  # ignore and clear cache

        logger.debug(
            "Git Clone from Repo:{} Branch: {} to {}",
            git_url,
            normalized_branch_info,
            repo_dir,
        )

        kwargs = {"stderr": subprocess.PIPE, "stdout": subprocess.PIPE} if silent else {}
        if commit is None:
            # shallow clone repo by branch/tag
            p = subprocess.Popen(
                [
                    "git",
                    "clone",
                    "-b",
                    normalized_branch_info,
                    git_url,
                    repo_dir,
                    "--depth=1",
                ],
                **kwargs,
            )
            cls._check_clone_pipe(p)
        else:
            # clone repo and checkout to commit_id
            p = subprocess.Popen(["git", "clone", git_url, repo_dir], **kwargs)
            cls._check_clone_pipe(p)

            with cd(repo_dir):
                logger.debug("git checkout to {}", commit)
                p = subprocess.Popen(["git", "checkout", commit], **kwargs)
                _, err = p.communicate()
                if p.returncode:
                    shutil.rmtree(repo_dir, ignore_errors=True)
                    raise GitCheckoutError(
                        "Git checkout error, please check the commit id.\n" + err.decode()
                    )
        with cd(repo_dir):
            shutil.rmtree(".git")

        return repo_dir

    @classmethod
    def _check_clone_pipe(cls, p):
        _, err = p.communicate()
        if p.returncode:
            raise GitPullError("Repo pull error, please check repo info.\n" + err.decode())


class GitHTTPSFetcher(RepoFetcherBase):
    HTTP_TIMEOUT = (HTTP_CONNECTION_TIMEOUT, HTTP_READ_TIMEOUT)

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
            raise InvalidGitHost("git_host: '{}' is malformed.".format(git_host))

        repo_owner, repo_name, branch_info = cls._parse_repo_info(repo_info)
        normalized_branch_info = branch_info.replace("/", "_")
        repo_dir_raw = "{}_{}_{}".format(repo_owner, repo_name, normalized_branch_info) + (
            "_{}".format(commit) if commit else ""
        )
        repo_dir = "_".join(__version__.split(".")) + "_" + cls._gen_repo_dir(repo_dir_raw)
        archive_url = "https://{}/{}/{}/archive/{}.zip".format(
            git_host, repo_owner, repo_name, commit or branch_info
        )

        if use_cache and os.path.exists(repo_dir):  # use cache
            logger.debug("Cache Found in {}", repo_dir)
            return repo_dir

        shutil.rmtree(repo_dir, ignore_errors=True)  # ignore and clear cache

        logger.debug("Downloading from {} to {}".format(archive_url, repo_dir))
        cls._download_zip_and_extract(archive_url, repo_dir)

        return repo_dir

    @classmethod
    def _download_zip_and_extract(cls, url, target_dir):
        resp = requests.get(url, timeout=cls.HTTP_TIMEOUT, stream=True)
        if resp.status_code != 200:
            raise HTTPDownloadError("An error occurred when downloading from {}".format(url))

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


PROTOCOLS = {
    "HTTPS": GitHTTPSFetcher,
    "SSH": GitSSHFetcher,
}


def download_from_url(url: str, dst: str):
    resp = requests.get(url, timeout=120, stream=True)
    if resp.status_code != 200:
        raise HTTPDownloadError("An error occurred when downloading from {}".format(url))

    total_size = int(resp.headers.get("Content-Length", 0))
    _bar = tqdm(total=total_size, unit="iB", unit_scale=True)

    with open(dst, "w+b") as f:
        for chunk in resp.iter_content(CHUNK_SIZE):
            if not chunk:
                break
            _bar.update(len(chunk))
            f.write(chunk)
        _bar.close()


def _get_repo(
    git_host: str,
    repo_info: str,
    use_cache: bool = False,
    commit: Optional[str] = None,
    protocol: str = DEFAULT_PROTOCOL,
) -> str:
    if protocol not in PROTOCOLS:
        raise InvalidProtocol(
            "Invalid protocol, the value should be one of {}.".format(", ".join(PROTOCOLS.keys()))
        )
    cache_dir = os.path.expanduser(os.path.join(_cache_dir, "hub"))
    with cd(cache_dir):
        fetcher = PROTOCOLS[protocol]
        repo_dir = fetcher.fetch(git_host, repo_info, use_cache, commit)
        return os.path.join(cache_dir, repo_dir)


def _check_dependencies(module: types.ModuleType) -> None:
    if not hasattr(module, HUBDEPENDENCY):
        return

    dependencies = getattr(module, HUBDEPENDENCY)
    if not dependencies:
        return
    missing_deps = [m for m in dependencies if importlib.util.find_spec(m)]
    if len(missing_deps):
        raise RuntimeError("Missing dependencies: {}".format(", ".join(missing_deps)))


def load_module(name: str, path: str) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _init_hub(
    repo_info: str,
    git_host: str,
    entry: str = DEFAULT_HUBCONF_ENTRY,
    use_cache: bool = True,
    commit: Optional[str] = None,
    protocol: str = DEFAULT_PROTOCOL,
):
    cache_dir = os.path.expanduser(os.path.join(_cache_dir, "hub"))
    os.makedirs(cache_dir, exist_ok=True)
    absolute_repo_dir = _get_repo(
        git_host, repo_info, use_cache=use_cache, commit=commit, protocol=protocol
    )
    sys.path.insert(0, absolute_repo_dir)
    hubmodule = load_module(entry, os.path.join(absolute_repo_dir, entry))
    sys.path.remove(absolute_repo_dir)

    return hubmodule


@functools.wraps(_init_hub)
def import_module(*args, **kwargs):
    return _init_hub(*args, **kwargs)


def list(
    repo_info: str,
    git_host: str = DEFAULT_GIT_HOST,
    entry: str = DEFAULT_HUBCONF_ENTRY,
    use_cache: bool = True,
    commit: Optional[str] = None,
    protocol: str = DEFAULT_PROTOCOL,
) -> List[str]:
    hubmodule = _init_hub(repo_info, git_host, entry, use_cache, commit, protocol)
    return [_ for _ in dir(hubmodule) if not _.startswith("__") and callable(getattr(hubmodule, _))]


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
    hubmodule = _init_hub(repo_info, git_host, hubconf_entry, use_cache, commit, protocol)

    if not hasattr(hubmodule, entry) or not callable(getattr(hubmodule, entry)):
        raise RuntimeError("Cannot find callable {} in hubconf.py".format(entry))

    _check_dependencies(hubmodule)

    module = getattr(hubmodule, entry)(*args, **kwargs)
    return module


def help(
    repo_info: str,
    entry: str,
    git_host: str = DEFAULT_GIT_HOST,
    hubconf_entry: str = DEFAULT_HUBCONF_ENTRY,
    use_cache: bool = True,
    commit: Optional[str] = None,
    protocol: str = DEFAULT_PROTOCOL,
) -> str:
    hubmodule = _init_hub(repo_info, git_host, hubconf_entry, use_cache, commit, protocol)

    if not hasattr(hubmodule, entry) or not callable(getattr(hubmodule, entry)):
        raise RuntimeError("Cannot find callable {} in hubconf.py".format(entry))

    doc = getattr(hubmodule, entry).__doc__
    return doc


class pretrained:  # noqa
    def __init__(self, url, load_func):
        self.url = url
        self.load_func = load_func

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

                cached_file = os.path.join(_cache_dir, filename)
                download_from_url(self.url, cached_file)
                self.load_func(cached_file, model)
            return model

        return pretrained_model_func
