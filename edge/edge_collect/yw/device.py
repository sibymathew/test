"""
Modbus Device Controller
-------------------------


"""
from yw.constants import DeviceInformation
from yw.interfaces import Singleton
from yw.yw_utilities import dict_property
from yw.compat import iteritems, itervalues, izip, int2byte

from collections import OrderedDict

#---------------------------------------------------------------------------#
# Network Access Control
#---------------------------------------------------------------------------#
class ModbusAccessControl(Singleton):
    '''
    This is a simple implementation, if the host does not appear in the table (all
    unknown hosts) its connection will simply be closed.

    Since it is a singleton, only one version can possible exist and all
    instances pull from here. Extended for also Series 3, Series 4
    '''
    '''
    Extended to support Series 3, Series 4 for YW
    '''
    __nmstable = [
            "127.0.0.1",
    ]

    def __iter__(self):
        ''' Iterater over the network access table

        :returns: An iterator of the network access table
        '''
        return self.__nmstable.__iter__()

    def __contains__(self, host):
        ''' Check if a host is allowed to access resources based on Series 3, Series 4 for given VFD


        '''
        return host in self.__nmstable

    def add(self, host):
        ''' Add allowed host(s) from the NMS table based on Series 3, Series 4 for given VFD


        '''
        if not isinstance(host, list):
            host = [host]
        for entry in host:
            if entry not in self.__nmstable:
                self.__nmstable.append(entry)

    def remove(self, host):
        ''' Remove allowed host(s) from the NMS table  based on Series 3, Series 4 for given VFD


        '''
        if not isinstance(host, list):
            host = [host]
        for entry in host:
            if entry in self.__nmstable:
                self.__nmstable.remove(entry)

    def check(self, host):
        ''' Check if a host is allowed to access resources  based on Series 3, Series 4 for given VFD


        '''
        return host in self.__nmstable


#---------------------------------------------------------------------------#
# Modbus Plus Statistics
#---------------------------------------------------------------------------#
class ModbusPlusStatistics(object):
    '''
    This is used to maintain the current VFD plus statistics count. As of
    right now this is simply a stub to complete the implementation guide.
    '''
    '''
    To be expended for all other VFD statuses 
    TBD:  Power ON/OFF statuses
    '''

    __data = OrderedDict({
        'node_type_id'                   : [0x00] * 2, # 00
        'software_version_number'        : [0x00] * 2, # 01
        'network_address'                : [0x00] * 2, # 02
        'mac_state_variable'             : [0x00] * 2, # 03
        'peer_status_code'               : [0x00] * 2, # 04
        'token_pass_counter'             : [0x00] * 2, # 05
        'token_rotation_time'            : [0x00] * 2, # 06

        'program_master_token_failed'    : [0x00],     # 07 hi
        'data_master_token_failed'       : [0x00],     # 07 lo
        'program_master_token_owner'     : [0x00],     # 08 hi
        'data_master_token_owner'        : [0x00],     # 08 lo
        'program_slave_token_owner'      : [0x00],     # 09 hi
        'data_slave_token_owner'         : [0x00],     # 09 lo
        'data_slave_command_transfer'    : [0x00],     # 10 hi
        '__unused_10_lowbit'             : [0x00],     # 10 lo

        'program_slave_command_transfer' : [0x00],     # 11 hi
        'program_master_rsp_transfer'    : [0x00],     # 11 lo
        'program_slave_auto_logout'      : [0x00],     # 12 hi
        'program_master_connect_status'  : [0x00],     # 12 lo
        'receive_buffer_dma_overrun'     : [0x00],     # 13 hi
        'pretransmit_deferral_error'     : [0x00],     # 13 lo
        'frame_size_error'               : [0x00],     # 14 hi
        'repeated_command_received'      : [0x00],     # 14 lo
        'receiver_alignment_error'       : [0x00],     # 15 hi
        'receiver_collision_abort_error' : [0x00],     # 15 lo
        'bad_packet_length_error'        : [0x00],     # 16 hi
        'receiver_crc_error'             : [0x00],     # 16 lo
        'transmit_buffer_dma_underrun'   : [0x00],     # 17 hi
        'bad_link_address_error'         : [0x00],     # 17 lo

        'bad_mac_function_code_error'    : [0x00],     # 18 hi
        'internal_packet_length_error'   : [0x00],     # 18 lo
        'communication_failed_error'     : [0x00],     # 19 hi
        'communication_retries'          : [0x00],     # 19 lo
        'no_response_error'              : [0x00],     # 20 hi
        'good_receive_packet'            : [0x00],     # 20 lo
        'unexpected_path_error'          : [0x00],     # 21 hi
        'exception_response_error'       : [0x00],     # 21 lo
        'forgotten_transaction_error'    : [0x00],     # 22 hi
        'unexpected_response_error'      : [0x00],     # 22 lo

        'active_station_bit_map'         : [0x00] * 8, # 23-26
        'token_station_bit_map'          : [0x00] * 8, # 27-30
        'global_data_bit_map'            : [0x00] * 8, # 31-34
        'receive_buffer_use_bit_map'     : [0x00] * 8, # 35-37
        'data_master_output_path'        : [0x00] * 8, # 38-41
        'data_slave_input_path'          : [0x00] * 8, # 42-45
        'program_master_outptu_path'     : [0x00] * 8, # 46-49
        'program_slave_input_path'       : [0x00] * 8, # 50-53
    })

    def __init__(self):
        '''
        Initialize the modbus plus statistics with the default
        information.
        '''
        self.reset()

    def __iter__(self):
        ''' Iterater over the statistics

        :returns: An iterator of the modbus plus statistics
        '''
        return iteritems(self.__data)

    def reset(self):
        ''' This clears all of the modbus plus statistics
        '''
        for key in self.__data:
            self.__data[key] = [0x00] * len(self.__data[key])

    def summary(self):
        ''' Returns a summary of the modbus plus statistics

        :returns: 54 16-bit words representing the status
        '''
        return itervalues(self.__data)

    def encode(self):
        ''' Returns a summary of the modbus plus statistics

        :returns: 54 16-bit words representing the status
        '''
        total, values = [], sum(self.__data.values(), [])
        for c in range(0, len(values), 2):
            total.append((values[c] << 8) | values[c+1])
        return total


