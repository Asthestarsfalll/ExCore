---
sidebar_position: 1
title: Welcome to ExCore
---

:::info What is ExCore
ExCore is a Configuration/Registry System designed for deeplearning, with some utils.
:::

## What inspired ExCore

:::info ExCore wouldn't exist if not for the previous work of others.
Deeplearning:

1. [MMCV](https://github.com/open-mmlab/mmcv)
2. [MMEngine](https://github.com/open-mmlab/mmengine)
3. [PaddleSeg](https://github.com/PaddlePaddle/PaddleSeg)
4. [PaddleDetection](https://github.com/PaddlePaddle/PaddleDetection)
5. [detectron2](https://github.com/facebookresearch/detectron2)

LSP:

1. [taplo](https://github.com/tamasfe/taplo)

:::

### Configuration System

The configuration and registry system is a great design. One of it's biggest challenges is that there is a gap between plain text config files(e.g. yaml and json) and python. The loudest complains are about editing features -- config auto-completion and code navigation. It's a awful experience when your program break down just because the name in config is misspelled.

The second challenge is that the codebase is becoming more and more complicted and nesting. Learner must pay more efforts on it. But this is not the topic here, just to mention that to solve this I am starting another project -- [CodeSlim](https://github.com/Asthestarsfalll/CodeSlim)(Just started).

Back to the config system itself, since community has beed suffering from the plain text config files for a long time, some are turn to using Python as config. `MMEngine` introduced a pure Python style configuration just for class code navigation.

```python
from torch.optim import SGD


optimizer = dict(type=SGD, lr=0.1)
```

`detectron2` has a more elegant implementation -- `LazyCall`, which discards the `type` and is able to instantiate recursively.

```python
from detectron2.config import LazyCall
from torch.optim import SGD


optimizer = LazyCall(SGD)(lr=0.1)
```

However, both of them only provide auto-completion and navigation for the class instead of their arguments. This is one of the reasons why ExCore was created.

### Registry System

The [blog](https://ppwwyyxx.com/blog/2023/Registration-Does-Not-Scale-Well/) of ppwwyyxx inspired me a lot. To reduce the unnecessary imports, `ExCore` provides `LazyRegistry`, which store the mappings of class/function name to its `qualname` and dump the mappings to local. When config parsing, the necessary modules will be imported.

Rather than calling it a registry, it's more like providing a tagging feature. With the feature, `ExCore` can find all class/function and statically analysis them, then dump the results in local to support some editing features to config files, see [config extention](./config/config_extention).

### Plain Text Configuration

To be honest, I don't like the Python style config at all. The readability of Python is not as good as YAML or TOML. If using Python, why not just instantiate all modules in a file, then import it if need.

```python
# a.py
model = xxx(a=1,b=2)
optimier = xx(model.parameters())
...

# usage
from configs import a
model = a.model
optimier = a.optimier
...
```

:::info
`ExCore` also supports python style config, see [here](./config/node).
:::

## Some defects

1. Too static.
2. Not fully tested.

## Others

`ExCore` is just a toy now. Dumping data into local is a rough workaround. Build an LSP server may be a more elegant way.
