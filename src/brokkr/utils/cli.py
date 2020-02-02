#!/usr/bin/env python3
"""
Main-level command handling routine for running brokkr on the command line.
"""

# Standard library imports
import argparse

# Local imports
import brokkr.config.base
from brokkr.config.constants import PACKAGE_NAME
import brokkr.config.handlers


VERSION_PARAM = "version"
SUBCOMMAND_PARAM = "subcommand_name"
SYSTEM_PATH_PARAM = "system_path"

ARGS_TODELETE = {VERSION_PARAM, SUBCOMMAND_PARAM, SYSTEM_PATH_PARAM}


def generate_argparser_main():
    parser_main = argparse.ArgumentParser(
        description="Client to monitor and manage remote IoT sensors.",
        argument_default=argparse.SUPPRESS)
    parser_main.add_argument(
        "--version", action="store_true", dest=VERSION_PARAM,
        help="If passed, will print the version and exit")
    subparsers = parser_main.add_subparsers(
        title="Subcommands", help="Subcommand to execute",
        metavar="Subcommand", dest=SUBCOMMAND_PARAM)

    system_path_parsers = []
    script_parsers = []

    # Parser for the version subcommand
    subparsers.add_parser(
        VERSION_PARAM, help="Print Brokkr's version, and then exit")

    # Parser for the help subcommand
    subparsers.add_parser(
        "help", help="Print help on Brokkr's command line arguments")

    # Parser for the start subcommand
    parser_start = subparsers.add_parser(
        "start", help="Start the monitoring, processing and control client",
        argument_default=argparse.SUPPRESS)
    parser_start.add_argument(
        "--log-level-file", type=str,
        help="Level of messages to log to disk")
    parser_start.add_argument(
        "--log-level-console", type=str,
        help="Level of messages to log to the console")
    system_path_parsers.append(parser_start)

    # Parser for the monitor subcommand
    parser_monitor = subparsers.add_parser(
        "monitor", help="Start just the monitoring client",
        argument_default=argparse.SUPPRESS)
    parser_monitor.add_argument(
        "--output-path", nargs="?", default=None, const=True,
        help=("Doesn't write anything if not passed; "
              "if passed without an argument, writes to the default data dir; "
              "if passed a path to a custom data dir, writes data there"))
    parser_monitor.add_argument(
        "--monitor-interval-s", type=int,
        help="Interval between status checks, in s")
    parser_monitor.add_argument(
        "-v", "--verbose", action="count", default=0,
        help=("Verbosity level; only errors by default, -v for basic info, "
              "-vv for detailed info and -vvv for debug info"))
    system_path_parsers.append(parser_monitor)

    # Parser for the install-all subcommand
    parser_install_all = subparsers.add_parser(
        "install-all", help="Install all elements needed to run the package",
        argument_default=argparse.SUPPRESS)
    parser_install_all.add_argument(
        "--no-install-services", action="store_true",
        help="If passed, will not install the Brokkr and AutoSSH services")
    script_parsers.append(parser_install_all)

    # Parser for the install-autossh subcommand
    parser_install_autossh = subparsers.add_parser(
        "install-autossh", help="Install AutoSSH as a systemd service",
        argument_default=argparse.SUPPRESS)
    parser_install_autossh.add_argument(
        "--skip-package-install", action="store_true",
        help="Don't attempt to install distro package, just service unit")
    parser_install_autossh.add_argument(
        "--platform", choices={"linux", },
        help="Manually override automatic platform detection")
    script_parsers.append(parser_install_autossh)

    # Parser for the install-config subcommand
    parser_install_config = subparsers.add_parser(
        "install-config", help="Install Brokkr's config files for the system",
        argument_default=argparse.SUPPRESS)
    script_parsers.append(parser_install_config)

    # Parser for the install-dialout subcommand
    parser_install_dialout = subparsers.add_parser(
        "install-dialout", help="Enable serial port access for the user",
        argument_default=argparse.SUPPRESS)
    script_parsers.append(parser_install_dialout)

    # Parser for the install-firewall subcommand
    parser_install_firewall = subparsers.add_parser(
        "install-firewall", help="Enable needed ports through the firewall",
        argument_default=argparse.SUPPRESS)
    script_parsers.append(parser_install_firewall)

    # Parser for the install-service subcommand
    parser_install_service = subparsers.add_parser(
        "install-service", help="Install Brokkr as a systemd service (Linux)",
        argument_default=argparse.SUPPRESS)
    parser_install_service.add_argument(
        "--platform", choices={"linux", },
        help="Manually override automatic platform detection")
    script_parsers.append(parser_install_service)

    # Parser for the install-udev subcommand
    parser_install_udev = subparsers.add_parser(
        "install-udev", help="Enable full access to USB ports via udev rules",
        argument_default=argparse.SUPPRESS)
    script_parsers.append(parser_install_udev)

    # Parser for the configure-reset subcommand
    parser_configure_reset = subparsers.add_parser(
        "configure-reset", help="Reset brokkr-managed configuration files",
        argument_default=argparse.SUPPRESS)
    parser_configure_reset.add_argument(
        "--reset-names", nargs="+",
        choices={"all", *brokkr.config.handlers.ALL_CONFIG_HANDLERS.keys()},
        help="Which config names to reset; by default, resets all of them")
    parser_configure_reset.add_argument(
        "--reset-levels", nargs="+",
        choices={"all", *brokkr.config.handlers.ALL_CONFIG_LEVEL_NAMES},
        help="Which config levels to reset; by default, resets all of them")
    parser_configure_reset.add_argument(
        "--include-system", action="store_true",
        help="Don't attempt to install distro package, just service unit")
    script_parsers.append(parser_configure_reset)

    # Parser for the configure-unit subcommand
    parser_configure_unit = subparsers.add_parser(
        "configure-unit", help="Set up per-unit configuration",
        argument_default=argparse.SUPPRESS)
    parser_configure_unit.add_argument(
        "number", type=int,
        help="The unit number of this particular Brokkr client")
    parser_configure_unit.add_argument(
        "network_interface",
        help="The network interface for uplink on particular Brokkr client")
    parser_configure_unit.add_argument(
        "--site-description", default="",
        help="An optional description of this particular Brokkr site")
    script_parsers.append(parser_configure_unit)

    # Parser for the configure-system subcommand
    parser_configure_system = subparsers.add_parser(
        "configure-system", help="Set up sensor system configuration",
        argument_default=argparse.SUPPRESS)
    parser_configure_system.add_argument(
        "system_config_path",
        help="The path to the sensor system config directory")
    script_parsers.append(parser_configure_system)

    # Add common parameters to subcommand groups
    for system_path_parser in system_path_parsers:
        system_path_parser.add_argument(
            "--system-path", dest=SYSTEM_PATH_PARAM,
            help=("Sets the directory to use to load system config data. "
                  "Override the settings in the config file and the env var."))
    for script_parser in script_parsers:
        script_parser.add_argument(
            "-v", "--verbose", action="store_true", default=None,
            help="If passed, will print details of the exact actions executed")

    return parser_main


