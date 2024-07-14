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
        d: dict,
        obj: Tmp,
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
        default_d={},  # noqa: B006
        default_tuple=(0, "", 0.0),
        default_list=[0, 1],  # noqa: B006
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
    property, _ = parse_registry(R)
    property = property["properties"]["A"]["properties"]
    for k, v in property.items():
        print(k, v)

    _assert(property, "i", "number")
    _assert(property, "s", "string")
    _assert(property, "f", "number")
    _assert(property, "d", "object")
    _assert(property, "obj", "string")
    _assert(property, "uni1", "")
    _assert(property, "uni2", "")
    _assert(property, "uni3", "")
    _assert(property, "tup", "array")
    _assert(property, "lis", "array", "string")
    _assert(property, "test1", "")
    _assert(property, "op", "string")
    _assert(property, "op1", "")
    _assert(property, "default_i", "number")
    _assert(property, "default_s", "string")
    _assert(property, "default_f", "number")
    _assert(property, "default_d", "object")
    _assert(property, "default_tuple", "array")
    _assert(property, "default_list", "array", "number")


test_type_parsing()
