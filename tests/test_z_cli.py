import os

from init import execute, init


def test_init_force():
    init()


def test_generate_registries():
    # FIXME(typer): Argument
    execute("excore generate-registries temp")
    assert os.path.exists("./source_code/temp.py")
    from source_code import temp  # noqa: F401


def test_config_extension():
    execute("excore config-extension")


def test_cache():
    execute("excore cache-list")


def test_primary():
    execute("excore primary-fields")


def test_typehints():
    execute(
        "excore generate-typehints temp_typing --class-name "
        "TypedWrapper --info-class-name Info --config ./configs/launch/test_optim.toml"
    )
    assert os.path.exists("./source_code/temp_typing.py")
    from source_code.temp_typing import Info, TypedWrapper  # noqa: F401


def test_clear_cache():
    execute("excore clear-cache", ["y"])


def test_quote():
    execute("excore quote ./configs/lrsche")
    assert os.path.exists("./configs/lrsche/lrsche_overrode.toml")
    assert os.path.exists("./configs/lrsche/lrsche_error_overrode.toml")
    os.remove("./configs/lrsche/lrsche_overrode.toml")
    os.remove("./configs/lrsche/lrsche_error_overrode.toml")
