from __future__ import annotations

import importlib
import inspect
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from inspect import Parameter, isclass, ismodule
from typing import TYPE_CHECKING, Type, Union, final, overload

from .._constants import workspace
from .._exceptions import (
    CoreConfigParseError,
    CoreConfigSupportError,
    ModuleBuildError,
    ModuleValidateError,
    StrToClassError,
)
from .._misc import CacheOut
from ..engine.logging import logger
from ..engine.registry import Registry
from .action import DictAction

if TYPE_CHECKING:
    from types import FunctionType, ModuleType
    from typing import Any, Callable, Dict, Literal

    from typing_extensions import Self

    from ..engine.hook import Hook
    from .parse import ConfigDict

    NodeClassType = Type[Any]
    NodeParams = Dict[str, Any]
    NodeInstance = object

    NoCallSkipFlag = Self

    SpecialFlag = Literal["@", "!", "$", "&", ""]


__all__ = ["silent"]

REUSE_FLAG: Literal["@"] = "@"  # flag for shared module, which will be built once and cached out.
INTER_FLAG: Literal["!"] = (
    "!"  # flag for intermediate module, which will be built from scratch if need.
)
CLASS_FLAG: Literal["$"] = "$"  # flag for use module class itself, instead of its instance.
REFER_FLAG: Literal["&"] = "&"  # flag for refer a value from top level of config.
OTHER_FLAG: Literal[""] = ""  # default flag.

FLAG_PATTERN = re.compile(r"^([@!$&])(.*)$")
DO_NOT_CALL_KEY = "__no_call__"  # flag for no call, which will be skipped.
IS_PARSING = True  # flag for parsing
SPECIAL_FLAGS = [OTHER_FLAG, INTER_FLAG, REUSE_FLAG, CLASS_FLAG, REFER_FLAG]
HOOK_FLAGS = ["@", "."]  # hook flags.


def silent() -> None:
    """
    Disables logging of build messages.
    """
    workspace.excore_log_build_message = False


def _is_special(k: str) -> tuple[str, SpecialFlag]:
    """Determine if the given string begin with target special flag.
        `@` denotes reused module, which will only be built once and cached out.
        `!` denotes intermediate module, which will be built from scratch if need.
        `$` denotes use module class itself, instead of its instance.
        `&` denotes use refer a value from top level of config.
        And other registered user defined special flag, see `register_special_flag`.
        All default flags see `SPECIAL_FLAGS`

    Args:
        k (str): The input string to check.

    Returns:
        tuple[str, str]: A tuple containing the modified string and the special flag.
    """
    match = FLAG_PATTERN.match(k)
    if match:
        logger.ex(f"Find match `{match}`.")
        return match.group(2), match.group(1)  # type: ignore
    logger.ex("No Match.")
    return k, ""


def _str_to_target(module_name: str) -> ModuleType | NodeClassType | FunctionType:
    """Imports a module or retrieves a class/function from a module
        based on the provided module name.

    Args:
        module_name (str): The name of the module or the module path with the target class/function.

    Returns:
        ModuleType | NodeClassType | FunctionType: The imported module, class or function.

    Raises:
        StrToClassError: If the module or target cannot be imported or found.
    """
    module_names = module_name.split(".")
    if len(module_names) == 1:
        return importlib.import_module(module_names[0])
    target_name = module_names.pop(-1)
    try:
        module = importlib.import_module(".".join(module_names))
    except ModuleNotFoundError as exc:
        raise StrToClassError(f"Cannot import such module: `{'.'.join(module_names)}`") from exc
    try:
        module = getattr(module, target_name)
    except AttributeError as exc:
        raise StrToClassError(
            f"Cannot find such module `{target_name}` form `{'.'.join(module_names)}`"
        ) from exc
    return module


