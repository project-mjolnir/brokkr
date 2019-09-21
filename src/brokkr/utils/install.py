"""
Setup and installation utilities for Brokkr.
"""

# Standard library imports
import logging
import subprocess
import sys

# Local imports
import brokkr.config.autossh
import brokkr.config.log
import brokkr.config.main
import brokkr.config.service
import brokkr.config.systemd
import brokkr.utils.misc


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


def log_setup(verbose=None):
    if verbose is None:
        logging_level = 99
    elif verbose:
        logging_level = "DEBUG"
    else:
        logging_level = "INFO"
    logging.basicConfig(stream=sys.stdout, level=logging_level)


def install_distro_package(package_name, verbose=None):
    log_setup(verbose)

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


def install_service(service_settings, service_filename, services_enable=None,
                    services_disable=None, platform=None, verbose=None):
    log_setup(verbose)

    logging.debug("Installing %s service...", service_filename)
    platform_config = brokkr.config.systemd.get_platform_config(platform)
    logging.debug("Using platform config settings: %s", platform_config)
    logging.debug("Generating service configuration file...")
    service_config = brokkr.config.systemd.generate_systemd_config(
        service_settings, platform)
    logging.debug("Writing service configuration file to %s",
                  platform_config.install_path / service_filename)
    output_path = brokkr.config.systemd.write_systemd_config(
        service_config, service_filename, platform)

    logging.debug("Reloading systemd daemon...")
    subprocess.run(("systemctl", "daemon-reload"), timeout=5, check=True)

    for service in services_disable:
        logging.debug("Disabling %s (if enabled)...", service)
        subprocess.run(("systemctl", "disable", service),
                       timeout=5, check=False)

    for service in (*services_enable, service_filename):
        logging.debug("Enabling %s...", service)
        subprocess.run(("systemctl", "enable", service),
                       timeout=5, check=True)

    logging.info("Successfully installed %s service to %s",
                 service_filename, output_path)


def install_autossh(skip_package_install=False, platform=None, verbose=None):
    log_setup(verbose)

    if not skip_package_install:
        install_succeeded = install_distro_package("autossh")
        if not install_succeeded:
            return install_succeeded

    install_service(
        brokkr.config.autossh.AUTOSSH_SERVICE_DEFAULTS,
        brokkr.config.autossh.AUTOSSH_SERVICE_FILENAME,
        services_enable=brokkr.config.autossh.AUTOSSH_SERVICES_ENABLE,
        services_disable=brokkr.config.autossh.AUTOSSH_SERVICES_DISABLE,
        platform=platform,
        )
    return True


def install_brokkr_service(platform=None, verbose=None):
    log_setup(verbose)

    install_service(
        brokkr.config.service.BROKKR_SERVICE_DEFAULTS,
        brokkr.config.service.BROKKR_SERVICE_FILENAME,
        services_enable=brokkr.config.service.BROKKR_SERVICES_ENABLE,
        services_disable=brokkr.config.service.BROKKR_SERVICES_DISABLE,
        platform=platform,
    )


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


def install_all(no_install_services=False, verbose=None):
    log_setup(verbose)
    logging.debug("Installing all Brokkr external componenets...")

    install_config_files()

    if sys.platform.startswith("linux") or sys.platform.startswith("win"):
        install_firewall_ports()

    if sys.platform.startswith("linux"):
        install_dialout()
        if not no_install_services:
            install_autossh()
            install_brokkr_service()


def reset_config(config_type="all", verbose=None):
    log_setup(verbose)
    logging.debug("Resetting Brokkr configuration: %s", config_type)

    for config, handler in (("log", brokkr.config.log.CONFIG_HANDLER),
                            ("main", brokkr.config.main.CONFIG_HANDLER)):
        if config_type in ("all", config):
            logging.debug("Restting %s config...", config)
            for config_subtype in handler.config_types:
                handler.generate_config(config_subtype)

    logging.info("Reset Brokker configuration: %s", config_type)
