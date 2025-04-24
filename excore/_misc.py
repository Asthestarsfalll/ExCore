from __future__ import annotations

import functools
from collections.abc import Sequence
from typing import Any, Callable

from tabulate import tabulate


class CacheOut:
    """
    A decorator class to cache the output of a method.

    This class is designed to be used as a decorator for methods. It caches the
    output of the decorated method in the instance's `cached_elem` attribute.
    If the cached value is not equal to the instance itself, it sets the cached
    value and returns it. Otherwise, it simply returns the cached value.

    Methods:
        __call__: Decorates a method to cache its output.
    """

    def __call__(self, func: Callable[..., Any]):
        """
        Decorates a method to cache its output.

        Args:
            func (Callable[..., Any]): The method to be decorated.

        Returns:
            Callable[..., Any]: The decorated method.
        """

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
    """
    Create a formatted table from the given header and contents.

    This function takes a header and contents, optionally a prefix, and additional
    keyword arguments for table formatting. It then creates a table using the
    tabulate library and prepends the specified prefix.

    Args:
        header (str | list[str] | tuple[str, ...] | None): The header for the table.
            Can be a string, list of strings, tuple of strings, or None.
        contents (Sequence[str] | Sequence[Sequence[str]]): The contents of the table.
            Can be a sequence of strings or a sequence of sequences of strings.
        prefix (str): A prefix to prepend to the table. Default is a newline character.
        **table_kwargs (Any): Additional keyword arguments to pass to the tabulate function.

    Returns:
        str: A formatted string representing the table with the specified prefix.
    """
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
