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

# Local imports
from brokkr.config.constants import PACKAGE_NAME


# --- Time functions --- #

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


# --- Logging functions --- #

MAX_VERBOSE = 3
MIN_VERBOSE = -3
LOG_LEVEL = {
    -3: 99,
    -2: logging.CRITICAL,
    -1: logging.ERROR,
    0: logging.WARNING,
    1: logging.INFO,
    2: logging.DEBUG,
    3: logging.DEBUG,
    }
SUBHANDLERS_LEVEL = 3


def determine_log_level(verbose=0):
    verbose = round(verbose)
    if verbose > MAX_VERBOSE:
        return LOG_LEVEL[MAX_VERBOSE]
    if verbose < MIN_VERBOSE:
        return LOG_LEVEL[MIN_VERBOSE]
    return LOG_LEVEL[verbose]


def setup_basic_logging(verbose=0, quiet=0, script_mode=False):
    # Setup logging config
    log_args = {"stream": sys.stdout, "style": "{"}

    verbose = 0 if verbose is None else verbose
    quiet = 0 if quiet is None else quiet
    verbose_net = verbose - quiet

    log_level = determine_log_level(verbose_net)
    if script_mode and log_level >= logging.INFO:
        log_args["format"] = "{message}"
    else:
        log_args["format"] = "{levelname} | {name} | {message}"
    if script_mode or verbose >= SUBHANDLERS_LEVEL:
        log_args["level"] = log_level

    # Initialize logging
    logging.basicConfig(**log_args)
    logger = logging.getLogger(PACKAGE_NAME)
    if not script_mode and verbose_net < SUBHANDLERS_LEVEL:
        logger.setLevel(log_level)
    return logger


def basic_logging(func):
    @functools.wraps(func)
    def _basic_logging(*args, verbose=0, quiet=0, **kwargs):
        setup_basic_logging(verbose=verbose, quiet=quiet, script_mode=True)
        value = func(*args, **kwargs)
        return value
    return _basic_logging


# --- General utility functions --- #

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


# --- Common utility mixins and decorators --- #

class AutoReprMixin:
    def __repr__(self):
        argument_list = ", ".join(
            [f"{key}={value!r}" for key, value in self.__dict__.items()])
        return f"{type(self).__name__}({argument_list})"
