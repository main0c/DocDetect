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

    _signal = pyqtSignal(str, name='CheckingThread')
    _check_time = 0

    def __init__(self, data, tid, lock):
        super(CheckingThread, self).__init__()
        self.tid = tid
        self.data = data
        self.lock = lock

    # ts之内有010
    @staticmethod
    def check010(arr, ts):
        is_find = False
        st = 0

        ctime = time.time()-ts
        idx = len(arr)
        if idx == 1:
            dt = arr[0]
            if dt['s'] == 1:
                st = 3
        elif idx == 2:
            while idx > 0:
                idx = idx - 1
                dt = arr[idx]
                if dt['t'] > ctime:
                    if st == 0:
                        if dt['s'] == 0:
                            st = 1
                        else:
                            st = 3
                            break
                    elif st == 1:
                        if dt['s'] == 1:
                            st = 3
                            break
                else:
                    break
        else:
            while idx > 0:
                idx = idx-1
                dt = arr[idx]
                DBG(str(dt)+str(idx))
                if dt['t'] > ctime:
                    if st == 0:
                        if dt['s'] == 0:
                            st = 1
                        else:
                            st = 3
                            break
                    elif st == 1:
                        if dt['s'] == 1:
                            st = 3
                        else:
                            st = 1
                            break
                    elif st == 2:
                        if dt['s'] == 0:
                            st = 3
                            break
                else:
                    break
        if st == 3:
            is_find = True
        return is_find

    def check_use_or_serve(self):
        # READY状态下判断S2亮 use or Serve:
        # 前10s判断s1有010状态变更
        DBG('check_use_or_serve')
        if self.check010(self.data.s1_array, 10) is True:
            DBG('check_use_or_serve 1')
            # 查找3s内beaconArray有没有在附近
            time.sleep(3)
            DBG('check_use_or_serve 2')
            if len(self.data.beacons_array) == 0:
                DBG('check_use_or_serve 3')
                # 设置use状态
                dic = {'type': int(IntMessage.use), 'pyload': ''}
                self._signal.emit(json.dumps(dic))
            else:
                DBG('check_use_or_serve 4')
                # 设置serve状态，并且获取最近的beacon
                self._signal.emit(json.dumps(self.data.check_nearest_beacon(5)))

    def check_serve(self):
        DBG('check_serve')
        if self.check010(self.data.s1_array, 10) is True:
            DBG('check_serve 1')
            # 查找3s内beaconArray有没有在附近
            time.sleep(3)
            DBG('check_serve 2')
            if len(self.data.beacons_array) == 0:
                DBG('check_serve 3')
                # 设置use状态
                dic = {'type': int(IntMessage.use), 'pyload': ''}
                self._signal.emit(json.dumps(dic))
            else:
                DBG('check_use_or_serve 4')
                # 设置serve状态，并且获取最近的beacon
                self._signal.emit(json.dumps(self.data.check_nearest_beacon(5)))

    def check_serve_or_clean(self):
        DBG('check_serve_or_clean')
        if self.check010(self.data.s1_array, 10) is True:
            DBG('check_serve_or_clean 1')
            # 查找3s内beaconArray有没有在附近
            time.sleep(3)
            DBG('check_serve_or_clean 2')
            if len(self.data.beacons_array) == 0:
                DBG('check_serve_or_clean 3')
                # 设置use状态
                dic = {'type': int(IntMessage.clean), 'pyload': ''}
                self._signal.emit(json.dumps(dic))
            else:
                DBG('check_use_or_serve 4')
                # 设置serve状态，并且获取最近的beacon
                self._signal.emit(json.dumps(self.data.check_nearest_beacon(10)))

    def serve_check_use(self):
        time.sleep(10)
        # SERVE状态下判断serve or clean:
        # S2亮前10s判断s1有010状态变更
        time.sleep(3)
        self._signal.emit(json.dumps(self.data.check_nearest_beacon(5)))
        # USE：S1-1情况下判断未来3s有没有S2-010再判断S1后来有没有010如果有设置clean
        #       然后搜索附近beacon，如果有beacon找最近beacon设置serve

    def check_use_or_clean(self):
        # USE状态下判断serve or clean:前10s判断s1有010状态变更
        time.sleep(10)
        # READY状态下判断S2亮 use or Serve:
        # 前10s判断s1有010状态变更
        if self.check010(self.datas1_array, 10) is True:
            # 查找3s内beaconArray有没有在附近
            time.sleep(3)
            if len(self.data.beacons_array) == 0:
                # 设置use状态
                dic = {'type': int(IntMessage.use), 'pyload': ''}
                self._signal.emit(json.dumps(dic))
            else:
                # 设置serve状态，并且获取最近的beacon
                dic = {'type': int(IntMessage.serve), 'pyload': str(self.data.check_nearest_beacon(5))}
                self._signal.emit(json.dumps(dic))

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
                    elif self.data.ck_statu == ThreadCheckStatus.checking_serve:
                        self.check_serve()
                    elif self.data.ck_statu == ThreadCheckStatus.checking_serve_or_clean:
                        self.check_serve_or_clean()
                    # elif self.data.ck_statu == ThreadCheckStatus.checking_use_or_clean:
                    #     self.check_use_or_clean()
                    else:
                        DBG("get_checking == TRUE 5")
                self.data.reset_checking()
                self.lock.release()
            else:
                data = g_check_queue.get()
                # DBG(data)
                self._signal.emit(data)
