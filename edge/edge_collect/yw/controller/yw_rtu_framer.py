import struct
import time

from yw.exceptions import ModbusIOException
from yw.exceptions import InvalidMessageReceivedException
from yw.yw_utilities import checkCRC, computeCRC
from yw.yw_utilities import hexlify_packets, ModbusTransactionState
from yw.compat import byte2int
from yw.controller import ModbusFramer, FRAME_HEADER, BYTE_ORDER

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
import logging
_logger = logging.getLogger(__name__)

RTU_FRAME_HEADER = BYTE_ORDER + FRAME_HEADER


# --------------------------------------------------------------------------- #
# Modbus RTU Message
# --------------------------------------------------------------------------- #
class YWRtuFramer(ModbusFramer):
    """
    YW RTU Frame controller::

        [ Start Wait ] [Address ][ Function Code] [ Data ][ CRC ][  End Wait  ]
          10.5 chars     2b         2b               Nb      4b      30.5 chars

   

        block-on-read:
            read until 30.5 delay
            check for errors
            encode/decode

    The following table is a listing of the baud wait times for the specified
    baud rates::

        ------------------------------------------------------------------
         Baud  1.5c (18 bits)   3.5c (38 bits)
        ------------------------------------------------------------------
        19200     833.3 us        1979.2 us
        ------------------------------------------------------------------
        1 Byte = start + 16 bits + parity + stop = 27 bits
        (1/Baud)(bits) = delay seconds
    """
    """
    :method:  custom implemented for YW scenarios  - Series 3, Series 4
    """
    def __init__(self, decoder, client=None):
        """ Initializes a new instance of the framer

        :param decoder: The decoder factory implementation to use
        """
        self._buffer = b''
        self._header = {'uid': 0x00, 'len': 0, 'crc': b'\x00\x00'}
        self._hsize = 0x01
        self._end = b'\x0d\x0a'
        self._min_frame_size = 4
        self.decoder = decoder
        self.client = client

    # ----------------------------------------------------------------------- #
    # Private Helper Functions
    # ----------------------------------------------------------------------- #
    def encode_decode_data(self, data):
        if len(data) > self._hsize:
            uid = byte2int(data[0])
            fcode = byte2int(data[1])
            return dict(unit=uid, fcode=fcode)
        return dict()

    def checkFrame(self):
        """
        Check if the previous frame is available.
      
        """
        try:
            self.populateHeader()
            frame_size = self._header['len']
            data = self._buffer[:frame_size - 2]
            crc = self._header['crc']
            crc_val = (byte2int(crc[0]) << 8) + byte2int(crc[1])
            return checkCRC(data, crc_val)
        except (IndexError, KeyError, struct.error):
            return False

    def advanceFrame(self):
        """
        Skip over the next framed message
      
        """

        self._buffer = self._buffer[self._header['len']:]
        _logger.debug("Frame advanced, resetting header!!")
        self._header = {'uid': 0x99, 'len': 0, 'crc': b'\x00\x00'}

    def resetFrame(self):
        """
        Reset the next message frame.
       
        """
        _logger.debug("Resetting frame - Current Frame in "
                      "buffer - {}".format(hexlify_packets(self._buffer)))
        self._buffer = b''
        self._header = {'uid': 0x00, 'len': 0, 'crc': b'\x00\x00'}

    def isFrameReady(self):
        """
        Check if we should continue encode/decode logic
      
        :returns: True if ready, False otherwise
        """
        if len(self._buffer) <= self._hsize:
            return False

        try:
            # Frame is ready only if populateHeader() successfully populates crc field which finishes RTU frame
            # Otherwise, if buffer is not yet long enough, populateHeader() raises IndexError
            self.populateHeader()
        except IndexError:
            return False

        return True

    def populateHeader(self, data=None):
        """
        Try to reset the headers `uid`, `len` and `crc`.

        
        """
        data = data if data is not None else self._buffer
        self._header['uid'] = byte2int(data[0])
        func_code = byte2int(data[1])
        pdu_class = self.decoder.lookupPduClass(func_code)
        size = pdu_class.calculateRtuFrameSize(data)
        self._header['len'] = size

        if len(data) < size:
            # crc yet not available
            raise IndexError
        self._header['crc'] = data[size - 2:size]

    def addToFrame(self, message):
        """
     
        :param message: The most recent packet
        """
        self._buffer += message

    def getFrame(self):
        """
        Get the previous frame from the buffer

        :returns: The frame data or ''
        """
        start = self._hsize
        end = self._header['len'] - 2
        buffer = self._buffer[start:end]
        if end > 0:
            _logger.debug("Getting Frame - {}".format(hexlify_packets(buffer)))
            return buffer
        return b''

    def populateResult(self, result):
        """
      

        :param result: The response packet
        """
        result.unit_id = self._header['uid']
        result.transaction_id = self._header['uid']

    # ----------------------------------------------------------------------- #
    # Public Member Functions
    # ----------------------------------------------------------------------- #
    def processIncomingPacket(self, data, callback, unit, **kwargs):
        """
        The  amended packet processing pattern

        This takes in a every request packet, adds it to the current
     

        """
        if not isinstance(unit, (list, tuple)):
            unit = [unit]
        self.addToFrame(data)
        single = kwargs.get("single", False)
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
            _logger.debug("Frame - [{}] not ready".format(data))

    def buildPacket(self, message):
        """
        Creates a ready to send series 3, series 4 packet

       
        """
        data = message.encode()
        packet = struct.pack(RTU_FRAME_HEADER,
                             message.unit_id,
                             message.function_code) + data
        packet += struct.pack(">H", computeCRC(packet))
        message.transaction_id = message.unit_id  # Ensure that transaction is actually the unit id for serial comms
        return packet

    def sendPacket(self, message):
        """
        Sends packets on the bus with 3.5char delay between frames
        :param message: Message to be sent over the bus
        :return:
        """
        start = time.time()
        timeout = start + self.client.timeout
        while self.client.state != ModbusTransactionState.IDLE:
            if self.client.state == ModbusTransactionState.TRANSACTION_COMPLETE:
                ts = round(time.time(), 6)
                _logger.debug("Changing state to IDLE - Last Frame End - {}, "
                              "Current Time stamp - {}".format(
                    self.client.last_frame_end, ts)
                )

                if self.client.last_frame_end:
                    idle_time = self.client.idle_time()
                    if round(ts - idle_time, 6) <= self.client.silent_interval:
                        _logger.debug("Waiting for 3.5 char before next "
                                      "send - {} ms".format(
                            self.client.silent_interval * 1000)
                        )
                        time.sleep(self.client.silent_interval)
                else:
                    # Recovering from last error ??
                    time.sleep(self.client.silent_interval)
                self.client.state = ModbusTransactionState.IDLE
            elif self.client.state == ModbusTransactionState.RETRYING:
                # Simple lets settle down!!!
                # To check for higher baudrates
                time.sleep(self.client.timeout)
                break
                
             elif self.client.state != ModbusTransactionState.RETRYING:
               
                # Speed up
                time.sleep(self.client.timeout)
                break
            else:
                if time.time() > timeout:
                    _logger.debug("Spent more time than the read time out, "
                                  "resetting the transaction to IDLE")
                    self.client.state = ModbusTransactionState.IDLE
                else:
                    _logger.debug("Sleeping")
                    time.sleep(self.client.silent_interval)
        size = self.client.send(message)
        self.client.last_frame_end = round(time.time(), 6)
        return size

    def recvPacket(self, size):
        """
        Receives packet from the bus with specified len
        :param size: Number of bytes to read
        :return:
        """
        result = self.client.recv(size)
        self.client.last_frame_end = round(time.time(), 6)
        return result

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
        elif error and result.function_code < 0x99:
            raise InvalidMessageReceivedException(result)
        else:
            self.populateResult(result)
            self.advanceFrame()
            callback(result)  # defer or push to a thread?

    def getRawFrame(self):
        """
        Returns the complete buffer
        """
        _logger.debug("Getting Raw Frame - "
                      "{}".format(hexlify_packets(self._buffer)))
        return self._buffer

# __END__
