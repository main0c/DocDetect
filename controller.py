#!/usr/bin/python3

from GPIODetect import GPIODetect

from scanner.scannerble import ScannerBLE
from comm.intmessage import IntMessage
from utils.debug import DBG
from gui.gui import Gui
import json
from getSysInfo import GetSysInfo


from PyQt4.QtCore import *

import queue
import time

g_data_queue = queue.Queue(2048)


class UIThread(QThread):
    # 定义信号,定义参数为str类型
    signal = pyqtSignal(str, name='UIThread')

    def __init__(self):
        super(UIThread, self).__init__()

    def run(self):
        # DBG("run!")
        while True:
            if g_data_queue.empty():
                time.sleep(1)
                # DBG("test")
            else:
                data = g_data_queue.get()
                # DBG(data)
                self.signal.emit(data)


class Controller:

    _scannerble = None
    _gui = None
    conn = None
    array_full = []
    # 创建线程
    _thread = UIThread()
    _sysInfo = GetSysInfo()
    _detect = None

    def __init__(self):
        self._detect = GPIODetect(self.gpio_detect)
        self._detect.setup()
        self._detect.detct()
        self._sysInfo.setcommCallback(self.get_system_info)
        # DBG("Welcome to Controller!")
        self._scannerble = ScannerBLE(self.scanner_comm, "hci0")

        self._gui = Gui(self.gui_comm)
        # 注册信号处理函数
        self._thread.signal.connect(self.update_ui)
        self._thread.start()
        self._gui.start_gui()

    def beacon_comm(self, msg):
        # DBG("Welcome to beacon_comm!")
        if msg.get_type() is IntMessage.BEACON_DATA_ERROR:  # pass input error back to GUI
            self._gui.comm(IntMessage(IntMessage.ALERT_GUI, {'ALERT_TEXT': "Your input is not correct!",
                                                             'ALERT_DETAIL': msg.get_payload()['ERROR']}))

    def gui_comm(self, msg):
        if not isinstance(msg, IntMessage):
            raise Exception("Message has to be an IntMessage")
        msg_type = msg.get_type()
        # start different beacon standards
        if msg_type is IntMessage.START_SCAN_BLE:
            self._scannerble.scan()
        elif msg_type is IntMessage.STOP_SCAN_BLE:
            DBG('Stopped BLE Scan')
            self._scannerble.stop_scan()
        elif msg_type is IntMessage.GETSYSINFO:
            self._sysInfo.detct()
        elif msg_type is IntMessage.STOPGETSYSINFO:
            self._sysInfo.cleanup()
        elif msg_type is IntMessage.QUITAPP:
            self._sysInfo.cleanup()
            self._scannerble.stop_scan()
            self._detect.cleanup()

    @staticmethod
    def scanner_comm(msg):
        dic = {'type': int(msg.get_type()), 'pyload': str(msg.get_payload())}
        g_data_queue.put(json.dumps(dic))

    def update_ui(self, msg):
        dic = json.loads(msg)
        self._gui.comm(IntMessage(dic['type'],  eval(dic['pyload'])))

    @staticmethod
    def gpio_detect(msg):
        dic = {'type': msg, 'pyload': '{}'}
        # msg1 = IntMessage(IntMessage.SCANNED_IBEACON,
        #                   {'UUID': '111', 'MAJOR': '333', 'MINOR': '444', 'TX': '5555', 'RSSI': '6666',
        #                    'time': time.time()})
        # dic = {'type': int(msg1.get_type()), 'pyload': str(msg1.get_payload())}
        g_data_queue.put(json.dumps(dic))

    @staticmethod
    def get_system_info(msg):
        DBG('get_system_info')
        dic = {'type': int(msg.get_type()), 'pyload': str(msg.get_payload())}
        g_data_queue.put(json.dumps(dic))

    @staticmethod
    def dummy_fun(msg):
        DBG(msg)


def main():
    # DBG("Welcome to PiBeacon!")

    controller = Controller()
    controller.dummy_fun('controller start')


if __name__ == '__main__':
    main()
