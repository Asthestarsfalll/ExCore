from torchvision import models
from torchvision.models import segmentation

from source_code import BACKBONE, HEAD, MODEL

MODEL.match(segmentation)
BACKBONE.match(models, force=True)
HEAD.register_module(segmentation.fcn.FCNHead)
