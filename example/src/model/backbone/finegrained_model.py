import torch
from torch import nn

from src import MODEL, MODULE

MODULE.register_module(torch)


@MODEL.register()
class FinegrainedModel:
    def __init__(self, backbone, head):
        print(backbone)
        print(head)
        self.backbone = backbone
        self.head = head


MODEL.register_module(nn.Conv2d, receive="in_channels", send="out_channels")
MODEL.register_module(nn.BatchNorm2d, receive="num_features", send="num_features")
