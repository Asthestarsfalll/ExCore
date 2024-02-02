from typing import List

from .._exceptions import CoreConfigParseError
from ..engine import Registry, logger
from ..utils.misc import _create_table
from .model import (
    ChainedInvocationWrapper,
    InterNode,
    ModuleNode,
    ModuleWrapper,
    ReusedNode,
    VariableReference,
    _attr2module,
    _convert2module,
    _dispatch_module_node,
)


def _dict2list(v, return_list=False):
    """
    Converts a dictionary to a list of its values.

    Args:
        v (dict): The dictionary to be converted.
        return_list (bool): Enforce to return list.

    Returns:
        list: A list of the values in the input dictionary.
            If the input is not a dictionary or is an empty dictionary,
            the original input is returned.
            If the input dictionary has only one value and return_list is False,
            the value itself is returned.
    """
    if v:
        v = list(v.values())
        if not return_list and len(v) == 1:
            v = v[0]
    return v


def _parse_param(name):
    names = name.split("@")
    attrs = names.pop(0).split(".")
    attrs = [i for i in attrs if i]
    hooks = [i for i in names if i]
    return attrs.pop(0), attrs, hooks


class AttrNode(dict):
    target_fields: List
    registered_fields: List

    def __new__(cls):
        if not hasattr(cls, "target_fields"):
            raise RuntimeError("Call `set_target_fields` before `load`")

        # make target fields unique when multiple load.
        class AttrNodeImpl(AttrNode):
            # otherwise it will share the same class variable with father class.
            target_fields = AttrNode.target_fields

        inst = super().__new__(AttrNodeImpl)
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

    def isolated_keys(self):
        keys = list(self.keys())
        for k in keys:
            if k not in self.target_fields:
                yield k

    def _parse_target_modules(self):
        for name in self.target_fields:
            if name not in self:
                continue
            if name in self.registered_fields:
                base = name
            else:
                _, base = Registry.find(list(self[name].keys())[0])
                if base is None:
                    raise CoreConfigParseError(f"Unregistered module `{name}`")
            v = _attr2module(self.pop(name), base)
            v = _dict2list(v)
            self[name] = ModuleWrapper(v)

    def _parse_isolated_registered_module(self, name):
        v = _attr2module(self.pop(name), name)
        v = _dict2list(v, True)
        for i in v:
            assert i.base == name
            self[i.name] = ModuleWrapper(i)
            _, _ = Registry.find(i.name)
            if _ is None:
                raise CoreConfigParseError(f"Unregistered module `{i.name}`")

    def _parse_implicit_module(self, name, module_type=ModuleNode) -> ModuleWrapper:
        _, base = Registry.find(name)
        converted = ModuleWrapper(module_type(name, base))
        if not base:
            raise CoreConfigParseError(f"Unregistered module `{name}`")
        if module_type == ReusedNode:
            self[name] = converted
        return converted

    def _parse_isolated_module(self, name, module_type=ModuleNode):
        _, base = Registry.find(name)
        if base:
            self[name] = ModuleWrapper(module_type(name, base).update(self[name]))

    def _parse_isolated_obj(self):
        for name in self.isolated_keys():
            modules = self[name]
            if isinstance(modules, dict):
                if name in self.registered_fields:
                    self._parse_isolated_registered_module(name)
                else:
                    self._parse_isolated_module(name)

    def _contain_module(self, name):
        for k in self.target_fields:
            if k not in self:
                continue
            wrapper = self[k]
            if not isinstance(wrapper, ModuleWrapper):
                wrapper = ModuleWrapper(wrapper)
            for i in wrapper.values():
                if i.name == name:
                    self.__base__ = k
                    return True
        return False

    def _get_name(self, name, ori_name):
        if not name.startswith("$"):
            return name
        base = name[1:]
        wrapper = self.get(base, False)
        if not wrapper:
            raise CoreConfigParseError(
                f"Cannot find field {base} with `{ori_name}`,"
                "please adjust module definition order in config files."
            )
        if len(wrapper) == 1:
            return wrapper.first().name
        raise CoreConfigParseError(
            f"More than one candidates are found: {[k.name for k in wrapper.values()]}"
            f" with `{ori_name}`, please redifine the field `{base}` in config files."
        )

    def _apply_hooks(self, node, hooks):
        name = node.name  # for ModuleWrapper
        for h in hooks:
            node = self[h].first()(node=node)
        node.name = name
        return node

    # FIXME: Maybe ReusedNode should firstly search in hidden modules?
    def _parse_single_param(self, ori_name, params):
        name, attrs, hooks = _parse_param(ori_name)
        name = self._get_name(name, ori_name)
        ModuleType = _dispatch_module_node[params.base]
        if name in self:
            converted = _convert2module(self[name], params.base, ModuleType)
            self[name] = converted
        elif self._contain_module(name):
            # once the hiddn module was added to config
            # this branch is unreachable.
            wrapper = self[self.__base__]
            converted = _convert2module(getattr(wrapper, name), params.base, ModuleType)
            self[name] = converted
            if self.__base__ not in self.target_fields:
                wrapper.pop(name)
                if len(wrapper) == 0:
                    self.pop(self.__base__)
                self[self.__base__] = wrapper.first()
            else:
                wrapper.update(converted)
        else:
            # once the implicit module was added to config
            # this branch is unreachable.
            converted = self._parse_implicit_module(name, ModuleType)
        converted = converted.first()

        if not isinstance(converted, ModuleType):
            raise CoreConfigParseError(
                f"Error when parse params {params.name}, \
                  target_type is {ModuleType}, but got {type(converted)}"
            )
        if attrs:
            converted = ChainedInvocationWrapper(converted, attrs)
        if hooks:
            converted = self._apply_hooks(converted, hooks)
        return converted

    def _parse_module_node(self, node):
        to_pop = []
        param_names = list(node.keys())
        for param_name in param_names:
            params = node[param_name]
            if isinstance(params, InterNode):
                target_module_names = params.target_feild
                if not isinstance(target_module_names, list):
                    target_module_names = [target_module_names]
                converted_modules = [
                    self._parse_single_param(name, params) for name in target_module_names
                ]
                to_pop.extend(target_module_names)
                node[param_name] = ModuleWrapper(converted_modules)
            elif isinstance(params, VariableReference):
                ref_name = params()
                if ref_name not in self:
                    raise CoreConfigParseError(f"Can not find reference: {ref_name}.")
                node[param_name] = self[ref_name]
        if hasattr(self, "__route__"):
            delattr(self, "__route__")
        return to_pop

    def _parse_module_wrapper(self, wrapper):
        to_pop = []
        for m in wrapper.values():
            to_pop.extend(self._parse_module_node(m))
        return to_pop

    def _parse_inter_modules(self):
        to_pop = []
        for name in list(self.keys()):
            module = self[name]
            if isinstance(module, ModuleWrapper):
                to_pop.extend(self._parse_module_wrapper(module))
        self._clean(to_pop)

    def _clean(self, to_pop):
        for i in to_pop:
            self.pop(i, None)

    def parse(self):
        self._parse_target_modules()
        self._parse_isolated_obj()
        self._parse_inter_modules()

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
        if isinstance(v, dict):
            for _k, _v in v.items():
                _dict[".".join([k, _k])] = _v
        else:
            _dict[k] = v


def set_target_fields(target_fields):
    if hasattr(AttrNode, "target_fields"):
        logger.ex("`target_fields` will be set to {}", target_fields)
    if target_fields:
        AttrNode.set_target_fields(target_fields)
