import queue
import json

import time

from PyQt4.QtCore import *
from DetectManager import ThreadCheckStatus
from comm.intmessage import IntMessage
from utils.debug import DBG

# ready=0\in use=1\service=2\clean=3\

g_check_queue = queue.Queue(2048)


class CheckingThread(QThread):
    # 定义信号,定义参数为str类型
    _signal = pyqtSignal(str)
    _check_time = 0

    def __init__(self, data, tid, lock):
        super(CheckingThread, self).__init__()
        self.tid = tid
        self.data = data
        self.lock = lock

    def check_use_or_serve(self):
        # READY状态下判断S2亮 use or Serve:
        # 前10s判断s1有010状态变更
        DBG('check_use_or_serve')
        if self.data.check010(self.data.s1_array, 10) is True:
            DBG('check_use_or_serve 1')
            # 查找3s内beaconArray有没有在附近
            time.sleep(3)
            DBG('check_use_or_serve 2')
            if len(self.data.beacons_array) == 0:
                DBG('check_use_or_serve 3')
                # 设置use状态
                dic = {'type': int(IntMessage.use), 'pyload': ''}
                input = json.dumps(dic)
                self._signal.emit(input)
            else:
                DBG('check_use_or_serve 4')
                # 设置serve状态，并且获取最近的beacon
                input = json.dumps(self.data.check_nearest_beacon(5))
                self._signal.emit(input)

    def use_check_serve_or_clean(self):
        # USE状态下判断serve or clean:
        # S1亮灯后判断3s后S2有010状态变更Y—再判断附近有没有beacon Y:SERVE N:USE
        time.sleep(3)
        input = json.dumps(self.data.check_nearest_beacon(5))
        self._signal.emit(input)
        # S2亮灯后判断3s后S2有没有010，有再判断2s后S1有没有010，Y:再判断附近有没有beacon SERVE N再判断S2有没有010Y:USE N:CLEAN
        time.sleep(10)

    def serve_check_use(self):
        time.sleep(10)
        # SERVE状态下判断serve or clean:
        # S2亮前10s判断s1有010状态变更
        time.sleep(3)
        input = json.dumps(self.data.check_nearest_beacon(5))
        self._signal.emit(input)
        # USE：S1-1情况下判断未来3s有没有S2-010再判断S1后来有没有010如果有设置clean
        #       然后搜索附近beacon，如果有beacon找最近beacon设置serve

    def check_use_or_clean(self):
        # USE状态下判断serve or clean:前10s判断s1有010状态变更
        time.sleep(10)
        # READY状态下判断S2亮 use or Serve:
        # 前10s判断s1有010状态变更
        if self.data.check010(self.datas1_array, 10) is True:
            # 查找3s内beaconArray有没有在附近
            time.sleep(3)
            if len(self.data.beacons_array) == 0:
                # 设置use状态
                dic = {'type': int(IntMessage.use), 'pyload': ''}
                input = json.dumps(dic)
                self._signal.emit(input)
            else:
                # 设置serve状态，并且获取最近的beacon
                dic = {'type': int(IntMessage.serve), 'pyload': str(self.data.check_nearest_beacon(5))}
                input = json.dumps(dic)
                self._signal.emit(input)

    def run(self):
        # DBG("run!")
        while True:
            if g_check_queue.empty():
                time.sleep(1)
                # DBG("CheckingThread")
                self.lock.acquire()

                if self.data.get_checking() is True:
                    if self.data.ck_statu == ThreadCheckStatus.checking_use_or_serve:
                        self.check_use_or_serve()
                    elif self.data.ck_statu == ThreadCheckStatus.checking_serve_or_clean:
                        # 判断当前是否离开，离开的话beacon arr=0
                        self.checkServeOrClean()
                    elif self.data.ck_statu == ThreadCheckStatus.checking_use_or_clean:
                        self.checkUserOrClean()
                    else:
                        DBG("get_checking == TRUE 5")
                self.data.reset_checking()
                self.lock.release()
            else:
                data = g_check_queue.get()
                # DBG(data)
                self._signal.emit(data)
