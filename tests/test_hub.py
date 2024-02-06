import pytest

from excore import hub


def test_hub_load():
    with pytest.raises(ModuleNotFoundError):
        hub.load(
            "zhanghang1989/ResNeSt",
            entry="resnest50",
            hubconf_entry="hubconf.py",
            git_host="github.com",
        )
        hub.import_module(
            "zhanghang1989/ResNeSt", git_host="github.com", hubconf_entry="hubconf.py"
        )
