# Brokkr

A Python package to log data and status information from a local HAMMA sensor and a SS-MPPT-15L power controller on a Raspberry Pi and transmit it back to a central server.


## Power controller data

To read in data from the power controller, the same must be connected via the serial to USB adapter, the Python packages ``pymodbus`` and ``pyserial`` are required, and the following command must be run at some point after installing the system and creating a user account to ensure the account is added to the correct permissions group to access the serial ports (make sure to log out and log back in after doing so):

```bash
sudo usermod -a -G dialout $USER
```
