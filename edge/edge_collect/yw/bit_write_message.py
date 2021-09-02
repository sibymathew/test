"""
Bit Writing Request/Response
------------------------------

TODO write mask request/response
"""
import struct
from yw.constants import ModbusStatus
from yw.yw_base import ModbusRequest
from yw.yw_base import ModbusResponse
from yw.yw_base import ModbusExceptions as merror
from yw.yw_utilities import pack_bitstring, unpack_bitstring

#---------------------------------------------------------------------------#
# Local Constants
#---------------------------------------------------------------------------#
# These are defined in the spec to turn a coil on/off
#---------------------------------------------------------------------------#
_turn_coil_on  = struct.pack(">H", ModbusStatus.On)
_turn_coil_off = struct.pack(">H", ModbusStatus.Off)


class WriteSingleCoilRequest(ModbusRequest):
    '''
    This function code is used to write a single output to either ON or OFF
    in a remote device.


    '''
    function_code = 5
    _rtu_frame_size = 8

    def __init__(self, address=None, value=None, **kwargs):
        ''' Initializes a new instance


        '''
        ModbusRequest.__init__(self, **kwargs)
        self.address = address
        self.value = bool(value)

    def encode(self):
        ''' Encodes write coil request

        :returns: The byte encoded message
        '''
        result  = struct.pack('>H', self.address)
        if self.value: result += _turn_coil_on
        else: result += _turn_coil_off
        return result

    def decode(self, data):
        ''' Decodes a write coil request

        :param data: The packet data to decode
        '''
        self.address, value = struct.unpack('>HH', data)
        self.value = (value == ModbusStatus.On)

    def execute(self, context):
        ''' Run a write coil request for both Series 3 , Series 4

        '''
        #if self.value not in [ModbusStatus.Off, ModbusStatus.On]:
        #    return self.doException(merror.IllegalValue)
        if not context.validate(self.function_code, self.address, 1):
            return self.doException(merror.IllegalAddress)

        context.setValues(self.function_code, self.address, [self.value])
        values = context.getValues(self.function_code, self.address, 1)
        return WriteSingleCoilResponse(self.address, values[0])

    def get_response_pdu_size(self):
        """
        Func_code (1 byte) + Output Address (2 byte) + Output Value  (2 Bytes)
        :return: 
        """
        return 1 + 2 + 2

    def __str__(self):
        ''' Returns a string representation of the instance for both Series 3 , Series 4


        '''
        return "WriteCoilRequest(%d, %s) => " % (self.address, self.value)


class WriteSingleCoilResponse(ModbusResponse):
    '''
    The normal response is an echo of the request, returned after the coil
    state has been written.
    '''
    function_code = 5
    _rtu_frame_size = 8

    def __init__(self, address=None, value=None, **kwargs):
        ''' Initializes a new instance


        '''
        ModbusResponse.__init__(self, **kwargs)
        self.address = address
        self.value = value

    def encode(self):
        ''' Encodes write coil response for both Series 3 , Series 4

        :return: The byte encoded message
        '''
        result  = struct.pack('>H', self.address)
        if self.value: result += _turn_coil_on
        else: result += _turn_coil_off
        return result

    def decode(self, data):
        ''' Decodes a write coil response for both Series 3 , Series 4


        '''
        self.address, value = struct.unpack('>HH', data)
        self.value = (value == ModbusStatus.On)

    def __str__(self):
        ''' Returns a string representation of the instance

        :returns: A string representation of the instance
        '''
        return "WriteCoilResponse(%d) => %d" % (self.address, self.value)


class WriteMultipleCoilsRequest(ModbusRequest):
    '''
    "This function code is used to force ON/OFF states are specified by contents of the request
    data field. A logical '1' in a bit position of the field requests the
    corresponding output to be ON. A logical '0' requests it to be OFF."
    '''
    function_code = 15
    _rtu_byte_count_pos = 6
    
    def __init__(self, address=None, values=None, **kwargs):
        ''' Initializes a new instance


        '''
        ModbusRequest.__init__(self, **kwargs)
        self.address = address
        if not values: values = []
        elif not hasattr(values, '__iter__'): values = [values]
        self.values  = values
        self.byte_count = (len(self.values) + 7) // 8

    def encode(self):
        ''' Encodes write coils request for both Series 3 , Series 4

        :returns: The byte encoded message
        '''
        count   = len(self.values)
        self.byte_count = (count + 7) // 8
        packet  = struct.pack('>HHB', self.address, count, self.byte_count)
        packet += pack_bitstring(self.values)
        return packet

    def decode(self, data):
        ''' Decodes a write coils request for both Series 3 , Series 4

        :param data: The packet data to decode
        '''
        self.address, count, self.byte_count = struct.unpack('>HHB', data[0:5])
        values = unpack_bitstring(data[5:])
        self.values = values[:count]

    def execute(self, context):
        ''' Run a write coils request for both Series 3 , Series 4


        '''
        count = len(self.values)
        if not (1 <= count <= 0x07b0):
            return self.doException(merror.IllegalValue)
        if (self.byte_count != (count + 7) // 8):
            return self.doException(merror.IllegalValue)
        if not context.validate(self.function_code, self.address, count):
            return self.doException(merror.IllegalAddress)

        context.setValues(self.function_code, self.address, self.values)
        return WriteMultipleCoilsResponse(self.address, count)

    def __str__(self):
        ''' Returns a string representation of the instance

        :returns: A string representation of the instance
        '''
        params = (self.address, len(self.values))
        return "WriteNCoilRequest (%d) => %d " % params

    def get_response_pdu_size(self):
        """
        Func_code (1 byte) + Output Address (2 byte) + Quantity of Outputs  (2 Bytes)
        :return:
        """
        return 1 + 2 + 2


class WriteMultipleCoilsResponse(ModbusResponse):
    '''
    The normal response returns the function code, starting address, and
    quantity of coils forced for both Series 3 , Series 4
    '''
    function_code = 15
    _rtu_frame_size = 8

    def __init__(self, address=None, count=None, **kwargs):
        ''' Initializes a new instance


        '''
        ModbusResponse.__init__(self, **kwargs)
        self.address = address
        self.count = count

    def encode(self):
        ''' Encodes write coils response for both Series 3 , Series 4

        :returns: The byte encoded message
        '''
        return struct.pack('>HH', self.address, self.count)

    def decode(self, data):
        ''' Decodes a write coils response for both Series 3 , Series 4


        '''
        self.address, self.count = struct.unpack('>HH', data)

    def __str__(self):
        ''' Returns a string representation of the instance for both Series 3 , Series 4

        :returns: A string representation of the instance
        '''
        return "WriteNCoilResponse(%d, %d)" % (self.address, self.count)

#---------------------------------------------------------------------------#
# Exported symbols
#---------------------------------------------------------------------------#
__all__ = [
    "WriteSingleCoilRequest", "WriteSingleCoilResponse",
    "WriteMultipleCoilsRequest", "WriteMultipleCoilsResponse",
]
