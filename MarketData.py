import pandas as pd
from datetime import datetime
import time
import json
from bitmex_websocket import BitMEXWebsocket
from datetime import datetime
import calendar, requests

'''
https://www.bitmex.com/api/udf/history?symbol=XBTUSD&resolution=1&from=1555771700&to=1555858100

'''


class MarketData:
    @classmethod
    def initialize(cls):
        api_info = open('./ignore/api.json', "r")
        json_data = json.load(api_info)  # JSON形式で読み込む
        id = json_data['id']
        secret = json_data['secret']
        api_info.close()
        cls.ws = BitMEXWebsocket(endpoint="https://www.bitmex.com/api/v1", symbol="XBTUSD", api_key=id,
                             api_secret=secret)
        cls.ws.get_instrument()

    @classmethod
    def read_quote_from_csv(cls):
        try:
            while cls.ws.ws.sock.connected:

                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                # Ticker情報を取得！
                tick = cls.ws.get_ticker()
                # ポジション情報を取得！(get_position()はありませんが、プロパティ「data」の中にちゃんと入ってるんですね)
                # ただし、ポジションが一つもない場合、'position'というデータ自体がありませんので、そこを考慮します
                if 'position' in cls.ws.data:
                    positions = cls.ws.data['position']
                else:
                    positions = []
                # 取得したポジション情報には現在保有している全ての通貨セットのポジションが含まれますので、'XBTUSD'でフィルタリングします
                positions = [position for position in positions if position['symbol'] == 'XBTUSD']

                print("%s : ticker : %s" % (now, tick))
                for position in positions:
                    print("%s : position : synbol %s : qty %s" % (now, position['symbol'], position['currentQty']))
                    #print("%s : position : synbol %s : qty %s" % (now, position['symbol'], position['currentQty']))

                # 0.1秒ごとに繰り返します！
                time.sleep(0.1)
        except:
            cls.ws.exit()

    @classmethod
    def download_hist_ohlc(cls, symbol, period, from_ut, to_ut):
        # 現在時刻のUTC naiveオブジェクト
        now = datetime.utcnow()

        # UTC naiveオブジェクト -> Unix time
        unixtime = calendar.timegm(now.utctimetuple())

        # 60分前のUnixTime
        since = unixtime - 60 * 60

        # APIリクエスト(1時間前から現在までの5m足OHLCVデータを取得)
        param = {"period": 5, "from": since, "to": unixtime}
        url = "https://www.bitmex.com/api/udf/history?symbol=XBTUSD&resolution={period}&from={from}&to={to}".format(
            **param)
        res = requests.get(url)
        data = res.json()

        # レスポンスのjsonデータからOHLCVのDataFrameを作成
        df = pd.DataFrame({
            "timestamp": data["t"],
            "open": data["o"],
            "high": data["h"],
            "low": data["l"],
            "close": data["c"],
            "volume": data["v"],
        }, columns=["timestamp", "open", "high", "low", "close", "volume"])



if __name__ == '__main__':
    MarketData.initialize()
    MarketData.read_quote_from_csv()