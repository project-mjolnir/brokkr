"""
Setup and installation utilities for Brokkr.
"""

# Standard library imports
import logging
import subprocess
import sys

# Local imports
import brokkr.config.log
import brokkr.config.main
import brokkr.config.service
import brokkr.utils.misc


PORTS_TO_OPEN = (("8084", "udp"), )

FIREWALL_COMMANDS_LINUX = {
    "firewalld": lambda port, proto: (
        "firewall-cmd", f"--add-port={port}/{proto}"),
    "UFW": lambda port, proto: ("ufw", "allow", f"{port}/{proto}"),
    "NFTables": lambda port, proto: ("nft", "add", "rule", "inet", "filter",
                                     "input", proto, "dport", port, "accept"),
    "IPTables": lambda port, proto: ("iptables", "-A", "INPUT", "-p", proto,
                                     "--dport", port, "-j", "ACCEPT"),
    }

FIREWALL_COMMANDS_LINUX_AFTER = {
    "firewalld": ("firewall-cmd", "--runtime-to-permanent"),
    }

FIREWALL_COMMANDS_WINDOWS = {
    "netsh": lambda port, proto: (
        "netsh", "advfirewall", "firewall", "add", "rule",
        f"name=Open {proto} port {port}", "dir=in", "action=allow",
        f"protocol={proto}", f"localport={port}",
        ),
    }


def log_setup(verbose=None):
    if verbose is None:
        logging_level = 99
    elif verbose:
        logging_level = "DEBUG"
    else:
        logging_level = "INFO"
    logging.basicConfig(stream=sys.stdout, level=logging_level)


def install_config_files(verbose=None):
    log_setup(verbose)

    logging.debug("Installing log config...")
    brokkr.config.log.CONFIG_HANDLER.read_configs()
    logging.debug("Installing main config...")
    brokkr.config.main.CONFIG_HANDLER.read_configs()
    logging.info("Config files installed to %s",
                 brokkr.config.main.CONFIG_HANDLER.config_dir)


def install_dialout(verbose=None):
    log_setup(verbose)

    logging.debug("Enabling serial port access for user %s...",
                  brokkr.utils.misc.get_actual_username())
    subprocess.run(("usermod", "-a", "-G", "dialout",
                    brokkr.utils.misc.get_actual_username()),
                   timeout=5, check=True)
    logging.info("Enabled serial port access for user %s",
                 brokkr.utils.misc.get_actual_username())


def install_firewall_ports(ports_to_open=PORTS_TO_OPEN, verbose=None):
    log_setup(verbose)
    logging.debug("Opening firewall ports: %s", ports_to_open)

    if sys.platform.startswith("linux"):
        firewall_commands = FIREWALL_COMMANDS_LINUX
    elif sys.platform.startswith("win"):
        firewall_commands = FIREWALL_COMMANDS_WINDOWS
    else:
        raise ValueError(
            "Firewall port enabling only currently supported on "
            f"Linux and Windows, not on {sys.platform}.")

    for name, command in firewall_commands.items():
        logging.debug(f"Trying {name}...")
        for port, proto in ports_to_open:
            try:
                subprocess.run(command(port, proto), timeout=5, check=False)
            except FileNotFoundError:
                logging.debug(f"{name} not found on system.")
            except Exception:
                logging.info(f"Error running {name} ignored.")
                logging.debug(f"Details:", exc_info=True)

    if sys.platform.startswith("linux"):
        for name, command in FIREWALL_COMMANDS_LINUX_AFTER.items():
            logging.debug(f"Running followup command for {name}...")
            try:
                subprocess.run(command, timeout=5, check=False)
            except FileNotFoundError:
                logging.debug(f"{name} not found on system.")
            except Exception:
                logging.info(f"Error running followup {name} ignored.")
                logging.debug(f"Details:", exc_info=True)

    logging.info("Attempted to open firewall ports: %s", ports_to_open)


def install_service(platform=None, output_path=None, verbose=None):
    log_setup(verbose)

    logging.debug("Installing Brokkr service...")
    platform_config = brokkr.config.service.get_platform_config(platform)
    logging.debug("Using platform config settings: %s", platform_config)
    logging.debug("Generating service configuration file...")
    service_config = brokkr.config.service.generate_service_config(platform)
    logging.debug("Writing service configuration file to %s",
                  output_path if output_path else platform_config.install_path)
    output_path = brokkr.config.service.write_service_config(
        service_config, platform, output_path)

    logging.debug("Reloading systemd daemon...")
    subprocess.run(("systemctl", "daemon-reload"), timeout=5, check=True)
    logging.debug("Disabling chrony (if present)...")
    subprocess.run(("systemctl", "disable", "chronyd"), timeout=5, check=False)
    logging.debug("Disabling ntpd (if present)...")
    subprocess.run(("systemctl", "disable", "ntpd"), timeout=5, check=False)
    logging.debug("Enabling systemd-timesyncd...")
    subprocess.run(("systemctl", "enable", "systemd-timesyncd"),
                   timeout=5, check=True)
    logging.debug("Enabling sshd...")
    subprocess.run(("systemctl", "enable", "sshd"), timeout=5, check=True)

    logging.debug("Enabling Brokkr service...")
    subprocess.run(("systemctl", "enable", "brokkr"), timeout=5, check=True)
    logging.info("Successfully installed Brokkr service to %s", output_path)
    return service_config


def install_all(no_install_service=False, verbose=None):
    log_setup(verbose)
    logging.debug("Installing all Brokkr external componenets...")

    install_config_files()

    if sys.platform.startswith("linux") or sys.platform.startswith("win"):
        install_firewall_ports()

    if sys.platform.startswith("linux"):
        install_dialout()
        if not no_install_service:
            install_service()


def reset_config(config_type="all", verbose=None):
    log_setup(verbose)
    logging.debug("Resetting Brokkr configuration: %s", config_type)

    for config, handler in (("log", brokkr.config.log.CONFIG_HANDLER),
                            ("main", brokkr.config.main.CONFIG_HANDLER)):
        if config_type in ("all", config):
            logging.debug(f"Restting {config} config...")
            for config_subtype in handler.config_types:
                handler.generate_config(config_subtype)

    logging.info("Reset Brokker configuration: %s", config_type)
