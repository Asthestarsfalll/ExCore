---
title: Config System
sidebar_position: 2
---

import Tabs from '@theme/Tabs';

import TabItem from '@theme/TabItem';

import styles from '/src/css/tab.css';

:::warning
The config system is a bit complicated. Be patient.
:::

## Beyond `LazyConfig`

Config system is the **core** of deeplearning projects which enable us to manage and adjust hyperparameters and expriments. There are attemps of pure python configs because the whole community has been suffering from the plain text config files for a long while. But the pure python style configs also have its own defects. For example, `MMEngine` uses `type` to specify class and config always nesting, `detectron2` uses `LazyConfig` to store the arguments to lazily instantiate. But both of them only provides code navigation and auto-completion for the class. The arguments are still aches for community.

Config System in `ExCore` is designed specifically for deeplearning training (generally refers to all similar part, e.g. testing, evaluating) procedure. _The core premise is to categorize the objects to be created in the config into three classes - `Primary`, `Intermediate`, and `Isolated` objects_

1. `Primary` objects are those which are **directly** used in training, e.g. model, optimizer. `ExCore` will instantiate and return them.
2. `Intermediate` objects are those which are **indirectly** used in training, e.g. backbone of the model, parameters of model that will pass to optimizer. `ExCore` will instantiate them, and pass them to target `Primary` objects as arguments according some rules.
3. `Isolated` objects refer to python built-in objects which will be parsed when loading toml, e.g. int, string, list and dict.

`ExCore` extends the syntax of toml file, introducing some special prefix characters -- `!`, `@`, `$` and '&' to simplify the config definition.

## Features

### Get rid of `type`

In order to get rid of `type`, `ExCore` regards all registered names as `reserved words`. The `Primary` module need to be defined like `[PrimaryFields.ModuleName]`. `PrimaryFields` are some pre-defined fields, e.g. `Model`, `Optimizer`. `ModuleName` are registered names.

<Tabs groupId="config">
<TabItem value="toml" >

```toml
[Model.FCN]
layers = 50
num_classes = 1
```

</TabItem>
<TabItem value="yaml" >

```yaml
Model:
  # Error
  type: ResNet # <----- ugly type
  layers: 50
  num_classes: 1
```

</TabItem>
</Tabs>

### Eliminate modules nesting

Nesting is a terrible exprience especially when you don't know how many indentations or brackets in configs. `ExCore` use some special prefix characters to specify certain arguments are modules as well. More prefixes will be introduced later.

<Tabs groupId="config">

<TabItem value ='toml'>

```toml
[TrainData.Cityscapes]
dataset_root = "data/cityscapes"
mode = 'train'
# use `!` to show this is a module, It's formal to use a quoted key "!transforms", but whatever
# Error
!transforms = ["ResizeStepScale", "RandomPaddingCrop", "Normalize"]

# `PrimaryFields` can be omitted in defination of `Intermediate` module
[ResizeStepScale]
min_scale_factor = 0.5
max_scale_factor = 2.0
scale_step_size = 0.25

# or explicitly specify ``PrimaryFields
[Transforms.RandomPaddingCrop]
crop_size = [1024, 512]

# It can even be undefined when there are no arguments
# [Normalize]
```

</TabItem>

<TabItem value='yaml'>

```yaml
TrainData:
# Error
  type: Cityscapes
  dataset_root: data/cityscapes
  transforms:
     # Error
   - type: ResizeStepScale
     min_scale_factor: 0.5
     max_scale_factor: 2.0
     scale_step_size: 0.25
     # Error
   - type: RandomPaddingCrop
        crop_size: [1024, 512]
     # Error
   - type: Normalize
  mode: train
```

</TabItem>
</Tabs>

### ✨Auto-complement for config files

The ols-style design of plain text configs has been criticized for being difficult to write (without auto-completion) and not allowing navigation to the corresponding class. However, Language Server Protocol can be leveraged to support various code editing features, such as auto-completion, type-hinting, and code navigation. By utilizing lsp and json schema, it's able to provide the ability of auto-completion, some weak type-hinting (If code is well annotated, such as standard type hint in python, it will acheive more) and docstring of corresponding class.

