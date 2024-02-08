from excore import ConfigArgumentHook
from source_code import HOOK


@HOOK.register()
class BnWeightDecayHook(ConfigArgumentHook):
    def __init__(self, node, enabled: bool, bn_weight_decay: bool, weight_decay: float):
        super().__init__(node, enabled)
        self.bn_weight_decay = bn_weight_decay
        self.weight_decay = weight_decay

    def hook(self):
        model = self.node()
        if self.bn_weight_decay:
            optim_params = model.parameters()
        else:
            p_bn = [p for n, p in model.named_parameters() if "bn" in n]
            p_non_bn = [p for n, p in model.named_parameters() if "bn" not in n]
            optim_params = [
                {"params": p_bn, "weight_decay": 0},
                {"params": p_non_bn, "weight_decay": self.weight_decay},
            ]
        return optim_params


@HOOK.register()
class DoNothing(ConfigArgumentHook):
    def __init__(self, node, enabled: bool):
        super().__init__(node, enabled)

    def hook(self):
        return self.node()
