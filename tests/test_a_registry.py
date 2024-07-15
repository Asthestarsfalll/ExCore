import time

import pytest

from excore import Registry, load_registries

load_registries()

Registry.unlock_register()


def test_print():
    import source_code as S

    print(S.MODEL)


def test_find():
    import source_code as S

    tar, base = S.BACKBONE.find("ResNet")
    assert base == "Backbone"
    assert tar.split(".")[-1] == "ResNet"


def test_register_module():
    reg = Registry("__test")
    reg.register_module(time)
    assert reg["time"] == "time"


def test_global():
    import source_code as S

    g = Registry.make_global()
    assert g["time"] == "time"
    assert g["ResNet"] == "torchvision.models.resnet.ResNet"
    with pytest.raises(ValueError):
        S.MODEL.register_module(time)
    assert id(S.MODEL) == id(Registry.get_registry("Model"))


def test_module_table():
    import source_code as S

    print(S.MODEL.module_table())
    print(S.MODEL.module_table("*resnet*"))


def test_id():
    import source_code as S

    assert Registry.get_registry("Head") == S.HEAD
