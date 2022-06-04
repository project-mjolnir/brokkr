# Brokkr Roadmap


## Version 0.5.0

* Add comprehensive system monitoring with psutil, network status and vcgencmd
* Add additional sensor device steps and presets (SPI, GPIO, GPS, UART, etc)
* Implement rsync uplink of monitoring data, logging, and AGS packet headers
* Add sophisticated, configurable, multi-phase bootstrap/install/setup system
* Implement intelligent watchdog to reset network link or reboot device on errors
* Further refactor design and multiprocessing as needed



## Version 1.0.0

* Factor modular components (confighandler, loghandler, mphandler, etc) into packages
* Add additional processing steps for statistics and diagnostics on ingested data
* Add checkout command to test site connectivity, functionality and config
* Add basic unit and integration tests, and setup CIs
* Write docstrings for all public functions



## Version 1.1.0

* Add sync config command?
* Add high-level remote configuration and management functionality?
* Validate config with JSONschema?
