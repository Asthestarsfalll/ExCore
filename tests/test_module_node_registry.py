from excore.config import ModuleNode, load, register_special_flag


class FoolModuleNode(ModuleNode):
    priority = 2

    def __call__(self, **params):
        for k, v in self.items():
            if isinstance(v, int):
                v += 1
            self[k] = v
        return super().__call__()


register_special_flag("*", FoolModuleNode)


def test_module_node_registry():
    cfg = load("./configs/launch/test_module_registry.toml")
    module, _ = cfg.build_all()
    assert module.Model.classifier[0].in_channels == 513
