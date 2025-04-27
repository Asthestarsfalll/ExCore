---
title: hook
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

```python
def __new__(cls, name, bases, attrs):
```

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

```python
def __init__(self, hooks: Sequence[Hook]) -> None:
```
### 🅼 check\_life\_span

```python
@staticmethod
def check_life_span(hook: Hook) -> bool:
```

Checks whether a given \`Hook\` object has exceeded its maximum lifespan.

**Returns:**

- True if the \`Hook\` object has exceeded its maximum lifespan, otherwise False.
### 🅼 exist

```python
def exist(self, stage) -> bool:
```

Determines whether any hooks are registered for a given event stage.

**Parameters:**

- **stage** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): The name of the event stage to check.

**Returns:**

- True if any hooks are registered for the given event stage, otherwise False.
### 🅼 pre\_call

```python
def pre_call(self) -> Any:
```

Called before any hooks are executed during an event stage.
### 🅼 after\_call

```python
def after_call(self) -> Any:
```

Called after all hooks have been executed during an event stage.
### 🅼 \_\_call\_\_

```python
def __call__(self, stage, *inps) -> None:
```

Executes all hooks registered for a given event stage.

**Parameters:**

- **stage** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): The name of the event stage to trigger.
- ***inps**: Input arguments to pass to the hook functions.
### 🅼 call\_hooks

```python
def call_hooks(self, stage, *inps) -> None:
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
