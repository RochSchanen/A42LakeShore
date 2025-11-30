# file: LAKESHORE.py
# created: 2025 11 28
# author: Roch Schanen
# content: monitor LAKESHORE and temperature control

from sys import exit
from time import time
from time import strftime
from time import localtime
from time import monotonic
from time import sleep
from time import perf_counter
from datetime import datetime
from socket import gethostname
from threading import Thread
from numpy import array

import pyvisa

#####################################################################
#                                                             VERSION

VERSION = "0.00"


#####################################################################
#                                                               DEBUG

_DEBUG = [
    # "ALL",
    # VERBOSE,
    # "NONE",
    "TEMPFILE",
    "LOG_GPIB",
    "NOGPIB",    # GPIB "OPEN", "WRITE", and "QUERY" ineffective
    # "SINGLE",
]

def debug(*flags):
    if "NONE" in _DEBUG: return False
    if "ALL" in _DEBUG: return True
    for f in flags:
        if f.upper() in _DEBUG: return True
    if flags: return False
    return True

#####################################################################
#                                                                FILE

def checkpath(fp):
    if not fp[-1] == '/': fp += '/'
    if not exists(fp): exit(f"path '{fp}' not found.")
    if debug(): print(f"path '{fp}' checked.")
    # done
    return True


#####################################################################
#                                                                HOST

if debug(): print(f"identified hostname '{gethostname()}'")


#####################################################################
#                                                              CONFIG

configuration = {

    'PYA042000001': {
        'DEVICENAME'        : "GPIB2::24::INSTR",   # LAKESHORE
        'LAKESHORE_Heater_Resistance': 194.0,       # HEATER RESISTANCE [OHM]
        "FILEPATH"          : "./",                 # DATA FOLDER
        "LOCALFILEPATH"     : '.',                  # LOCAL FOLDER
        "SAVINGINTERVALS"   : 10.0,                 # SAVE EVERY 5s
        "TEMPFILEPATH"      : '.',                  # DEBUG
        "TEMPFILENAME"      : 'd.dat',              # DEBUG
    },

    'TOSH135': {
        'DEVICENAME'        : "GPIB2::24::INSTR",   # LAKESHORE
        'LAKESHORE_Heater_Resistance': 194.0,       # HEATER RESISTANCE [OHM]
        "FILEPATH"          : "./",                 # DATA FOLDER
        "LOCALFILEPATH"     : '.',                  # LOCAL FOLDER
        "SAVINGINTERVALS"   : 10.0,                 # SAVE EVERY 5s
        "TEMPFILEPATH"      : '.',                  # DEBUG
        "TEMPFILENAME"      : 'd.dat',              # DEBUG
    },

}[gethostname().upper()]


#####################################################################
#                                                               SETUP

setup = {
    "MESUREMENTINTERVAL": 2,  # MEASURE DATA EVERY 1s
}

dn = configuration["DEVICENAME"]
lfp = configuration["FILEPATH"]
tfp = configuration["TEMPFILEPATH"]

#####################################################################
#                                                               FILES

class monitor_file():

    def __init__(self, fp, fn):
        # record time stamp
        self.created = strftime(r'%Y%m%dT%H%M%S', localtime())
        #  new file path (time stamped)
        fp = fp.rstrip('/')
        self.fp = f"{fp}/{fn}{self.created}.dat"
        # force fixed temporary file name for debugging
        if debug("TEMPFILE"):
            fp = configuration['TEMPFILEPATH']
            fn = configuration['TEMPFILENAME']
            self.fp = f"{fp}/{fn}"
            # clear file
            fh = open(self.fp, "w")
            fh.close()
        # declare header text and data list
        self.headertext, self.data = "", []
        # setup timer
        self.time = monotonic() + configuration['SAVINGINTERVALS']
        # done
        return

    def flushheader(self, fh):
        fh.write(self.headertext)
        self.headertext = None
        return

    def writeheaderblock(self, b):
        for i, l in enumerate(b.split(f"\n")[1:-1]):
            if i == 0: n = len(l) - len(l.lstrip())
            self.headertext += f"# {l[n:]}\n"
        return

    def savedata(self):
        if not self.data: return
        if monotonic() < self.time: return
        fh = open(self.fp, "a")
        if self.headertext: self.flushheader(fh)
        for d in self.data: fh.write(f"{d}\n")
        fh.close()
        self.data = []
        # reset timer
        self.time = monotonic() + configuration['SAVINGINTERVALS']
        # done
        return

    def writedata(self, datastr):
        # append line of data
        self.data.append(datastr)
        # try saving available data
        self.savedata()
        # done
        return

    def flushdata(self):
        self.time = monotonic()
        self.savedata()
        # done
        return

