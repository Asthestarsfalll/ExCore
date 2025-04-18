import torch
from torchvision import models
from torchvision.models import segmentation

from excore import Registry
from source_code import BACKBONE, HEAD, MODEL

BLOCK = Registry("Block")
MODEL.match(segmentation)


def _match(name: str, module):
    return not name.endswith("Outputs")


BACKBONE.match(models, force=True, match_func=_match)
HEAD.register_module(segmentation.fcn.FCNHead)


@BACKBONE.register(force=True)
class VGG:
    def __init__(self, x):
        self.x = x


@MODEL.register()
class TestClass:
    def __init__(self, cls, cls1=None):
        self.cls = cls
        self.cls1 = cls1


@BACKBONE.register()
class MockModel:
    def __init__(self, block):
        self.block = block


@BLOCK.register()
class TestBlock:
    pass


BLOCK.register_module(torch.nn.Conv2d, receive="in_channels", send="out_channels")
BLOCK.register_module(torch.nn.BatchNorm2d, receive="num_features", send="num_features")
