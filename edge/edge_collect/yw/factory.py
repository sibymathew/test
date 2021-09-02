"""
Modbus Request/Response Decoder Factories
-------------------------------------------


Implementation is extensively customized to support VFD RTU so to read multiple registers in parallel.

"""

from yw.yw_base import IllegalFunctionRequest
from yw.yw_base import ExceptionResponse
from yw.yw_base import ModbusRequest, ModbusResponse
from yw.yw_base import ModbusExceptions as ecode
from yw.interfaces import IModbusDecoder
from yw.exceptions import ModbusException, MessageRegisterException
from yw.bit_read_message import *
from yw.bit_write_message import *
from yw.diag_message import *
from yw.file_message import *
from yw.other_message import *
from yw.mei_message import *
from yw.register_read_message import *
from yw.register_write_message import *
from yw.compat import byte2int


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
import logging
_logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Server Decoder
# --------------------------------------------------------------------------- #
class ServerDecoder(IModbusDecoder):
    """ Request Message Factory (Server)

    To add more implemented functions, simply add them to the list
    """
    __function_table = [
            ReadYWRegistersRequest,
            ReadDiscreteInputsRequest,
            ReadInputRegistersRequest,
            ReadCoilsRequest,
            WriteMultipleCoilsRequest,
            WriteMultipleRegistersRequest,
            WriteSingleRegisterRequest,
            WriteSingleCoilRequest,
            ReadWriteMultipleRegistersRequest,
            DiagnosticStatusRequest,
            ReadExceptionStatusRequest,
            GetCommEventCounterRequest,
            GetCommEventLogRequest,
            ReportSlaveIdRequest,
            ReadFileRecordRequest,
            WriteFileRecordRequest,
            MaskWriteRegisterRequest,
            ReadFifoQueueRequest,
            ReadDeviceInformationRequest,
    ]
    __sub_function_table = [
            ReturnQueryDataRequest,
            RestartCommunicationsOptionRequest,
            ReturnDiagnosticRegisterRequest,
            ChangeAsciiInputDelimiterRequest,
            ForceListenOnlyModeRequest,
            ClearCountersRequest,
            ReturnBusMessageCountRequest,
            ReturnBusCommunicationErrorCountRequest,
            ReturnBusExceptionErrorCountRequest,
            ReturnSlaveMessageCountRequest,
            ReturnSlaveNoResponseCountRequest,
            ReturnSlaveNAKCountRequest,
            ReturnSlaveBusyCountRequest,
            ReturnSlaveBusCharacterOverrunCountRequest,
            ReturnIopOverrunCountRequest,
            ClearOverrunCountRequest,
            GetClearModbusPlusRequest,
            ReadDeviceInformationRequest,
    ]

    def __init__(self):
        """ Initializes the client lookup tables
        """
        functions = set(f.function_code for f in self.__function_table)
        self.__lookup = dict([(f.function_code, f) for f in self.__function_table])
        self.__sub_lookup = dict((f, {}) for f in functions)
        for f in self.__sub_function_table:
            self.__sub_lookup[f.function_code][f.sub_function_code] = f

    def decode(self, message):
        """ Wrapper to decode a request packet


        :return: The decoded modbus message or None if error
        """
        try:
            return self._helper(message)
        except ModbusException as er:
            _logger.warning("Unable to decode request %s" % er)
        return None

    def lookupPduClass(self, function_code):
        """ Use `function_code` to determine the class of the PDU.

        :returns: The class of the PDU that has a matching `function_code`.
        """
        return self.__lookup.get(function_code, ExceptionResponse)

    def _helper(self, data):
        """

        :returns: The decoded request or illegal function request object
        """
        function_code = byte2int(data[0])
        request = self.__lookup.get(function_code, lambda: None)()
        if not request:
            _logger.debug("Factory Request[%d]" % function_code)
            request = IllegalFunctionRequest(function_code)
        else:
            fc_string = "%s: %s" % (
                str(self.__lookup[function_code]).split('.')[-1].rstrip(
                    "'>"),
                function_code
            )
            _logger.debug("Factory Request[%s]" % fc_string)
        request.decode(data[1:])

        if hasattr(request, 'sub_function_code'):
            lookup = self.__sub_lookup.get(request.function_code, {})
            subtype = lookup.get(request.sub_function_code, None)
            if subtype: request.__class__ = subtype

        return request
    
    def register(self, function=None):
        """
        Registers a function and sub function class , Custom function class to register
        :return:
        """
        if function and not issubclass(function, ModbusRequest):
            raise MessageRegisterException("'{}' is Not a valid Modbus Message"
                                           ". Class needs to be derived from "
                                           "`yw.yw_base.ModbusRequest` "
                                           "".format(
                function.__class__.__name__
            ))
        self.__lookup[function.function_code] = function
        if hasattr(function, "sub_function_code"):
            if function.function_code not in self.__sub_lookup:
                self.__sub_lookup[function.function_code] = dict()
            self.__sub_lookup[function.function_code][
                function.sub_function_code] = function


