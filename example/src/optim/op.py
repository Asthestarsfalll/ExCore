from excore import logger
from . import OPTIM


@OPTIM.register()
class AdamW:
    def __init__(self, **kwargs):
        logger.debug("AdamW kwargs: {}", kwargs)
