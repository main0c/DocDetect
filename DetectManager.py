from comm.intmessage import IntMessage
from utils.debug import DBG
import enum
import time  # 引入time模块
import math



class ThreadCheckStatus(enum.Enum):
    checking_no = 3
    checking_use_or_serve = 0
    checking_serve_or_clean = 1
    checking_use_or_clean = 2


class DetectManager():
    # beacon距离数组
    bstatus_dic = {}
    # s1灯时序数组
    s1_array = []
    # dict = {'s': 1, 't': 123456};
    # s2灯时序数组
    s2_array = []
    # 当前房间时序数组
    room_array = []
    beacons_array = []

    ck_statu = ThreadCheckStatus.checking_no

    def __init__(self):
        self.pool = [1, 2, 3]
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
        is_find = False
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
            is_find = True
        return is_find

    # ts之内有01
    def check01(self, arr, ts):
        is_find = False
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
            is_find = True
        return is_find

    # ts之内有10
    def check10(self, arr, ts):
        is_find = False
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
            is_find = True
        return is_find

    def set_history_beacon_behavior(self, pl):
        find = False
        strudid = ''+str(pl['UUID']) + str(pl['MINOR']) + str(pl['MAJOR'])
        for key in self.bstatus_dic:
            if (strudid == key):
                find = True
                arr = self.bstatus_dic[strudid]
                arr.append(pl)
                self.bstatus_dic[strudid] = arr
                break
        if (find == False):
            self.bstatus_dic[strudid] = [pl]
        # DBG("set_history_beacon_behavior:")
        # DBG(self.bstatus_dic)

    def beacon_comming(self):
        # 10s内beacon一直在数组中
        if len(self.beacons_array) == 0:
            return False
        ct = 0
        avg = 0
        for key in self.bstatus_dic:
            arr = self.bstatus_dic[key]
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
        if len(self.beacons_array) == 0:
            return False
        ct = 0
        for index, pl in enumerate(self.beacons_array):
            if time.time()- pl["time"] < 10:
                ct = ct + 1
        print(str(ct)+'======')
        return ct != 0

    def get_pre_s1_lighton(self):
        if len(self.s1_array) > 0:
            return self.s1_array[len(self.s1_array) - 1]
        return 0

    def get_pre_s2_lighton(self):
        if len(self.s2_array) > 0:
            return self.s2_array[len(self.s2_array)-1]
        return 0

    def get_room_pre_statu(self):
        if len(self.room_array) == 0:
            return IntMessage.ready
        return self.room_array[len(self.room_array)-1]

    def dummy_function(self):
        a = 0
        return a
        # DBG("dummy")

    def s1_event_comming(self, statu):
        self.s1_array.append({'s': statu, 't': time.time()})
        # DBG("s1_event_comming:")
        pre_statu = self.get_room_pre_statu()
        if pre_statu == IntMessage.use:
            if statu == 0:
                self.ck_statu = ThreadCheckStatus.checking_serve_or_clean
        if pre_statu == IntMessage.serve:
            if statu == 0:
                self.ck_statu = ThreadCheckStatus.checking_serve_or_clean

    def s2_event_comming(self, statu):
        self.s2_array.append({'s': statu, 't': time.time()})
        pre_statu = self.get_room_pre_statu()
        # DBG("s2_event_comming:" + str(statu) + '---room Statu:' + str(pre_statu))
        if pre_statu == IntMessage.ready:
            # 收到s2灭掉信号
            if statu == 0:
                self.dummy_function()
            # 收到s2亮信号
            else:
                DBG('check')
                if self.get_checking() == False:
                    DBG('check1')
                    # if self.get_pre_s2_lighton() == 0:
                    DBG('check2')
                    self.set_checking()
                    DBG('check3')
                    self.ckStatu = ThreadCheckStatus.checking_use_or_serve
        elif pre_statu == IntMessage.use:
            # 收到s2灭掉信号
            if statu == 0:
                if self.get_checking() == False:
                    #3s内s2有亮的情况
                    if self.check01(self.s2_array,3):
                        # while True:
                        #     time.sleep(1)
                            if self.get_pre_s1_lighton() == 0:
                                self.set_checking()
                                self.ckStatu = ThreadCheckStatus.checking_use_or_clean
                                # break
            # 收到s2亮信号
            else:
                if self.is_has_beacons():
                    # 判断上一个s1在10s内是否是1或0
                    if self.beacon_comming():
                        self.dummy_function()
                        # self.setRoomStatu(IntMessage.serve, '')
        elif pre_statu == IntMessage.serve:
            # 收到s2灭掉信号
            if statu == 0:
                self.dummy_function()
                # self.setRoomStatu(IntMessage.clean, '')
            # 收到s2亮信号
            else:
                self.dummy_function()
        elif pre_statu == IntMessage.clean:
            self.dummy_function()

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