#####################################################################
#                                                           LAKESHORE

class LAKESHORE():

    def __init__(self):

        # get resource manager instance
        rm = pyvisa.ResourceManager()
        if debug("LOG_GPIB"): print(rm)

        # get list of all visa resources
        rs = rm.list_resources()
        if debug("LOG_GPIB"): print(rs)

        lsn = configuration["DEVICENAME"]

        if not lsn in rs:
            print(f"failed to find instrument at LakeShore address {lsn}.")
            exit()

        # record configuration
        self.rm = rm
        self.lsn = lsn
        self.hr = configuration["LAKESHORE_Heater_Resistance"]

        # done
        return

    def Open(self):
        # get GPIB handle from the LakeShore visa id
        if debug("LOG_GPIB"): print(f"open_resource('{self.lsn}')")
        if debug("NOGPIB"):
            print("skipped...")
            return
        self.lsh = self.rm.open_resource(self.lsn)
        # done
        return

    def Close(self):
        # done
        return

    def Configure(self):
        # done
        return

    def Start(self):
        return

    def Stop(self):
        return

    def write(self, w):
        if debug("LOG_GPIB"): print(f"{self.lsn} write '{w}'")
        if debug("NOGPIB"):
            print("skipped...")
            return
        self.lsh.write(w)
        return

    def query(self, w):
        if debug("LOG_GPIB"): print(f"{self.lsn} query '{w}'")
        if debug("NOGPIB"):
            print("skipped... return '1'")
            return "1"
        return self.lsh.query(w)

    def read(self):
        T1R = float(self.query(f"RDGR? 1")) # THERMOMETER 1 RESISTANCE
        T1T = float(self.query(f"RDGK? 1")) # THERMOMETER 1 TEMPERATURE
        TSP = float(self.query(f"SETP?")) # TEMPERATURE SET POINT
        HTR = int(self.query(f"HTRRNG?")) # HEATER RANGE
        HTV = float(self.query(f"HTR?"))  # HEATER VALUE
        # if debug("NOGPIB"): # return bogus data
        #     return (1.0, 1.0, 1.0, 1, 1.0)
        return (T1R, T1T, TSP, HTR, HTV)

#####################################################################
#                                                              SINGLE

