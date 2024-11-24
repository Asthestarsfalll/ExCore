from __future__ import annotations

from typing import TYPE_CHECKING

from .._exceptions import CoreConfigParseError, ImplicitModuleParseError
from .._misc import _create_table
from ..engine import Registry, logger
from .model import (
    OTHER_FLAG,
    REFER_FLAG,
    ChainedInvocationWrapper,
    ClassNode,
    ModuleNode,
    ModuleWrapper,
    ReusedNode,
    VariableReference,
    _dispatch_module_node,
    _is_special,
)

if TYPE_CHECKING:
    from typing import Generator, Sequence

    from typing_extensions import Self

    from .model import ConfigNode, NodeType, SpecialFlag


def _check_implicit_module(module: ModuleNode) -> None:
    import inspect
    from inspect import Parameter

    cls = module.cls
    signature = inspect.signature(cls.__init__)
    empty = []
    for idx, param in enumerate(signature.parameters.values()):
        if (
            idx != 0
            and param.default == param.empty
            and param.kind not in [Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD]
        ):
            empty.append(param.name)
    if empty:
        raise ImplicitModuleParseError(
            f"Parse class `{cls.__name__}` to `Implicit`, "
            f"but find parameters: {empty} without default value."
        )


def _dict2node(module_type: SpecialFlag, base: str, _dict: dict):
    ModuleType = _dispatch_module_node[module_type]
    return {name: ModuleType.from_base_name(base, name, v) for name, v in _dict.items()}


def _parse_param_name(name) -> tuple[str, list[str], list[str]]:
    names = name.split("@")
    attrs = names.pop(0).split(".")
    attrs = [i for i in attrs if i]
    hooks = [i for i in names if i]
    return attrs.pop(0), attrs, hooks


def _flatten_list(
    lis: Sequence[ConfigNode | VariableReference | list[ConfigNode]],
) -> Sequence[ConfigNode | VariableReference]:
    new_lis = []
    for i in lis:
        if isinstance(i, list):
            new_lis.extend(i)
        else:
            new_lis.append(i)  # type: ignore
    return new_lis


