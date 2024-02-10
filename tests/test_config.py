import pytest
import torch
from torchvision.models import VGG, ResNet

from excore import config
from excore._exceptions import CoreConfigParseError, CoreConfigSupportError, ModuleBuildError


class TestConfig:
    def _load(self, path, check=True):
        cfg = config.load(path)
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
        self._load("./configs/launch/test_lrsche.toml")

    def test_lr_sche(self):
        modules, info = self._load("./configs/launch/test_lrsche.toml")
        lr = modules.LRSche
        optimizer = modules.Optimizer
        assert id(lr.optimizer) == id(optimizer)

    def test_non_registry_target(self):
        self._load("./configs/dataset/data.toml", check=False)

    def test_argument_error(self):
        with pytest.raises(ModuleBuildError):
            self._load("./configs/dataset/data_error.toml")

    def test_wrong_type(self):
        with pytest.raises(CoreConfigSupportError):
            self._load("./configs/launch/error.yaml")

    def test_class(self):
        modules, _ = self._load("./configs/launch/test_class.toml", False)
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
