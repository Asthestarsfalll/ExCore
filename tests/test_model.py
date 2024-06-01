import pytest

from excore.config.model import ModuleNode


def test_lshift():
    module = ModuleNode(1)
    module << dict(a=1)
    assert module["a"] == 1
    with pytest.raises(TypeError):
        module << 1


def test_rshift():
    module = ModuleNode(1)
    module1 = ModuleNode(2).add(a=3)
    module1 >> module
    assert module["a"] == 3
    with pytest.raises(TypeError):
        module >> 1
