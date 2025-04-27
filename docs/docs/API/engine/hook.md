---
title: hook
sidebar_position: 3
---

## TOC

- **Classes:**
  - 🅲 [Hook](#🅲-hook) - Represents a hook that can be used to register callback functions for specific events.
  - 🅲 [MetaHookManager](#🅲-metahookmanager)
  - 🅲 [HookManager](#🅲-hookmanager)
  - 🅲 [ConfigHookManager](#🅲-confighookmanager)

## Classes

## 🅲 Hook

```python
class Hook(Protocol):
    __HookType__: Sequence[Any] = None
    __LifeSpan__: float = None
    __CallInter__: int = None
    __call__: Callable = None
```

Represents a hook that can be used to register callback functions for specific events.

This class is meant to be used with Python 3.8\+ and the \`typing.Protocol\` type hinting feature.
It defines the following class-level attributes:

- \_\_HookType\_\_: A sequence of event types that this hook can handle.
- \_\_LifeSpan\_\_: The duration \(in seconds\) that this hook will remain active once registered.
- \_\_CallInter\_\_: The minimum time \(in seconds\) between consecutive calls to the callback
    function.
- \_\_call\_\_: The callback function that will be executed when an event of the specified type
    occurs.

Note: This class cannot be instantiated directly, but it can be used to define other classes
    or functions that implement its interface.
## 🅲 MetaHookManager

```python
class MetaHookManager(type):
    stages: tuple[str, ...] = ()
```


### 🅼 \_\_new\_\_

<details>

<summary>\_\_new\_\_</summary>
```python
def __new__(cls, name, bases, attrs):
    inst = type.__new__(cls, name, bases, attrs)
    stages = inst.stages
    if inst.__name__ != "HookManager" and not stages:
        raise HookManagerBuildError(
            f"The hook manager `{inst.__name__}` must have valid stages"
        )
    return inst
```

</details>


Overrides the default \`\_\_new\_\_\` method to validate the \`stages\` attribute.

**Returns:**

- The new instance of the \`HookManager\` subclass.

**Raises:**

- **[HookManagerBuildError](../-exceptions#🅲-hookmanagerbuilderror)**: If the \`HookManager\` subclass does not have
a valid \`stages\` attribute.
## 🅲 HookManager

```python
class HookManager:
    stages: tuple[str, ...] = tuple()
```


### 🅼 \_\_init\_\_

<details>

<summary>\_\_init\_\_</summary>
```python
def __init__(self, hooks: Sequence[Hook]) -> None:
    assert isinstance(hooks, Sequence)
    __error_msg = "The hook `{}` must have a valid `{}`, got {}"
    for h in hooks:
        if not hasattr(h, "__HookType__") or h.__HookType__ not in self.stages:
            raise HookBuildError(
                __error_msg.format(
                    h.__class__.__name__, "__HookType__", h.__HookType__
                )
            )
        if not hasattr(h, "__LifeSpan__") or h.__LifeSpan__ <= 0:
            raise HookBuildError(
                __error_msg.format(
                    h.__class__.__name__, "__LifeSpan__", h.__LifeSpan__
                )
            )
        if not hasattr(h, "__CallInter__") or h.__CallInter__ <= 0:
            raise HookBuildError(
                __error_msg.format(
                    h.__class__.__name__, "__CallInter__", h.__CallInter__
                )
            )
    self.hooks = defaultdict(list)
    self.calls: dict[str, int] = defaultdict(int)
    for h in hooks:
        self.hooks[h.__HookType__].append(h)
```

</details>

### 🅼 check\_life\_span

```python
@staticmethod
def check_life_span(hook: Hook) -> bool:
    hook.__LifeSpan__ -= 1
    return hook.__LifeSpan__ <= 0
```

Checks whether a given \`Hook\` object has exceeded its maximum lifespan.

**Returns:**

- True if the \`Hook\` object has exceeded its maximum lifespan, otherwise False.
### 🅼 exist

```python
def exist(self, stage) -> bool:
    return self.hooks[stage] != []
```

Determines whether any hooks are registered for a given event stage.

**Parameters:**

- **stage** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): The name of the event stage to check.

**Returns:**

- True if any hooks are registered for the given event stage, otherwise False.
### 🅼 pre\_call

```python
def pre_call(self) -> Any:
    return
```

Called before any hooks are executed during an event stage.
### 🅼 after\_call

```python
def after_call(self) -> Any:
    return
```

Called after all hooks have been executed during an event stage.
### 🅼 \_\_call\_\_

<details>

<summary>\_\_call\_\_</summary>
```python
def __call__(self, stage, *inps) -> None:
    dead_hook_idx: list[int] = []
    calls = self.calls[stage]
    for idx, hook in enumerate(self.hooks[stage]):
        if calls % hook.__CallInter__ == 0:
            res = hook(*inps)
            if res and self.check_life_span(hook):
                dead_hook_idx.append(idx - len(dead_hook_idx))
    for idx in dead_hook_idx:
        self.hooks[stage].pop(idx)
    self.calls[stage] = calls + 1
```

</details>


Executes all hooks registered for a given event stage.

**Parameters:**

- **stage** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): The name of the event stage to trigger.
- ***inps**: Input arguments to pass to the hook functions.
### 🅼 call\_hooks

```python
def call_hooks(self, stage, *inps) -> None:
    self.pre_call()
    self(stage, *inps)
    self.after_call()
```

Convenience method for calling all hooks at a given event stage.

**Parameters:**

- **stage** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): The name of the event stage to trigger.
- ***inps**: Input arguments to pass to the hook functions.
## 🅲 ConfigHookManager

```python
class ConfigHookManager(HookManager):
    stages: tuple[str, ...] = ("pre_build", "every_build", "after_build")
```
