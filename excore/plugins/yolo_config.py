from typing import TYPE_CHECKING

from ..config.models import ModuleNode, register_special_flag

if TYPE_CHECKING:
    from ..config.models import NoCallSkipFlag, NodeInstance, NodeParams


class DetailNode(ModuleNode):
    priority = 2
    module_key = "target"

    def _update_params(self, **params: NodeParams):
        if DetailNode.module_key not in self:
            raise RuntimeError()
        super()._update_params(**params)

    def __call__(self, **params: NodeParams) -> NoCallSkipFlag | NodeInstance:
        pass


def enable_detialed_confing(special_flag: str = "*", module_key: str = "target") -> None:
    DetailNode.module_key = module_key
    register_special_flag(special_flag, DetailNode)
