from typing import Dict, List, Type

from .._exceptions import CoreConfigParseError
from ..engine import Registry, logger
from ..utils.misc import _create_table
from .model import (
    OTHER_FLAG,
    REFER_FLAG,
    ChainedInvocationWrapper,
    ModuleNode,
    ModuleWrapper,
    ReusedNode,
    VariableReference,
    _dispatch_module_node,
    _is_special,
)


def _dict2node(module_type: str, base: str, _dict: Dict, return_list=False):
    ModuleType: Type[ModuleNode] = _dispatch_module_node[module_type]
    if return_list:
        return [ModuleType.from_base_name(base, name, **v) for name, v in _dict.items()]
    return {name: ModuleType.from_base_name(base, name, **v) for name, v in _dict.items()}


def _parse_param_name(name):
    names = name.split("@")
    attrs = names.pop(0).split(".")
    attrs = [i for i in attrs if i]
    hooks = [i for i in names if i]
    return attrs.pop(0), attrs, hooks


class ConfigDict(dict):
    target_fields: List
    registered_fields: List

    def __new__(cls):
        if not hasattr(cls, "target_fields"):
            raise RuntimeError("Call `set_target_fields` before `load`")

        # make target fields unique when multiple load.
        class ConfigDictImpl(ConfigDict):
            # otherwise it will share the same class variable with father class.
            target_fields = ConfigDict.target_fields

        inst = super().__new__(ConfigDictImpl)
        return inst

    @classmethod
    def set_target_fields(cls, target_fields):
        """
        Sets the `target_modules` attribute to the specified list of module names,
            and `registered_modules` attributes based on the current state
            of the `Registry` object.

        Note that `set_key_fields` must be called before `config.load`.

        Attributes:
            target_modules (List[str]): Target module names that need to be built.
            registered_modules (List[str]): A list of all module names that have been registered.
        """
        cls.target_fields = target_fields

    def parse(self):
        self._parse_target_modules()
        self._parse_isolated_obj()
        self._parse_inter_modules()
        self._wrap()
        self._clean()

    def _wrap(self):
        for name in self.target_keys():
            self[name] = ModuleWrapper(self[name])

    def _clean(self):
        for name in self.non_target_keys():
            if name in self.registered_fields or isinstance(self[name], ModuleNode):
                self.pop(name)

    def target_keys(self):
        for name in self.target_fields:
            if name in self:
                yield name

    def non_target_keys(self):
        keys = list(self.keys())
        for k in keys:
            if k not in self.target_fields:
                yield k

    def _parse_target_modules(self):
        for name in self.target_keys():
            if name in self.registered_fields:
                base = name
            else:
                reg = Registry.get_registry(name)
                if reg is None:
                    raise CoreConfigParseError(f"Undefined registry `{name}`")
                for n in self[name].keys():
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
        if module_type == ReusedNode:
            self[name] = node
        return node

    def _parse_isolated_module(self, name, module_type):
        _, base = Registry.find(name)
        if base:
            self[name] = module_type.from_base_name(base, name).update(self[name])

    def _parse_isolated_obj(self):
        for name in self.non_target_keys():
            modules = self[name]
            if isinstance(modules, dict):
                if name in self.registered_fields:
                    self._parse_isolated_registered_module(name)
                else:
                    self._parse_isolated_module(name, ModuleNode)

    def _contain_module(self, name):
        fileds = set([*self.target_fields, *self.registered_fields])
        for k in fileds:
            if k not in self:
                continue
            for node in self[k].values():
                if node.name == name:
                    self.__base__ = k
                    return True
        return False

    def _get_name(self, name, ori_name):
        if not name.startswith("$"):
            return name
        base = name[1:]
        modules = self.get(base, False)
        if not modules:
            raise CoreConfigParseError(f"Cannot find field {base} with `{ori_name}`")
        if len(modules) == 1:
            return list(modules.keys())[0]
        raise CoreConfigParseError(
            f"More than one candidates are found: {[k.name for k in modules.values()]}"
            f" with `{ori_name}`, please redifine the field `{base}` in config files."
        )

    def _apply_hooks(self, node, hooks):
        for hook in hooks:
            if hook not in self:
                raise CoreConfigParseError(f"Unregistered hook {hook}")
            node = self[hook](node=node)
        return node

    def _parse_single_param(self, ori_name, module_type):
        if module_type == REFER_FLAG:
            return VariableReference(ori_name)
        target_type = _dispatch_module_node[module_type]
        name, attrs, hooks = _parse_param_name(ori_name)
        name = self._get_name(name, ori_name)
        ori_type = None
        if name in self:
            ori_type = self[name].__class__
            if ori_type == ModuleNode:
                self[name] = target_type.from_node(self[name])
            node = self[name]
        elif self._contain_module(name):
            ori_type = self[self.__base__][name].__class__
            if ori_type == ModuleNode:
                self[self.__base__][name] = target_type.from_node(self[self.__base__][name])
            node = self[self.__base__][name]
        else:
            node = self._parse_implicit_module(name, target_type)
        if ori_type and ori_type not in (ModuleNode, target_type):
            raise CoreConfigParseError(
                f"Error when parsing params {ori_name}, \
                  target_type is {target_type}, but got {ori_type}"
            )
        name = node.name  # for ModuleWrapper
        if attrs:
            node = ChainedInvocationWrapper(node, attrs)
            node.name = name
        if hooks:
            node = self._apply_hooks(node, hooks)
            node.name = name
        if hasattr(self, "__base__"):
            delattr(self, "__base__")
        return node

    def _parse_modules(self, node: ModuleNode):
        for param_name in list(node.keys()):
            true_name, module_type = _is_special(param_name)
            if not module_type:
                continue
            value = node.pop(param_name)
            if isinstance(value, list):
                value = [self._parse_single_param(v, module_type) for v in value]
            elif isinstance(value, str):
                value = self._parse_single_param(value, module_type)
            else:
                raise CoreConfigParseError(f"Wrong type: {param_name, value}")
            if isinstance(value, VariableReference):
                ref_name = value()
                if ref_name not in self:
                    raise CoreConfigParseError(f"Can not find reference: {ref_name}.")
                node[true_name] = self[ref_name]
            else:
                node[true_name] = ModuleWrapper(value)

    def _parse_inter_modules(self):
        for name in list(self.keys()):
            module = self[name]
            if name in self.target_fields and isinstance(module, dict):
                for m in module.values():
                    self._parse_modules(m)
            elif isinstance(module, ModuleNode):
                self._parse_modules(module)

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


def set_target_fields(target_fields):
    if hasattr(ConfigDict, "target_fields"):
        logger.ex("`target_fields` will be set to {}", target_fields)
    if target_fields:
        ConfigDict.set_target_fields(target_fields)
