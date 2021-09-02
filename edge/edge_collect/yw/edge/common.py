'''
Modbus Client Common
----------------------------------


'''
from yw.bit_read_message import *
from yw.bit_write_message import *
from yw.register_read_message import *
from yw.register_write_message import *
from yw.diag_message import *
from yw.file_message import *
from yw.other_message import *

from yw.yw_utilities import ModbusTransactionState


class ModbusClientMixin(object):
    '''
    This is a modbus client mixin that provides additional factory
    methods for all the current modbus methods. This can be used
    instead of the normal pattern of::


    '''
    state = ModbusTransactionState.IDLE
    last_frame_end = 0
    silent_interval = 0

    def read_coils(self, address, count=1, **kwargs):
        '''


        :returns: A deferred response handle
        '''
        request = ReadCoilsRequest(address, count, **kwargs)
        return self.execute(request)

    def read_discrete_inputs(self, address, count=1, **kwargs):
        '''


        :returns: A deferred response handle
        '''
        request = ReadDiscreteInputsRequest(address, count, **kwargs)
        return self.execute(request)

    def write_coil(self, address, value, **kwargs):
        '''


        :returns: A deferred response handle
        '''
        request = WriteSingleCoilRequest(address, value, **kwargs)
        return self.execute(request)

    def write_coils(self, address, values, **kwargs):
        '''


        :returns: A deferred response handle
        '''
        request = WriteMultipleCoilsRequest(address, values, **kwargs)
        return self.execute(request)

    def write_register(self, address, value, **kwargs):
        '''


        :returns: A deferred response handle
        '''
        request = WriteSingleRegisterRequest(address, value, **kwargs)
        return self.execute(request)

    def write_registers(self, address, values, **kwargs):
        '''


        :returns: A deferred response handle
        '''
        request = WriteMultipleRegistersRequest(address, values, **kwargs)
        return self.execute(request)

    def read_yw_registers(self, address, count=1, **kwargs):
        '''


        :returns: A deferred response handle
        '''
        
        '''
        :custom params for YW
        :accepts RTU params, PLC params as dynamic registers         
        '''
        request = ReadYWRegistersRequest(address, count, **kwargs)
        return self.execute(request)

    def read_input_registers(self, address, count=1, **kwargs):
        '''


        :returns: A deferred response handle
        '''
        request = ReadInputRegistersRequest(address, count, **kwargs)
        return self.execute(request)

    def readwrite_registers(self, *args, **kwargs):
        '''


        :returns: A deferred response handle
        '''
        request = ReadWriteMultipleRegistersRequest(*args, **kwargs)
        return self.execute(request)

    def mask_write_register(self, *args, **kwargs):
        '''


        :returns: A deferred response handle
        '''
        request = MaskWriteRegisterRequest(*args, **kwargs)
        return self.execute(request)

#---------------------------------------------------------------------------#
# Exported symbols
#---------------------------------------------------------------------------#
__all__ = [ 'ModbusClientMixin' ]
