# Brokkr

A Python package to receive science data and status information from a local HAMMA2 lightning sensor and a Sunsaver MPPT-15L charge controller, store it locally, and transmit it back to a central server (generally, but not necessarily one running the Sindri package).
Further, it can maintain a reverse SSH tunnel to an accessible server for remote access, and receive and execute power, processing system and sensor control commands forwarded as custom binary TCP packets over said connection.



## Installation and Setup

Built and tested under Python 3.7 (but should be compatible with Python >=3.6; lack thereof should be considered a bug) and recent (<= 2019) versions of the packages listed in the `requirements.txt` file.

To read in data from the charge controller, the same must be connected via the serial to USB adapter, the Python packages ``pymodbus`` and ``pyserial`` are required, and if on most Linux systems, the following command must be run at some point after installing the system and creating an account to ensure the user is added to the correct permissions group to access the serial ports (make sure to log out and log back in after doing so):

```bash
sudo usermod -a -G dialout $USER
```
