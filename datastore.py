import struct
import dbus
import time
import os
from typing import Callable, ValuesView
import logging
log = logging.getLogger(__name__)


VE_INTERFACE = "com.victronenergy.BusItem"

# Note, currently not used, as update latency was too high.
# Blocking get may be no better.
class BusItemTracker(object):
    '''
    Watches the dbus for changes to a single value on a service.
    The value is available at .value, it will be None is no value is present
    @param bus dbus object, session or system
    @param serviceName  eg com.victronenergy.system
    @param path path of the property eg /Ac/L1/Power
    '''

    dbus_int_types = (dbus.Int32, dbus.UInt32, dbus.Byte, dbus.Int16, dbus.UInt16, dbus.UInt32, dbus.Int64, dbus.UInt64)


    def __init__(self, bus, serviceName: str,  path: str, onchange: Callable ) -> None:
        self._path = path
        self._value = None
        self._onchange = onchange
        self._values = {}
        self._serviceName = serviceName

        self.lastChange = time.time()

        self._match = bus.get_object(serviceName, path, introspect=False).connect_to_signal(
            "ItemsChanged", self._items_changed_handler)
        log.info(f' added tracker for  {serviceName} {path}')



    def __del__(self) -> None:
        self._match.remove()
        self._match = None
    
    @property
    def value(self):
        return self._value
    
    def unwrap_dbus_value(self, val):
        """Converts D-Bus values back to the original type. For example if val is of type DBus.Double,
        a float will be returned."""
        if isinstance(val, self.dbus_int_types):
            return int(val)
        if isinstance(val, dbus.Double):
            return float(val)
        if isinstance(val, dbus.Array):
            v = [self.unwrap_dbus_value(x) for x in val]
            return None if len(v) == 0 else v
        if isinstance(val, (dbus.Signature, dbus.String)):
            return str(val)
        # Python has no byte type, so we convert to an integer.
        if isinstance(val, dbus.Byte):
            return int(val)
        if isinstance(val, dbus.ByteArray):
            return "".join([bytes(x) for x in val])
        if isinstance(val, (list, tuple)):
            return [self.unwrap_dbus_value(x) for x in val]
        if isinstance(val, (dbus.Dictionary, dict)):
            # Do not unwrap the keys, see comment in wrap_dbus_value
            return dict([(x, self.unwrap_dbus_value(y)) for x, y in val.items()])
        if isinstance(val, dbus.Boolean):
            return bool(val)
        return val

    # TODO, handle items being removed
    def _items_changed_handler(self, items: dict) -> None:
        if not isinstance(items, dict):
            return
        self.lastChange = time.time()
        self._values.clear()
        for path, changes in items.items():
            try:
                self._values[str(path)] = self.unwrap_dbus_value(changes['Value'])
            except KeyError:
                continue
        self._onchange(self._values)

    def getInitialValues(self, bus, paths: str) -> dict:
        dbusValues = bus.call_blocking(self._serviceName, '/', VE_INTERFACE, 'GetValue', '', [])
        values = {}
        for path,v in dbusValues.items():
            fullPath = f'/{path}'
            if fullPath in paths:
                values[fullPath] = self.unwrap_dbus_value(v)
                log.debug(f'Initial {fullPath} {values[fullPath]}')
            else:
                log.debug(f'Drop path {fullPath}')
        return values

    def isDead(self) -> bool:
        return ((time.time() - self.lastChange) > 30)