if debug("single"):

    L = LAKESHORE()
    L.Open()
    L.Configure()
    L.Start()

    # measure delays
    time_start = perf_counter()

    data = None
    # data = L.query(f"*ISDN?")
    # data = L.query(f"RDGR? 1") # thermometer resistance
    # data = L.query(f"RDGK? 1") # thermometer temperature
    # L.write("HTRRNG 0") # heater off
    # L.write("HTRRNG 1") # smallest range
    # data = L.query(f"HTRRNG?")
    # data = L.write(f"SETP 40.0E-3")
    # data = L.query(f"SETP?")
    # HTR? # heater output
    """
    Resistor = 194 ohms
    0 = Off, 
    1 = 31.6 μA
    2 = 100 μA
    3 = 316 μA
    4 = 1.00 mA
    5 = 3.16 mA
    6 = 10.0 mA
    7 = 31.6 mA
    8 = 100 mA
    """

    T1R = float(L.query(f"RDGR? 1")) # THERMOMETER 1 RESISTANCE [Ohm]
    T1T = float(L.query(f"RDGK? 1")) # THERMOMETER 1 TEMPERATURE [K]
    TSP = float(L.query(f"SETP?")) # TEMPERATURE SET POINT [K]
    HTR = int(L.query(f"HTRRNG?")) # HEATER RANGE [index]
    HTV = float(L.query(f"HTR?"))  # HEATER VALUE [W]
    data = (T1R, T1T, TSP, HTR, HTV)

    Range_Amps = array([

          0.0,      # 0 OFF 
        
         31.60E-6,  # 1 microamp
        100.00E-6,  # 2
        316.00E-6,  # 3

          1.00E-3,  # 4 milliamp
          3.16E-3,  # 5
         10.00E-3,  # 6
         31.60E-3,  # 7
        100.00E-3,  # 8
    ])

    Power_Range = Range_Amps*Range_Amps*L.hr
    print(Power_Range[HTR])

    # measure delays and display
    time_delay = perf_counter() - time_start
    print(data, f": measured in {time_delay*1000:.3f}ms")

    # clean up
    L.Stop()
    L.Close()

    exit()

# #####################################################################
#                                                                  LOOP

def RunningThread():

    if debug("SHOWDATA"): i = 0  # init var

    while Running:

        if debug("SHOWDATA"): print(f"count #{i:02} ")

        # -------------------- MEASUREMENTS INTERVAL --------------------

        sleep(setup['MESUREMENTINTERVAL'])

        # -------------------- RETRIEVE MEASUREMENTS --------------------

        # get time stamp
        ts = datetime.now().strftime('%H:%M:%S.%f')

        # get LakeShore readings and configuration

        (T1R, T1T, TSP, HTR, HTV) = LS.read()

        if debug("SHOWDATA"): print(data)

        # -------------------- ANALYSE -------------------
        s = time()
        # compute pressure values, flow rate, ...

        # -------------------- RECORD --------------------

        # record data
        w = f"{ts[:-5]}\t"
        w += f"{s:12.1f}\t"
        w += f"{T1R:8.3e}\t"
        w += f"{T1T:8.3e}\t"
        w += f"{TSP:8.3e}\t"
        w += f"{HTR}\t"
        w += f"{HTV:8.3e}\t"

        if debug("SHOWDATA"):
            print(w)
            i += 1

        fh.writedata(w)

        # -------------------- RECALL NEXT DATA POINT -----


    # finalise thread
    fh.flushdata()
    # done (thread ends here)
    return


# INSTANCIATE DEVICES

LS = LAKESHORE()

# SETUP FILES

fh = monitor_file(configuration['FILEPATH'], "LS370_")
fh.writeheaderblock(f"""
file    : {fh.fp.split('/')[-1]}
content : "LakeShore370" raw data
created : {fh.created}
author  : Roch Schanen LakeShore.py V{VERSION}
Heater Resistance : {LS.hr} [Ohms]
column 01 : time stamp [HH:MM:SS.F]
column 02 : time in seconds [s]
column 03 : Thermometer 1 Resistance [Ohms]
column 04 : Thermometer 1 Temperature [K] 
column 05 : Temperature Set-point [K]
column 06 : Heater Range [index] 
column 07 : Heater Value [W]
""")

# SETUP DEVICES

LS.Open()
LS.Configure()
LS.Start()

# SETUP LOOP (THREAD)

LOOP = Thread(target=RunningThread)
Running = True
LOOP.start()

# run until user press enter
print("--- PRESS ENTER TO QUIT ---")
i = input()
print("--- INTERRUPTING ---")
Running = False

# FINALISING

LOOP.join()
LS.Stop()
LS.Close()
fh.flushdata()
exit()
