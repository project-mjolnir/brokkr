"""
Initialization and functionality for Brokkr's error log handlers.
"""

# Standard library imports
import copy
import functools
import logging
import os
import sys
import time

# Local imports
from brokkr.config.constants import PACKAGE_NAME, OUTPUT_PATH_DEFAULT
import brokkr.utils.misc


MAX_VERBOSE = 3
MIN_VERBOSE = -3
LOG_LEVEL = {
    -3: 99,
    -2: logging.CRITICAL,
    -1: logging.ERROR,
    0: logging.WARNING,
    1: logging.INFO,
    2: logging.DEBUG,
    3: 2,
    }

LOG_FORMAT_BASIC = "{message}"
LOG_FORMAT_FANCY = "{levelname} | {name} | {message}"


def log_details(logger, error=None, **objs_tolog):
    if isinstance(logger, logging.Logger):
        logger = logging.info
    if error is None:
        # Add stacklevel in Python 3.8
        logger("Error details:", exc_info=1)
    elif error:
        logger("Error details: %r", error.__dict__)
    for obj_name, obj_value in objs_tolog.items():
        logger("%s details: %r", obj_name.capitalize(), obj_value.__dict__)


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
    if script_mode and log_level >= logging.DEBUG:
        log_args["format"] = LOG_FORMAT_BASIC
    else:
        log_args["format"] = LOG_FORMAT_FANCY
    if script_mode or log_level < logging.DEBUG:
        log_args["level"] = log_level

    # Initialize logging
    logging.basicConfig(**log_args)
    logger = logging.getLogger(PACKAGE_NAME)
    if not script_mode and log_level >= logging.DEBUG:
        logger.setLevel(log_level)
    return logger


def basic_logging(func):
    @functools.wraps(func)
    def _basic_logging(*args, verbose=0, quiet=0, **kwargs):
        setup_basic_logging(verbose=verbose, quiet=quiet, script_mode=True)
        value = func(*args, **kwargs)
        return value
    return _basic_logging


def setup_log_levels(log_config, file_level=None, console_level=None):
    file_level = (file_level.upper()
                  if isinstance(file_level, str) else file_level)
    console_level = (console_level.upper()
                     if isinstance(console_level, str) else console_level)
    for handler, level in (("file", file_level), ("console", console_level)):
        if level:
            log_config["handlers"][handler]["level"] = level
            if handler not in log_config["root"]["handlers"]:
                log_config["root"]["handlers"].append(handler)
    levels_tocheck = (level for level in (
        file_level, console_level, log_config["root"]["level"]
        ) if (level == 0 or level))
    level_min = min((int(getattr(logging, str(level_name), level_name))
                     for level_name in levels_tocheck))
    log_config["root"]["level"] = level_min
    return log_config


def setup_log_handler_paths(
        log_config,
        output_path=OUTPUT_PATH_DEFAULT,
        **filename_args,
        ):
    for log_handler in log_config["handlers"].values():
        if log_handler.get("filename", None):
            log_filename = brokkr.utils.misc.convert_path(
                log_handler["filename"].format(**filename_args))
            if not log_filename.is_absolute() and output_path:
                log_filename = output_path / log_filename
            os.makedirs(log_filename.parent, exist_ok=True)
            log_handler["filename"] = log_filename

    return log_config


def setup_full_log_config(
        log_config,
        log_level_file=None,
        log_level_console=None,
        output_path=OUTPUT_PATH_DEFAULT,
        **filename_args,
        ):
    # Load and set logging config
    logging.Formatter.converter = time.gmtime
    log_config = copy.deepcopy(log_config)

    log_config = setup_log_handler_paths(
        log_config, output_path, **filename_args)

    if any((log_level_file, log_level_console)):
        log_config = setup_log_levels(
            log_config, log_level_file, log_level_console)

    logging.config.dictConfig(log_config)
    return log_config
