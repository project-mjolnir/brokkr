#!/usr/bin/env python3
"""
Main-level brokkr entry point.
"""

# Standard library imports
import multiprocessing

# Local imports
import brokkr.utils.cli


def main():
    brokkr.utils.cli.main()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
