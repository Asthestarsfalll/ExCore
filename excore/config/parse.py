from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING

from .._exceptions import CoreConfigParseError, EnvVarParseError
from .._misc import _create_table
from ..engine import Registry, logger
from . import models
from .models import (
    HOOK_FLAGS,
    OTHER_FLAG,
    REFER_FLAG,
    ConfigHookNode,
    ModuleNode,
    ModuleWrapper,
    ReusedNode,
    _dispatch_argument_hook,
    _dispatch_module_node,
    _is_special,
)

if TYPE_CHECKING:
    from collections.abc import Generator, Sequence

    from typing_extensions import Self

    from .models import ConfigNode, NodeParams, NodeType, SpecialFlag


def _dict2node(module_type: SpecialFlag, base: str, _dict: dict) -> dict[str, ModuleNode]:
    ModuleType = _dispatch_module_node[module_type]
    return {name: ModuleType.from_base_name(base, name, v) for name, v in _dict.items()}


def _parse_param_name(name: str) -> tuple[str, list[tuple[str, str]]]:
    names = re.split(rf"([{''.join(HOOK_FLAGS)}])", name)
    return names.pop(0), list(zip(names[::2], names[1::2]))


def _flatten_list(
    lis: Sequence[ConfigNode | list[ConfigNode]],
) -> Sequence[ConfigNode]:
    new_lis = []
    for i in lis:
        if isinstance(i, list):
            new_lis.extend(i)
        else:
            new_lis.append(i)  # type: ignore
    return new_lis


