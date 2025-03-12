from excore import ConfigArgumentHook, logger
from src import HOOK


@HOOK.register()
class ParamsArgHook(ConfigArgumentHook):
    def hook(self):
        logger.debug("params argument hook")
        return self.node()


@HOOK.register()
class DoSomething(ConfigArgumentHook):
    def hook(self):
        logger.debug("do something")
        return self.node()


@HOOK.register()
class AddModelParams:
    __HookType__ = "every_build"
    __LifeSpan__ = 1
    __CallInter__ = 1

    def __call__(self, cfg, module_dict, isolate_dict):
        if "Model" in module_dict:
            assert "Optimizer" not in module_dict
            model = module_dict["Model"]
            cfg.Optimizer << dict(params=model[0].parameters())
            logger.info("AddModelParams: add model params to optimizer")
            logger.info(cfg.Optimizer.get("params"))
            return True
        return False
