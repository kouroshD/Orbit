# Copyright (c) 2022, NVIDIA CORPORATION & AFFILIATES, ETH Zurich, and University of Toronto
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Utilities for working with dictionaries."""


import collections.abc
import importlib
from typing import Any, Callable, Dict, Iterable, Mapping

__all__ = ["class_to_dict", "update_class_from_dict", "update_dict", "print_dict"]

"""
Dictionary <-> Class operations.
"""


def class_to_dict(obj: object) -> Dict[str, Any]:
    """Convert an object into dictionary recursively.

    Note:
        Ignores all names starting with "__" (i.e. built-in methods).

    Args:
        obj (object): An instance of a class to convert.

    Raises:
        ValueError: When input argument is not an object.

    Returns:
        Dict[str, Any]: Converted dictionary mapping.
    """
    # check that input data is class instance
    if not hasattr(obj, "__class__"):
        raise ValueError(f"Expected a class instance. Received: {type(obj)}.")
    # convert object to dictionary
    if isinstance(obj, dict):
        obj_dict = obj
    else:
        obj_dict = obj.__dict__
    # convert to dictionary
    data = dict()
    for key, value in obj_dict.items():
        # disregard builtin attributes
        if key.startswith("__"):
            continue
        # check if attribute is callable -- function
        if callable(value):
            data[key] = f"{value.__module__}:{value.__name__}"
        # check if attribute is a dictionary
        elif hasattr(value, "__dict__") or isinstance(value, dict):
            data[key] = class_to_dict(value)
        else:
            data[key] = value
    return data


def update_class_from_dict(obj, data: Dict[str, Any], _ns: str = "") -> None:
    """Reads a dictionary and sets object variables recursively.

    This function performs in-place update of the class member attributes.

    Args:
        obj (object): An instance of a class to update.
        data (Dict[str, Any]): Input dictionary to update from.
        _ns (str): Namespace of the current object. This is useful for nested configuration
            classes or dictionaries. Defaults to "".

    Raises:
        TypeError: When input is not a dictionary.
        ValueError: When dictionary has a value that does not match default config type.
        KeyError: When dictionary has a key that does not exist in the default config type.
    """
    for key, value in data.items():
        key_ns = _ns + "/" + key
        if hasattr(obj, key):
            obj_mem = getattr(obj, key)
            if isinstance(obj_mem, Mapping):
                # Note: We don't handle two-level nested dictionaries. Just use configclass if this is needed.
                # iterate over the dictionary to look for callable values
                for k, v in obj_mem.items():
                    if callable(v):
                        value[k] = _string_to_callable(value[k])
                setattr(obj, key, value)
            elif isinstance(value, Mapping):
                # recursively call if it is a dictionary
                update_class_from_dict(obj_mem, value, _ns=key_ns)
            elif isinstance(value, Iterable) and not isinstance(value, str):
                # check length of value to be safe
                if len(obj_mem) != len(value) and obj_mem is not None:
                    raise ValueError(
                        f"[Config]: Incorrect length under namespace: {key_ns}. Expected: {len(obj_mem)}, Received: {len(value)}."
                    )
                else:
                    setattr(obj, key, value)
            elif callable(obj_mem):
                # update function name
                value = _string_to_callable(value)
                setattr(obj, key, value)
            elif isinstance(value, type(obj_mem)):
                # check that they are type-safe
                setattr(obj, key, value)
            else:
                raise ValueError(
                    f"[Config]: Incorrect type under namespace: {key_ns}. Expected: {type(obj_mem)}, Received: {type(value)}."
                )
        else:
            raise KeyError(f"[Config]: Key not found under namespace: {key_ns}.")


"""
Dictionary operations.
"""


def update_dict(orig_dict: dict, new_dict: collections.abc.Mapping) -> dict:
    """Updates existing dictionary with values from a new dictionary.

    This function mimics the dict.update() function. However, it works for
    nested dictionaries as well.

    Reference:
        https://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth

    Args:
        orig_dict (dict): The original dictionary to insert items to.
        new_dict (collections.abc.Mapping): The new dictionary to insert items from.

    Returns:
        dict: The updated dictionary.
    """
    for keyname, value in new_dict.items():
        if isinstance(value, collections.abc.Mapping):
            orig_dict[keyname] = update_dict(orig_dict.get(keyname, {}), value)
        else:
            orig_dict[keyname] = value
    return orig_dict


def print_dict(val, nesting: int = -4, start: bool = True):
    """Outputs a nested dictionary."""
    if type(val) == dict:
        if not start:
            print("")
        nesting += 4
        for k in val:
            print(nesting * " ", end="")
            print(k, end=": ")
            print_dict(val[k], nesting, start=False)
    else:
        print(val)


"""
Private helper functions.
"""


def _string_to_callable(name: str) -> Callable:
    """Resolves the module and function names to return the function.

    Args:
        name (str): The function name. The format should be 'module:attribute_name'.

    Raises:
        ValueError: When the resolved attribute is not a function.
        ValueError: _description_

    Returns:
        Callable: The function loaded from the module.
    """
    try:
        mod_name, attr_name = name.split(":")
        mod = importlib.import_module(mod_name)
        callable_object = getattr(mod, attr_name)
        # check if attribute is callable
        if callable(callable_object):
            return callable_object
        else:
            raise ValueError(f"The imported object is not callable: '{name}'")
    except AttributeError as e:
        msg = (
            "While updating the config from a dictionary, we could not interpret the entry"
            "as a callable object. The format of input should be 'module:attribute_name'\n"
            f"While processing input '{name}', received the error:\n {e}."
        )
        raise ValueError(msg)