class ConfigDict(dict):
    primary_fields: list
    primary_to_registry: dict[str, str]
    registered_fields: list
    all_fields: set[str]
    scratchpads_fields: set[str] = set()
    current_field: str | None = None

    def __new__(cls) -> Self:
        if not hasattr(cls, "primary_fields"):
            raise RuntimeError("Call `set_primary_fields` before `load`")

        # make primary fields unique when multiple load.
        class ConfigDictImpl(ConfigDict):
            # otherwise it will share the same class variable with father class.
            primary_fields = ConfigDict.primary_fields
            primary_to_registry = ConfigDict.primary_to_registry
            scratchpads_fields = ConfigDict.scratchpads_fields

        inst = super().__new__(ConfigDictImpl)  # type: ignore
        return inst  # type: ignore

    @classmethod
    def set_primary_fields(
        cls, primary_fields: Sequence[str], primary_to_registry: dict[str, str]
    ) -> None:
        """
        Sets the `primary_fields` attribute to the specified list of module names,
            and `registered_fields` attributes based on the current state
            of the `Registry` object.

        Note that `set_primary_fields` must be called before `config.load`.
        """
        cls.primary_fields = list(primary_fields)
        cls.primary_to_registry = primary_to_registry

    def parse(self) -> None:
        """
        Parsing config into some `ModuleNode`s, the procedures are as following:

            1. Convert config nodes in `primary_fields` to `ModuleNode` at first,
                the field will be regarded as a set of nodes, e.g. `self[Model]`
                consists of two models.

                i. If the field is registed, the base registry is set to field;
                ii. If not, search `Registry` to get the base registry of each node.

            2. Convert isolated objects to `ModuleNode`;

                i. If the field is registed, search `Registry` to get the base registry of each node
                    Raising error if it cannot find;
                ii. If not, regard the field as a single node, and search `Registry`.
                iii. If search fail, regard the field as a scratchpads.

            3. Parse all the `ModuleNode` to target type of Node, e.g. `ReusedNode` and `ClassNode`.

                Visit the top level of config dict:
                i. If the name is in `primary_fields` or `scratchpads_fields`, parse each node of
                    field;
                ii. Else if the node is instance of `ModuleNode`, parse it to target node.

            4. Wrap all the nodes of `primary_fields` into ModuleWrapper.

            5. Clean some remain non-primary nodes. Only keep the primary nodes.

        In the 3rd step, it will parse every parameter of each module node

            if its name has a special prefix, e.g. `!`, `@` or `$`.
            The special parameter should be a string, a list of string or a dict of string.
            They will be parsed to target module nodes in given format(alone, list or dict).

        According to given string parameters, e.g. `['ResNet', 'SegHead']`,

            1. It will firstly search from the top level of config.
            2. If it dose not exist, it will search from `primary_fields`,
                `scratchpads_fields` and `registered_fields`.
            3. If it still dose not exist, it will be regraded as a implicit module,
                which must have non-required parameters.

        For the first two situations, the node will be convert to target type of node,
            then it will be set back to config for cache. For the last situation,
            it will only be set back when target module type is `ReusedNode`. But if the
            target module type is `ClassNode`, it will not be set back.

        NOTE: Set converted nodes back to config is necceary for `ReusedNode`.

        NOTE: use `export EXCORE_DEBUG=1` to enable excore debug to
            get more information when parsing.
        """
        logger.ex("Parse primary modules.")
        self._parse_primary_modules()
        logger.ex("Parse isolated objects.")
        self._parse_isolated_obj()
        logger.ex("Parse inter modules.")
        self._parse_inter_modules()
        self._wrap()
        self._clean()

    def _wrap(self) -> None:
        for name in self.primary_keys():
            self[name] = ModuleWrapper(self[name])

    def _clean(self) -> None:
        for name in self.non_primary_keys():
            if name in self.registered_fields or isinstance(self[name], ModuleNode):
                self.pop(name)

    def primary_keys(self) -> Generator[str, None, None]:
        for name in self.primary_fields:
            if name in self:
                yield name

    def non_primary_keys(self) -> Generator[str, None, None]:
        keys = list(self.keys())
        for k in keys:
            if k not in self.primary_fields:
                yield k

    def _parse_primary_modules(self) -> None:
        for name in self.primary_keys():
            logger.ex(f"parse field {name}.")
            if name in self.registered_fields:
                base = name
                logger.ex(f"Find field registed. Base field is {base}.")
            else:
                reg = Registry.get_registry(self.primary_to_registry.get(name, ""))
                if reg is None:
                    raise CoreConfigParseError(f"Undefined registry `{name}`.")
                for n in self[name]:
                    if n not in reg:
                        raise CoreConfigParseError(f"Unregistered module `{n}`.")
                base = reg.name
                logger.ex(f"Search from Registry. Base field is {base}.")

            self[name] = _dict2node(OTHER_FLAG, base, self.pop(name))
            logger.ex(f"Set ModuleNode to self[{name}].")

    def _parse_isolated_registered_module(self, name: str) -> None:
        v = _dict2node(OTHER_FLAG, name, self.pop(name))
        for i in v.values():
            _, _ = Registry.find(i.name)
            if _ is None:
                raise CoreConfigParseError(f"Unregistered module `{i.name}`")
        self[name] = v

    def _parse_implicit_module(self, name: str, module_type: NodeType) -> ModuleNode:
        _, base = Registry.find(name)
        if not base:
            raise CoreConfigParseError(f"Unregistered module `{name}`")
        logger.ex(f"Find base {base} with implicit module {name}.")
        node = module_type.from_base_name(base, name)
        _check_implicit_module(node)
        if module_type == ReusedNode:
            logger.ex("Target type is ReusedNode, set node to top level.")
            self[name] = node
        return node

    def _parse_isolated_module(self, name: str) -> bool:
        logger.ex(f"Not a registed field. Parse isolated module {name}.")
        _, base = Registry.find(name)
        if base:
            logger.ex("Find registed. Convert to `ModuleNode`.")
            self[name] = ModuleNode.from_base_name(base, name) << self[name]
            return True
        return False

    def _parse_scratchpads(self, name: str) -> None:
        logger.ex(f"Not a registed node. Regrad as scratchpads {name}.")
        has_module = False
        modules = self[name]
        for k, v in list(modules.items()):
            if not isinstance(v, dict):
                return
            _, base = Registry.find(k)
            if base:
                has_module = True
                logger.ex("Find item registed. Convert to `ModuleNode`.")
                modules[k] = ModuleNode.from_base_name(base, k) << v
        if has_module:
            logger.ex(f"Add `{name}` to scratchpads_fields.")
            self.scratchpads_fields.add(name)
            self.all_fields.add(name)

    def _parse_isolated_obj(self) -> None:
        for name in self.non_primary_keys():
            logger.ex(f"parse module {name}.")
            modules = self[name]
            if isinstance(modules, dict):
                if name in self.registered_fields:
                    logger.ex("Find module registed.")
                    self._parse_isolated_registered_module(name)
                elif not self._parse_isolated_module(name):
                    self._parse_scratchpads(name)

    def _contain_module(self, name: str) -> bool:
        is_contain = False
        for k in self.all_fields:
            if k not in self:
                continue
            for node in self[k].values():
                if node.name == name:
                    if not is_contain:
                        is_contain = True
                    else:
                        raise CoreConfigParseError(
                            f"Parameter `{name}` conflicts with "
                            f"field `{self.current_field}` and `{k}`, "
                            f"considering using format `$field` to get module."
                        )
                    self.current_field = k
        return is_contain

    def _get_name_and_field(
        self, name: str, ori_name: str
    ) -> tuple[str, str | None] | tuple[list[str], str]:
        if not name.startswith("$"):
            return name, None
        names = name[1:].split("::")
        if len(names) > 2:
            raise CoreConfigParseError(f"Only support index one level with name `{name}`")
        base = names[0]
        spec_name = names[1:]
        modules = self.get(base, False)
        if not modules:
            raise CoreConfigParseError(f"Cannot find field `{base}` with `{ori_name}`")
        if len(spec_name) > 0:
            if spec_name[0] == "*":
                logger.warning(
                    f"`The results of {names} "
                    "depend on their definition in config files when using `*`."
                )
                return [k.name for k in modules.values()], base
            if spec_name[0] not in modules:
                raise CoreConfigParseError(
                    f"Cannot get module `{spec_name[0]}` with param `{name}`."
                    f" Should be one of `{[k.name for k in modules.values()]}`."
                )
            return spec_name[0], base
        elif len(modules) > 1:
            raise CoreConfigParseError(
                f"More than one candidates are found: {[k.name for k in modules.values()]}"
                f" with `{ori_name}`, please redifine the field `{base}` in config files, "
                f"or get module with format `$field.name`."
            )
        return list(modules.keys())[0], base

    def _apply_hooks(self, node: ModuleNode, hooks: list[str], attrs: list[str]) -> ConfigNode:
        if attrs:
            node = ChainedInvocationWrapper(node, attrs)  # type: ignore
        if not hooks:
            return node
        for hook in hooks:
            if hook not in self:
                raise CoreConfigParseError(f"Unregistered hook `{hook}`")
            node = self[hook](node=node)
        return node

    def _convert_node(
        self, name: str, source: ConfigDict, target_type: NodeType
    ) -> tuple[ModuleNode, NodeType]:
        ori_type = source[name].__class__
        logger.ex(f"Original_type is `{ori_type}`, target_type is `{target_type}`.")
        node = source[name]
        if target_type.priority != ori_type.priority or target_type is ClassNode:
            node = target_type.from_node(source[name])
            self._parse_module(node)
            if target_type.priority > ori_type.priority:
                source[name] = node
        return node, ori_type

    def _parse_single_param(
        self,
        name: str,
        ori_name: str,
        field: str | None,
        target_type: NodeType,
        attrs: list[str],
        hooks: list[str],
    ) -> ConfigNode:
        if name in self.all_fields:
            raise CoreConfigParseError(
                f"Conflict name: `{name}`, the class name cannot be same with field name"
            )
        ori_type = None
        cache_field = self.current_field
        if not field and name in self:
            logger.ex("Find module in top level.")
            node, ori_type = self._convert_node(name, self, target_type)
        elif field or self._contain_module(name):
            self.current_field = field or self.current_field
            logger.ex(f"Find module in second level, " f"current_field is {self.current_field}.")
            node, ori_type = self._convert_node(name, self[self.current_field], target_type)
        else:
            logger.ex("Implicit module.")
            node = self._parse_implicit_module(name, target_type)
        self.current_field = cache_field

        # InterNode and ReusedNode
        if ori_type and ori_type.priority + target_type.priority == 5:
            raise CoreConfigParseError(
                f"Error when parsing param `{ori_name}`, "
                f"target_type is `{target_type}`, but got original_type `{ori_type}`. "
                f"Please considering using `scratchpads` to avoid conflicts."
            )
        node = self._apply_hooks(node, hooks, attrs)  # type: ignore
        return node

    def _parse_param(
        self, ori_name: str, module_type: SpecialFlag
    ) -> ConfigNode | list[ConfigNode] | VariableReference:
        logger.ex(f"Parse with {ori_name}, {module_type}")
        if module_type == REFER_FLAG:
            return VariableReference(ori_name)
        target_type = _dispatch_module_node[module_type]
        name, attrs, hooks = _parse_param_name(ori_name)
        names, field = self._get_name_and_field(name, ori_name)
        logger.ex(f"Get name:{names}, field:{field}, attrs:{attrs}, hooks:{hooks}.")
        if isinstance(names, list):
            logger.ex(f"Detect output type list {ori_name}.")
            return [
                self._parse_single_param(n, ori_name, field, target_type, attrs, hooks)
                for n in names
            ]
        return self._parse_single_param(names, ori_name, field, target_type, attrs, hooks)

    def _parse_module(self, node: ModuleNode) -> None:
        logger.ex(f"Parse ModuleNode {node}.")
        for param_name in list(node.keys()):
            true_name, module_type = _is_special(param_name)
            if not module_type:
                logger.ex(f"Skip parameter {param_name}.")
                continue
            value = node.pop(param_name)
            is_dict = False
            if isinstance(value, list):
                logger.ex(f"{param_name}: List parameter {value}.")
                value = [self._parse_param(v, module_type) for v in value]
                value = _flatten_list(value)
            elif isinstance(value, str):
                logger.ex(f"{param_name}: Single parameter {value}.")
                value = self._parse_param(value, module_type)
            elif isinstance(value, dict):
                logger.ex(f"{param_name}: Dict parameter {value}.")
                value = {k: self._parse_param(v, module_type) for k, v in value.items()}
                is_dict = True
            else:
                raise CoreConfigParseError(f"Wrong type: {param_name, value}")
            if isinstance(value, VariableReference):
                ref_name = value()
                logger.ex(f"Detect VariableReference, value is parsed to {ref_name}.")
                if not value.has_env:
                    if ref_name not in self:
                        raise CoreConfigParseError(f"Can not find reference: {ref_name}.")
                    node[true_name] = self[ref_name]
                else:
                    node[true_name] = ref_name
            else:
                # FIXME: Parsing inner VariableReference
                node[true_name] = ModuleWrapper(value, is_dict)

    def _parse_inter_modules(self) -> None:
        for name in list(self.keys()):
            logger.ex(f"Parse inter module {name}")
            module = self[name]
            if (
                name in self.primary_fields
                or name in self.scratchpads_fields
                and isinstance(module, dict)
            ):
                logger.ex(f"Parse Dict {name}")
                for m in module.values():
                    self._parse_module(m)
            elif isinstance(module, ModuleNode):
                self._parse_module(module)

    def __str__(self) -> str:
        _dict: dict = {}
        for k, v in self.items():
            self._flatten(_dict, k, v)
        return _create_table(
            None,
            [(k, v) for k, v in _dict.items()],
        )

    def _flatten(self, _dict: dict, k: str, v: dict) -> None:
        if isinstance(v, dict) and not isinstance(v, ModuleNode):
            for _k, _v in v.items():
                _dict[".".join([k, _k])] = _v
        else:
            _dict[k] = v

    def dump(self, path: str) -> None:
        import toml

        with open(path, "w", encoding="UTF-8") as f:
            toml.dump(self, f)


def set_primary_fields(cfg) -> None:
    primary_fields = cfg.primary_fields
    primary_to_registry = cfg.primary_to_registry
    if hasattr(ConfigDict, "primary_fields"):
        logger.ex("`primary_fields` will be set to {}", primary_fields)
    if primary_fields:
        ConfigDict.set_primary_fields(primary_fields, primary_to_registry)
