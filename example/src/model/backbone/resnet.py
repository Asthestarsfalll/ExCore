from typing import List

from src import MODEL


@MODEL.register(is_backbone=False)
class BasicBlock:
    def __init__(self, in_chan=0, out_chan=0):
        pass


@MODEL.register(is_pretrained=True, is_backbone=True)
class ResNet:
    def __init__(self, in_channel: int, depth: int, block: BasicBlock, layers: List[int]):
        assert block == BasicBlock
        self.in_channel = in_channel
        self.depth = depth
        self.layers = layers
