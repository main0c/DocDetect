import RPi.GPIO as GPIO
from repeat import RepeatTimer
from comm.intmessage import IntMessage
from utils.debug import DBG
import enum
import time  # 引入time模块



class ThreadCheckStatus(enum.Enum):
    checking_no = 3
    checking_use_or_serve = 0
    checking_serve_or_clean = 1
    checking_use_or_clean = 2


class DetectManager():
    # beacon距离数组
    _bstatusDic = {}
    # s1灯时序数组
    _s1Array = []
    # dict = {'s': 1, 't': 123456};
    # s2灯时序数组
    _s2Array = []
    # 当前房间时序数组
    _roomArray = []
    _beaconsArray = []

    ckStatu = ThreadCheckStatus.checking_no

    def __init__(self):
        self.pool=[1,2,3]
        self.checking = False

    def setChecking(self):
        self.checking = True
    def resetChecking(self):
        self.checking = False
    def getChecking(self):
        return self.checking
    def get(self):
        if self.pool.__len__()>0:
            return self.pool.pop()
        else:
            return None
    def add(self,data):
        self.pool.append(data)
    def print(self):
        print(self.pool)
    def show(self):
        copy=self.pool[:]
        return copy
 # ts之内有010
    def check010(self, arr, ts):
        isFind = False
        st = 0;
        ctime = time.time()-ts
        idx = len(arr)
        while (idx > 0):
            idx = idx-1
            print(str(arr[idx]))
            print('---')
            print(str(st))

            dt = arr[idx]
            if dt['t'] > ctime:
                if st == 0:
                    if dt['s'] == 0:
                        st = 1
                elif st == 1:
                    if dt['s'] == 1:
                        st = 2
                elif st == 2:
                    if dt['s'] == 0:
                        st = 3
            else:
                break
        if st == 3:
            isFind = True
        return isFind

    # ts之内有01
    def check01(self, arr, ts):
        isFind = False
        st = 0;
        ctime = time.time() - ts
        idx = len(arr)
        while (idx > 0):
            idx = idx - 1
            dt = arr[idx]
            if dt['t'] > ctime:
                if st == 0:
                    if dt['s'] == 1:
                        st = 1
                elif st == 1:
                    if dt['s'] == 0:
                        st = 2
            else:
                break
        if st == 2:
            isFind = True
        return isFind
    # ts之内有10
    def check10(self, arr, ts):
        isFind = False
        st = 0;
        ctime = time.time() - ts
        idx = len(arr)
        while (idx > 0):
            idx = idx - 1
            dt = arr[idx]
            if dt['t'] > ctime:
                if st == 0:
                    if dt['s'] == 0:
                        st = 1
                elif st == 1:
                    if dt['s'] == 1:
                        st = 2
            else:
                break
        if st == 2:
            isFind = True
        return isFind