#---------------------------------------------------------------------------#
# Device Information Control
#---------------------------------------------------------------------------#
class ModbusDeviceIdentification(object):
    '''
    This is used to supply the device identification
    for the readDeviceIdentification function

    For more information read section 6.21 of the modbus
    application protocol.
    '''
    __data = {
        0x00: '',  # VendorName
        0x01: '',  # ProductCode
        0x02: '',  # MajorMinorRevision
        0x03: '',  # VendorUrl
        0x04: '',  # ProductName
        0x05: '',  # ModelName
        0x06: '',  # UserApplicationName
        0x07: '',  # reserved
        0x08: '',  # reserved
        # 0x80 -> 0xFF are private
    }

    __names = [
        'VendorName',
        'ProductCode',
        'MajorMinorRevision',
        'VendorUrl',
        'ProductName',
        'ModelName',
        'UserApplicationName',
    ]

    def __init__(self, info=None):
        '''
        Initialize the datastore with the elements you need.

        '''
        if isinstance(info, dict):
            for key in info:
                if (0x06 >= key >= 0x00) or (0xFF >= key >= 0x80):
                    self.__data[key] = info[key]

    def __iter__(self):
        ''' Iterater over the device information

        :returns: An iterator of the device information
        '''
        return iteritems(self.__data)

    def summary(self):
        ''' Return a summary of the main items

        :returns: An dictionary of the main items
        '''
        return dict(zip(self.__names, itervalues(self.__data)))

    def update(self, value):
        ''' Update the values of this identity
        using the value to copy values from
        '''
        self.__data.update(value)

    def __setitem__(self, key, value):
        ''' Wrapper used to access the device information


        '''
        if key not in [0x07, 0x08]:
            self.__data[key] = value

    def __getitem__(self, key):
        ''' Wrapper used to access the device information


        '''
        return self.__data.setdefault(key, '')

    def __str__(self):
        ''' Build a representation of the device

        :returns: A string representation of the device
        '''
        return "DeviceIdentity"

    #-------------------------------------------------------------------------#
    # Properties
    #-------------------------------------------------------------------------#
    VendorName          = dict_property(lambda s: s.__data, 0)
    ProductCode         = dict_property(lambda s: s.__data, 1)
    MajorMinorRevision  = dict_property(lambda s: s.__data, 2)
    VendorUrl           = dict_property(lambda s: s.__data, 3)
    ProductName         = dict_property(lambda s: s.__data, 4)
    ModelName           = dict_property(lambda s: s.__data, 5)
    UserApplicationName = dict_property(lambda s: s.__data, 6)


