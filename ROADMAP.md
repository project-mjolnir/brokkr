# Brokkr Roadmap


## Version 0.4.0 (NET March 2021)

* Read in and write out high-bandwidth TCP datastreams
* Add handling for mounting, management and cleanup of external USB devices
* Decode, process and write asynchronous header data from datastreams
* Add additional sensor device steps and presets (SPI, GPIO, GPS, UART, etc)
* Add comprehensive system monitoring with psutil, network status and vcgencmd



## Version 0.5.0 (NET Summer 2021)

* Implement rsync uplink of monitoring data, logging, and AGS packet headers
* Add sophisticated, configurable, multi-phase bootstrap/install/setup system
* Implement intelligent watchdog to reset network link or reboot device on errors
* Further refactor design and multiprocessing as needed



## Version 1.0.0 (NET Fall 2021)

* Factor modular components (confighandler, loghandler, mphandler, etc) into packages
* Add additional processing steps for statistics and diagnostics on ingested data
* Add checkout command to test site connectivity, functionality and config
* Add basic unit and integration tests, and setup CIs
* Write docstrings for all public functions



## Version 1.1.0 (NET Late 2021?)

* Add sync config command?
* Add high-level remote configuration and management functionality?
* Validate config with JSONschema?

