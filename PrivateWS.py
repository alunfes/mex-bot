import websocket
import json
import urllib
import hmac
import hashlib
import time
import pprint

class PrivateWSData:
    @classmethod
    def initialize(cls):
        cls.message = ''
        pws = PrivateWS()

class PrivateWS:
    def __init__(self):
        # サーバとのデータのやりとりを表示するため、Trueを指定する。（確認したくないのであればFalseで問題ないです）
        websocket.enableTrace(False)
        # 接続先URLと各コールバック関数を引数に指定して、WebSocketAppのインスタンスを作成
        self.ws_pub = websocket.WebSocketApp(url='wss://www.bitmex.com/realtime',
                                    on_open=self.on_open,
                                    on_message=self.on_message,
                                    on_close=self.on_close,
                                    on_error=self.on_error)
        self.ws_pub.run_forever()




    def signature(self, api_secret: str, verb: str, url: str, nonce: int) -> str:
        data = ''
        parsed_url = urllib.parse.urlparse(url)
        path = parsed_url.path
        if parsed_url.query:
            path = path + '?' + parsed_url.query
        message = (verb + path + str(nonce) + data).encode('utf-8')
        sign = hmac.new(api_secret.encode('utf-8'), message, digestmod=hashlib.sha256).hexdigest()
        return sign

    def on_open(self, ws):
        print('opened bitmex private ws.')
        api_info = open('./ignore/api.json', "r")
        json_data = json.load(api_info)  # JSON形式で読み込む
        id = json_data['id']
        secret = json_data['secret']
        api_info.close()
        expires = int(time.time()) + 1000000
        signature = self.signature(api_secret=secret, verb = 'GET', url = '/realtime', nonce = expires)
        auth = {
                   'op': 'authKeyExpires',
                   'args': [id, expires, signature]
        }
        ws.send(json.dumps(auth))

        channels = {
            'op': 'subscribe',
            'args': [
                'wallet',
                'execution:XBTUSD',
                'order:XBTUSD',
                'position:XBTUSD',
            ]
        }
        ws.send(json.dumps(channels))

    def on_message(self, ws, message):
        pprint.pprint(message)
        PrivateWSData.message = message



    def on_close(self, ws):
        print('closed private ws')
        self.__init__()

    def on_error(self, ws, error):
        print(error)