@dataclass
class ModuleNode(dict):
    """A base class representing `LazyConfig` which is similar to `detectron2.config.lazy.LazyCall`.
        Wrap a class, function or python module and its parameters util
        you want to call it.

    Attributes:
        target (Any): The class or module associated with the node.
        _no_call (bool): Flag to indicate if the node should not be called
            when you actually call it. Usually used with function
            so in the config parsing phase the `target` will not be called.
            Defaults to False.
        priority (int): Priority level of the node, used in parsing phase.

    Methods:
        _update_params: Updates the parameters of the node.
        name: Property to get the name of the associated class.
        add: Adds parameters to the node.
        _instantiate: Handle instantiating.
        __call__: Calls the node to instantiate the module.
        __lshift__: Updates the node with new parameters.
        __rshift__: Merges another node into the current node.
        from_str: Creates a node from a string target.
        from_base_name: Creates a node from a base registry and name.
        from_node: Creates a node from another node.
        validate: Validates the node's parameters.

    Examples:
        # Store class
        node = ModuleNode(MyClass).add(a=1, b=2)
        instance = node()

        # Store function
        node = ModuleNode(my_func).add(a=1, b=2)
        result = node()

        # Store module
        node = ModuleNode(my_module).add(a=1, b=2)
        result = node() # module itself
    """

    target: Any
    _no_call: bool = field(default=False, repr=False)
    priority: int = field(default=0, repr=False)

    def _update_params(self, **params: NodeParams) -> None:
        """Updates the parameters of the node, if any parameter is instance of `ModuleNode`,
            it will be called first.

        Args:
            **params (NodeParams): The parameters to update.
        """
        return_params = {}
        for k, v in self.items():
            if isinstance(v, (ModuleWrapper, ModuleNode)):
                v = v()
            return_params[k] = v
        self.update(params)
        self.update(return_params)

    @property
    def name(self) -> str:
        """
        Property to get the name of the associated class or module.

        Returns:
            str: The name of the class or module.
        """
        return self.target.__name__

    def add(self, **params: NodeParams) -> Self:
        """Adds parameters to the node.

        Args:
            **params: The parameters to add.

        Returns:
            Self: The updated node.
        """
        self.update(params)
        return self

    def _instantiate(self) -> NodeInstance:
        """Instantiates the module, handling errors.

        Returns:
            NodeInstance: The instantiated module.

        Raises:
            ModuleBuildError: If instantiation fails.
        """
        try:
            if ismodule(self.target):
                return self.target
            module = self.target(**self)
        except Exception as exc:
            raise ModuleBuildError(
                f"Instantiate Error with module {self.target} and arguments {self.items()}"
            ) from exc
        if workspace.excore_log_build_message:
            logger.success(
                f"Successfully instantiated: {self.target.__name__} with arguments {self.items()}"
            )
        return module

    def __call__(self, **params: NodeParams) -> NoCallSkipFlag | NodeInstance:  # type: ignore
        """Call the node.

        Args:
            **params: The parameters for instantiation.

        Returns:
            NoCallSkipFlag | NodeInstance: The instantiated module or the node itself
                if _no_call is True.
        """
        print(IS_PARSING)
        if IS_PARSING and self._no_call:
            return self
        self._update_params(**params)
        self.validate()
        module = self._instantiate()
        return module

    def __lshift__(self, params: NodeParams) -> Self:
        """Updates the node with new parameters.

        Args:
            params (NodeParams): The parameters to update.

        Returns:
            Self: The updated node.

        Raises:
            TypeError: If the provided parameters are not a dictionary.

        Examples:
            node << dict()
        """
        if not isinstance(params, dict):
            raise TypeError(f"Expect type is dict, but got {type(params)}")
        self.update(params)
        return self

    def __rshift__(self, __other: ModuleNode) -> Self:
        """Merges another node into the current node.

        Args:
            __other (ModuleNode): The node to merge.

        Returns:
            Self: The updated node.

        Raises:
            TypeError: If the provided other node is not a ModuleNode.

        Examples:
            node >> other
        """
        if not isinstance(__other, ModuleNode):
            raise TypeError(f"Expect type is `ModuleNode`, but got {type(__other)}")
        __other.update(self)
        return self

    @classmethod
    def __excore_check_target_type__(cls, target_type: type[ModuleNode]) -> bool:
        """Checks if the target type do not matches the expected type.
            Used in config parsing phase.

        Args:
            target_type (type[ModuleNode]): The target type to check.

        Returns:
            bool: False, as this is a base class method.
        """
        return False

    @classmethod
    def __excore_parse__(cls, config: ConfigDict, **locals: dict[str, Any]) -> ModuleNode | None:
        """User defined parsing logic. Disabled by default.

        Args:
            config (ConfigDict): The configuration to parse.
            **locals (dict[str, Any]): Additional local variables for parsing.

        Returns:
            None | ModuleNode: The parsed node or None.
        """
        return None

    @classmethod
    def from_str(cls, str_target: str, params: NodeParams | None = None) -> ModuleNode:
        """Creates a node from a string target.

        Args:
            str_target (str): The string target representing the module or class.
            params (NodeParams, optional): The parameters for the node. Defaults to None.

        Returns:
            ModuleNode: The created node.

        Examples:
            node = ModuleNode.from_str("package.module.class", dict(param1=value1))

        Note:
            The `str_target` must be registered in the registry. More details see `Registry`.
        """
        node = cls(_str_to_target(str_target))
        if params:
            node.update(params)
        if node.pop(DO_NOT_CALL_KEY, False):
            node._no_call = True
        return node

    @classmethod
    def from_base_name(cls, base: str, name: str, params: NodeParams | None = None) -> ModuleNode:
        """Creates a node from a base registry and name.

        Args:
            base (str): The base registry.
            name (str): The name of the module or class.
            params (NodeParams, optional): The parameters for the node. Defaults to None.

        Returns:
            ModuleNode: The created node.

        Raises:
            ModuleBuildError: If the module cannot be found in the registry.

        Examples:
             >>> node = ModuleNode.from_base_name("Module", "ClassName", dict(param1=value1))
        """
        try:
            cls_name = Registry.get_registry(base)[name]
        except KeyError as exc:
            raise ModuleBuildError(
                f"Failed to find the registered module `{name}` with base registry `{base}`"
            ) from exc
        return cls.from_str(cls_name, params)

    @classmethod
    def from_node(cls, _other: ModuleNode) -> ModuleNode:
        """Creates a new ModuleNode instance from another ModuleNode instance.

        Args:
            _other (ModuleNode): The other ModuleNode instance to create from.

        Returns:
            ModuleNode: A new ModuleNode instance or the original if they are of the same class.

        Examples:
            node = ModuleNode.from_node(other_node)
        """
        if _other.__class__.__name__ == cls.__name__:
            return _other
        node = cls(_other.target) << _other
        node._no_call = _other._no_call
        return node

    @staticmethod
    def _inspect_params(cls: type) -> list[inspect.Parameter]:
        """Retrieves the inspect parameter objects of a class or function.

        Args:
            cls (type): The class or function to inspect.

        Returns:
            list[inspect.Parameter]: A list of inspect.Parameter objects.
        """
        signature = inspect.signature(cls.__init__ if isclass(cls) else cls)
        params = list(signature.parameters.values())
        if isclass(cls):  # skip self
            params = params[1:]
        return params

    def validate(self) -> None:
        """Validate the parameters of the ModuleNode instance.

        This method checks if all required parameters are provided.
        If validation is globally disabled or the associated class is a module,
            the method returns immediately.

        If any required parameters are missing and manual setting is not allowed,
            a ModuleValidateError is raised.

        If missing parameters are found and manual setting is allowed,
            the user is prompted to provide values for them. The values will be parsed to
            `int`, `str`, `list`, `tuple` or `dict`. More details see `DictAction._parse_iterable`.
        """
        if not workspace.excore_validate:
            return
        if ismodule(self.target):
            return

        missing = []
        defaults = []
        params = ModuleNode._inspect_params(self.target)

        for param in params:
            if (
                param.default == param.empty
                and param.kind
                not in [
                    Parameter.VAR_POSITIONAL,
                    Parameter.VAR_KEYWORD,
                ]
                and param.name not in self
            ):
                missing.append(param.name)
            else:
                defaults.append(param.name)

        message = (
            f"Validating `{self.target.__name__}` , "
            f"finding missing parameters: `{missing}` without default values."
        )
        if not workspace.excore_manual_set and missing:
            raise ModuleValidateError(message)
        if missing:
            logger.info(message)
        for param_name in missing:
            logger.info(f"Input value of parameter `{param_name}`:")
            value = input()
            self[param_name] = DictAction._parse_iterable(value)


