# ExCore

`ExCore` is still in an early development stage.

## Features

### Config System

Config system is the **core** of deeplearning projects which enable us to manage and adjust hyperparameters and expriments. There are some attempts of config system because the whole community has been suffering from the plain text config files for a long while.

Config System in `ExCore` is specifically designed for deeplearning training (generally refers to all similar part, e.g. testing, evaluating) procedure. _The core premise is to categorize the objects to be created in the config into three classes - `Primary`, `Intermediate`, and `Isolated` objects_

1. `Primary` objects are those which are **directly** used in training, e.g. model, optimizer. `ExCore` will instantiate and return them.
2. `Intermediate` objects are those which are **indirectly** used in training, e.g. backbone of the model, parameters of model that will pass to optimizer. `ExCore` will instantiate them, and pass them to target `Primary` objects as arguments according some rules.
3. `Isolated` objects refer to python built-in objects which will be parsed when loading toml, e.g. int, string, list and dict.

`ExCore` extends the syntax of toml file, introducing some special prefix characters -- `!`, `@`, `$` and '&' to simplify the config defination.

The config system has following features.

<details>
  <summary>Get rid of `type`</summary>

```yaml
Model:
  type: ResNet # <----- ugly type
  layers: 50
  num_classes: 1
```

In order to get rid of `type`, `ExCore` regards all registered names as `reserved words`. The `Primary` module need to be defined like `[PrimaryName.ModuleName]`. `PrimaryName` are some pre-defined fields, e.g. `Model`, `Optimizer`. `ModuleName` are registered names.

```toml
[Model.FCN]
layers = 50
num_classes = 1
```

</details>

<details>
  <summary>Eliminate modules nesting</summary>

```yaml
TrainData:
  type: Cityscapes
  dataset_root: data/cityscapes
  transforms:
   - type: ResizeStepScale
     min_scale_factor: 0.5
     max_scale_factor: 2.0
     scale_step_size: 0.25
   - type: RandomPaddingCrop
        crop_size: [1024, 512]
   - type: Normalize
  mode: train

```

`ExCore` use some special prefix characters to specify certain arguments are modules as well. More prefixes will be introduced later.

```toml
[TrainData.Cityscapes]
dataset_root = "data/cityscapes"
mode = 'train'
# use `!` to show this is a module, It's formal to use a quoted key "!transforms", but whatever
!transforms = ["ResizeStepScale", "RandomPaddingCrop", "Normalize"]

# `PrimaryName` can be omitted in defination of `Intermediate` module
[ResizeStepScale]
min_scale_factor = 0.5
max_scale_factor = 2.0
scale_step_size = 0.25

# or explicitly specify ``PrimaryName
[Transforms.RandomPaddingCrop]
crop_size = [1024, 512]

# It can even be undefined when there are no arguments
# [Normalize]

```

</details>

<details>
  <summary> :sparkles:Auto-complement for config files </summary>

The old-style design of plain text configs has been criticized for being difficult to write (without auto-completion) and not allowing navigation to the corresponding class. However, Language Server Protocol can be leveraged to support various code editing features, such as auto-completion, type-hinting, and code navigation. By utilizing lsp and json schema, it's able to provide the ability of auto-completion, some weak type-hinting (If code is well annotated, such as standard type hint in python, it will acheive more) and docstring of corresponding class.

