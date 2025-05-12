---
title: Registry System
sidebar_position: 3
---

import Tabs from '@theme/Tabs';

import TabItem from '@theme/TabItem';

import styles from '/src/css/tab.css';

## LazyRegistry

The [blog](https://ppwwyyxx.com/blog/2023/Registration-Does-Not-Scale-Well/) of ppwwyyxx inspired `LazyRegistry`. To reduce the unnecessary imports, `ExCore` provides `LazyRegistry`, which store the mappings of class/function name to its `qualname` and dump the mappings to local. When config parsing, the necessary modules will be imported.

Rather than calling it a registry, it's more like providing a tagging feature. With the feature, `ExCore` can find all class/function and statically analysis them, then dump the results in local to support some editing features to config files, see [config extension](../config/config_extension).

## Features

### Extra information

```python
from excore import Registry

Models = Registry("Model", extra_field="is_backbone")


@Models.register(is_backbone=True)
class ResNet:
    pass

```

### Modules classification and fuzzy search

```python
from excore import Registry

Models = Registry("Model", extra_field="is_backbone")


@Models.register(is_backbone=True)
class ResNet:
    pass

@Models.register(is_backbone=True)
class ResNet50:
    pass

@Models.register(is_backbone=True)
class ResNet101:
    pass

@Models.register(is_backbone=False)
class head:
    pass


print(Models.module_table(select_info='is_backbone'))

print(Models.module_table(filter='**Res**'))
```

results:

```
  ╒═══════════╤═══════════════╕
  │ Model     │ is_backbone   │
  ╞═══════════╪═══════════════╡
  │ ResNet    │ True          │
  ├───────────┼───────────────┤
  │ ResNet101 │ True          │
  ├───────────┼───────────────┤
  │ ResNet50  │ True          │
  ├───────────┼───────────────┤
  │ head      │ False         │
  ╘═══════════╧═══════════════╛

  ╒═══════════╕
  │ Model     │
  ╞═══════════╡
  │ ResNet    │
  ├───────────┤
  │ ResNet101 │
  ├───────────┤
  │ ResNet50  │
  ╘═══════════╛
```

### Register all

```python
from torch import optim
from excore import Registry

OPTIM = Registry("Optimizer")


def _get_modules(name: str, module) -> bool:
    if name[0].isupper():
        return True
    return False


OPTIM.match(optim, _get_modules)
print(OPTIM)
```

results:

```
╒════════════╤════════════════════════════════════╕
│ NAME       │ DIR                                │
╞════════════╪════════════════════════════════════╡
│ Adadelta   │ torch.optim.adadelta.Adadelta      │
├────────────┼────────────────────────────────────┤
│ Adagrad    │ torch.optim.adagrad.Adagrad        │
├────────────┼────────────────────────────────────┤
│ Adam       │ torch.optim.adam.Adam              │
├────────────┼────────────────────────────────────┤
│ AdamW      │ torch.optim.adamw.AdamW            │
├────────────┼────────────────────────────────────┤
│ SparseAdam │ torch.optim.sparse_adam.SparseAdam │
├────────────┼────────────────────────────────────┤
│ Adamax     │ torch.optim.adamax.Adamax          │
├────────────┼────────────────────────────────────┤
│ ASGD       │ torch.optim.asgd.ASGD              │
├────────────┼────────────────────────────────────┤
│ SGD        │ torch.optim.sgd.SGD                │
├────────────┼────────────────────────────────────┤
│ RAdam      │ torch.optim.radam.RAdam            │
├────────────┼────────────────────────────────────┤
│ Rprop      │ torch.optim.rprop.Rprop            │
├────────────┼────────────────────────────────────┤
│ RMSprop    │ torch.optim.rmsprop.RMSprop        │
├────────────┼────────────────────────────────────┤
│ Optimizer  │ torch.optim.optimizer.Optimizer    │
├────────────┼────────────────────────────────────┤
│ NAdam      │ torch.optim.nadam.NAdam            │
├────────────┼────────────────────────────────────┤
│ LBFGS      │ torch.optim.lbfgs.LBFGS            │
╘════════════╧════════════════════════════════════╛
```

### All in one

Through Registry to find all registries. Make registries into a global one.

```python
from excore import Registry

MODEL = Registry.get_registry("Model")

G = Registry.make_global()
```

### ✨Register module

`Registry` is able to not only register class or function, but also a python module, for example:

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
