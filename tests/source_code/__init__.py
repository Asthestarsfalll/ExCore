import time

import torch

from excore import Registry

MODEL = Registry("Model")
BLOCK = Registry("Block")
HEAD = Registry("Head")
BACKBONE = Registry("Backbone")
DATA = Registry("Data")
HOOK = Registry("Hook")
LOSS = Registry("Loss")
LRCHE = Registry("LRSche")
OPTIM = Registry("Optimizer")
TRANSFORM = Registry("Transform")
MODULE = Registry("module")

MODULE.register_module(time)
MODULE.register_module(torch)
