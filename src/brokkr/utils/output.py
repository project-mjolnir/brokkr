"""
Functions to write out collected monitoring data to a CSV file.
"""

# Standard library imports
import datetime
import logging
from pathlib import Path

# Local imports
from brokkr.config.main import CONFIG
from brokkr.config.metadata import METADATA
from brokkr.config.unit import UNIT_CONFIG
import brokkr.utils.misc


LOGGER = logging.getLogger(__name__)


def format_data(data=None, seperator="\n"):
    data_list = [
        "{key}: {value!s}".format(
            key=key.replace("_", " ").title(), value=value)
        for key, value in data.items()]
    formatted_data = seperator.join(data_list) + "\n"
    return formatted_data


def render_output_filename(
        output_path=Path(),
        filename_template=None,
        extension=None,
        **filename_kwargs,
        ):
    if extension:
        extension.strip(".")
    if filename_template is None:
        filename_template = CONFIG["general"]["output_filename_client"]

    # Add master output path to output path if is relative
    if not output_path.is_absolute():
        output_path_root = Path(
            CONFIG["general"]["output_path_client"].as_posix().format(
                system_name=METADATA["name"]))
        if output_path_root:
            output_path = output_path_root / output_path
    output_path = brokkr.utils.misc.convert_path(output_path)

    system_prefix = CONFIG["general"]["system_prefix"]
    if not system_prefix:
        system_prefix = METADATA["name"]

    filename_kwargs_default = {
        "system_name": METADATA["name"],
        "system_prefix": system_prefix,
        "unit_number": UNIT_CONFIG["number"],
        "utc_datetime": datetime.datetime.utcnow().date(),
        "utc_date": datetime.datetime.utcnow().date(),
        "utc_time": datetime.datetime.utcnow().time(),
        "local_datetime": datetime.datetime.now().date(),
        "local_date": datetime.datetime.now().date(),
        "local_time": datetime.datetime.now().time(),
        }
    if extension:
        filename_kwargs_default["extension"] = extension
    all_filename_kwargs = {**filename_kwargs_default, **filename_kwargs}
    LOGGER.debug("Kwargs for output filename: %s", all_filename_kwargs)

    rendered_filename = filename_template.format(**all_filename_kwargs)
    output_path = (Path(output_path) / rendered_filename)

    # Add file extension if it has not yet been affixed and is passed
    if extension is not None and not output_path.suffix:
        output_path = output_path.with_suffix("." + extension)
    return output_path
