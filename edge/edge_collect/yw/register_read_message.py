'''
Register Reading Request/Response
---------------------------------
'''
'''
Base register classes are customized to decode YW variety of registers using VFD 
'''
import struct
from yw.yw_base import ModbusRequest
from yw.yw_base import ModbusResponse
from yw.yw_base import ModbusExceptions as merror
from yw.compat import int2byte, byte2int


class ReadRegistersRequestBase(ModbusRequest):
    '''
    Base class for reading a modbus register
    '''
    _rtu_frame_size = 8

    def __init__(self, address, count, **kwargs):
        ''' Initializes a new instance


        '''
        ModbusRequest.__init__(self, **kwargs)
        self.address = address
        self.count = count

    def encode(self):
        ''' Encodes the request packet

        :return: The encoded packet
        '''
        return struct.pack('>HH', self.address, self.count)

    def decode(self, data):
        ''' Decode a register request packet to decode YW variety of registers using VFD


        '''
        self.address, self.count = struct.unpack('>HH', data)

    def get_response_pdu_size(self):
        """

        :return: 
        """
        return 1 + 1 + 2 * self.count

    def __str__(self):
        ''' Returns a string representation of the instance

        :returns: A string representation of the instance
        '''
        return "ReadRegisterRequest (%d,%d)" % (self.address, self.count)


class ReadRegistersResponseBase(ModbusResponse):
    '''
    Base class for responding to a modbus register read  YW variety of registers using VFD
    '''

    _rtu_byte_count_pos = 2

    def __init__(self, values, **kwargs):
        ''' Initializes a new instance


        '''
        ModbusResponse.__init__(self, **kwargs)
        self.registers = values or []

    def encode(self):
        ''' Encodes the response packet

        :returns: The encoded packet
        '''
        result = int2byte(len(self.registers) * 2)
        for register in self.registers:
            result += struct.pack('>H', register)
        return result

    def decode(self, data):
        ''' Decode a register response packet

        :param data: The request to decode
        '''
        byte_count = byte2int(data[0])
        self.registers = []
        for i in range(1, byte_count + 1, 2):
            self.registers.append(struct.unpack('>H', data[i:i + 2])[0])

    def getRegister(self, index):
        ''' Get the requested register


        :returns: The request register
        '''
        return self.registers[index]

    def __str__(self):
        ''' Returns a string representation of the instance

        :returns: A string representation of the instance
        '''
        return "%s (%d)" % (self.__class__.__name__, len(self.registers))


class ReadYWRegistersRequest(ReadRegistersRequestBase):
    '''
    This function code is used to read the registers .
    '''
    '''
    :custom params for YW
    :accepts RTU 
    '''
    
    function_code = 3

    def __init__(self, address=None, count=None, **kwargs):
        ''' Initializes a new instance of the request

        :param address: The starting address to read from
        :param count: The number of registers to read from address
        '''
        ReadRegistersRequestBase.__init__(self, address, count, **kwargs)

    def execute(self, context):
        ''' Run a read holding request against a datastore

        :param context: The datastore to request from
        :returns: An initialized response, exception message otherwise
        '''
        if not (1 <= self.count <= 0x7d):
            return self.doException(merror.IllegalValue)
        if not context.validate(self.function_code, self.address, self.count):
            return self.doException(merror.IllegalAddress)
        values = context.getValues(self.function_code, self.address, self.count)
        return ReadYWRegistersResponse(values)


class ReadYWRegistersResponse(ReadRegistersResponseBase):
    '''
    This function code is used to read the registers
    '''
    '''
    :custom params for YW
    :accepts RTU 
    '''
    function_code = 3

    def __init__(self, values=None, **kwargs):
        ''' Initializes a new response instance


        '''
        ReadRegistersResponseBase.__init__(self, values, **kwargs)


class ReadInputRegistersRequest(ReadRegistersRequestBase):
    '''
    This function code is used to read input registers

    '''
    function_code = 4

    def __init__(self, address=None, count=None, **kwargs):
        ''' Initializes a new instance of the request


        '''
        ReadRegistersRequestBase.__init__(self, address, count, **kwargs)

    def execute(self, context):
        ''' Run a read input request against a datastore


        :returns: An initialized response, exception message otherwise
        '''
        if not (1 <= self.count <= 0x7d):
            return self.doException(merror.IllegalValue)
        if not context.validate(self.function_code, self.address, self.count):
            return self.doException(merror.IllegalAddress)
        values = context.getValues(self.function_code, self.address, self.count)
        return ReadInputRegistersResponse(values)


