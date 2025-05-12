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
    """Retrieve configuration dictionary based on index.

    This function checks if the index starts with "$", indicating a hierarchical path.
    If so, it splits the index and traverses the configuration dictionary accordingly.
    If the index does not start with "$", it directly attempts to retrieve the value
    from the configuration dictionary.

    Args:
        index (str): The index key to retrieve the configuration.
        config (ConfigDict): The configuration dictionary to search within.

    Returns:
        dict | None: The retrieved configuration dictionary or None if not found.

    Raises:
        CoreConfigParseError: If the indexed configuration path does not exist.

    Example:
        >>> config = {"a": {"b": {"c": 42}}}  # Loaded toml config
        >>> _get_info_dict("$a::b::c", config)
        42
    """
    if not index.startswith("$"):
        return config.pop(index, None)
    for idx in index[1:].split("::"):
        if not (config := config.pop(idx, None)):
            raise CoreConfigParseError(f"{index}")
    return config


def _check_info(info: dict) -> None:
    """Validate configuration info dictionary.

    This function checks if the info dictionary contains all the expected keys:
    "$class_mapping", "info", and "args". If any of these keys are missing, it raises
    a CoreConfigParseError with an appropriate error message.

    Args:
        info (dict): The configuration info dictionary to validate.

    Raises:
        CoreConfigParseError: If any of the expected keys are missing from the info dictionary.
    """
    excepted_keys = ["$class_mapping", "info", "args"]
    for key in excepted_keys:
        if key not in info:
            raise CoreConfigParseError(f"Excepted keys {excepted_keys}, but cannot found {key}.")


def _get_rcv_snd(module: type) -> list[str | list[str]]:
    """Retrieve receive and send parameter configurations for a module.

    Args:
        module (type): The module class to get configurations for.

    Returns:
        list[str | list[str]]: A list containing receive and send parameters [receive, send].

    Raises:
        CoreConfigParseError: If required configuration fields are missing in the registry.
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
    if isinstance(item, str):
        return [item]
    return item


def _construct_kwargs(
    passby_args: list[ArgType], args: list[ArgType], param_names: list[str], receive: list[str]
) -> dict[str, ArgType]:
    """Construct keyword arguments for module initialization.

    Args:
        passby_args (list[ArgType]): List of arguments passed from the previous layer.
        args (list[ArgType]): List of arguments for the current layer.
        param_names (list[str]): List of parameter names.
        receive (list[str]): List of parameter names to receive.

    Returns:
        dict[str, ArgType]: Dictionary of constructed keyword arguments.

    Raises:
        RuntimeError: If the length of `args` exceeds the length of
            `param_names` that are not in `receive`.
    """
    kwargs = {n: a for n, a in zip(receive, passby_args)}
    param_names = [i for i in param_names if i not in receive]
    if len(args) > len(param_names):
        raise RuntimeError(f"Expected length of `{args}` to be less than f`{len(param_names)}.`")
    kwargs.update({n: a for n, a in zip(param_names, args)})
    return kwargs


class FinegrainedConfig(ConfigArgumentHook):
    """Fine-grained configuration hook for handling parameter passing and hierarchical config.

    This class implements a configuration system that allows parameter passing between modules
    and supports hierarchical module construction.

    More details can be found in the documentation of the `ConfigArgumentHook` class.

    Args:
        node (ModuleNode): Module node object.
        class_mapping (list[type]): List of class mappings.
        info (list[list[int]]): List of module configuration information.
            Each element should contain the number and module index in class_mapping.
        args (list[list[ArgType]]): List of module arguments.
        unpack (bool, optional): Whether to unpack the layers list when calling container.
            Defaults to False. If True, layers will be passed as *layers, otherwise as a list.
        enabled (bool, optional): Whether to enable this hook. Defaults to True.

    Attributes:
        rcv_key (str): Key name for receiving parameters.
        snd_key (str): Key name for sending parameters.

    Examples:
        >>> # Example can be found in `example/finegrained.py`.
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
        """Initialize the fine-grained configuration hook."""
        super().__init__(node, enabled)
        self.class_mapping = class_mapping
        self.param_names = [[p.name for p in ModuleNode._inspect_params(c)] for c in class_mapping]
        rcv_snd = [_get_rcv_snd(c) for c in class_mapping]
        self.receive = [_to_list(i[0]) for i in rcv_snd]
        self.send = [_to_list(i[1]) for i in rcv_snd]
        self.info = info
        self.args = args
        self.unpacking = unpack

    def hook(self, **kwargs: Any) -> Any:
        """Execute the configuration hook logic.

        This method builds the module hierarchy according to the configuration info
        and handles parameter passing between modules. It checks the compatibility
        of passby arguments with receive parameters and ensures that the lengths
        of receive and send parameters match between consecutive modules. It then
        constructs the keyword arguments for module initialization, creates the
        module instances, and returns the built module container.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            Any: Built module container.

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
        """Prepare the configuration node.

        Args:
            node (ConfigNode): Configuration node.
            hook_info (str): Hook information string.
            config (ConfigDict): Configuration dictionary.

        Returns:
            ConfigNode: Processed configuration node.

        Raises:
            CoreConfigParseError: When no hook_info is found.
        """
        if not (info := _get_info_dict(hook_info, config)):
            raise CoreConfigParseError()
        _check_info(info)
        info_node = ConfigHookNode(cls).add(**info)
        config._parse_module(info_node)
        return info_node.add(node=node)()  # type: ignore


def enable_finegrained_config(
    hook_flag: str = "*",
    rcv_key: str = "receive",
    snd_key: str = "send",
    force: bool = False,
) -> None:
    """Enable fine-grained configuration functionality.

    This function registers FinegrainedConfig as a global argument hook and sets the
    receive and send key names for the configuration. It also allows for specifying
    a hook flag and enabling force registration.

    Args:
        hook_flag (str, optional): The hook flag to use for registration. Defaults to '*'.
        rcv_key (str, optional): Key name for receiving parameters. Defaults to "receive".
        snd_key (str, optional): Key name for sending parameters. Defaults to "send".
        force (bool, optional): Whether to force the registration of the hook. Defaults to False.

    Note:
        This function registers `FinegrainedConfig` as a global argument hook.

    Example:
        >>> from excore.plugins.finegrained_config import enable_finegrained_config
        >>> enable_finegrained_config()
    """
    register_argument_hook(hook_flag, FinegrainedConfig, force)
    FinegrainedConfig.rcv_key = rcv_key
    FinegrainedConfig.snd_key = snd_key