![](https://user-images.githubusercontent.com/72954905/267884541-56e75031-48a2-4768-8a6c-fc7b83ed977e.gif)

![config](https://github.com/Asthestarsfalll/ExCore/assets/72954905/2b0e151c-5c2b-4082-9796-d171e211c7c8)

</details>

<details>
  <summary>Config inheritance</summary>
Use `__base__` to inherit from a toml file.  Only dict can be updated locally, other types are overwritten directly.

```toml
__base__ = ["xxx.toml", "xxxx.toml"]
```

</details>

<details>
  <summary>`@`Reused module</summary>

`ExCore` use `@` to mark the reused module, which is shared between different modules.

```toml
# FCN and SegNet will use the same ResNet object
[Model.FCN]
@backbone = "ResNet"

[Model.SegNet]
@backbone = "ResNet"

[ResNet]
layers = 50
in_channel = 3

```

equls to

```python
resnet = ResNet(layers=50, in_channel=3)

FCN(backbone=resnet)
SegNet(backbone=resnet)

# If use `!`, it equls to

FCN(backbone=ResNet(layers=50, in_channel=3))
SegNet(backbone=ResNet(layers=50, in_channel=3))
```

</details>

<details>
  <summary>`$`Class and cross file</summary>

`ExCore` use `$` to represents class itself, which will not be instantiated.

```toml
[Model.ResNet]
$block = "BasicBlock"
layers = 50
in_channel = 3
```

equls to

```python
from xxx import ResNet, BasicBlock
ResNet(block=BasicBlock, layers=50, in_channel=3)
```

In order to refer module accross files, `$` can be used before `PrimaryName`. For example:

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
!block="$Block"
```

So we can combine file A and C or file B and C with a toml file

```toml
__base__ = ["A.toml", "C.toml"]
# or
__base__ = ["B.toml", "C.toml"]
```

</details>

<details>
  <summary>`&`Variable reference</summary>

`ExCore` use `&` to refer a variable from the top-level of config.

**Note: The value may be overwritten when inheriting, so the call it variable.**

```toml
size = 224

[TrainData.ImageNet]
&train_size = "size"
!transforms = ['RandomResize', 'Pad']
data_path = 'xxx'

[Transform.Pad]
&pad_size = "size"

[TestData.ImageNet]
!transforms = ['Normalize']
&test_size = "size"
data_path = 'xxx'
```

</details>

<details>
  <summary>:sparkles:Argument-level hook</summary>

`ExCore` provide a simple way to call argument-level hooks without arguments.

```toml
[Optimizer.AdamW]
@params = "$Model.parameters()"
weight_decay = 0.01
```

If you want to call a class or static method.

```toml
[Model.XXX]
$backbone = "A.from_pretained()"
```

Attributes can also be used.

```toml
[Model.XXX]
!channel = "$Block.out_channel"
```

It also can be chained invoke.

```toml
[Model.XXX]
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

</details>

<details>
  <summary>Instance-level hook</summary>

If the logic of module building are overwhelming complicated, instance-level hook may be helpful.

</details>

<details>
  <summary>:sparkles:Lazy Config with simple API</summary>
The core conception of LazyConfig is 'Lazy', which represents a status of delay. Before instantiating, all the parameters will be stored in a special dict which additionally contains what the target class is. So It's easy to alter any parameters of the module and control which module should be instantiated and which module should not.

It's also used to address the defects of plain text configs through python lsp which is able to provide code navigation, auto-completion and more.

`ExCore` implements some nodes - `MoudleNode`, `InternNode`, `ReusedNode`, `ClassNode`, `ConfigHookNode`, `ChainedInvocationWrapper` and `VariableReference` and a `LazyConfig` to manage all nodes.

`ExCore` provides only 2 simple API to build moduels -- 'load' and `build_all`.

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
model = lazy_cfg.Model() # Model is one of `PrimaryName`
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

</details>

<details>
  <summary>Config print</summary>

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

</details>

### Registry

<details>
  <summary>Extra information registed with componments</summary>

```python
from excore import Registry

Models = Registry("Model", extra_field="is_backbone")


@Models.register(is_backbone=True)
class ResNet:
    pass

```

</details>

<details>
  <summary>Componments classification and fuzzy search</summary>

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

</details>

<details>
  <summary>Register all</summary>

```python
from excore import Registry

from xxx import yyy

Models = Registry('Model')

def match_methods(name: str) -> bool:
    pass

# Register all module with match_methods
Models.match(yyy, match_methods)
```

</details>

<details>
  <summary>Register all</summary>

```python
from excore import Registry

from xxx import yyy

Models = Registry('Model')

def match_methods(name: str) -> bool:
    pass

# Register all module with match_methods
Models.match(yyy, match_methods)
```

</details>

### RoadMap

For more features you may refer to [Roadmap of ExCore](https://github.com/users/Asthestarsfalll/projects/4)
