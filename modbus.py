
import serial
import time
import struct
import random
from datastore import SD230DataStore


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
import logging
log = logging.getLogger(__name__)




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

class RandomSerial(object):


    testpattern = bytearray([0x34,0x03,0x03,0x20,0x00,0x00,0x10,0x01,
         0x04,0x00,0x00,0x00,0x0e,0x71,0xce,0x01,
         0x04,0x00,0x00,0x00,0x0e,0x71,0xce,0x02,
         0x04,0x00,0x00,0x00,0x12,0x70,0x34,0x02,
         0x04,0x00,0x00,0x00,0x12,0x70,0x34,0x03,
         0x03,0x20,0x00,0x00,0x10,0x4e,0x24,0x02,
         0x04,0x00,0x00,0x00,0x12,0x70,0x34,0x03,
         0x03,0x20,0x00,0x00,0x10,0x4e,0x24,0x03,
         0x03,0x20,0x00,0x00,0x10,0x4e,0x24,0x03,
         0x03,0x20,0x00,0x00,0x10,0x4e,0x24,0x04,
         0x03,0x00,0x06,0x00,0x02,0x24,0x5f,0x04,
         0x03,0x00,0x06,0x00,0x02,0x24,0x5f,0x34,
         0x03,0x03,0x20,0x00,0x00,0x10,0x01,0x04,
         0x00,0x00,0x00,0x0e,0x71,0xce,0x01,0x04,
         0x00,0x00,0x00,0x0e,0x71,0xce,0x02,0x04,
         0x00,0x00,0x00,0x12,0x70,0x34,0x02,0x04,
         0x00,0x00,0x00,0x12,0x70,0x34,0x03,0x03,
         0x20,0x00,0x00,0x10,0x4e,0x24,0x03,0x03,
         0x20,0x00,0x00,0x10,0x4e,0x24,0x04,0x03,
         0x00,0x06,0x00,0x02,0x24,0x5f,0x04,0x03,
         0x00,0x06,0x00,0x02,0x24,0x5f,0x01,0x04,
         0x00,0x00,0x00,0x0e,0x71,0xce,0x01,0x04,
         0x00,0x00,0x00,0x0e,0x71,0xce,0x02,0x04,
         0x00,0x00,0x00,0x12,0x70,0x34,0x02,0x04,
         0x00,0x00,0x00,0x12,0x70,0x34,0x03,0x03,
         0x20,0x00,0x00,0x10,0x4e,0x24,0x03,0x03,
         0x20,0x00,0x00,0x10,0x4e,0x24,0x04,0x03,
         0x00,0x06,0x00,0x02,0x24,0x5f,0x34,0x03,
         0x03,0x20,0x00,0x00,0x10,0x04,0x03,0x00,
         0x06,0x00,0x02,0x24,0x5f,0x01,0x04,0x00,
         0x00,0x00,0x0e,0x71,0xce,0x01,0x04,0x00,
         0x00,0x00,0x0e,0x71,0xce,0x02,0x04,0x00,
         0x00,0x00,0x12,0x70,0x34,0x02,0x04,0x00,
         0x00,0x00,0x12,0x70,0x34,0x03,0x03,0x20,
         0x00,0x00,0x10,0x4e,0x24,0x03,0x03,0x20,
         0x00,0x00,0x10,0x4e,0x24,0x04,0x03,0x00,
         0x06,0x00,0x02,0x24,0x5f,0x02,0x04,0x00,
         0x00,0x00,0x12,0x70,0x34,0x02,0x04,0x00,
         0x12,0x00,0x12,0xd0,0x31,0x02,0x04,0x00,
         0x34,0x00,0x0c,0xb1,0xf2,0x02,0x04,0x00,
         0x46,0x00,0x0c,0x11,0xe9,0x02,0x04,0x00,
         0xc8,0x00,0x06,0xf1,0xc5,0x02,0x04,0x01,
         0x56,0x00,0x04,0x10,0x16])


    def __init__(self) -> None:
        self._bp = 0



    @property
    def in_waiting(self) -> int:
        return 1024

    def read(self, *args, **kwargs) -> bytearray:
        size = random.randint(0, 22)
        buffer = bytearray()
        for n in range(size):
            buffer.append(self.testpattern[self._bp])
            self._bp = (self._bp+1)%len(self.testpattern)
        return buffer

    def write(self, value) -> None:
        log.info(f'{value.hex()}')

