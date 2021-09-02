"""
yw Interfaces
---------------------

A collection of base classes that are used throughout
the yw library.

Interfaces are implemented with custom params to extend Series 3, Series 4 data collection thru RTU
"""
from yw.exceptions import (NotImplementedException,
                                 MessageRegisterException)


# --------------------------------------------------------------------------- #
# Generic
# --------------------------------------------------------------------------- #
class Singleton(object):
    """
    Singleton base class
    http://mail.python.org/pipermail/python-list/2007-July/450681.html
    """
    """
    :method:  custom implemented for YW scenarios  - Series 3, Series 4
    """
    def __new__(cls, *args, **kwargs):
        """ Create a new instance
        """
        if '_inst' not in vars(cls):
            cls._inst = object.__new__(cls)
        return cls._inst


# --------------------------------------------------------------------------- #
# Project Specific
# --------------------------------------------------------------------------- #
class IModbusDecoder(object):
    """ Modbus Decoder Base Class


    """

    def decode(self, message):
        """ Wrapper to decode a given packet


        :return: The decoded modbus message or None if error
        """
        raise NotImplementedException(
            "Method not implemented by derived class")

    def lookupPduClass(self, function_code):
        """ Use `function_code` to determine the class of the PDU.


        :returns: The class of the PDU that has a matching `function_code`.
        """
        raise NotImplementedException(
            "Method not implemented by derived class")

    def register(self, function=None):
        """
        Registers a function and sub function class with the decoder

        :return:
        """
        raise NotImplementedException(
            "Method not implemented by derived class")


class IModbusFramer(object):
    """
     a new Framer object (tcp, rtu, ascii, series 3, series 4).
    """

    def checkFrame(self):
        """ Check and decode the next frame

        :returns: True if we successful, False otherwise
        """
        raise NotImplementedException(
            "Method not implemented by derived class")

    def advanceFrame(self):
        """ Iterate over the current framed message
        """
        raise NotImplementedException(
            "Method not implemented by derived class")

    def addToFrame(self, message):
        """  used before the decoding while loop to add the received   data to the buffer handle.


        """
        raise NotImplementedException(
            "Method not implemented by derived class")

    def isFrameReady(self):
        """ Check if we should continue decode logic for given VFD connection



        :returns: True if ready, False otherwise
        """
        raise NotImplementedException(
            "Method not implemented by derived class")

    def getFrame(self):
        """ Get the next frame from the buffer

        :returns: The frame data or ''
        """
        raise NotImplementedException(
            "Method not implemented by derived class")

    def populateResult(self, result):
        """ Populates the modbus result with current frame header

        We basically copy the data back over from the current header
        to the result header. This may not be needed for serial messages.

        :param result: The response packet
        """
        raise NotImplementedException(
            "Method not implemented by derived class")

    def processIncomingPacket(self, data, callback):
        """ The new packet processing pattern pushed to the callback
        function to process and send.


        """
        raise NotImplementedException(
            "Method not implemented by derived class")

    def buildPacket(self, message):
        """ Creates a ready to send modbus packet


        :returns: The built packet
        """
        raise NotImplementedException(
            "Method not implemented by derived class")


class IModbusSlaveContext(object):
    """
    Interface for a modbus slave data context


    """
    __fx_mapper = {2: 'd', 4: 'i'}
    __fx_mapper.update([(i, 'h') for i in [3, 6, 16, 22, 23]])
    __fx_mapper.update([(i, 'c') for i in [1, 5, 15]])

    def decode(self, fx):
        """ Converts the function code to the datastore to


        :returns: one of [d(iscretes),i(nputs),h(olding),c(oils)
        """
        """
        :returns: one of [d(iscretes),i(nputs),h(olding),c(oils),r(ead),c(custom register)
        """
        return self.__fx_mapper[fx]

    def reset(self):
        """ Resets all the datastores to their default values
        """
        raise NotImplementedException("Context Reset")

    def validate(self, fx, address, count=1):
        """ Validates the request to make sure it is in range


        :returns: True if the request in within range, False otherwise
        """
        raise NotImplementedException("validate context values")

    def getValues(self, fx, address, count=1):
        """ Get `count` values from datastore


        :returns: The requested values from a:a+c
        """
        raise NotImplementedException("get context values")

    def setValues(self, fx, address, values):
        """ Sets the datastore with the supplied values

        """
        raise NotImplementedException("set context values")


class IPayloadBuilder(object):
    """
    This is an interface to a class that can build a payload

    """

    def build(self):
        """ Return the payload buffer as a list



        :returns: The payload buffer as a list
        """
        raise NotImplementedException("set context values")


# --------------------------------------------------------------------------- #
# Exported symbols
# --------------------------------------------------------------------------- #
__all__ = [
    'Singleton',
    'IModbusDecoder', 'IModbusFramer', 'IModbusSlaveContext',
    'IPayloadBuilder',
]
