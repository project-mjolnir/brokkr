"""
Installation commands and utilities for Brokkr.
"""

# Standard library imports
import logging
import subprocess
import sys

# Third party imports
import serviceinstaller

# Local imports
import brokkr.config.autossh
import brokkr.config.log
import brokkr.config.main
import brokkr.config.service
import brokkr.utils.misc
from brokkr.utils.misc import basic_logging


DISTRO_INSTALL_COMMANDS = (
    lambda package_name: ("apt-get", "-y", "install", package_name),
    lambda package_name: ("dnf", "-y", "install", package_name),
    lambda package_name: ("yum", "-y", "install", package_name),
    lambda package_name: ("pacman", "-S", "--noconfirm", package_name),
    )

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


def install_distro_package(package_name):
    logging.debug("Installing %s...", package_name)
    for command in DISTRO_INSTALL_COMMANDS:
        logging.debug("Trying %s...", command("")[0])
        try:
            subprocess.run(command(package_name), check=True)
        except Exception:
            logging.debug("%s failed, skipping...", command("")[0])
        else:
            logging.debug("%s succeeded in installing AutoSSH", command("")[0])
            return True
    logging.error("Failed to install %s", package_name)
    return False


@basic_logging
def install_autossh(skip_package_install=False, platform=None):
    if not skip_package_install:
        install_succeeded = install_distro_package("autossh")
        if not install_succeeded:
            return install_succeeded

    serviceinstaller.install_service(
        brokkr.config.autossh.AUTOSSH_SERVICE_DEFAULTS,
        service_filename=brokkr.config.autossh.AUTOSSH_SERVICE_FILENAME,
        services_enable=brokkr.config.autossh.AUTOSSH_SERVICES_ENABLE,
        services_disable=brokkr.config.autossh.AUTOSSH_SERVICES_DISABLE,
        platform=platform,
        )
    return True


@basic_logging
def install_brokkr_service(platform=None):
    serviceinstaller.install_service(
        brokkr.config.service.BROKKR_SERVICE_DEFAULTS,
        service_filename=brokkr.config.service.BROKKR_SERVICE_FILENAME,
        services_enable=brokkr.config.service.BROKKR_SERVICES_ENABLE,
        services_disable=brokkr.config.service.BROKKR_SERVICES_DISABLE,
        platform=platform,
    )


@basic_logging
def install_config_files():
    logging.debug("Installing log config...")
    brokkr.config.log.CONFIG_HANDLER.read_configs()
    logging.debug("Installing main config...")
    brokkr.config.main.CONFIG_HANDLER.read_configs()
    logging.info("Config files installed to %s",
                 brokkr.config.main.CONFIG_HANDLER.config_dir)


@basic_logging
def install_dialout():
    logging.debug("Enabling serial port access for user %s...",
                  brokkr.utils.misc.get_actual_username())
    subprocess.run(("usermod", "-a", "-G", "dialout",
                    brokkr.utils.misc.get_actual_username()),
                   timeout=5, check=True)
    logging.info("Enabled serial port access for user %s",
                 brokkr.utils.misc.get_actual_username())


@basic_logging
def install_firewall_ports(ports_to_open=PORTS_TO_OPEN):
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
        logging.debug("Trying %s...", name)
        for port, proto in ports_to_open:
            try:
                subprocess.run(command(port, proto), timeout=5, check=False)
            except FileNotFoundError:
                logging.debug("%s not found on system.", name)
            except Exception:
                logging.info("Error running %s ignored.", name)
                logging.debug("Details:", exc_info=True)

    if sys.platform.startswith("linux"):
        for name, command in FIREWALL_COMMANDS_LINUX_AFTER.items():
            logging.debug("Running followup command for %s...", name)
            try:
                subprocess.run(command, timeout=5, check=False)
            except FileNotFoundError:
                logging.debug("%s not found on system.", name)
            except Exception:
                logging.info("Error running followup %s ignored.", name)
                logging.debug("Details:", exc_info=True)

    logging.info("Attempted to open firewall ports: %s", ports_to_open)


@basic_logging
def install_all(no_install_services=False):
    logging.debug("Installing all Brokkr external componenets...")

    install_config_files()

    if sys.platform.startswith("linux") or sys.platform.startswith("win"):
        install_firewall_ports()

    if sys.platform.startswith("linux"):
        install_dialout()
        if not no_install_services:
            install_autossh()
            install_brokkr_service()


@basic_logging
def reset_config(config_type="all"):
    logging.debug("Resetting Brokkr configuration: %s", config_type)

    for config, handler in (("log", brokkr.config.log.CONFIG_HANDLER),
                            ("main", brokkr.config.main.CONFIG_HANDLER)):
        if config_type in ("all", config):
            logging.debug("Restting %s config...", config)
            for config_subtype in handler.config_types:
                handler.generate_config(config_subtype)

    logging.info("Reset Brokker configuration: %s", config_type)
