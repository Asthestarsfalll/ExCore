from typing import Dict, List, Optional, Set, Type

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


def _dict2node(module_type: str, base: str, _dict: Dict):
    ModuleType: Type[ModuleNode] = _dispatch_module_node[module_type]
    return {name: ModuleType.from_base_name(base, name, v) for name, v in _dict.items()}


def _parse_param_name(name):
    names = name.split("@")
    attrs = names.pop(0).split(".")
    attrs = [i for i in attrs if i]
    hooks = [i for i in names if i]
    return attrs.pop(0), attrs, hooks


def _flatten_list(lis):
    new_lis = []
    for i in lis:
        if isinstance(i, list):
            new_lis.extend(i)
        else:
            new_lis.append(i)
    return new_lis


def _flatten_dict(dic):
    new_dic = {}
    for k, v in dic.items():
        if isinstance(v, list):
            v = _flatten_list(v)
        new_dic[k] = v
    return new_dic


class ConfigDict(dict):
    primary_fields: List
    primary_to_registry: Dict[str, str]
    registered_fields: List
    all_fields: Set[str]
    scratchpads_fields: Set[str] = set()
    current_field: Optional[str] = None

    def __new__(cls):
        if not hasattr(cls, "primary_fields"):
            raise RuntimeError("Call `set_primary_fields` before `load`")

        # make primary fields unique when multiple load.
        class ConfigDictImpl(ConfigDict):
            # otherwise it will share the same class variable with father class.
            primary_fields = ConfigDict.primary_fields
            primary_to_registry = ConfigDict.primary_to_registry
            scratchpads_fields = ConfigDict.scratchpads_fields

        inst = super().__new__(ConfigDictImpl)
        return inst

    @classmethod
    def set_primary_fields(cls, primary_fields, primary_to_registry):
        """
        Sets the `primary_fields` attribute to the specified list of module names,
            and `registered_fields` attributes based on the current state
            of the `Registry` object.

        Note that `set_primary_fields` must be called before `config.load`.
        """
        cls.primary_fields = primary_fields
        cls.primary_to_registry = primary_to_registry

    def parse(self):
        self._parse_primary_modules()
        self._parse_isolated_obj()
        self._parse_inter_modules()
        self._wrap()
        self._clean()

    def _wrap(self):
        for name in self.primary_keys():
            self[name] = ModuleWrapper(self[name])

    def _clean(self):
        for name in self.non_primary_keys():
            if name in self.registered_fields or isinstance(self[name], ModuleNode):
                self.pop(name)

    def primary_keys(self):
        for name in self.primary_fields:
            if name in self:
                yield name

    def non_primary_keys(self):
        keys = list(self.keys())
        for k in keys:
            if k not in self.primary_fields:
                yield k

    def _parse_primary_modules(self):
        for name in self.primary_keys():
            if name in self.registered_fields:
                base = name
            else:
                reg = Registry.get_registry(self.primary_to_registry.get(name, ""))
                if reg is None:
                    raise CoreConfigParseError(f"Undefined registry `{name}`")
                for n in self[name]:
                    if n not in reg:
                        raise CoreConfigParseError(f"Unregistered module `{n}`")
                base = reg.name

            self[name] = _dict2node(OTHER_FLAG, base, self.pop(name))

    def _parse_isolated_registered_module(self, name):
        v = _dict2node(OTHER_FLAG, name, self.pop(name))
        for i in v.values():
            _, _ = Registry.find(i.name)
            if _ is None:
                raise CoreConfigParseError(f"Unregistered module `{i.name}`")
        self[name] = v

    def _parse_implicit_module(self, name, module_type):
        _, base = Registry.find(name)
        if not base:
            raise CoreConfigParseError(f"Unregistered module `{name}`")
        node = module_type.from_base_name(base, name)
        _check_implicit_module(node)
        if module_type == ReusedNode:
            self[name] = node
        return node

    def _parse_isolated_module(self, name):
        _, base = Registry.find(name)
        if base:
            self[name] = ModuleNode.from_base_name(base, name) << self[name]
            return True
        return False

    def _parse_scratchpads(self, name):
        has_module = False
        modules = self[name]
        for k, v in list(modules.items()):
            if not isinstance(v, dict):
                return
            _, base = Registry.find(k)
            if base:
                has_module = True
                modules[k] = ModuleNode.from_base_name(base, k) << v
        if has_module:
            self.scratchpads_fields.add(name)
            self.all_fields.add(name)

    def _parse_isolated_obj(self):
        for name in self.non_primary_keys():
            modules = self[name]
            if isinstance(modules, dict):
                if name in self.registered_fields:
                    self._parse_isolated_registered_module(name)
                elif not self._parse_isolated_module(name):
                    self._parse_scratchpads(name)

    def _contain_module(self, name):
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

    def _get_name_and_field(self, name, ori_name):
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

    def _apply_hooks(self, node, hooks, attrs):
        if attrs:
            node = ChainedInvocationWrapper(node, attrs)
        if not hooks:
            return node
        for hook in hooks:
            if hook not in self:
                raise CoreConfigParseError(f"Unregistered hook {hook}")
            node = self[hook](node=node)
        return node

    def _parse_single_param(self, name, ori_name, field, target_type, attrs, hooks):
        if name in self.all_fields:
            raise CoreConfigParseError(
                f"Conflict name: `{name}`, the class name cannot be same with field name"
            )
        ori_type = None
        if not field and name in self:
            ori_type = self[name].__class__
            if ori_type in (ModuleNode, ClassNode):
                node = target_type.from_node(self[name])
                self._parse_module(node)
                self[name] = node
            node = self[name]
        elif field or self._contain_module(name):
            self.current_field = field or self.current_field
            ori_type = self[self.current_field][name].__class__
            if ori_type in (ModuleNode, ClassNode):
                node = target_type.from_node(self[self.current_field][name])
                base = self.current_field
                self._parse_module(node)
                self.current_field = base
                self[self.current_field][name] = node
            node = self[self.current_field][name]
        else:
            node = self._parse_implicit_module(name, target_type)
        if ori_type and ori_type not in (ModuleNode, ClassNode, target_type):
            raise CoreConfigParseError(
                f"Error when parsing param `{ori_name}`, "
                f"target_type is `{target_type}`, but got `{ori_type}`"
            )
        node = self._apply_hooks(node, hooks, attrs)
        return node

    def _parse_param(self, ori_name, module_type):
        if module_type == REFER_FLAG:
            return VariableReference(ori_name)
        target_type = _dispatch_module_node[module_type]
        name, attrs, hooks = _parse_param_name(ori_name)
        name, field = self._get_name_and_field(name, ori_name)
        if isinstance(name, list):
            return [
                self._parse_single_param(n, ori_name, field, target_type, attrs, hooks)
                for n in name
            ]
        return self._parse_single_param(name, ori_name, field, target_type, attrs, hooks)

    def _parse_module(self, node: ModuleNode):
        for param_name in list(node.keys()):
            true_name, module_type = _is_special(param_name)
            if not module_type:
                continue
            value = node.pop(param_name)
            is_dict = False
            if isinstance(value, list):
                value = [self._parse_param(v, module_type) for v in value]
                value = _flatten_list(value)
            elif isinstance(value, str):
                value = self._parse_param(value, module_type)
            elif isinstance(value, dict):
                value = {k: self._parse_param(v, module_type) for k, v in value.items()}
                value = _flatten_dict(value)
                is_dict = True
            else:
                raise CoreConfigParseError(f"Wrong type: {param_name, value}")
            if isinstance(value, VariableReference):
                ref_name = value()
                if not value.has_env:
                    if ref_name not in self:
                        raise CoreConfigParseError(f"Can not find reference: {ref_name}.")
                    node[true_name] = self[ref_name]
                else:
                    node[true_name] = ref_name
            else:
                node[true_name] = ModuleWrapper(value, is_dict)

    def _parse_inter_modules(self):
        for name in list(self.keys()):
            module = self[name]
            if (
                name in self.primary_fields
                or name in self.scratchpads_fields
                and isinstance(module, dict)
            ):
                for m in module.values():
                    self._parse_module(m)
            elif isinstance(module, ModuleNode):
                self._parse_module(module)

    def __str__(self):
        _dict = {}
        for k, v in self.items():
            self._flatten(_dict, k, v)
        return _create_table(
            None,
            [(k, v) for k, v in _dict.items()],
            False,
        )

    def _flatten(self, _dict, k, v):
        if isinstance(v, dict) and not isinstance(v, ModuleNode):
            for _k, _v in v.items():
                _dict[".".join([k, _k])] = _v
        else:
            _dict[k] = v

    def dump(self, path: str):
        import toml

        with open(path, "w", encoding="UTF-8") as f:
            toml.dump(self, f)


def set_primary_fields(cfg):
    primary_fields = cfg["primary_fields"]
    primary_to_registry = cfg["primary_to_registry"]
    if hasattr(ConfigDict, "primary_fields"):
        logger.ex("`primary_fields` will be set to {}", primary_fields)
    if primary_fields:
        ConfigDict.set_primary_fields(primary_fields, primary_to_registry)
