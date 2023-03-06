from core import Registry

MODELS = Registry("Model")
DATAS = Registry("Data")
TRANSFORMS = Registry("Transform")
OPTIM = Registry("Optimizer")
LOSSES = Registry("Loss")


@MODELS.register()
class ResNet:
    def __init__(self, **kwargs):
        pass


@MODELS.register(name="SimpleHead")
class Head:
    def __init__(self, **kwargs):
        pass


@MODELS.register()
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
