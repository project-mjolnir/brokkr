# Brokkr Changelog


## Version 0.2.5 (2019-01-24)

Bugfix release with the following change:

* Fix serious persistent error after disconnect/reconnecting charge controller
* Improve serial port selection alg and ignore built-in ARM serial port
* Improve logging messages selecting and connecting to serial port
* Remove spurious Unicode BOM that somehow snuck into README



## Version 0.2.4 (2019-01-14)

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
