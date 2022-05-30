# Brokkr

A client for data ingest/logging/uplink, remote management and autonomous & central control of scientific IoT sensors as part of the Mjolnir system.
Originally developed to receive science data and status information from a local HAMMA2 lightning sensor and a Sunsaver MPPT-15L charge controller, store it locally, and transmit it back to a central server (generally, but not necessarily one running the Sindri package), but is now being evolved to be extensible and configurable for a wide variety of applications, from low-cost, low-power arrays of hundreds of environmental monitoring sensors, to sophisticated instruments mounted on aircraft and UAVs.
Further, it can maintain a reverse SSH tunnel to an accessible server for remote access, and receive and execute power, processing system and sensor control commands forwarded as TCP packets over said connection.

The goal of Project Mjolnir is to make it easy for PIs or students without a coding background to easily get started gathering and analyzing data from low-cost sensors right away, and allowing those with basic programming experience to easily develop, test and share their own plugins to work with new types of sensors, outputs and more with little or no extra work over a "quick and dirty" approach but major long-term benefits.
The long-term vision is to create an ecosystem of open-source presets, plugins, examples and more for a wide variety of low-cost scientific IoT sensors.



## Key Features

* Support for SPI, I2C, GPIO, Analog, SMBus, UART, Modbus, TCP, UDP, and more as inputs, and print/pretty print, file and system logging, CSV, and TCP packets as output built into the core
* Easy to use, powerful plugin framework with a simple API and minimal boilterplate for input, processing and output steps; can be either simple Python files placed in a specific directory, or proper Python packages
* Plugins for alerts/triggered actions, Slack notifications, REST/web APIs and much more
* Built-in support for dozens of different sensors including ECH2O EC-5, EC-10, EC-20, DS18S20, DS1822, DS18B20, DS28EA00, DS1825, MAX31850K, HIH6130, Si7021, SHT31D, MPL3115A2, MLX90614, HTU21D, DHT11, DHT22, BMP280, BME280, MPPT-15L, HAMMA2, ADS1015, ADS1115, and generic switch, counter, GPIO and analog anemometer dir and speed, plus time, runtime, ping, and more
* Drop-in, declarative preset system for supporting new sensors, devices and protocols; presets can be enabled with as little as 1 line in the master config file, and extensively customized via config options
* Robust error handling, status logging, automatic installation, service configuration and multiprocess management infrastructure
* Hierarchical configuration system, allowing for multiple levels of settings and overrides
* System-independent and fully multi-system capable; all metadata, config, plugins and presets stored within VCS-trackable self-contained package for easy management



## License

Copyright (c) 2019-2022 C.A.M. Gerlach, the UAH HAMMA Group and the Project Mjolnir Contributors

This project is distributed under the terms of the MIT (Expat) License; see the [LICENSE.txt](./LICENSE.txt) for more details.



## Installation and Setup

Brokkr is built and tested under Python 3.6-3.10, with a relatively minimal set of lightweight, pure-Python core dependencies.
It works best on Linux, but is tested to be fully functional (aside from service features) on Windows (and _should_ work equally on macOS) using the Anaconda distribution.


### Standard install

On Linux (or other platforms, for experienced users), Brokkr can be installed like any other Python package, via ``pip`` into a ``venv`` virtual environment.

For example, with the venv created inside ``ENV_DIR`` in the current working directory, and installing the ``EXTRA`` packages needed to support specific sensor types (e.g. ``modbus``, ``serial``, ``adafruit``, etc, or ``all`` for all of them) as desired:

```shell
python3 -m venv ENV_DIR
source ENV_DIR/bin/activate
pip install brokkr[EXTRA1,EXTRA2...]
```

On Windows and Mac, use of Anaconda/Miniconda is recommended, substituting conda environments for venvs.
While these platforms are supported for development, some functionality specific to running Brokkr in production may be unavailable.

For information on installing a development version, see the [Contributing Guide](./CONTRIBUTING.md).

Then, you need to take a few more steps to get your environment set up: clone the system config package(s) you want to use with Brokkr (replace the example ``mjolnir-config-template`` path with yours), register them, and set up your config and unit information.
``SYSTEM_SHORTNAME`` is whatever name you want to register the system with in the system file, and ``UNIT_NUMBER`` is the integer number (arbitrary, but should be unique) you want to designate the device you're installing on.

