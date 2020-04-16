"""
General utility functions for Brokkr.
"""

# Standard library imports
import collections.abc
import functools
import getpass
import logging
import multiprocessing
import operator
import os
from pathlib import Path
import signal
import time

# Third party imports
import packaging.version

# Local imports
import brokkr
from brokkr.constants import (
    SLEEP_TICK_S,
    LEVEL_NAME_SYSTEM,
    SYSTEM_NAME_DEFAULT,
    )


# Constants for run periodic
NS_IN_S = int(1e9)
SIGNALS_SET = ["SIG" + signame for signame in {"TERM", "HUP", "INT", "BREAK"}]


# --- Time functions --- #

def time_ns():
    # Fallback to non-ns time functions on <= Python 3.6
    try:
        return time.time_ns()
    except AttributeError:
        return int(time.time() * NS_IN_S)


def monotonic_ns():
    # Fallback to non-ns time functions on <= Python 3.6
    try:
        return time.monotonic_ns()
    except AttributeError:
        return int(time.monotonic() * NS_IN_S)


START_TIME = monotonic_ns()


def start_time_offset(n_digits=3):
    return round((monotonic_ns() - START_TIME) / NS_IN_S, n_digits)


# --- General utility functions --- #

def is_iterable(obj):
    return (isinstance(obj, collections.abc.Iterable)
            and not isinstance(obj, (str, bytes)))


def get_full_class_name(obj):
    try:
        return ".".join([type(obj).__module__, type(obj).__qualname__])
    except AttributeError:
        return type(obj)


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


def get_nested_attr(obj, attrs):
    attrs = attrs.split(".")
    for attr in attrs:
        obj = getattr(obj, attr)
    return obj


def get_inner_dict(obj, keys):
    inner_dict = obj
    for key in keys:
        inner_dict = inner_dict[key]
    return inner_dict


def get_all_attribute_values_recursive(
        objects, attr_get, attr_recurse):
    all_attribute_values = []
    for obj in objects:
        # Get attribute value on this level
        attr_value = getattr(obj, attr_get, None)
        if attr_value is not None:
            all_attribute_values.append(attr_value)

        # Get attribute values for subobjects
        subobjects = getattr(obj, attr_recurse, None)
        if subobjects:
            subobject_attr_values = get_all_attribute_values_recursive(
                subobjects, attr_get=attr_get, attr_recurse=attr_recurse)
            if subobject_attr_values:
                all_attribute_values += subobject_attr_values

    return all_attribute_values


def get_actual_username():
    try:
        username = os.environ["SUDO_USER"]
        if username:
            return username
    except KeyError:
        pass
    return getpass.getuser()


def convert_path(path):
    path = Path(
        str(path).replace("~", "~" + os.getenv("SUDO_USER", ""))).expanduser()
    return path


# --- System path utilities --- #

def get_system_path(systempath_config, allow_default=True):
    default_system = systempath_config["default_system"]
    system_paths = systempath_config["system_paths"]
    system_path_override = systempath_config["system_path_override"]

    if system_path_override:
        return system_path_override

    if (default_system == SYSTEM_NAME_DEFAULT
            and not system_paths.get(default_system, None)):
        if allow_default:
            return Path()
        raise RuntimeError(f"System still set to default ({default_system})")

    if not system_paths:
        raise RuntimeError("No system paths configured; no override set")

    if not default_system:
        raise RuntimeError("No system name configured; no override set")

    try:
        system_path = system_paths[default_system]
    except KeyError:
        raise KeyError(f"System {default_system} not in {system_paths!r}")

    return convert_path(system_path)


def validate_system_path(system_path, metadata_handler, logger=None):
    if logger is None:
        logger = logging.getLogger()
    if not system_path or system_path == Path():
        logger.error(
            "System path %r is empty", system_path)
        return False

    system_path = convert_path(system_path)
    if not Path(system_path).exists():
        logger.error(
            "No system config directory found at system path %r",
            system_path.as_posix())
        return False

    metadata_path = system_path / (
        metadata_handler.config_levels[LEVEL_NAME_SYSTEM].path.name)
    if not convert_path(metadata_path).exists():
        logger.error(
            "No system metadata found at system path %r",
            system_path.as_posix())
        return False

    return True


def check_system_version(metadata, logger):
    issue_found = False
    for key_name, long_name, func in [
            ("brokkr_version_min", "greater than", operator.gt),
            ("brokkr_version_max", "less than", operator.le),
                ]:
        if metadata[key_name] and func(
                packaging.version.parse(metadata[key_name]),
                packaging.version.parse(brokkr.__version__)):
            logger(
                "%s supported Brokkr version %s of system %s "
                "is %s current Brokkr version %s",
                key_name.split("_")[-1].title(),
                metadata[key_name],
                metadata["name"],
                long_name,
                brokkr.__version__,
                )
            issue_found = True
    return issue_found


# --- Common utility mixins and decorators --- #

class AutoReprMixin:
    def __repr__(self):
        argument_list = ", ".join(
            [f"{key}={value!r}" for key, value in self.__dict__.items()])
        return f"{type(self).__name__}({argument_list})"


# --- Run periodic loop decorator --- #

def generate_quit_handler(exit_event, logger=None):
    if logger is None:
        logger = logging.getLogger(__name__)

    def _quit_handler(signo, _frame):
        """Signal handler that prints a message and sets an event."""
        if logger:
            logger.warning("Interrupted by signal %s; terminating.", signo)
        exit_event.set()
    return _quit_handler


def set_signal_handler(signal_handler, signals=SIGNALS_SET):
    """Helper function that sets a signal handler for the given signals."""
    for signal_type in signals:
        try:
            signal.signal(getattr(signal, signal_type), signal_handler)
        except AttributeError:  # Windows doesn't have SIGHUP
            continue


def _pass_func():
    pass


def run_periodic(
        func=None,
        period_s=0,
        exit_event=None,
        outer_exit_event=None,
        logger=None,
        ):
    """Decorator to run a function at a periodic interval w/signal handling."""
    if func is None:
        func = _pass_func
    if exit_event is None:
        exit_event = multiprocessing.Event()
    if outer_exit_event is None:
        outer_exit_event = exit_event
    if logger is None:
        logger = logging.getLogger(__name__)

    @functools.wraps(func)
    def _run_periodic(*args, **kwargs):
        # Set up quit signal handler
        if logger:
            logger.debug("Setting up signal handlers in periodic loop...")
        set_signal_handler(generate_quit_handler(exit_event, logger=logger))

        # Mainloop to run at intervals
        while not outer_exit_event.is_set():
            func(*args, **kwargs)

            if period_s <= 0:
                continue
            next_time = (
                monotonic_ns() + int(period_s * NS_IN_S)
                - (monotonic_ns() - START_TIME)
                % int(period_s * NS_IN_S))
            while not exit_event.is_set() and monotonic_ns() < next_time:
                time.sleep(max(0, min(
                    [SLEEP_TICK_S, (next_time - monotonic_ns()) / NS_IN_S])))

    return _run_periodic