class InterNode(ModuleNode):
    """Intermediate module node. More details see `config.overview`.

    Attributes:
        priority (int): Priority level set to 2.

    Methods:
        __excore_check_target_type__: Checks if the target type is ReusedNode.
    """

    priority: int = 2

    @classmethod
    def __excore_check_target_type__(cls, target_type: type[ModuleNode]) -> bool:
        """
        Checks if the target type is ReusedNode.

        Danger:
            Same `ModuleName` referring to both `ReusedNode` and `InterNode` are not allowed.

        Args:
            target_type (type[ModuleNode]): The target type to check.

        Returns:
            bool: True if the target type is ReusedNode, otherwise False.
        """
        return target_type is ReusedNode


class ConfigHookNode(ModuleNode):
    """Wrapper for `Hook` or `ConfigArgumentHook`.

    Attributes:
        priority (int): Priority level set to 1.

    Methods:
        validate: Validates the node, ensuring 'node' parameter is not present.
    """

    priority: int = 1

    def validate(self) -> None:
        """Validates the node, ensuring 'node' parameter is not present.
            Because the `node` should be passed in config parsing phase
            instead of config definition.

        Raises:
            ModuleValidateError: If 'node' parameter is found.
        """
        if "node" in self:
            raise ModuleValidateError(
                f"Parameter `node:{self['node']}` should not exist in `ConfigHookNode`."
            )
        super().validate()

    @overload
    def __call__(self, **params: NodeParams) -> NodeInstance | Hook | ConfigArgumentHook: ...

    @overload
    def __call__(self, **params: dict[str, ModuleNode]) -> ConfigHookNode: ...

    def __call__(self, **params: NodeParams) -> NodeInstance | Hook | ConfigArgumentHook:
        """Calls the node to instantiate the module.

        Args:
            **params: The parameters for instantiation.

        Returns:
            NodeInstance | Hook | ConfigArgumentHook: The instantiated module or hook.
        """
        self._update_params(**params)
        return self._instantiate()


