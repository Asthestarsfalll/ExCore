from .. import MODELS


@MODELS.register(is_pretrained=True, is_backbone=True)
class ResNet:
    def __init__(self, **kwargs):
        pass
