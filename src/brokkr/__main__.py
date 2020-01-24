#!/usr/bin/env python3
"""
Main-level command handling routine for running brokkr on the command line.
"""

# Standard library imports
import argparse


def generate_argparser_main():
    parser_main = argparse.ArgumentParser(
        description="Client to monitor and manage remote IoT sensors.",
        argument_default=argparse.SUPPRESS)
    parser_main.add_argument(
        "--version", action="store_true",
        help="If passed, will print the version and exit")
    subparsers = parser_main.add_subparsers(
        title="Subcommands", help="Brokkr subcommand to execute",
        metavar="Subcommand", dest="subcommand_name")

    # Parser for the version subcommand
    subparsers.add_parser(
        "version", help="Print Brokkr's version, and then exit")

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

    script_parsers = []

    # Parser for the install-all subcommand
    parser_install_all = subparsers.add_parser(
        "install-all", help="Install all elements needed to run Brokkr")
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
        "--platform", choices=("linux", ),
        help="Manually override automatic platform detection")
    script_parsers.append(parser_install_autossh)

    # Parser for the install-config subcommand
    parser_install_config = subparsers.add_parser(
        "install-config", help="Install Brokkr's config files for the system")
    script_parsers.append(parser_install_config)

    # Parser for the install-dialout subcommand
    parser_install_dialout = subparsers.add_parser(
        "install-dialout", help="Enable serial port access for the user")
    script_parsers.append(parser_install_dialout)

    # Parser for the install-firewall subcommand
    parser_install_firewall = subparsers.add_parser(
        "install-firewall", help="Enable needed ports through the firewall")
    script_parsers.append(parser_install_firewall)

    # Parser for the install-service subcommand
    parser_install_service = subparsers.add_parser(
        "install-service", help="Install Brokkr as a systemd service (Linux)",
        argument_default=argparse.SUPPRESS)
    parser_install_service.add_argument(
        "--platform", choices=("linux", ),
        help="Manually override automatic platform detection")
    script_parsers.append(parser_install_service)

    # Parser for the configure-reset subcommand
    parser_configure_reset = subparsers.add_parser(
        "configure-reset", help="Reset brokkr-managed configuration files")
    parser_configure_reset.add_argument(
        "--config-names", nargs="?", default="all",
        choices=("all", "main", "log", "unit"),
        help="Which config names to reset; by default, resets all of them")
    parser_configure_reset.add_argument(
        "--config-types", nargs="?", default="all",
        choices=("all", "remote", "local"),
        help="Which config types to reset; by default, resets all of them")
    script_parsers.append(parser_configure_reset)

    # Parser for the configure-unit subcommand
    parser_configure_unit = subparsers.add_parser(
        "configure-unit", help="Set up per-unit configuration")
    parser_configure_unit.add_argument(
        "number", type=int,
        help="The unit number of this particular Brokkr client")
    parser_configure_unit.add_argument(
        "network_interface",
        help="The network interface for uplink on particular Brokkr client")
    parser_configure_unit.add_argument(
        "--description", default="",
        help="An optional description of this particular Brokkr client")
    script_parsers.append(parser_configure_unit)

    # Add verbose parameter to all script-like subcommands
    for script_parser in script_parsers:
        script_parser.add_argument(
            "-v", "--verbose", action="store_true",
            help="If passed, will print details of the exact actions executed")

    return parser_main


def main():
    parser_main = generate_argparser_main()
    parsed_args = parser_main.parse_args()
    subcommand = getattr(parsed_args, "subcommand_name", None)
    subcommand = (subcommand.replace("-", "_")
                  if subcommand is not None else subcommand)

    try:
        delattr(parsed_args, "subcommand_name")
    except Exception:  # Ignore any problem deleting the arg
        pass

    if getattr(parsed_args, "version", None) or subcommand == "version":
        import brokkr
        print("Brokkr version " + str(brokkr.__version__))
    elif subcommand == "help":
        parser_main.print_help()
    elif subcommand == "start":
        import brokkr.start
        brokkr.start.start_brokkr(**vars(parsed_args))
    elif subcommand == "monitor":
        import brokkr.start
        brokkr.start.start_monitoring(**vars(parsed_args))
    elif subcommand.startswith("install_"):
        import brokkr.utils.install
        getattr(brokkr.utils.install, subcommand)(**vars(parsed_args))
    elif subcommand.startswith("configure_"):
        import brokkr.utils.configure
        getattr(brokkr.utils.configure, subcommand)(**vars(parsed_args))
    else:
        parser_main.print_usage()


if __name__ == "__main__":
    main()
