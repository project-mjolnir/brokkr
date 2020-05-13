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


def format_data(data=None, seperator="\n", include_raw=False):
    output_data_list = []
    for data_name, data_value in data.items():
        # Get key attributes to pretty-print
        value = getattr(data_value, "value", data_value)
        raw_value = getattr(data_value, "raw_value", None)
        uncertainty = getattr(data_value, "uncertainty", None)
        if getattr(data_value, "data_type", None):
            name = data_value.data_type.full_name
            unit = data_value.data_type.unit
        else:
            name = data_name.replace("_", " ").title()
            unit = None

        # Build list of values to print per data object
        data_componets = [f"{name}:", f"{value!s}"]
        if not getattr(data_value, "is_na", data_value == "NA"):
            if unit:
                data_componets.append(f"{unit}")
            if (uncertainty not in (None, False)
                    and not (isinstance(uncertainty, int)
                             and uncertainty == 1)):
                data_componets.append(f"+/-{uncertainty!s}")
                if unit:
                    data_componets.append(f"{unit}")
            if raw_value is not None and include_raw:
                data_componets.append(f"(Raw: {raw_value!r})")
        elif getattr(data_value, "value", data_value) != "NA":
            data_componets.append("(NA)")
        data_item = " ".join(data_componets)
        output_data_list.append(data_item)

    formatted_data = seperator.join(output_data_list)
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
    if not Path(output_path).is_absolute():
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
        "output_type": "data",
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
