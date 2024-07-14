from typing import Dict, List, Optional, Tuple, Union

from excore import Registry
from excore.config._json_schema import parse_registry

R = Registry("R")


class Tmp:
    pass


class Tmp2:
    pass


@R.register()
class A:
    def __init__(
        self,
        i: int,
        s: str,
        f: float,
        d: Dict,
        d1: dict,
        obj: Tmp,
        uni1: Union[int, float],
        uni2: Union[int, str],
        uni3: Union[Tmp, Tmp2],
        tup: Tuple[int, str, float],
        lis: List[str],
        test1: Union[str, None],
        test2: Union[str, None, int],
        op: Optional[str] = None,
        op1: Optional[Union[str, int]] = None,
        default_i=1,
        default_s="",
        default_f=0.0,
        default_d={},  # noqa: B006 # pylint: disable=W0102
        default_tuple=(0, "", 0.0),
        default_list=[0, 1],  # noqa: B006
        *args,
        **kwargs,
    ):
        pass


def _assert(p: dict, name: str, t: str, item=None):
    assert p.get(name).get("type", "") == t
    if item is not None:
        assert p.get(name).get("items", False)
        assert p.get(name).get("items").get("type") == item
    else:
        assert p.get(name).get("items", None) is None


def test_type_parsing():
    properties, _ = parse_registry(R)
    properties = properties["properties"]["A"]["properties"]
    for k, v in properties.items():
        print(k, v)

    _assert(properties, "i", "number")
    _assert(properties, "s", "string")
    _assert(properties, "f", "number")
    _assert(properties, "d", "object")
    _assert(properties, "d1", "object")
    _assert(properties, "obj", "string")
    _assert(properties, "uni1", "")
    _assert(properties, "uni2", "")
    _assert(properties, "uni3", "")
    _assert(properties, "tup", "array")
    _assert(properties, "lis", "array", "string")
    _assert(properties, "test1", "string")
    _assert(properties, "test2", "")
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
    R.clear()