class Request(object):
    def __init__(self, frame) -> None:
        self.unit_id = int(frame[0])
        self.function = int(frame[1])
        self.address, self.count = struct.unpack(">HH", frame[2:6])
        self.frame = bytearray(frame)
    def __str__(self) -> str:
        return f'unit:{self.unit_id} fn:{self.function} addr:{self.address} count:{self.count} Frame:{self.frame.hex()}'
        pass

    def key(self):
        return f'{self.unit_id}:{self.function}:{self.address}:{self.count}'





class ModbusRTUSerialServer(object):
    '''
    A very much simplified RTU Serial server to work with a GLIb main loop.
    '''


    def __init__(self, datastore: SD230DataStore, device , 
            unit:int=0x02,
            baudrate:int=9600) -> None:
        """ Overloaded initializer for the socket server

        :param port: The serial port to attach to
        :param stopbits: The number of stop bits to use
        :param bytesize: The bytesize of the serial messages
        :param parity: Which kind of parity to use
        :param baudrate: The baud rate to use for the serial device
        :param timeout: The timeout to use for the serial device
        """
        self.unit = unit
        self.packetCount = {}
        self.totalPacketCount = 0
        self._buffer = b''
        self._bp = 0


        # datacontext implements 
        self.datastore = datastore
        self.__crc16_table = self.generate_crc16_table()

        if device != None:
            self.serial = serial.Serial(port=device,
                                        timeout=1, 
                                        bytesize=8,
                                        stopbits=1,
                                        baudrate=baudrate,
                                        parity='N')
        else:
            self.serial = RandomSerial()


    def generate_crc16_table(self):
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


    def computeCRC(self, data):
        """ Computes a crc16 on the passed in string. For modbus,
        this is only used on the binary serial protocols (in this
        case RTU).

        The difference between modbus's crc16 and a normal crc16
        is that modbus starts the crc value out at 0xffff.

        :param data: The data to create a crc16 of
        :returns: The calculated CRC
        """
        crc = 0xffff
        for a in data:
            idx = self.__crc16_table[(crc ^ a) & 0xff]
            crc = ((crc >> 8) & 0xff) ^ idx
        swapped = ((crc << 8) & 0xff00) | ((crc >> 8) & 0x00ff)
        return swapped


    def checkCRC(self, data, check):
        """ Checks if the data matches the passed in CRC

        :param data: The data to create a crc16 of
        :param check: The CRC to validate
        :returns: True if matched, False otherwise
        """
        return self.computeCRC(data) == check

    def countPackets(self, key):
        self.totalPacketCount = self.totalPacketCount + 1
        if key in self.packetCount:
            self.packetCount[key] = self.packetCount[key] + 1
        else:
            self.packetCount[key] = 1
        if self.totalPacketCount%100 == 0:
            log.debug(f'Total:{self.totalPacketCount} {self.packetCount}')


    def checkPacket(self, packet):
        """
        Check if the next frame is available.
        Return True if we were successful.

        1. Populate header
        2. Discard frame if UID does not match
        """
        frame_size = len(packet)
        data = packet[:frame_size - 2]
        crc = packet[frame_size - 2:frame_size]
        crc_val = (crc[0] << 8) + crc[1]
        if self.checkCRC(data, crc_val):
            log.debug(f'Check ok')
            return True
        else:
            log.info(f'Check fail')
            return False



    def sendReadResponse(self, request, response):
        result = b''
        for register in response:
            result += struct.pack('>H', register)

        packet = struct.pack(">BBB",
                             request.unit_id,
                             request.function,
                             len(response)*2
                             )
        packet += result
        packet += struct.pack(">H", self.computeCRC(packet))
        if self.checkPacket(packet):
            log.debug(f'send {packet.hex()}')
        else:
            log.info(f'send {packet.hex()}')
        self.checkPacket(packet)
        self.serial.write(packet)



    '''
    IllegalFunction         = 0x01
    IllegalAddress          = 0x02
    IllegalValue            = 0x03
    SlaveFailure            = 0x04
    Acknowledge             = 0x05
    SlaveBusy               = 0x06
    MemoryParityError       = 0x08
    GatewayPathUnavailable  = 0x0A
    GatewayNoResponse       = 0x0B
    '''


    def sendIllegalFunction(self, request):
        packet = struct.pack(">BB",
                             request.unit_id,
                             request.fn | 0x80,
                             0x01)
        packet += struct.pack(">H", self.computeCRC(packet))
        self.serial.write(packet)

    def sendIllegalCount(self, request):
        packet = struct.pack(">BB",
                             request.unit_id,
                             request.fn | 0x80,
                             0x03)
        packet += struct.pack(">H", self.computeCRC(packet))
        self.serial.write(packet)


    def decodeFrame(self, frame):
        if len(frame) == 8:
            request = Request(frame)
            crc = struct.unpack('>H', frame[6:8])[0]
            if self.checkCRC(frame[0:-2], crc):
                # frame is valid, extract values
                return request
            elif request.unit_id == 2 and request.function == 4:
                log.info(f'Rejected {request}')
        else:
            log.info("Frame not len 8")
        return None

    def processIncomingPacket(self, data):
        # add the data to the end of the packet
        # then scan for units of interest
        # then test for a valid request frame
        #
        if data:
            self._buffer += data
            # scan upto the buffer - 8, because all requests are 8 long
            # and this a slave
            log.debug(f'start {self._bp} {len(self._buffer)} {self._buffer.hex()}')
            while self._bp <= len(self._buffer)-8:
                request = self.decodeFrame(self._buffer[self._bp:self._bp+8])
                if request:
                    self.countPackets(request.key())
                    if request.unit_id == self.unit:
                        if ( request.function == 4):
                            # input
                            if request.count > 125:
                                self.sendIllegalCount(request)
                            else:
                                reg_count = 0
                                registers = []
                                while reg_count < request.count:
                                    reg_count = reg_count + self.datastore.packValue(request.address, reg_count, registers)
                                log.debug(f"ok {request} {self._buffer.hex()}")
                                self.sendReadResponse(request, registers)
                        else:
                            self.sendIllegalFunction(request)
                            log.info(f"error {request} ")
                    else:
                        # pass, ignore since not this unit
                        log.debug(f"ignore {request} {self._buffer.hex()} ")
                    self._buffer = self._buffer[self._bp+8:]
                    self._bp = 0
                else:
                    self._bp = self._bp+1
            self._bp = self._bp-1
            if self._bp < 0:
                self._bp = 0
            log.debug(f'end {self._bp} {len(self._buffer)} {self._buffer.hex()}')





    

    def handle(self, threaded: bool = False) -> None:
        #try:
        self.datastore.checkInit()
        data = None
        if threaded:
            if self.serial:
                log.debug(f'Try read {self.serial}')
                #  Minimum valid command is 8 bytes, wait 1s for that to arrive
                self.processIncomingPacket(self.serial.read(8))
        else:
            if self.serial:
                if self.serial.in_waiting > 0:
                    # only read what is available to avoid blocking.
                    data = self.serial.read(self.serial.in_waiting)






    def close(self) -> None:
        """ Callback for stopping the running server
        """
        log.debug("Modbus server stopped")
        if self.serial != None:
            self.serial.close()
            self.serial = None