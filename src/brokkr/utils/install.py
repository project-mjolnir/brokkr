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
try:
    import serviceinstaller
except ModuleNotFoundError:  # If its not installed, eg. on non-Linux platforms
    # pylint: disable=invalid-name
    serviceinstaller = None

# Local imports
import brokkr.config.base
import brokkr.pipeline.builder
import brokkr.start
import brokkr.utils.log
import brokkr.utils.misc
import brokkr.utils.services


# General constants
COMMAND_TIMEOUT = 30

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
UDEV_INSTALL_PATH = Path("/", "etc", "udev", "rules.d")
UDEV_FILENAME = "98-brokkr-usb.rules"
UDEV_RULES = """
# Enable brokkr client to reset and power up/down USB devices
SUBSYSTEM=="usb", MODE="0660", GROUP="dialout"
SUBSYSTEM=="usb-serial", MODE="0660", GROUP="dialout"

"""


def _install_distro_package(package_name):
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


def _write_os_config_file(file_contents, filename, output_path):
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


@brokkr.utils.log.basic_logging
def install_autossh(skip_package_install=False, platform=None):
    # pylint: disable=import-outside-toplevel
    from brokkr.config.main import CONFIG
    if serviceinstaller is None:
        raise ModuleNotFoundError("Serviceinstaller must be installed.")
    if not CONFIG["autossh"]["server_hostname"]:
        raise RuntimeError(
            "Cannot install autossh: Hostname not provided in config. "
            "Run 'brokkr configure-system' to set the system config path, "
            "and ensure a value is preset for at least the "
            "'server_hostname' key in the main config's 'autossh' section.")

    if not skip_package_install:
        install_succeeded = _install_distro_package("autossh")
        if not install_succeeded:
            return install_succeeded

    serviceinstaller.install_service(
        **brokkr.utils.services.AUTOSSH_SERVICE_KWARGS, platform=platform)
    return True


@brokkr.utils.log.basic_logging
def install_service(platform=None):
    if serviceinstaller is None:
        raise ModuleNotFoundError("Serviceinstaller must be installed.")
    serviceinstaller.install_service(
        **brokkr.utils.services.BROKKR_SERVICE_KWARGS, platform=platform)


@brokkr.utils.log.basic_logging
def install_dependencies(dry_run=False):
    # pylint: disable=import-outside-toplevel
    from brokkr.config.main import CONFIG

    # Build pipelines to search
    logging.debug("Checking pipelines for dependencies to install")
    if not CONFIG["pipelines"]:
        logging.warning("No pipelines defined; skipping dependency search")
        return None
    build_context = brokkr.start.create_build_context()
    top_level_builder = brokkr.pipeline.builder.ObjectBuilder(
        steps=CONFIG["pipelines"], build_context=build_context)
    top_level_builder.setup()

    # Get dependencies from pipelines
    all_dependencies = brokkr.utils.misc.get_all_attribute_values_recursive(
        top_level_builder.subbuilders,
        attr_get="dependencies",
        attr_recurse="subbuilders",
        )
    all_dependencies = {
        item for sublist in all_dependencies for item in sublist}
    if not all_dependencies:
        logging.info("No dependencies found, skipping install")
        return all_dependencies
    if dry_run:
        logging.warning("Dry run, would install: %s", all_dependencies)
        return all_dependencies
    logging.debug("Dependencies found: %s", all_dependencies)

    # Install dependencies
    install_command = (
        [sys.executable, "-m", "pip", "install"] + list(all_dependencies))
    logging.debug("Dependency install command invocation: %s",
                  " ".join(install_command))
    try:
        subprocess.run(install_command, check=True)
    except Exception as e:
        logging.error("%s running dependency install: %s",
                      type(e).__name__, e)
        logging.info("Error details:", exc_info=True)
        logging.info("Command invocation: %s", " ".join(install_command))
        return None
    logging.info("Successfully install dependencies: %s", all_dependencies)

    return all_dependencies


@brokkr.utils.log.basic_logging
def install_dialout():
    logging.debug("Enabling serial port access for user %s...",
                  brokkr.utils.misc.get_actual_username())
    subprocess.run(("usermod", "-a", "-G", "dialout",
                    brokkr.utils.misc.get_actual_username()),
                   timeout=COMMAND_TIMEOUT, check=True)
    logging.info("Enabled serial port access for user %s",
                 brokkr.utils.misc.get_actual_username())


@brokkr.utils.log.basic_logging
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
                subprocess.run(
                    command(port, proto), timeout=COMMAND_TIMEOUT, check=False)
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
                subprocess.run(command, timeout=COMMAND_TIMEOUT, check=False)
            except FileNotFoundError:
                logging.debug("%s not found on system.", name)
            except Exception:
                logging.info("Error running followup %s ignored.", name)
                logging.debug("Error details:", exc_info=True)
                logging.debug("Command invocation: %s", " ".join(command))

    logging.info("Attempted to open firewall ports: %r", ports_to_open)


@brokkr.utils.log.basic_logging
def install_udev(
        udev_rules=UDEV_RULES,
        udev_filename=UDEV_FILENAME,
        udev_install_path=UDEV_INSTALL_PATH,
        ):
    logging.debug("Installing udev rules for USB access...")

    if not sys.platform.startswith("linux"):
        raise NotImplementedError("Udev rules are only implemented on Linux.")

    _write_os_config_file(udev_rules, udev_filename, udev_install_path)

    # Reload udev to update configuration
    subprocess.run(["udevadm", "control", "--reload-rules"],
                   timeout=COMMAND_TIMEOUT, check=True)
    subprocess.run(
        ["udevadm", "trigger"], timeout=COMMAND_TIMEOUT, check=True)


@brokkr.utils.log.basic_logging
def install_all(no_install_services=False):
    logging.debug("Installing all Brokkr external componenets...")

    if sys.platform.startswith("linux") or sys.platform.startswith("win"):
        install_firewall()

    if sys.platform.startswith("linux"):
        install_dialout()
        install_udev()
        if not no_install_services:
            install_autossh()
            install_service()
