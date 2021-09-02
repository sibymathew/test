'''
Modbus Remote Events
------------------------------------------------------------

An event byte returned by the Get Communications Event Log function
can be any one of four types. The type is defined by bit 7
(the high-order bit) in each byte. It may be further defined by bit 6.
'''
from yw.exceptions import NotImplementedException
from yw.exceptions import ParameterException
from yw.yw_utilities import pack_bitstring, unpack_bitstring


class ModbusEvent(object):

    def encode(self):
        ''' Encodes the status bits to an event message

        :returns: The encoded event message
        '''
        raise NotImplementedException()

    def decode(self, event):
        ''' Decodes the event message to its status bits

        :param event: The event to decode
        '''
        raise NotImplementedException()


class RemoteReceiveEvent(ModbusEvent):
    ''' Remote device MODBUS Receive Event


    '''

    def __init__(self, **kwargs):
        ''' Initialize a new event instance
        '''
        self.overrun   = kwargs.get('overrun', False)
        self.listen    = kwargs.get('listen', False)
        self.broadcast = kwargs.get('broadcast', False)

    def encode(self):
        ''' Encodes the status bits to an event message

        :returns: The encoded event message
        '''
        bits  = [False] * 3
        bits += [self.overrun, self.listen, self.broadcast, True]
        packet = pack_bitstring(bits)
        return packet

    def decode(self, event):
        ''' Decodes the event message to its status bits

        :param event: The event to decode
        '''
        bits = unpack_bitstring(event)
        self.overrun   = bits[4]
        self.listen    = bits[5]
        self.broadcast = bits[6]


class RemoteSendEvent(ModbusEvent):
    ''' Remote device MODBUS Send Event

    The remote device stores this type of event byte when  the corresponding
    condition is TRUE. The bit layout is::


    '''

    def __init__(self, **kwargs):
        ''' Initialize a new event instance
        '''
        self.read          = kwargs.get('read', False)
        self.slave_abort   = kwargs.get('slave_abort', False)
        self.slave_busy    = kwargs.get('slave_busy', False)
        self.slave_nak     = kwargs.get('slave_nak', False)
        self.write_timeout = kwargs.get('write_timeout', False)
        self.listen        = kwargs.get('listen', False)

    def encode(self):
        ''' Encodes the status bits to an event message

        :returns: The encoded event message
        '''
        bits = [self.read, self.slave_abort, self.slave_busy,
            self.slave_nak, self.write_timeout, self.listen]
        bits  += [True, False]
        packet = pack_bitstring(bits)
        return packet

    def decode(self, event):
        ''' Decodes the event message to its status bits

        :param event: The event to decode
        '''
        # todo fix the start byte count
        bits = unpack_bitstring(event)
        self.read          = bits[0]
        self.slave_abort   = bits[1]
        self.slave_busy    = bits[2]
        self.slave_nak     = bits[3]
        self.write_timeout = bits[4]
        self.listen        = bits[5]


class EnteredListenModeEvent(ModbusEvent):
    ''' Remote device Entered Listen Only Mode


    '''

    value = 0x04
    __encoded = b'\x04'

    def encode(self):
        ''' Encodes the status bits to an event message

        :returns: The encoded event message
        '''
        return self.__encoded

    def decode(self, event):
        ''' Decodes the event message to its status bits

        :param event: The event to decode
        '''
        if event != self.__encoded:
            raise ParameterException('Invalid decoded value')


class CommunicationRestartEvent(ModbusEvent):
    ''' Remote device Initiated Communication Restart added to the existing event log.

    The event is defined by a content of zero.
    '''

    value = 0x00
    __encoded = b'\x00'

    def encode(self):
        ''' Encodes the status bits to an event message

        :returns: The encoded event message
        '''
        return self.__encoded

    def decode(self, event):
        ''' Decodes the event message to its status bits


        '''
        if event != self.__encoded:
            raise ParameterException('Invalid decoded value')
