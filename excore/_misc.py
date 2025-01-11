from __future__ import annotations

import functools
from typing import Any, Callable, Sequence

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
    header: str | list[str] | tuple[str, ...] | None,
    contents: Sequence[str] | Sequence[Sequence[str]],
    prefix: str = "\n",
    **table_kwargs: Any,
) -> str:
    if len(contents) > 0 and isinstance(contents[0], str):
        contents = [(i,) for i in contents]  # type: ignore
    if header is None:
        header = ()
    if not isinstance(header, (list, tuple)):
        header = [header]
    table = tabulate(
        contents,
        headers=header,
        tablefmt="fancy_grid",
        **table_kwargs,
    )
    return prefix + table
