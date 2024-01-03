from excore import Registry

MODEL = Registry("Model", extra_field=["is_pretrained", "is_backbone"])
DATA = Registry("Data")
HOOK = Registry("Hook")
LOSS = Registry("Loss")
LRCHE = Registry("LRSche")
OPTIM = Registry("Optimizer")
TRANSFORM = Registry("Transform")
