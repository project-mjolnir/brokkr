"""
General utility functions for the pipeline module.
"""

# Standard library imports
import unittest.mock


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


def is_all_na(input_data, na_values=None):
    na_values = {None} if na_values is None else na_values
    data_objects = get_data_objects(input_data)
    all_na = all([getattr(data_object, "is_na", data_object in na_values)
                  for data_object in data_objects])
    return all_na
