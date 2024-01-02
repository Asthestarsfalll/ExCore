from src import MODEL


@MODEL.register(is_pretrained=True)
class FCN:
    def __init__(self, **kwargs):
        pass

    def parameters(self):
        return "parameters of FCN"
