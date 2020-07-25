"""
General utility functions for the pipeline module.
"""


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
