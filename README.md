# ExCore

Build your own development toolkit efficiently.

`ExCore` is still in an early development stage.

Docments will be supported soon.

## Features

### Config System

Config system in `ExCore` is based on `toml`, and has following features.

<details>
  <summary>Get rid of `type`</summary>

  ```yaml
  Model:
    type: ResNet
    layers: 50
    num_classes: 1

  ```

  ```toml
  [Model.FCN]
  layers = 50
  num_classes = 1
  ```
</details>

<details>
  <summary>Eliminate components nesting</summary>

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
  ```toml
  [TrainData.Cityscapes]
  dataset_root = "data/cityscapes"
  mode = 'train'
  # use `!` to show this is a module, It's formal to use a quoted key "!transforms", but whatever
  !transforms = ["ResizeStepScale", "RandomPaddingCrop", "Normalize"]

  [ResizeStepScale]
  min_scale_factor = 0.5
  max_scale_factor = 2.0
  scale_step_size = 0.25

  # or explicitly specify which `Registry` it belongs to.
  [Transforms.RandomPaddingCrop]
  crop_size = [1024, 512]

  [Normalize]

  ```

</details>

<details>
  <summary> :sparkles:Auto-complement for config files </summary>

  ![](https://user-images.githubusercontent.com/72954905/267884541-56e75031-48a2-4768-8a6c-fc7b83ed977e.gif)

</details>

</details>

<details>
  <summary>Support reused module</summary>

  ```toml
  # use `@` to mark the reused module
  # FCN and SegNet will use the same ResNet 
  [Model.FCN]
  @backbone = "ResNet"

  [Model.SegNet]
  @backbone = "ResNet"

  [ResNet]
  layers = 50
  in_channel = 3

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
