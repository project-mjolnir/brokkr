"""
Routines to write out collected status data to a CSV file.
"""

# Standard library imports
import csv
import datetime
import io
import logging
from pathlib import Path

# Local imports
from config import CONFIG


logger = logging.getLogger(__name__)


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
        logger.debug("Monitoring data successfully written to CSV")
        return True
    except Exception as e:
        logger.error("%s writing monitoring data to local CSV at %s: %s",
                     type(e).__name__, out_file, e)
        logger.info("Details:", exc_info=1)
        logger.info("Attempted to write data: %s", data)
        return False
    finally:
        if close_file:
            try:
                data_csv.close()
            except Exception as e:
                logger.warning("%s attempting to close monitoring CSV %s: %s",
                               type(e).__name__, out_file, e)
                logger.info("Details:", exc_info=1)
