from src import MODEL


@MODEL.register(is_pretrained=False, is_backbone=False)
class SimpleHead:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
