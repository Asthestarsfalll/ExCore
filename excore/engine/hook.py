from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from typing import Any, Callable, Protocol

from excore._exceptions import HookBuildError, HookManagerBuildError

__all__ = ["HookManager", "ConfigHookManager", "Hook"]


class Hook(Protocol):
    """
    Represents a hook that can be used to register callback functions for specific events.

    This class is meant to be used with Python 3.8+ and the `typing.Protocol` type hinting feature.
    It defines the following class-level attributes:

    - __HookType__: A sequence of event types that this hook can handle.
    - __LifeSpan__: The duration (in seconds) that this hook will remain active once registered.
    - __CallInter__: The minimum time (in seconds) between consecutive calls to the callback
        function.
    - __call__: The callback function that will be executed when an event of the specified type
        occurs.

    Note: This class cannot be instantiated directly, but it can be used to define other classes
        or functions that implement its interface.
    """

    __HookType__: Sequence[Any]
    __LifeSpan__: float
    __CallInter__: int
    __call__: Callable


class MetaHookManager(type):
    stages: tuple[str, ...] = ()
    """
    A metaclass that is used to validate the `stages` attribute of a `HookManager` subclass.

    This metaclass is responsible for enforcing the following rules:

    1. The `stages` attribute must be defined as a list or tuple of strings.
    2. The `HookManager` subclass must have a valid `stages` attribute.

    Args:
        type (type): The type of the class being created.
        name (str): The name of the class being created.
        bases (tuple): The base classes of the class being created.
        attrs (dict): A dictionary of attributes for the class being created.

    Returns:
        The new instance of the `HookManager` class.

    Raises:
        HookManagerBuildError: If the `HookManager` class does not have a valid `stages` attribute.
    """

    def __new__(cls, name, bases, attrs):
        """
        Overrides the default `__new__` method to validate the `stages` attribute.

        Returns:
            The new instance of the `HookManager` subclass.

        Raises:
            HookManagerBuildError: If the `HookManager` subclass does not have
                a valid `stages` attribute.
        """
        inst = type.__new__(cls, name, bases, attrs)
        stages = inst.stages
        if inst.__name__ != "HookManager" and not stages:
            raise HookManagerBuildError(
                f"The hook manager `{inst.__name__}` must have valid stages"
            )

        return inst


class HookManager(metaclass=MetaHookManager):
    stages: tuple[str, ...] = tuple()
    """
    Manages a set of hooks that can be triggered by events that occur during program execution.

    This class uses the `MetaHookManager` metaclass to validate its `stages` attribute,
        which must be defined as a tuple of string values. Each string represents a distinct "stage"
        in the program execution where hooks can be triggered.

    Args:
        hooks (Sequence[Hook]): A sequence of `Hook` objects to be registered with the manager.

    Attributes:
        hooks (defaultdict[list]): A dictionary mapping event stages to lists of `Hook` objects.
        calls (defaultdict[int]): A dictionary tracking the number of times each event stage
            has been called.

    Methods:
        check_life_span(hook: Hook) -> bool: Checks whether a given `Hook` object has exceeded
            its maximum lifespan.
        exist(stage: str) -> bool: Determines whether any hooks are registered for
            a given event stage.
        pre_call() -> None: Called before any hooks are executed during an event stage.
        after_call() -> None: Called after all hooks have been executed during an event stage.
        __call__(stage: str, *inps) -> None: Executes all hooks registered for a given event stage.
        call_hooks(stage: str, *inps) -> None: Convenience method for calling all hooks
            at a given event stage.

    Raises:
        HookBuildError: If any `Hook` object passed to the constructor has invalid attributes.

    Note: This class is meant to be subclassed to define more specific hook managers
        for different applications.
    """

    def __init__(self, hooks: Sequence[Hook]) -> None:
        assert isinstance(hooks, Sequence)

        __error_msg = "The hook `{}` must have a valid `{}`, got {}"
        for h in hooks:
            if not hasattr(h, "__HookType__") or h.__HookType__ not in self.stages:
                raise HookBuildError(
                    __error_msg.format(h.__class__.__name__, "__HookType__", h.__HookType__)
                )
            if not hasattr(h, "__LifeSpan__") or h.__LifeSpan__ <= 0:
                raise HookBuildError(
                    __error_msg.format(h.__class__.__name__, "__LifeSpan__", h.__LifeSpan__)
                )
            if not hasattr(h, "__CallInter__") or h.__CallInter__ <= 0:
                raise HookBuildError(
                    __error_msg.format(h.__class__.__name__, "__CallInter__", h.__CallInter__)
                )
        self.hooks = defaultdict(list)
        self.calls: dict[str, int] = defaultdict(int)
        for h in hooks:
            self.hooks[h.__HookType__].append(h)

    @staticmethod
    def check_life_span(hook: Hook) -> bool:
        """
        Checks whether a given `Hook` object has exceeded its maximum lifespan.

        Returns:
            True if the `Hook` object has exceeded its maximum lifespan, otherwise False.
        """
        hook.__LifeSpan__ -= 1
        return hook.__LifeSpan__ <= 0

    def exist(self, stage) -> bool:
        """
        Determines whether any hooks are registered for a given event stage.

        Args:
            stage (str): The name of the event stage to check.

        Returns:
            True if any hooks are registered for the given event stage, otherwise False.
        """
        return self.hooks[stage] != []

    def pre_call(self) -> Any:
        """
        Called before any hooks are executed during an event stage.
        """
        return

    def after_call(self) -> Any:
        """
        Called after all hooks have been executed during an event stage.
        """
        return

    def __call__(self, stage, *inps) -> None:
        """
        Executes all hooks registered for a given event stage.

        Args:
            stage (str): The name of the event stage to trigger.
            *inps: Input arguments to pass to the hook functions.
        """
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

    def call_hooks(self, stage, *inps) -> None:
        """
        Convenience method for calling all hooks at a given event stage.

        Args:
            stage (str): The name of the event stage to trigger.
            *inps: Input arguments to pass to the hook functions.
        """
        self.pre_call()
        self(stage, *inps)
        self.after_call()


class ConfigHookManager(HookManager):
    stages: tuple[str, ...] = ("pre_build", "every_build", "after_build")
    """A subclass of HookManager that allows hooks to be registered and executed
    at specific points in the build process.

    Attributes:
        stages (tuple): A tuple containing three strings representing the different
            points in the build process where hooks can be executed. The stages are:
            "pre_build", "every_build", and "after_build".
    """
