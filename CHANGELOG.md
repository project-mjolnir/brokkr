# Brokkr Changelog


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
