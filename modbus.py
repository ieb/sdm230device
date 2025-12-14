
from pymodbus.framer import ModbusFramer
import serial
import time
from pymodbus.constants import Defaults
from pymodbus.factory import ServerDecoder
from pymodbus.framer.rtu_framer import ModbusRtuFramer
from pymodbus.framer.ascii_framer import ModbusAsciiFramer
from pymodbus.utilities import computeLRC
from pymodbus.register_read_message import ReadInputRegistersRequest, ReadInputRegistersResponse
from datastore import SD230DataStore


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
import logging
log = logging.getLogger(__name__)


class StdinSerial(object):
    '''
    Allows manual testing on stdin with Ascii modbus strings
    '''

    def __init__(self) -> None:
        self._framer = ModbusAsciiFramer(ServerDecoder())

    @property
    def framer(self) -> ModbusFramer:
        return self._framer

    @property
    def in_waiting(self) -> int:
        return 1024

    def read(self, *args, **kwargs) -> bytearray:
        line = input('-->:')
        if line:
            line = line.rstrip()
            lrc = computeLRC(bytes.fromhex(line[1:]))
            b = bytearray()
            b.extend(line.encode())
            b.extend(f'{lrc:02x}'.encode())
            b.extend('\r\n'.encode())
            return b
        return None

    def write(self, value) -> None:
        print(f'<--:{value.decode("utf-8")}')

class CannedSerial(object):
    '''
    Emits an automated test RTU test pattern
    '''

    testpattern = [
     bytearray([0x02,0x04,0x00,0x00,0x00,0x12,0x70,0x34]),
     bytearray([0x02,0x04,0x00,0x12,0x00,0x12,0xd0,0x31]),
     bytearray([0x02,0x04,0x00,0x34,0x00,0x0c,0xb1,0xf2]),
     bytearray([0x02,0x04,0x00,0x46,0x00,0x0c,0x11,0xe9]),
     bytearray([0x02,0x04,0x00,0xc8,0x00,0x06,0xf1,0xc5]),
     bytearray([0x02,0x04,0x01,0x56,0x00,0x04,0x10,0x16]),
    ]
    description = [
        ['0-17','020424xxxxxxxx0000000000000000xxxxxxxx0000000000000000xxxxxxxx0000000000000000CCCC'],
        ['18-35','020424xxxxxxxx00000000000000000xxxxxxxx0000000000000000xxxxxxxx0000000000000000CCCC'],
        ['52-63','020418000000000000000000000000000000000000000000000000CCCC'],
        ['70-81','020418xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx00000000CCCC'],
        ['200-206','02040c000000000000000000000000CCCC'],
        ['342-346','020408xxxxxxxxxxxxxxxxCCCC'],
    ]

    def __init__(self) -> None:
        self.reqN = 0
        self.fast = False
        self._framer = ModbusRtuFramer(ServerDecoder())

    @property
    def framer(self) -> ModbusFramer:
        return self._framer


    @property
    def in_waiting(self) -> int:
        return 1024

    def read(self, *args, **kwargs) -> bytearray:
        time.sleep(0.2)
        self.fast = not self.fast
        if self.fast:
            return self.testpattern[0]
        else:
            self.reqN = self.reqN + 1
            if self.reqN == len(self.testpattern):
                self.reqN = 1
            log.debug(self.description[self.reqN][0])
            log.debug(self.description[self.reqN][1])
            return self.testpattern[self.reqN]

    def write(self, value) -> None:
        log.info(f'{value.hex()}')


class ModbusRTUSerialServer(object):
    '''
    A very much simplified RTU Serial server to work with a GLIb main loop.
    '''


    def __init__(self, datastore: SD230DataStore, device: str=None , 
            unit:int=0x02,
            baudrate:int=Defaults.Baudrate) -> None:
        """ Overloaded initializer for the socket server

        :param port: The serial port to attach to
        :param stopbits: The number of stop bits to use
        :param bytesize: The bytesize of the serial messages
        :param parity: Which kind of parity to use
        :param baudrate: The baud rate to use for the serial device
        :param timeout: The timeout to use for the serial device
        """
        self.unit = unit
        # datacontext implements 
        self.datastore = datastore
        self.last_frame_end = time.time()
        # 3.5 chars == 38 bits ( for 8,1,N)
        self.silent_time = (1/baudrate)*38

        if device != None:
            self.framer = ModbusRtuFramer(ServerDecoder())
            self.serial = serial.Serial(port=device,
                                        timeout=3, 
                                        bytesize=8,
                                        stopbits=1,
                                        baudrate=baudrate,
                                        parity='N')
        else:
            self.serial = CannedSerial()
            self.framer = self.serial.framer

    

    def handle(self, threaded: bool = False) -> None:
        #try:
        self.datastore.checkInit()
        data = None
        if self.serial:
            if self.serial.in_waiting > 0:
                log.debug(f'Try read {self.serial}')
                # only read what is available to avoid blocking.
                data = self.serial.read(self.serial.in_waiting)
            else:
                time.sleep(0.2)

        if data:
            log.debug(f'Got data {data}')
            now = time.time()
            if (now - self.last_frame_end) > 1:
                # last data base > 1s ago, reset the frame
                log.debug('Frame timed out, resetting')
                self.framer.resetFrame()
            self.last_frame_end = now
            while True:
                self.framer.processIncomingPacket(data, self.respond,
                                              self.unit, single=True)
                if not self.framer.isFrameReady():
                    break
                data = bytes()

        #except Exception as msg:
        #    # Since we only have a single socket, we cannot exit
        #    # Clear frame buffer
        #    self.framer.resetFrame()
        #    log.info("Error: Serial error occurred %s" % msg)

    def respond(self, request) -> None:
        '''
        request contains   ReadInputRegistersRequest

        '''
        log.debug(f'Got request {request}')
        if isinstance(request, ReadInputRegistersRequest):
            start = time.time()
            reg_count = 0
            registers = []
            while reg_count < request.count:
                reg_count = reg_count + self.datastore.packValue(request.address, reg_count, registers)
            # message now contains the bytes of the message,
            # may need to wait 3.5 
            # pack the result, encode and send
            responseMessage = ReadInputRegistersResponse(registers, unit=request.unit_id)
            log.debug(f'Created message {responseMessage}')
            packet = self.framer.buildPacket(responseMessage)
            log.debug(f'Created packet {packet}')
            log.debug(f'Took {time.time()-start}s')

            # ensure there is at least 3.5 chars of silence between packets.
            now = time.time()
            end_silent = self.last_frame_end + self.silent_time
            if now < end_silent:
                log.debug('sleep before end')
                time.sleep(end_silent - now)

            self.serial.write(packet)
            self.last_frame_end = time.time()



    def close(self) -> None:
        """ Callback for stopping the running server
        """
        log.debug("Modbus server stopped")
        if self.serial != None:
            self.serial.close()
            self.serial = None