![](https://user-images.githubusercontent.com/72954905/267884541-56e75031-48a2-4768-8a6c-fc7b83ed977e.gif)

![config](https://github.com/Asthestarsfalll/ExCore/assets/72954905/2b0e151c-5c2b-4082-9796-d171e211c7c8)

`ExCore` dump the mappings of class name and it file location to support code navigation. Currently only support for neovim, see [excore.nvim](https://github.com/Asthestarsfalll/excore.nvim).

![to_class](https://github.com/Asthestarsfalll/ExCore/assets/72954905/9677c204-eb46-4cf3-a8bf-03f9bee8d6fb)

### Config inheritance

Use `__base__` to inherit from a toml file. Only dict can be updated locally, other types are overwritten directly.

```toml
__base__ = ["xxx.toml", "xxxx.toml"]
```

### `@`Reused module

`ExCore` use `@` to mark the reused module, which is shared between different modules.

<Tabs groupId = "python">
<TabItem value = 'toml'>

```toml
# FCN and SegNet will use the same ResNet object
[Model.FCN]
# Error
@backbone = "ResNet"

[Model.SegNet]
# Error
@backbone = "ResNet"

[ResNet]
layers = 50
in_channel = 3
```

</TabItem>

<TabItem value='python'>

```python
resnet = ResNet(layers=50, in_channel=3)

FCN(backbone=resnet)
SegNet(backbone=resnet)

# If use `!`, it equls to

FCN(backbone=ResNet(layers=50, in_channel=3))
SegNet(backbone=ResNet(layers=50, in_channel=3))
```

</TabItem>
</Tabs>

### `$`Refer Class and cross file

`ExCore` use `$` to represents class itself, which will not be instantiated.

<Tabs groupId='python'>
<TabItem value='toml'>

```toml
[Model.ResNet]
# Error
$block = "BasicBlock"
layers = 50
in_channel = 3
```

</TabItem>
<TabItem value='python'>

```python
from xxx import ResNet, BasicBlock
ResNet(block=BasicBlock, layers=50, in_channel=3)
```

</TabItem>
</Tabs>

In order to refer module accross files, `$` can be used before `PrimaryFields`. For example:

File A:

```toml
[Block.BasicBlock]
```

File B:

```toml
[Block.BottleneckBlock]
```

File C:

```toml
[Model.ResNet]
# Error
!block="$Block"
```

So we can combine file A and C or file B and C with a toml file

```toml
__base__ = ["A.toml", "C.toml"]
# or
__base__ = ["B.toml", "C.toml"]
```

### `&`Variable reference

`ExCore` use `&` to refer a variable from the top-level of config.

**Note: The value may be overwritten when inheriting, so the call it variable.**

```toml
size = 224

[TrainData.ImageNet]
# Error
&train_size = "size"
# Error
!transforms = ['RandomResize', 'Pad']
data_path = 'xxx'

[Transform.Pad]
# Error
&pad_size = "size"

[TestData.ImageNet]
# Error
!transforms = ['Normalize']
# Error
&test_size = "size"
data_path = 'xxx'
```

### ✨Using module in config

The `Registry` in `ExCore` is able to register a module:

```python
from excore import Registry
import torch

MODULE = Registry("module")
MODULE.register_module(torch)
```

Then you can use torch in config file:

<Tabs groupId='python'>
<TabItem value='toml'>

```toml
[Model.ResNet]
# Error
$activation = "torch.nn.ReLU"
# or
# Error
!activation = "torch.nn.ReLU"
```

</TabItem>

<TabItem value='python'>

```python
import torch
from xxx import ResNet

ResNet(torch.nn.ReLU)
# or
ResNet(torch.nn.ReLU())
```

</TabItem>

</Tabs>

:::warning
You shouldn't define arguments of a module.
:::

### ✨Argument-level hook

`ExCore` provide a simple way to call argument-level hooks without arguments.

```toml
[Optimizer.AdamW]
# Error
@params = "$Model.parameters()"
weight_decay = 0.01
```

If you want to call a class or static method.

```toml
[Model.XXX]
# Error
$backbone = "A.from_pretained()"
```

Attributes can also be used.

```toml
[Model.XXX]
# Error
!channel = "$Block.out_channel"
```

It also can be chained invoke.

```toml
[Model.XXX]
# Error
!channel = "$Block.last_conv.out_channels"
```

This way requsts you to define such methods or attributes in target class and can not pass arguments. So `ExCore` provides `ConfigArgumentHook`.

```python
class ConfigArgumentHook(node, enabled)
```

You need to implements your own class inherited from `ConfigArgumentHook`. For example:

```python
from excore.engine.hook import ConfigArgumentHook

from . import HOOKS


@HOOKS.register()
class BnWeightDecayHook(ConfigArgumentHook):
    def __init__(self, node, enabled: bool, bn_weight_decay: bool, weight_decay: float):
        super().__init__(node, enabled)
        self.bn_weight_decay = bn_weight_decay
        self.weight_decay = weight_decay

    def hook(self):
        model = self.node()
        if self.bn_weight_decay:
            optim_params = model.parameters()
        else:
            p_bn = [p for n, p in model.named_parameters() if "bn" in n]
            p_non_bn = [p for n, p in model.named_parameters() if "bn" not in n]
            optim_params = [
                {"params": p_bn, "weight_decay": 0},
                {"params": p_non_bn, "weight_decay": self.weight_decay},
            ]
        return optim_params

```

```toml
[Optimizer.SGD]
# Error
@params = "$Model@BnWeightDecayHook"
lr = 0.05
momentum = 0.9
weight_decay = 0.0001

[ConfigHook.BnWeightDecayHook]
weight_decay = 0.0001
bn_weight_decay = false
enabled = true
```

Use `@` to call user defined hooks.

### ✨Lazy Config with simple API

The core conception of LazyConfig is 'Lazy', which represents a status of delay. Before instantiating, all the parameters will be stored in a special dict which additionally contains what the target class is. So It's easy to alter any parameters of the module and control which module should be instantiated and which module should not.

It's also used to address the defects of plain text configs through python lsp which is able to provide code navigation, auto-completion and more.

`ExCore` implements some nodes - `MoudleNode`, `InternNode`, `ReusedNode`, `ClassNode`, `ConfigHookNode`, `ChainedInvocationWrapper` and `VariableReference` and a `LazyConfig` to manage all nodes.

Typically, we follow the following procedure.

```python
from excore import config
layz_cfg = config.load('xxx.toml')
module_dict, run_info = config.build_all(layz_cfg)
```

The results of `build_all` are respectively `Primary` modules and `Isolated` objects.

If you only want to use a certain module.

```python
from excore import config
layz_cfg = config.load('xxx.toml')
model = lazy_cfg.Model() # Model is one of `PrimaryFields`
# or
model = layz_cfg['Model']()
```

If you want to follow other logic to build modules, you can still use `LazyConfig` to adjust the arguments of `node`s and more things.

```python
from excore import config
layz_cfg = config.load('xxx.toml')
lazy_cfg.Model.add_params(pre_trained='./')

module_dict, run_info = config.build_all(layz_cfg)
```

### Config print

```python
from excore import config
cfg = config.load_config('xx.toml')
print(cfg)
```

Result:

```
╒══════════════════════════╤══════════════════════════════════════════════════════════════════════╕
│ size                     │ 1024                                                                 │
├──────────────────────────┼──────────────────────────────────────────────────────────────────────┤
│ TrainData.CityScapes     │ ╒═════════════╤════════════════════════════════════════════════════╕ │
│                          │ │ &train_size │ size                                               │ │
│                          │ ├─────────────┼────────────────────────────────────────────────────┤ │
│                          │ │ !transforms │ ['RandomResize', 'RandomFlip', 'Normalize', 'Pad'] │ │
│                          │ ├─────────────┼────────────────────────────────────────────────────┤ │
│                          │ │ data_path   │ xxx                                                │ │
│                          │ ╘═════════════╧════════════════════════════════════════════════════╛ │
├──────────────────────────┼──────────────────────────────────────────────────────────────────────┤
│ Transform.RandomFlip     │ ╒══════╤═════╕                                                       │
│                          │ │ prob │ 0.5 │                                                       │
│                          │ ├──────┼─────┤                                                       │
│                          │ │ axis │ 0   │                                                       │
│                          │ ╘══════╧═════╛                                                       │
├──────────────────────────┼──────────────────────────────────────────────────────────────────────┤
│ Transform.Pad            │ ╒═══════════╤══════╕                                                 │
│                          │ │ &pad_size │ size │                                                 │
│                          │ ╘═══════════╧══════╛                                                 │
├──────────────────────────┼──────────────────────────────────────────────────────────────────────┤
│ Normalize.std            │ [0.5, 0.5, 0.5]                                                      │
├──────────────────────────┼──────────────────────────────────────────────────────────────────────┤
│ Normalize.mean           │ [0.5, 0.5, 0.5]                                                      │
├──────────────────────────┼──────────────────────────────────────────────────────────────────────┤
│ TestData.CityScapes      │ ╒═════════════╤═══════════════╕                                      │
│                          │ │ !transforms │ ['Normalize'] │                                      │
│                          │ ├─────────────┼───────────────┤                                      │
│                          │ │ &test_size  │ size          │                                      │
│                          │ ├─────────────┼───────────────┤                                      │
│                          │ │ data_path   │ xxx           │                                      │
│                          │ ╘═════════════╧═══════════════╛                                      │
├──────────────────────────┼──────────────────────────────────────────────────────────────────────┤
│ Model.FCN                │ ╒═══════════╤════════════╕                                           │
│                          │ │ @backbone │ ResNet     │                                           │
│                          │ ├───────────┼────────────┤                                           │
│                          │ │ @head     │ SimpleHead │                                           │
│                          │ ╘═══════════╧════════════╛                                           │
...
```
