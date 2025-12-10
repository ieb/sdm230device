
# SDM230 Software Grid meter 

This acts as a SDM230 Modbus RTU grid meter backed by the GX DBus data. It will respond to modbus RTU input register requests emitting the registers. Values come from the DBus locations which are watched for changes. 

# developing

The UV setup is for local testing only, do not use on the GX device which has everything as part of the VenusOS image. Most attempts to change that image fail as many of the binaries for development are not built by Victron in a way that can be used.



# Installation

In the GX device


Then copy everything here into that location

    mkdir /data/sdm230device
    scp -r . root@192.168.1.101:/data/sdm230device

    or

    cd /data
    git clone https://github.com/ieb/sdm230device.git /data/sdm230device

Run the install script



    cd /data/sdm230device
    # cleanup anything left from local development
    rm -rf .venv
    find . -name __pycache__ -exec rm -rf {} \;

    # set permissions in case.
    chmod 1755 /data/sdm230device
    chmod 755 /data/sdm230device/service/run
    chmod 755 /data/sdm230device/service/log/run

    # enable the service
    ln -s /data/sdm230device/service /service/sdm230device

    # stop tty scanning for the chosen device
    /opt/victronenergy/serial-starter/stop-tty.sh ttyUSB0

To survive a restart append the following lines to /data/rc.local

    /opt/victronenergy/serial-starter/stop-tty.sh ttyUSB0
    ln -s /data/sdm230device/service /service/sdm230device

Here check that the service/run file has the right command line, here using /dev/ttyUSB0

    exec /data/sdm230device/main.py -s /dev/ttyUSB0 -r 9600



Start the service

    svc -u /service/sdm230device

## debugging

Update the code from local development

    scp *.py root@192.168.1.101:/data/sdm230device

Stop the service

    svc -d /service/sdm230device

Run on the command line


    /data/sdm230device/main.py -s /dev/ttyUSB0 -r 9600


When done, start the service

    svc -u /service/sdm230device


## Ascii test patterns

The LRC checksum will be applied
Format is https://ozeki.hu/p_5855-modbus-ascii.html

    :AABBCCCCDDDD

: is the start char
AA is the unit
BA is the function
CCCC is the start register
DDDD is the count

LRC checksum is calculated by the reader

read from unit 2 input register from 00 for 18 registers

    :020400000012
    :020400120012
    :02040034000c
    :02040046000c
    :020400c80006
    :020401560004

# Notes

## DBus

A DBus tracker only gets updates every second so switched to getting the values with a blocking call as this takes 0.001s and might eliminate data latency between the value being read from the real SDM230 and the response over serial by this module.

## current setup

        regs = [
            Reg_f32b(0x0000, '/Ac/Voltage',        1, '%.1f V', max_age=0.2),
            Reg_f32b(0x0006, '/Ac/Current',        1, '%.1f A', max_age=0.2),
            Reg_f32b(0x000c, '/Ac/Power',          1, '%.1f W', max_age=0.2),
            Reg_f32b(0x0046, '/Ac/Frequency',      1, '%.1f Hz'),
            Reg_f32b(0x0048, '/Ac/Energy/Forward', 1, '%.1f kWh'),
            Reg_f32b(0x004a, '/Ac/Energy/Reverse', 1, '%.1f kWh'),
        ]


## Analysis of capture log from PV Inverter

'''
{'unit': 2, 'function': 4, 'reg': 342, 'regHex': '0156', 'count': 4} 1.0 0.0006324555320336413
{'unit': 2, 'function': 4, 'reg': 0, 'regHex': '0000', 'count': 18} 0.2000048309178744 0.0005441443317693632
{'unit': 2, 'function': 4, 'reg': 18, 'regHex': '0012', 'count': 18} 1.0 0.0007416198487095257
{'unit': 2, 'function': 4, 'reg': 52, 'regHex': '0034', 'count': 12} 1.0 0.0006708203932499002
{'unit': 2, 'function': 4, 'reg': 70, 'regHex': '0046', 'count': 12} 1.0 0.0005916079783099293
{'unit': 2, 'function': 4, 'reg': 200, 'regHex': '00c8', 'count': 6} 1.0 0.0005547001962251988


DATE=2022-05-17T19:41:27.054;ERR=NO;FRAME=02-04-24-43-74-a9-82-00-00-00-00-00-00-00-00-3f-ae-7a-82-00-00-00-00-00-00-00-00-43-68-be-ed-00-00-00-00-00-00-00-00-63-97;SLAVE=2

0, 18 0.2s
0x0000 18
0x0000  /Ac/L%d/Voltage
0x0002  Phase 2  zeros
0x0004  Phase 3  zeros
0x0006  /Ac/L%d/Current
0x0008  P2 zeros
0x000A  P3 zeros
0x000C  /Ac/L%d/Power (Active)
0x000E  P2 zeros
0x0010  P3 zeros


DATE=2022-05-17T19:41:26.956;ERR=NO;FRAME=02-04-24-43-a6-c0-4c-00-00-00-00-00-00-00-00-c3-6e-db-aa-00-00-00-00-00-00-00-00-3f-32-a8-82-00-00-00-00-00-00-00-00-51-35;SLAVE=2

18 36
0x0012 18
0x0012 /Ac/Power/Apparent W  Apparent Power
0x0014 P2 zeros
0x0016 P3 zeros
0x0018 /Ac/Power/Reactive VAr Reactive power
0x001A P2 zeros
0x001C P3 zeros
0x001E /Ac/Power/Factor
0x0020 P2 zeros
0x0022 P3 zeros

02-04-18-00-00-00-00-00-00-00-00-00-00-00-00-00-00-00-00-00-00-00-00-00-00-00-00-83-4c;SLAVE=2
52 64
0x0034 12
0x0034 Total System power zeros
0x0036 zeros
0x0038 Total System voltszeros
0x003Azeros
0x003C VArzeros
0x003E Total System power factorzeros

DATE=2022-05-17T19:41:30.338;ERR=NO;FRAME=02-04-18-
42-47-9c-32
43-04-2e-98
42-02-db-23
40-ef-8d-50
42-87-8e-56
00-00-00-00
9b-e5;SLAVE=2

70 82  
0x0046 12 
0x0046 /Ac/Frequency
0x0048 /Ac/Energy/Forward  (import)
0x004A /Ac/Energy/Reverse  (export)
0x004C /Ac/ReactiveEnergy/Forward   toadd
0x004E /Ac/ReactiveEnergy/Reactive/Reverse   toadd
0x0050 ??  zero

DATE=2022-05-17T19:41:26.522;ERR=NO;FRAME=02-04-0c-00-00-00-00-00-00-00-00-00-00-00-00-d6-b6;SLAVE=2

200 206
0x00c8 6
0x00c8 L1 to L2 V zero
0x00cA L2 to L3V zero
0x00cc L3 to L1 V zero


DATE=2022-05-17T19:41:26.719;ERR=NO;FRAME=02-04-08-
43-24-e5-1f-
42-96-87-2b-
5f-22;SLAVE=2

Update 30s
342 346
0x0156 4
0x0156 /Ac/Energy/Total Total Active Energy  kWh  toadd
0x0158 /Ac/ReactiveEnergy/Total  Total Reactive Energy kVArh toadd


