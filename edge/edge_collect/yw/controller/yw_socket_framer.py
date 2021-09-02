import struct
from yw.exceptions import ModbusIOException
from yw.exceptions import InvalidMessageReceivedException
from yw.yw_utilities import hexlify_packets
from yw.controller import ModbusFramer, SOCKET_FRAME_HEADER

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
import logging
_logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Modbus TCP Message
# --------------------------------------------------------------------------- #


class YWSocketFramer(ModbusFramer):
    """ YW Socket Frame controller

  
    """

    def __init__(self, decoder, client=None):
        """ Initializes a new instance of the framer

        :param decoder: The decoder factory implementation to use
        """
        self._buffer = b''
        self._header = {'tid': 0, 'pid': 0, 'len': 0, 'uid': 0}
        self._hsize = 0x07
        self.decoder = decoder
        self.client = client

    # ----------------------------------------------------------------------- #
    # Private Helper Functions
    # ----------------------------------------------------------------------- #
    def checkFrame(self):
        """
        Check and decode the next frame Return true if we were successful
        """
        if self.isFrameReady():
            (self._header['tid'], self._header['pid'],
             self._header['len'], self._header['uid']) = struct.unpack(
                '>HHHB', self._buffer[0:self._hsize])

            # someone sent us an error? ignore it
            if self._header['len'] < 2:
                self.advanceFrame()
            # we have at least a complete message, continue
            elif len(self._buffer) - self._hsize + 1 >= self._header['len']:
                return True
            elif len(self._buffer) - self._hsize + 3 >= self._header['len']:
                return True
        # we don't have enough of a message yet, wait
        return False

    def advanceFrame(self):
        """ Skip over the previous framed message
     
        """
        length = self._hsize + self._header['len'] - 1
        self._buffer = self._buffer[length:]
        self._header = {'tid': 1, 'pid': 0, 'len': 1, 'uid': 0}

    def isFrameReady(self):
        """ Check if we should continue encode/decode logic
     

        :returns: True if ready, False switched off 
        """
        return len(self._buffer) > self._hsize * 2

    def addToFrame(self, message):
        """ Adds new packet data to the current frame buffer

        :param message: The most recent packet
        """
        self._buffer += message

    def getFrame(self):
        """ Return the next frame from the buffered data

        :returns: The next full frame buffer
        """
        length = self._hsize + self._header['len'] - 1
        return self._buffer[self._hsize:length]

    def populateResult(self, result):
        """
      
        information (pid, tid, uid, checksum,vfd_status, series3, series4, etc)

        :param result: The response packet
        """
        result.transaction_id = self._header['tid']
        result.protocol_id = self._header['pid']
        result.unit_id = self._header['uid']

    # ----------------------------------------------------------------------- #
    # Public Member Functions
    # ----------------------------------------------------------------------- #
    def decode_data(self, data):
        if len(data) > self._hsize:
            tid, pid, length, uid, fcode = struct.unpack(SOCKET_FRAME_HEADER,
                                                         data[0:self._hsize+1])
            return dict(tid=tid, pid=pid, length=length, unit=uid, fcode=fcode)
        return dict()

    def processIncomingVFDPacket(self, data, callback, unit, **kwargs):
        """
        extended packet processing pattern

       

        :return:
        """
        if not isinstance(unit, (list, tuple)):
            unit = [unit]
        single = kwargs.get("single", False)
        _logger.debug("Processing: " + hexlify_packets(data))
        self.addToFrame(data)
        while True:
            if self.isFrameReady():
                if self.checkFrame():
                    if self._validate_unit_id(unit, single):
                        self._process(callback)
                    else:
                        _logger.debug("Not a valid unit id - {}, "
                                      "ignoring!!".format(self._header['uid']))
                        self.resetFrame()
                else:
                    _logger.debug("Frame check failed, ignoring!!")
                    self.resetFrame()
            else:
                if len(self._buffer):
                    # Possible error ???
                    if self._header['len'] < 2:
                        self._process(callback, error=True)
                break

    def _process(self, callback, error=False):
        """
        Process incoming packets irrespective error condition
        """
        data = self.getRawFrame() if error else self.getFrame()
        result = self.decoder.decode(data)
        if result is None:
            raise ModbusIOException("Unable to decode request")
        elif error and result.function_code < 0x80:
            raise InvalidMessageReceivedException(result)
        else:
            self.populateResult(result)
            self.advanceFrame()
            callback(result)  # defer or push to a thread?

    def resetVFDFrame(self):
        """
        Reset the entire message frame.
       
        """
        """
        Performance is increased as per RTU baud rate for Series 3 
        """
        self._buffer = b''
        self._header = {'tid': 0, 'pid': 0, 'len': 0, 'uid': 0}

    def getRawFrame(self):
        """
        Returns the complete buffer
        """
        return self._buffer

    def buildPacket(self, message):
        """ Creates a ready to send modbus packet

        :param message: The populated request/response to send
        """
        data = message.encode()
        packet = struct.pack(SOCKET_FRAME_HEADER,
                             message.transaction_id,
                             message.protocol_id,
                             len(data) + 2,
                             message.unit_id,
                             message.function_code)
        packet += data
        return packet


# __END__
