import threading
import time
from multiprocessing import Process
class boss():
    def __init__(self):
        data=list_manage()
        lock=threading.Lock()
        self.data=data
        c0=consume(data,'c0',lock)
        p=product(data,'p',lock)
        c1=consume(data,'c1',lock)
        c0.start()
        p.start()
        c1.start()
        self.go()
    def go(self):
        while True:
            time.sleep(0.1)
            # print('root process',self.data)
            # self.data.print()
            print('boss check , ',self.data.show())

class consume(threading.Thread):
    def __init__(self,data,id,lock):
        threading.Thread.__init__(self)
        self.id=id
        self.data=data
        self.lock=lock
        # self.run(data)
    def run(self):
        while True :
            time.sleep(1)
            self.lock.acquire()
            print('thread ',self.id,' consume once,get ',self.data.get())
            self.lock.release()

class product(threading.Thread):
    def __init__(self,data,id,lock):
        threading.Thread.__init__(self)
        self.id=id
        self.data=data
        self.lock=lock
    def run(self):
        count=0
        while True:
            count+=1
            time.sleep(0.4)
            self.lock.acquire()
            self.data.add(count)
            self.lock.release()
            print('thread ',self.id,' product once, add ',count)

class list_manage():
    def __init__(self):
        self.pool=[1,2,3]
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

if __name__=='__main__':
    p=Process(target=boss,args=())
    p.start()
