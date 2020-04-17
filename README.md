# Brokkr

A client for data ingest/logging/uplink, remote management and autonomous & central control of scientific IoT sensors as part of the Mjolnir system.
Originally developed to receive science data and status information from a local HAMMA2 lightning sensor and a Sunsaver MPPT-15L charge controller, store it locally, and transmit it back to a central server (generally, but not necessarily one running the Sindri package), but is now being evolved to be extensible and configurable for a wide variety of applications, from low-cost, low-power arrays of hundreds of environmental monitoring sensors, to sophisticated instruments mounted on aircraft and UAVs.
Further, it can maintain a reverse SSH tunnel to an accessible server for remote access, and receive and execute power, processing system and sensor control commands forwarded as TCP packets over said connection.



## Requirements

Built and tested under Python 3.7 (but should be compatible with Python >=3.6; lack thereof should be considered a bug), and should be forward-compatible with Python 3.8 (albeit as yet not fully tested).
Compatible and tested with recent (>= 2019) versions of the packages listed in the ``requirements.txt`` file.
Works best on Linux, but is tested to be fully functional (aside from service features) on Windows (and _should_ work equally macOS) under the Anaconda distribution.


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
source ENV_DIR/bin/activate
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
4. Run ``brokkr configure-system <systempath>`` to set the system config dir path
5. Run ``brokkr install --phase 1`` to perform the necessary steps to enable Internet
6. Update all packages to latest (``apt update && apt full-upgrade && apt autoremove``) and reinstall brokkr with all packages (``pip uninstall brokkr && pip install brokkr``)
7. Run ``brokkr install --phase 2`` to install remaining items
8. Run ``brokkr setup-device`` to trigger device-specific setup actions
9. Create venv for Sindri and ``pip install`` it (optional)
10. Once on-site, perform unit configuration (see below)

A sample bash script will be provided that runs steps 3-9 of this workflow automatically, and can be customized to the needs of a specific system.


### Flashing Brokkr onto a prepared card

If a card is already prepared via the steps mentioned in the "Automated clean install" section (minus the `brokkr setup-device` step), flashing it onto another device and preparing it for deployment is simple.

1. After flashing the Pi and activating the appropriate venv, run ``brokkr setup-device`` to regenerate the harnesses device-specific items (password, hashes, SSH keys, etc). You’ll need to enter the Pi’s current and desired password at the interactive prompt.
2. Once a specific unit number is assigned to a Pi, or on site, run ``brokkr configure-unit <unit-number> <network-interface>`` to set the unit number, connection mode, and other unit-specific details.
3. Finally, on site, once the final unit configuration is set (or after it is changed in the future), perform on-site setup as below


### On-site setup

On site, you'll want to take a couple additional actions to pair a specific device with a specific site, and test connectivity.

1. Run ``brokkr configure-unit <unit-number> <network-interface>`` to set up the basic unit configuration
2. Run ``brokkr setup-unit`` to perform final per-unit on-site setup, register and test the link to the sensor, and verify connectivity to the upstream server
3. Power off the device, connect it to all desired hardware and reboot



## Usage

Run the `brokkr status` command to get a snapshot of the monitoring data, and the `brokkr monitor` command to get a pretty-printed display of all the main monitoring variables, updated in real time (1s) as you watch.

The ``brokkr install-*`` commands perform installation functions and the ``brokkr configure-*`` scripts help set up a new or updated ``brokkr`` install.
Use ``brokkr --help`` to get help, ``brokkr --version`` to get the current version.
On Linux, the ``brokkr`` systemd service can be interacted with via the standard systemd commands, e.g. ``sudo systemd {start, stop, enable, disable} brokkr``, ``systemd status brokkr``, ``journalctl -u brokkr``, etc, and the same for ``autossh-brokkr`` which controls remote SSH connectivity.



## Configuration

Configuration files are located under the XDG-standard ``~/.config/brokkr`` directory in the ini-like [TOML](https://github.com/toml-lang/toml) format; they can be generated by running ``brokkr install-config`` (which will not overwrite them if they already exist), and reset to defaults with ``brokkr configure-reset``.
The ``*_remote.json`` config files are designed to be updated automatically from the server.
To temporarily override the centrally-managed settings with local ones, configure the appropriate settings in ``{config-name}_local.toml`` and set its ``override`` to ``true``.
