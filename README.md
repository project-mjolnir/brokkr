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


## Requirements

Built and tested under Python 3.7 (but should be compatible with Python >=3.6; lack thereof should be considered a bug), and should be forward-compatible with Python 3.8 (albeit as yet not fully tested).
Compatible and tested with recent (>= 2019) versions of the packages listed in the ``requirements.txt`` file.
Works best on Linux, but is tested to be fully functional (aside from service features) on Windows (and _should_ work equally macOS) under the Anaconda distribution.


## License

Copyright © 2019-2020 C.A.M. Gerlach, the UAH HAMMA Group and the Project Mjolnir Contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

For the avoidance of doubt, per the terms of the LGPL, plugins, presets and configuration packages are not considered integral parts of the covered work, and may be released under any license, free or proprietary.

The code at the following paths are released under the MIT (Expat) License, Copyright © C.A.M. Gerlach 2019-2020, and subject to future independent release:

```
brokkr/src/brokkr/config/base.py
brokkr/src/brokkr/multiprocess/
brokkr/src/brokkr/pipeline/
brokkr/src/brokkr/utils/log.py
brokkr/src/brokkr/utils/misc.py
```


## Installation and Setup


### Standard install

On Linux, Brokkr can be installed like any other Python package via ``pip`` into a virtual environment like so (with the venv created inside `ENV_NAME` in the current working directory), with the extra packages needed to support specific sensor types (e.g. ``modbus``, ``serial``, ``adafruit``, ``all`` etc) installed as desired:

```bash
python3 -m venv ENV_DIR
source ENV_DIR/bin/activate
pip install brokkr[EXTRA1,EXTRA2...]
```

or, to install a development version:

```bash
python3 -m venv ENV_NAME
source ENV_NAME/bin/activate
git clone https://github.com/hamma-dev/serviceinstaller.git
cd serviceinstaller
pip install -e .
cd ..
git clone https://github.com/hamma-dev/brokkr.git
cd brokkr
pip install -e .[EXTRA1,EXTRA2...]
cd ..
```

On Windows and Mac, use of Anaconda/Miniconda is recommended, substituting conda environments for venvs. While these platforms are supported for development, some functionality specific to running Brokkr in production may be unavailable.

Then, you need to take a few more steps to get your environment set up: clone the system config package(s) you want to use with Brokkr (replace the example ``mjolnir-config-template`` path with yours), register them, and set up your config and unit information.
``SYSTEM_SHORTNAME`` is whatever name you want to register the system with in the system file, and ``UNIT_NUMBER`` is the integer number (arbitrary, but should be unique) you want to designate the device you're installing on.

```
git clone https://github.com/hamma-dev/mjolnir-config-template.git
brokkr configure-system SYSTEM_SHORTNAME /path/to/system/mjolnir-config-template
brokkr configure-init
brokkr configure-unit UNIT_NUMBER
```

Finally, you can run the post-installation setup steps as needed for your system.
For a simple system, to just install the systemd service unit to run Brokkr on startup and restart it if it fails,

```bash
sudo /path/to/virtual/environment/ENV_DIR/bin/python -m brokkr install-service``
```

or for a full install of all post-setup tasks, including the config files, firewall access, and (on Linux) serial port access, Brokkr systemd service, and SSH/AutoSSH service and configuration:

```
sudo /path/to/virtual/environment/ENV_DIR/bin/python -m brokkr install-all
```

Finally, you can check that Brokkr is working with ``brokkr --version``, ``brokkr status`` and the other commands detailed in ``brokkr --help``.
Simply reboot to automatically complete setup and start the ``brokkr`` service, or on all platforms you can manually execute it on the command line immediately with ``brokkr start``.


### Automated clean install

However, for setup on typical IoT devices (i.e. single-board computers like the Raspberry Pi) running a clean copy of a modern Linux-based operating system, Brokkr features a comprehensive setup routine that can bootstrap all key aspects of a factory-fresh system to be ready for deployment in the field.
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

Run the `brokkr status` command to get a snapshot of the monitoring data, and the `brokkr monitor` command to get a pretty-printed display of all the main monitoring variables, updated in real time (1s) as you watch.

The ``brokkr install-*`` commands perform installation functions and the ``brokkr configure-*`` scripts help set up a new or updated ``brokkr`` install.
Use ``brokkr --help`` to get help, ``brokkr --version`` to get the current version.
On Linux, the ``brokkr`` systemd service can be interacted with via the standard systemd commands, e.g. ``sudo systemd {start, stop, enable, disable} brokkr-hamma``, ``systemd status brokkr-hamma``, ``journalctl -u brokkr-hamma``, etc, and the same for ``autossh-brokkr`` which controls remote SSH connectivity.


### Interactive Use (Foreground)
First activate the appropriate Python virtual environment (``source ENV_DIR/bin/activate``).

Then:

* Main foreground start command, for testing: ``brokkr start``
* Oneshot status output: ``brokkr status``
* Lightweight realtime monitoring (prints to screen, can also write to file): ``brokkr monitor``


### Running Brokkr as a Service (Background)

* Generate, install and enable service automatically
    * ``sudo /home/pi/path/to/ENV_DIR/bin/python -m brokkr install-service``
* Start/stop
    * ``sudo systemctl start brokkr-SYSTEMNAME``
    * ``sudo systemctl start brokkr-SYSTEMNAME``
* Enable/disable running on startup
    * ``sudo systemctl enable brokkr-SYSTEMNAME``
    * ``sudo systemctl disable brokkr-SYSTEMNAME``
* Basic status check and latest log output
    * ``systemctl status brokkr-SYSTEMNAME``
* Full log output (also logged to text file ``~/brokkr/hamma/brokkr_hamma_NNN.log``)
    * ``journalctl -xe -u brokkr-SYSTEMNAME``



## Configuration


A major design goal of Brokkr and the Mjolnir system is extensive, flexible and straightforward reconfiguration for different sensor networks and changing needs.
All the system configuration is normally handled through the Mjolnir-HAMMA system config package in the standard Mjolnir config schema developed for this system (located at ~/dev/mjolnir-hamma), aside from a few high-level elements specific to each unit which all have interactive configuration commands as below.

However, if local customization is needed beyond the high-level options specified here, instead of modifying the version-control-tracked system config package directly, the config system built for this is fully hierarchical and all settings can be fully overridden via the corresponding local config in ~/.config/brokkr/hamma
Brokkr fully supports configuration, logging, operation and output of any number of Mjolnir systems simultaneously, all on the same Pi.

Configuration files are located under the XDG-standard ``~/.config/brokkr`` directory in the ini-like [TOML](https://github.com/toml-lang/toml) format; they can be generated by running ``brokkr configure-init`` (which will not overwrite them if they already exist), and reset to defaults with ``brokkr configure-reset``.


### High-level local setting configuration

#### Register, update and remove systems

Register a Mjolnir system:

```bash
brokkr configure-system <SYSTEM-NAME> </PATH/TO/SYSTEM/CONFIG/DIR>
```

(e.g. ``brokkr configure-system hamma /home/pi/dev/mjolnir-hamma``)

You can also use this command to remove, update, verify and set default systems with the appropriate arguments, see brokkr configure-system --help``


#### Generate local config files

Generate empty local per-system (i.e. override) config files if not already present:

```
brokkr configure-init
```

#### Set per-unit configuration

```
brokkr configure-unit <UNIT_NUMBER> --network-interface <INTERFACE>
```

(e.g. ``brokkr configure-unit 1 --network-interface wlan0``)


#### Reset configuration

Reset unit and local override configuration (optionally minus system registry):

```
brokkr configure-reset
```
