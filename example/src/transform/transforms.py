from . import TRANSFORMS


@TRANSFORMS.register()
class RandomResize:
    def __init__(self, **kwargs):
        pass


@TRANSFORMS.register()
class Normalize:
    def __init__(self, **kwargs):
        pass


@TRANSFORMS.register()
class RandomFlip:
    def __init__(self, **kwargs):
        pass


@TRANSFORMS.register()
class Pad:
    def __init__(self, **kwargs):
        pass
