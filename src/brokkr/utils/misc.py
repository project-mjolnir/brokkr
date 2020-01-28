"""
General utility functions for Brokkr.
"""

# Standard library imports
import collections.abc
import functools
import getpass
import logging
import os
import time
import sys


def time_ns():
    # Fallback to non-ns time functions on Python <=3.6
    try:
        return time.time_ns()
    except AttributeError:
        return int(time.time()) * 1e9


def monotonic_ns():
    # Fallback to non-ns time functions on Python <=3.6
    try:
        return time.monotonic_ns()
    except AttributeError:
        return int(time.monotonic()) * 1e9


START_TIME = monotonic_ns()


def start_time_offset(n_digits=3):
    return round((monotonic_ns() - START_TIME) / 1e9, n_digits)


def setup_basic_logging(verbose=None):
    log_format = "{message}"
    if verbose is None:
        logging_level = 99
    elif verbose:
        logging_level = "DEBUG"
        log_format = "{levelname}: ({name}) {message}"
    else:
        logging_level = "INFO"
    logging.basicConfig(stream=sys.stdout, level=logging_level,
                        format=log_format, style="{")


def basic_logging(func):
    @functools.wraps(func)
    def _basic_logging(*args, verbose=None, **kwargs):
        setup_basic_logging(verbose=verbose)
        value = func(*args, **kwargs)
        return value
    return _basic_logging


def update_dict_recursive(base, update):
    for update_key, update_value in update.items():
        base_value = base.get(update_key, {})
        if not isinstance(base_value, collections.abc.Mapping):
            base[update_key] = update_value
        elif isinstance(update_value, collections.abc.Mapping):
            base[update_key] = update_dict_recursive(
                base_value, update_value)
        else:
            base[update_key] = update_value
    return base


def get_actual_username():
    try:
        username = os.environ["SUDO_USER"]
        if username:
            return username
    except KeyError:
        pass
    return getpass.getuser()


def auto_repr(exclude):
    def auto_repr_inner(obj):
        def wrapper(self):
            argument_list = ", ".join([f"{key}={value!r}"
                                       for key, value in self.__dict__.items()
                                       if key not in exclude])
            return f"{type(self).__name__}({argument_list})"
        setattr(obj, "__repr__", wrapper)
        return obj
    return auto_repr_inner
