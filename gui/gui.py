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
import json
import threading

from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from gui.BeaconUI import Ui_PiBeacon
from DetectManager import DetectManager
from CheckingThread import CheckingThread
from comm.intmessage import IntMessage
from utils.debug import DBG

try:
    _fromutf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromutf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8


    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


class Gui:
    _commcallback = None
    _app = None
    _ui = None
    _mainwindow = None
    _thread = None

    def __init__(self, commcallback):
        self._commcallback = commcallback

        # ready=0\in use=1\service=2\clean=3\
        data = DetectManager()
        lock = threading.Lock()
        self.data = data
        _thread = CheckingThread(data, 'thread', lock)
        _thread._signal.connect(self.check_stack)
        _thread._check_time = 0
        _thread.start()
        self._thread = _thread

    def check_stack(self, msg):
        dic = json.loads(msg)
        pl = dic['pyload']
        if pl is '':
            self.set_room_statu({'type': dic['type'], 'pyload':  ''})
        else:
            self.set_room_statu({'type': dic['type'], 'pyload': eval(pl)})
        # self.set_room_statu(dict['type'], eval(dict['pyload']))

    def set_room_statu(self, dic):
        msg = IntMessage(dic['type'],  dic['pyload'])
        DBG("set_room_statu:"+str(msg.get_type()))

        self.data.room_array.append(msg.get_type())

        if msg.get_type() == IntMessage.ready:
            self._ui.statuLeftBtn.setText("IS READY")
            self._ui.statuLeftBtn.setStyleSheet(
                "QPushButton {background-color:rgb(33, 255, 6);color: white; border: none;font-size:24px;}")
            self._ui.statuRightBtn.setText("Please Come In")
        elif msg.get_type() == IntMessage.use:
            DBG("lai la!!!!!!")
            self._ui.statuLeftBtn.setText("IN USE")
            self._ui.statuLeftBtn.setStyleSheet(
                "QPushButton {background-color: yellow;color: white; border: none;font-size:24px;}")
            self._ui.statuRightBtn.setText("Now Serve")
        elif msg.get_type() == IntMessage.serve:
            pl = msg.get_payload()
            info = ('UUID:' + str(pl['UUID']) + 'MAJ:' + str(pl['MAJOR']) + 'MIN:' + str(pl['MINOR']))
            self._ui.becon_info_label.setText(info)
            self._ui.statuLeftBtn.setText("IN SERVICE")
            self._ui.statuLeftBtn.setStyleSheet(
                "QPushButton {background-color: blue;color: white; border: none;font-size:24px;}")

            self._ui.statuRightBtn.setText("Now Serve")
        elif msg.get_type() == IntMessage.clean:
            self._ui.statuLeftBtn.setText("NEED CLEAN")
            self._ui.statuLeftBtn.setStyleSheet(
                "QPushButton {background-color: gray;color: white; border: none;font-size:24px;}")
            self._ui.statuRightBtn.setText("Do not enter")

    def fill_model(self, model, strvalue, row, column):
        model.setItem(row, column, QtGui.QStandardItem(strvalue))
        # 设置字符颜色
        model.item(row, column).setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
        # 设置字符位置
        self.model.item(row, column).setTextAlignment(QtCore.Qt.AlignCenter)

    def tableview_set(self, arr):

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
        self.model.setHeaderData(0, QtCore.Qt.Horizontal, _fromutf8(u"DIST"))
        self.model.setHeaderData(1, QtCore.Qt.Horizontal, _fromutf8(u"TX"))
        self.model.setHeaderData(2, QtCore.Qt.Horizontal, _fromutf8(u"RSSI"))
        self.model.setHeaderData(3, QtCore.Qt.Horizontal, _fromutf8(u"UUID"))
        self.model.setHeaderData(4, QtCore.Qt.Horizontal, _fromutf8(u"MAJOR"))
        self.model.setHeaderData(5, QtCore.Qt.Horizontal, _fromutf8(u"MINOR"))
        # 添加表项
        for item in arr:
            self.fill_model(self.model, str(round(self.data.calculate_distance(item['TX'], item['RSSI']), 2)) + " m",
                            index, 0)
            self.fill_model(self.model, str(item['TX']), index, 1)
            self.fill_model(self.model, str(item['RSSI']), index, 2)
            self.fill_model(self.model, item['UUID'], index, 3)
            self.fill_model(self.model, str(item['MAJOR']), index, 4)
            self.fill_model(self.model, str(item['MINOR']), index, 5)
            index += 1
        self._ui.tableView.setModel(self.model)

    @staticmethod
    def fill_label(label, msg, statu):
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
            self.fill_label(self._ui.led1Lbl, "LED1Light On", 1)
            self.data.s1_event_comming(1)
            # DBG("led1Light On:")
        if msg.get_type() is IntMessage.LED1LightOff:
            self.fill_label(self._ui.led1Lbl, "LED1Light Off", 0)
            self.data.s1_event_comming(0)
            # DBG("led1Light Off:")
        if msg.get_type() is IntMessage.LED2LightOn:
            self.fill_label(self._ui.led2Lbl, "LED2Light On", 1)
            self.data.s2_event_comming(1)
            # DBG("LED2Light:On")
        if msg.get_type() is IntMessage.LED2LightOff:
            self.fill_label(self._ui.led2Lbl, "LED2Light Off", 0)
            self.data.s2_event_comming(0)
            # DBG("LED2Light:Off")

        # Beacon scan - parameters textbox output
        blebar = self._ui.bcscanausgabe.verticalScrollBar()

        if msg.get_type() is IntMessage.SCANNED_IBEACON:
            # DBG(pl)
            # DBG(type(pl))
            distance = self.data.calculate_distance(pl['TX'], pl['RSSI'])
            # 小于10m的beacon去掉
            if float(distance) < 10.0:
            # self._ui.bcscanausgabe.append('iBeacon' + '\nUUID: ' + '\t' + pl['UUID'] + '\n')
                self._ui.bcscanausgabe.append('iBeacon' + '\nUUID: ' + '\t' + str(pl['UUID']) + '\nMAJOR: ' + '\t' + str(
                    pl['MAJOR']) + '\nMINOR: ' + '\t' + str(pl['MINOR']) + '\nTX: ' + '\t' + str(
                    pl['TX']) + '\tRSSI: ' + '\t' + str(pl['RSSI']) + '\tdist' + str(
                    distance) + '\n')
                blebar.setValue(blebar.maximum())
                find = False
                for index, item in enumerate(self.data.beacons_array):
                    if (item['UUID'] == pl['UUID'] and item['MAJOR'] == pl['MAJOR'] and item['MINOR'] == pl['MINOR']):
                        find = True
                        self.data.beacons_array[index] = pl
                        break
                if find is False:
                    self.data.beacons_array.append(pl)

                self.data.set_history_beacon_behavior(pl)
                self.tableview_set(self.data.beacons_array)

        # print sent signal into the outbox for each beacon type
        if msg.get_type() is IntMessage.GETSYSINFO:
            self._ui.sysInfoLbl.setText(str(pl['pyload']))

    # Definition of the alert box
    def show_dialog(self, msgtxt, detailtxt):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(msgtxt)
        msg.setWindowTitle("Alert")
        msg.setDetailedText(detailtxt)
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        DBG("value of pressed message box button:")

    def start_gui(self):
        self._app = QtGui.QApplication(sys.argv)
        self._mainwindow = QtGui.QMainWindow()
        self._ui = Ui_PiBeacon()
        self._ui.setupUi(self._mainwindow)
        self.bcscan()
        self.saved_values()

        self._ui.led1Lbl.setAutoFillBackground(True)
        self._ui.led2Lbl.setAutoFillBackground(True)

        self.set_room_statu({'type': int(IntMessage.ready), 'pyload': ''})
        self._mainwindow.show()
        self._ui.menuSave.triggered[QAction].connect(self.save_to_config)
        self._app.aboutToQuit.connect(self.uiclosed)
        sys.exit(self._app.exec_())

    # load saved values from config
    @staticmethod
    def saved_values():
        DBG("saved_values:")

    # save values to config
    def save_to_config(self):
        DBG("save_to_config:")
        self.show_dialog("Saved current values!", "The current values of all Beacons have been saved."
                                                  "They will be available on the next application start.")

    # Beacon Scan Output
    def bcscan(self):
        self._ui.bcscanstart.clicked.connect(self.bcscanstart_clicked)
        self._ui.bcscanstop.clicked.connect(self.bcscanstop_clicked)
        self._ui.getSysBtn.clicked.connect(self.getsysbutton_clicked)
        self._ui.stopGetSysBtn.clicked.connect(self.stopgetsysbutton_clicked)
        self._ui.statuLeftBtn.clicked.connect(self.statuleftbutton_clicked)
        self._ui.statuRightBtn.clicked.connect(self.staturightbutton_clicked)

    def getsysbutton_clicked(self):
        DBG('getsysbutton_clicked')
        msg = IntMessage(IntMessage.GETSYSINFO)
        self._commcallback(msg)

    def stopgetsysbutton_clicked(self):
        DBG('stopgetsysbutton_clicked')
        msg = IntMessage(IntMessage.STOPGETSYSINFO)
        self._commcallback(msg)

    def bcscanstart_clicked(self):
        msg = IntMessage(IntMessage.START_SCAN_BLE)
        self._commcallback(msg)
        DBG("Scan Button clicked")

    def bcscanstop_clicked(self):
        msg = IntMessage(IntMessage.STOP_SCAN_BLE)
        self._commcallback(msg)
        DBG("Stop Button clicked")

    def statuleftbutton_clicked(self):
        pre_statu = self.data.get_room_pre_statu()
        DBG('---room Statu:' + str(pre_statu))
        if pre_statu == IntMessage.clean:
            self.set_room_statu({'type': int(IntMessage.ready), 'pyload': ''})

    def staturightbutton_clicked(self):
        pre_statu = self.data.get_room_pre_statu()
        DBG('---room Statu:' + str(pre_statu))
        if pre_statu == IntMessage.clean:
            self.set_room_statu({'type': int(IntMessage.ready), 'pyload': ''})

    # ui closed
    def uiclosed(self):
        msg = IntMessage(IntMessage.QUITAPP)
        self._commcallback(msg)
        # self._app.exec_()
