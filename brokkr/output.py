"""
Routines to write out collected status data to a CSV file.
"""

# Standard library imports
import csv
import datetime
import io
from pathlib import Path

# Local imports
from config import CONFIG


def determine_output_filename(output_path=CONFIG["monitor"]["output_path"],
                              prefix=CONFIG["general"]["name_prefix"]):
    output_path = (Path(output_path)
                   / ("{prefix}{number}_{date!s}.csv".format(
                           prefix=prefix,
                           number=CONFIG["site"]["number"],
                           date=datetime.datetime.utcnow().date())))
    return output_path


def write_line_csv(data, out_file):
    try:
        if isinstance(out_file, io.IOBase):
            close_file = False
            data_csv = out_file
        else:
            close_file = True
            data_csv = open(out_file, mode="a", encoding="utf-8", newline="")
        csv_writer = csv.DictWriter(
            data_csv, fieldnames=data.keys(), extrasaction="ignore",
            dialect="unix", delimiter=",", quoting=csv.QUOTE_MINIMAL,
            strict=False)
        if not data_csv.tell():
            csv_writer.writeheader()
        csv_writer.writerow(data)
    finally:
        if close_file:
            try:
                data_csv.close()
            except Exception:
                pass
