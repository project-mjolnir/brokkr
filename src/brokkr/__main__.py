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
        "-v", "--version", action="store_true",
        help="If passed, will print the version and exit")
    subparsers = parser_main.add_subparsers(
        title="Subcommands", help="Brokkr subcommand to execute",
        metavar="Subcommand", dest="subcommand_name")

    # Parser for the start subcommand
    parser_start = subparsers.add_parser(
        "start", help="Start the monitoring, processing and control client",
        argument_default=argparse.SUPPRESS)
    parser_start.add_argument(
        "--output_path", type=Path,
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

    # Parser for the install-service subcommand
    parser_install_service = subparsers.add_parser(
        "install-service", help="Install Brokkr as a systemd service (Linux)",
        argument_default=argparse.SUPPRESS)
    parser_install_service.add_argument(
        "--platform", choices=("linux", ),
        help="Manually override automatic platform detection")
    parser_install_service.add_argument(
        "--output_path", type=Path,
        help="A custom filename and path to which to save the service file")
    parser_install_service.add_argument(
        "-v", "--verbose", action="store_true",
        help="If passed, will print details of the exact actions executed")

    # Parser for the version subcommand
    subparsers.add_parser(
        "version", help="Print Brokkr's version, and then exit")

    # Parser for the help subcommand
    subparsers.add_parser(
        "help", help="Print help on Brokkr's command line arguments")

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
    elif subcommand == "install-service":
        import brokkr.config.service
        brokkr.config.service.install_service_config(**vars(parsed_args))
    elif subcommand == "start":
        import brokkr.startup
        brokkr.startup.start_brokkr(**vars(parsed_args))
    elif subcommand == "help":
        parser_main.print_help()
    else:
        parser_main.print_usage()


if __name__ == "__main__":
    main()
