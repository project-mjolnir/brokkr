"""
Setup and configuration commands and utilities for Brokkr.
"""

# Standard library imports
import logging
from pathlib import Path

# Local imports
from brokkr.constants import (
    CONFIG_NAME_SYSTEMPATH,
    CONFIG_NAME_UNIT,
    CONFIG_PATH_LOCAL,
    LEVEL_NAME_DEFAULTS,
    LEVEL_NAME_LOCAL,
    )
import brokkr.config.systempathhandler
import brokkr.config.handlers
import brokkr.utils.log


ALL_RESET = "all"
DEFAULT_CONFIG_LEVEL = "local"


def _write_config_file_wrapper(config_name, config_data,
                               config_level=DEFAULT_CONFIG_LEVEL):
    logging.debug("Setting up %s config with data: %r",
                  config_name, config_data)
    config_handler = brokkr.config.handlers.ALL_CONFIG_HANDLERS[config_name]
    config_source = config_handler.config_levels[config_level]
    config_source.write_config(config_data)
    logging.info("%s config file updated in %r", config_name.title(),
                 config_source.path.as_posix())


@brokkr.utils.log.basic_logging
def configure_init():
    config_handlers = brokkr.config.handlers.ALL_CONFIG_HANDLERS
    for config_name, handler in config_handlers.items():
        logging.debug("Initializing %s config...", config_name)
        handler.read_configs()
    logging.info("Config files installed to %r", CONFIG_PATH_LOCAL.as_posix())


@brokkr.utils.log.basic_logging
def configure_reset(reset_names=ALL_RESET, reset_levels=ALL_RESET,
                    include_systempath=None):
    # Include systempath config in configs to reset only if explictly specified
    if include_systempath is None:
        include_systempath = (
            reset_names != ALL_RESET
            and CONFIG_NAME_SYSTEMPATH in reset_names)
    if include_systempath:
        config_handlers = brokkr.config.handlers.ALL_CONFIG_HANDLERS
    else:
        config_handlers = brokkr.config.handlers.CONFIG_HANDLERS

    # Ensure value of all is handled properly
    reset_names = ALL_RESET if reset_names[0] == ALL_RESET else reset_names
    reset_levels = ALL_RESET if reset_levels[0] == ALL_RESET else reset_levels

    # Reset each specified config name and level
    for config_name, handler in config_handlers.items():
        if reset_names == ALL_RESET or config_name in reset_names:
            for level_name, level_source in handler.config_levels.items():
                if reset_levels == ALL_RESET or level_name in reset_levels:
                    if not getattr(level_source, "preset", True):
                        logging.debug("Resetting %s configuration for %s",
                                      level_name, config_name)
                        level_source.write_config()

    logging.info("Reset %s configuration for %s", reset_levels, reset_names)


@brokkr.utils.log.basic_logging
def configure_unit(number, network_interface, site_description=""):
    unit_config_data = {
        "number": number,
        "network_interface": network_interface,
        "site_description": site_description,
        }
    _write_config_file_wrapper(
        CONFIG_NAME_UNIT, unit_config_data)
    return unit_config_data


def _deregister_systempath(system_alias, systempath_config, skip_verify=False):
    if systempath_config["default_system"] == system_alias:
        systempath_config["default_system"] = ""
        logging.warning(
            "Deregistering default system %s; ensure you set another",
            system_alias)
    try:
        del systempath_config["system_paths"][system_alias]
        logging.info("System %s deregistered", system_alias)
    except KeyError:
        if not skip_verify:
            logging.error("System %s not registered in system list %r",
                          system_alias,
                          set(systempath_config["system_paths"].keys()))
            return systempath_config
        logging.info("System %s not registered in system list %r",
                     system_alias,
                     set(systempath_config["system_paths"].keys()))

    return systempath_config


