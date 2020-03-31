"""
Data input from devices using the Modbus protocol.
"""

# Standard library imports
import struct

# Third party imports
import pymodbus.client.sync
import pymodbus.pdu
import serial.tools.list_ports

# Local imports
import brokkr.pipeline.baseinput
import brokkr.utils.misc
import brokkr.utils.ports


MODBUS_COIL_TYPE = "?"
MODBUS_REGISTER_TYPE = "H"

MODBUS_SERIAL_KWARGS_DEFAULT = {
    "method": "rtu",
    "strict": False,
    "timeout": 2,
    }


class ModbusInput(brokkr.pipeline.baseinput.ValueInputStep):
    def __init__(
            self,
            start_address=0x0000,
            unit=1,
            modbus_client="ModbusSerialClient",
            modbus_command="read_holding_registers",
            modbus_kwargs=None,
            datatype_default_kwargs=None,
            **value_input_kwargs):
        """
        Class to read data from an attached Modbus device.

        Parameters
        ----------
        start_address : int or hex, optional
           Register or coil start offset (PDU address). The default is 0x0000.
        unit : int or hex, optional
            Unit ID to request data from. The default is 1.
        modbus_params
            Parameters to pass to the modbus client being used.
            If modbus_client is serial, will use sensible defaults.

        """
        if datatype_default_kwargs is None:
            datatype_default_kwargs = {}
        self._raw_type = (
            MODBUS_REGISTER_TYPE if "register" in modbus_command
            else MODBUS_COIL_TYPE)
        super().__init__(
            binary_decoder=True,
            datatype_default_kwargs={
                **{"input_type": self._raw_type}, **datatype_default_kwargs},
            **value_input_kwargs)

        self._start_address = start_address
        self._unit = unit

        self._modbus_class = getattr(pymodbus.client.sync, modbus_client)
        self._modbus_function = modbus_command
        self._modbus_kwargs = {} if modbus_kwargs is None else modbus_kwargs

    def _handle_failed_connect(self, error, modbus_client, port_object):
        # pylint: disable=unused-argument, no-self-use
        return False

    def _get_responce_data(self, modbus_client, port_object=None):
        if self._raw_type == MODBUS_REGISTER_TYPE:
            responce_count = (
                self.decoder.packet_size
                // struct.calcsize("!" + MODBUS_REGISTER_TYPE))
        else:
            responce_count = len(self.data_types)
        try:
            responce_data = getattr(modbus_client, self._modbus_function)(
                address=self._start_address,
                count=responce_count,
                unit=self._unit)
            # If modbus data is an exception, log it and return None
            if isinstance(responce_data, BaseException):
                raise responce_data
            if isinstance(responce_data, pymodbus.pdu.ExceptionResponse):
                self.logger.error("Error reading Modbus data for %s",
                                  port_object)
                self.log_helper.log(error=responce_data, client=modbus_client,
                                    port=port_object)
                return None
        # Catch and log errors reading modbus data
        except Exception as e:
            self.logger.error("%s reading Modbus data for %s: %s",
                              type(e).__name__, port_object, e)
            self.log_helper.log(client=modbus_client, port=port_object)
            return None
        finally:
            self.logger.debug("Closing Modbus client connection")
            try:
                modbus_client.close()
            # Catch and log any errors closing the modbus connection
            except AttributeError:
                self.logger.debug(
                    "Modbus client of type %r lacks close method; skipping",
                    brokkr.utils.misc.get_full_class_name(modbus_client))
            except Exception as e:
                self.logger.warning("%s closing modbus device at %s: %s",
                                    type(e).__name__, port_object, e)
                self.log_helper.log(client=modbus_client, port=port_object)

        return responce_data

    def _read_modbus_data(self, port_object=None):
        """
        Read data from an attached Modbus device.

        Parameters
        ----------
        None.

        Returns
        -------
        responce_data : pymodbbus Responce
            Pymodbus data object reprisenting the read data,
            or None if no data could be read and an exception was logged.

        """
        # Read data over Modbus
        modbus_client = self._modbus_class(**self._modbus_kwargs)
        self.log_helper.log("debug", error=False, client=modbus_client)
        try:
            try:
                connect_successful = modbus_client.connect()
            # If connecting to the device fails due to an OS-level problem
            # e.g. being disconnected previously, attempt to reset it
            except OSError as e:
                connect_successful = self._handle_failed_connect(
                    error=e,
                    port_object=port_object,
                    modbus_client=modbus_client,
                    )
                if not connect_successful:
                    raise
            if connect_successful:
                modbus_data = self._get_responce_data(
                    modbus_client=modbus_client)
            else:
                # Raise an error if connect not successful
                self.logger.error(
                    "Error reading modbus data: Cannot connect to device %s",
                    port_object)
                self.log_helper.log(
                    error=False, client=modbus_client, port=port_object)
                return None
            self.logger.debug("Responce data: %r",
                              getattr(modbus_data, "__dict__", None))
        except Exception as e:
            self.logger.error("%s connecting to Modbus device at %s: %s",
                              type(e).__name__, port_object, e)
            self.log_helper.log(client=modbus_client, port=port_object)
            return None

        return modbus_data

    def read_raw_data(self, input_data=None):
        modbus_data = self._read_modbus_data()

        if modbus_data is not None:
            try:
                if self._raw_type == MODBUS_REGISTER_TYPE:
                    raw_data = modbus_data.registers
                else:
                    raw_data = modbus_data.bits
            except Exception:
                raw_data = None
                self.logger.error(
                    "Could not get Modbus responce data from obj %r",
                    modbus_data)
                self.log_helper.log(modbus_data=modbus_data)
            else:
                # Convert uint16s or bools back to packed bytes
                if self._raw_type == MODBUS_COIL_TYPE:
                    # Coil responce length is rounded up to the nearest byte
                    raw_data = raw_data[:len(self.data_types)]

                struct_format = "!" + self._raw_type * len(raw_data)
                raw_data = struct.pack(struct_format, *raw_data)
                self.logger.debug(
                    "Converted Modbus responce to struct of format %r: %r",
                    struct_format, raw_data)
        else:
            raw_data = None

        return raw_data


class ModbusSerialInput(ModbusInput):
    def __init__(
            self,
            modbus_client="ModbusSerialClient",
            serial_port=None,
            serial_pids=None,
            try_usb_reset=False,
            **modbus_kwargs):
        """
        Class to read data from an attached Modbus serial (RTU/ASCII) device.

        Parameters
        ----------
        serial_port : str or None, optional
            Serial port device to use. The default is None, which uses the
            first device matching the PID(s), or else the first detected.
        serial_pids : iterable of int, optional
            If serial port device not specified, collection of USB PIDs
            to look for to find the expected USB to serial adapter.
            By default, doesn't look for any and instead just picks the first.

        """
        super().__init__(modbus_client=modbus_client, **modbus_kwargs)

        self._modbus_kwargs = {**MODBUS_SERIAL_KWARGS_DEFAULT,
                               **self._modbus_kwargs}
        self._serial_port = serial_port
        self._serial_pids = [] if serial_pids is None else serial_pids
        self._try_usb_reset = try_usb_reset

    def _handle_failed_connect(
            self, error, modbus_client=None, port_object=None):
        if not self._try_usb_reset:
            return False
        self.logger.warning(
            "%s connecting to Modbus device at %s; attempting USB reset",
            type(error).__name__, port_object)

        reset_success = brokkr.utils.ports.reset_usb_port(port_object)
        if not reset_success:
            return False
        connect_successful = modbus_client.connect()
        self.logger.warning("Reset Modbus device at %s; original error %s: %s",
                            port_object, type(error).__name__, error)
        self.log_helper.log(client=modbus_client, port=port_object)

        return connect_successful

    def _read_modbus_data(self, port_object=None):
        # Get serial port to use from port list
        if not port_object:
            port_list = serial.tools.list_ports.comports()
            port_object = brokkr.utils.ports.get_serial_port(
                port_list=port_list,
                port=self._serial_port,
                pids=self._serial_pids,
                )
        if not port_object:
            return None

        self._modbus_kwargs["port"] = port_object.device
        modbus_data = super()._read_modbus_data(port_object=port_object)
        return modbus_data


class ModbusEthernetInput(ModbusInput):
    def __init__(
            self,
            modbus_client="ModbusTcpClient",
            **modbus_kwargs):
        """
        Class to read data from a Modbus Ethernet (TCP/UDP/TLS) device.
        """
        super().__init__(modbus_client=modbus_client, **modbus_kwargs)

    def _read_modbus_data(self, port_object=None):
        # Get port object for use in logging
        if not port_object:
            port_object = {
                "host": self._modbus_kwargs.get("host", "127.0.0.1"),
                "port": self._modbus_kwargs.get("port", "Default"),
                }

        modbus_data = super()._read_modbus_data(port_object=port_object)
        return modbus_data
