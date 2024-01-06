from src import LRCHE


@LRCHE.register()
class CosDecay:
    def __init__(self, optimizer, learning_rate):
        self.optimizer = optimizer
        self.learning_rate = learning_rate
