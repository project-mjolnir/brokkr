"""
Routines to write out collected status data to a CSV file.
"""

import csv
import io


def write_line_csv(data, file):
    try:
        if isinstance(file, io.IOBase):
            close_file = False
            data_csv = file
        else:
            close_file = True
            data_csv = open(file, mode="a", encoding="utf-8", newline="")
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
