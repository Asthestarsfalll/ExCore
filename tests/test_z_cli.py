import os

from init import excute, init


def test_init_force():
    init()


def test_generate_registries():
    excute("excore generate-registries temp")
    assert os.path.exists("./source_code/temp.py")
    from source_code import temp  # noqa: F401


def test_config_extention():
    excute("excore config-extention")


def test_cache():
    excute("excore cache-list")


def test_primary():
    excute("excore primary-fields")


def test_typehints():
    excute(
        "excore generate-typehints temp_typing --class-name "
        "TypedWrapper --info-class-name Info --config ./configs/launch/test_optim.toml"
    )
    assert os.path.exists("./source_code/temp_typing.py")
    from source_code.temp_typing import Info, TypedWrapper  # noqa: F401


def test_clear_cache():
    excute("excore clear-cache")
