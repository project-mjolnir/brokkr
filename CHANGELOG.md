# Brokkr Changelog


## Version 0.4.0 (2022-06-03)

Stable release supporting Python 3.6-3.10.

### Summary of changes since 0.3.x

This is an overview of what's new in Brokkr 0.4.0 relative to 0.3.x stable.
See the individual alpha release entries for full details.
The remaining sections discuss the changes since the last alpha.

* Add input and output queues to tie together multiple pipelines
* Add support for TCP and arbitrary network packets as inputs
* Add arbitrary binary decode on input and writing on output
* Add external drive discovery, mounting and selection
* Add ``install-scripts`` command to install symlinks to system scripts
* Add ``netcat`` command to interactively send and receive network data

### Core features

* Add support for many new service installation options & per-mode services
* Detect when not invoked from Brokkr's own CLI and ignore CLI args in config

### Bug fixes

* Fix FileOutputStep bug when processing unhashable DataValue types
* Fix multiple bugs and issues with service installation

### Infrastructure

* Migrate from toml to tomli for better perf, maintenance & TOML 1.0.0 support
* Modernize packaging infrastructure for PEP 517 w/pyproject.toml & setup.cfg
* Officially document support for Python 3.10 (now supports 3.6-3.10)
* Add detailed Contributing Guide and greatly expand Readme

### Under the hood

* Add hook to run custom callback on multiprocess worker start
* Add extra debug logging during filepath rendering
* Fix/suppress new Pylint messages & add a suite of extension checkers
* Update Release Guide to use more modern and robust procedure
* Further related refactoring



## Version 0.4.0 Alpha 2 (2021-02-17)

Alpha release with the following changes:

Core features:
* Add Decode InputStep for standalone binary value decoding from any source
* Add new ``install-scripts`` command to install symlinks to system scripts
* Enable ValueInputs adding DataValues to existing dicts/lists
* Add timestamp to all datavalues, and support filling as filename args
* Fill arbitrary DataValues as filename args if specified
* Add ability to truncate data to just headers when putting to queue
* Allow file outputsteps to select a specific key to output
* Add ``truncate_after`` option to ValueInput and improve input handling

Under the hood:
* Avoid class of bugs with inplace update of system presets
* Upgrade pylint configuration and fix linting issues
* Upgrade gitattributes configuration to current version
* Improve error handling in numerous places
* Further refactoring and code cleanup
* Fix a number of minor bugs, inconsistencies and textual/doc issues



## Version 0.4.0 Alpha 1 (2020-08-13)

Alpha release with the following changes:

Core features:
* Add input and output queues to tie together multiple pipelines
* Add support for TCP and arbitrary network packets as inputs
* Add binary file writing for output
* Add external drive discovery, mounting and selection
* Add netcat command to send commands and receive simple network data

Infrastructure:
* Greatly enhance functionality of FileOutputStep and filename/path gen
* Add CLI option to select pipeline to run with `brokkr status`/`monitor`
* Enable ability to enable/disable specific pipelines with config option
* Add smart repr for large/binary objects in pretty printer

Under the hood:
* Refactor network code for enhanced functionality, robustness and perf.
* Improve error handling and debug logging package-wide
* Improve error/NA/exit sentinels, shutdown and pipeline handling
* Further general refactoring, cleanup and commenting



## Version 0.3.0 Final (2020-06-18)

Stable release with the following changes:

* Ensure preset fill is recursive
* Add suffix to column name to allow multiple sensors per preset
* Add option to inject zero on startup to indicate breaks in data continuity
* Add ability to fill data_types presets defined in steps
* Further minor improvements, refactoring and bug fixes
* Further enhancements to documentation
* Package for stable release



## Version 0.3.0 Alpha 3 (2020-05-13)

Alpha release with the following changes:

Core Features:
* Add support for numerous new sensor and protocol types:
    * Adafruit Analog
    * Adafruit I2C
    * Adafruit Onewire
    * Generic Analog
    * Generic Counter
    * Generic GPIO/Digital
    * Generic I2C/SMBus
    * Generic Onewire

Under the Hood:
* Numerous minor improvements and bug fixes
* Further documentation improvements



## Version 0.3.0 Alpha 2 (2020-04-25)

