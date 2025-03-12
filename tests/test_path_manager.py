import os
import shutil
from dataclasses import dataclass
from pathlib import Path

import pytest

from excore.plugins.path_manager import PathManager

BASE_PATH = os.path.abspath("./tmp/path_manager_test")
SUB_FOLDERS = ["folder1", "folder2"]
CONFIG_NAME = "config"
INSTANCE_NAME = "instance_test"

os.makedirs(BASE_PATH, exist_ok=True)


class DataError:
    def __init__(self) -> None:
        self.a: str = ""


@dataclass
class Data:
    floder1: str = "folder1"
    floder2: str = "folder2"


def teardown(func):
    def _f():
        func()
        shutil.rmtree(BASE_PATH, ignore_errors=True)

    return _f


@teardown
def test_init():
    pm = PathManager(
        base_path=BASE_PATH,
        sub_folders=SUB_FOLDERS,
        config_name=CONFIG_NAME,
        instance_name=INSTANCE_NAME,
    )
    assert pm.base_path == Path(BASE_PATH)
    assert pm.config_name == Path(CONFIG_NAME)
    assert pm.instance_name == Path(INSTANCE_NAME)


@teardown
def test_get():
    pm = PathManager(
        base_path=BASE_PATH,
        sub_folders=SUB_FOLDERS,
        config_name=CONFIG_NAME,
        instance_name=INSTANCE_NAME,
        config_name_first=True,
        return_str=True,
    )
    pm.mkdir()
    path_str = pm.get("folder1")
    assert os.path.exists(path_str)
    expected_path = f"{BASE_PATH}/{CONFIG_NAME}/{'folder1'}/{pm.instance_name}"
    assert path_str == expected_path


@teardown
def test_get_path():
    pm = PathManager(
        base_path=BASE_PATH,
        sub_folders=SUB_FOLDERS,
        config_name=CONFIG_NAME,
        instance_name=INSTANCE_NAME,
        config_name_first=True,
        return_str=False,
    )
    pm.mkdir()
    path = pm.get("folder1")
    path.exists()
    expected_path = f"{BASE_PATH}/{CONFIG_NAME}/{'folder1'}/{pm.instance_name}"
    assert str(path) == expected_path


@teardown
def test_config_first_and_remove_all():
    with PathManager(
        base_path=BASE_PATH,
        sub_folders=SUB_FOLDERS,
        config_name=CONFIG_NAME,
        instance_name=INSTANCE_NAME,
        config_name_first=True,
    ) as pm:
        for sub_folder in pm.sub_folders:
            full_path = Path(BASE_PATH) / Path(CONFIG_NAME) / sub_folder / pm.instance_name
            assert full_path.exists()

        pm.remove_all()
        for sub_folder in pm.sub_folders:
            full_path = Path(BASE_PATH) / Path(CONFIG_NAME) / sub_folder / pm.instance_name
            assert not full_path.exists()


@teardown
def test_context_manager():
    with pytest.raises(RuntimeError):
        with PathManager(
            base_path=BASE_PATH,
            sub_folders=SUB_FOLDERS,
            config_name=CONFIG_NAME,
            instance_name=INSTANCE_NAME,
        ):
            raise RuntimeError

    for sub_folder in SUB_FOLDERS:
        full_path = Path(BASE_PATH) / Path(CONFIG_NAME) / Path(sub_folder) / Path(INSTANCE_NAME)
        assert not full_path.exists()


@teardown
def test_dataclass():
    with PathManager(
        base_path=BASE_PATH,
        sub_folders=Data(),
        config_name=CONFIG_NAME,
        instance_name=INSTANCE_NAME,
        config_name_first=True,
    ) as pm:
        for sub_folder in pm.sub_folders:
            full_path = Path(BASE_PATH) / Path(CONFIG_NAME) / sub_folder / pm.instance_name
            assert full_path.exists()


@teardown
def test_error():
    with pytest.raises(TypeError):
        PathManager(BASE_PATH, DataError(), CONFIG_NAME, INSTANCE_NAME)
