from src import MODEL


@MODEL.register(name="SimpleHead", is_pretrained=False, is_backbone=False)
class Head:
    def __init__(self, **kwargs):
        pass
