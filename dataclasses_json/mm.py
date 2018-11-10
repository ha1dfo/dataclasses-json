import warnings
from dataclasses import MISSING, is_dataclass

from marshmallow import fields

from dataclasses_json.core import _is_supported_generic
from dataclasses_json.utils import (_is_collection, _is_mapping,
                                    _is_nonstr_collection, _issubclass_safe)

_type_to_cons = {
    dict: fields.Dict,
    list: fields.List,
    str: fields.Str,
    int: fields.Int,
    float: fields.Float,
    bool: fields.Bool
}


def _make_nested_fields(fields_, dataclass_json_cls):
    nested_fields = {}
    for field, type_, field_many in _inspect_nested_fields(fields_):
        if _issubclass_safe(type_, dataclass_json_cls):
            schema = fields.Nested(type_.schema(),
                                   many=field_many,
                                   default=None)
            nested_fields[field.name] = schema
        else:
            warnings.warn(f"Nested dataclass field {field.name} of type "
                          f"{field.type} detected in "
                          f"{cls.__name__} that is not an instance of "
                          f"dataclass_json. Did you mean to recursively "
                          f"serialize this field? If so, make sure to "
                          f"augment {field.type} with either the "
                          f"`dataclass_json` decorator or mixin.")
    return nested_fields


def _inspect_nested_fields(fields_):
    nested_dc_fields_and_is_many = []
    for field in fields_:
        if _is_supported_generic(field.type):
            t_arg = field.type.__args__[0]
            if is_dataclass(t_arg):
                if _is_collection(field.type):
                    nested_dc_fields_and_is_many.append((field, t_arg, True))
                else:
                    nested_dc_fields_and_is_many.append((field, t_arg, False))
        elif is_dataclass(field.type):
            nested_dc_fields_and_is_many.append((field, field.type, False))
    return nested_dc_fields_and_is_many


def _make_default_fields(fields_, cls):
    default_fields = {}
    for field in fields_:
        if field.default is not MISSING:
            default_fields[field.name] = _make_default_field(field.type,
                                                             field.default,
                                                             cls)
        elif field.default_factory is not MISSING:
            default_fields[field.name] = _make_default_field(field.type,
                                                             field.default_factory,
                                                             cls)
    return default_fields


def _make_default_field(type_, default, cls):
    cons_type = type_
    cons_type = (list if _is_nonstr_collection(cons_type) else cons_type)
    cons_type = (dict if _is_mapping(cons_type) else cons_type)
    cons = _type_to_cons[cons_type]
    if cons is fields.List:
        type_arg = type_.___args__[0]
        if type_arg not in _type_to_cons:
            raise TypeError(f"Unsupported {type_arg} detected. Is it "
                            f"a supported JSON type or dataclass_json "
                            f"instance?")
        arg_cons = _type_to_cons[type_arg]
        return cons(cls, arg_cons, missing=default)
    return cons(cls, missing=default)