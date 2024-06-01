from torchvision import models
from torchvision.models import segmentation

from excore import Registry
from source_code import BACKBONE, HEAD, MODEL

BLOCK = Registry("Block")
MODEL.match(segmentation)


def _match(name: str, module):
    if not name.endswith("Outputs"):
        return True
    return False


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
