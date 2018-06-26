#  **************************************************************
#   Projekt         : PiBeacon
#   Modul           : gui.gui
#  --------------------------------------------------------------
#   Autor(en)       : Henrik Schaffhauser
#   Beginn-Datum    : 22.07.2016
#  --------------------------------------------------------------
#   Beschreibung    : GUI functions
#  --------------------------------------------------------------
#
#  **************************************************************
#  --------------------------------------------------------------
#   wann                 wer   was
#   10.05.2017           TS    Adding Checkbox for Pairing
#  --------------------------------------------------------------
import sys
import math
import time  # 引入time模块
import enum
import queue
import json

import threading
import time
from multiprocessing import Process


from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from comm.intmessage import IntMessage
from gui.BeaconUI import Ui_PiBeacon
from DetectManager import DetectManager
from DetectManager import IntMessage
from DetectManager import ThreadCheckStatus
from getSysInfo import GetSysInfo
import RPi.GPIO as GPIO
from repeat import RepeatTimer
from comm.intmessage import IntMessage
from utils.debug import DBG
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8


    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

        # ready=0\in use=1\service=2\clean=3\

g_check_queue = queue.Queue(2048)


class Checking_Thread(QThread):
    #定义信号,定义参数为str类型
    _signal=pyqtSignal(str)
    _check_time = 0
    def __init__(self,data,id,lock):
        super(Checking_Thread,self).__init__()
        self.id = id
        self.data = data
        self.lock = lock

    # ts之内有beacon并获得最近一个beacon 返回{'udid':str(pl)}
    def checkNearestBeacon(self, bdic, ts):
        bas = []
        for key in bdic:
            arr = bdic[key]
            avg = 0
            ct = 0
            for index, pl in enumerate(arr):
                if time.time() - pl["time"] < 10:
                    avg = avg + self.calculateDistance(pl['TX'], pl['RSSI'])
                    ct = ct + 1
            if ct > 0:
                avg = avg / ct
            # 把距离小于10m的提取出来
            if avg < 10:
                bas.append([key, str(avg)])
        rtdic = {}
        if len(bas)>0:
            findat = bas[0]
            for index, at in enumerate(bas):
                if index > 0:
                    if int(findat[1]) < int(at[1]):
                        findat = at
            rtdic = {'type': int(IntMessage.serve), 'pyload': str(findat[0])}
        else:
            rtdic = {'type': int(IntMessage.use), 'pyload': ''}
        return rtdic
    def checkUseOrServe(self):
        # READY状态下判断S2亮 use or Serve:
        # 前10s判断s1有010状态变更
        DBG('checkUseOrServe')
        if self.data.check010(self.data._s1Array, 10) == True:
            DBG('checkUseOrServe 1')
            # 查找3s内beaconArray有没有在附近
            time.sleep(3)
            DBG('checkUseOrServe 2')
            if len(self.data._beaconsArray) == 0:
                DBG('checkUseOrServe 3')
                # 设置use状态
                dic = {'type': int(IntMessage.use), 'pyload': ''}
                input = json.dumps(dic)
                self._signal.emit(input)
            else:
                DBG('checkUseOrServe 4')
                # 设置serve状态，并且获取最近的beacon
                input = json.dumps(self.checkNearestBeacon(self.data._bstatusDic, 5))
                self._signal.emit(input)
    def UseCheckServeOrClean(self):
        # USE状态下判断serve or clean:
        # S1亮灯后判断3s后S2有010状态变更Y—再判断附近有没有beacon Y:SERVE N:USE
        time.sleep(3)
        input = json.dumps(self.checkNearestBeacon(self.data._bstatusDic, 5))
        self._signal.emit(input)
        # S2亮灯后判断3s后S2有没有010，有再判断2s后S1有没有010，Y:再判断附近有没有beacon SERVE N再判断S2有没有010Y:USE N:CLEAN
        time.sleep(10)
    def ServeCheckUse(self):
        time.sleep(10)
        # SERVE状态下判断serve or clean:
        # S2亮前10s判断s1有010状态变更
        time.sleep(3)
        input = json.dumps(self.checkNearestBeacon(self.data._bstatusDic, 5))
        self._signal.emit(input)
        # USE：S1-1情况下判断未来3s有没有S2-010再判断S1后来有没有010如果有设置clean
        #       然后搜索附近beacon，如果有beacon找最近beacon设置serve
    def checkUseOrClean(self):
        # USE状态下判断serve or clean:前10s判断s1有010状态变更
        time.sleep(10)
        # READY状态下判断S2亮 use or Serve:
        # 前10s判断s1有010状态变更
        if self.data.check010(self.data_s1Array, 10) == True:
            # 查找3s内beaconArray有没有在附近
            time.sleep(3)
            if len(self.data._beaconsArray) == 0:
                # 设置use状态
                dic = {'type': int(IntMessage.use), 'pyload': ''}
                input = json.dumps(dic)
                self._signal.emit(input)
            else:
                # 设置serve状态，并且获取最近的beacon
                input = json.dumps(self.checkNearestBeacon(self.data._bstatusDic, 5))
                self._signal.emit(input)
    def run(self):
        # DBG("run!")
        while True:
            if g_check_queue.empty():
                time.sleep(1)
                # DBG("Checking_Thread")
                self.lock.acquire()

                if self.data.getChecking() == True:
                    if self.data.ckStatu == ThreadCheckStatus.checking_use_or_serve:
                        self.checkUseOrServe()
                    elif self.data.ckStatu == ThreadCheckStatus.checking_serve_or_clean:
                        # 判断当前是否离开，离开的话beacon arr=0
                        self.checkServeOrClean()
                    elif self.data.ckStatu == ThreadCheckStatus.checking_use_or_clean:
                        self.checkUserOrClean()
                    else:
                        DBG("getChecking == TRUE 5")
                self.data.resetChecking()
                self.lock.release()
            else:
                data = g_check_queue.get()
                # DBG(data)
                self._signal.emit(data)