#wallet
'''
'{"table":"wallet","action":"partial","keys":["account","currency"],
"types":{"account":"long","currency":"symbol","prevDeposited":"long","prevWithdrawn":"long",
"prevTransferIn":"long","prevTransferOut":"long","prevAmount":"long","prevTimestamp":"timestamp","deltaDeposited":"long",
"deltaWithdrawn":"long","deltaTransferIn":"long","deltaTransferOut":"long","deltaAmount":"long","deposited":"long","withdrawn":"long",
"transferIn":"long","transferOut":"long","amount":"long","pendingCredit":"long","pendingDebit":"long","confirmedDebit":"long",
"timestamp":"timestamp","addr":"symbol","script":"symbol","withdrawalLock":"symbols"},"foreignKeys":{},
"attributes":{"account":"sorted","currency":"grouped"},"filter":{"account":243795},
"data":[{"account":243795,"currency":"XBt","prevDeposited":1500000,"prevWithdrawn":0,"prevTransferIn":0,"prevTransferOut":0,
"prevAmount":1500000,"prevTimestamp":"2019-05-09T12:00:00.000Z","deltaDeposited":0,"deltaWithdrawn":0,"deltaTransferIn":0,
"deltaTransferOut":0,"deltaAmount":0,"deposited":1500000,"withdrawn":0,"transferIn":0,"transferOut":0,"amount":1500000,
"pendingCredit":0,"pendingDebit":0,"confirmedDebit":0,"timestamp":"2019-05-09T12:00:00.124Z",
"addr":"3BMEXFDDJBWxoKAGCipo2netvuBa4brrfo",
"script":"534104",
"withdrawalLock":[]}]}'
'''
#position
'''
'{"table":"position","action":"update","data":[{"account":243795,"symbol":"XBTUSD","currency":"XBt","currentTimestamp":"2019-05-10T11:22:15.048Z","markPrice":6274.74,"timestamp":"2019-05-10T11:22:15.048Z","lastPrice":6274.74,"currentQty":0,"liquidationPrice":null}]}'
'{"table":"position","action":"update","data":[{"account":243795,"symbol":"XBTUSD","currency":"XBt","currentTimestamp":"2019-05-10T11:25:20.045Z","markPrice":6270.78,"timestamp":"2019-05-10T11:25:20.045Z","lastPrice":6270.78,"currentQty":1,"liquidationPrice":66.5}]}'
'{"table":"position","action":"update","data":[{"account":243795,"symbol":"XBTUSD","currency":"XBt","currentTimestamp":"2019-05-10T11:25:35.046Z","markPrice":6273.79,"markValue":-15939,"riskValue":15939,"homeNotional":0.00015939,"maintMargin":191,"unrealisedGrossPnl":18,"unrealisedPnl":18,"unrealisedPnlPcnt":0.0011,"unrealisedRoePcnt":0.1128,"timestamp":"2019-05-10T11:25:35.046Z","lastPrice":6273.79,"lastValue":-15939,"currentQty":1,"liquidationPrice":66.5}]}'
'''
#order
'''
('{"table":"execution","action":"insert","data":[{"execID":"82952ee5-d25d-5b53-b0e6-9be1c45098e7","orderID":"788f34e5-d9d4-4db5-3701-e02da6a52637","clOrdID":"","clOrdLinkID":"","account":243795,"symbol":"XBTUSD","side":"Buy","lastQty":null,"lastPx":null,"underlyingLastPx":null,"lastMkt":"","lastLiquidityInd":"","simpleOrderQty":null,"orderQty":10000,"price":10714.5,"displayQty":null,"stopPx":null,"pegOffsetValue":null,"pegPriceType":"","currency":"USD","settlCurrency":"XBt","execType":"New","ordType":"Limit","timeInForce":"GoodTillCancel","execInst":"","contingencyType":"","exDestination":"XBME","ordStatus":"New","triggered":"","workingIndicator":true,"ordRejReason":"","simpleLeavesQty":null,"leavesQty":10000,"simpleCumQty":null,"cumQty":0,"avgPx":null,"commission":null,"tradePublishIndicator":"","multiLegReportingType":"SingleSecurity","text":"Submission '
 'from '
'''

#execution
'''
('{"table":"execution","action":"insert","data":[{"execID":"e104aace-9148-15bb-a754-31001e32a20d","orderID":"598b64bd-b5ef-e623-d58c-2c8466824c0a","clOrdID":"","clOrdLinkID":"","account":243795,"symbol":"XBTUSD","side":"Sell","lastQty":7598,"lastPx":10720.5,"underlyingLastPx":null,"lastMkt":"XBME","lastLiquidityInd":"AddedLiquidity","simpleOrderQty":null,"orderQty":10000,"price":10720.5,"displayQty":null,"stopPx":null,"pegOffsetValue":null,"pegPriceType":"","currency":"USD","settlCurrency":"XBt","execType":"Trade","ordType":"Limit","timeInForce":"GoodTillCancel","execInst":"","contingencyType":"","exDestination":"XBME","ordStatus":"Filled","triggered":"","workingIndicator":false,"ordRejReason":"","simpleLeavesQty":null,"leavesQty":0,"simpleCumQty":null,"cumQty":10000,"avgPx":10720.5,"commission":-0.00025,"tradePublishIndicator":"PublishTrade","multiLegReportingType":"SingleSecurity","text":"Submission '
 'from '
'''

if __name__ == '__main__':
    PrivateWSData.initialize()
    while True:
        #print(PrivateWSData.message)
        time.sleep(1)

    #rwa = PrivateWS()