# Brokkr Roadmap


## Version 0.4.0 (NET July 2020)

* Add comprehensive system monitoring with psutil, network status and vcgencmd
* Read in and write out high-bandwidth TCP datastreams
* Add handling for mounting, management and cleanup of external USB devices
* Decode, process and write asynchronous header data from datastreams
* Implement intelligent watchdog to reset network link or reboot device on errors
* Port log handler to new architecture and do additional refactoring and cleanup
* Add additional sensor device steps and presets (SPI, GPIO, GPS, UART, etc)



## Version 0.5.0 (NET August 2020)

* Implement TCP uplink of monitoring data, logging, and AGS packet headers
* Enable multiple asynchronous monitoring routines (e.g. hourly dump of EEPROM)
* Add sophisticated, configurable, multi-phase bootstrap/install/setup system
* Further refactor design and multiprocessing as needed



## Version 1.0.0 (NET September 2020)

* Factor modular components (confighandler, loghandler, mphandler, etc) into packages
* Add additional processing steps for statistics and diagnostics on ingested data
* Add checkout command to test site connectivity, functionality and config
* Add basic unit and integration tests, and setup CIs
* Write docstrings for all public functions



## Version 1.1.0 (Late 2020?)

* Add sync config command
* Add high-level remote configuration and management functionality
* Validate config with JSONschema



## Version 2.0.0 (???)

* Real time data processing and uplink
* Additional uplink modules
* Support additional core sensor, device and preset types