class ConfigDict(dict):
    """A specialized dictionary used for parsing and managing configuration data.
        It extends the functionality of the standard Python dictionary to
        include methods for parsing configuration nodes,
        handling special parameters, and managing primary and registered fields.

    Attributes
        primary_fields: A list of primary field names.
        primary_to_registry: A dictionary mapping primary field names to
            their corresponding registries.
        registered_fields: A list of registered field names.
        all_fields: A set containing all field names.
        scratchpads_fields: A set containing scratchpad field names.
        current_field: The current field being processed (can be None).
        reused_caches: A dictionary for caching reused nodes.
    """

    primary_fields: list
    primary_to_registry: dict[str, str]
    registered_fields: list
    all_fields: set[str]
    scratchpads_fields: set[str] = set()
    current_field: str | None = None
    reused_caches: dict[str, ReusedNode]

    def __new__(cls) -> Self:
        if not hasattr(cls, "primary_fields"):
            raise RuntimeError("Call `set_primary_fields` before `load`")

        # make primary fields unique when multiple load.
        class ConfigDictImpl(ConfigDict):
            # otherwise it will share the same class variable with father class.
            primary_fields = ConfigDict.primary_fields
            primary_to_registry = ConfigDict.primary_to_registry
            scratchpads_fields = ConfigDict.scratchpads_fields
            reused_caches = {}

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

                i. If the field is registered, the base registry is set to field;
                ii. If not, search `Registry` to get the base registry of each node.

            2. Convert isolated objects to `ModuleNode`;

                i. If the field is registered, search `Registry` to get the base registry
                    of each node. Raising error if it cannot find;
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
            then it will be set back to config for cache according to the priority.
        For the last situation, it will only be set back when target module type is `ReusedNode`.
            But if the target module type is `ClassNode`, it will not be set back.

        NOTE: Set converted nodes back to config is necceary for `ReusedNode`.

        NOTE: use `export EXCORE_DEBUG=1` to enable excore debug to
            get more information when parsing.
        """
        models.IS_PARSING = True
        self._parse_primary_modules()
        self._parse_isolated_obj()
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
        logger.ex("Parse primary modules.")
        for name in self.primary_keys():
            logger.ex(f"\tParse primary field {name}.")
            if name in self.registered_fields:
                base = name
                logger.ex(f"\t\tFind field registered. Base field is `{base}`.")
            else:
                reg = Registry.get_registry(self.primary_to_registry.get(name, ""))
                if reg is None:
                    raise CoreConfigParseError(f"Undefined registry `{name}`.")
                for n in self[name]:
                    if n not in reg:
                        raise CoreConfigParseError(f"Unregistered module `{n}`.")
                base = reg.name
                logger.ex(f"\t\tSearch from Registry. Base field is {base}.")

            self[name] = _dict2node(OTHER_FLAG, base, self.pop(name))
            logger.ex(f"\tSet ModuleNode to self[{name}].")

    def _parse_isolated_registered_module(self, name: str) -> None:
        v = _dict2node(OTHER_FLAG, name, self.pop(name))
        for i in v.values():
            _, _ = Registry.find(i.name)
            if _ is None:
                raise CoreConfigParseError(f"Unregistered module `{i.name}`")
        self[name] = v

    def _parse_implicit_module(self, name: str, module_type: NodeType) -> ModuleNode:
        logger.ex("\t\t\tImplicit module.")
        _, base = Registry.find(name)
        if not base:
            raise CoreConfigParseError(f"Unregistered module `{name}`")
        logger.ex(f"\t\t\tFind base `{base}` with implicit module `{name}`.")
        node = module_type.from_base_name(base, name)
        if module_type is not ConfigHookNode:
            node.validate()
        if issubclass(module_type, ReusedNode):
            logger.ex("\t\t\tTarget type is `ReusedNode` or subclass of it, set node to top level.")
            self[name] = node
        return node

    def _parse_isolated_module(self, name: str) -> bool:
        logger.ex(f"\t\tNot a registered field. Parse as isolated module `{name}`.")
        _, base = Registry.find(name)
        if base:
            logger.ex("\t\tFind registered. Convert to `ModuleNode`.")
            self[name] = ModuleNode.from_base_name(base, name) << self[name]
            return True
        return False

    def _parse_scratchpads(self, name: str) -> None:
        logger.ex(f"\t\tNot a registered node. Regrad as scratchpads `{name}`.")
        has_module = False
        modules = self[name]
        for k, v in list(modules.items()):
            if not isinstance(v, dict):
                return
            _, base = Registry.find(k)
            if base:
                has_module = True
                logger.ex("\t\t\tFind item registered. Convert to `ModuleNode`.")
                modules[k] = ModuleNode.from_base_name(base, k) << v
        if has_module:
            logger.ex(f"\t\tAdd `{name}` to scratchpads_fields.")
            self.scratchpads_fields.add(name)
            self.all_fields.add(name)

    def _parse_isolated_obj(self) -> None:
        logger.ex("Parse isolated objects.")
        for name in self.non_primary_keys():
            logger.ex(f"\tParse module {name}.")
            modules = self[name]
            if isinstance(modules, dict):
                if name in self.registered_fields:
                    logger.ex("\t\tFind module registered.")
                    self._parse_isolated_registered_module(name)
                elif not self._parse_isolated_module(name):
                    self._parse_scratchpads(name)

    def _contain_module(self, name: str) -> bool:
        is_contain = False
        for k in self.all_fields:
            if k not in self:
                continue
            for node in self[k].values():
                if not hasattr(node, "name"):
                    continue
                if node.name == name:
                    if not is_contain:
                        is_contain = True
                    else:
                        raise CoreConfigParseError(
                            f"Parameter `{name}` conflicts with "
                            f"field `{self.current_field}` and `{k}`, "
                            f"considering using format `$field::module_name` to get module."
                        )
                    self.current_field = k
        return is_contain

    def _parse_env_var(self, value: str) -> str:
        env_names = re.findall(r"\$\{([^}]+)\}", value)
        for env in env_names:
            if not (env_value := os.environ.get(env, None)):
                raise EnvVarParseError(f"Can not get environment variable {env}.")
            value = re.sub(r"\$\{" + re.escape(env) + r"\}", env_value, value)
        return value

    def _get_name_and_field(
        self, name: str, ori_name: str | None = None
    ) -> tuple[str, str | None] | tuple[list[str], str]:
        parsed_value = self._parse_env_var(name)
        if parsed_value != name:
            return name, None
        if not name.startswith("$"):
            return name, None
        if len(spec_name := name[1:].split("::")) > 2:
            raise CoreConfigParseError(f"Only support index one level with name `{name}`")
        base = spec_name.pop(0)
        if not (modules := self.get(base, False)):
            raise CoreConfigParseError(f"Cannot find field `{base}` with `{ori_name or name}`")
        if len(spec_name) > 0:
            if spec_name[0] == "*":
                logger.warning(
                    f"`The results of {ori_name or name} "
                    "depend on their definition in config files when using `*`."
                )
                return [k.name for k in modules.values()], base
            if spec_name[0] not in modules:
                raise CoreConfigParseError(
                    f"Cannot get module `{spec_name[0]}` with param `{ori_name or name}`."
                    f" Should be one of `{[k.name for k in modules.values()]}`."
                )
            return spec_name[0], base
        elif len(modules) > 1:
            raise CoreConfigParseError(
                f"More than one candidates are found: {[k.name for k in modules.values()]}"
                f" with `{ori_name or name}`, please redefine the field `{base}` in config files, "
                f"or get module with format `$field::name`."
            )
        return list(modules.keys())[0], base

    def _apply_hooks(self, node: ConfigNode, hooks: list[tuple[str, str]]) -> ConfigNode:
        for hook_flag, hook_info in hooks:
            node = _dispatch_argument_hook[hook_flag].__excore_prepare__(node, hook_info, self)
        return node

    def _convert_node(
        self,
        name: str,
        source: ConfigDict,
        target_type: NodeType,
        node_params: NodeParams | None = None,
    ) -> tuple[ModuleNode, NodeType]:
        ori_type: NodeType = source[name].__class__
        logger.ex(f"\t\t\tOriginal_type is `{ori_type}`, target_type is `{target_type}`.")
        node: ModuleNode = source[name]
        if node_params:
            node.add(**node_params)
        if target_type.priority != ori_type.priority:
            node = target_type.from_node(source[name])
            self._parse_module(node)
            if target_type.priority > ori_type.priority:
                logger.ex("\t\t\tSet Back.")
                source[name] = node
        return node, ori_type

    def _get_node_from_name_and_field(
        self,
        name: str,
        field: str | None,
        target_type: NodeType,
        node_params: NodeParams | None = None,
    ) -> tuple[ModuleNode, NodeType | None]:
        ori_type = None
        cache_field = self.current_field
        if (node := target_type.__excore_parse__(self, **locals())) is not None:
            logger.ex(f"\t\t\t `__excore_parse__` from `{target_type}`, got node {node}.")
            return node, None
        if not field and name in self:
            logger.ex("\t\t\tFind module in top level.")
            node, ori_type = self._convert_node(name, self, target_type, node_params)
        elif field or self._contain_module(name):
            self.current_field = field or self.current_field
            logger.ex(
                f"\t\t\tFind module in second level, current_field is `{self.current_field}`."
            )
            node, ori_type = self._convert_node(
                name, self[self.current_field], target_type, node_params
            )
        else:
            node = self._parse_implicit_module(name, target_type)
        self.current_field = cache_field
        return node, ori_type

    def _parse_single_param(
        self,
        name: str,
        ori_name: str,
        field: str | None,
        target_type: NodeType,
        hooks: list[tuple[str, str]],
    ) -> ConfigNode:
        if name in self.all_fields:
            raise CoreConfigParseError(
                f"Conflict name: `{name}`, the class name cannot be same with field name"
            )
        node, ori_type = self._get_node_from_name_and_field(name, field, target_type)

        # InterNode and ReusedNode
        if ori_type and ori_type.__excore_check_target_type__(target_type):
            raise CoreConfigParseError(
                f"Error when parsing param `{ori_name}`, "
                f"target_type is `{target_type}`, but got original_type `{ori_type}`. "
                f"Please considering using `scratchpads` to avoid conflicts."
            )
        node = self._apply_hooks(node, hooks)  # type: ignore
        return node

    def _parse_params(
        self, ori_name: str, module_type: SpecialFlag
    ) -> ConfigNode | list[ConfigNode]:
        logger.ex(f"\t\tParse with `{ori_name}` and `{module_type}`.")
        target_type = _dispatch_module_node[module_type]
        name, hooks = _parse_param_name(ori_name)
        names, field = self._get_name_and_field(name, ori_name)
        logger.ex(f"\t\tGet name:{names}, field:{field}, hooks:{hooks}.")
        if isinstance(names, list):
            logger.ex(f"\t\tDetect output type list {ori_name}.")
            return [self._parse_single_param(n, ori_name, field, target_type, hooks) for n in names]
        return self._parse_single_param(names, ori_name, field, target_type, hooks)

    def _parse_module(self, node: ModuleNode) -> None:
        logger.ex(f"\t\tParse ModuleNode `{node}`.")
        for param_name in list(node.keys()):
            true_name, module_type = _is_special(param_name)
            if not module_type:
                logger.ex(f"\t\tSkip parameter `{param_name}`.")
                continue
            value = node.pop(param_name)
            if (
                isinstance(value, str)
                and value[0] == REFER_FLAG
                and not (value := self.get(value[1:], None))
            ):
                raise CoreConfigParseError(f"Cannot find `{value[1:]}` with `&`.")
            is_dict = False
            if isinstance(value, list):
                logger.ex(f"\t\t{param_name}: List parameter {value}.")
                value = [self._parse_params(v, module_type) for v in value]
                value = _flatten_list(value)
            elif isinstance(value, str):
                logger.ex(f"\t\t{param_name}: Single parameter {value}.")
                value = self._parse_params(value, module_type)
            elif isinstance(value, dict):
                logger.ex(f"\t\t{param_name}: Dict parameter {value}.")
                value = {k: self._parse_params(v, module_type) for k, v in value.items()}
                is_dict = True
            else:
                raise CoreConfigParseError(f"Wrong type: {param_name, value}")
            node[true_name] = ModuleWrapper(value, is_dict)

    def _parse_inter_modules(self) -> None:
        logger.ex("Parse inter modules.")
        for name in list(self.keys()):
            logger.ex(f"\tParse inter module `{name}`")
            module = self[name]
            if (
                name in self.primary_fields
                or name in self.scratchpads_fields
                and isinstance(module, ModuleNode)
            ):
                logger.ex(f"\tParse Dict {name}")
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
        logger.ex("`primary_fields` will be reset to {}", primary_fields)
    if primary_fields:
        ConfigDict.set_primary_fields(primary_fields, primary_to_registry)
