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
from brokkr.config.main import CONFIG
from brokkr.config.metadata import METADATA
from brokkr.config.unit import UNIT_CONFIG
import brokkr.utils.misc


CSV_PARAMS = {
    "extrasaction": "ignore",
    "dialect": "unix",
    "delimiter": ",",
    "quoting": csv.QUOTE_MINIMAL,
    "strict": False,
    }

LOGGER = logging.getLogger(__name__)


def render_output_filename(
        output_path,
        filename=CONFIG["general"]["output_filename_client"],
        **filename_args,
        ):
    # Add master output path to output path if is relative
    output_path_root = Path(CONFIG["general"]["output_path_client"].as_posix()
                            .format(system_name=METADATA["name"]))
    if not output_path.is_absolute() and output_path_root:
        output_path = output_path_root / output_path
    output_path = brokkr.utils.misc.convert_path(output_path)

    system_prefix = CONFIG["general"]["system_prefix"]
    if not system_prefix:
        system_prefix = METADATA["name"]

    filename_args_default = {
        "system_name": METADATA["name"],
        "system_prefix": system_prefix,
        "unit_number": UNIT_CONFIG["number"],
        "utc_date": datetime.datetime.utcnow().date(),
        }
    all_filename_args = {**filename_args_default, **filename_args}
    LOGGER.debug("Args for output filename: %s", all_filename_args)

    rendered_filename = filename.format(**all_filename_args)
    output_path = (Path(output_path) / rendered_filename)
    return output_path


def write_line_csv(data, out_file, **csv_params):
    csv_params = {**CSV_PARAMS, **csv_params}
    try:
        if isinstance(out_file, io.IOBase):
            close_file = False
            data_csv = out_file
            out_file_path = out_file.name.replace(os.sep, "/")
        else:
            close_file = True
            out_file = Path(out_file)
            out_file_path = out_file.as_posix()
            LOGGER.debug(
                "Ensuring output directory at %r", out_file.parent.as_posix())
            os.makedirs(out_file.parent, exist_ok=True)
            data_csv = open(out_file, mode="a", encoding="utf-8", newline="")
        csv_writer = csv.DictWriter(
            data_csv, fieldnames=data.keys(), **csv_params)
        if not data_csv.tell():
            csv_writer.writeheader()
        csv_writer.writerow(data)
        LOGGER.debug("Data successfully written to CSV at %r", out_file_path)
        return True
    except Exception as e:
        LOGGER.error("%s writing output data to local CSV at %r: %s",
                     type(e).__name__, out_file, e)
        LOGGER.info("Error details:", exc_info=True)
        LOGGER.info("Data details: %r", data)
        return False
    finally:
        if close_file:
            try:
                data_csv.close()
            except Exception as e:
                LOGGER.warning("%s attempting to close output CSV %r: %s",
                               type(e).__name__, out_file, e)
                LOGGER.info("Error details:", exc_info=True)
