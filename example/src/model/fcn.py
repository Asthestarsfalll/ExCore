from src import MODEL

IDX = 0  # for check


@MODEL.register(is_pretrained=True)
class FCN:
    def __init__(self, **kwargs):
        global IDX  # pylint: disable=global-statement

        for k, v in kwargs.items():
            setattr(self, k, v)
        IDX += 1

    def parameters(self):
        return f"parameters of FCN_{IDX}"
