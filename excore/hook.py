from collections import defaultdict
from typing import Sequence, Protocol, Any, Callable
from ._exceptions import HookBuildError, HookManagerBuildError

__all__ = ["HookManager", "ConfigHookManager", "Hook"]


class Hook(Protocol):
    __HookType__: Sequence[Any]
    __LifeSpan__: float
    __CallInter__: int
    __call__: Callable


class MetaHookManager(type):
    stages = None

    def __new__(cls, name, bases, attrs):
        inst = type.__new__(cls, name, bases, attrs)
        stages = inst.stages
        if inst.__name__ != "HookManager" and stages is None:
            raise HookManagerBuildError(
                "The hook manager `{}` must have valid stages".format(inst.__name__)
            )

        return inst


class HookManager(metaclass=MetaHookManager):
    stages = tuple()

    def __init__(self, hooks: Sequence[Hook]):
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
        self.calls = defaultdict(int)
        for h in hooks:
            self.hooks[h.__HookType__].append(h)

    @staticmethod
    def check_life_span(hook: Hook):
        hook.__LifeSpan__ -= 1
        return hook.__LifeSpan__ <= 0

    def exist(self, stage):
        return self.hooks[stage] != []

    def pre_call(self):
        return

    def after_call(self):
        return

    def __call__(self, stage, *inps):
        dead_hook_idx = []
        calls = self.calls[stage]
        for idx, hook in enumerate(self.hooks[stage]):
            if calls % hook.__CallInter__ == 0:
                res = hook(*inps)
                if res and self.check_life_span(hook):
                    dead_hook_idx.append(idx - len(dead_hook_idx))
        for idx in dead_hook_idx:
            self.hooks[stage].pop(idx)
        self.calls[stage] = calls + 1

    def call_hooks(self, stage, *inps):
        self.pre_call()
        self.__call__(stage, *inps)
        self.after_call()


class ConfigHookManager(HookManager):
    stages = ("pre_build", "every_build", "after_build")