def _configure_system(
        system_alias, system_path=None,
        set_default=None, reset=False, skip_verify=False):
    # pylint: disable=import-outside-toplevel, too-many-branches
    from brokkr.config.systempath import SYSTEMPATH_CONFIGS
    config_handler_systempath = (
        brokkr.config.systempathhandler.CONFIG_HANDLER_SYSTEMPATH)
    config_levels_current = {LEVEL_NAME_DEFAULTS, LEVEL_NAME_LOCAL}
    if reset:
        config_levels_new = {LEVEL_NAME_DEFAULTS}
        logging.info("Reset systempath configuration")
    else:
        config_levels_new = config_levels_current
    current_config, systempath_config = tuple(
        (config_handler_systempath.render_config(
            {key: value for key, value in SYSTEMPATH_CONFIGS.items()
             if key in config_levels})
         for config_levels in (config_levels_current, config_levels_new)))

    # Delete system path entry if a falsy value is passed for it
    if system_path in {"", " ", False}:
        logging.debug("Deregistering system %s", system_alias)
        systempath_config = _deregister_systempath(
            system_alias, systempath_config, skip_verify=skip_verify)
    else:
        if set_default is None and system_alias:
            set_default = not systempath_config["default_system"]
            logging.debug("Set default not passed, assuming %s", set_default)
        if system_path is not None:
            if not skip_verify:
                logging.debug("Verifying system path %r", system_path)
                config_handler_metadata = (
                    brokkr.config.handlers.CONFIG_HANDLER_METADATA)
                system_path_valid = brokkr.utils.misc.validate_system_path(
                    system_path=system_path,
                    metadata_handler=config_handler_metadata,
                    )
                if not system_path_valid:
                    logging.error("System path %r invalid; terminating. "
                                  "Use --skip-verify to skip this check.",
                                  system_path)
                    return systempath_config
                logging.debug("System path valid")
            else:
                logging.debug("Skipping verification of system path %s",
                              system_path)
            logging.info("Setting system path for system %s", system_alias)
            systempath_config["system_paths"][system_alias] = (
                Path(system_path).as_posix())
        if set_default:
            logging.debug("Checking that system is registered")
            try:
                # pylint: disable=pointless-statement
                systempath_config["system_paths"][system_alias]
                logging.debug("System is registered")
            except KeyError:
                if not skip_verify:
                    logging.error(
                        "System %s not registered in system list %r",
                        system_alias,
                        set(systempath_config["system_paths"].keys()))
                    return systempath_config
                logging.info(
                    "System %s not registered in system list %r",
                    system_alias,
                    set(systempath_config["system_paths"].keys()))
            systempath_config["default_system"] = system_alias
            logging.info("Set default to system %s", system_alias)

    if systempath_config != current_config:
        logging.debug("Changes detected in config, writing output")
        _write_config_file_wrapper(
            CONFIG_NAME_SYSTEMPATH, systempath_config)
    else:
        logging.debug("No changes to write")
    return systempath_config


@brokkr.utils.log.basic_logging
def configure_system(
        system_name=None, system_config_path=None, default=None,
        reset=False, skip_verify=False):
    # pylint: disable=import-outside-toplevel
    if reset or (system_name is not None and (system_config_path is not None
                                              or default)):
        logging.debug("Setting system data")
        systempath_config = _configure_system(
            system_name, system_config_path, set_default=default,
            reset=reset, skip_verify=skip_verify)
        return systempath_config

    logging.debug("Printing system data")
    from brokkr.config.systempath import SYSTEMPATH_CONFIGS
    if len(SYSTEMPATH_CONFIGS[LEVEL_NAME_LOCAL]) <= 1:
        print("No system paths configured.")
        logging.debug("Full configs: %r", SYSTEMPATH_CONFIGS)
        return SYSTEMPATH_CONFIGS[LEVEL_NAME_LOCAL]
    config_handler_systempath = (
        brokkr.config.systempathhandler.CONFIG_HANDLER_SYSTEMPATH)
    systempath_config = config_handler_systempath.render_config(
        {key: value for key, value in SYSTEMPATH_CONFIGS.items()
         if key in {LEVEL_NAME_DEFAULTS, LEVEL_NAME_LOCAL}})
    logging.debug("Got systempath config %r", systempath_config)

    default_system = systempath_config["default_system"]
    if system_name is None:
        if default:
            if default_system:
                path = systempath_config["system_paths"][default_system]
                print(f"Default system: {default_system}; path: {path}")
            else:
                print("No default system set")
        else:
            print("Registered system paths:")
            for name, path in systempath_config["system_paths"].items():
                print(f"{name}: {path!r}"
                      f"{' (default)' if name == default_system else ''}")
    else:
        try:
            path = systempath_config["system_paths"][system_name]
            print(f"System path found for system {system_name}: {path} "
                  f"(Default: {system_name == default_system})")
        except KeyError:
            print(f"System path {system_name} not found")

    return systempath_config
