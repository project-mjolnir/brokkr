"""
General utility functions for Brokkr.
"""

import time


def time_ns():
    # Fallback to non-ns time functions on Python <=3.6
    try:
        return time.time_ns()
    except AttributeError:
        return (int(time.time()) * 1e9)


def monotonic_ns():
    # Fallback to non-ns time functions on Python <=3.6
    try:
        return time.monotonic_ns()
    except AttributeError:
        return (int(time.monotonic()) * 1e9)
