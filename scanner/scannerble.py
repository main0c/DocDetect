#  **************************************************************
#   Projekt         : PiBeacon
#   Modul           : Scanner
#  --------------------------------------------------------------
#   Autor(en)       : Daniel Haß
#   Beginn-Datum    : 01.08.2016
#  --------------------------------------------------------------
#   Beschreibung    : Scan for nearby Beacons
#  --------------------------------------------------------------
#
#   Reference:
#   https://github.com/google/eddystone/blob/master/eddystone-url/implementations/linux/scan-for-urls
#
#  **************************************************************
#   Änderungs-Protokoll:
#  --------------------------------------------------------------
#   wann                 wer   was
#  --------------------------------------------------------------
import subprocess
import threading
import time  # 引入time模块

from comm.intmessage import IntMessage
from utils.debug import DBG

class ScanParser(threading.Thread):

    _running = True
    _dump = None
    _comm = None

    def __init__(self, dump, comm):
        threading.Thread.__init__(self)
        self._dump = dump
        self._comm = comm

    def run(self):
        self.parse()

    def test_for_beacon(self, payload):
        data = bytearray.fromhex(payload)

        # EddystoneBeacon
        if len(data) >= 20 and data[19] == 0xaa and data[20] == 0xfe:  # check if an Eddystone was scanned
            serviceDataLength = data[21]
            frameType = data[25]

            if frameType == 0x10:
                DBG("Eddystone-URL")  # scanned an Eddystone-URL frame, no further handling here
            elif frameType == 0x00:
                DBG("Eddystone-UID")
                # read TX value an convert to signed integer
                DBG("TX: {}".format(int.from_bytes(data[26], byteorder='big', signed=True)))
                # read Namespace and Instance ID as HEX values
                DBG("Namespace: {}".format(payload[(27*3):(37*3)]))
                DBG("Instance: {}".format(payload[(37*3):(43*3)]))
                # send scanned data to controller
                msg = IntMessage(IntMessage.SCANNED_EDDYSTONEUID,
                                 {'NID': payload[(27*3):(37*3)],
                                  'IID': payload[(37*3):(43*3)],
                                  'TX': data[26]-256})
                self._comm(msg)
            elif frameType == 0x20:
                DBG("Eddystone-TLM")  # scanned an Eddystone-TLM frame, no further handling here
            else:
                DBG("Unknown Eddystone frame type: {}".format(frameType))

        # iBeacon
        elif len(data) >= 20 and data[17] == 0x1a and data[18] == 0xff:  # check if an iBeacon was scanned
            # DBG("iBeacon")
            # read UUID as HEX from scanned data
            # DBG("UUID: {}".format(payload[(23 * 3):(39 * 3)]))
            # read Major and Minor and convert to a unsigned integer
            # DBG("Major: {}".format(int.from_bytes(data[39:41], byteorder='big', signed=False)))
            # DBG("Minor: {}".format(int.from_bytes(data[41:43], byteorder='big', signed=False)))
            # read TX value an convert to signed integer
            # DBG("TX: {}".format(int.from_bytes(data[43:44], byteorder='big', signed=True)))
            # send scanned data to controller
            msg = IntMessage(IntMessage.SCANNED_IBEACON,
                             {'UUID': payload[(23 * 3):(39 * 3)],
                              'MAJOR': int.from_bytes(data[39:41], byteorder='big', signed=False),
                              'MINOR': int.from_bytes(data[41:43], byteorder='big', signed=False),
                              'TX': int.from_bytes(data[43:44], byteorder='big', signed=True),
                              'RSSI': int.from_bytes(data[44:45], byteorder='big', signed=True),'time': time.time()
                              })
            self._comm(msg)

        # AltBeacon
        elif len(data) >= 20 and data[17] == 0x1b and data[18] == 0xff:  # check if an AltBeacon was scanned
            DBG("Altbeacon")
            # read BeaconID as HEX from scanned data
            DBG("Beacon ID: {}".format(payload[(23 * 3):(43 * 3)]))
            # read RSSI value an convert to signed integer
            DBG("RSSI: {}".format(int.from_bytes(data[43:44], byteorder='big', signed=True)))
            # read MFG as HEX from scanned data
            DBG("MFG RSV: {}".format(payload[(44 * 3):(45 * 3)]))
            # send scanned data to controller
            msg = IntMessage(IntMessage.SCANNED_ALTBEACON,
                             {'BID': payload[(23 * 3):(43 * 3)],
                              'RSSI': int.from_bytes(data[43:44], byteorder='big', signed=True),
                              'MFG': payload[(44 * 3):(45 * 3)]})
            self._comm(msg)

        # Unknown BLE advertisement
        else:
            # DBG("Unknown BLE Adv")
            pass

    # main worker function of scanner
    def parse(self):
        # DBG("Thread started..")
        packet = None
        while self._running:  # is scanner still activated?
            for line in self._dump:  # read data from HCI-dump
                line = line.decode()
                # parsing of HCI-dump output
                if line.startswith("> "):
                    if packet: self.test_for_beacon(packet)
                    packet = line[2:].strip()
                elif line.startswith("< "):
                    if packet: self.test_for_beacon(packet)
                    packet = None
                else:
                    if packet: packet += " " + line.strip()


    def stop_parsing(self):
        self._running = False

class ScannerBLE():

    _commcallback = None
    _blescan = subprocess.Popen('ls', None)
    _dump = subprocess.Popen('ls', None)
    _scannerth = ScanParser(None, None)
    _hci = None

    def __init__(self, commcallback, hci_dev):
        self._commcallback = commcallback
        self._hci = hci_dev

    def scan(self):
        subprocess.call(["hciconfig", self._hci, 'reset'])  # clear previous HCI settings
        # tell HCI to start scanning and disable duplicate detection
        self._blescan = subprocess.Popen(["hcitool", "lescan", "--duplicates"], stdout=subprocess.DEVNULL)
        # dump scanned data to analyse PIPE
        self._dump = subprocess.Popen(["hcidump", "--raw"], stdout=subprocess.PIPE)
        self._scannerth = ScanParser(self._dump.stdout, self._commcallback)
        self._scannerth.start()  # start scanner worker thread

    def stop_scan(self):
        self._scannerth.stop_parsing()
        self._blescan.kill()
        self._dump.kill()
