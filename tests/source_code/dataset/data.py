from torchvision import datasets

from source_code import DATA

DATA.match(datasets)


@DATA.register()
class MockData:
    def __init__(self, trans):
        self.trans = trans