class ReusedNode(InterNode):
    """A subclass of InterNode representing a reused module node.

    Attributes:
        priority (int): Priority level set to 3.

    Methods:
        __call__: Calls the node to instantiate the module, with caching.
        __excore_check_target_type__: Checks if the target type is InterNode.
    """

    priority: int = 3

    @CacheOut()
    def __call__(self, **params: NodeParams) -> NodeInstance | NoCallSkipFlag:  # type: ignore
        """Calls the node to instantiate the module, with caching, see `CacheOut`.

        Args:
            **params: The additional parameters for instantiation.

        Returns:
            NodeInstance | NoCallSkipFlag: The instantiated module or the node itself
                if _no_call is True.
        """
        return super().__call__(**params)

    @classmethod
    def __excore_check_target_type__(cls, target_type: NodeType) -> bool:
        """Checks if the target type is InterNode.
            Same `ModuleName` referring to both `ReusedNode` and `InterNode` are not allowed.

        Args:
            target_type (NodeType): The target type to check.

        Returns:
        """
        return target_type is InterNode


class ClassNode(ModuleNode):
    """`ClassNode` returns the wrapped class, function or module itself instead of calling them.

    Attributes:
        priority (int): Priority level set to 1.
    """

    priority: int = 1

    def validate(self) -> None:
        """
        Does nothing for class nodes for it should not have any parameters.
        """
        return  # Do nothing

    def __call__(self) -> NodeClassType | FunctionType | ModuleType:  # type: ignore
        """Returns the class, function or module itself.

        Returns:
            NodeClassType | FunctionType | ModuleType: The class or function.
        """
        return self.target


