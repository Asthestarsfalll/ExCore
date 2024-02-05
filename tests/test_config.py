import pytest
import torch
from torchvision.models import ResNet

from excore import config
from excore._exceptions import CoreConfigParseError


class TestConfig:
    def test_reused_and_intern(self):
        cfg = config.load("./configs/launch/test_reused_intern.toml")
        modules = config.build_all(cfg)[0]
        assert isinstance(modules.Model.FCN.backbone, ResNet)
        assert isinstance(modules.Model.DeepLabV3.backbone, ResNet)
        assert id(modules.Model.FCN.backbone) == id(modules.Model.DeepLabV3.backbone)
        assert id(modules.Backbone) == id(modules.Model.FCN.backbone)
        assert id(modules.Model.FCN.classifier) != id(modules.Model.DeepLabV3.classifier)

    def test_reused_and_intern_error(self):
        with pytest.raises(CoreConfigParseError):
            cfg = config.load("./configs/launch/test_reused_intern_error.toml")
            config.build_all(cfg)

    def test_optimizer(self):
        cfg = config.load("./configs/launch/test_optim.toml")
        modules = config.build_all(cfg)[0]
        optim = modules.Optimizer
        model = modules.Model.backbone
        inp = torch.randn(2, 3, 224, 224)
        out = model(inp)
        loss = out.sum()
        loss.backward()
        optim.step()

    def test_argument_hook(self):
        cfg = config.load("./configs/launch/test_lrsche.toml")
        config.build_all(cfg)[0]

    def test_lr_sche(self):
        cfg = config.load("./configs/launch/test_lrsche.toml")
        modules = config.build_all(cfg)[0]
        lr = modules.LRSche
        optimizer = modules.Optimizer
        assert id(lr.optimizer) == id(optimizer)