class SD230DataStore(object):
    '''
    Watches the dbus to pack a map with values.
    '''

    dbusMap = {
        0x0000: '/Ac/Voltage',
        0x0006: '/Ac/Current',
        0x000c: '/Ac/Power',
        0x0012: '/Ac/ApparentPower',
        0x0018: '/Ac/ReactivePower',
        0x001E: '/Ac/PowerFactor',
        0x0046: '/Ac/Frequency',
        0x0048: '/Ac/Energy/Forward', 
        0x004a: '/Ac/Energy/Reverse', 
        0x004c: '/Ac/Energy/ReactiveForward',
        0x004e: '/Ac/Energy/ReactiveReverse',
        0x0156: '/Ac/Energy/Total',
        0x0158: '/Ac/Energy/ReactiveTotal', 
    }

    def __init__(self) -> None:
        super().__init__()
        self.dbusConn = dbus.SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else dbus.SystemBus()
        self.dbusValues = {}
        self.pathsSeen = {}
        self.useServiceTracker = False
        self.gridTracker = None
        dbusNames = self.dbusConn.list_names()
        self.gridServiceName = None
        for x in dbusNames:
            s = str(x)
            if s.startswith('com.victronenergy.grid'):
                self.gridServiceName = s
        log.info(f' grid service name {self.gridServiceName}')
        if self.gridServiceName == None:
            raise Exception('Cant find grid service name in dbus')




    def checkInit(self) -> None:
        # create watches on the dbus for each of the entries in the dbus map
        self.createServiceTracker()

    def destroy(self) -> None:
        self.deleteServiceTracker()

    def deleteServiceTracker(self) -> None:
        if self.gridTracker:
            log.info(f'Destroy grid service tracker {self}')
            self.gridTracker.__del__()
            self.gridTracker = None



    def createServiceTracker(self) -> None:
        '''
        Create a Dbus tracker to recieve changes.
        Skip if already available.
        '''
        if self.useServiceTracker:
            if self.gridTracker:
                if self.gridTracker.isDead():
                    log.info(f'Grid Tracker dead, recreate')
                    self.deleteServiceTracker()
            if self.gridTracker == None:
                if (self.gridTracker == None 
                    and self.gridServiceName != None):
                    self.gridTracker = BusItemTracker(self.dbusConn, self.gridServiceName, '/', self.gridChanged)
                    # get the inital values
                    self.dbusValues = self.gridTracker.getInitialValues(self.dbusConn, self.dbusMap.values())
                    for path in self.dbusMap.values():
                        self.pathsSeen[path] = time.time()

                else:
                    log.error("No grid tracker created ")


    def gridChanged(self, values: dict) -> None:
        '''
        When the dbus value changes update the local copy
        to be used when packing a register.
        '''
        now = time.time()
        for path, value in values.items():
            if path in self.dbusMap.values():
                log.info(f" Update {path} value {value} age {now-self.pathsSeen[path]}")
                self.dbusValues[path] = value
                self.pathsSeen[path] = now

    def packValue(self, address: int, offset: int, message: list) -> int:
        '''
        Pack the message with the register as int16 and return the 
        number of registers that were packed. registers are always uint16 stored
        bigendian '>2H' 
        the SDM230 uses 32 bit floats in IEE 754 format
        '''
        register = address+offset
        path = None
        if register in self.dbusMap:
            # pack 32 bit floats in IEE 754 format.
            path = self.dbusMap[register]
            value = None
            if self.useServiceTracker:
                if path in self.dbusValues:
                    value = float(self.dbusValues[path])
            else:
                try:
                    start = time.time()
                    dbusValue = self.dbusConn.call_blocking(self.gridServiceName, path, VE_INTERFACE, 'GetValue', '', [])
                    log.debug(f'DBus Call took {time.time() - start} {dbusValue}')
                    if dbusValue != None:
                        value = float(dbusValue)
                except dbus.exceptions.DBusException:
                    log.error(f'Cant get value on {self.gridServiceName}:{path}')
            if value != None:
                packed = struct.unpack('>2H', struct.pack('>f', value))
                log.debug(f'packed {register} {path} {value} as {packed}')
                message.extend(packed)
            else:
                log.info(f'packed {register} {path} no value')
                message.extend([0x00, 0x00])
            return 2
        else:
            log.debug(f'skip {register} ')
            message.extend([0x00])
            return 1

    def setValue(self, path: str, value: float) -> bool:
        if path in self.dbusMap.values():
            self.dbusValues[path] = value
            return True
        return False





