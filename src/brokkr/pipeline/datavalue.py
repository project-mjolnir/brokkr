"""
Reprisent of each measurement/observation/variable as a standard DataValue.
"""

# Local imports
from brokkr.config.main import CONFIG
import brokkr.utils.misc


class DataType(brokkr.utils.misc.AutoReprMixin):
    def __init__(
            self,
            name,
            conversion=True,
            binary_type=None,
            input_type=None,
            na_marker=CONFIG["general"]["na_marker"],
            full_name=None,
            unit=None,
            uncertainty=None,
            custom_attrs=None,
            **conversion_kwargs,
                ):
        self.name = name
        self.conversion = conversion
        self.binary_type = binary_type
        self.input_type = binary_type if input_type is None else input_type
        self.na_marker = na_marker
        self.conversion_kwargs = conversion_kwargs

        self.full_name = self.name if full_name is None else full_name
        self.unit = unit
        self.uncertainty = uncertainty

        if custom_attrs is not None:
            for attr_name, attr_value in custom_attrs.items():
                setattr(self, attr_name, attr_value)


class DataValue(brokkr.utils.misc.AutoReprMixin):
    def __init__(
            self,
            value,
            data_type,
            raw_value=None,
            uncertainty=None,
            is_na=None,
                ):
        try:
            data_type.name
        except AttributeError:
            self.data_type = DataType(**data_type)
        else:
            self.data_type = data_type

        self.value = value
        self.raw_value = self.value if raw_value is None else raw_value
        self.uncertainty = (
            self.data_type.uncertainty if uncertainty is None else uncertainty)

        if is_na is None:
            is_na = (self.value == self.data_type.na_marker)
        self.is_na = is_na

    def __str__(self):
        return str(self.value)