class DeviceInformationFactory(Singleton):
    ''' This is a helper factory that really just hides
    some of the complexity of processing the device information
    requests (function code 0x2b 0x0e).
    '''

    __lookup = {
        DeviceInformation.Basic: lambda c, r, i: c.__gets(r, list(range(i, 0x03))),
        DeviceInformation.Regular: lambda c, r, i: c.__gets(r, list(range(i, 0x07))
            if c.__get(r, i)[i] else list(range(0, 0x07))),
        DeviceInformation.Extended: lambda c, r, i: c.__gets(r,
            [x for x in range(i, 0x100) if x not in range(0x07, 0x80)]
            if c.__get(r, i)[i] else
            [x for x in range(0, 0x100) if x not in range(0x07, 0x80)]),
        DeviceInformation.Specific: lambda c, r, i: c.__get(r, i),
    }

    @classmethod
    def get(cls, control, read_code=DeviceInformation.Basic, object_id=0x00):
        ''' Get the requested device data from the system


        '''
        identity = control.Identity
        return cls.__lookup[read_code](cls, identity, object_id)

    @classmethod
    def __get(cls, identity, object_id):
        ''' Read a single object_id from the device information

        '''
        return { object_id:identity[object_id] }

    @classmethod
    def __gets(cls, identity, object_ids):
        ''' Read multiple object_ids from the device information


        '''
        return dict((oid, identity[oid]) for oid in object_ids if identity[oid])


#---------------------------------------------------------------------------#
# Counters Handler
#---------------------------------------------------------------------------#
class ModbusCountersHandler(object):
    '''
    This is a helper class to simplify the properties for the counters::



    .. note:: I threw the event counter in here for convenience
    '''
    __data = dict([(i, 0x0000) for i in range(9)])
    __names   = [
        'BusMessage',
        'BusCommunicationError',
        'SlaveExceptionError',
        'SlaveMessage',
        'SlaveNoResponse',
        'SlaveNAK',
        'SlaveBusy',
        'BusCharacterOverrun'
        'Event '
    ]

    def __iter__(self):
        ''' Iterater over the device counters

        :returns: An iterator of the device counters
        '''
        return izip(self.__names, itervalues(self.__data))

    def update(self, values):
        ''' Update the values of this identity
        using another identify as the value

        :param values: The value to copy values from
        '''
        for k, v in iteritems(values):
            v += self.__getattribute__(k)
            self.__setattr__(k, v)

    def reset(self):
        ''' This clears all of the system counters
        '''
        self.__data = dict([(i, 0x0000) for i in range(9)])

    def summary(self):
        ''' Returns a summary of the counters current status

        :returns: A byte with each bit representing each counter
        '''
        count, result = 0x01, 0x00
        for i in itervalues(self.__data):
            if i != 0x00: result |= count
            count <<= 1
        return result

    #-------------------------------------------------------------------------#
    # Properties
    #-------------------------------------------------------------------------#
    BusMessage            = dict_property(lambda s: s.__data, 0)
    BusCommunicationError = dict_property(lambda s: s.__data, 1)
    BusExceptionError     = dict_property(lambda s: s.__data, 2)
    SlaveMessage          = dict_property(lambda s: s.__data, 3)
    SlaveNoResponse       = dict_property(lambda s: s.__data, 4)
    SlaveNAK              = dict_property(lambda s: s.__data, 5)
    SlaveBusy             = dict_property(lambda s: s.__data, 6)
    BusCharacterOverrun   = dict_property(lambda s: s.__data, 7)
    Event                 = dict_property(lambda s: s.__data, 8)


