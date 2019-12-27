from LgbModel import LgbModel
from OneMinMarketData import OneMinMarketData
from RealtimeWSAPI import RealtimeWSAPI
from Bot import Bot
from LogMaster import LogMaster
from SystemFlg import SystemFlg
import time
from LineNotification import LineNotification

class Test:
    def start(self):
        LineNotification.initialize()
        OneMinMarketData.initialize_for_bot()
        ws = RealtimeWSAPI()
        bot = Bot('./Data/sim_log.csv', True)
        while True:
           time.sleep(1)

if __name__ == '__main__':
    SystemFlg.initialize()
    t = Test()
    t.start()
