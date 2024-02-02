import functools
import threading
import time

from tabulate import tabulate


class CacheOut:
    def __call__(self, func):
        @functools.wraps(func)
        def _cache(self):
            if not hasattr(self, "cached_elem"):
                self.cached_elem = func(self)
            return self.cached_elem

        return _cache


class FileLock:
    def __init__(self, file_path, timeout=15):
        self.file_path = file_path
        self.timeout = timeout
        self.lock = threading.Lock()

    def __enter__(self):
        start_time = time.time()
        while not self.lock.acquire(False):
            if time.time() - start_time >= self.timeout:
                raise TimeoutError("Failed to acquire lock on file")
            time.sleep(0.1)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.lock.release()


def _create_table(header, contents, split=True, prefix="\n", **tabel_kwargs):
    if split:
        contents = [(i,) for i in contents]
    if header is None:
        header = ()
    if not isinstance(header, (list, tuple)):
        header = [header]
    table = tabulate(
        contents,
        headers=header,
        tablefmt="fancy_grid",
        **tabel_kwargs,
    )
    return prefix + table
