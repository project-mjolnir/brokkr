"""
Functions to write out collected monitoring data to a CSV file.
"""

# Standard library imports
import csv
import datetime
import io
import logging
import os
from pathlib import Path

# Local imports
from brokkr.config.bootstrap import UNIT_CONFIG, METADATA_CONFIG
from brokkr.config.static import CONFIG


CSV_PARAMS = {
    "extrasaction": "ignore",
    "dialect": "unix",
    "delimiter": ",",
    "quoting": csv.QUOTE_MINIMAL,
    "strict": False,
    }


logger = logging.getLogger(__name__)


def determine_output_filename(
        output_path=CONFIG["monitor"]["output_path"],
        prefix=METADATA_CONFIG["name"],
        unit_number=UNIT_CONFIG["number"],
        ):
    output_path = (Path(output_path)
                   / ("{prefix}{unit_number}_{date!s}.csv".format(
                       prefix=prefix,
                       unit_number=unit_number,
                       date=datetime.datetime.utcnow().date())))
    return output_path


def write_line_csv(data, out_file, **csv_params):
    csv_params = {**CSV_PARAMS, **csv_params}
    try:
        if isinstance(out_file, io.IOBase):
            close_file = False
            data_csv = out_file
        else:
            close_file = True
            out_file = Path(out_file)
            logger.debug(
                "Ensuring output directory at %r", out_file.parent.as_posix())
            os.makedirs(out_file.parent, exist_ok=True)
            data_csv = open(out_file, mode="a", encoding="utf-8", newline="")
        csv_writer = csv.DictWriter(
            data_csv, fieldnames=data.keys(), **csv_params)
        if not data_csv.tell():
            csv_writer.writeheader()
        csv_writer.writerow(data)
        logger.debug("Monitoring data successfully written to CSV at %r",
                     out_file)
        return True
    except Exception as e:
        logger.error("%s writing monitoring data to local CSV at %r: %s",
                     type(e).__name__, out_file, e)
        logger.info("Error details:", exc_info=1)
        logger.info("Data details: %r", data)
        return False
    finally:
        if close_file:
            try:
                data_csv.close()
            except Exception as e:
                logger.warning("%s attempting to close monitoring CSV %r: %s",
                               type(e).__name__, out_file, e)
                logger.info("Error details:", exc_info=1)
