from excore import Registry
from excore.logger import logger

MODELS = Registry("Model", extra_field=["is_pretrained", "is_backbone"])
DATAS = Registry("Data")
TRANSFORMS = Registry("Transform")
OPTIM = Registry("Optimizer")
LOSSES = Registry("Loss")
HOOKS = Registry("Hook")
LRCHE = Registry("LRSche")


@HOOKS.register()
class AddModelParams:
    __HookType__ = "every_build"
    __LifeSpan__ = 1
    __CallInter__ = 1

    def __call__(self, cfg, module_dict):
        if "Model" in module_dict:
            model = module_dict["Model"]
            k = list(cfg["Optimizer"].keys())[0]
            cfg["Optimizer"][k]["params"] = model.pramameters()
            logger.info("AddModelParams: add model params to optimizer")
            logger.info(cfg["Optimizer"][k])
            return True
        return False


@HOOKS.register()
class AddOptimizer:
    __HookType__ = "every_build"
    __LifeSpan__ = 1
    __CallInter__ = 1

    def __call__(self, cfg, module_dict):
        if "LRSche" in module_dict:
            raise RuntimeError
        if "Optimizer" in module_dict:
            optim = module_dict["Optimizer"]
            k = list(cfg["LRSche"].keys())[0]
            cfg["LRSche"][k]["optimizer"] = optim
            logger.info("AddOptimizer: add optimizer to lr_scheduler")
            logger.info(cfg["LRSche"][k])
            return True
        return False


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

    def pramameters(self):
        return 1


@OPTIM.register()
class AdamW:
    def __init__(self, **kwargs):
        logger.debug("AdamW kwargs: {}", kwargs)


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


@LRCHE.register()
class CosDecay:
    def __init__(self, **kwargs):
        pass
