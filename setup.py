#!/usr/bin/env python3
"""
Setup script for Brokkr, a scientific IoT sensor client.
"""

from pathlib import Path

import setuptools


PROJECT_NAME = "brokkr"


with open(Path(__file__).resolve().parent / "README.md",
          "r", encoding="utf-8") as readme_file:
    LONG_DESCRIPTION = readme_file.read()

VERSION = {}
with open(Path(__file__).resolve().parent
          / "src" / PROJECT_NAME / "_version.py",
          "r", encoding="utf-8") as version_file:
    exec(version_file.read(), VERSION)


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
        "pymodbus",
        "pyserial",
        "toml",
        ],
    entry_points={
        "console_scripts": [
            f"{PROJECT_NAME}={PROJECT_NAME}.__main__:main"]
        },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Environment :: No Input/Output (Daemon)",
        "Intended Audience :: Science/Research",
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
