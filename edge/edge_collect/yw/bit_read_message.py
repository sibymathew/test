"""
Bit Reading Request/Response messages
--------------------------------------

"""
import struct
from yw.yw_base import ModbusRequest
from yw.yw_base import ModbusResponse
from yw.yw_base import ModbusExceptions as merror
from yw.yw_utilities import pack_bitstring, unpack_bitstring
from yw.compat import byte2int


class ReadBitsRequestBase(ModbusRequest):
    ''' Base class for Messages Requesting bit values '''

    _rtu_frame_size = 8

    def __init__(self, address, count, **kwargs):
        ''' Initializes the read request data


        '''
        ModbusRequest.__init__(self, **kwargs)
        self.address = address
        self.count = count

    def encode(self):
        ''' Encodes a request pdu

        :returns: The encoded pdu
        '''
        return struct.pack('>HH', self.address, self.count)

    def decode(self, data):
        ''' Decodes a request pdu

        :param data: The packet data to decode
        '''
        self.address, self.count = struct.unpack('>HH', data)
    
    def get_response_pdu_size(self):
        """
        Func_code based on Quantity of Coils (n Bytes)
        :return: 
        """
        count = self.count//8
        if self.count % 8:
            count += 1

        return 1 + 1 + count
    
    def __str__(self):
        ''' Returns a string representation of the instance

        :returns: A string representation of the instance
        '''
        return "ReadBitRequest(%d,%d)" % (self.address, self.count)


class ReadBitsResponseBase(ModbusResponse):
    ''' Base class for Messages responding to bit-reading values '''

    _rtu_byte_count_pos = 2

    def __init__(self, values, **kwargs):
        ''' Initializes a new instance


        '''
        ModbusResponse.__init__(self, **kwargs)
        self.bits = values or []

    def encode(self):
        ''' Encodes response pdu

        :returns: The encoded packet message
        '''
        result = pack_bitstring(self.bits)
        packet = struct.pack(">B", len(result)) + result
        return packet

    def decode(self, data):
        ''' Decodes response pdu

        :param data: The packet data to decode
        '''
        ''' Added to decode Series 3, Series 4 for YW
        '''
        self.byte_count = byte2int(data[0])
        self.bits = unpack_bitstring(data[1:])

    def setBit(self, address, value=1):
        ''' Helper function to set the specified bit upto n bytes


        '''
        self.bits[address] = (value != 0)

    def resetBit(self, address):
        ''' Helper function to set the specified bit to 0 for n byte


        '''
        self.setBit(address, 0)

    def getBit(self, address):
        ''' Helper function to get the specified bit's value for n byte


        '''
        return self.bits[address]

    def __str__(self):
        ''' Returns a string representation of the instance


        '''
        return "%s(%d)" % (self.__class__.__name__, len(self.bits))


class ReadCoilsRequest(ReadBitsRequestBase):
    '''
    This function code is used to read from 1 to the first coil specified, and the number of
    coils. In the PDU Coils are addressed starting at zero.
    '''
    function_code = 1

    def __init__(self, address=None, count=None, **kwargs):
        ''' Initializes a new instance

        :param address: The address to start reading from
        :param count: The number of bits to read
        '''
        ReadBitsRequestBase.__init__(self, address, count, **kwargs)

    def execute(self, context):
        ''' Run a read coils request before running the request,
        request is valid against the current datastore.


        '''
        if not (1 <= self.count <= 0x7d0):
            return self.doException(merror.IllegalValue)
        if not context.validate(self.function_code, self.address, self.count):
            return self.doException(merror.IllegalAddress)
        values = context.getValues(self.function_code, self.address, self.count)
        return ReadCoilsResponse(values)


class ReadCoilsResponse(ReadBitsResponseBase):
    '''
    The coils in the response LSB of the  first data byte contains the output addressed in the query. The other
    coils follow output quantity is not a multiple of eight, the
    remaining bits in the final data byte will be padded with zeros

    '''
    function_code = 1

    def __init__(self, values=None, **kwargs):
        ''' Intializes a new instance

        :param values: The request values to respond with
        '''
        ReadBitsResponseBase.__init__(self, values, **kwargs)


class ReadDiscreteInputsRequest(ReadBitsRequestBase):
    '''
    This function code is used to read from the first input specified, and the
    number of inputs.
    '''
    function_code = 2

    def __init__(self, address=None, count=None, **kwargs):
        ''' Intializes a new instance

        :param address: The address to start reading from
        :param count: The number of bits to read
        '''
        ReadBitsRequestBase.__init__(self, address, count, **kwargs)

    def execute(self, context):
        ''' Run a read discrete input request before running the request, we make sure that the request is in
        the max valid range


        '''
        if not (1 <= self.count <= 0x7d0):
            return self.doException(merror.IllegalValue)
        if not context.validate(self.function_code, self.address, self.count):
            return self.doException(merror.IllegalAddress)
        values = context.getValues(self.function_code, self.address, self.count)
        return ReadDiscreteInputsResponse(values)


class ReadDiscreteInputsResponse(ReadBitsResponseBase):
    '''
    The discrete inputs in the response message are packed from low order
    to high order in subsequent bytes, the remaining bits in the final data byte will be padded with zeros

    '''
    function_code = 2

    def __init__(self, values=None, **kwargs):
        ''' Intializes a new instance


        '''
        ReadBitsResponseBase.__init__(self, values, **kwargs)

#---------------------------------------------------------------------------#
# Exported symbols
#---------------------------------------------------------------------------#
__all__ = [
    "ReadCoilsRequest", "ReadCoilsResponse",
    "ReadDiscreteInputsRequest", "ReadDiscreteInputsResponse",
]
