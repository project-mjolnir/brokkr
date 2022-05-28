"""
Functions to write out collected monitoring data to a CSV file.
"""

# Standard library imports
import datetime
import logging
import os.path
from pathlib import Path
import shutil
import subprocess

# Local imports
from brokkr.config.main import CONFIG
from brokkr.config.metadata import METADATA
from brokkr.config.unit import UNIT_CONFIG
import brokkr.utils.misc


LOGGER = logging.getLogger(__name__)

MOUNT_TIMEOUT_S = 10


def apply_item_limit(value, item_limit):
    try:
        value = str(value[:item_limit])
    except TypeError:
        value = str(value)[:item_limit]
    return value


def format_data(
        data=None,
        seperator="\n",
        include_raw=False,
        item_limit=None,
        ):
    output_data_list = []
    for data_name, data_value in data.items():
        # Get key attributes to pretty-print
        value = getattr(data_value, "value", data_value)
        raw_value = getattr(data_value, "raw_value", None)
        if item_limit is not None:
            value = apply_item_limit(value, item_limit)
            raw_value = apply_item_limit(raw_value, item_limit)
        uncertainty = getattr(data_value, "uncertainty", None)
        if getattr(data_value, "data_type", None):
            name = data_value.data_type.full_name
            unit = data_value.data_type.unit
        else:
            name = data_name.replace("_", " ").title()
            unit = None

        # Build list of values to print per data object
        data_componets = [f"{name}:", f"{value}"]
        if not getattr(data_value, "is_na", data_value == "NA"):
            # Add details for data that is not NA
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
        # pylint: disable-next=confusing-consecutive-elif
        elif getattr(data_value, "value", data_value) != "NA":
            # Mark data as NA if is_na set but doesn't have a value of NA
            data_componets.append("(NA)")
        data_item = " ".join(data_componets)
        output_data_list.append(data_item)

    formatted_data = seperator.join(output_data_list)
    return formatted_data


def find_drives(drive_glob, base_path, filename_kwargs=None):
    if filename_kwargs is None:
        filename_kwargs = {}

    base_path = brokkr.utils.misc.convert_path(
        base_path.format(**filename_kwargs))
    drive_glob = drive_glob.format(**filename_kwargs)
    found_drives = [drive for drive in base_path.glob(drive_glob)
                    if not drive.is_dir() or os.path.ismount(drive)]
    LOGGER.debug("Found drives: %r",
                 [drive.as_posix() for drive in found_drives])
    return found_drives


def mount_drives(
        mount_glob, base_path, current_drives, filename_kwargs=None):
    if filename_kwargs is None:
        filename_kwargs = {}

    mounted_drives = []
    mounted_drive_names = [drive.name for drive in current_drives]
    LOGGER.debug("Currently mounted drive names: %r", mounted_drive_names)
    LOGGER.debug("Checking drives to mount")
    drives_to_mount = find_drives(drive_glob=mount_glob,
                                  base_path=base_path,
                                  filename_kwargs=filename_kwargs)

    for drive_to_mount in drives_to_mount:
        if drive_to_mount.name not in mounted_drive_names:
            mount_command = ["udisksctl", "mount", "--no-user-interaction",
                             "-b", str(drive_to_mount)]
            LOGGER.debug(
                "Drive %s not in mounted drives, running mount command %r",
                drive_to_mount.as_posix(), mount_command)
            try:
                subprocess.run(
                    mount_command, check=True, timeout=MOUNT_TIMEOUT_S)
            except Exception as e:
                LOGGER.error("%s mounting drive %s with command %r: %s",
                             type(e).__name__, drive_to_mount.as_posix(),
                             " ".join(mount_command), e)
                LOGGER.info("Error details:", exc_info=True)
            else:
                mounted_drives.append(drive_to_mount)

    if mounted_drives:
        LOGGER.info("Mounted drives: %r",
                    [drive.as_posix() for drive in mounted_drives])
    else:
        LOGGER.debug("No drives to mount")

    return mounted_drives


def select_drive(
        canidate_drives,
        select_criteria,
        select_descending=False,
        min_free_gb=1,
        ):
    disk_usage_attributes = {"total", "used", "free"}
    supported_criteria = {"name", *disk_usage_attributes}

    if select_criteria == "name":
        sorted_drives = sorted(canidate_drives)
    elif select_criteria in disk_usage_attributes:
        sorted_drives = [(canidate_drive, shutil.disk_usage(canidate_drive))
                         for canidate_drive in canidate_drives]
        sorted_drives = sorted(
            sorted_drives, key=lambda tup: getattr(tup[1], select_criteria))
    else:
        raise ValueError(
            f"Select criteria {select_criteria} not {supported_criteria}")

    if select_descending:
        sorted_drives = reversed(sorted_drives)

    drive_path = None
    for drive_path in sorted_drives:
        if select_criteria in disk_usage_attributes:
            free_space = drive_path[1].free
            drive_path = drive_path[0]
        else:
            free_space = shutil.disk_usage(drive_path).free
        if free_space >= (min_free_gb * 1e9):
            break
    else:
        raise RuntimeError("All drives full!")

    return drive_path


