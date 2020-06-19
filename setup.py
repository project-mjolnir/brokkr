#!/usr/bin/env python3
"""
Setup script for Brokkr, a scientific IoT sensor client.
"""

# Standard library imports
from pathlib import Path

# Third party imports
import setuptools


PROJECT_NAME = "brokkr"


with open(Path(__file__).resolve().parent / "README.md",
          mode="r", encoding="utf-8") as readme_file:
    LONG_DESCRIPTION = readme_file.read()

# Single source the version; based on a PyPA pattern and exec is nessesary
VERSION = {}
with open(Path(__file__).resolve().parent
          / "src" / PROJECT_NAME / "_version.py",
          mode="r", encoding="utf-8") as version_file:
    exec(version_file.read(), VERSION)  # pylint: disable=exec-used


setuptools.setup(
    name=PROJECT_NAME,
    version=VERSION["__version__"],
    author="C.A.M. Gerlach/UAH HAMMA group",
    author_email="CAM.Gerlach@Gerlach.CAM",
    description=("A client for data ingest/logging/uplink, remote management "
                 "and autonomous & central control of scientific IoT sensors "
                 "as part of the Mjolnir system."),
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    keywords="iot lightning sensor remote control research m2m raspberry pi",
    url="https://github.com/hamma-dev/brokkr",
    packages=setuptools.find_packages("src"),
    package_dir={"": "src"},
    python_requires=">=3.6",
    install_requires=[
        "packaging",
        "serviceinstaller >= 0.1.3 ; sys_platform=='linux'",
        "simpleeval",
        "toml",
        ],
    extras_require={
        "all": [
            "Adafruit-Blinka",
            "adafruit-circuitpython-busdevice",
            "gpiozero",
            "pymodbus",
            "pyserial",
            "RPi.GPIO",
            "smbus2",
            ],
        "adafruit": [
            "Adafruit-Blinka",
            "adafruit-circuitpython-busdevice",
            ],
        "gpio": [
            "gpiozero",
            "RPi.GPIO",
            ],
        "modbus": [
            "pymodbus",
            "pyserial",
            ],
        "smbus": [
            "smbus2",
            ],
        },
    entry_points={
        "console_scripts": [
            f"{PROJECT_NAME}={PROJECT_NAME}.__main__:main"]
        },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Environment :: No Input/Output (Daemon)",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Networking :: Monitoring :: Hardware Watchdog",
        ],
    )