class ConfigArgumentHook(ABC):
    """An abstract base class for configuration argument hooks.

    Attributes:
        flag (str): The flag associated with the hook.
        node (Callable): The node associated with the hook.
        enabled (bool): Whether apply the hook.
        name (str): The name of the wrapped node.
        _is_initialized (bool): Flag to check if the hook is initialized.

    Methods:
        __init__: Initializes the hook with a node and enabled status.
        hook: Abstract method to implement the hook logic.
        __call__: Calls the hook or the node based on the enabled status.
        __excore_prepare__: Prepares the hook with configuration.
    """

    flag: str = "@"

    def __init__(
        self,
        node: Callable,
        enabled: bool = True,
    ) -> None:
        """Initializes the hook with a node and enabled status.

        Args:
            node (Callable): The node associated with the hook.
            enabled (bool, optional): Whether apply the hook. Defaults to True.

        Raises:
            ValueError: If the node does not have a name attribute.
        """
        self.node = node
        self.enabled = enabled
        if not hasattr(node, "name"):
            raise ValueError("The `node` must have name attribute.")
        self.name = node.name
        self._is_initialized = True

    @abstractmethod
    def hook(self, **kwargs: Any) -> Any:
        """Abstract method to implement the hook logic.

        Args:
            **kwargs: The keyword arguments for the hook.

        Returns:
            Any: The result of the hook.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        raise NotImplementedError(f"`{self.__class__.__name__}` do not implement `hook` method.")

    @final
    def __call__(self, **kwargs: Any) -> Any:
        """Calls the hook or the node based on the enabled status.

        Args:
            **kwargs: The keyword arguments for the call.

        Returns:
            Any: The result of the hook or the node call.

        Raises:
            CoreConfigSupportError: If the hook is not properly initialized.
        """
        if not getattr(self, "_is_initialized", False):
            raise CoreConfigSupportError(
                f"Call super().__init__(node) in class `{self.__class__.__name__}`"
            )
        if self.enabled:
            return self.hook(**kwargs)
        return self.node(**kwargs)

    @classmethod
    def __excore_prepare__(cls, node: ConfigNode, hook_info: str, config: ConfigDict) -> ConfigNode:
        """Prepares the hook with configuration.

        Args:
            node (ConfigNode): The node to wrap.
            hook_info (str): The hook information.
            config (ConfigDict): The configuration dictionary.

        Returns:
            ConfigNode: The prepared node.

        Raises:
            CoreConfigParseError: If more than one or no hooks are found.
        """
        hook_name, field = config._get_name_and_field(hook_info)
        if not isinstance(hook_name, str):
            raise CoreConfigParseError(
                f"More than one or none of hooks are found with `{hook_info}`."
            )
        hook_node = config._get_node_from_name_and_field(hook_name, field, ConfigHookNode)[0]
        node = hook_node(node=node)  # type:ignore
        return node


class GetAttr(ConfigArgumentHook):
    """A subclass of ConfigArgumentHook for getting attributes.

    Attributes:
        flag (str): The flag associated with the hook, set to ".".
        attr (str): The attribute to get.

    Methods:
        __init__: Initializes the hook with a node and attribute.
        hook: Implements the hook logic to get the attribute.
        from_list: Creates a chain of GetAttr hooks.
        __excore_prepare__: Prepares the hook with configuration.
    """

    flag: str = "."

    def __init__(self, node: ConfigNode, attr: str) -> None:
        """Initializes the hook with a node and attribute.

        Args:
            node (ConfigNode): The node associated with the hook.
            attr (str): The attribute to get.
        """
        super().__init__(node)
        self.attr = attr

    def hook(self, **params: NodeParams) -> Any:
        """Implements the hook logic to get the attribute.

        Args:
            **params: The parameters for the hook.

        Returns:
            Any: The value of the attribute.

        Raises:
            ModuleBuildError: `DO_NOT_CALL_KEY` is not supported.
        """
        target = self.node(**params)
        if isinstance(target, ModuleNode):
            raise ModuleBuildError(f"Do not support `{DO_NOT_CALL_KEY}`")
        return eval("target." + self.attr)

    @classmethod
    def from_list(cls, node: ConfigNode, attrs: list[str]) -> ConfigNode:
        """Creates a chain of GetAttr hooks.

        Args:
            node (ConfigNode): The initial node.
            attrs (list[str]): The list of attributes to get.

        Returns:
            ConfigNode: The final node in the chain.
        """
        for attr in attrs:
            node = cls(node, attr)
        return node

    @classmethod
    def __excore_prepare__(cls, node: ConfigNode, hook_info: str, config: ConfigDict) -> ConfigNode:
        """Prepares the hook with configuration.

        Args:
            node (ConfigNode): The node to warp.
            hook_info (str): The hook information.
            config (ConfigDict): The configuration dictionary.

        Returns:
            ConfigNode: The prepared node.
        """
        return cls(node, hook_info)


class VariableReference(ClassNode):
    """A subclass of ClassNode for variable references.
    Inherited from `ClassNode` is just for convenience.
    """

    _name: str

    @classmethod
    def __excore_parse__(cls, config: ConfigDict, **locals) -> VariableReference:
        """Find the reference and build the node.

        Args:
            config (ConfigDict): The configuration to parse.
            **locals: Additional local variables for parsing.

        Returns:
            VariableReference: The parsed node.

        Raises:
            CoreConfigParseError: If the reference cannot be found.
        """
        name = locals["name"]
        logger.ex(f"Got `name` {name}.")
        parsed_value = config._parse_env_var(name)
        if parsed_value != name:
            node = cls(parsed_value)
        elif name not in config:
            raise CoreConfigParseError(f"Can not find reference: {name}.")
        else:
            node = cls(config[name])
        node._name = name
        return node

    @property
    def name(self) -> str:
        return self._name


ConfigNode = Union[ModuleNode, ConfigArgumentHook]  # ConfigNode type in parsing phase
NodeType = Type[ModuleNode]  # Type of ModuleNode


class ModuleWrapper(dict):
    def __init__(
        self,
        modules: dict[str, ConfigNode] | list[ConfigNode] | ConfigNode | None = None,
        is_dict: bool = False,
    ) -> None:
        super().__init__()
        if modules is None:
            return
        self.is_dict = is_dict
        if isinstance(modules, (ModuleNode, ConfigArgumentHook)):
            self[modules.name] = modules
        elif isinstance(modules, dict):
            for k, m in modules.items():
                if isinstance(m, list):
                    m = ModuleWrapper(m)
                self[k] = m
        elif isinstance(modules, list):
            for m in modules:
                self[self._get_name(m)] = m
            if len(self) != len(modules):
                raise ValueError("Currently not support for the same class name")
        else:
            raise TypeError(
                f"Expect modules to be `list`, `dict` or `ModuleNode`, but got {type(modules)}"
            )

    def _get_name(self, m) -> Any:
        if hasattr(m, "name"):
            return m.name
        return m.__class__.__name__

    def __lshift__(self, params: NodeParams) -> None:
        if len(self) == 1:
            self[next(iter(self.keys()))] << params
        else:
            raise RuntimeError("Wrapped more than 1 ModuleNode, index first")

    def first(self) -> NodeInstance | Self:
        if len(self) == 1:
            return next(iter(self.values()))
        return self

    def __getattr__(self, __name: str) -> Any:
        if __name in self.keys():
            return self[__name]
        raise KeyError(f"Invalid key `{__name}`, must be one of `{list(self.keys())}`")

    def __call__(self):
        if self.is_dict:
            return {k: v() for k, v in self.items()}
        res = [m() for m in self.values()]
        return res[0] if len(res) == 1 else res

    def __repr__(self) -> str:
        return f"ModuleWrapper{list(self.values())}"


_dispatch_module_node: dict[SpecialFlag, NodeType] = {
    OTHER_FLAG: ModuleNode,
    REUSE_FLAG: ReusedNode,
    INTER_FLAG: InterNode,
    CLASS_FLAG: ClassNode,
    REFER_FLAG: VariableReference,
}

_dispatch_argument_hook: dict[str, Type[ConfigArgumentHook]] = {
    "@": ConfigArgumentHook,  # type:ignore
    ".": GetAttr,
}


def register_special_flag(flag: str, node_type: NodeType, force: bool = False) -> None:
    """Register a new special flag for module nodes.

    Args:
        flag (str): The special flag to register.
        node_type (NodeType): The type of node associated with the flag.
        force (bool, optional): Whether to force registration if the flag already exists.
            Defaults to False.

    Raises:
        ValueError: If the flag already exists and force is False.
    """
    if not force and flag in SPECIAL_FLAGS:
        raise ValueError(f"Special flag `{flag}` already exist.")
    SPECIAL_FLAGS.append(flag)
    global FLAG_PATTERN
    FLAG_PATTERN = re.compile(rf"^([{''.join(SPECIAL_FLAGS)}])(.*)$")
    _dispatch_module_node[flag] = node_type  # type: ignore
    logger.ex(f"Register new module node `{node_type}` with special flag `{flag}.`")


def register_argument_hook(
    flag: str, node_type: Type[ConfigArgumentHook], force: bool = False
) -> None:
    """Register a new argument hook.

    Args:
        flag (str): The flag associated with the hook.
        node_type (Type[ConfigArgumentHook]): The type of hook to register.
        force (bool, optional): Whether to force registration if the flag already exists.
            Defaults to False.

    Raises:
        ValueError: If the flag already exists and force is False.
    """
    if not force and flag in HOOK_FLAGS:
        raise ValueError(f"Special flag `{flag}` already exist.")
    HOOK_FLAGS.append(flag)
    _dispatch_argument_hook[flag] = node_type
    logger.ex(f"Register new hook node `{node_type}` with special flag `{flag}.`")
