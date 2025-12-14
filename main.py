#! /usr/bin/python3 -u

from argparse import ArgumentParser
import dbus
import dbus.mainloop.glib
import faulthandler
from functools import partial
import os
import signal
import sys
import time
import traceback
import resource
from gi.repository import GLib
import threading


import watchdog

from modbus import ModbusRTUSerialServer
from datastore import SD230DataStore



import logging
log = logging.getLogger(__name__)

NAME = os.path.basename(__file__)
VERSION = '2.01'

__all__ = ['NAME', 'VERSION']






class Client:
    def __init__(self, tty: str, rate: int) -> None:
        self.tty = tty
        self.rate = rate
        self.rss = 0
        self.last_rss_change = 0
        self.watchdog = None
        if tty:
            self.watchdog = watchdog.Watchdog()

    def init(self) -> None:
        self.datastore = SD230DataStore()
        self.datastore.checkInit()
        self.modbusServer = ModbusRTUSerialServer(self.datastore, device=self.tty, baudrate=self.rate)
        if self.watchdog:
            self.watchdog.start()


    def destroy(self) -> None:
        self.modbusServer.close()
        self.datastore.destroy()


    def check_rss(self) -> None:
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if rss != self.rss:
            now = time.time()
            change = rss-self.rss
            rate = 0
            if self.last_rss_change > 0:
                elapsed = now - self.last_rss_change
                rate = (3600.0*change)/(elapsed*1024)
            log.info(f' rss:{rss} change:{change} rate:{rate} MB/h')
            self.rss = rss
            self.last_rss_change = now
            if self.rss > 32000:
                log.error(f'RSS reached limit, exiting')
                sys.exit()


    def update_timer(self) -> bool:
        try:
            self.modbusServer.handle()
            if self.watchdog:
                self.watchdog.update()
        except:
            log.error('Uncaught exception in update')
            traceback.print_exc()

        return True



    def run(self):
        while self.running:
            try:
                self.modbusServer.handle(threaded=True)
                if self.watchdog:
                    self.watchdog.update()
            except:
                log.error('Uncaught exception in update')
                traceback.print_exc()




    def start(self):
        self.stop()
        self.thread = threading.Thread(target=self.run)
        self.running = True
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread = None





def main():
    parser = ArgumentParser(add_help=True)
    parser.add_argument('-d', '--debug', help='enable debug logging',
                        action='store_true')
    parser.add_argument('--leak',
                        help='Enable memory leak detection', default=120)
    parser.add_argument('-m', '--mode', choices=['ascii', 'rtu'], default='rtu')
    parser.add_argument('-r', '--rate', type=int, default=9600) 
    parser.add_argument('-s', '--serial')

    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s %(levelname)s %(name)-10s %(message)s',
                        level=(logging.DEBUG if args.debug else logging.INFO))

    logging.getLogger('pymodbus.client.sync').setLevel(logging.CRITICAL)

    log.info('%s v%s', NAME, VERSION)

    signal.signal(signal.SIGINT, lambda s, f: os._exit(1))
    faulthandler.register(signal.SIGUSR1)
    faulthandler.enable()

    dbus.mainloop.glib.threads_init()
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    mainloop = GLib.MainLoop()

    tty=None
    if args.serial:
        tty = args.serial 
    client = Client(tty, args.rate)
    client.init()

    client.start()

    # non threaded operation, GLib.timeout_add(10, client.update_timer)

    GLib.timeout_add(1000, client.check_rss)

    checkLeakPeriod = int(args.leak)
    #if checkLeakPeriod > 0:
    #    log.info('Detect leaks')
    #    from gc_debug import LeakDetector
    #    leak_detector = LeakDetector()
    #    GLib.timeout_add_seconds(checkLeakPeriod, leak_detector.detect_leak)

    mainloop.run()
    client.stop()
    client.destroy()




if __name__ == "__main__":
    main()
