#  **************************************************************
#   Projekt         : PiBeacon
#   Modul           :
#  --------------------------------------------------------------
#   Autor(en)       :
#   Beginn-Datum    :
#  --------------------------------------------------------------
#   Beschreibung    :
#  --------------------------------------------------------------
#
#  **************************************************************
#  --------------------------------------------------------------
#   wann                 wer   was
#  --------------------------------------------------------------

class IntMessage():

    # Message Types:
    START_SCAN_BLE = 3
    STOP_SCAN_BLE = 4
    SCANNED_IBEACON = 5
    ALERT_GUI = 6
    BEACON_DATA_ERROR = 7
    RESET_IBEACON = 8
    SIGNAL_IBEACON = 9
    GUI_READY = 10
    SET_AUTOSTART_IBEACON = 11
    SAVE_IBEACON = 12
    PAIRING_ENABLED = 13
    PAIRING_DISABLED = 14
    LED1LightOn = 15
    LED1LightOff = 16
    LED2LightOn = 17
    LED2LightOff = 18
    GETSYSINFO = 188
    STOPGETSYSINFO = 189
    QUITAPP = 1111

    ready = 10000
    use = 10001
    serve = 10002
    clean = 10003
    _type = None
    _payload = None

    def __init__(self, type, payload=None):
        self._type = type
        self._payload = payload

    def addVal(self, key, value):
        # TODO needs implementation
        raise NotImplemented

    def get_type(self):
        return self._type

    def get_payload(self):
        return self._payload
