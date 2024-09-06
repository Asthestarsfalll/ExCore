from __future__ import annotations

import functools
from typing import Any, Callable

from tabulate import tabulate


class CacheOut:
    def __call__(self, func: Callable[..., Any]):
        @functools.wraps(func)
        def _cache(self) -> Any:
            if not hasattr(self, "cached_elem"):
                cached_elem = func(self)
                if cached_elem != self:
                    self.cached_elem = cached_elem
                return cached_elem
            return self.cached_elem

        return _cache


def _create_table(
    header: str | list[str] | tuple[str, ...],
    contents: list[str | tuple[str, ...] | list[str]],
    split: bool = True,
    prefix: str = "\n",
    **tabel_kwargs: Any,
) -> str:
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