def parse_args(sys_argv=None):
    parser_main = generate_argparser_main()
    if sys_argv is None:
        parsed_args = parser_main.parse_args()
    else:
        parsed_args = parser_main.parse_args(sys_argv)

    # Get, format and remove subcommand
    subcommand = getattr(parsed_args, SUBCOMMAND_PARAM, None)
    subcommand = (subcommand.replace("-", "_")
                  if subcommand is not None else "")
    try:
        delattr(parsed_args, SUBCOMMAND_PARAM)
    except Exception:  # Ignore any problem deleting the arg
        pass

    # Override subcomamnd with version if passed
    if getattr(parsed_args, VERSION_PARAM, None):
        subcommand = VERSION_PARAM

    # Delete unneeded individual args
    for arg_todelete in ARGS_TODELETE:
        try:
            delattr(parsed_args, arg_todelete)
        except Exception:  # Ignore any problem deleting the arg
            pass

    return subcommand, parsed_args


def dispatch_command(subcommand, parsed_args):
    if subcommand == VERSION_PARAM:
        import brokkr
        print(f"{PACKAGE_NAME.title()} version {str(brokkr.__version__)}")
    elif subcommand == "help":
        generate_argparser_main().print_help()
    elif subcommand == "start":
        import brokkr.start
        brokkr.start.start_brokkr(**parsed_args)
    elif subcommand == "monitor":
        import brokkr.start
        brokkr.start.start_monitoring(**parsed_args)
    elif subcommand.startswith("install_"):
        import brokkr.utils.install
        getattr(brokkr.utils.install, subcommand)(**parsed_args)
    elif subcommand.startswith("configure_"):
        import brokkr.utils.configure
        getattr(brokkr.utils.configure, subcommand)(**parsed_args)
    else:
        generate_argparser_main().print_usage()


def main():
    subcommand, parsed_args = parse_args()
    dispatch_command(subcommand, vars(parsed_args))


if __name__ == "__main__":
    main()
