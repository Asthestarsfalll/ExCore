from torchvision import models
from torchvision.models import segmentation

from source_code import BACKBONE, HEAD, MODEL

MODEL.match(segmentation)


def _match(name: str, module):
    if not name.endswith("Outputs"):
        return True
    return False


BACKBONE.match(models, force=True, match_func=_match)
HEAD.register_module(segmentation.fcn.FCNHead)