def get_output_drive(
        drive_glob,
        base_path="/media/{current_user}",
        mount_glob=None,
        mount_base_path="/dev/disk/by-label",
        fallback_path=None,
        select_criteria="name",
        select_descending=False,
        min_free_gb=1,
        filename_kwargs=None,
        ):
    if filename_kwargs is None:
        filename_kwargs = {}
    if mount_glob is True:
        mount_glob = drive_glob

    LOGGER.debug("Finding mounted drives")
    canidate_drives = find_drives(drive_glob=drive_glob,
                                  base_path=base_path,
                                  filename_kwargs=filename_kwargs)

    if mount_glob is not None:
        mounted_drives = mount_drives(mount_glob=mount_glob,
                                      base_path=mount_base_path,
                                      current_drives=canidate_drives,
                                      filename_kwargs=filename_kwargs)
        if mounted_drives:
            LOGGER.debug("Rescanning for mounted drives")
            canidate_drives = find_drives(drive_glob=drive_glob,
                                          base_path=base_path,
                                          filename_kwargs=filename_kwargs)

    if not canidate_drives:
        if fallback_path is not None:
            drive_path = brokkr.utils.misc.convert_path(
                fallback_path.format(**filename_kwargs))
            LOGGER.info("No drives found, falling back to %s",
                        drive_path.as_posix())
        else:
            raise RuntimeError(
                f"No drives found at {base_path!s} matching {drive_glob}")
    elif len(canidate_drives) == 1:
        drive_path = canidate_drives[0]
    else:
        drive_path = select_drive(canidate_drives,
                                  select_criteria=select_criteria,
                                  select_descending=select_descending,
                                  min_free_gb=min_free_gb)

    return drive_path


def render_output_filename(
        output_path=Path(),
        filename_template=None,
        extension=None,
        drive_kwargs=None,
        **filename_kwargs,
        ):
    if filename_template is None:
        filename_template = CONFIG["general"]["output_filename_client"]
    if extension:
        extension = extension.strip(".")
    if drive_kwargs is None:
        drive_kwargs = {}

    # Get system profix with fallback
    system_prefix = CONFIG["general"]["system_prefix"]
    if not system_prefix:
        system_prefix = METADATA["name"]

    filename_kwargs_default = {
        "system_name": METADATA["name"],
        "system_prefix": system_prefix,
        "unit_number": UNIT_CONFIG["number"],
        "utc_datetime": datetime.datetime.utcnow(),
        "utc_date": datetime.datetime.utcnow().date(),
        "utc_time": datetime.datetime.utcnow().time(),
        "local_datetime": datetime.datetime.now(),
        "local_date": datetime.datetime.now().date(),
        "local_time": datetime.datetime.now().time(),
        "current_ms": datetime.datetime.utcnow().microsecond // 1000,
        "output_type": "data",
        "current_user": brokkr.utils.misc.get_actual_username(),
        }
    if extension:
        filename_kwargs_default["extension"] = extension
    all_filename_kwargs = {**filename_kwargs_default, **filename_kwargs}
    LOGGER.debug("Kwargs for output filename: %s", all_filename_kwargs)

    # Construct path and get drives
    if drive_kwargs.get("drive_glob", None) is not None:
        drive_path = get_output_drive(
            filename_kwargs=all_filename_kwargs, **drive_kwargs)
        LOGGER.debug("Selected drive: %s", drive_path.as_posix())
        all_filename_kwargs["drive_path"] = str(drive_path)

    # Add master output path to output path if is relative
    output_path = Path(output_path.format(**all_filename_kwargs))
    if not output_path.is_absolute():
        output_path_root = Path(
            CONFIG["general"]["output_path_client"].as_posix().format(
                system_name=METADATA["name"]))
        if output_path_root:
            output_path = output_path_root / output_path
    output_path = brokkr.utils.misc.convert_path(output_path)

    rendered_filename = filename_template.format(**all_filename_kwargs)
    output_path = (Path(output_path) / rendered_filename)

    # Add file extension if it has not yet been affixed and is passed
    if extension is not None and not output_path.suffix:
        output_path = output_path.with_suffix("." + extension)

    return output_path
