from excore.config import ModuleNode, load, register_special_flag


class FoolModuleNode(ModuleNode):
    priority = 2

    def __call__(self, **params):
        p = {}
        for k, v in self.items():
            if isinstance(v, int):
                v += 1
            p[k] = v
        return super().__call__(**p)


register_special_flag("*", FoolModuleNode)


def test_module_node_registry():
    cfg = load("./configs/launch/test_module_registry.toml")
    module, _ = cfg.build_all()
    assert module.Model.classifier[0].in_channels == 513
