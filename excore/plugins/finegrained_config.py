from __future__ import annotations

from typing import TYPE_CHECKING, Any

from excore._exceptions import CoreConfigParseError
from excore.config.models import (
    ConfigArgumentHook,
    ConfigHookNode,
    ModuleNode,
    register_argument_hook,
)
from excore.engine.registry import Registry

if TYPE_CHECKING:
    from typing import Union

    from excore.config import ConfigDict, ConfigNode

    ArgType = Union[int, float, bool, str, list, dict]


def _get_info_dict(index: str, config: ConfigDict) -> dict | None:
    if not index.startswith("$"):
        return config.pop(index, None)
    for idx in index[1:].split("::"):
        if not (config := config.pop(idx, None)):
            raise CoreConfigParseError(f"{index}")
    return config


def _check_info(info: dict) -> None:
    excepted_keys = ["$class_mapping", "info", "args"]
    for key in excepted_keys:
        if key not in info:
            raise CoreConfigParseError(f"Excepted keys {excepted_keys}, but cannot found {key}.")


def _get_rcv_snd(module: type) -> list[str | list[str]]:
    module_name = module.__name__
    registry_name = Registry.find(module_name)[1]
    assert registry_name is not None
    reg = Registry.get_registry(registry_name)
    keys = [FinegrainedConfig.rcv_key, FinegrainedConfig.snd_key]
    for k in keys:
        if k not in reg.extra_field:
            raise CoreConfigParseError(f"`{k}` must in extra_field of Registry `{registry_name}`.")
    return [reg.get_extra_info(module_name, k) for k in keys]


def _to_list(item: str | list[str]) -> list[str]:
    if isinstance(item, str):
        return [item]
    return item


def _construct_kwargs(
    passby_args: list[ArgType], args: list[ArgType], param_names: list[str], receive: list[str]
) -> dict[str, ArgType]:
    kwargs = {n: a for n, a in zip(receive, passby_args)}
    param_names = [i for i in param_names if i not in receive]
    if len(args) > len(param_names):
        raise RuntimeError(f"Expected length of `{args}` to be less than f`{len(param_names)}.`")
    kwargs.update({n: a for n, a in zip(param_names, args)})
    return kwargs


class FinegrainedConfig(ConfigArgumentHook):
    rcv_key: str = "receive"
    snd_key: str = "send"

    def __init__(
        self,
        node: ModuleNode,
        class_mapping: list[type],
        info: list[list[int]],
        args: list[list[ArgType]],
        enabled: bool = True,
    ) -> None:
        super().__init__(node, enabled)
        self.class_mapping = class_mapping
        self.param_names = [[p.name for p in ModuleNode._get_params(c)] for c in class_mapping]
        rcv_snd = [_get_rcv_snd(c) for c in class_mapping]
        self.receive = [_to_list(i[0]) for i in rcv_snd]
        self.send = [_to_list(i[1]) for i in rcv_snd]
        self.info = info
        self.args = args

    def hook(self, **kwargs: Any) -> Any:
        container = self.node()
        layers = []
        passby = [self.args.pop(0)]
        prev_module_idx = self.info[0][-1]
        for (from_idx, number, module_idx), args in zip(self.info, self.args):
            if len(passby_args := passby[from_idx]) != len(self.receive[module_idx]):
                raise RuntimeError(
                    f"Passby args {passby_args} are not compatible with {self.receive[module_idx]}"
                )
            if len(self.receive[module_idx]) != len(self.send[prev_module_idx]):
                raise RuntimeError(
                    f"Expected the `{self.receive[module_idx]}` and "
                    "`{self.send[prev_module_idx]} to have same length.`"
                )
            kwargs = _construct_kwargs(
                passby_args,
                args,
                self.param_names[module_idx],
                self.receive[module_idx],
            )
            for _ in range(number):
                layers.append(self.class_mapping[module_idx](**kwargs))
            passby.append([kwargs[k] for k in self.send[module_idx]])
            prev_module_idx = module_idx
        try:
            return container(*layers)
        except Exception:
            return container(layers)

    @classmethod
    def __excore_prepare__(cls, node: ConfigNode, hook_info: str, config: ConfigDict) -> ConfigNode:
        if not (info := _get_info_dict(hook_info, config)):
            raise CoreConfigParseError()
        _check_info(info)
        info_node = ConfigHookNode(cls).add(**info)
        config._parse_module(info_node)
        return info_node.add(node=node)()  # type: ignore


def enable_finegrained_config(
    rcv_key: str = "receive", snd_key: str = "send", strict: bool = False
) -> None:
    register_argument_hook("*", FinegrainedConfig)
    FinegrainedConfig.rcv_key = rcv_key
    FinegrainedConfig.snd_key = snd_key
