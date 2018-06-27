import RPi.GPIO as GPIO
from repeat import RepeatTimer
from comm.intmessage import IntMessage
from utils.debug import DBG
import enum
import time  # 引入time模块
import json
import math



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

    def set_checking(self):
        self.checking = True
    def reset_checking(self):
        self.checking = False
    def get_checking(self):
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
        st = 0
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
        st = 0
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
        st = 0
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




    def setHistoryBeaconBehavior(self, pl):
        find = False
        strudid = ''+str(pl['UUID']) + str(pl['MINOR']) + str(pl['MAJOR'])
        for key in self._bstatusDic:
            if (strudid == key):
                find = True
                arr = self._bstatusDic[strudid]
                arr.append(pl)
                self._bstatusDic[strudid] = arr
                break
        if (find == False):
            self._bstatusDic[strudid] = [pl]
        # DBG("setHistoryBeaconBehavior:")
        # DBG(self._bstatusDic)


    def beaconComming(self):
        # 10s内beacon一直在数组中
        if len(self._beaconsArray) == 0:
            return False
        ct = 0
        avg = 0
        for key in self._bstatusDic:
            arr = self._bstatusDic[key]
            for index, pl in enumerate(arr):
                if time.time() - pl["time"] < 10:
                    avg = avg + self.calculate_distance(pl['TX'], pl['RSSI'])
                    ct = ct + 1
        if ct > 0:
            avg = avg/ct
        print(str(avg) + 'avg======')
        return avg < 10
    def is_has_beacons(self):
        #10s内beacon一直在数组中
        if len(self._beaconsArray) == 0:
            return False
        ct = 0
        for index, pl in enumerate(self._beaconsArray):
            if time.time()- pl["time"] < 10:
                ct = ct + 1
        print(str(ct)+'======')
        return ct != 0

    def getPreS1LightOn(self):
        if len(self._s1Array) > 0:
            return self._s1Array[len(self._s1Array) - 1]
        return 0
    def getPreS2LightOn(self):
        if len(self._s2Array) > 0:
            return self._s2Array[len(self._s2Array)-1]
        return 0
    def getRoomPreStatu(self):
        if len(self._roomArray) == 0:
            return IntMessage.ready
        return self._roomArray[len(self._roomArray)-1]

    def dummyFunction(self):
        a = 0
        # DBG("dummy")

    def s1EventComming(self, statu):
        DBG("s1EventComming:")
        preStatu = self.getRoomPreStatu()
        if preStatu == IntMessage.use:
            if statu == 0:
                self.ckStatu = ThreadCheckStatus.checking_serve_or_clean
        if preStatu == IntMessage.serve:
            if statu == 0:
                self.ckStatu = ThreadCheckStatus.checking_serve_or_clean

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
                if self.get_checking() == False:
                    DBG('check1')
                    # if self.getPreS2LightOn() == 0:
                    DBG('check2')
                    self.set_checking()
                    DBG('check3')
                    self.ckStatu = ThreadCheckStatus.checking_use_or_serve
        elif preStatu == IntMessage.use:
            # 收到s2灭掉信号
            if statu == 0:
                if self.get_checking() == False:
                    #3s内s2有亮的情况
                    if self.check01(self._s2Array,3):
                        # while True:
                        #     time.sleep(1)
                            if self.getPreS1LightOn() == 0:
                                self.set_checking()
                                self.ckStatu = ThreadCheckStatus.checking_use_or_clean
                                # break
            # 收到s2亮信号
            else:
                if self.is_has_beacons():
                    # 判断上一个s1在10s内是否是1或0
                    if self.beaconComming():
                        self.dummyFunction()
                        # self.setRoomStatu(IntMessage.serve, '')
        elif preStatu == IntMessage.serve:
            # 收到s2灭掉信号
            if statu == 0:
                self.dummyFunction()
                # self.setRoomStatu(IntMessage.clean, '')
            # 收到s2亮信号
            else:
                self.dummyFunction()
        elif preStatu == IntMessage.clean:
            self.dummyFunction()

    def calculate_distance(self, tx_power, rssi):
        rssi = float(rssi)
        tx_power = float(tx_power)

        if rssi == 0:
            return -1.0

        ratio = rssi * 1.0 / tx_power
        if ratio < 1.0:
            return math.pow(ratio, 10)
        else:
            accuracy = (0.89976) * math.pow(ratio, 7.7095) + 0.111
            return accuracy