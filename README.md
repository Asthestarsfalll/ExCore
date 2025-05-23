# ExCore

![](./docs/static/img/lo.png)

`ExCore` is a Configuration/Registry System designed for deeplearning, with some utils.

:sparkles: `ExCore` supports auto-completion, type-hinting, docstring and code navigation for config files

`ExCore` is still in an early development stage.

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/Asthestarsfalll/ExCore)

[Documentation](https://excore.onism.space/)

English | [中文](./README_cn.md)

## Features

### Config System

Config system is the **core** of deeplearning projects which enable us to manage and adjust hyperparameters and expriments. There are some attempts of config system because the whole community has been suffering from the plain text config files for a long while.

Config System in `ExCore` is specifically designed for deeplearning training (generally refers to all similar part, e.g. testing, evaluating) procedure. _The core premise is to categorize the objects to be created in the config into three classes - `Primary`, `Intermediate`, and `Isolated` objects_

1. `Primary` objects are those which are **directly** used in training, e.g. model, optimizer. `ExCore` will instantiate and return them.
2. `Intermediate` objects are those which are **indirectly** used in training, e.g. backbone of the model, parameters of model that will pass to optimizer. `ExCore` will instantiate them, and pass them to target `Primary` objects as arguments according some rules.
3. `Isolated` objects refer to python built-in objects which will be parsed when loading toml, e.g. int, string, list and dict.

`ExCore` extends the syntax of toml file, introducing some special prefix characters -- `!`, `@`, `$` and `&` to simplify the config definition.

So we introduce some terminologies in ExCore:

1. `PrimaryField`: e.g. Model, TrainData, TestData and so on.
2. `RegistryName`: The name of a Registry, e.g. Models, Datasets, Losses and so on. It can be the same as `PrimaryField`.
3. `ModuleName`: All registered items (class, function, module) are called Module. So the name of it is `ModuleName`.

The config system has following features.

<details>
  <summary>Get rid of `type`</summary>

```yaml
Model:
  type: ResNet # <----- ugly type
  layers: 50
  num_classes: 1
```

In order to get rid of `type`, `ExCore` regards all registered names as `reserved words`. The `Primary` module need to be defined like `[PrimaryField.ModuleName]`. `PrimaryField` are some pre-defined fields, e.g. `Model`, `Optimizer`. `ModuleName` are registered names.

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

# `PrimaryField` can be omitted in definition of `Intermediate` module
[ResizeStepScale]
min_scale_factor = 0.5
max_scale_factor = 2.0
scale_step_size = 0.25

# or explicitly specify `PrimaryField`
[Transforms.RandomPaddingCrop]
crop_size = [1024, 512]

# It can even be undefined when there are no arguments
# [Normalize]

```

</details>

<details>
  <summary> :sparkles:Auto-complement, type-hinting, docstring and code navigation for config files </summary>

The old-style design of plain text configs has been criticized for being difficult to write (without auto-completion) and not allowing navigation to the corresponding class. However, Language Server Protocol can be leveraged to support various code editing features, such as auto-completion, type-hinting, and code navigation. By utilizing lsp and json schema, it's able to provide the ability of auto-completion, some weak type-hinting (If code is well annotated, such as standard type hint in python, it will achieve more) and docstring of corresponding class.

![](https://user-images.githubusercontent.com/72954905/267884541-56e75031-48a2-4768-8a6c-fc7b83ed977e.gif)

![config](https://github.com/Asthestarsfalll/ExCore/assets/72954905/2b0e151c-5c2b-4082-9796-d171e211c7c8)

`ExCore` dump the mappings of class name and it file location to support code navigation. Currently only support for neovim, see [excore.nvim](https://github.com/Asthestarsfalll/excore.nvim).

![to_class](https://github.com/Asthestarsfalll/ExCore/assets/72954905/9677c204-eb46-4cf3-a8bf-03f9bee8d6fb)

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
  <summary>`$`Refer Class and cross file</summary>

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

In order to refer module across files, `$` can be used before `PrimaryField`. For example:

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

`&` can use in the parameters as well. It's always used with the argument hooks. Refer to `finegrained_config`.

</details>

<details>
  <summary>:sparkles:Using python module in config file</summary>

The `Registry` in `ExCore` is able to register a module:

```python
from excore import Registry
import torch

MODULE = Registry("module")
MODULE.register_module(torch)
```

Then you can use torch in config file:

```toml
[Model.ResNet]
$activation = "torch.nn.ReLU"
# or
$activation = "torch.nn.ReLU()"
# or, note: implement with eval
$activation = "torch.nn.ReLU(inplace)"
```

```python
import torch
from xxx import ResNet

ResNet(torch.nn.ReLU)
# or
ResNet(torch.nn.ReLU())
# or
ResNet(torch.nn.ReLU(inplace=True))
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

This way requests you to define such methods or attributes in target class and can not pass arguments. So `ExCore` provides `ConfigArgumentHook`.

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

If the logic of module building are too complicated, instance-level hook may be helpful.

TODO

</details>

<details>
  <summary>:sparkles:Lazy Config with simple API</summary>
The core conception of LazyConfig is 'Lazy', which represents a status of delay. Before instantiating, all the parameters will be stored in a special dict which additionally contains what the target class is. So It's easy to alter any parameters of the module and control which module should be instantiated and which module should not.

It's also used to address the defects of plain text configs through python lsp which is able to provide code navigation, auto-completion and more.

`ExCore` implements some nodes - `ModuleNode`, `InternNode`, `ReusedNode`, `ClassNode`, `ConfigHookNode`, `GetAttr` and `VariableReference` and a `LazyConfig` to manage all nodes.

`ExCore` provides only 2 simple API to build modules -- 'load' and `build_all`.

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
model = lazy_cfg.Model() # Model is one of `PrimaryField`
# or
model = layz_cfg['Model']()
```

If you want to follow other logic to build modules, you can still use `LazyConfig` to adjust the arguments of `node`s and more things.

```python
from excore import config
layz_cfg = config.load('xxx.toml')
lazy_cfg.Model << dict(pre_trained='./')
# or
lazy_cfg.Model.add(pre_trained='./')

module_dict, run_info = config.build_all(layz_cfg)
```

</details>

<details>
  <summary>:sparkles:Module validation and lazy assignment</summary>

Validate parameters of modules before their initialization and call, which will save time from some serial long initialization.

If there is any parameter missing, you can manually assign it to avoid crushing. It will be parsed to str, int, list, tuple, or dict.

Use environment variable `EXCORE_VALIDATE` and `EXCORE_MANUAL_SET` to control whether validate and assign.

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
  <summary>:sparkles:LazyRegistry</summary>
To reduce the unnecessary imports, `ExCore` provides `LazyRegistry`, which store the mappings of class/function name to its `qualname` and dump the mappings to local. When config parsing, the necessary modules will be imported.

</details>

<details>
  <summary>Extra information</summary>

```python
from excore import Registry

Models = Registry("Model", extra_field="is_backbone")


@Models.register(is_backbone=True)
class ResNet:
    pass

```

</details>

<details>
  <summary>Modules classification and fuzzy search</summary>

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

</details>

<details>
  <summary>All in one</summary>

Through Registry to find all registries. Make registries into a global one.

```python
from excore import Registry

MODEL = Registry.get_registry("Model")

G = Registry.make_global()

```

</details>

<details>
  <summary>:sparkles:Register module</summary>

`Registry` is able to not only register class or function, but also a python module, for example:

```python
from excore import Registry
import torch

MODULE = Registry("module")
MODULE.register_module(torch)
```

Then you can use torch in config file:

```toml
[Model.ResNet]
$activation = "torch.nn.ReLU"
# or
!activation = "torch.nn.ReLU"
```

equls to

```python
import torch
from xxx import ResNet

ResNet(torch.nn.ReLU)
# or
ResNet(torch.nn.ReLU())
```

</details>

### Plugins

<details>
  <summary>PathManager</summary>

Manage paths in a structured manner for creating directories, if the scoped functions fail, it can automatically delete the created directories.

```python
from excore.plugins.path_manager import PathManager

with PathManager(
    base_path = "./exp",
    sub_folders=["folder1", "folder2"],
    config_name="config_dir",
    instance_name="test1",
    remove_if_fail=True,
    sub_folder_exist_ok=False,
    config_name_first=False,
    return_str=True,
) as pm:
    folder1_path:str = pm.get("folder1")
    folder2_path:str = pm.get("folder2")
    do_sth(folder1_path, folder2_path)
    train()
```

The structure will be

```
exp
├── folder1
│   └── config_dir
│       └── test1
└── folder2
    └── config_dir
        └── test1
```

You can also use the dataclass for a better experience:

```python
from dataclasses import dataclass

from excore.plugins.path_manager import PathManager


@dataclass
class SubPath:
    folder1: str = "folder1"
    folder2: str = "folder2"

sub_path = SubPath()

with PathManager(
    base_path = "./exp",
    sub_folders=sub_path,
    config_name="config_dir",
    instance_name="test1",
    remove_if_fail=True,
    sub_folder_exist_ok=False,
    config_name_first=False,
    return_str=True,
) as pm:
    folder1_path:str = sub_path.folder1
    folder2_path:str = sub_path.folder2
    do_sth(folder1_path, folder2_path)
    train()
```

</details>

<details>
  <summary>:sparkles:Fine-Grained Config</summary>

Refer to YOLO-style configuration to enable fine-grained control over model architecture."

Firstly, we need to add more some information to the registered class that we want to configure fine-grainedly.

```python
from excore import Registry

MODEL = Registry("Model", extra_field=["receive", "send"])
MODEL.register_module(nn.Conv2d, receive="in_channels", send="out_channels")
MODEL.register_module(nn.BatchNorm2d, receive="num_features", send="num_features")
```

`receive` should be a str or a list of str, which contains the parameter names during the passing procedures. So is `send`.

Secondly, enable the `fine-grained config` by

```python
from excore.plugins.finegrained_config import enable_finegrained_config

enable_finegrained_config()
```

Thirdly, use `*` to define the finegrained_config. There are 3 required parameters:

- `$class_mapping`: List of class names to be used
- `info`: List of [repeat_times, module_index] for each layer
- `args`: Arguments list for each layer's initialization

```toml
class_mapping = ['Conv2d', 'BatchNorm2d']
[Backbone.FinegrainedModel]
$backbone = "torch.nn.Sequential*FinegrainedConfig"

[FinegrainedConfig]
$class_mapping = "&class_mapping"
# [from, number, module idx]
info = [
  [1, 0],
  [3, 0],
  [1, 1],
  [2, 0],
  [1, 1],
]
args = [
  [3],
  [32, 3],
  [64, 3],
  [128],
  [224, 1],
  [224],
]

```
`$backbone = "torch.nn.Sequential*$ConfigInfo::backbone"` where `torch.nn.Sequential` is the wrapper of the results of `FinegrainedConfig`. `*FinegrainedConfig` means apply the `finegrained_config` hook and get its initialize parameters from dict `FinegrainedConfig`.

The finegrained_config will pass the parameters according to `receive` and `send` names of each class.

Finally the `backbone` will be:

```bash
Sequential(
  (0): Conv2d(3, 32, kernel_size=(3, 3), stride=(1, 1))
  (1): Conv2d(32, 64, kernel_size=(3, 3), stride=(1, 1))
  (2): Conv2d(32, 64, kernel_size=(3, 3), stride=(1, 1))
  (3): Conv2d(32, 64, kernel_size=(3, 3), stride=(1, 1))
  (4): BatchNorm2d(64, eps=128, momentum=0.1, affine=True, track_running_stats=True)
  (5): Conv2d(64, 224, kernel_size=(1, 1), stride=(1, 1))
  (6): Conv2d(64, 224, kernel_size=(1, 1), stride=(1, 1))
  (7): BatchNorm2d(224, eps=224, momentum=0.1, affine=True, track_running_stats=True)
)
```

</details>

### RoadMap

For more features you may refer to [Roadmap of ExCore](https://github.com/users/Asthestarsfalll/projects/4)
