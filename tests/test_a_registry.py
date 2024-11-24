import time

import pytest

from excore import Registry, load_registries, _enable_excore_debug

load_registries()

_enable_excore_debug()

import source_code as S


def test_print():
    print(S.MODEL)


def test_find():
    tar, base = S.BACKBONE.find("ResNet")
    assert base == "Backbone"
    assert tar.split(".")[-1] == "ResNet"


def test_register_module():
    Registry.unlock_register()
    reg = Registry("__test")
    reg.register_module(time)
    assert reg["time"] == "time"


def test_global():
    g = Registry.make_global()
    assert g["time"] == "time"
    assert g["ResNet"] == "torchvision.models.resnet.ResNet"
    with pytest.raises(ValueError):
        S.MODEL.register_module(time)
    assert id(S.MODEL) == id(Registry.get_registry("Model"))
    Registry.lock_register()


def test_module_table():
    print(S.MODEL.module_table())
    print(S.MODEL.module_table("*resnet*"))


def test_id():
    assert Registry.get_registry("Head") == S.HEAD
