# ExCore

![](./docs/static/img/lo.png)

`ExCore` 是一个专为深度学习所设计的配置/注册系统，并且带有一些小工具。

:sparkles: `ExCore` 支持配置文件的自动补全、类型提示、文档字符串和代码跳转。

`ExCore` 仍在实验阶段。

[English](./README.md) | 中文

## 特性

### 配置系统

`ExCore` 中的配置系统专为深度学习中的训练(泛指所有相似的部分，如测试、验证等.下同)流程所设计。其核心前提是将配置文件中所要创建的对象分为三类—— `主要`、 `中间` 和 `孤立` 对象。

1. `主要` 对象是指在训练中 **直接** 使用的对象，如模型、优化器等。`ExCore` 会创建并返回这些对象。
2. `中间` 对象是指在训练中 **间接** 使用的对象，如模型的主干、将要传入优化器的模型参数。
3. `孤立` 对象是指 python 内建对象，会在读取配置文件时直接解析，如 int, string, list, dict 等

`ExCore` 扩展了 toml 文件的语法，引入了一些特殊的前缀字符 —— `!`, `@`, `$` 和 '&' 以简化配置文件的定义过程.

本配置系统有以下特性

<details>
  <summary>摆脱 `type`</summary>

```yaml
Model:
  type: ResNet # <----- ugly type
  layers: 50
  num_classes: 1
```

为了摆脱`type`, `ExCore` 将所有注册的名称都视为 `保留字`. `主要` 模块需要定义为 `[PrimaryFields.ModuleName]`. `PrimaryFields` 是一些预先定义的字段, 如 `Model`, `Optimizer`. `ModuleName` 即为注册的名称。

```toml
[Model.FCN]
layers = 50
num_classes = 1
```

</details>

<details>
  <summary>消除模块嵌套</summary>

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

`ExCore` 使用一些特殊的前缀字符来表明一些参数也是模块。后面会介绍更多前缀.

```toml
[TrainData.Cityscapes]
dataset_root = "data/cityscapes"
mode = 'train'
# 使用 `!` 表示这是一个需要实例化的模块。规范来说应该使用引号包裹"!transforms"，但是无所谓
!transforms = ["ResizeStepScale", "RandomPaddingCrop", "Normalize"]

# 中间对象的`PrimaryFields` 可以被省略
[ResizeStepScale]
min_scale_factor = 0.5
max_scale_factor = 2.0
scale_step_size = 0.25

# 也可以显式地指定
[Transforms.RandomPaddingCrop]
crop_size = [1024, 512]

# 没有参数时甚至可以不定义
# [Normalize]

```

</details>

<details>
  <summary> :sparkles: 配置文件自动补全，类型提示，文档字符串和代码跳转</summary>

旧式配置的设计因难以编写（没有自动补全功能）和无法导航到相应的类而饱受诟病。然而语言服务器协议（Language Server Protocol）可用于支持各种代码编辑功能，如自动完成、类型提示和代码导航。通过利用 lsp 和 json_schema，它能够提供自动补全、一些弱类型提示（如果代码注释得很好，如 python 中的标准类型提示，它将实现更多功能）和相应类的文档字符串功能。

