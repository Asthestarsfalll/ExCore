from typing import List

from src import DATA


@DATA.register()
class CityScapes:
    def __init__(self, data_path: str, img_size: List[int], transforms):
        pass
