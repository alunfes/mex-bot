import pandas as pd
from datetime import datetime
import time
import json
from bitmex_websocket import BitMEXWebsocket

'''
https://public.bitmex.com/?prefix=data/

timestamp,symbol,bidSize,bidPrice,askPrice,askSize
2019-04-19D00:00:05.759343000,ADAM19,159977,1.58e-05,1.581e-05,185957
2019-04-19D00:00:08.754300000,ADAM19,154354,1.58e-05,1.581e-05,185957
2019-04-19D00:00:08.792447000,ADAM19,124354,1.58e-05,1.581e-05,185957
2019-04-19D00:00:09.141532000,ADAM19,111575,1.58e-05,1.581e-05,185957
2019-04-19D00:00:09.496339000,ADAM19,111575,1.58e-05,1.581e-05,206760
2019-04-19D00:00:09.867536000,ADAM19,77576,1.58e-05,1.581e-05,206760
2019-04-19D00:00:10.303366000,ADAM19,77576,1.58e-05,1.581e-05,240760
2019-04-19D00:00:10.473032000,ADAM19,111576,1.58e-05,1.581e-05,240760
2019-04-19D00:00:10.615971000,ADAM19,77576,1.58e-05,1.581e-05,240760
2019-04-19D00:00:10.619206000,ADAM19,77576,1.58e-05,1.581e-05,206760
2019-04-19D00:00:22.902119000,ADAM19,71949,1.58e-05,1.581e-05,206760
2019-04-19D00:00:24.392009000,ADAM19,71949,1.58e-05,1.581e-05,176760
2019-04-19D00:00:24.751056000,ADAM19,71949,1.58e-05,1.581e-05,210760
2019-04-19D00:00:25.757368000,ADAM19,71949,1.58e-05,1.581e-05,215244
2019-04-19D00:00:27.311674000,ADAM19,72701,1.58e-05,1.581e-05,215244
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


if __name__ == '__main__':
    MarketData.initialize()
    MarketData.read_quote_from_csv()