"""
General utility functions for Brokkr.
"""

# Standard library imports
import collections.abc
import functools
import getpass
import logging
import os
import signal
import threading
import time


# Constants for run periodic
PERIOD_S_DEFAULT = 1
SIGNALS_SET = ["SIG" + signame for signame in {"TERM", "HUP", "INT", "BREAK"}]
SLEEP_TICK_S = 0.5


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


# --- Run periodic loop decorator --- #

def generate_quit_handler(exit_event, logger=None):
    if logger is None:
        logger = logging.getLogger(__name__)

    def _quit_handler(signo, _frame):
        """Signal handler that prints a message and sets an event."""
        logger.warning("\nInterrupted by signal %s; terminating.", signo)
        exit_event.set()
    return _quit_handler


def set_signal_handler(signal_handler, signals=SIGNALS_SET):
    """Helper function that sets a signal handler for the given signals."""
    for signal_type in signals:
        try:
            signal.signal(getattr(signal, signal_type), signal_handler)
        except AttributeError:  # Windows doesn't have SIGHUP
            continue


def run_periodic(
        func, period_s=PERIOD_S_DEFAULT, exit_event=None, logger=None):
    """Decorator to run a function at a periodic interval w/signal handling."""
    exit_event = threading.Event() if exit_event is None else exit_event

    @functools.wraps(func)
    def _run_periodic(*args, **kwargs):
        # Set up quit signal handler
        set_signal_handler(generate_quit_handler(exit_event, logger=logger))

        # Mainloop to run at intervals
        while not exit_event.is_set():
            func(*args, **kwargs)

            if period_s <= 0:
                continue
            next_time = (
                monotonic_ns() + period_s * 1e9 - (monotonic_ns() - START_TIME)
                % (period_s * 1e9))
            while not exit_event.is_set() and monotonic_ns() < next_time:
                exit_event.wait(max(0, min(
                    [SLEEP_TICK_S, (next_time - monotonic_ns()) / 1e9])))
        exit_event.clear()

    return _run_periodic