Alpha release with the following changes:

Core Features:
* Add DataType and DataValue classes with automatic handling and extra attributes
* Add ValueInputStep with built-in decode and additional automation
* Add lightweight plugin system for steps

Infrastructure:
* Add preset type insertion in presets
* Add dependency checking, installation and management
* Add version check for system config packages

Under the Hood:
* Refactor existing classes and presets to use new API
* Numerous minor improvements and bug fixes
* Further documentation improvements



## Version 0.3.0 Alpha 1 (2020-03-21)

Major alpha release with the following changes:

Core Features:
* Add multiprocess architecture, management and termination
* Add Pipeline core framework and port current codebase over to it
* Centralize configuration, presets and plugins into a system config package
* Enable use with non-HAMMA systems, and support multiple at once
* Add system and unit config creation, handling and management

Infrastructure:
* Make behavior fully configuration via preferences and factor out HAMMA-specific components
* Improve handling of config file/preset errors with much friendlier messages and behavior
* Enhance install, configuration and setup features
* Improve handling, formatting and customizability of logging
* Overhaul CLI UI, UX, commands and flexibility

Under the Hood:
* Complete rewrite of core config system to OO for modularity, flexibility and simplicity
* Make all inputs, outputs and primary logic OO and class-based for modularity
* Comprehensively refactor for cleaner organization, more reliable operating and easier extension
* Numerous bug fixes and minor improvements
* Improve readme and documentation



## Version 0.2.5 (2020-01-24)

Bugfix release with the following changes:

* Fix serious persistent error after disconnect/reconnecting charge controller
* Improve serial port selection alg and ignore built-in ARM serial port
* Improve logging messages selecting and connecting to serial port
* Remove spurious Unicode BOM that somehow snuck into README



## Version 0.2.4 (2020-01-14)

Bugfix release with the following change:

* Fix low-level system I/O error connecting to Modbus device not being caught



## Version 0.2.3 (2019-11-18)

Bugfix release with the following change:

* Fix pseudo-underflow in temperature data due to incorrect int interpretation



## Version 0.2.2 (2019-10-28)

Bugfix release with the following changes:

* Avoid bug on debian-like platforms manually enabling ``ssshd``
* Require `serviceinstaller` >= 0.1.1 to fix other similar install bugs/issues



## Version 0.2.1 (2019-09-24)

Bugfix release with the following changes:

* Fix incorrect lengths of NA data for charge controller and sensor H&S packets
* Force (Auto)SSH to keep retrying on failed port forwarding
* Improve (Auto)SSH responsiveness, robustness and performance



Version 0.2.0 (2019-09-20)

Major feature and infrastructure release with numerous improvements.

Core Features:

* Read, decode and log all data from AGS Health & Status packets
* Record total runtime and improve precision of time retrieval
* Record ping return code instead of just True/False
* Automatically detect correct sunsaver serial device
* Greatly improve charge controller error handling, portability and robustness
* Automatically name and rotate monitoring data files by date
* Refine CSV output format for better readability and space-efficiency

Infrastructure:

* Add fully modular, object-oriented configuration management system
* Add comprehensive logging system with modular configuration
* Add systemd service for continuous monitoring and for AutoSSH connectivity
* Split script API into subcommands & add version, help and reset functionality
* Add comprehensive install scripts for config, services and permissions
* Improve readme with more detailed information and instructions

Under the Hood:

* Package Brokkr for pip/PyPI and add changelog, release guide and metadata
* Rewrite monitoring routine to get status data from a fully modular source list
* Separate main, startup and monitoring code for simpler invocation & modularity
* Refactor numerous components to be more flexible and follow best practices



## Version 0.1.1 (2019-08-02)

Temporary field patch (not formally released), with the following changes:

* Add basic logging of startup, shutdown and error messages to file
* Fix critical bug causing a crash attempting to write to non-existent stdout
* Fix serious bug with ping function always returning ``True``



## Version 0.1.0 (2019-07-27)

Initial deployed release, with the following features:

* Periodic monitoring and data logging
* Ping sensor and record results
* Read in, process and output charge controller data
* Format and write monitoring data to CSV
* Basic Readme, requirements, gitignore and module structure
