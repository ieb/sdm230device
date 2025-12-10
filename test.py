import sys
import os
import struct

from pymodbus.utilities import checkCRC

sys.path.insert(1, os.path.join(os.path.dirname(__file__), 'mocks'))
from datastore import SD230DataStore
from modbus import ModbusRTUSerialServer

import logging
logging.basicConfig(format='%(asctime)s %(levelname)s %(name)-10s %(message)s',
                        level=logging.INFO)

log = logging.getLogger(__name__)


def checkResponseHeader(raw, expected):
    if not raw[0] == 0x02: 
        log.error(f'Unit wrong {raw[0]}')
        raise AssertionError('wrong unit in response ')
    if not raw[1] == 0x04: 
        log.error(f'Function wrong {raw[1]}')
        raise AssertionError('wrong function in response ')
    length = len(expected)*2
    if not raw[2] == 2*length: 
        log.error(f'Length wrong {raw[2]}, expected {2*length}')
        raise AssertionError('wrong length in response ')
    crc = raw[-2:]
    crc_val = ((crc[0]) << 8) + (crc[1])

    log.info(f'checksum {crc_val}')
    if not checkCRC(raw[0:-2], crc_val):
        raise AssertionError('Bad Checksum')
    data = raw[3:-2]
    if not len(data) == 2*length:
        raise AssertionError('Data Size Wrong')
    log.info(f'data {data}')
    values = []
    for x in range((int)(length/2)):
        values.append(struct.unpack('>f', data[4*x:4*(x+1)])[0])
    log.info(f'values {values}')
    if len(values) != len(expected):
        raise AssertionError('Data Size not as expected after decoding')
    for x in range(len(expected)):
        if round(values[x],5) != round(expected[x],5):
            log.error(f'Element {x} expected {expected[x]} got {values[x]}')
            raise AssertionError('Data Size not as expected after decoding')



if __name__ == "__main__":
    datastore = SD230DataStore()
    datastore.gridTracker = False
    datastore.init()
    if not datastore.setValue('/Ac/Voltage',243): raise AssertionError('cant set value')
    if not datastore.setValue('/Ac/Current',-5.2): raise AssertionError('cant set value')
    if not datastore.setValue('/Ac/Power',1023): raise AssertionError('cant set value')
    if not datastore.setValue('/Ac/ApparentPower',1000): raise AssertionError('cant set value')
    if not datastore.setValue('/Ac/ReactivePower',100): raise AssertionError('cant set value')
    if not datastore.setValue('/Ac/PowerFactor',1.02): raise AssertionError('cant set value')
    if not datastore.setValue('/Ac/Frequency',49.2): raise AssertionError('cant set value')
    if not datastore.setValue('/Ac/Energy/Forward',1021): raise AssertionError('cant set value')
    if not datastore.setValue('/Ac/Energy/Reverse',101): raise AssertionError('cant set value')
    if not datastore.setValue('/Ac/ReactiveEnergy/Forward',1088): raise AssertionError('cant set value')
    if not datastore.setValue('/Ac/ReactiveEnergy/Reverse',1099): raise AssertionError('cant set value')
    if not datastore.setValue('/Ac/Energy/Total',10990): raise AssertionError('cant set value')
    if not datastore.setValue('/Ac/ReactiveEnergy/Total',10921): raise AssertionError('cant set value')

    if datastore.setValue('/Ac/ReactiveEnergy/Fake',10921): raise AssertionError('set non existant value')
    message = []
    address = 0x0000
    count = 18
    offset = 0
    while offset < count:
        offset = offset + datastore.packValue(address, offset, message) 


    log.info(f'{message}')

    server = ModbusRTUSerialServer(datastore)
    ## registetrs 0-17
    buffer = bytearray([0x02, 0x04, 0x00, 0x00, 0x00, 0x12, 0x70, 0x34])
    server.serial.setbuffer(buffer)
    server.handle()
    checkResponseHeader(server.serial.lastWrite, [243.0, 0.0, 0.0, -5.2, 0.0, 0.0, 1023.0, 0.0, 0.0])

    ## registeres 18-35
    buffer = bytearray([0x02, 0x04, 0x00, 0x12, 0x00, 0x12, 0xd0, 0x31])
    server.serial.setbuffer(buffer)
    server.handle()
    checkResponseHeader(server.serial.lastWrite, [1000.0, 0.0, 0.0, 100.0, 0.0, 0.0, 1.02, 0.0, 0.0])

    ## registeres 52
    buffer = bytearray([0x02, 0x04, 0x00, 0x34, 0x00, 0xc, 0xb1, 0xf2])
    server.serial.setbuffer(buffer)
    server.handle()
    checkResponseHeader(server.serial.lastWrite, [0,0,0,0,0,0])



    ## registeres 70
    buffer = bytearray([0x02, 0x04, 0x00, 0x46, 0x00, 0xc, 0x11, 0xe9])
    server.serial.setbuffer(buffer)
    server.handle()
    checkResponseHeader(server.serial.lastWrite, [49.2, 1021, 101, 1088, 1099, 0.0])


    ## registeres 200-206
    buffer = bytearray([0x02, 0x04, 0x00, 0xc8, 0x00, 0x06, 0xf1, 0xc5])
    server.serial.setbuffer(buffer)
    server.handle()
    checkResponseHeader(server.serial.lastWrite, [0,0,0])

    
    ## registeres 342-346
    buffer = bytearray([0x02, 0x04, 0x01, 0x56, 0x00, 0x04, 0x10, 0x16])
    server.serial.setbuffer(buffer)
    server.handle()
    checkResponseHeader(server.serial.lastWrite, [10990, 10921])
