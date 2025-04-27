---
title: models
---

## TOC

- **Attributes:**
  - 🅰 [NodeClassType](#🅰-nodeclasstype)
  - 🅰 [NodeParams](#🅰-nodeparams) - flag for shared module, which will be built once and cached out.
  - 🅰 [NodeInstance](#🅰-nodeinstance) - flag for shared module, which will be built once and cached out.
  - 🅰 [NoCallSkipFlag](#🅰-nocallskipflag) - flag for shared module, which will be built once and cached out.
  - 🅰 [SpecialFlag](#🅰-specialflag) - flag for shared module, which will be built once and cached out.
  - 🅰 [REUSE\_FLAG](#🅰-reuse_flag) - flag for shared module, which will be built once and cached out.
  - 🅰 [INTER\_FLAG](#🅰-inter_flag) - flag for intermediate module, which will be built from scratch if need.
  - 🅰 [CLASS\_FLAG](#🅰-class_flag) - flag for use module class itself, instead of its instance.
  - 🅰 [REFER\_FLAG](#🅰-refer_flag) - flag for refer a value from top level of config.
  - 🅰 [OTHER\_FLAG](#🅰-other_flag) - default flag.
  - 🅰 [FLAG\_PATTERN](#🅰-flag_pattern) - flag for no call, which will be skipped.
  - 🅰 [DO\_NOT\_CALL\_KEY](#🅰-do_not_call_key) - flag for no call, which will be skipped.
  - 🅰 [IS\_PARSING](#🅰-is_parsing) - flag for parsing
  - 🅰 [SPECIAL\_FLAGS](#🅰-special_flags) - hook flags.
  - 🅰 [HOOK\_FLAGS](#🅰-hook_flags) - hook flags.
  - 🅰 [ConfigNode](#🅰-confignode) - ConfigNode type in parsing phase
  - 🅰 [NodeType](#🅰-nodetype) - Type of ModuleNode
  - 🅰 [\_dispatch\_module\_node](#🅰-_dispatch_module_node) - type:ignore
  - 🅰 [\_dispatch\_argument\_hook](#🅰-_dispatch_argument_hook) - type:ignore
- **Functions:**
  - 🅵 [silent](#🅵-silent) - Disables logging of build messages.
  - 🅵 [\_is\_special](#🅵-_is_special) - Determine if the given string begin with target special flag.
  - 🅵 [\_str\_to\_target](#🅵-_str_to_target) - Imports a module or retrieves a class/function from a module
  - 🅵 [register\_special\_flag](#🅵-register_special_flag) - Register a new special flag for module nodes.
  - 🅵 [register\_argument\_hook](#🅵-register_argument_hook) - Register a new argument hook.
- **Classes:**
  - 🅲 [ModuleNode](#🅲-modulenode) - A base class representing `LazyConfig` which is similar to `detectron2.config.lazy.LazyCall`.
  - 🅲 [InterNode](#🅲-internode) - Intermediate module node. More details see `config.overview`.
  - 🅲 [ConfigHookNode](#🅲-confighooknode) - Wrapper for `Hook` or `ConfigArgumentHook`.
  - 🅲 [ReusedNode](#🅲-reusednode) - A subclass of InterNode representing a reused module node.
  - 🅲 [ClassNode](#🅲-classnode) - `ClassNode` returns the wrapped class, function or module itself instead of calling them.
  - 🅲 [ConfigArgumentHook](#🅲-configargumenthook) - An abstract base class for configuration argument hooks.
  - 🅲 [GetAttr](#🅲-getattr) - A subclass of ConfigArgumentHook for getting attributes.
  - 🅲 [VariableReference](#🅲-variablereference) - A subclass of ClassNode for variable references.
  - 🅲 [ModuleWrapper](#🅲-modulewrapper)

## Attributes

## 🅰 NodeClassType

```python
NodeClassType = Type[Any]
```

## 🅰 NodeParams

```python
NodeParams = Dict[str, Any] #flag for shared module, which will be built once and cached out.
```

## 🅰 NodeInstance

```python
NodeInstance = object #flag for shared module, which will be built once and cached out.
```

## 🅰 NoCallSkipFlag

```python
NoCallSkipFlag = Self #flag for shared module, which will be built once and cached out.
```

## 🅰 SpecialFlag

```python
SpecialFlag = Literal["@", "!", "$", "&", ""] #flag for shared module, which will be built once and cached out.
```

## 🅰 REUSE\_FLAG

```python
REUSE_FLAG: Literal["@"] = "@" #flag for shared module, which will be built once and cached out.
```

## 🅰 INTER\_FLAG

```python
INTER_FLAG: Literal["!"] = "!" #flag for intermediate module, which will be built from scratch if need.
```

## 🅰 CLASS\_FLAG

```python
CLASS_FLAG: Literal["$"] = "$" #flag for use module class itself, instead of its instance.
```

## 🅰 REFER\_FLAG

```python
REFER_FLAG: Literal["&"] = "&" #flag for refer a value from top level of config.
```

## 🅰 OTHER\_FLAG

```python
OTHER_FLAG: Literal[""] = "" #default flag.
```

## 🅰 FLAG\_PATTERN

```python
FLAG_PATTERN = re.compile("^([@!$&])(.*)$") #flag for no call, which will be skipped.
```

## 🅰 DO\_NOT\_CALL\_KEY

```python
DO_NOT_CALL_KEY = """__no_call__""" #flag for no call, which will be skipped.
```

## 🅰 IS\_PARSING

```python
IS_PARSING = True #flag for parsing
```

## 🅰 SPECIAL\_FLAGS

```python
SPECIAL_FLAGS = [OTHER_FLAG, INTER_FLAG, REUSE_FLAG, CLASS_FLAG, REFER_FLAG] #hook flags.
```

## 🅰 HOOK\_FLAGS

```python
HOOK_FLAGS = ["@", "."] #hook flags.
```

## 🅰 ConfigNode

```python
ConfigNode = Union[ModuleNode, ConfigArgumentHook] #ConfigNode type in parsing phase
```

## 🅰 NodeType

```python
NodeType = Type[ModuleNode] #Type of ModuleNode
```

## 🅰 \_dispatch\_module\_node

```python
_dispatch_module_node: dict[SpecialFlag, NodeType] = {
    OTHER_FLAG: ModuleNode,
    REUSE_FLAG: ReusedNode,
    INTER_FLAG: InterNode,
    CLASS_FLAG: ClassNode,
    REFER_FLAG: VariableReference,
} #type:ignore
```

## 🅰 \_dispatch\_argument\_hook

```python
_dispatch_argument_hook: dict[str, Type[ConfigArgumentHook]] = {
    "@": ConfigArgumentHook,
    ".": GetAttr,
} #type:ignore
```


## Functions

## 🅵 silent

```python
def silent() -> None:
```

Disables logging of build messages.
## 🅵 \_is\_special

```python
def _is_special(k: str) -> tuple[str, SpecialFlag]:
```

Determine if the given string begin with target special flag.

\`@\` denotes reused module, which will only be built once and cached out.
    \`\!\` denotes intermediate module, which will be built from scratch if need.
    \`$\` denotes use module class itself, instead of its instance.
    \`&\` denotes use refer a value from top level of config.
    And other registered user defined special flag, see \`register\_special\_flag\`.
    All default flags see \`SPECIAL\_FLAGS\`

**Parameters:**

- **k** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): The input string to check.

**Returns:**

- **tuple[str, str]**: A tuple containing the modified string and the special flag.
## 🅵 \_str\_to\_target

```python
def _str_to_target(
    module_name: str,
) -> ModuleType | NodeClassType | FunctionType:
```

Imports a module or retrieves a class/function from a module

based on the provided module name.

**Parameters:**

- **module_name** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): The name of the module or the module path with the target class/function.

**Returns:**

- **[ModuleType](https://docs.python.org/3/library/types.html#types.ModuleType) | [NodeClassType](models#🅰-nodeclasstype) | [FunctionType](https://docs.python.org/3/library/types.html#types.FunctionType)**: The imported module, class or function.

**Raises:**

- **[StrToClassError](../-exceptions#🅲-strtoclasserror)**: If the module or target cannot be imported or found.
## 🅵 register\_special\_flag

```python
def register_special_flag(
    flag: str, node_type: NodeType, force: bool = False
) -> None:
```

Register a new special flag for module nodes.

**Parameters:**

- **flag** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): The special flag to register.
- **node_type** ([NodeType](models#🅰-nodetype)): The type of node associated with the flag.
- **force** ([bool](https://docs.python.org/3/library/stdtypes.html#boolean-values)): Whether to force registration if the flag already exists.
Defaults to False.

**Raises:**

- **[ValueError](https://docs.python.org/3/library/exceptions.html#ValueError)**: If the flag already exists and force is False.
## 🅵 register\_argument\_hook

```python
def register_argument_hook(
    flag: str, node_type: Type[ConfigArgumentHook], force: bool = False
) -> None:
```

Register a new argument hook.

**Parameters:**

- **flag** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): The flag associated with the hook.
- **node_type** (Type[ConfigArgumentHook]): The type of hook to register.
- **force** ([bool](https://docs.python.org/3/library/stdtypes.html#boolean-values)): Whether to force registration if the flag already exists.
Defaults to False.

**Raises:**

- **[ValueError](https://docs.python.org/3/library/exceptions.html#ValueError)**: If the flag already exists and force is False.

## Classes

## 🅲 ModuleNode

```python
@dataclass
class ModuleNode(dict):
    target: Any = None
    _no_call: bool = field(default=False, repr=False)
    priority: int = field(default=0, repr=False)
```

A base class representing \`LazyConfig\` which is similar to \`detectron2.config.lazy.LazyCall\`.

Wrap a class, function or python module and its parameters util
    you want to call it.

**Attributes:**

- **target** ([Any](https://docs.python.org/3/library/typing.html#typing.Any)): The class or module associated with the node.
- **_no_call** ([bool](https://docs.python.org/3/library/stdtypes.html#boolean-values)): Flag to indicate if the node should not be called
when you actually call it. Usually used with function
so in the config parsing phase the \`target\` will not be called.
Defaults to False.
- **priority** ([int](https://docs.python.org/3/library/stdtypes.html#numeric-types-int-float-complex)): Priority level of the node, used in parsing phase.

**Examples:**

```python
# Store class
node = ModuleNode(MyClass).add(a=1, b=2)
instance = node()

# Store function
node = ModuleNode(my_func).add(a=1, b=2)
result = node()

# Store module
node = ModuleNode(my_module).add(a=1, b=2)
result = node() # module itself
```


### 🅼 \_update\_params

```python
def _update_params(self, **params: NodeParams) -> None:
```

Updates the parameters of the node, if any parameter is instance of \`ModuleNode\`,

it will be called first.

**Parameters:**

- ****params** ([NodeParams](models#🅰-nodeparams)): The parameters to update.
### 🅼 name

```python
@property
def name(self) -> str:
```

Property to get the name of the associated class or module.

**Returns:**

- **[str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)**: The name of the class or module.
### 🅼 add

```python
def add(self, **params: NodeParams) -> Self:
```

Adds parameters to the node.

**Parameters:**

- ****params**: The parameters to add.

**Returns:**

- **[Self](https://docs.python.org/3/library/typing.html#typing.Self)**: The updated node.
### 🅼 \_instantiate

```python
def _instantiate(self) -> NodeInstance:
```

Instantiates the module, handling errors.

**Returns:**

- **[NodeInstance](models#🅰-nodeinstance)**: The instantiated module.

**Raises:**

- **[ModuleBuildError](../-exceptions#🅲-modulebuilderror)**: If instantiation fails.
### 🅼 \_\_call\_\_

```python
def __call__(self, **params: NodeParams) -> NoCallSkipFlag | NodeInstance:
```

Call the node.

**Parameters:**

- ****params**: The parameters for instantiation.

**Returns:**

- **[NoCallSkipFlag](models#🅰-nocallskipflag) | [NodeInstance](models#🅰-nodeinstance)**: The instantiated module or the node itself
if \_no\_call is True.
### 🅼 \_\_lshift\_\_

```python
def __lshift__(self, params: NodeParams) -> Self:
```

Updates the node with new parameters.

**Parameters:**

- **params** ([NodeParams](models#🅰-nodeparams)): The parameters to update.

**Returns:**

- **[Self](https://docs.python.org/3/library/typing.html#typing.Self)**: The updated node.

**Raises:**

- **[TypeError](https://docs.python.org/3/library/exceptions.html#TypeError)**: If the provided parameters are not a dictionary.

**Examples:**

```python
node << dict()
```
### 🅼 \_\_rshift\_\_

```python
def __rshift__(self, __other: ModuleNode) -> Self:
```

Merges another node into the current node.

**Parameters:**

- **__other** ([ModuleNode](models#🅲-modulenode)): The node to merge.

**Returns:**

- **[Self](https://docs.python.org/3/library/typing.html#typing.Self)**: The updated node.

**Raises:**

- **[TypeError](https://docs.python.org/3/library/exceptions.html#TypeError)**: If the provided other node is not a ModuleNode.

**Examples:**

```python
node >> other
```
### 🅼 \_\_excore\_check\_target\_type\_\_

```python
@classmethod
def __excore_check_target_type__(cls, target_type: type[ModuleNode]) -> bool:
```

Checks if the target type do not matches the expected type.

Used in config parsing phase.

**Parameters:**

- **target_type** (type[ModuleNode]): The target type to check.

**Returns:**

- **[bool](https://docs.python.org/3/library/stdtypes.html#boolean-values)**: False, as this is a base class method.
### 🅼 \_\_excore\_parse\_\_

```python
@classmethod
def __excore_parse__(
    cls, config: ConfigDict, **locals: dict[str, Any]
) -> ModuleNode | None:
```

User defined parsing logic. Disabled by default.

**Parameters:**

- **config** ([ConfigDict](parse#🅲-configdict)): The configuration to parse.
- ****locals** (dict[str, Any]): Additional local variables for parsing.

**Returns:**

- **[None](https://docs.python.org/3/library/constants.html#None) | [ModuleNode](models#🅲-modulenode)**: The parsed node or None.
### 🅼 from\_str

```python
@classmethod
def from_str(
    cls, str_target: str, params: NodeParams | None = None
) -> ModuleNode:
```

Creates a node from a string target.

**Parameters:**

- **str_target** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): The string target representing the module or class.
- **params** ([NodeParams](models#🅰-nodeparams)) (default to `None`): The parameters for the node. Defaults to None.

**Returns:**

- **[ModuleNode](models#🅲-modulenode)**: The created node.

**Examples:**

```python
node = ModuleNode.from_str("package.module.class", dict(param1=value1))
```

:::note
The `str_target` must be registered in the registry. More details see `Registry`.

:::
### 🅼 from\_base\_name

```python
@classmethod
def from_base_name(
    cls, base: str, name: str, params: NodeParams | None = None
) -> ModuleNode:
```

Creates a node from a base registry and name.

**Parameters:**

- **base** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): The base registry.
- **name** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): The name of the module or class.
- **params** ([NodeParams](models#🅰-nodeparams)) (default to `None`): The parameters for the node. Defaults to None.

**Returns:**

- **[ModuleNode](models#🅲-modulenode)**: The created node.

**Raises:**

- **[ModuleBuildError](../-exceptions#🅲-modulebuilderror)**: If the module cannot be found in the registry.

**Examples:**

```python
>>> node = ModuleNode.from_base_name("Module", "ClassName", dict(param1=value1))
```
### 🅼 from\_node

```python
@classmethod
def from_node(cls, _other: ModuleNode) -> ModuleNode:
```

Creates a new ModuleNode instance from another ModuleNode instance.

**Parameters:**

- **_other** ([ModuleNode](models#🅲-modulenode)): The other ModuleNode instance to create from.

**Returns:**

- **[ModuleNode](models#🅲-modulenode)**: A new ModuleNode instance or the original if they are of the same class.

**Examples:**

```python
node = ModuleNode.from_node(other_node)
```
### 🅼 \_inspect\_params

```python
@staticmethod
def _inspect_params(cls: type) -> list[inspect.Parameter]:
```

Retrieves the inspect parameter objects of a class or function.

**Parameters:**

- **cls** ([type](https://docs.python.org/3/library/functions.html#type)): The class or function to inspect.

**Returns:**

- **list[inspect.Parameter]**: A list of inspect.Parameter objects.
### 🅼 validate

```python
def validate(self) -> None:
```

Validate the parameters of the ModuleNode instance.

This method checks if all required parameters are provided.
If validation is globally disabled or the associated class is a module,
    the method returns immediately.

If any required parameters are missing and manual setting is not allowed,
    a ModuleValidateError is raised.

If missing parameters are found and manual setting is allowed,
    the user is prompted to provide values for them. The values will be parsed to
    \`int\`, \`str\`, \`list\`, \`tuple\` or \`dict\`. More details see \`DictAction.\_parse\_iterable\`.
## 🅲 InterNode

```python
class InterNode(ModuleNode):
    priority: int = 2
```

Intermediate module node. More details see \`config.overview\`.

**Attributes:**

- **priority** ([int](https://docs.python.org/3/library/stdtypes.html#numeric-types-int-float-complex)): Priority level set to 2.


### 🅼 \_\_excore\_check\_target\_type\_\_

```python
@classmethod
def __excore_check_target_type__(cls, target_type: type[ModuleNode]) -> bool:
```

Checks if the target type is ReusedNode.

**Parameters:**

- **target_type** (type[ModuleNode]): The target type to check.

**Returns:**

- **[bool](https://docs.python.org/3/library/stdtypes.html#boolean-values)**: True if the target type is ReusedNode, otherwise False.

:::danger
Same `ModuleName` referring to both `ReusedNode` and `InterNode` are not allowed.

:::
## 🅲 ConfigHookNode

```python
class ConfigHookNode(ModuleNode):
    priority: int = 1
```

Wrapper for \`Hook\` or \`ConfigArgumentHook\`.

**Attributes:**

- **priority** ([int](https://docs.python.org/3/library/stdtypes.html#numeric-types-int-float-complex)): Priority level set to 1.


### 🅼 validate

```python
def validate(self) -> None:
```

Validates the node, ensuring 'node' parameter is not present.

Because the \`node\` should be passed in config parsing phase
    instead of config definition.

**Raises:**

- **[ModuleValidateError](../-exceptions#🅲-modulevalidateerror)**: If 'node' parameter is found.
### 🅼 \_\_call\_\_

```python
@overload
def __call__(
    self, **params: NodeParams
) -> NodeInstance | Hook | ConfigArgumentHook:
```
### 🅼 \_\_call\_\_

```python
@overload
def __call__(self, **params: dict[str, ModuleNode]) -> ConfigHookNode:
```
### 🅼 \_\_call\_\_

```python
def __call__(
    self, **params: NodeParams
) -> NodeInstance | Hook | ConfigArgumentHook:
```

Calls the node to instantiate the module.

**Parameters:**

- ****params**: The parameters for instantiation.

**Returns:**

- **[NodeInstance](models#🅰-nodeinstance) | [Hook](../engine/hook#🅲-hook) | [ConfigArgumentHook](models#🅲-configargumenthook)**: The instantiated module or hook.
## 🅲 ReusedNode

```python
class ReusedNode(InterNode):
    priority: int = 3
```

A subclass of InterNode representing a reused module node.

**Attributes:**

- **priority** ([int](https://docs.python.org/3/library/stdtypes.html#numeric-types-int-float-complex)): Priority level set to 3.


### 🅼 \_\_call\_\_

```python
@CacheOut()
def __call__(self, **params: NodeParams) -> NodeInstance | NoCallSkipFlag:
```

Calls the node to instantiate the module, with caching, see \`CacheOut\`.

**Parameters:**

- ****params**: The additional parameters for instantiation.

**Returns:**

- **[NodeInstance](models#🅰-nodeinstance) | [NoCallSkipFlag](models#🅰-nocallskipflag)**: The instantiated module or the node itself
if \_no\_call is True.
### 🅼 \_\_excore\_check\_target\_type\_\_

```python
@classmethod
def __excore_check_target_type__(cls, target_type: NodeType) -> bool:
```

Checks if the target type is InterNode.

Same \`ModuleName\` referring to both \`ReusedNode\` and \`InterNode\` are not allowed.

**Parameters:**

- **target_type** ([NodeType](models#🅰-nodetype)): The target type to check.

**Returns:**

-
## 🅲 ClassNode

```python
class ClassNode(ModuleNode):
    priority: int = 1
```

\`ClassNode\` returns the wrapped class, function or module itself instead of calling them.

**Attributes:**

- **priority** ([int](https://docs.python.org/3/library/stdtypes.html#numeric-types-int-float-complex)): Priority level set to 1.


### 🅼 validate

```python
def validate(self) -> None:
```

Does nothing for class nodes for it should not have any parameters.
### 🅼 \_\_call\_\_

```python
def __call__(self) -> NodeClassType | FunctionType | ModuleType:
```

Returns the class, function or module itself.

**Returns:**

- **[NodeClassType](models#🅰-nodeclasstype) | [FunctionType](https://docs.python.org/3/library/types.html#types.FunctionType) | [ModuleType](https://docs.python.org/3/library/types.html#types.ModuleType)**: The class or function.
## 🅲 ConfigArgumentHook

```python
class ConfigArgumentHook(ABC):
    flag: str = "@"
```

An abstract base class for configuration argument hooks.

**Attributes:**

- **flag** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): The flag associated with the hook.
- **node** ([Callable](https://docs.python.org/3/library/typing.html#typing.Callable)): The node associated with the hook.
- **enabled** ([bool](https://docs.python.org/3/library/stdtypes.html#boolean-values)): Whether apply the hook.
- **name** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): The name of the wrapped node.
- **_is_initialized** ([bool](https://docs.python.org/3/library/stdtypes.html#boolean-values)): Flag to check if the hook is initialized.


### 🅼 \_\_init\_\_

```python
def __init__(self, node: Callable, enabled: bool = True) -> None:
```

Initializes the hook with a node and enabled status.

**Parameters:**

- **node** ([Callable](https://docs.python.org/3/library/typing.html#typing.Callable)): The node associated with the hook.
- **enabled** ([bool](https://docs.python.org/3/library/stdtypes.html#boolean-values)) (default to `True`): Whether apply the hook. Defaults to True.

**Raises:**

- **[ValueError](https://docs.python.org/3/library/exceptions.html#ValueError)**: If the node does not have a name attribute.
### 🅼 hook

```python
@abstractmethod
def hook(self, **kwargs: Any) -> Any:
```

Abstract method to implement the hook logic.

**Parameters:**

- ****kwargs**: The keyword arguments for the hook.

**Returns:**

- **[Any](https://docs.python.org/3/library/typing.html#typing.Any)**: The result of the hook.

**Raises:**

- **[NotImplementedError](https://docs.python.org/3/library/exceptions.html#NotImplementedError)**: If the method is not implemented by a subclass.
### 🅼 \_\_call\_\_

```python
@final
def __call__(self, **kwargs: Any) -> Any:
```

Calls the hook or the node based on the enabled status.

**Parameters:**

- ****kwargs**: The keyword arguments for the call.

**Returns:**

- **[Any](https://docs.python.org/3/library/typing.html#typing.Any)**: The result of the hook or the node call.

**Raises:**

- **[CoreConfigSupportError](../-exceptions#🅲-coreconfigsupporterror)**: If the hook is not properly initialized.
### 🅼 \_\_excore\_prepare\_\_

```python
@classmethod
def __excore_prepare__(
    cls, node: ConfigNode, hook_info: str, config: ConfigDict
) -> ConfigNode:
```

Prepares the hook with configuration.

**Parameters:**

- **node** ([ConfigNode](models#🅰-confignode)): The node to wrap.
- **hook_info** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): The hook information.
- **config** ([ConfigDict](parse#🅲-configdict)): The configuration dictionary.

**Returns:**

- **[ConfigNode](models#🅰-confignode)**: The prepared node.

**Raises:**

- **[CoreConfigParseError](../-exceptions#🅲-coreconfigparseerror)**: If more than one or no hooks are found.
## 🅲 GetAttr

```python
class GetAttr(ConfigArgumentHook):
    flag: str = "."
```

A subclass of ConfigArgumentHook for getting attributes.

**Attributes:**

- **flag** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): The flag associated with the hook, set to ".".
- **attr** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): The attribute to get.


### 🅼 \_\_init\_\_

```python
def __init__(self, node: ConfigNode, attr: str) -> None:
```

Initializes the hook with a node and attribute.

**Parameters:**

- **node** ([ConfigNode](models#🅰-confignode)): The node associated with the hook.
- **attr** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): The attribute to get.
### 🅼 hook

```python
def hook(self, **params: NodeParams) -> Any:
```

Implements the hook logic to get the attribute.

**Parameters:**

- ****params**: The parameters for the hook.

**Returns:**

- **[Any](https://docs.python.org/3/library/typing.html#typing.Any)**: The value of the attribute.

**Raises:**

- **[ModuleBuildError](../-exceptions#🅲-modulebuilderror)**: \`DO\_NOT\_CALL\_KEY\` is not supported.
### 🅼 from\_list

```python
@classmethod
def from_list(cls, node: ConfigNode, attrs: list[str]) -> ConfigNode:
```

Creates a chain of GetAttr hooks.

**Parameters:**

- **node** ([ConfigNode](models#🅰-confignode)): The initial node.
- **attrs** (list[str]): The list of attributes to get.

**Returns:**

- **[ConfigNode](models#🅰-confignode)**: The final node in the chain.
### 🅼 \_\_excore\_prepare\_\_

```python
@classmethod
def __excore_prepare__(
    cls, node: ConfigNode, hook_info: str, config: ConfigDict
) -> ConfigNode:
```

Prepares the hook with configuration.

**Parameters:**

- **node** ([ConfigNode](models#🅰-confignode)): The node to warp.
- **hook_info** ([str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)): The hook information.
- **config** ([ConfigDict](parse#🅲-configdict)): The configuration dictionary.

**Returns:**

- **[ConfigNode](models#🅰-confignode)**: The prepared node.
## 🅲 VariableReference

```python
class VariableReference(ClassNode):
    _name: str = None
```

A subclass of ClassNode for variable references.

Inherited from \`ClassNode\` is just for convenience.


### 🅼 \_\_excore\_parse\_\_

```python
@classmethod
def __excore_parse__(cls, config: ConfigDict, **locals) -> VariableReference:
```

Find the reference and build the node.

**Parameters:**

- **config** ([ConfigDict](parse#🅲-configdict)): The configuration to parse.
- ****locals**: Additional local variables for parsing.

**Returns:**

- **[VariableReference](models#🅲-variablereference)**: The parsed node.

**Raises:**

- **[CoreConfigParseError](../-exceptions#🅲-coreconfigparseerror)**: If the reference cannot be found.
### 🅼 name

```python
@property
def name(self) -> str:
```
## 🅲 ModuleWrapper

```python
class ModuleWrapper(dict):
```


### 🅼 \_\_init\_\_

```python
def __init__(
    self,
    modules: (
        dict[str, ConfigNode] | list[ConfigNode] | ConfigNode | None
    ) = None,
    is_dict: bool = False,
) -> None:
```
### 🅼 \_get\_name

```python
def _get_name(self, m) -> Any:
```
### 🅼 \_\_lshift\_\_

```python
def __lshift__(self, params: NodeParams) -> None:
```
### 🅼 first

```python
def first(self) -> NodeInstance | Self:
```
### 🅼 \_\_getattr\_\_

```python
def __getattr__(self, __name: str) -> Any:
```
### 🅼 \_\_call\_\_

```python
def __call__(self):
```
### 🅼 \_\_repr\_\_

```python
def __repr__(self) -> str:
```
