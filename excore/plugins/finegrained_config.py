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
    """Gets and removes configuration information from the config dictionary.

    Args:
        index: Configuration index string, can be a simple key
            or a compound key path starting with $.
        config: Configuration dictionary object.

    Returns:
        dict | None: Found configuration info dictionary, or None if not found.

    Raises:
        CoreConfigParseError: When using $ syntax but corresponding config is not found.
    """
    if not index.startswith("$"):
        return config.pop(index, None)
    for idx in index[1:].split("::"):
        if not (config := config.pop(idx, None)):
            raise CoreConfigParseError(f"{index}")
    return config


def _check_info(info: dict) -> None:
    """Validates that the configuration info dictionary contains all required keys.

    Args:
        info: Configuration info dictionary to validate.

    Raises:
        CoreConfigParseError: When required keys are missing.
    """
    excepted_keys = ["$class_mapping", "info", "args"]
    for key in excepted_keys:
        if key not in info:
            raise CoreConfigParseError(f"Excepted keys {excepted_keys}, but cannot found {key}.")


def _get_rcv_snd(module: type) -> list[str | list[str]]:
    """Gets the receive and send parameter configurations for a module.

    Args:
        module: Module class to get configurations for.

    Returns:
        List containing receive and send parameters [receive, send].

    Raises:
        CoreConfigParseError: When required configuration fields are missing in registry.
    """
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
    """Converts a string or list of strings to a list of strings.

    Args:
        item: Input string or list of strings.

    Returns:
        Converted list of strings.
    """
    if isinstance(item, str):
        return [item]
    return item


def _construct_kwargs(
    passby_args: list[ArgType], args: list[ArgType], param_names: list[str], receive: list[str]
) -> dict[str, ArgType]:
    """Constructs keyword arguments needed for module initialization.

    Args:
        passby_args: List of arguments passed from previous layer.
        args: List of arguments for current layer.
        param_names: List of parameter names.
        receive: List of parameter names to receive.

    Returns:
        Dictionary of constructed keyword arguments.

    Raises:
        RuntimeError: When argument counts don't match.
    """
    kwargs = {n: a for n, a in zip(receive, passby_args)}
    param_names = [i for i in param_names if i not in receive]
    if len(args) > len(param_names):
        raise RuntimeError(f"Expected length of `{args}` to be less than f`{len(param_names)}.`")
    kwargs.update({n: a for n, a in zip(param_names, args)})
    return kwargs


class FinegrainedConfig(ConfigArgumentHook):
    """Fine-grained configuration hook for handling parameter passing and hierarchical configuration

    This class implements a configuration system that allows parameter passing between modules
    and supports hierarchical module construction.

    Attributes:
        rcv_key: Key name for receiving parameters.
        snd_key: Key name for sending parameters.
    """

    rcv_key: str = "receive"
    snd_key: str = "send"

    def __init__(
        self,
        node: ModuleNode,
        class_mapping: list[type],
        info: list[list[int]],
        args: list[list[ArgType]],
        unpack: bool = False,
        enabled: bool = True,
    ) -> None:
        """Initializes the fine-grained configuration hook.

        Args:
            node: Module node object.
            class_mapping: List of class mappings.
            info: List of module configuration information.
                Each element should contain number and module index in class_mapping.
            args: List of module arguments.
            unpack: Whether to unpack the layers list when calling container.
                If True, layers will be passed as *layers, otherwise as a single list.
            enabled: Whether to enable this hook.
        """
        super().__init__(node, enabled)
        self.class_mapping = class_mapping
        self.param_names = [[p.name for p in ModuleNode._get_params(c)] for c in class_mapping]
        rcv_snd = [_get_rcv_snd(c) for c in class_mapping]
        self.receive = [_to_list(i[0]) for i in rcv_snd]
        self.send = [_to_list(i[1]) for i in rcv_snd]
        self.info = info
        self.args = args
        self.unpacking = unpack

    def hook(self, **kwargs: Any) -> Any:
        """Executes the configuration hook logic.

        Builds module hierarchy according to configuration info and handles parameter passing
        between modules.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            Built module container.

        Raises:
            RuntimeError: When parameter passing is incompatible.
        """
        container = self.node()
        layers = []
        passby = [self.args.pop(0)]
        prev_module_idx = self.info[0][-1]
        for (number, module_idx), args in zip(self.info, self.args):
            if len(passby_args := passby[-1]) != len(self.receive[module_idx]):
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
        if self.unpacking:
            return container(*layers)
        return container(layers)

    @classmethod
    def __excore_prepare__(cls, node: ConfigNode, hook_info: str, config: ConfigDict) -> ConfigNode:
        """Prepares the configuration node.

        Args:
            node: Configuration node.
            hook_info: Hook information string.
            config: Configuration dictionary.

        Returns:
            Processed configuration node.

        Raises:
            CoreConfigParseError: When configuration parsing fails.
        """
        if not (info := _get_info_dict(hook_info, config)):
            raise CoreConfigParseError()
        _check_info(info)
        info_node = ConfigHookNode(cls).add(**info)
        config._parse_module(info_node)
        return info_node.add(node=node)()  # type: ignore


def enable_finegrained_config(
    rcv_key: str = "receive", snd_key: str = "send", strict: bool = False
) -> None:
    """Enables fine-grained configuration functionality.

    Args:
        rcv_key: Key name for receiving parameters.
        snd_key: Key name for sending parameters.
        strict: Whether to enable strict mode.

    Note:
        This function registers FinegrainedConfig as a global argument hook.
    """
    register_argument_hook("*", FinegrainedConfig)
    FinegrainedConfig.rcv_key = rcv_key
    FinegrainedConfig.snd_key = snd_key