#---------------------------------------------------------------------------#
# Main server control block
#---------------------------------------------------------------------------#
class ModbusControlBlock(Singleton):
    '''
    This is a global singleotn that controls all system information

    All activity should be logged here and all diagnostic requests
    should come from here.
    '''

    __mode = 'ASCII'
    __diagnostic = [False] * 16
    __instance = None
    __listen_only = False
    __delimiter = '\r'
    __counters = ModbusCountersHandler()
    __identity = ModbusDeviceIdentification()
    __plus     = ModbusPlusStatistics()
    __events   = []

    #-------------------------------------------------------------------------#
    # Magic
    #-------------------------------------------------------------------------#
    def __str__(self):
        ''' Build a representation of the control block

        :returns: A string representation of the control block
        '''
        return "ModbusControl"

    def __iter__(self):
        ''' Iterater over the device counters

        :returns: An iterator of the device counters
        '''
        return self.__counters.__iter__()

    #-------------------------------------------------------------------------#
    # Events
    #-------------------------------------------------------------------------#
    def addEvent(self, event):
        ''' Adds a new event to the event log

        :param event: A new event to add to the log
        '''
        self.__events.insert(0, event)
        self.__events = self.__events[0:64]  # chomp to 64 entries
        self.Counter.Event += 1

    def getEvents(self):
        ''' Returns an encoded collection of the event log.

        :returns: The encoded events packet
        '''
        events = [event.encode() for event in self.__events]
        return b''.join(events)

    def clearEvents(self):
        ''' Clears the current list of events
        '''
        self.__events = []

    #-------------------------------------------------------------------------#
    # Other Properties
    #-------------------------------------------------------------------------#
    Identity = property(lambda s: s.__identity)
    Counter  = property(lambda s: s.__counters)
    Events   = property(lambda s: s.__events)
    Plus     = property(lambda s: s.__plus)

    def reset(self):
        ''' This clears all of the system counters and the
            diagnostic register
        '''
        self.__events = []
        self.__counters.reset()
        self.__diagnostic = [False] * 16

    #-------------------------------------------------------------------------#
    # Listen Properties
    #-------------------------------------------------------------------------#
    def _setListenOnly(self, value):
        ''' This toggles the listen only status


        '''
        self.__listen_only = bool(value)

    ListenOnly = property(lambda s: s.__listen_only, _setListenOnly)

    #-------------------------------------------------------------------------#
    # Mode Properties
    #-------------------------------------------------------------------------#
    def _setMode(self, mode):
        ''' This toggles the current serial mode with data transfer method in (RTU, ASCII)
        '''
        if mode in ['ASCII', 'RTU']:
            self.__mode = mode

    Mode = property(lambda s: s.__mode, _setMode)

    #-------------------------------------------------------------------------#
    # Delimiter Properties
    #-------------------------------------------------------------------------#
    def _setDelimiter(self, char):
        ''' This changes the serial delimiter character


        '''
        if isinstance(char, str):
            self.__delimiter = char.encode()
        if isinstance(char, bytes):
            self.__delimiter = char
        elif isinstance(char, int):
            self.__delimiter = int2byte(char)

    Delimiter = property(lambda s: s.__delimiter, _setDelimiter)

    #-------------------------------------------------------------------------#
    # Diagnostic Properties
    #-------------------------------------------------------------------------#
    def setDiagnostic(self, mapping):
        ''' This sets the value in the diagnostic register, where Dictionary of key:value pairs to set
        '''
        for entry in iteritems(mapping):
            if entry[0] >= 0 and entry[0] < len(self.__diagnostic):
                self.__diagnostic[entry[0]] = (entry[1] != 0)

    def getDiagnostic(self, bit):
        ''' This gets the value in the diagnostic register


        :returns: The current value of the requested bit
        '''
        try:
            if bit and bit >= 0 and bit < len(self.__diagnostic):
                return self.__diagnostic[bit]
        except Exception:
            return None

    def getDiagnosticRegister(self):
        ''' This gets the entire diagnostic register based on Series 3, Series 4 for given VFD

        :returns: The diagnostic register collection
        '''
        return self.__diagnostic

#---------------------------------------------------------------------------#
# Exported Identifiers
#---------------------------------------------------------------------------#
__all__ = [
        "ModbusAccessControl",
        "ModbusPlusStatistics",
        "ModbusDeviceIdentification",
        "DeviceInformationFactory",
        "ModbusControlBlock"
]
