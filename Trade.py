import requests
import ccxt
import time


class Trade:
    @classmethod
    def initialize(cls):
        bm = ccxt.bitmex({‘apiKey’: ‘APIキーを入れる’,‘secret’: ‘secretを入れる’,})