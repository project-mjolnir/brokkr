# Brokkr Roadmap


## Version 0.3.0 (End of Feb 2020; nearly complete)

* Design and implement multiprocess architecture across client
* Add extensive system monitoring with psutil, network status and vcgencmd
* Read in and write out high-bandwidth TCP datastream (AGS science data)
* Add sophisticated, configurable, multi-phase bootstrap/install/setup system
* Refactor configuration system into a modular, object-oriented architecture
* Add system and unit configuration modules and system config package
* Enhance error handling, logging, CLI/UX, performance and more
* Comprehensive refactor and cleanup throughout



## Version 0.4.0 (Mid March 2020)

* Implement uplink of monitoring data, logging, and AGS packet headers
* Add intelligent watchdog to reset network link or reboot device on errors
* Enable multiple asynchronous monitoring routines (e.g. hourly dump of EEPROM)
* Further refactor design and multiprocessing as needed



## Version 1.0.0 (End of March 2020)

* Run additional periodic statistics and diagnostics on ingested data
* Add checkout command to test site connectivity, functionality and config
* Implement fully object-oriented data ingest, decode and uplink
* Factor system-specific items out of core and into config and device profiles
* Add basic unit and integration tests, and setup CIs
* Write docstrings for all public functions



## Version 1.1.0 (May 2020)

* Add lightweight plugin system
* Add sync config command
* Add high-level remote configuration and management functionality
* Validate config with JSONschema?



## Version 2.0.0 (???)

* Real time science data processing and uplink?
* Additional uplink modules?