```shell
git clone https://github.com/project-mjolnir/mjolnir-config-template.git
brokkr configure-system SYSTEM_SHORTNAME /path/to/system/mjolnir-config-template
brokkr configure-init
brokkr configure-unit UNIT_NUMBER
```

Finally, you can run the post-installation setup steps as needed for your system.
First, you'll want to install any system-specific dependencies,

```shell
brokkr install-dependencies
```

Then, to just install the Systemd service unit to run Brokkr on startup, run:

```shell
sudo /PATH/TO/ENV_DIR/bin/python -m brokkr install-service``
brokkr install-dependencies
```

You can set a specific account, install path and startup arguments if desired; see ``brokkr install-service --help`` for more usage and option information.

For a full install of all post-setup tasks, including the config files, scripts, system-specific dependencies, firewall access, and (on Linux) serial port access, Brokkr systemd service, and SSH/AutoSSH service and configuration, you can instead run:

```shell
sudo /PATH/TO/ENV_DIR/bin/python -m brokkr install-all
brokkr install-dependencies
```

Finally, you can check that Brokkr is installed and set up correctly with ``brokkr --version``, ``brokkr status`` and the other commands detailed in ``brokkr --help``.
Simply reboot to automatically complete setup and start the ``brokkr`` service, or on all platforms you can manually execute it on the command line immediately with ``brokkr start``.


### Automated clean install (under development)

For setup on typical IoT devices (i.e. single-board computers like the Raspberry Pi) running a clean copy of a modern Linux-based operating system, Brokkr features a comprehensive setup routine that can bootstrap all key aspects of a factory-fresh system to be ready for deployment in the field.
Simply declare the configuration files you want copied, packages and services you want installed/enabled/disabled/removed, firewall ports you want open closed, and other custom actions (move files, sed scripts, commands run, etc) for each phase of the install as part of the system config package, and on your command, brokkr will do the rest.

A typical semi-automated install flow might look like the following

1. Flash SD card with OS image
2. Perform basic raspi-config, Fedora, etc. setup; change username if desired
3. Create and activate venv, ``pip install brokkr --no-dependencies`` from offline sdist and copy system config dir and any keyfiles
4. Run ``brokkr configure-system <systemname> <systempath>`` to set the system config dir path
5. Run ``brokkr install --phase 1`` to perform the necessary steps to enable Internet
6. Update all packages to latest (``apt update && apt full-upgrade && apt autoremove``) and reinstall brokkr with all packages (``pip uninstall brokkr && pip install brokkr``)
7. Run ``brokkr install --phase 2`` to install remaining items
8. Run ``brokkr setup-device`` to trigger device-specific setup actions
9. Create venv for Sindri and ``pip install sindri`` it (optional)
10. Once on-site, perform unit configuration (see below)

A sample bash script will be provided that runs steps 3-9 of this workflow automatically, and can be customized to the needs of a specific system.


### Flashing Brokkr onto a prepared card

If a card is already prepared via the steps mentioned in the "Automated clean install" section (minus the `brokkr setup-device` step), flashing it onto another device and preparing it for deployment is simple.

1. After flashing the Pi and activating the appropriate venv, run ``brokkr setup-device`` to regenerate the harnesses device-specific items (password, hashes, SSH keys, etc). You’ll need to enter the Pi’s current and desired password at the interactive prompt.
3. Finally, on site, once the final unit configuration is set (or after it is changed in the future), perform on-site setup as below


### On-site setup

On site, you'll want to take a couple additional actions to pair a specific device with a specific site, and test connectivity.

1. Run ``brokkr configure-unit <unit-number> --network-interface <network-interface>`` to set up the basic unit configuration
2. Run ``brokkr setup-unit`` to perform final per-unit on-site setup, register and test the link to the sensor, and verify connectivity to the upstream server
3. Power off the device, connect it to all desired hardware and reboot



## Usage

### Overview

See ``brokkr --help`` and ``brokkr <SUBCOMMAND> --help`` for detailed documentation of Brokkr's CLI, invocation, options and subcommands.
The following is a brief, high-level summary.

