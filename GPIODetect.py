import RPi.GPIO as GPIO
from repeat import RepeatTimer
from comm.intmessage import IntMessage
# from utils.debug import DBG


class GPIODetect():

    _commCallback = None
    repeatThread = RepeatTimer(1000, None)

    def __init__(self, commCallback):
        self._commCallback = commCallback

    def setup(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(12, GPIO.IN)
        GPIO.setup(16, GPIO.IN)
        GPIO.setup(21, GPIO.OUT)
        pass

    def detctThreadWork(self):
        # DBG("detctThreadWork!")
        if GPIO.input(12) == True:
            self._commCallback(IntMessage.LED1LightOn)
            # print("Someone is closing to No 1 !")
        else:
            self._commCallback(IntMessage.LED1LightOff)
            # print("No 1 Noanybody!")
        if GPIO.input(16) == True:
            self._commCallback(IntMessage.LED2LightOn)
            # print("Someone is closing to No 2 !")
        else:
            self._commCallback(IntMessage.LED2LightOff)
            # print("No 2 Noanybody!")

    def detct(self):
        # DBG("detct!")
        self.repeatThread = RepeatTimer(2, self.detctThreadWork)
        self.repeatThread.start()

    def cleanup(self):
        self.repeatThread.cancel()
        GPIO.cleanup()