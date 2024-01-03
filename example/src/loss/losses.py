from src import LOSS


@LOSS.register()
class OHEM:
    def __init__(self, **kwargs):
        pass


@LOSS.register()
class CrossEntropyLoss:
    def __init__(self, **kwargs):
        pass


@LOSS.register()
class BoundaryLoss:
    def __init__(self, **kwargs):
        pass
