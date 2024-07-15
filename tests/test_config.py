import os
import random
from copy import deepcopy

import pytest
import torch
from torchvision.models import ResNet

from excore import config
from excore._exceptions import (
    CoreConfigParseError,
    CoreConfigSupportError,
    EnvVarParseError,
    ImplicitModuleParseError,
    ModuleBuildError,
)
from excore.config.model import ModuleNode, ReusedNode
from excore.engine import logger


def shuffle_fields():
    random.shuffle(config.parse.ConfigDict.primary_fields)


def shuffle_dict(d):
    n = deepcopy(d)
    n.clear()
    items = list(d.items())
    random.shuffle(items)
    for k, v in items:
        if isinstance(v, dict):
            v = shuffle_dict(v)
        n[k] = v
    return n


class TestConfig:
    def _load(self, path, check=True):
        shuffle_fields()
        cfg = config.load(path, parse_config=False)
        cfg._config = shuffle_dict(cfg._config)
        logger.ex(cfg)
        modules, info = config.build_all(cfg)
        if check:
            self.check_info(info)
        return modules, info

    def check_info(self, info):
        assert info["test1"] == 1
        assert info["test2"] == [1, 2, 3]
        assert info["test3"] == {"a": 1, "b": 2, "c": 3}
        assert info["test4"]["test5"] == {"a": 1, "b": 2, "c": 3}

    def test_reused_and_intern(self):
        modules, info = self._load("./configs/launch/test_reused_intern.toml")
        assert isinstance(modules.Model.FCN.backbone, ResNet)
        assert isinstance(modules.Model.DeepLabV3.backbone, ResNet)
        assert id(modules.Model.FCN.backbone) == id(modules.Model.DeepLabV3.backbone)
        assert id(modules.Backbone) == id(modules.Model.FCN.backbone)
        assert id(modules.Model.FCN.classifier) != id(modules.Model.DeepLabV3.classifier)

    def test_reused_and_intern_error(self):
        with pytest.raises(CoreConfigParseError):
            self._load("./configs/launch/test_reused_intern_error.toml")

    def test_optimizer(self):
        modules, info = self._load("./configs/launch/test_optim.toml")
        assert info.get("learning_rate")
        optim = modules.Optimizer
        model = modules.Model.backbone
        inp = torch.randn(2, 3, 224, 224)
        out = model(inp)
        loss = out.sum()
        loss.backward()
        optim.step()

    def test_argument_hook(self):
        self._load("./configs/launch/test_optim_hook.toml")

    def test_lr_sche(self):
        modules, info = self._load("./configs/launch/test_lrsche.toml")
        lr = modules.LRSche
        optimizer = modules.Optimizer
        assert id(lr.optimizer) == id(optimizer)

    def test_non_registry_primary(self):
        self._load("./configs/dataset/data.toml", check=False)

    def test_argument_error(self):
        with pytest.raises(ModuleBuildError):
            self._load("./configs/dataset/data_error.toml")

    def test_wrong_type(self):
        with pytest.raises(CoreConfigSupportError):
            self._load("./configs/launch/error.yaml")

    def test_class(self):
        modules, _ = self._load("./configs/launch/test_class.toml", False)
        from source_code.models.nets import VGG

        assert modules.Model.cls == VGG

    def test_module(self):
        modules, _ = self._load("./configs/launch/test_module.toml", False)
        assert modules.Model.cls == torch.nn.ReLU

    def test_regitered_error(self):
        with pytest.raises(ModuleBuildError):
            self._load("./configs/launch/test_regitered_error.toml", False)

    def test_hidden_error(self):
        with pytest.raises(CoreConfigParseError):
            self._load("./configs/launch/test_hidden_error.toml", False)

    def test_ref_field_error(self):
        with pytest.raises(CoreConfigParseError):
            self._load("./configs/launch/test_ref_field_error.toml", False)

    def test_nest(self):
        self._load("./configs/launch/test_nest.toml", False)

    def test_nest_hidden(self):
        self._load("./configs/launch/test_nest_hidden.toml", False)

    def test_conflict_name_error(self):
        with pytest.raises(CoreConfigParseError):
            self._load("./configs/launch/test_conflict_name.toml", False)

    def test_dump(self):
        config.load("./configs/launch/test_nest.toml", dump_path="./temp_config.toml")
        assert os.path.exists("temp_config.toml")

    def test_dump2(self):
        cfg = config.load("./configs/launch/test_nest.toml")
        cfg.dump("./temp_config2.toml")
        assert os.path.exists("temp_config2.toml")

    def test_no_call(self):
        modules, _ = self._load("./configs/launch/test_no_call.toml", False)
        assert isinstance(modules.Model, ModuleNode)

    def test_no_call_with_reused_node(self):
        modules, _ = self._load("./configs/launch/test_no_call_reused.toml", False)
        assert isinstance(modules.Backbone.x, ReusedNode)
        assert id(modules.Backbone.x) == id(modules.Model)

    def test_dict_action(self):
        from init import excute

        excute(
            "python ./source_code/dict_action.py "
            "--config ./configs/launch/data.toml "
            "--cfg-options Test.1.data=[0,3] "
            'Test.2=1 Test.3="(0)" TMP.1.2.3.4.5.6=7 --dump ./temp_config3.toml'
        )

        cfg = config.load("./temp_config3.toml", parse_config=False).config

        assert cfg["Test"]["1"]["data"] == [0, 3]

    def test_override(self):
        cfg = config.load("./configs/launch/test_override.toml", parse_config=False).config
        assert cfg["Test"]["1"]["data"] == [0]
        assert cfg["Test"]["2"]["data"]["name"] == "test"

    def test_auto_parse(self):
        cfg = config.load("./configs/launch/test_reused_intern.toml", parse_config=False)
        modules = cfg.build_all()[0]
        assert isinstance(modules.Model.FCN.backbone, ResNet)
        assert isinstance(modules.Model.DeepLabV3.backbone, ResNet)
        assert id(modules.Model.FCN.backbone) == id(modules.Model.DeepLabV3.backbone)
        assert id(modules.Backbone) == id(modules.Model.FCN.backbone)
        assert id(modules.Model.FCN.classifier) != id(modules.Model.DeepLabV3.classifier)

    def test_implicit_module_parse(self):
        with pytest.raises(ImplicitModuleParseError):
            self._load("./configs/launch/test_implicit.toml", False)

    def test_reused_conflict(self):
        modules, _ = self._load("./configs/launch/test_param_conflict.toml", False)

        assert id(modules.DataModule.train) != id(modules.DataModule.val)
        assert id(modules.TrainData) != id(modules.TestData)
        assert id(modules.DataModule.train) == id(modules.TrainData)
        assert id(modules.DataModule.val) == id(modules.TestData)

    def test_reused_conflict_error(self):
        with pytest.raises(CoreConfigParseError):
            self._load("./configs/launch/test_param_conflict_error.toml", False)

    def test_cls_and_other_module(self):
        modules, _ = self._load("./configs/launch/test_cls_and_other_module.toml", False)
        from source_code.models.nets import VGG

        assert modules.Model.cls == VGG
        assert modules.Model.cls1 == VGG
        assert modules.DataModule.train.x == 1
        assert modules.DataModule.val.x == ""

    def test_env(self):
        modules, _ = self._load("./configs/launch/test_env.toml", False)
        assert modules.Backbone.x == os.environ.get("HOME")
        assert modules.DataModule.train == f"$HOME is {os.environ.get('HOME')}"

    def test_env_error(self):
        with pytest.raises(EnvVarParseError):
            self._load("./configs/launch/test_env_error.toml", False)

    def test_scratchpads(self):
        modules, _ = self._load("./configs/launch/test_scratchpads.toml", False)
        from source_code.dataset.data import MockData
        from source_code.models.nets import VGG, TestClass

        assert modules.Model.cls == [VGG, MockData] or modules.Model.cls == [MockData, VGG]
        assert modules.Model.cls1 == [VGG, MockData]
        assert VGG in modules.DataModule.train
        assert MockData in modules.DataModule.train
        assert TestClass in modules.DataModule.train
        assert modules.DataModule.val == VGG

    def test_get_error(self):
        with pytest.raises(CoreConfigParseError):
            self._load("./configs/launch/test_$_error.toml", False)

    def test_get_error2(self):
        with pytest.raises(CoreConfigParseError):
            self._load("./configs/launch/test_$_error2.toml", False)

    def test_get_error3(self):
        with pytest.raises(CoreConfigParseError):
            self._load("./configs/launch/test_$_error3.toml", False)

    def test_ref_error(self):
        with pytest.raises(CoreConfigParseError):
            self._load("./configs/launch/test_ref_error.toml", False)

    def test_dict_param(self):
        modules, _ = self._load("./configs/launch/test_dict_param.toml", False)

        from source_code.models.nets import VGG, TestClass

        assert modules.Model.cls["a"] == VGG
        assert modules.Model.cls["b"] == VGG

        assert modules.Model.cls1["a"] == VGG
        assert modules.Model.cls1["b"] == [VGG, TestClass] or modules.Model.cls1["b"] == [
            TestClass,
            VGG,
        ]


TestConfig().test_scratchpads()
