import websocket
import json
import time
import threading
from datetime import datetime
import dateutil
from OneMinMarketData import OneMinMarketData
import pytz
from SystemFlg import SystemFlg
import pprint
#from WSData import WSData
from LineNotification import LineNotification


class RealtimeWSAPI:
    def __init__(self):
        TickData.initialize()
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



    #tradeBin1m
    '''
    1m ohlcの取得が毎分15秒程度時差があるので分足を使うシステムでは使えない。
    {"table":"tradeBin1m","action":"insert","data":[{"timestamp":"2019-08-23T14:34:00.000Z","symbol":"XBTUSD","open":10394,"high":10394,"low":10388.5,"close":10388.5,"trades":413,"volume":1204198,"vwap":10390.6899,"lastSize":1000,"turnover":11589499007,"homeNotional":115.89499006999998,"foreignNotional":1204198}]}
    '''
    #trade
    '''
    {"info":"Welcome to the BitMEX Realtime API.","version":"2019-05-11T03:41:57.000Z","timestamp":"2019-05-12T08:34:24.778Z","docs":"https://www.bitmex.com/app/wsAPI","limit":{"remaining":39}}
    {"success":true,"subscribe":"trade:XBTUSD","request":{"op":"subscribe","args":["trade:XBTUSD"]}}
    {"table":"trade","action":"partial","keys":[],"types":{"timestamp":"timestamp","symbol":"symbol","side":"symbol","size":"long","price":"float","tickDirection":"symbol","trdMatchID":"guid","grossValue":"long","homeNotional":"float","foreignNotional":"float"},"foreignKeys":{"symbol":"instrument","side":"side"},"attributes":{"timestamp":"sorted","symbol":"grouped"},"filter":{"symbol":"XBTUSD"},"data":[{"timestamp":"2019-05-12T08:34:27.096Z","symbol":"XBTUSD","side":"Sell","size":4000,"price":7367,"tickDirection":"ZeroMinusTick","trdMatchID":"68b6d178-b37e-4fa0-09bc-8e749c5bac08","grossValue":54296000,"homeNotional":0.54296,"foreignNotional":4000}]}
    {"table":"trade","action":"insert","data":[{"timestamp":"2019-05-12T08:34:27.678Z","symbol":"XBTUSD","side":"Sell","size":213,"price":7367,"tickDirection":"ZeroMinusTick","trdMatchID":"dfbbcc82-5cdf-9d9d-5928-2d3f292f5e92","grossValue":2891262,"homeNotional":0.02891262,"foreignNotional":213}]}
    {"table":"trade","action":"insert","data":[{"timestamp":"2019-05-12T08:34:27.853Z","symbol":"XBTUSD","side":"Sell","size":41068,"price":7367,"tickDirection":"ZeroMinusTick","trdMatchID":"a9e0f35d-5c7d-f838-7492-b712ae9e32bd","grossValue":557457032,"homeNotional":5.57457032,"foreignNotional":41068},{"timestamp":"2019-05-12T08:34:27.853Z","symbol":"XBTUSD","side":"Sell","size":19,"price":7367,"tickDirection":"ZeroMinusTick","trdMatchID":"995210c4-65d1-49d5-3f24-8af933c7ea71","grossValue":257906,"homeNotional":0.00257906,"foreignNotional":19},{"timestamp":"2019-05-12T08:34:27.853Z","symbol":"XBTUSD","side":"Sell","size":51,"price":7367,"tickDirection":"ZeroMinusTick","trdMatchID":"e43bbee5-f645-305b-5331-49e8272f6189","grossValue":692274,"homeNotional":0.00692274,"foreignNotional":51},{"timestamp":"2019-05-12T08:34:27.853Z","symbol":"XBTUSD","side":"Sell","size":500,"price":7367,"tickDirection":"ZeroMinusTick","trdMatchID":"bc73d16b-b39f-3816-b9f9-cad9accb6200","grossValue":6787000,"homeNotional":0.06787,"foreignNotional":500},{"timestamp":"2019-05-12T08:34:27.853Z","symbol":"XBTUSD","side":"Sell","size":20,"price":7367,"tickDirection":"ZeroMinusTick","trdMatchID":"56f20dc3-d076-8c50-8f43-733752579b9b","grossValue":271480,"homeNotional":0.0027148,"foreignNotional":20},{"timestamp":"2019-05-12T08:34:27.853Z","symbol":"XBTUSD","side":"Sell","size":20,"price":7367,"tickDirection":"ZeroMinusTick","trdMatchID":"2ec8da21-5b3a-31da-6b55-312177032ea8","grossValue":271480,"homeNotional":0.0027148,"foreignNotional":20},{"timestamp":"2019-05-12T08:34:27.853Z","symbol":"XBTUSD","side":"Sell","size":31,"price":7367,"tickDirection":"ZeroMinusTick","trdMatchID":"a6b697ed-d378-cdc1-1aa6-1b534f2566b3","grossValue":420794,"homeNotional":0.00420794,"foreignNotional":31},{"timestamp":"2019-05-12T08:34:27.853Z","symbol":"XBTUSD","side":"Sell","size":1200,"price":7367,"tickDirection":"ZeroMinusTick","trdMatchID":"4f70b723-efbc-42fb-8883-3742647e4ba6","grossValue":16288800,"homeNotional":0.162888,"foreignNotional":1200},{"timestamp":"2019-05-12T08:34:27.853Z","symbol":"XBTUSD","side":"Sell","size":7091,"price":7367,"tickDirection":"ZeroMinusTick","trdMatchID":"60fb1d8a-b6f0-b353-ea41-54523dd7ab33","grossValue":96253234,"homeNotional":0.96253234,"foreignNotional":7091}]}
    {"table":"trade","action":"insert","data":[{"timestamp":"2019-05-12T08:34:28.813Z","symbol":"XBTUSD","side":"Buy","size":2000,"price":7367.5,"tickDirection":"PlusTick","trdMatchID":"79d79b98-9d99-e7d1-3e2a-d45d91515c32","grossValue":27146000,"homeNotional":0.27146,"foreignNotional":2000}]}
    '''
    # quote
    '''
    {"success":true,"subscribe":"quote:XBTUSD","request":{"op":"subscribe","args":["quote:XBTUSD"]}}
    {"table":"quote","action":"partial","keys":[],"types":{"timestamp":"timestamp","symbol":"symbol","bidSize":"long","bidPrice":"float","askPrice":"float","askSize":"long"},"foreignKeys":{"symbol":"instrument"},"attributes":{"timestamp":"sorted","symbol":"grouped"},"filter":{"symbol":"XBTUSD"},"data":[{"timestamp":"2019-05-09T07:30:33.944Z","symbol":"XBTUSD","bidSize":840761,"bidPrice":6063,"askPrice":6063.5,"askSize":769376}]}
    {"table":"quote","action":"insert","data":[{"timestamp":"2019-05-09T07:30:34.406Z","symbol":"XBTUSD","bidSize":840766,"bidPrice":6063,"askPrice":6063.5,"askSize":769376},{"timestamp":"2019-05-09T07:30:34.440Z","symbol":"XBTUSD","bidSize":840266,"bidPrice":6063,"askPrice":6063.5,"askSize":769376},{"timestamp":"2019-05-09T07:30:34.518Z","symbol":"XBTUSD","bidSize":848266,"bidPrice":6063,"askPrice":6063.5,"askSize":769376},{"timestamp":"2019-05-09T07:30:34.585Z","symbol":"XBTUSD","bidSize":848266,"bidPrice":6063,"askPrice":6063.5,"askSize":769416},{"timestamp":"2019-05-09T07:30:34.806Z","symbol":"XBTUSD","bidSize":848266,"bidPrice":6063,"askPrice":6063.5,"askSize":769417},{"timestamp":"2019-05-09T07:30:34.969Z","symbol":"XBTUSD","bidSize":848266,"bidPrice":6063,"askPrice":6063.5,"askSize":775417}]}
    {"table":"quote","action":"insert","data":[{"timestamp":"2019-05-09T07:30:35.228Z","symbol":"XBTUSD","bidSize":842266,"bidPrice":6063,"askPrice":6063.5,"askSize":775417},{"timestamp":"2019-05-09T07:30:35.440Z","symbol":"XBTUSD","bidSize":848266,"bidPrice":6063,"askPrice":6063.5,"askSize":775417},{"timestamp":"2019-05-09T07:30:35.523Z","symbol":"XBTUSD","bidSize":842266,"bidPrice":6063,"askPrice":6063.5,"askSize":775417},{"timestamp":"2019-05-09T07:30:35.544Z","symbol":"XBTUSD","bidSize":836266,"bidPrice":6063,"askPrice":6063.5,"askSize":775417},{"timestamp":"2019-05-09T07:30:35.577Z","symbol":"XBTUSD","bidSize":842266,"bidPrice":6063,"askPrice":6063.5,"askSize":775417},{"timestamp":"2019-05-09T07:30:35.582Z","symbol":"XBTUSD","bidSize":848266,"bidPrice":6063,"askPrice":6063.5,"askSize":775417},{"timestamp":"2019-05-09T07:30:35.752Z","symbol":"XBTUSD","bidSize":840266,"bidPrice":6063,"askPrice":6063.5,"askSize":775417},{"timestamp":"2019-05-09T07:30:35.927Z","symbol":"XBTUSD","bidSize":834266,"bidPrice":6063,"askPrice":6063.5,"askSize":775417},{"timestamp":"2019-05-09T07:30:35.928Z","symbol":"XBTUSD","bidSize":828266,"bidPrice":6063,"askPrice":6063.5,"askSize":775417},{"timestamp":"2019-05-09T07:30:35.935Z","symbol":"XBTUSD","bidSize":822266,"bidPrice":6063,"askPrice":6063.5,"askSize":775417},{"timestamp":"2019-05-09T07:30:35.944Z","symbol":"XBTUSD","bidSize":828266,"bidPrice":6063,"askPrice":6063.5,"askSize":775417},{"timestamp":"2019-05-09T07:30:35.948Z","symbol":"XBTUSD","bidSize":834266,"bidPrice":6063,"askPrice":6063.5,"askSize":775417},{"timestamp":"2019-05-09T07:30:35.953Z","symbol":"XBTUSD","bidSize":829266,"bidPrice":6063,"askPrice":6063.5,"askSize":775417},{"timestamp":"2019-05-09T07:30:35.955Z","symbol":"XBTUSD","bidSize":823266,"bidPrice":6063,"askPrice":6063.5,"askSize":775417},{"timestamp":"2019-05-09T07:30:35.956Z","symbol":"XBTUSD","bidSize":829266,"bidPrice":6063,"askPrice":6063.5,"askSize":775417},{"timestamp":"2019-05-09T07:30:35.968Z","symbol":"XBTUSD","bidSize":834266,"bidPrice":6063,"askPrice":6063.5,"askSize":775417},{"timestamp":"2019-05-09T07:30:35.991Z","symbol":"XBTUSD","bidSize":828266,"bidPrice":6063,"askPrice":6063.5,"askSize":775417},{"timestamp":"2019-05-09T07:30:36.005Z","symbol":"XBTUSD","bidSize":834266,"bidPrice":6063,"askPrice":6063.5,"askSize":775417}]}
    {"table":"quote","action":"insert","data":[{"timestamp":"2019-05-09T07:30:36.119Z","symbol":"XBTUSD","bidSize":840266,"bidPrice":6063,"askPrice":6063.5,"askSize":775417},{"timestamp":"2019-05-09T07:30:36.295Z","symbol":"XBTUSD","bidSize":840269,"bidPrice":6063,"askPrice":6063.5,"askSize":775417},{"timestamp":"2019-05-09T07:30:36.614Z","symbol":"XBTUSD","bidSize":840269,"bidPrice":6063,"askPrice":6063.5,"askSize":781417}]}
    '''
    #orderBook10
    '''
    [{'symbol': 'XBTUSD', 'bids': [[7031.5, 817994], [7031, 111648], [7030.5, 315645], [7030, 45546], [7029.5, 121735], [7029, 161285], [7028.5, 26876], [7028, 137289], [7027.5, 297982], [7027, 221844]], 'timestamp': '2019-12-15T01:23:07.533Z', 'asks': [[7032, 1679058], [7032.5, 109328], [7033, 152753], [7033.5, 835278], [7034, 76609], [7034.5, 5819], [7035, 273119], [7035.5, 485332], [7036, 280810], [7036.5, 161626]]}]
    [{'symbol': 'XBTUSD', 'bids': [[7031.5, 817994], [7031, 111648], [7030.5, 315645], [7030, 45546], [7029.5, 121735], [7029, 171285], [7028.5, 26876], [7028, 137289], [7027.5, 297982], [7027, 221844]], 'timestamp': '2019-12-15T01:23:07.568Z', 'asks': [[7032, 1679058], [7032.5, 109328], [7033, 152753], [7033.5, 835278], [7034, 76609], [7034.5, 5819], [7035, 273119], [7035.5, 485332], [7036, 280810], [7036.5, 161626]]}]
    [{'symbol': 'XBTUSD', 'bids': [[7031.5, 787994], [7031, 111648], [7030.5, 315645], [7030, 45546], [7029.5, 121735], [7029, 171285], [7028.5, 26876], [7028, 137289], [7027.5, 297982], [7027, 221844]], 'timestamp': '2019-12-15T01:23:07.917Z', 'asks': [[7032, 1679058], [7032.5, 109328], [7033, 152753], [7033.5, 835278], [7034, 76609], [7034.5, 5819], [7035, 273119], [7035.5, 485332], [7036, 280810], [7036.5, 161626]]}]
    [{'symbol': 'XBTUSD', 'asks': [[7032, 1687058], [7032.5, 109328], [7033, 152753], [7033.5, 835278], [7034, 76609], [7034.5, 5819], [7035, 273119], [7035.5, 485332], [7036, 280810], [7036.5, 161626]], 'timestamp': '2019-12-15T01:23:07.932Z', 'bids': [[7031.5, 787994], [7031, 111648], [7030.5, 315645], [7030, 45546], [7029.5, 121735], [7029, 171285], [7028.5, 26876], [7028, 137289], [7027.5, 297982], [7027, 221844]]}]
    [{'symbol': 'XBTUSD', 'asks': [[7032, 1687058], [7032.5, 109328], [7033, 152753], [7033.5, 835278], [7034, 76609], [7034.5, 5819], [7035, 273119], [7035.5, 495332], [7036, 270810], [7036.5, 161626]], 'timestamp': '2019-12-15T01:23:08.056Z', 'bids': [[7031.5, 787994], [7031, 111648], [7030.5, 315645], [7030, 45546], [7029.5, 121735], [7029, 171285], [7028.5, 26876], [7028, 137289], [7027.5, 297982], [7027, 221844]]}]
    [{'symbol': 'XBTUSD', 'asks': [[7032, 1686058], [7032.5, 109328], [7033, 152753], [7033.5, 835278], [7034, 76609], [7034.5, 5819], [7035, 273119], [7035.5, 495332], [7036, 270810], [7036.5, 161626]], 'timestamp': '2019-12-15T01:23:08.062Z', 'bids': [[7031.5, 787994], [7031, 111648], [7030.5, 315645], [7030, 45546], [7029.5, 121735], [7029, 171285], [7028.5, 26876], [7028, 137289], [7027.5, 297982], [7027, 221844]]}]
    [{'symbol': 'XBTUSD', 'bids': [[7031.5, 787309], [7031, 111648], [7030.5, 315645], [7030, 45546], [7029.5, 121735], [7029, 171285], [7028.5, 26876], [7028, 137289], [7027.5, 297982], [7027, 221844]], 'timestamp': '2019-12-15T01:23:08.096Z', 'asks': [[7032, 1686058], [7032.5, 109328], [7033, 152753], [7033.5, 835278], [7034, 76609], [7034.5, 5819], [7035, 273119], [7035.5, 495332], [7036, 270810], [7036.5, 161626]]}]
    [{'symbol': 'XBTUSD', 'asks': [[7032, 1688558], [7032.5, 109328], [7033, 152753], [7033.5, 835278], [7034, 76609], [7034.5, 5819], [7035, 273119], [7035.5, 495332], [7036, 270810], [7036.5, 161626]], 'timestamp': '2019-12-15T01:23:08.110Z', 'bids': [[7031.5, 787309], [7031, 111648], [7030.5, 315645], [7030, 45546], [7029.5, 121735], [7029, 171285], [7028.5, 26876], [7028, 137289], [7027.5, 297982], [7027, 221844]]}]
    [{'symbol': 'XBTUSD', 'asks': [[7032, 1686058], [7032.5, 109328], [7033, 152753], [7033.5, 835278], [7034, 76609], [7034.5, 5819], [7035, 273119], [7035.5, 495332], [7036, 270810], [7036.5, 161626]], 'timestamp': '2019-12-15T01:23:08.132Z', 'bids': [[7031.5, 787309], [7031, 111648], [7030.5, 315645], [7030, 45546], [7029.5, 121735], [7029, 171285], [7028.5, 26876], [7028, 137289], [7027.5, 297982], [7027, 221844]]}]
    '''
    def on_open(self, ws):
        print('opened bitmex public ws.')
        channels = {
            'op': 'subscribe',
            'args': [
                #'tradeBin1m:XBTUSD',
                'trade:XBTUSD',
                'quote:XBTUSD',
                'orderBook10:XBTUSD',
            ]
        }
        ws.send(json.dumps(channels))

    def on_message(self, ws, message):
        #message = dict(message)
        s = time.time()
        message = json.loads(message)
        if message['table'] == 'tradeBin1m':
            d = message['data'][-1]
            dt = datetime.dateutil.parser.parse(d['timestamp'])
            sdt = dt.strftime('%Y-%m-%d %H:%M:%S')
            ut = dt.strftime('%s')
            #print(sdt, d['open'], d['high'], d['low'], d['close'], datetime.now())
            #OneMinMarketData.add_tmp_ohlc(ut, sdt, d['open'], d['high'], d['low'], d['close'], d['volume'])
        elif message['table'] == 'trade':
            TickData.set_ltp(message['data'][-1]['price'])
            TickData.add_tmp_exec_data(message['data'])
        elif message['table'] == 'quote':
            pass
            #TickData.set_bid(message['data'][-1]['bidPrice'])
            #TickData.set_ask(message['data'][-1]['askPrice'])
        elif message['table'] == 'orderBook10':
            TickData.set_bid(message[0]['bids'][0][0])
            TickData.set_ask(message[0]['asks'][0][0])
        else:
            print('unknown message in RealtimeWSAPI!')
        #print('wsapi time=',time.time() - s)


    def on_close(self, ws):
        LineNotification.send_error('closed public ws')
        print('closed public ws')

    def on_error(self, ws, error):
        LineNotification.send_error('Error occurred in public webscoket! restart the ws thread.')
        LineNotification.send_error(str(error))
        print('Error occurred in public webscoket! restart the ws thread.', error)
        self.__init__()


