import os

from repeat import RepeatTimer
from comm.intmessage import IntMessage
from utils.debug import DBG

class GetSysInfo():
    _commCallback = None
    _repeatThread = RepeatTimer(1000,None)

    # def __init__(self):
    def __init__(self):
        super(GetSysInfo,self).__init__()
        self._repeatThread = RepeatTimer(1, self.detctThreadWork)
    def setcommCallback(self, commCallback):
        self._commCallback = commCallback

    # Return CPU temperature as a character string
    def getCPUtemperature(self):
        res = os.popen('vcgencmd measure_temp').readline()
        return (res.replace("temp=", "").replace("'C\n", ""))


# Return RAM information (unit=kb) in a list
# Index 0: total RAM
# Index 1: used RAM
# Index 2: free RAM
    def getRAMinfo(self):
        p = os.popen('free')
        i = 0
        while 1:
            i = i + 1
            line = p.readline()
            if i == 2:
                return (line.split()[1:4])

# Return % of CPU used by user as a character string
    def getCPUuse(self):
        return (str(os.popen("top -n1 | awk '/Cpu\(s\):/ {print $2}'").readline().strip()))


# Return information about disk space as a list (unit included)
# Index 0: total disk space
# Index 1: used disk space
# Index 2: remaining disk space
# Index 3: percentage of disk used
    def getDiskSpace(self):
        p = os.popen("df -h /")
        i = 0
        while 1:
            i = i + 1
            line = p.readline()
            if i == 2:
                return (line.split()[1:5])

    def detctThreadWork(self):
        # CPU informatiom
        DBG("detctThreadWork!")

        CPU_temp = self.getCPUtemperature()
        CPU_usage = self.getCPUuse()

        # RAM information
        # Output is in kb, here I convert it in Mb for readability
        RAM_stats = self.getRAMinfo()
        RAM_total = round(int(RAM_stats[0]) / 1000, 1)
        RAM_used = round(int(RAM_stats[1]) / 1000, 1)
        RAM_free = round(int(RAM_stats[2]) / 1000, 1)

        # Disk information
        DISK_stats = self.getDiskSpace()
        DISK_total = DISK_stats[0]
        DISK_used = DISK_stats[1]
        DISK_perc = DISK_stats[3]

        info = 'CPU Temperature = ' + CPU_temp
        info = info + '\nCPU Use = ' + CPU_usage
        info = info + '\nRAM Total = ' + str(RAM_total) + ' MB'
        info = info + '\nRAM Used = ' + str(RAM_used) + ' MB'
        info = info + '\nRAM Free = ' + str(RAM_free) + ' MB'

        info = info + '\nDISK Total Space = ' + str(DISK_total) + 'B'
        info = info + '\nDISK Used Space = ' + str(DISK_used) + 'B'
        info = info + '\nDISK Used Percentage = ' + str(DISK_perc)
        # print('')
        #
        # print('CPU Temperature = ' + CPU_temp)
        # print('CPU Use = ' + CPU_usage)
        # print('')
        # print('RAM Total = ' + str(RAM_total) + ' MB')
        # print('RAM Used = ' + str(RAM_used) + ' MB')
        # print('RAM Free = ' + str(RAM_free) + ' MB')
        # print('')
        # print('DISK Total Space = ' + str(DISK_total) + 'B')
        # print('DISK Used Space = ' + str(DISK_used) + 'B')
        # print('DISK Used Percentage = ' + str(DISK_perc))

        msg = IntMessage(IntMessage.GETSYSINFO,
                         {'pyload': info
                          })

        self._commCallback(msg)


    def detct(self):
        DBG("detct!")
        self._repeatThread.start()


    def cleanup(self):
        self._repeatThread.cancel()

