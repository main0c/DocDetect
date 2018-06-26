#  **************************************************************
#   Projekt         : PiBeacon
#   Modul           : beacon
#  --------------------------------------------------------------
#   Beginn-Datum    : 18.07.16
#  --------------------------------------------------------------
#   Beschreibung    : Wrapper for hcitool
#  --------------------------------------------------------------
#
#  **************************************************************
#  --------------------------------------------------------------
#   wann                 wer   was
#  --------------------------------------------------------------
import subprocess

class HCI():

    CMD_TOOL = "hcitool"
    CMD_CONFIG = "hciconfig"
    BLE_DEV = None

    def __init__(self, ble_dev="hci0"):
        self.BLE_DEV = ble_dev

    def start_adv(self, adv_data, interval):
        subprocess.call([self.CMD_CONFIG, self.BLE_DEV, 'up'], stdout=subprocess.DEVNULL)
        #subprocess.call([self.CMD_CONFIG, self.BLE_DEV, 'leadv', '3'])
        #subprocess.call([self.CMD_CONFIG, self.BLE_DEV, 'noscan'])

        self.set_adv_data(adv_data)
        # 0x0006 is used to set LE Advertising Parameters (BT Spec v4.2 - Sec. 7.8.5 - Page 968)
        data_interval = [self.CMD_TOOL, '-i', self.BLE_DEV, 'cmd', '0x08', '0x0006']
        data_interval.extend(HCI.calc_interval(interval))  # minimum interval
        data_interval.extend(HCI.calc_interval(interval))  # maximum interval
        # 03 - non connectable advertising
        data_interval.extend(['03', '00', '00', '00', '00', '00', '00', '00', '00', '07', '00'])
        subprocess.call(data_interval, stdout=subprocess.DEVNULL)
        subprocess.call([self.CMD_TOOL, '-i', self.BLE_DEV, 'cmd', '0x08', '0x000a', '01'], stdout=subprocess.DEVNULL)

    def set_adv_data(self, adv_data):
        # 0x0008 is used to LE Set Advertising Data Command (BT Spec v4.2 - Sec. 7.8.7 - Page 973)
        adv = [self.CMD_TOOL, '-i', 'hci0', 'cmd', '0x08', '0x0008']
        adv.extend(adv_data)
        subprocess.call(adv, stdout=subprocess.DEVNULL)

    def stop_adv(self):
        subprocess.call([self.CMD_CONFIG, self.BLE_DEV, 'down'])

    def power_hci_dev(self):
        subprocess.call([HCI.CMD_CONFIG, self.BLE_DEV, 'up'])

    def one_time_adv(self, adv):
        # 0x0008 is used to LE Set Advertising Data Command (BT Spec v4.2 - Sec. 7.8.7 - Page 973)
        adv_data = [HCI.CMD_TOOL, '-i', self.BLE_DEV, 'cmd', '0x08', '0x0008']
        adv_data.extend(adv)
        # 0x000A is used to LE Set Advertise Enable Command (BT Spec v4.2 - Sec. 7.8.9 - Page 975)
        subprocess.call([HCI.CMD_TOOL, '-i', self.BLE_DEV, 'cmd', '0x08', '0x000a', '01'], stdout=subprocess.DEVNULL)
        subprocess.call(adv_data, stdout=subprocess.DEVNULL)
        subprocess.call([HCI.CMD_TOOL, '-i', self.BLE_DEV, 'cmd', '0x08', '0x000a', '00'], stdout=subprocess.DEVNULL)

    @staticmethod
    def parse_uuid(userin):
        str_in = userin
        str_in = str_in.replace('-', '')
        str_in = str_in.upper()

        uuid = []
        for x in range(0, 16):
            uuid.append(str_in[0:2])
            str_in = str_in[2:]
        return uuid

    @staticmethod
    def to_hex_array(data):
        if len(data) % 2 != 0:
            raise Exception("Length of hex data has to be even")

        str_in = data
        str_in = str_in.replace('-', '')
        str_in = str_in.upper()

        hex_array = []
        while(str_in is not ''):
            hex_array.append(str_in[0:2])
            str_in = str_in[2:]

        return hex_array

    @staticmethod
    def calc_interval(interval):
        interval = int(interval)
        interval = int(interval/0.625)
        interval = HCI.to_hex_array(format(int.from_bytes(interval.to_bytes(2, byteorder='little'), byteorder='big'), '04x'))
        return interval
