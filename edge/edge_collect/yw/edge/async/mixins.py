import logging
from yw.edge.interface import BaseModbusClient
# from yw.bit_read_message import *
# from yw.bit_write_message import *
# from yw.register_read_message import *
# from yw.register_write_message import *
# from yw.diag_message import *
# from yw.file_message import *
# from yw.other_message import *
from yw.constants import Defaults

from yw.factory import ClientDecoder
from yw.transaction import ModbusSocketFramer


LOGGER = logging.getLogger(__name__)


class BaseAsyncModbusClient(BaseModbusClient):
    """
    This represents the base ModbusAsyncClient.
    """

    def __init__(self, framer=None, timeout=2, **kwargs):
        """ Initializes the framer module

        :param framer: The framer to use for the protocol. Default:
        ModbusSocketFramer
        :type framer: yw.transaction.ModbusSocketFramer
        """
        self._connected = False
        self._timeout = timeout

        super(BaseAsyncModbusClient, self).__init__(
            framer or ModbusSocketFramer(ClientDecoder()), **kwargs
        )


class AsyncModbusClientMixin(BaseAsyncModbusClient):
    """
    Async Modbus client mixing for UDP and TCP clients
    """
    def __init__(self, host="127.0.0.1", port=Defaults.Port, framer=None,
                 source_address=None, timeout=None, **kwargs):
        """
        Initializes a Modbus TCP/UDP asynchronous client
        :param host: Host IP address
        :param port: Port
        :param framer: Framer to use
        :param source_address: Specific to underlying client being used
        :param timeout: Timeout in seconds
        :param kwargs: Extra arguments
        """
        super(AsyncModbusClientMixin, self).__init__(framer=framer, **kwargs)
        self.host = host
        self.port = port
        self.source_address = source_address or ("", 0)
        self.timeout = timeout if timeout is not None else Defaults.Timeout


class AsyncModbusSerialClientMixin(BaseAsyncModbusClient):
    """
    Async Modbus Serial Client Mixing
    """
    def __init__(self, framer=None, port=None, **kwargs):
        """
        Initializes a Async Modbus Serial Client
        :param framer:  Modbus Framer
        :param port: Serial port to use
        :param kwargs: Extra arguments if any
        """
        super(AsyncModbusSerialClientMixin, self).__init__(framer=framer)
        self.port = port
        self.serial_settings = kwargs