class TickData:
    @classmethod
    def initialize(cls):
        cls.lock_data = threading.Lock()
        cls.lock_tmp_data = threading.Lock()
        cls.exec_data = []
        cls.tmp_exec_data = []
        cls.ltp = 0
        cls.bidprice = 0
        cls.askprice = 0
        cls.JST = pytz.timezone('Asia/Tokyo')
        #cls.last_ohlc_min = int(datetime.now(cls.JST).minute)+1 if datetime.now(cls.JST).minute != 59 else 0
        cls.last_ohlc_min = int(datetime.now(cls.JST).minute)
        th = threading.Thread(target=cls.__calc_ohlc_thread)
        th.start()

    @classmethod
    def set_bid(cls, p):
        with cls.lock_data:
            cls.bidprice = p

    @classmethod
    def get_bid(cls):
        return cls.bidprice

    @classmethod
    def set_ask(cls, p):
        with cls.lock_data:
            cls.askprice = p

    @classmethod
    def get_ask(cls):
        return cls.askprice

    @classmethod
    def set_ltp(cls, p):
        with cls.lock_data:
            cls.ltp = p

    @classmethod
    def get_ltp(cls):
        return cls.ltp

    @classmethod
    def add_exec_data(cls, exec):
        if len(exec) > 0:
            with cls.lock_data:
                cls.exec_data.extend(exec)
                if len(cls.exec_data) >= 30000:
                    del cls.exec_data[:-10000]

    @classmethod
    def add_tmp_exec_data(cls, exec):
        if len(exec) > 0:
            with cls.lock_tmp_data:
                cls.tmp_exec_data.extend(exec)

    @classmethod
    def get_tmp_exec_data(cls):
        with cls.lock_tmp_data:
            res = cls.tmp_exec_data[:]
            cls.tmp_exec_data = []
            return res

    @classmethod
    def get_exe_data(cls):
        return cls.exec_data[:]


    @classmethod
    def __calc_ohlc_thread(cls):
        target_min = -1
        next_min = -1
        while SystemFlg.get_system_flg():#計算開始の基準minuteを決定
            data = cls.get_tmp_exec_data()
            if len(data) > 0:
                target_min = int(data[-1]['timestamp'].split('T')[1].split(':')[1]) #計算開始の基準minuteを決定
                target_min = target_min +1 if target_min +1 < 60 else 0
                next_min = target_min +1 if target_min +1 < 60 else 0
                break
            time.sleep(0.1)

        while SystemFlg.get_system_flg():
            data = cls.get_tmp_exec_data()
            if len(data) > 0 and int(data[-1]['timestamp'].split('T')[1].split(':')[1]) == next_min or (datetime.now().minute == next_min and datetime.now().second > 2): #次の分のデータが入り出したらohlc計算する
                next_data = []
                target_data = []
                for d in data:
                    minut = int(d['timestamp'].split('T')[1].split(':')[1])
                    #if (next_min != 0 and minut >= next_min) or (next_min == 0 and minut >= 0):
                    if minut == next_min:
                        next_data.append(d) #次回の分のデータは次に回す
                    elif minut == target_min:
                        target_data.append(d)
                if len(next_data) > 0:
                    cls.add_tmp_exec_data(next_data)
                if len(target_data) == 0:
                    print('RealtimeWSAPI: target data len is 0 !')
                    LineNotification.send_error('RealtimeWSAPI: target data len is 0 !')
                    #reset target min
                    target_min = int(data[-1]['timestamp'].split('T')[1].split(':')[1])
                    target_min = target_min + 1 if target_min + 1 < 60 else 0
                    next_min = target_min + 1 if target_min + 1 < 60 else 0
                else:
                    p = [d.get('price') for d in target_data]
                    size = [d.get('size') for d in target_data]
                    dt = dateutil.parser.parse(target_data[-1]['timestamp'])
                    OneMinMarketData.add_tmp_ohlc(dt.timestamp(), dt, p[0], max(p), min(p), p[-1], sum(size))
                    #print(datetime.now())
                    #print('RealtimeWSAPI: ', dt.timestamp(), p[0], max(p), min(p), p[-1], sum(size))
                target_min = target_min + 1 if target_min + 1 < 60 else 0
                next_min = target_min + 1 if target_min + 1 < 60 else 0
            else:
                cls.add_tmp_exec_data(data)
            time.sleep(1)


if __name__ == '__main__':
    SystemFlg.initialize()
    rwa = RealtimeWSAPI()
    #OneMinMarketData.initialize_for_bot()
    while True:
        time.sleep(1)