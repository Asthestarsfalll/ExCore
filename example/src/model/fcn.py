from src import MODEL


class ID:
    def __str__(self):
        return f"{id(self)}"


@MODEL.register(is_pretrained=True)
class FCN:
    def __init__(self, **kwargs):
        self._id = ID()

        for k, v in kwargs.items():
            setattr(self, k, v)

    def parameters(self):
        return self._id
