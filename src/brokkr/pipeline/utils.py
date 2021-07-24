"""
General utility functions for the pipeline module.
"""

# Standard library imports
import unittest.mock

# Local imports
import brokkr.utils.misc


# --- Sentinels and constants --- #

NASentinel = unittest.mock.sentinel.NASentinel

ShutdownSentinel = unittest.mock.sentinel.ShutdownSentinel


# --- Utility functions --- #

def get_data_objects(input_data):
    try:
        return list(input_data.values())
    except AttributeError:
        return [input_data]


def get_data_values(input_data):
    data_objects = get_data_objects(input_data)
    data_values = [getattr(data_object, "value", data_object)
                   for data_object in data_objects]
    return data_values


def get_data_object(input_data, key_name=None, pop_input=False):
    if not input_data:
        return input_data
    if key_name:
        try:
            if pop_input:
                return input_data.pop(key_name)
            return input_data[key_name]
        except TypeError:
            for data_obj in input_data:
                data_obj_name = getattr(data_obj, "name", None)
                if data_obj_name == key_name:
                    output_data_object = data_obj
                    break
            else:
                error_message = (
                    f"Could not find key '{key_name}' in input data")
                raise KeyError(error_message) from None
            if pop_input:
                input_data.remove(output_data_object)
    else:
        if len(input_data) == 1:
            try:
                input_data = list(input_data.values())
            except AttributeError:  # Input data isn't a dict
                pass
            output_data_object = input_data[0]
            if pop_input:
                input_data.clear()
        else:
            output_data_object = input_data
    return output_data_object


def get_data_value(input_data, key_name=None, pop_input=False):
    output_data_object = get_data_object(
        input_data, key_name=key_name, pop_input=pop_input)
    if not output_data_object:
        return output_data_object
    output_data_value = getattr(
        output_data_object, "value", output_data_object)
    return output_data_value


def is_all_na(input_data, na_values=None):
    na_values = [None] if na_values is None else list(na_values)
    data_objects = get_data_objects(input_data)
    all_na = all((getattr(data_object, "is_na", data_object in na_values)
                  for data_object in data_objects))
    return all_na


def truncate_to_headers(input_data=None):
    if not input_data:
        return input_data
    input_data = brokkr.utils.misc.safe_deepcopy(input_data)
    data_objects = get_data_objects(input_data)
    for data_object in data_objects:
        header_bytes = getattr(data_object, "header_bytes", None)
        if header_bytes:
            data_object.value = data_object.value[:header_bytes]
    return input_data
