from typing import List

from src import MODEL


@MODEL.register(is_backbone=False)
class BasicBlock:
    def __init__(self, in_chan, out_chan):
        pass


@MODEL.register(is_pretrained=True, is_backbone=True)
class ResNet:
    def __init__(
        self, in_channel: int, depth: int, block: BasicBlock, layers: List[int]
    ):
        pass
