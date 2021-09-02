"""
YW Utilities
-----------------

A collection of utilities for packing data, unpacking
data computing checksums, and decode checksums, implemented for any VFD thru RTU
"""
from yw.compat import int2byte, byte2int, IS_PYTHON3
from six import string_types


class ModbusTransactionState(object):
    """
    Modbus Client States
    """
    IDLE = 0
    SENDING = 1
    WAITING_FOR_REPLY = 2
    WAITING_TURNAROUND_DELAY = 3
    PROCESSING_REPLY = 4
    PROCESSING_ERROR = 5
    TRANSACTION_COMPLETE = 6
    RETRYING = 7
    NO_RESPONSE_STATE = 8

    @classmethod
    def to_string(cls, state):
        states = {
            ModbusTransactionState.IDLE: "IDLE",
            ModbusTransactionState.SENDING: "SENDING",
            ModbusTransactionState.WAITING_FOR_REPLY: "WAITING_FOR_REPLY",
            ModbusTransactionState.WAITING_TURNAROUND_DELAY: "WAITING_TURNAROUND_DELAY",
            ModbusTransactionState.PROCESSING_REPLY: "PROCESSING_REPLY",
            ModbusTransactionState.PROCESSING_ERROR: "PROCESSING_ERROR",
            ModbusTransactionState.TRANSACTION_COMPLETE: "TRANSACTION_COMPLETE",
            ModbusTransactionState.RETRYING: "RETRYING TRANSACTION",
        }
        return states.get(state, None)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def default(value):
    """
    Given a python object, return the default value
    of that object.


    :returns: The default value
    """
    return type(value)()


def dict_property(store, index):
    """ Helper to create class properties of possible
    boilerplate code.

    :returns: An initialized property set
    """
    if hasattr(store, '__call__'):
        getter = lambda self: store(self)[index]
        setter = lambda self, value: store(self).__setitem__(index, value)
    elif isinstance(store, str):
        getter = lambda self: self.__getattribute__(store)[index]
        setter = lambda self, value: self.__getattribute__(store).__setitem__(
            index, value)
    else:
        getter = lambda self: store[index]
        setter = lambda self, value: store.__setitem__(index, value)

    return property(getter, setter)


# --------------------------------------------------------------------------- #
# Bit packing functions
# --------------------------------------------------------------------------- #
def pack_bitstring(bits):
    """ Creates a string out of an array of bits


    """
    ret = b''
    i = packed = 0
    for bit in bits:
        if bit:
            packed += 128
        i += 1
        if i == 8:
            ret += int2byte(packed)
            i = packed = 0
        else:
            packed >>= 1
    if 0 < i < 8:
        packed >>= (7 - i)
        ret += int2byte(packed)
    return ret


def unpack_bitstring(string):
    """ Creates bit array out of a string


    """
    byte_count = len(string)
    bits = []
    for byte in range(byte_count):
        if IS_PYTHON3:
            value = byte2int(int(string[byte]))
        else:
            value = byte2int(string[byte])
        for _ in range(8):
            bits.append((value & 1) == 1)
            value >>= 1
    return bits


def make_byte_string(s):
    """
    Returns byte string from a given string, python3 specific fix

    :return:
    """
    if IS_PYTHON3 and isinstance(s, string_types):
        s = s.encode()
    return s
# --------------------------------------------------------------------------- #
# Error Detection Functions
# --------------------------------------------------------------------------- #
def __generate_crc16_table():
    """ Generates a crc16 lookup table

    .. note:: This will only be generated once
    """
    result = []
    for byte in range(256):
        crc = 0x0000
        for _ in range(8):
            if (byte ^ crc) & 0x0001:
                crc = (crc >> 1) ^ 0xa001
            else: crc >>= 1
            byte >>= 1
        result.append(crc)
    return result

__crc16_table = __generate_crc16_table()


def computeCRC(data):
    """ Computes a crc16 on the passed in string. For modbus,
    this is only used on the binary serial protocols (in this
    case RTU).

    The difference between modbus's crc16 and a normal crc16
    is that modbus starts the crc value out at 0xffff.


    :returns: The calculated CRC
    """
    crc = 0xffff
    for a in data:
        idx = __crc16_table[(crc ^ byte2int(a)) & 0xff]
        crc = ((crc >> 8) & 0xff) ^ idx
    swapped = ((crc << 8) & 0xff00) | ((crc >> 8) & 0x00ff)
    return swapped


def checkCRC(data, check):
    """ Checks if the data matches the passed in CRC


    :returns: True if matched, False otherwise
    """
    return computeCRC(data) == check


def computeLRC(data):
    """ Used to compute the implementation
    can be found in appendex B of the serial line modbus description.


    :returns: The calculated LRC

    """
    lrc = sum(byte2int(a) for a in data) & 0xff
    lrc = (lrc ^ 0xff) + 1
    return lrc & 0xff


def checkLRC(data, check):
    """ Checks if the passed in data matches the LRC


    :returns: True if matched, False otherwise
    """
    return computeLRC(data) == check


def rtuFrameSize(data, byte_count_pos):
    """ Calculates the size of the frame based on the byte count.


    :returns: The size of the frame.


    """
    """
    customize based on YW frame sizes
    """
    return byte2int(data[byte_count_pos]) + byte_count_pos + 3


def hexlify_packets(packet):
    """
    Returns hex representation of bytestring recieved
    :param packet:
    :return:
    """
    if not packet:
        return ''
    if IS_PYTHON3:
        return " ".join([hex(byte2int(x)) for x in packet])
    else:
        return u" ".join([hex(byte2int(x)) for x in packet])
# --------------------------------------------------------------------------- #
# Exported symbols
# --------------------------------------------------------------------------- #
__all__ = [
    'pack_bitstring', 'unpack_bitstring', 'default',
    'computeCRC', 'checkCRC', 'computeLRC', 'checkLRC', 'rtuFrameSize'
]