For a quick check of Brokkr, its version and that of the current system (if configured), use ``brokkr --version``.
Run the ``brokkr status`` command to get a snapshot of the monitoring data, and the ``brokkr monitor`` command to get a pretty-printed display of all the main monitoring variables, updated in real time (every 1 s by default) as you watch.
``brokkr start`` is the main entrypoint for Brokkr's core functionality, loading and executing the configured data acquisition, processing and output pipelines, and in normal usage is run though the Brokkr service.

The ``brokkr install-*`` commands perform installation functions and the ``brokkr configure-*`` functionality helps set up a new or updated ``brokkr`` install.
On Linux, the ``brokkr-SYSTEMNAME`` systemd service can be interacted with via the standard systemd commands, e.g. ``sudo systemd {start, stop, enable, disable} brokkr-SYSTEMNAME``, ``systemd status brokkr-SYSTEMNAME``, ``journalctl -u brokkr-SYSTEMNAME``, etc, and the same for ``autossh-brokkr`` which controls remote SSH connectivity.


### Interactive Use (Foreground)

First, activate the appropriate Python virtual environment (e.g. ``source ENV_DIR/bin/activate``).

Then, you have a few options:

* Main foreground start command, for testing: ``brokkr start``
* Oneshot status output: ``brokkr status``
* Lightweight realtime monitoring (prints to screen, can also write to file): ``brokkr monitor``


### Running Brokkr as a Service (Background)

* Generate, install and enable service automatically:
    * ``sudo /home/pi/path/to/ENV_DIR/bin/python -m brokkr install-service``
* Start/stop:
    * ``sudo systemctl start brokkr-SYSTEMNAME``
    * ``sudo systemctl stop brokkr-SYSTEMNAME``
* Enable/disable running on startup:
    * ``sudo systemctl enable brokkr-SYSTEMNAME``
    * ``sudo systemctl disable brokkr-SYSTEMNAME``
* Basic status check and latest log output:
    * ``systemctl status brokkr-SYSTEMNAME``
* Full log output (also logged to text file ``~/brokkr/hamma/brokkr_hamma_NNN.log``)
    * ``journalctl -xe -u brokkr-SYSTEMNAME``



## Configuration

A major design goal of Brokkr and the Mjolnir system is extensive, flexible and straightforward reconfiguration for different sensor networks and changing needs.
For example, with the UAH HAMMA2 system, all the system configuration is normally handled through the [Mjolnir-HAMMA system config package](https://github.com/hamma-dev/mjolnir-hamma/) in the standard Mjolnir config schema developed for this system, aside from a few high-level elements specific to each unit which all have interactive configuration commands as below.

However, if local customization is needed beyond the high-level options specified here, instead of modifying the version-control-tracked system config package directly, the config system built for this is fully hierarchical and all settings can be fully overridden via the corresponding local config in ``~/.config/brokkr/SYSTEM_NAME``.
Brokkr fully supports configuration, logging, operation and output of any number of Mjolnir systems simultaneously, all on the same Pi.

Configuration files are located under the XDG-standard ``~/.config/brokkr`` directory in the ini-like [TOML](https://github.com/toml-lang/toml) format; they can be generated by running ``brokkr configure-init`` (which will not overwrite them if they already exist), and reset to defaults with ``brokkr configure-reset``.


### High-level local setting configuration

#### Register, update and remove systems

Register a Mjolnir system:

```shell
brokkr configure-system <SYSTEM-NAME> </PATH/TO/SYSTEM/CONFIG/DIR>
```

(e.g. ``brokkr configure-system hamma /home/pi/dev/mjolnir-hamma``)

You can also use this command to remove, update, verify and set default systems with the appropriate arguments; see ``brokkr configure-system --help``


#### Generate local config files

Generate empty local per-system (i.e. override) config files if not already present:

```shell
brokkr configure-init
```

#### Set per-unit configuration

```shell
brokkr configure-unit <UNIT_NUMBER> --network-interface <INTERFACE>
```

(e.g. ``brokkr configure-unit 1 --network-interface wlan0``)


#### Reset configuration

Reset unit and local override configuration (optionally minus the system registry):

```shell
brokkr configure-reset
```
