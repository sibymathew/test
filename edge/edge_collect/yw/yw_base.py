"""
Contains base classes for modbus request/response/error packets
"""
"""
Custom Protocol was implemented for Series 3, Series 4 
Utilities were added to support this protocol, classes and interfaces 
"""
from yw.interfaces import Singleton
from yw.exceptions import NotImplementedException
from yw.constants import Defaults
from yw.yw_utilities import rtuFrameSize
from yw.compat import iteritems, int2byte, byte2int

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
import logging
_logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Base YW protocols
# --------------------------------------------------------------------------- #
class YWProtocol(object):
    """
    Base class for all Modbus messages


    """
    """
    :method:  custom implemented for YW scenarios  - Series 3, Series 4
    """

    def __init__(self, **kwargs):
        """ Initializes the base data for a modbus request """
        self.transaction_id = kwargs.get('transaction', Defaults.TransactionId)
        self.protocol_id = kwargs.get('protocol', Defaults.ProtocolId)
        self.unit_id = kwargs.get('unit', Defaults.UnitId)
        self.skip_encode = kwargs.get('skip_encode', False)
        self.check = 0x0000

    def encode(self):
        """ Encodes the message

        :raises: A not implemented exception
        """
        raise NotImplementedException()

    def decode(self, data):
        """ Decodes data part of the message.


        :raises: A not implemented exception
        """
        raise NotImplementedException()

    @classmethod
    def calculateRtuFrameSize(cls, buffer):
        """ Calculates the size of a PDU.


        :returns: The number of bytes in the PDU.
        """
        if hasattr(cls, '_rtu_frame_size'):
            return cls._rtu_frame_size
        elif hasattr(cls, '_rtu_byte_count_pos'):
            return rtuFrameSize(buffer, cls._rtu_byte_count_pos)
        else: raise NotImplementedException(
            "Cannot determine RTU frame size for %s" % cls.__name__)


class ModbusRequest(YWProtocol):
    """ Base class for a modbus request PDU """

    def __init__(self, **kwargs):
        """ Proxy to the lower level initializer """
        YWProtocol.__init__(self, **kwargs)

    def doException(self, exception):
        """ Builds an error response based on the function


        :raises: An exception response
        """
        exc = ExceptionResponse(self.function_code, exception)
        _logger.error(exc)
        return exc


class ModbusResponse(YWProtocol):
    """ Base class for a modbus response PDU


    """

    should_respond = True

    def __init__(self, **kwargs):
        """ Proxy to the lower level initializer """
        YWProtocol.__init__(self, **kwargs)

    def isError(self):
        """Checks if the error is a success or failure"""
        return self.function_code > 0x80


# --------------------------------------------------------------------------- #
# Exception PDU's
# --------------------------------------------------------------------------- #
class ModbusExceptions(Singleton):
    """
    An enumeration of the valid modbus exceptions
    """
    IllegalFunction         = 0x01
    IllegalAddress          = 0x02
    IllegalValue            = 0x03
    SlaveFailure            = 0x04
    Acknowledge             = 0x05
    SlaveBusy               = 0x06
    MemoryParityError       = 0x08
    GatewayPathUnavailable  = 0x0A
    GatewayNoResponse       = 0x0B

    @classmethod
    def decode(cls, code):
        """ Given an error code, translate it to a
        string error name.

        :param code: The code number to translate
        """
        values = dict((v, k) for k, v in iteritems(cls.__dict__)
            if not k.startswith('__') and not callable(v))
        return values.get(code, None)


class ExceptionResponse(ModbusResponse):
    """ Base class for a modbus exception PDU """
    ExceptionOffset = 0x80
    _rtu_frame_size = 5

    def __init__(self, function_code, exception_code=None, **kwargs):
        """ Initializes the modbus exception response


        """
        ModbusResponse.__init__(self, **kwargs)
        self.original_code = function_code
        self.function_code = function_code | self.ExceptionOffset
        self.exception_code = exception_code

    def encode(self):
        """ Encodes a modbus exception response

        :returns: The encoded exception packet
        """
        return int2byte(self.exception_code)

    def decode(self, data):
        """ Decodes a modbus exception response

        :param data: The packet data to decode
        """
        self.exception_code = byte2int(data[0])

    def __str__(self):
        """ Builds a representation of an exception response

        :returns: The string representation of an exception response
        """
        message = ModbusExceptions.decode(self.exception_code)
        parameters = (self.function_code, self.original_code, message)
        return "Exception Response(%d, %d, %s)" % parameters


class IllegalFunctionRequest(ModbusRequest):
    """

    This exception code is returned if the slave: does not implement the function code
    """
    ErrorCode = 1

    def __init__(self, function_code, **kwargs):
        """ Initializes a IllegalFunctionRequest


        """
        ModbusRequest.__init__(self, **kwargs)
        self.function_code = function_code

    def decode(self, data):
        """ This is here so this failure will run correctly


        """
        pass

    def execute(self, context):
        """ Builds an illegal function request error response


        :returns: The error response packet
        """
        return ExceptionResponse(self.function_code, self.ErrorCode)

# --------------------------------------------------------------------------- #
# Exported symbols
# --------------------------------------------------------------------------- #


__all__ = [
    'ModbusRequest', 'ModbusResponse', 'ModbusExceptions',
    'ExceptionResponse', 'IllegalFunctionRequest',
]