# --------------------------------------------------------------------------- #
# Client Decoder
# --------------------------------------------------------------------------- #
class ClientDecoder(IModbusDecoder):
    """ Response Message Factory (Client)

    To add more implemented functions, simply add them to the list
    """
    """
    YW reisters were customized according to VFD scenarios
    """
    __function_table = [
            ReadYWRegistersResponse,
            ReadDiscreteInputsResponse,
            ReadInputRegistersResponse,
            ReadCoilsResponse,
            WriteMultipleCoilsResponse,
            WriteMultipleRegistersResponse,
            WriteSingleRegisterResponse,
            WriteSingleCoilResponse,
            ReadWriteMultipleRegistersResponse,
            DiagnosticStatusResponse,
            ReadExceptionStatusResponse,
            GetCommEventCounterResponse,
            GetCommEventLogResponse,
            ReportSlaveIdResponse,
            ReadFileRecordResponse,
            WriteFileRecordResponse,
            MaskWriteRegisterResponse,
            ReadFifoQueueResponse,
            ReadDeviceInformationResponse,
    ]
    __sub_function_table = [
            ReturnQueryDataResponse,
            RestartCommunicationsOptionResponse,
            ReturnDiagnosticRegisterResponse,
            ChangeAsciiInputDelimiterResponse,
            ForceListenOnlyModeResponse,
            ClearCountersResponse,
            ReturnBusMessageCountResponse,
            ReturnBusCommunicationErrorCountResponse,
            ReturnBusExceptionErrorCountResponse,
            ReturnSlaveMessageCountResponse,
            ReturnSlaveNoReponseCountResponse,
            ReturnSlaveNAKCountResponse,
            ReturnSlaveBusyCountResponse,
            ReturnSlaveBusCharacterOverrunCountResponse,
            ReturnIopOverrunCountResponse,
            ClearOverrunCountResponse,
            GetClearModbusPlusResponse,
            ReadDeviceInformationResponse,
    ]

    def __init__(self):
        """ Initializes the client lookup tables
        """
        functions = set(f.function_code for f in self.__function_table)
        self.__lookup = dict([(f.function_code, f)
                              for f in self.__function_table])
        self.__sub_lookup = dict((f, {}) for f in functions)
        for f in self.__sub_function_table:
            self.__sub_lookup[f.function_code][f.sub_function_code] = f

    def lookupPduClass(self, function_code):
        """ Use `function_code` to determine the class of the PDU.


        :returns: The class of the PDU that has a matching `function_code`.
        """
        return self.__lookup.get(function_code, ExceptionResponse)

    def decode(self, message):
        """ Wrapper to decode a response packet

        :param message: The raw packet to decode
        :return: The decoded modbus message or None if error
        """
        try:
            return self._helper(message)
        except ModbusException as er:
            _logger.error("Unable to decode response %s" % er)

        except Exception as ex:
            _logger.error(ex)
        return None

    def _helper(self, data):
        """
        This factory is used to generate the correct response packet to decode
        :returns: The decoded request or an exception response object
        """
        fc_string = function_code = byte2int(data[0])
        if function_code in self.__lookup:
            fc_string = "%s: %s" % (
                str(self.__lookup[function_code]).split('.')[-1].rstrip("'>"),
                function_code
            )
        _logger.debug("Factory Response[%s]" % fc_string)
        response = self.__lookup.get(function_code, lambda: None)()
        if function_code > 0x80:
            code = function_code & 0x7f  # strip error portion
            response = ExceptionResponse(code, ecode.IllegalFunction)
        if not response:
            raise ModbusException("Unknown response %d" % function_code)
        response.decode(data[1:])

        if hasattr(response, 'sub_function_code'):
            lookup = self.__sub_lookup.get(response.function_code, {})
            subtype = lookup.get(response.sub_function_code, None)
            if subtype: response.__class__ = subtype

        return response

    def register(self, function=None, sub_function=None, force=False):
        """
        Registers a function and sub function class with the decoder

        :return:
        """
        """
        YW reisters were customized according to VFD scenarios
        """
        if function and not issubclass(function, ModbusResponse):
            raise MessageRegisterException("'{}' is Not a valid Modbus Message"
                                           ". Class needs to be derived from "
                                           "`yw.yw_base.ModbusResponse` "
                                           "".format(
                function.__class__.__name__
            ))
        self.__lookup[function.function_code] = function
        if hasattr(function, "sub_function_code"):
            if function.function_code not in self.__sub_lookup:
                self.__sub_lookup[function.function_code] = dict()
            self.__sub_lookup[function.function_code][
                function.sub_function_code] = function

