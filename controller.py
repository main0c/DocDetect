#!/usr/bin/python3

from GPIODetect import GPIODetect

from scanner.scannerble import ScannerBLE
from comm.intmessage import IntMessage
from utils.debug import DBG
from gui.gui import Gui
from repeat import RepeatTimer
import json
#import numpy as np
from getSysInfo import GetSysInfo


from PyQt4.QtCore import *
from PyQt4.QtGui import *

import datetime
import queue
import time

g_data_queue = queue.Queue(2048)

class UI_Thread(QThread):
    #定义信号,定义参数为str类型
    _signal=pyqtSignal(str)
    def __init__(self):
        super(UI_Thread,self).__init__()
    def run(self):
        # DBG("run!")
        while True:
            if g_data_queue.empty():
                time.sleep(1)
                # DBG("test")
            else:
                data = g_data_queue.get()
                # DBG(data)
                self._signal.emit(data)

class Controller():

    _scannerble = None
    _gui = None
    conn = None
    array_full = []
    # 创建线程
    _thread = UI_Thread()
    _sysInfo = GetSysInfo()
    _detect = None
    def __init__(self):
        self._detect = GPIODetect(self.gpioDetect)
        self._detect.setup()
        self._detect.detct()
        self._sysInfo.setcommCallback(self.getSystem)
        # DBG("Welcome to Controller!")
        self._scannerble = ScannerBLE(self.scanner_comm, "hci0")

        self._gui = Gui(self.gui_comm)
        # 注册信号处理函数
        self._thread._signal.connect(self.updateUI)
        self._thread.start()
        self._gui.start_gui()

    def beacon_comm(self, msg):
        # DBG("Welcome to beacon_comm!")
        if msg.get_type() is IntMessage.BEACON_DATA_ERROR:  # pass input error back to GUI
            self._gui.comm(IntMessage(IntMessage.ALERT_GUI, {'ALERT_TEXT': "Your input is not correct!",
                                                             'ALERT_DETAIL': msg.get_payload()['ERROR']}))
        elif msg.get_type() is IntMessage.SIGNAL_IBEACON :
            signal_hex = msg.get_payload()['DATA']
            DBG("Current Signal: " + str(signal_hex))
            self._gui.comm(IntMessage(msg.get_type(), {'TEXT': signal_hex}))

    def gui_comm(self, msg):
        if not isinstance(msg, IntMessage):
            raise Exception("Message has to be an IntMessage")
        msg_type = msg.get_type()
        pl = msg.get_payload()

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

    def scanner_comm(self, msg):
        dic = {'type': int(msg.get_type()), 'pyload': str(msg.get_payload())}
        input = json.dumps(dic)
        g_data_queue.put(input)

    def updateUI(self, msg):
        dict = json.loads(msg)
        self._gui.comm(IntMessage(dict['type'],  eval(dict['pyload'])))

    def gpioDetect(self, msg):
        # print('xxxxxxxx'+str(time.time()))
        dic = {'type': msg, 'pyload': '{}'}
       # msg1 = IntMessage(IntMessage.SCANNED_IBEACON,
       #                   {'UUID': '111', 'MAJOR': '333', 'MINOR': '444', 'TX': '5555', 'RSSI': '6666','time': time.time()})
       # dic = {'type': int(msg1.get_type()), 'pyload': str(msg1.get_payload())}
        input = json.dumps(dic)
        g_data_queue.put(input)
    def getSystem(self, msg):
        DBG('getSystem')
        dic = {'type': int(msg.get_type()), 'pyload': str(msg.get_payload())}
        input = json.dumps(dic)
        g_data_queue.put(input)

def main() :
    # DBG("Welcome to PiBeacon!")

    controller = Controller()


if __name__ == '__main__':
    main()
