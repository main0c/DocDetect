#  **************************************************************
#   Projekt         : PiBeacon
#   Modul           : beacon
#  --------------------------------------------------------------
#   Beginn-Datum    : 18.07.16
#  --------------------------------------------------------------
#   Beschreibung    : Object representation of an iBeacon
#  --------------------------------------------------------------
#
#  **************************************************************
#  --------------------------------------------------------------
#   wann                 wer   was
#  --------------------------------------------------------------
from beacon.hci import HCI

class IBeacon():

    _uuid = None
    _major = None
    _minor = None
    _tx = None
    _interval = None

    _hci = None

    _ibeacon_prefix = "1e02011a1aff4c000215"

    def __init__(self, uuid, major, minor, tx, interval, hci):
        self._uuid = uuid
        self._major = int(major)
        self._minor = int(minor)
        self._tx = int(tx)
        self._interval = interval

        self._hci = hci

    def start(self):
        data = self.build_adv_data()
        self._hci.start_adv(data, self._interval)
        return data

    def stop(self):
        self._hci.stop_adv()

    # build advertisement data
    def build_adv_data(self):
        adv = []
        adv.extend(HCI.to_hex_array(IBeacon._ibeacon_prefix)) # iBeacon prefix
        adv.extend(HCI.parse_uuid(self._uuid))  # add UUID to data-string
        # 4 digit hex with leading zeros
        adv.extend(HCI.to_hex_array(format(self._major, '04x')))  # adding major to data-string
        adv.extend(HCI.to_hex_array(format(self._minor, '04x')))  # adding minor to data-string
        adv.append(format(self._tx & 0xFF, 'x'))  # convert TX to signed hex value
        adv.append('00')  # close data-string with zero byte
        return adv

    # check user input for errors
    @staticmethod
    def check_input(uuid, major, minor, tx):
        error = False
        # check correctness of uuid
        try:
            # convert Namespace ID to HEX to check for non HEX chars
            # remove hyphens from UUID
            int(uuid.replace('-', ''), 16)
        except ValueError:
            error = "UUID contains non HEX chars"

        if len(uuid) != 36:  # check length of UUID
            error = "UUID has not the correct length"

        # check if major & minor are valid
        if not 0 <= int(major) <= 65535 or not 0 <= int(minor) <= 65535:
            error = "Major or Minor not between 0 and 65535"

        # check if TX is valid
        if int(tx) > 0 or int(tx) < -127:
            error = "TX value is bigger than 0 oder smaller than -127"

        return error


