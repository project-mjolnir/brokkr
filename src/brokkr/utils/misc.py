"""
General utility functions for Brokkr.
"""

# Standard library imports
import collections.abc
import functools
import getpass
import logging
import os
from pathlib import Path
import signal
import threading
import time

# Local imports
from brokkr.constants import SLEEP_TICK_S, LEVEL_NAME_SYSTEM


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


def convert_path(path):
    path = Path(
        str(path).replace("~", "~" + os.getenv("SUDO_USER", ""))).expanduser()
    return path


# --- System path utilities --- #

def get_system_path(systempath_config, errors="ignore"):
    # Replace errors with enum
    error_modes = {"raise", "ignore"}
    if errors not in error_modes:
        raise ValueError(f"Errors must be one of {error_modes}, not {errors}")
    default_system = systempath_config["default_system"]
    system_paths = systempath_config["system_paths"]
    system_path_override = systempath_config["system_path_override"]

    if system_path_override:
        return system_path_override

    if not system_paths:
        if errors == "raise":
            raise RuntimeError("No system paths configured; no override set")
        return Path()

    if not default_system:
        if errors == "raise":
            raise RuntimeError("No system name configured; no override set")
        return Path()

    try:
        system_path = system_paths[default_system]
    except KeyError:
        if errors == "raise":
            raise KeyError(f"System {default_system} not in {system_paths!r}")
        return Path()

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
        exit_event = threading.Event()
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
