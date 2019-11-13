from LgbModel import LgbModel
from OneMinMarketData import OneMinMarketData
from RealtimeWSAPI import RealtimeWSAPI
from SystemFlg import SystemFlg
import time

class Test:
    def start(self):
        OneMinMarketData.initialize_for_bot(10)
        lgb = LgbModel()
        ws = RealtimeWSAPI()
        while True:
           time.sleep(1)

if __name__ == '__main__':
    SystemFlg.initialize()
    t = Test()
    t.start()
