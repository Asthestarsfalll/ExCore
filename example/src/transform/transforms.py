from src import TRANSFORM


@TRANSFORM.register()
class RandomResize:
    def __init__(self, **kwargs):
        pass


@TRANSFORM.register()
class Normalize:
    def __init__(self, **kwargs):
        pass


@TRANSFORM.register()
class RandomFlip:
    def __init__(self, **kwargs):
        pass


@TRANSFORM.register()
class Pad:
    def __init__(self, **kwargs):
        pass
