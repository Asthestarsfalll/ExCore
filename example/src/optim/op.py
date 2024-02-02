from excore import logger
from src import OPTIM


@OPTIM.register()
class AdamW:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        logger.debug("AdamW kwargs: {}", kwargs)
