import sys
from typing import Callable

import pytest
from test_config_extention import _assert

from excore import Registry
from excore.config._json_schema import parse_registry

S = Registry("S")


class Tmp:
    pass


class Tmp2:
    pass


t = Tmp()

if sys.version_info >= (3, 10, 0):

    @S.register()
    class B:
        def __init__(
            self,
            i: int,
            s: str,
            f: float,
            d: dict,
            obj: Tmp,
            c: Callable,
            uni1: int | float,
            uni2: int | str,
            uni3: Tmp | Tmp2,
            tup: tuple[int, str, float],
            lis: list[str],
            test1: str | None | int,
            op: str | None = None,
            op1: str | int | None = None,
            default_i=1,
            default_s="",
            default_f=0.0,
            default_d={},  # noqa: B006 # pylint: disable=W0102
            default_tuple=(0, "", 0.0),
            default_list=[0, 1],  # noqa: B006
            e=t,
            *args,
            **kwargs,
        ):
            pass


@pytest.mark.skipif(sys.version_info < (3, 10), reason="Python version >= 3.10 required")
def test_type_parsing():
    properties, _ = parse_registry(S)
    properties = properties["properties"]["B"]["properties"]
    for k, v in properties.items():
        print(k, v)

    _assert(properties, "i", "number")
    _assert(properties, "s", "string")
    _assert(properties, "f", "number")
    _assert(properties, "d", "object")
    _assert(properties, "obj", "string")
    _assert(properties, "c", "string")
    _assert(properties, "e", "number")
    _assert(properties, "uni1", "")
    _assert(properties, "uni2", "")
    _assert(properties, "uni3", "")
    _assert(properties, "tup", "array")
    _assert(properties, "lis", "array", "string")
    _assert(properties, "test1", "")
    _assert(properties, "op", "string")
    _assert(properties, "op1", "")
    _assert(properties, "default_i", "number")
    _assert(properties, "default_s", "string")
    _assert(properties, "default_f", "number")
    _assert(properties, "default_d", "object")
    _assert(properties, "default_tuple", "array")
    _assert(properties, "default_list", "array", "number")
    _assert(properties, "args", "array")
    _assert(properties, "kwargs", "object")
    S.clear()