# --------------------------------------------------------------------------- #
# Series 3 Series 4 VFD  Decoder
# --------------------------------------------------------------------------- #
class VFDDecoder(IModbusDecoder):
    """ Response Message Factory (Client)

    To add more implemented functions, simply add them to the list
    """
    """
    YW reisters were customized according to VFD scenarios
    """
    __function_table = [
            ReadYWRegistersResponse,
            ReadDiscreteInputsResponse,
            ReadInputRegistersResponse,
            ReadCoilsResponse,
            WriteMultipleCoilsResponse,
            WriteMultipleRegistersResponse,
            WriteSingleRegisterResponse,
            WriteSingleCoilResponse,
            ReadWriteMultipleRegistersResponse,
            DiagnosticStatusResponse,
            ReadExceptionStatusResponse,
            GetCommEventCounterResponse,
            GetCommEventLogResponse,
            ReportSlaveIdResponse,
            ReadFileRecordResponse,
            WriteFileRecordResponse,
            MaskWriteRegisterResponse,
            ReadFifoQueueResponse,
            ReadDeviceInformationResponse,
    ]
    __sub_function_table = [
            ReturnQueryDataResponse,
            RestartCommunicationsOptionResponse,
            ReturnDiagnosticRegisterResponse,
            ChangeAsciiInputDelimiterResponse,
            ForceListenOnlyModeResponse,
            ClearCountersResponse,
            ReturnBusMessageCountResponse,
            ReturnBusCommunicationErrorCountResponse,
            ReturnBusExceptionErrorCountResponse,
            ReturnSlaveMessageCountResponse,
            ReturnSlaveNoReponseCountResponse,
            ReturnSlaveNAKCountResponse,
            ReturnSlaveBusyCountResponse,
            ReturnSlaveBusCharacterOverrunCountResponse,
            ReturnIopOverrunCountResponse,
            ClearOverrunCountResponse,
            GetClearModbusPlusResponse,
            ReadDeviceInformationResponse,
    ]

    def __init__(self):
        """ Initializes the client lookup tables
        """
        functions = set(f.function_code for f in self.__function_table)
        self.__lookup = dict([(f.function_code, f)
                              for f in self.__function_table])
        self.__sub_lookup = dict((f, {}) for f in functions)
        for f in self.__sub_function_table:
            self.__sub_lookup[f.function_code][f.sub_function_code] = f

    def lookupPduClass(self, function_code):
        """ Use `function_code` to determine the class of the PDU.

        :param function_code: The function code specified in a frame.
        :returns: The class of the PDU that has a matching `function_code`.
        """
        return self.__lookup.get(function_code, ExceptionResponse)

    def decode(self, message):
        """ Wrapper to decode a response packet

        :param message: The raw packet to decode
        :return: The decoded modbus message or None if error
        """
        try:
            return self._helper(message)
        except ModbusException as er:
            _logger.error("Unable to decode response %s" % er)

        except Exception as ex:
            _logger.error(ex)
        return None

    def _helper(self, data):
        """
        This factory is used to generate the correct response object

        :returns: The decoded request or an exception response object
        """
        fc_string = function_code = byte2int(data[0])
        if function_code in self.__lookup:
            fc_string = "%s: %s" % (
                str(self.__lookup[function_code]).split('.')[-1].rstrip("'>"),
                function_code
            )
        _logger.debug("Factory Response[%s]" % fc_string)
        response = self.__lookup.get(function_code, lambda: None)()
        if function_code > 0x80:
            code = function_code & 0x7f  # strip error portion
            response = ExceptionResponse(code, ecode.IllegalFunction)
        if not response:
            raise ModbusException("Unknown response %d" % function_code)
        response.decode(data[1:])

        if hasattr(response, 'sub_function_code'):
            lookup = self.__sub_lookup.get(response.function_code, {})
            subtype = lookup.get(response.sub_function_code, None)
            if subtype: response.__class__ = subtype

        return response

    def register(self, function=None, sub_function=None, force=False):
        """
        Registers a function and sub function class with Force update the existing class
        :return:
        """
        """
        YW reisters were customized according to VFD scenarios
        """
        if function and not issubclass(function, ModbusResponse):
            raise MessageRegisterException("'{}' is Not a valid Modbus Message"
                                           ". Class needs to be derived from "
                                           "`yw.yw_base.ModbusResponse` "
                                           "".format(
                function.__class__.__name__
            ))
        self.__lookup[function.function_code] = function
        if hasattr(function, "sub_function_code"):
            if function.function_code not in self.__sub_lookup:
                self.__sub_lookup[function.function_code] = dict()
            self.__sub_lookup[function.function_code][
                function.sub_function_code] = function
# --------------------------------------------------------------------------- #
# Exported symbols
# --------------------------------------------------------------------------- #


__all__ = ['ServerDecoder', 'ClientDecoder']


