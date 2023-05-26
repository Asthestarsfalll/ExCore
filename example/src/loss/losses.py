from . import LOSSES


@LOSSES.register()
class OHEM:
    def __init__(self, **kwargs):
        pass


@LOSSES.register()
class CrossEntropyLoss:
    def __init__(self, **kwargs):
        pass


@LOSSES.register()
class BoundaryLoss:
    def __init__(self, **kwargs):
        pass
