import functools
import threading
import time

from tabulate import tabulate


class CacheOut:
    def __call__(self, func):
        @functools.wraps(func)
        def _cache(self):
            if not hasattr(self, "cached_elem"):
                cached_elem = func(self)
                if cached_elem != self:
                    self.cached_elem = cached_elem
                return cached_elem
            return self.cached_elem

        return _cache


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