class ReadInputRegistersResponse(ReadRegistersResponseBase):
    '''
    This function code is used to read from  input registers

    '''
    function_code = 4

    def __init__(self, values=None, **kwargs):
        ''' Initializes a new response instance

        :param values: The resulting register values
        '''
        ReadRegistersResponseBase.__init__(self, values, **kwargs)


class ReadWriteMultipleRegistersRequest(ModbusRequest):
    '''
    This function code performs a combination of  holding
    registers to be read as well as the starting address, byte count specifies the
    number of bytes to follow in the write data field."
    '''
    function_code = 23
    _rtu_byte_count_pos = 10

    def __init__(self, **kwargs):
        ''' Initializes a new request message


        '''
        ModbusRequest.__init__(self, **kwargs)
        self.read_address    = kwargs.get('read_address', 0x00)
        self.read_count      = kwargs.get('read_count', 0)
        self.write_address   = kwargs.get('write_address', 0x00)
        self.write_registers = kwargs.get('write_registers', None)
        if not hasattr(self.write_registers, '__iter__'):
            self.write_registers = [self.write_registers]
        self.write_count = len(self.write_registers)
        self.write_byte_count = self.write_count * 2

    def encode(self):
        ''' Encodes the request packet

        :returns: The encoded packet
        '''
        result = struct.pack('>HHHHB',
                self.read_address,  self.read_count, \
                self.write_address, self.write_count, self.write_byte_count)
        for register in self.write_registers:
            result += struct.pack('>H', register)
        return result

    def decode(self, data):
        ''' Decode the register request packet

        :param data: The request to decode
        '''
        self.read_address,  self.read_count,  \
        self.write_address, self.write_count, \
        self.write_byte_count = struct.unpack('>HHHHB', data[:9])
        self.write_registers  = []
        for i in range(9, self.write_byte_count + 9, 2):
            register = struct.unpack('>H', data[i:i + 2])[0]
            self.write_registers.append(register)

    def execute(self, context):
        ''' Run a write single register request against a datastore

        :param context: The datastore to request from
        :returns: An initialized response, exception message otherwise
        '''
        if not (1 <= self.read_count <= 0x07d):
            return self.doException(merror.IllegalValue)
        if not (1 <= self.write_count <= 0x079):
            return self.doException(merror.IllegalValue)
        if (self.write_byte_count != self.write_count * 2):
            return self.doException(merror.IllegalValue)
        if not context.validate(self.function_code, self.write_address,
                                self.write_count):
            return self.doException(merror.IllegalAddress)
        if not context.validate(self.function_code, self.read_address,
                                self.read_count):
            return self.doException(merror.IllegalAddress)
        context.setValues(self.function_code, self.write_address,
                          self.write_registers)
        registers = context.getValues(self.function_code, self.read_address,
                                      self.read_count)
        return ReadWriteMultipleRegistersResponse(registers)

    def get_response_pdu_size(self):
        """
        Func_code (1 byte) + Byte Count(1 byte) + 2 * Quantity of Coils (n Bytes)
        :return: 
        """
        return 1 + 1 + 2 * self.read_count

    def __str__(self):
        ''' Returns a string representation of the instance

        :returns: A string representation of the instance
        '''
        params = (self.read_address, self.read_count, self.write_address,
                  self.write_count)
        return "ReadWriteNRegisterRequest R(%d,%d) W(%d,%d)" % params


class ReadWriteMultipleRegistersResponse(ModbusResponse):
    '''
    The normal response contains the data from the group of registers that specifies the quantity of bytes
    '''
    function_code = 23
    _rtu_byte_count_pos = 2

    def __init__(self, values=None, **kwargs):
        ''' Initializes a new instance


        '''
        ModbusResponse.__init__(self, **kwargs)
        self.registers = values or []

    def encode(self):
        ''' Encodes the response packet

        :returns: The encoded packet
        '''
        result = int2byte(len(self.registers) * 2)
        for register in self.registers:
            result += struct.pack('>H', register)
        return result

    def decode(self, data):
        ''' Decode the register response packet

        :param data: The response to decode
        '''
        bytecount = byte2int(data[0])
        for i in range(1, bytecount, 2):
            self.registers.append(struct.unpack('>H', data[i:i + 2])[0])

    def __str__(self):
        ''' Returns a string representation of the instance

        :returns: A string representation of the instance
        '''
        return "ReadWriteNRegisterResponse (%d)" % len(self.registers)

#---------------------------------------------------------------------------#
# Exported symbols
#---------------------------------------------------------------------------#
__all__ = [
    "ReadYWRegistersRequest", "ReadYWRegistersResponse",
    "ReadInputRegistersRequest", "ReadInputRegistersResponse",
    "ReadWriteMultipleRegistersRequest", "ReadWriteMultipleRegistersResponse",
]
