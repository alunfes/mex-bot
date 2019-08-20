from PrivateWS import PrivateWS
from RealtimeWSAPI import RealtimeWSAPI
import threading


class WSData:
    @classmethod
    def initialize(cls):
        cls.trades = []
        rwa = RealtimeWSAPI()


    @classmethod
    def add_trades(cls, trade):
        cls.trades.append(trade)
        print(cls.trades)


if __name__ == '__main__':
    WSData.initialize()

