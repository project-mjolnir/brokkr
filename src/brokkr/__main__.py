#!/usr/bin/env python3
"""
Main-level command handling routine for running brokkr on the command line.
"""

# Standard library modules
import argparse
from pathlib import Path


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
        "--output-path", type=Path,
        help="A custom filename and path to which to save the monitor data")
    parser_start.add_argument(
        "--interval", type=int, dest="monitor_interval",
        help="Interval between status checks, in s")
    parser_start.add_argument(
        "--log-level-file", type=str,
        help="Level of messages to log to disk")
    parser_start.add_argument(
        "--log-level-console", type=str,
        help="Level of messages to log to the console")
    parser_start.add_argument(
        "-v", "--verbose", action="store_true",
        help="If passed, will print the data logged to the console")

    # Parser for the install-all subcommand
    parser_install_all = subparsers.add_parser(
        "install-all", help="Install all elements needed to run Brokkr")
    parser_install_all.add_argument(
        "--no-install-services", action="store_true",
        help="If passed, will not install the Brokkr and AutoSSH services")
    parser_install_all.add_argument(
        "-v", "--verbose", action="store_true",
        help="If passed, will print details of the exact actions executed")

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
    parser_install_autossh.add_argument(
        "-v", "--verbose", action="store_true",
        help="If passed, will print details of the exact actions executed")

    # Parser for the install-config subcommand
    parser_install_config = subparsers.add_parser(
        "install-config", help="Install Brokkr's config files for the system")
    parser_install_config.add_argument(
        "-v", "--verbose", action="store_true",
        help="If passed, will print details of the exact actions executed")

    # Parser for the install-dialout subcommand
    parser_install_dialout = subparsers.add_parser(
        "install-dialout", help="Enable serial port access for the user")
    parser_install_dialout.add_argument(
        "-v", "--verbose", action="store_true",
        help="If passed, will print details of the exact actions executed")

    # Parser for the install-firewall subcommand
    parser_install_firewall = subparsers.add_parser(
        "install-firewall", help="Enable needed ports through the firewall")
    parser_install_firewall.add_argument(
        "-v", "--verbose", action="store_true",
        help="If passed, will print details of the exact actions executed")

    # Parser for the install-service subcommand
    parser_install_service = subparsers.add_parser(
        "install-service", help="Install Brokkr as a systemd service (Linux)",
        argument_default=argparse.SUPPRESS)
    parser_install_service.add_argument(
        "--platform", choices=("linux", ),
        help="Manually override automatic platform detection")
    parser_install_service.add_argument(
        "-v", "--verbose", action="store_true",
        help="If passed, will print details of the exact actions executed")

    # Parser for the reset subcommand
    parser_reset = subparsers.add_parser(
        "reset", help="Reset brokkr logging and main configuration files")
    parser_reset.add_argument(
        "config_type", nargs="?", default="all",
        choices=("all", "main", "log"),
        help="Which config type to reset. By default, resets all of them")
    parser_reset.add_argument(
        "-v", "--verbose", action="store_true",
        help="If passed, will print details of the exact actions executed")

    return parser_main


def main():
    parser_main = generate_argparser_main()
    parsed_args = parser_main.parse_args()
    subcommand = getattr(parsed_args, "subcommand_name", None)
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
        import brokkr.startup
        brokkr.startup.start_brokkr(**vars(parsed_args))
    elif subcommand == "install-all":
        import brokkr.utils.install
        brokkr.utils.install.install_all(**vars(parsed_args))
    elif subcommand == "install-autossh":
        import brokkr.utils.install
        brokkr.utils.install.install_autossh(**vars(parsed_args))
    elif subcommand == "install-config":
        import brokkr.utils.install
        brokkr.utils.install.install_config_files(**vars(parsed_args))
    elif subcommand == "install-dialout":
        import brokkr.utils.install
        brokkr.utils.install.install_dialout(**vars(parsed_args))
    elif subcommand == "install-firewall":
        import brokkr.utils.install
        brokkr.utils.install.install_firewall_ports(**vars(parsed_args))
    elif subcommand == "install-service":
        import brokkr.utils.install
        brokkr.utils.install.install_brokkr_service(**vars(parsed_args))
    elif subcommand == "reset":
        import brokkr.utils.install
        brokkr.utils.install.reset_config(**vars(parsed_args))
    else:
        parser_main.print_usage()


if __name__ == "__main__":
    main()