class Gui():

    _commCallback = None
    _app = None
    _ui = None
    _mainwindow = None
    _thread = None

    def __init__(self, commCallback):
        self._commCallback = commCallback

        # ready=0\in use=1\service=2\clean=3\
        data = DetectManager()
        lock = threading.Lock()
        self.data = data
        _thread = Checking_Thread(data, 'thread', lock)
        _thread._signal.connect(self.checkStack)
        _thread._check_time = 0
        _thread.start()
        self._thread = _thread


    def checkStack(self,msg):
        dict = json.loads(msg)
        # self._gui.comm(IntMessage(dict['type'],  eval(dict['pyload'])))
        self.setRoomStatu(dict['type'],eval(dict['pyload']))

    def setHistoryBeaconBehavior(self, pl):
        find = False
        strudid = ''+str(pl['UUID']) + str(pl['MINOR']) + str(pl['MAJOR'])
        for key in self.data._bstatusDic:
            if (strudid == key):
                find = True
                arr = self.data._bstatusDic[strudid]
                arr.append(pl)
                self.data._bstatusDic[strudid] = arr
                break
        if (find == False):
            self.data._bstatusDic[strudid] = [pl]
        # DBG("setHistoryBeaconBehavior:")
        # DBG(self.data._bstatusDic)


    def beaconComming(self):
        # 10s内beacon一直在数组中
        if len(self.data._beaconsArray) == 0:
            return False
        ct = 0

        for key in self.data._bstatusDic:
            arr = self.data._bstatusDic[key]
            avg = 0
            for index, pl in enumerate(arr):
                if time.time() - pl["time"] < 10:
                    avg = avg + self.calculateDistance(pl['TX'], pl['RSSI'])
                    ct = ct + 1
        if ct > 0:
            avg = avg/ct
        print(str(avg) + 'avg======')
        return avg < 10
    def isHasBeacons(self):
        #10s内beacon一直在数组中
        if len(self.data._beaconsArray) == 0:
            return False
        ct = 0
        for index, pl in enumerate(self.data._beaconsArray):
            if time.time()- pl["time"] < 10:
                ct = ct + 1
        print(str(ct)+'======')
        return ct != 0

    def getPreS1LightOn(self):
        if len(self.data._s1Array) > 0:
            return self.data._s1Array[len(self.data._s1Array) - 1]
        return 0
    def getPreS2LightOn(self):
        if len(self.data._s2Array) > 0:
            return self.data._s2Array[len(self.data._s2Array)-1]
        return 0
    def getRoomPreStatu(self):
        if len(self.data._roomArray) == 0:
            return IntMessage.ready
        return self.data._roomArray[len(self.data._roomArray)-1]

    def dummyFunction(self):
        a = 0
        # DBG("dummy")

    def s1EventComming(self, statu):
        DBG("s1EventComming:")
        preStatu = self.getRoomPreStatu()
        if preStatu == IntMessage.use:
            if statu == 0:
                self.data.ckStatu = ThreadCheckStatus.checking_serve_or_clean
        if preStatu == IntMessage.serve:
            if statu == 0:
                self.data.ckStatu = ThreadCheckStatus.checking_serve_or_clean

    def s2EventComming(self, statu):
        preStatu = self.getRoomPreStatu()
        # DBG("s2EventComming:" + str(statu) + '---room Statu:' + str(preStatu))
        if preStatu == IntMessage.ready:
            # 收到s2灭掉信号
            if statu == 0:
                self.dummyFunction()
            # 收到s2亮信号
            else:
                DBG('check')
                if self.data.getChecking() == False:
                    DBG('check1')
                    # if self.getPreS2LightOn() == 0:
                    DBG('check2')
                    self.data.setChecking()
                    DBG('check3')
                    self.data.ckStatu = ThreadCheckStatus.checking_use_or_serve
        elif preStatu == IntMessage.use:
            # 收到s2灭掉信号
            if statu == 0:
                if self.data.getChecking() == False:
                    #3s内s2有亮的情况
                    if self.data.check01(self.data._s2Array,3):
                        # while True:
                        #     time.sleep(1)
                            if self.getPreS1LightOn() == 0:
                                self.data.setChecking()
                                self.data.ckStatu = ThreadCheckStatus.checking_use_or_clean
                                # break
            # 收到s2亮信号
            else:
                if self.isHasBeacons():
                    # 判断上一个s1在10s内是否是1或0
                    if self.beaconComming():
                        self.setRoomStatu(IntMessage.serve, '')
        elif preStatu == IntMessage.serve:
            # 收到s2灭掉信号
            if statu == 0:
                self.setRoomStatu(IntMessage.clean, '')
            # 收到s2亮信号
            else:
                self.dummyFunction()
        elif preStatu == IntMessage.clean:
            self.dummyFunction()

    def setRoomStatu(self, statu,payload):
        DBG("setRoomStatu:")
        self.data._roomArray.append(statu)
        preStatu = statu
        if preStatu == IntMessage.ready:
            self._ui.statuLeftBtn.setText("IS READY")
            self._ui.statuLeftBtn.setStyleSheet("QPushButton {background-color:rgb(33, 255, 6);color: white; border: none;font-size:24px;}");

            # self._ui.statuLeftBtn.setStyleSheet("QPushButton {background-color: green; font-size:24px;} \
            #              QPushButton:hover:pressed {border-image:url(pic/pressed.jpg);font-size:24px;} \
            #              QPushButton:hover:!pressed {border-image:url(pic/hover.jpg);font-size:24px;} ");
            # self._ui.statuLeftBtn.setStyleSheet('''color: white;
            #                                  background-color: green;
            #                                  selection-color: red;
            #                                  selection-background-color: blue''')
            self._ui.statuRightBtn.setText("Please Come In")
        elif preStatu == IntMessage.use:
            self._ui.statuLeftBtn.setText("IN USE")
            self._ui.statuLeftBtn.setStyleSheet("QPushButton {background-color: yellow;color: white; border: none;font-size:24px;}");
            self._ui.statuRightBtn.setText("Now Serve")
        elif preStatu == IntMessage.serve:
            self._ui.statuLeftBtn.setText("IN SERVICE")
            self._ui.statuLeftBtn.setStyleSheet("QPushButton {background-color: blue;color: white; border: none;font-size:24px;}");

            self._ui.statuRightBtn.setText("Now Serve")
        elif preStatu == IntMessage.clean:
            self._ui.statuLeftBtn.setText("NEED CLEAN")
            self._ui.statuLeftBtn.setStyleSheet("QPushButton {background-color: gray;color: white; border: none;font-size:24px;}");
            self._ui.statuRightBtn.setText("Do not enter")

    def fillModel(self, model, str, row, column):
        model.setItem(row, column, QtGui.QStandardItem(str))
        # 设置字符颜色
        model.item(row, column).setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
        # 设置字符位置
        self.model.item(row, column).setTextAlignment(QtCore.Qt.AlignCenter)
    def tableView_set(self,arr):

        # 添加表头：
        self.model = QtGui.QStandardItemModel(self._ui.tableView)
        # 设置单元格禁止更改
        self._ui.tableView.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        # 表头信息显示居中
        self._ui.tableView.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignCenter)
        # 设置表格属性：
        self.model.setRowCount(20)
        self.model.setColumnCount(6)
        # 设置列宽
        self._ui.tableView.setColumnWidth(0, 80)
        self._ui.tableView.setColumnWidth(1, 50)
        self._ui.tableView.setColumnWidth(2, 50)
        self._ui.tableView.setColumnWidth(3, 120)
        self._ui.tableView.setColumnWidth(4, 60)
        self._ui.tableView.setColumnWidth(5, 60)
        index = 0
        # 设置表头
        self.model.setHeaderData(0, QtCore.Qt.Horizontal, _fromUtf8(u"DIST"))
        self.model.setHeaderData(1, QtCore.Qt.Horizontal, _fromUtf8(u"TX"))
        self.model.setHeaderData(2, QtCore.Qt.Horizontal, _fromUtf8(u"RSSI"))
        self.model.setHeaderData(3, QtCore.Qt.Horizontal, _fromUtf8(u"UUID"))
        self.model.setHeaderData(4, QtCore.Qt.Horizontal, _fromUtf8(u"MAJOR"))
        self.model.setHeaderData(5, QtCore.Qt.Horizontal, _fromUtf8(u"MINOR"))
        # 添加表项
        for item in arr:
            self.fillModel(self.model, str(round(self.calculateDistance(item['TX'], item['RSSI']), 2)) + " m", index, 0)
            self.fillModel(self.model, str(item['TX']), index, 1)
            self.fillModel(self.model, str(item['RSSI']), index, 2)
            self.fillModel(self.model, item['UUID'], index, 3)
            self.fillModel(self.model, str(item['MAJOR']), index, 4)
            self.fillModel(self.model, str(item['MINOR']), index, 5)
            index += 1
        self._ui.tableView.setModel(self.model)
    @staticmethod
    def calculateDistance(self, txPower, rssi):
        rssi = float(rssi)
        txPower = float(txPower)

        if rssi == 0:
            return -1.0

        ratio = rssi * 1.0 / txPower
        if ratio < 1.0:
            return math.pow(ratio, 10)
        else:
            accuracy = (0.89976) * math.pow(ratio, 7.7095) + 0.111
            return accuracy
    def fillLabel(self, label, msg, statu):
        label.setText(msg)
        if statu == 1:
            pe = QPalette()
            pe.setColor(QPalette.WindowText, Qt.red)
            pe.setColor(QPalette.Window, Qt.white)
            label.setPalette(pe)
        else:
            pe = QPalette()
            pe.setColor(QPalette.WindowText, Qt.white)
            pe.setColor(QPalette.Window, Qt.darkGray)
            label.setPalette(pe)

    def comm(self, msg):
        pl = msg.get_payload()
        if msg.get_type() is IntMessage.ALERT_GUI:
            self.show_dialog(msg.get_payload()['ALERT_TEXT'], msg.get_payload()['ALERT_DETAIL'])
        if msg.get_type() is IntMessage.LED1LightOn:
            self.fillLabel(self._ui.led1Lbl, "LED1Light On", 1)
            self.data._s1Array.append({'s': 1, 't': time.time()})
            self.s1EventComming(1)
            # DBG("led1Light On:")
        if msg.get_type() is IntMessage.LED1LightOff:
            self.fillLabel(self._ui.led1Lbl, "LED1Light Off", 0)
            self.data._s1Array.append({'s': 0, 't': time.time()})
            self.s1EventComming(0)
            # DBG("led1Light Off:")
        if msg.get_type() is IntMessage.LED2LightOn:
            self.fillLabel(self._ui.led2Lbl, "LED2Light On", 1)
            self.data._s2Array.append({'s': 1, 't': time.time()})
            self.s2EventComming(1)
            # DBG("LED2Light:On")
        if msg.get_type() is IntMessage.LED2LightOff:
            self.fillLabel(self._ui.led2Lbl, "LED2Light Off", 0)
            self.data._s2Array.append({'s': 1, 't': time.time()})
            self.s2EventComming(0)
            # DBG("LED2Light:Off")


        #Beacon scan - parameters textbox output
        blebar = self._ui.bcscanausgabe.verticalScrollBar()

        if msg.get_type() is IntMessage.SCANNED_IBEACON:
            # DBG(pl)
            # DBG(type(pl))
            # self._ui.bcscanausgabe.append('iBeacon' + '\nUUID: ' + '\t' + pl['UUID'] + '\n')
            self._ui.bcscanausgabe.append('iBeacon' + '\nUUID: ' + '\t' + str(pl['UUID']) + '\nMAJOR: ' + '\t' + str(pl['MAJOR']) + '\nMINOR: ' + '\t' + str(pl['MINOR']) + '\nTX: ' + '\t' + str(pl['TX']) + '\tRSSI: ' + '\t' + str(pl['RSSI']) + '\tdist'+str(self.calculateDistance(pl['TX'],pl['RSSI']))+ '\n')
            blebar.setValue(blebar.maximum())
            find = False
            for index, item in enumerate(self.data._beaconsArray):
                if(item['UUID'] == pl['UUID'] and item['MAJOR'] == pl['MAJOR'] and item['MINOR'] == pl['MINOR']):
                    find = True
                    self.data._beaconsArray[index] = pl
                    break
            if(find == False):
                self.data._beaconsArray.append(pl)

            self.setHistoryBeaconBehavior(pl)
            self.tableView_set(self.data._beaconsArray)

        #print sent signal into the outbox for each beacon type
        if msg.get_type() is IntMessage.SIGNAL_IBEACON:
            self._ui.ibgesendetessignal.append(str(pl['TEXT']))
        if msg.get_type() is IntMessage.GETSYSINFO:
            self._ui.sysInfoLbl.setText(str(pl['pyload']))


    #Definition of the alert box
    def show_dialog(self, msgtxt, detailtxt):
       msg = QMessageBox()
       msg.setIcon(QMessageBox.Information)
       msg.setText(msgtxt)
       msg.setWindowTitle("Alert")
       msg.setDetailedText(detailtxt)
       msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
       DBG ("value of pressed message box button:"), retval

    def start_gui(self):
        self._app = QtGui.QApplication(sys.argv)
        self._mainwindow = QtGui.QMainWindow()
        self._ui = Ui_PiBeacon()
        self._ui.setupUi(self._mainwindow)
        self.bcscan()
        self.saved_values()

        self._ui.led1Lbl.setAutoFillBackground(True)
        self._ui.led2Lbl.setAutoFillBackground(True)

        self.setRoomStatu(IntMessage.ready, '')
        self._mainwindow.show()
        self._ui.menuSave.triggered[QAction].connect(self.save_to_config)
        self._app.aboutToQuit.connect(self.uiclosed)
        sys.exit(self._app.exec_())

    #load saved values from config
    def saved_values(self):
        DBG("saved_values:")

    # save values to config
    def save_to_config(self):
        DBG("save_to_config:")
        self.show_dialog("Saved current values!", "The current values of all Beacons have been saved."
                                                  "They will be available on the next application start.")

    #Beacon Scan Output
    def bcscan(self):
        self._ui.bcscanstart.clicked.connect(self.bcscanstart_clicked)
        self._ui.bcscanstop.clicked.connect(self.bcscanstop_clicked)
        self._ui.getSysBtn.clicked.connect(self.getSysBtn_clicked)
        self._ui.stopGetSysBtn.clicked.connect(self.stopGetSysBtn_clicked)
        self._ui.statuLeftBtn.clicked.connect(self.statuLeftButton_clicked)
        self._ui.statuRightBtn.clicked.connect(self.statuRightButton_clicked)

    def getSysBtn_clicked(self):
        DBG('getSysBtn_clicked')
        msg = IntMessage(IntMessage.GETSYSINFO)
        self._commCallback(msg)

    def stopGetSysBtn_clicked(self):
        DBG('stopGetSysBtn_clicked')
        msg = IntMessage(IntMessage.STOPGETSYSINFO)
        self._commCallback(msg)

    def bcscanstart_clicked(self):

        msg = IntMessage(IntMessage.START_SCAN_BLE)
        self._commCallback(msg)
        DBG ("Scan Button clicked")

    def bcscanstop_clicked(self):

        msg = IntMessage(IntMessage.STOP_SCAN_BLE)
        self._commCallback(msg)
        DBG ("Stop Button clicked")

    def btscanstart_clicked(self):

        msg = IntMessage(IntMessage.START_SCAN_BT)
        self._commCallback(msg)

    def statuLeftButton_clicked(self):
        preStatu = self.getRoomPreStatu()
        DBG('---room Statu:' + str(preStatu))
        if preStatu == IntMessage.clean:
            self.setRoomStatu(IntMessage.ready, '')

    def statuRightButton_clicked(self):
        preStatu = self.getRoomPreStatu()
        DBG('---room Statu:' + str(preStatu))
        if preStatu == IntMessage.clean:
            self.setRoomStatu(IntMessage.ready, '')

    #ui closed
    def uiclosed(self):
        msg = IntMessage(IntMessage.QUITAPP)
        self._commCallback(msg)
        #self._app.exec_()


