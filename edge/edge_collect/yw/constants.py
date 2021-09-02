'''
Constants For Modbus Server/Client
----------------------------------

This is the single location for storing default
values for the servers and clients.

Extended with teh requirements of YW to support multiple VFDs

'''
from yw.interfaces import Singleton


class Defaults(Singleton):
    ''' A collection of modbus default values


    .. attribute:: Baudrate

       The speed at which the data is transmitted over the serial line.
       This defaults to 19200.

    .. attribute:: Parity

       The type of checksum to use to verify data integrity. This can be
       on of the following::



    '''
    Port                = 502
    TLSPort             = 802
    Backoff             = 0.3
    Retries             = 3
    RetryOnEmpty        = False
    RetryOnInvalid      = False
    Timeout             = 3
    Reconnects          = 0
    TransactionId       = 0
    ProtocolId          = 0
    UnitId              = 0x00
    Baudrate            = 19200
    Parity              = 'N'
    Bytesize            = 8
    Stopbits            = 1
    ZeroMode            = False
    IgnoreMissingSlaves = False
    ReadSize            = 1024
    broadcast_enable    = False

class ModbusStatus(Singleton):
    '''
    These represent various status codes in the modbus
    protocol.


    .. attribute:: Ready

       This indicates that a modbus device is currently
       free to perform the next request task.

    .. attribute:: On

       This indicates that the given modbus entity is on

    .. attribute:: Off

       This indicates that the given modbus entity is off



       This indicates that the given modbus slave is not running
    '''
    Waiting  = 0xffff
    Ready    = 0x0000
    On       = 0xff00
    Off      = 0x0000
    SlaveOn  = 0xff
    SlaveOff = 0x00


class Endian(Singleton):
    ''' An enumeration representing the various byte endianess.



    .. note:: I am simply borrowing the format strings from the
       python struct module for my convenience.
    '''
    Auto   = '@'
    Big    = '>'
    Little = '<'


class ModbusPlusOperation(Singleton):
    ''' Represents the type of modbus plus request


    '''
    GetStatistics   = 0x0003
    ClearStatistics = 0x0004


class DeviceInformation(Singleton):
    ''' Represents what type of device information to read



    .. attribute:: Extended

       In addition to regular data objects, the device provides additional
       and optional identification and description private data about the
       VFD itself. All of these data are dependent of Series, Series 4.

    .. attribute:: Specific

       Request to return a single data object for given VFD.
    '''
    Basic    = 0x01
    Regular  = 0x02
    Extended = 0x03
    Specific = 0x04


class MoreData(Singleton):
    ''' Represents the more follows condition

    .. attribute:: Nothing

       This indiates that no more objects are going to be returned.

    .. attribute:: KeepReading

       This indicates that there are more objects to be returned.
    '''
    Nothing     = 0x00
    KeepReading = 0xFF

#---------------------------------------------------------------------------#
# Exported Identifiers
#---------------------------------------------------------------------------#
__all__ = [
    "Defaults", "ModbusStatus", "Endian",
    "ModbusPlusOperation",
    "DeviceInformation", "MoreData",
]
