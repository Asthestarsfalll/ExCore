from src import OPTIM

from excore.logger import logger


@OPTIM.register()
class AdamW:
    def __init__(self, **kwargs):
        logger.debug("AdamW kwargs: {}", kwargs)
