"""
Routines to write out collected status data to a CSV file.
"""

import csv
import datetime
import io
from pathlib import Path


def determine_output_filename(output_path):
    output_path = (Path(output_path)
                   / (str(datetime.datetime.utcnow().date()) + ".csv"))
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
