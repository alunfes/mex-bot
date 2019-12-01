import websocket
import threading
import json
import urllib
import hmac
import hashlib
import time
from collections import deque
from Trade import Trade


class PrivateWS:
    def __init__(self):
        PrivateWSData.initialize()
        # サーバとのデータのやりとりを表示するため、Trueを指定する。
        websocket.enableTrace(False)
        # 接続先URLと各コールバック関数を引数に指定して、WebSocketAppのインスタンスを作成
        self.ws_pub = websocket.WebSocketApp(url='wss://www.bitmex.com/realtime',
                                    on_open=self.on_open,
                                    on_message=self.on_message,
                                    on_close=self.on_close,
                                    on_error=self.on_error)
        self.thread = threading.Thread(target=lambda: self.ws_pub.run_forever())
        self.thread.daemon = True
        self.thread.start()


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
        message = json.loads(message)
        #pprint.pprint(message)
        if message['table'] == 'execution':
            d = message['data']
            PrivateWSData.add_exec_data(d)
        elif message['table'] == 'order':
            d = message['data']
            PrivateWSData.add_order_data(d)
        elif message['table'] == 'position':
            d = message['data']
            PrivateWSData.add_order_data(d)



    def on_close(self, ws):
        print('closed private PrivateWS')
        self.__init__()

    def on_error(self, ws, error):
        print('PrivateWS error!')
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
{'table': 'order', 'action': 'insert', 'data': [{'orderID': '0315ec82-5c97-5a9e-857a-c4dc22d1b725', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Buy', 'simpleOrderQty': None, 'orderQty': 100000, 'price': 10310.5, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'New', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 100000, 'simpleCumQty': None, 'cumQty': 0, 'avgPx': None, 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from www.bitmex.com', 'transactTime': '2019-08-26T13:15:37.800Z', 'timestamp': '2019-08-26T13:15:37.800Z'}]}
{'table': 'order', 'action': 'update', 'data': [{'orderID': '0315ec82-5c97-5a9e-857a-c4dc22d1b725', 'workingIndicator': True, 'clOrdID': '', 'account': 243795, 'symbol': 'XBTUSD', 'timestamp': '2019-08-26T13:15:37.800Z'}]}
{'table': 'order', 'action': 'update', 'data': [{'orderID': '0315ec82-5c97-5a9e-857a-c4dc22d1b725', 'ordStatus': 'Filled', 'workingIndicator': False, 'leavesQty': 0,'cumQty': 100000, 'avgPx': 10310.5, 'timestamp': '2019-08-26T13:16:01.495Z', 'clOrdID': '', 'account': 243795, 'symbol': 'XBTUSD'}]}
 {'table': 'order', 'action': 'insert', 'data': [{'orderID': 'b9193d01-35e5-3f14-a025-8abef4c005d2', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Sell', 'simpleOrderQty': None, 'orderQty': 100000, 'price': 10330.5, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'New', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 100000, 'simpleCumQty': None, 'cumQty': 0, 'avgPx': None, 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from www.bitmex.com', 'transactTime': '2019-08-26T13:16:49.182Z', 'timestamp': '2019-08-26T13:16:49.182Z'}]}
 {'table': 'order', 'action': 'update', 'data': [{'orderID': 'b9193d01-35e5-3f14-a025-8abef4c005d2', 'workingIndicator': True, 'clOrdID': '', 'account': 243795, 'symbol': 'XBTUSD', 'timestamp': '2019-08-26T13:16:49.182Z'}]}
 {'table': 'order', 'action': 'update', 'data': [{'orderID': 'b9193d01-35e5-3f14-a025-8abef4c005d2', 'ordStatus': 'PartiallyFilled', 'leavesQty': 92246, 'cumQty': 7754, 'avgPx': 10330.5, 'timestamp': '2019-08-26T13:19:52.162Z', 'clOrdID': '', 'account': 243795, 'symbol': 'XBTUSD'}]}
 {'table': 'order', 'action': 'update', 'data': [{'orderID': 'b9193d01-35e5-3f14-a025-8abef4c005d2', 'leavesQty': 91746, 'cumQty': 8254, 'timestamp': '2019-08-26T13:19:52.172Z', 'clOrdID': '', 'account': 243795, 'symbol': 'XBTUSD'}]}
 [{'orderID': '1d5d977d-261e-42d9-73e9-ea82376e88cc', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Buy', 'simpleOrderQty': None, 'orderQty': 1000, 'price': None, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'ordType': 'Market', 'timeInForce': 'ImmediateOrCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'New', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 1000, 'simpleCumQty': None, 'cumQty': 0, 'avgPx': None, 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from www.bitmex.com', 'transactTime': '2019-11-30T12:48:20.912Z', 'timestamp': '2019-11-30T12:48:20.912Z'}]
[{'orderID': '1d5d977d-261e-42d9-73e9-ea82376e88cc', 'price': 7703, 'workingIndicator': True, 'clOrdID': '', 'account': 243795, 'symbol': 'XBTUSD', 'timestamp': '2019-11-30T12:48:20.912Z'}]
[{'orderID': '1d5d977d-261e-42d9-73e9-ea82376e88cc', 'ordStatus': 'Filled', 'workingIndicator': False, 'leavesQty': 0, 'cumQty': 1000, 'avgPx': 7703, 'clOrdID': '', 'account': 243795, 'symbol': 'XBTUSD', 'timestamp': '2019-11-30T12:48:20.912Z'}]
'''

#execution
'''
{'table': 'execution', 'action': 'insert', 'data': [{'execID': 'dce57cf2-373c-0361-521a-04032ab65eb3', 'orderID': '0315ec82-5c97-5a9e-857a-c4dc22d1b725', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Buy', 'lastQty': None, 'lastPx': None, 'underlyingLastPx': None, 'lastMkt': '', 'lastLiquidityInd': '', 'simpleOrderQty': None, 'orderQty': 100000, 'price': 10310.5, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'execType': 'New', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'New', 'triggered': '', 'workingIndicator': True, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 100000, 'simpleCumQty': None, 'cumQty': 0, 'avgPx': None, 'commission': None, 'tradePublishIndicator': '', 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from www.bitmex.com', 'trdMatchID': '00000000-0000-0000-0000-000000000000', 'execCost': None, 'execComm': None, 'homeNotional': None, 'foreignNotional': None, 'transactTime': '2019-08-26T13:15:37.800Z', 'timestamp': '2019-08-26T13:15:37.800Z'}]}
{'table': 'execution', 'action': 'insert', 'data': [{'execID': 'b57cbd25-0bae-b9dd-b087-2a16cdb64d34', 'orderID': '0315ec82-5c97-5a9e-857a-c4dc22d1b725', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Buy', 'lastQty': 100000, 'lastPx': 10310.5, 'underlyingLastPx': None, 'lastMkt': 'XBME', 'lastLiquidityInd': 'AddedLiquidity', 'simpleOrderQty': None, 'orderQty': 100000, 'price': 10310.5, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'execType': 'Trade', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'Filled', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 0, 'simpleCumQty': None, 'cumQty': 100000, 'avgPx': 10310.5, 'commission': -0.00025, 'tradePublishIndicator': 'PublishTrade', 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from www.bitmex.com', 'trdMatchID': '6d5b58f0-6f92-7778-cc35-63e0f8bf8ffc', 'execCost': -969900000, 'execComm': -242475, 'homeNotional': 9.699, 'foreignNotional': -100000, 'transactTime': '2019-08-26T13:16:01.495Z', 'timestamp': '2019-08-26T13:16:01.495Z'}]}
{'table': 'execution', 'action': 'insert', 'data': [{'execID': 'ef28f5e6-3c4f-42cd-fe35-5ad22369b35a', 'orderID': 'b9193d01-35e5-3f14-a025-8abef4c005d2', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Sell', 'lastQty': None, 'lastPx': None, 'underlyingLastPx': None, 'lastMkt': '', 'lastLiquidityInd': '', 'simpleOrderQty': None, 'orderQty': 100000, 'price': 10330.5, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'execType': 'New', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'New', 'triggered': '', 'workingIndicator': True, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 100000, 'simpleCumQty': None, 'cumQty': 0, 'avgPx': None, 'commission': None, 'tradePublishIndicator': '', 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from www.bitmex.com', 'trdMatchID': '00000000-0000-0000-0000-000000000000', 'execCost': None, 'execComm': None, 'homeNotional': None, 'foreignNotional': None, 'transactTime': '2019-08-26T13:16:49.182Z', 'timestamp': '2019-08-26T13:16:49.182Z'}]}
{'table': 'execution', 'action': 'insert', 'data': [{'execID': '66bc1ab7-f700-56bd-ef0a-8f6ff4c4759c', 'orderID': 'b9193d01-35e5-3f14-a025-8abef4c005d2', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Sell', 'lastQty': 500, 'lastPx': 10330.5, 'underlyingLastPx': None, 'lastMkt': 'XBME', 'lastLiquidityInd': 'AddedLiquidity', 'simpleOrderQty': None, 'orderQty': 100000, 'price': 10330.5, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'execType': 'Trade', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'PartiallyFilled', 'triggered': '', 'workingIndicator': True, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 91746, 'simpleCumQty': None, 'cumQty': 8254, 'avgPx': 10330.5, 'commission': -0.00025, 'tradePublishIndicator': 'PublishTrade', 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from www.bitmex.com', 'trdMatchID': '051e3631-b7d0-c4a8-6e4b-2694b3dfc982', 'execCost': 4840000, 'execComm': -1210, 'homeNotional': -0.0484, 'foreignNotional': 500, 'transactTime': '2019-08-26T13:19:52.172Z', 'timestamp': '2019-08-26T13:19:52.172Z'}]}
{'table': 'execution', 'action': 'insert', 'data': [{'execID': '9027d184-42fd-ab23-7d3b-0f1c9f0a4606', 'orderID': 'b9193d01-35e5-3f14-a025-8abef4c005d2', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Sell', 'lastQty': 3500, 'lastPx': 10330.5, 'underlyingLastPx': None, 'lastMkt': 'XBME', 'lastLiquidityInd': 'AddedLiquidity', 'simpleOrderQty': None, 'orderQty': 100000, 'price': 10330.5, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'execType': 'Trade', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'PartiallyFilled', 'triggered': '', 'workingIndicator': True, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 88246, 'simpleCumQty': None, 'cumQty': 11754, 'avgPx': 10330.5, 'commission': -0.00025, 'tradePublishIndicator': 'PublishTrade', 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from www.bitmex.com', 'trdMatchID': '3a918fad-9653-6ac1-c34a-6156e5c5e46a', 'execCost': 33880000, 'execComm': -8470, 'homeNotional': -0.3388, 'foreignNotional': 3500, 'transactTime': '2019-08-26T13:19:52.181Z', 'timestamp': '2019-08-26T13:19:52.181Z'}]}
{'table': 'execution', 'action': 'insert', 'data': [{'execID': '6f88732c-4f32-0034-2978-136da1d0208a', 'orderID': 'b9193d01-35e5-3f14-a025-8abef4c005d2', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Sell', 'lastQty': 88246, 'lastPx': 10330.5, 'underlyingLastPx': None, 'lastMkt': 'XBME', 'lastLiquidityInd': 'AddedLiquidity', 'simpleOrderQty': None, 'orderQty': 100000, 'price': 10330.5, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'execType': 'Trade', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'Filled', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 0, 'simpleCumQty': None, 'cumQty': 100000, 'avgPx': 10330.5, 'commission': -0.00025, 'tradePublishIndicator': 'PublishTrade', 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from www.bitmex.com', 'trdMatchID': '03fe30ea-e658-b79d-a4f1-2a24aa7332ce', 'execCost': 854221280, 'execComm': -213555, 'homeNotional': -8.5422128, 'foreignNotional': 88246, 'transactTime': '2019-08-26T13:19:52.259Z', 'timestamp': '2019-08-26T13:19:52.259Z'}]}
'''



class PrivateWSData:
    @classmethod
    def initialize(cls):
        cls.lock_exec_data = threading.Lock()
        cls.lock_order_data = threading.Lock()
        cls.order_data = {}
        cls.exec_data = []
        cls.position_data = {}


    @classmethod
    def add_exec_data(cls, data):
        with cls.lock_exec_data:
            if len(data) > 0:
                cls.exec_data.append(data[0])

    @classmethod
    def get_exec_data(cls):
        with cls.lock_exec_data:
            res = cls.exec_data[:]
            cls.exec_data = []
            return res


    @classmethod
    def get_all_order_data(cls):
        with cls.lock_order_data:
            return cls.order_data

    @classmethod
    def get_order_data(cls, order_id):
        with cls.lock_order_data:
            return cls.order_data[order_id]

    @classmethod
    def add_order_data(cls, data):
        with cls.lock_order_data:
            if len(data) > 0 and 'lastQty' in data[0].keys():
                print('add_order_data:', data[0])
                cls.order_data[data[0]['orderID']] = data[0]

    @classmethod
    def remove_order_data(cls, order_id):
        with cls.lock_order_data:
            cls.order_data.pop(order_id)


if __name__ == '__main__':
    pws = PrivateWS()
    while True:
        #print(PrivateWSData.message)
        time.sleep(1)

    #rwa = PrivateWS()