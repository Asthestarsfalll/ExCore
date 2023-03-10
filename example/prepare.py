from excore import Registry

MODELS = Registry("Model", extra_field=["is_pretrained", "is_backbone"])
DATAS = Registry("Data")
TRANSFORMS = Registry("Transform")
OPTIM = Registry("Optimizer")
LOSSES = Registry("Loss")


@MODELS.register(is_pretrained=True, is_backbone=True)
class ResNet:
    def __init__(self, **kwargs):
        pass


@MODELS.register(name="SimpleHead", is_pretrained=False, is_backbone=False)
class Head:
    def __init__(self, **kwargs):
        pass


@MODELS.register(is_pretrained=True)
class FCN:
    def __init__(self, **kwargs):
        pass


@OPTIM.register()
class AdamW:
    def __init__(self, **kwargs):
        pass


@DATAS.register()
class CityScapes:
    def __init__(self, **kwargs):
        pass


@TRANSFORMS.register()
class RandomResize:
    def __init__(self, **kwargs):
        pass


@TRANSFORMS.register()
class Normalize:
    def __init__(self, **kwargs):
        pass


@TRANSFORMS.register()
class RandomFlip:
    def __init__(self, **kwargs):
        pass


@LOSSES.register()
class OHEM:
    def __init__(self, **kwargs):
        pass


@LOSSES.register()
class CrossEntropyLoss:
    def __init__(self, **kwargs):
        pass


@LOSSES.register()
class BoundaryLoss:
    def __init__(self, **kwargs):
        pass
