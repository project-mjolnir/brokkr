"""
Installation commands and utilities for Brokkr.
"""

# Standard library imports
import logging
import os
from pathlib import Path
import subprocess
import sys

# Third party imports
import serviceinstaller

# Local imports
import brokkr.config.autossh
import brokkr.config.base
import brokkr.config.handlers
import brokkr.config.service
import brokkr.utils.misc
from brokkr.utils.misc import basic_logging


# General constants
DISTRO_INSTALL_COMMANDS = (
    lambda package_name: ("apt-get", "-y", "install", package_name),
    lambda package_name: ("dnf", "-y", "install", package_name),
    lambda package_name: ("yum", "-y", "install", package_name),
    lambda package_name: ("pacman", "-S", "--noconfirm", package_name),
    )

# Firewall constants
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

# Udev constants
UDEV_INSTALL_PATH = Path("etc", "udev", "rules.d")
UDEV_FILENAME = "10-brokkr-usb.rules"
UDEV_RULES = """
# Enable brokkr client to reset and power up/down USB devices
SUBSYSTEM=="usb", MODE="0660", GROUP="dialout"
SUBSYSTEM=="usb-serial", MODE="0660", GROUP="dialout"
"""


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


def write_system_config_file(file_contents, filename, output_path):
    output_path = Path(output_path)
    os.makedirs(output_path, mode=0o755, exist_ok=True)
    with open(output_path / filename, "w",
              encoding="utf-8", newline="\n") as config_file:
        config_file.write(file_contents)
    os.chmod(output_path / filename, 0o644)
    try:
        os.chown(output_path / filename, 0, 0)
    except AttributeError:
        pass  # No chown on Windows
    return output_path


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
def install_service(platform=None):
    serviceinstaller.install_service(
        brokkr.config.service.SERVICE_DEFAULTS,
        service_filename=brokkr.config.service.SERVICE_FILENAME,
        services_enable=brokkr.config.service.SERVICES_ENABLE,
        services_disable=brokkr.config.service.SERVICES_DISABLE,
        platform=platform,
    )


@basic_logging
def install_config():
    config_handlers = brokkr.config.handlers.CONFIG_HANDLERS
    for config_name, handler in config_handlers.items():
        logging.debug("Installing %s config...", config_name)
        handler.read_configs()
    logging.info(
        "Config files installed to %r",
        brokkr.config.base.DEFAULT_CONFIG_PATH.as_posix())


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
def install_firewall(ports_to_open=PORTS_TO_OPEN):
    logging.debug("Opening firewall ports: %r", ports_to_open)

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
                logging.debug("Error details:", exc_info=True)
                logging.debug("Command invocation: %s", " ".join(command))

    if sys.platform.startswith("linux"):
        for name, command in FIREWALL_COMMANDS_LINUX_AFTER.items():
            logging.debug("Running followup command for %s...", name)
            try:
                subprocess.run(command, timeout=5, check=False)
            except FileNotFoundError:
                logging.debug("%s not found on system.", name)
            except Exception:
                logging.info("Error running followup %s ignored.", name)
                logging.debug("Error details:", exc_info=True)
                logging.debug("Command invocation: %s", " ".join(command))

    logging.info("Attempted to open firewall ports: %r", ports_to_open)


@basic_logging
def install_udev(
        udev_rules=UDEV_RULES,
        udev_filename=UDEV_FILENAME,
        udev_install_path=UDEV_INSTALL_PATH,
        ):
    logging.debug("Installing udev rules for USB access...")

    if not sys.platform.startswith("linux"):
        raise NotImplementedError("Udev rules are only implemented on Linux.")

    write_system_config_file(udev_rules, udev_filename, udev_install_path)

    # Reload udev to update configuration
    subprocess.run(["udevadm", "control", "--reload-rules"],
                   timeout=5, check=True)
    subprocess.run(["udevadm", "trigger"], timeout=5, check=True)


@basic_logging
def install_all(no_install_services=False):
    logging.debug("Installing all Brokkr external componenets...")

    install_config()

    if sys.platform.startswith("linux") or sys.platform.startswith("win"):
        install_firewall()

    if sys.platform.startswith("linux"):
        install_dialout()
        install_udev()
        if not no_install_services:
            install_autossh()
            install_service()