![](https://user-images.githubusercontent.com/72954905/267884541-56e75031-48a2-4768-8a6c-fc7b83ed977e.gif)

![config](https://github.com/Asthestarsfalll/ExCore/assets/72954905/2b0e151c-5c2b-4082-9796-d171e211c7c8)

`ExCore` 通过将类名到代码文件位置的映射保存在本地来支持代码跳转的功能。目前只支持neovim, 见 [excore.nvim](https://github.com/Asthestarsfalll/excore.nvim).

![to_class](https://github.com/Asthestarsfalll/ExCore/assets/72954905/9677c204-eb46-4cf3-a8bf-03f9bee8d6fb)

</details>

<details>
  <summary>配置继承</summary>

使用`__base__` 从另一个toml文件继承，只有字典会局部更新，其他类型会直接被覆盖。

```toml
__base__ = ["xxx.toml", "xxxx.toml"]
```

</details>

<details>
  <summary>@复用（共享）模块</summary>

`ExCore` 使用 `@` 来标记重复使用的模块，这些模块可以在不同模块之间共享。

```toml
# FCN 和 SegNet 将会使用同一个 ResNet 对象
[Model.FCN]
@backbone = "ResNet"

[Model.SegNet]
@backbone = "ResNet"

[ResNet]
layers = 50
in_channel = 3
```

等同于

```python
resnet = ResNet(layers=50, in_channel=3)

FCN(backbone=resnet)
SegNet(backbone=resnet)

# 如果使用"!"，那么其等同于

FCN(backbone=ResNet(layers=50, in_channel=3))
SegNet(backbone=ResNet(layers=50, in_channel=3))
```

</details>

<details>
  <summary>$ 引用类和跨文件</summary>

`ExCore` 使用 `$` 来表示使用类本身而不用实例化

```toml
[Model.ResNet]
$block = "BasicBlock"
layers = 50
in_channel = 3
```

等同于

```python
from xxx import ResNet, BasicBlock
ResNet(block=BasicBlock, layers=50, in_channel=3)
```

为了跨文件引用模块，`$` 可以用于 `PrimaryFields` 之前，例如：

文件 A:

```toml
[Block.BasicBlock]
```

文件 B:

```toml
[Block.BottleneckBlock]
```

文件 C:

```toml
[Model.ResNet]
!block="$Block"
```

所以我们可以将文件A C 或文件B C结合

```toml
__base__ = ["A.toml", "C.toml"]
# or
__base__ = ["B.toml", "C.toml"]
```

</details>

<details>
  <summary>&变量引用</summary>

`ExCore` 使用 `&` 来引用配置文件最顶层的变量。

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
  <summary>:sparkles:在配置文件中使用python模块</summary>

`ExCore` 中的注册器可以注册一个模块，如：

```python
from excore import Registry
import torch

MODULE = Registry("module")
MODULE.register_module(torch)
```

然后你可以在配置文件中使用 torch

```toml
[Model.ResNet]
$activation = "torch.nn.ReLU"
# 或者
$activation = "torch.nn.ReLU()"
# 或者, 注意，这里直接使用eval
$activation = "torch.nn.ReLU(inplace=True)"
```

```python
import torch
from xxx import ResNet

ResNet(torch.nn.ReLU)
# 或者
ResNet(torch.nn.ReLU())
# 或者
ResNet(torch.nn.ReLU(inplace=True))
```

</details>

<details>
  <summary>:sparkles:参数级别 Hook</summary>

`ExCore` 提供了一个简单方式调用无参的参数Hook。

```toml
[Optimizer.AdamW]
@params = "$Model.parameters()"
weight_decay = 0.01
```

如果你想要调用一个类方法或者静态方法。

```toml
[Model.XXX]
$backbone = "A.from_pretained()"
```

属性也可以被使用。

```toml
[Model.XXX]
!channel = "$Block.out_channel"
```

也可以链式调用。

```toml
[Model.XXX]
!channel = "$Block.last_conv.out_channels"
```

这种方式要求你在目标类的上定义相应的方法或属性，并且不能传递参数。因此 `ExCore` 提供了 `ConfigArgumentHook`

```python
class ConfigArgumentHook(node, enabled)
```

你需要继承自 `ConfigArgumentHook` 实现自己的类，例如：

```python
from excore import ConfigArgumentHook

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

使用 `@` 来调用用户定义的Hook.

</details>

<details>
  <summary>实例级别 hook</summary>

If the logic of module building are too complicated, instance-level hook may be helpful.

TODO

</details>

<details>
  <summary>:sparkles:Lazy Config with simple API</summary>
LazyConfig 的核心概念是 `Lazy`，它代表一种延迟的状态。在实例化之前，所有参数都会存储在一个特殊的字典中，该字典还包含了目标类/函数是什么。因此，可以很容易地更改模块的任何参数，并控制应该实例化哪个模块，不应该实例化哪个模块。

它还用于通过Python语言服务（LSP）解决纯文本配置的缺陷，Python LSP能够提供代码导航、自动补全等功能。

`ExCore` 实现了一些节点—— `ModuleNode`、`InternNode`、`ReusedNode`、`ClassNode`、`ConfigHookNode`、`GetAttr` 和 `VariableReference`，以及一个 `LazyConfig` 来管理所有节点。

`ExCore` 只提供了两个简单的 API 来构建模块—— `load` 和 `build_all` 。

通常情况下，使用以下代码一键创建所有对象：

```python
from excore import config
layz_cfg = config.load('xxx.toml')
module_dict, run_info = config.build_all(layz_cfg)
```

`build_all` 的结果分别是 `Primary` 模块和 `Isolated` 对象。

如果你只想使用某个特定的模块：

```python
from excore import config
layz_cfg = config.load('xxx.toml')
model = layz_cfg.Model() # Model是`PrimaryFields`之一
# 或者
model = layz_cfg['Model']()
```

如果你想按照其他逻辑构建模块，你仍然可以使用 `LazyConfig` 来调整 `node`s 的参数和其他事情。

```python
from excore import config
layz_cfg = config.load('xxx.toml')
lazy_cfg.Model << dict(pre_trained='./')
# 或者
lazy_cfg.Model.add(pre_trained='./')

module_dict, run_info = config.build_all(layz_cfg)
```

</details>

<details>
  <summary>:sparkles:模块参数验证及延迟赋参</summary>

在模块初始化和调用之前验证参数，这将节省一些连续的耗时初始化的时间。

可以手动设置任何缺少的参数值，其会被解析为字符串、整数、列表、元组或字典。

使用环境变量 `EXCORE_VALIDATE` 和 `EXCORE_MANUAL_SET` 来控制是否进行验证和分配。

</details>

<details>
  <summary>配置打印</summary>

```python
from excore import config
cfg = config.load_config('xx.toml')
print(cfg)
```

结果:

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

为了减少不必要的导入，`ExCore` 提供了 `LazyRegistry`，其可以存储类或函数的名称到它们的 “限制名称” （qualname）映射，并且将映射转储到本地。当配置文件解析时，必要的模块才会被导入。

</details>

<details>
  <summary>存储额外信息</summary>

```python
from excore import Registry

Models = Registry("Model", extra_field="is_backbone")


@Models.register(is_backbone=True)
class ResNet:
    pass

```

</details>

<details>
  <summary>模块分类和模糊搜索</summary>

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
  <summary>一键注册</summary>

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
  <summary>多合一</summary>

可以通过 Registry 来获取所有已定义的注册器，并且可以将它们合并为一个全局注册器。

```python
from excore import Registry

MODEL = Registry.get_registry("Model")

G = Registry.make_global()

```

</details>

<details>
  <summary>:sparkles:注册 python 模块</summary>

`Registry` 不只能够注册类或者函数，还能注册python模块，如:

```python
from excore import Registry
import torch

MODULE = Registry("module")
MODULE.register_module(torch)
```

可以在配置中使用 torch：

```toml
[Model.ResNet]
$activation = "torch.nn.ReLU"
# 或者
!activation = "torch.nn.ReLU"
```

等同于

```python
import torch
from xxx import ResNet

ResNet(torch.nn.ReLU)
# 或者
ResNet(torch.nn.ReLU())
```

</details>

### RoadMap

更多特性可以参照 [Roadmap of ExCore](https://github.com/users/Asthestarsfalll/projects/4)
