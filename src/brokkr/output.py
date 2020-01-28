"""
Functions to write out collected monitoring data to a CSV file.
"""

# Standard library imports
import csv
import datetime
import io
import logging
from pathlib import Path

# Local imports
from brokkr.config.main import CONFIG
from brokkr.config.unit import UNIT_CONFIG


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
        prefix=CONFIG["general"]["name_prefix"],
        unit_number=UNIT_CONFIG["number"],
        ):
    output_path = (Path(output_path)
                   / ("{prefix}{unit_number}_{date!s}.csv".format(
                       prefix=prefix,
                       unit_number=unit_number,
                       date=datetime.datetime.utcnow().date())))
    return output_path


def write_line_csv(data, out_file, **csv_params):
    try:
        if isinstance(out_file, io.IOBase):
            close_file = False
            data_csv = out_file
        else:
            close_file = True
            data_csv = open(out_file, mode="a", encoding="utf-8", newline="")
        csv_params = {**CSV_PARAMS, **csv_params}
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
