import websocket
import json
import time
import threading
from datetime import datetime
from OneMinMarketData import OneMinMarketData
import pytz
from SystemFlg import SystemFlg
import pprint
#from WSData import WSData



'''

'''

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
    def on_open(self, ws):
        print('opened bitmex public ws.')
        channels = {
            'op': 'subscribe',
            'args': [
                #'tradeBin1m:XBTUSD',
                'trade:XBTUSD',
                'quote:XBTUSD',
            ]
        }
        ws.send(json.dumps(channels))

    def on_message(self, ws, message):
        #message = dict(message)
        message = json.loads(message)
        if message['table'] == 'tradeBin1m':
            d = message['data'][-1]
            dt = datetime.dateutil.parser.parse(d['timestamp'])
            sdt = dt.strftime('%Y-%m-%d %H:%M:%S')
            ut = dt.strftime('%s')
            print(sdt, d['open'], d['high'], d['low'], d['close'], datetime.now())
            #OneMinMarketData.add_tmp_ohlc(ut, sdt, d['open'], d['high'], d['low'], d['close'], d['volume'])
        elif message['table'] == 'trade':
            TickData.set_ltp(message['data'][-1]['price'])
            TickData.add_tmp_exec_data(message['data'])
        elif message['table'] == 'quote':
            TickData.set_bid(message['data'][-1]['bidPrice'])
            TickData.set_ask(message['data'][-1]['askPrice'])
        else:
            print('unknown message')


    def on_close(self, ws):
        print('closed public ws')

    def on_error(self, ws, error):
        print(error)
        print('Error occurred in public webscoket! restart the ws thread.')
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
        with cls.lock_data:
            return cls.bidprice

    @classmethod
    def set_ask(cls, p):
        with cls.lock_data:
            cls.askprice = p

    @classmethod
    def get_ask(cls):
        with cls.lock_data:
            return cls.askprice

    @classmethod
    def set_ltp(cls, p):
        with cls.lock_data:
            cls.ltp = p

    @classmethod
    def get_ltp(cls):
        with cls.lock_data:
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

    '''
    00:00:10 started, last_min = 00:01
    00:00:10 no action as not enough data
    00:01:00 no action as not enough data
    00:02:00 calc data for 00:01, last_min = 00:02
    00:02:20 no action as not enough data, last_min = 00:02
    
    1. ohlc threadを開始、00秒からohlc計算を開始
    2. tmp_exec_dataからデータを取得して、target_minと一致するデータを対象にohlc計算
    3. 59.9 - 00.01あたりの時間でohlcをOneMinMarketDataに入れる。
    4. ohlcの再計算開始
    dataに対象の分以外のデータが入っていることがありうる。次の分のデータがある場合は、使わずにtmp_exec_dataに追加、前の分は捨てる。
    
    '''
    @classmethod
    def __calc_ohlc_thread(cls):
        while SystemFlg.get_system_flg():
            if datetime.now(cls.JST).second == 0: #00秒からohlc計算を開始
                cls.target_ohlc_min = datetime.now(cls.JST).minute #set target minutes
                while SystemFlg.get_system_flg():
                    flg = False
                    open = 0
                    high = 0
                    low = 9999999
                    close = 0
                    volume = 0
                    next_min = cls.target_ohlc_min+1 if cls.target_ohlc_min !=59 else 0
                    dt = datetime.now(cls.JST)
                    ut =dt.timestamp()
                    loop_flg = True
                    while loop_flg:
                        data = cls.get_tmp_exec_data()
                        #dataに対象の分以外のデータが入っていることがありうる。次の分のデータがある場合は、使わずにtmp_exec_dataに追加、前の分は捨てる。
                        target = []
                        next_target = []
                        for d in data:
                            minut = int(d['timestamp'].split('T')[1].split(':')[1])
                            if minut == cls.target_ohlc_min:
                                target.append(d)
                            #elif minut == next_min:
                            #    next_target.append(d)
                        cls.add_tmp_exec_data(next_target)
                        if len(target) > 0:
                            p = [d.get('price') for d in target]
                            size = [d.get('size') for d in target]
                            if open == 0:
                                opendt = [d.get('timestamp') for d in target]
                                condt = list(map(lambda x: float(x.split(':')[2][:-1]), opendt))
                                open = p[condt.index(min(condt))]
                            m = max(p)
                            lw = min(p)
                            high = m if m > high else high
                            low = lw if lw < low else low
                            volume += sum(size)
                        #次の00秒でohlcを確定させる
                        if flg == False and datetime.now(cls.JST).second > 5:
                            flg = True
                        if flg and datetime.now(cls.JST).second <= 4:
                            close = p[-1]
                            #print(datetime.now(cls.JST), dt, open, high, low, close, volume)
                            print('ws add ohlc')
                            if open ==0 or open > 99999:
                                print('invalid val was detected in realtime ohlc!')
                            if dt.minute == 0:
                                print('ws dt=', dt)
                            OneMinMarketData.add_tmp_ohlc(ut,dt,open,high,low,close,volume)
                            cls.target_ohlc_min = next_min
                            loop_flg = False
                            break
                        time.sleep(0.1)
                    time.sleep(0.1)





    @classmethod
    def __calc_ohlc(cls):
        if int(datetime.now(cls.JST).minute) > cls.last_ohlc_min or (int(cls.last_ohlc_min) == 59 and int(datetime.now(cls.JST).minute) == 0):
            executions = cls.get_exe_data()
            dlist = [d.get('timestamp') for d in executions]
            p = [d.get('price') for d in executions]
            size = [d.get('size') for d in executions]
            i = 1
            target_min = int(datetime.now(cls.JST).minute - 1 if datetime.now(cls.JST).minute > 0 else 59)
            plist = []
            sizelist = []
            while int(dlist[-i].split('T')[1].split(':')[1]) != target_min:
                i += 1
            while int(dlist[-i].split('T')[1].split(':')[1]) == target_min:
                plist.append(p[-i])
                sizelist.append(size[-i])
                i += 1
            zurashi_time = target_min + 1 if target_min != 59 else 0  # to consist with cryptowatch data
            cls.ohlc.dt.append(
                datetime(datetime.now(cls.JST).year, datetime.now(cls.JST).month, datetime.now(cls.JST).day,
                         datetime.now(cls.JST).hour, zurashi_time, 0))

            ut = cls.ohlc.dt[-1].timestamp()
            dt = datetime.fromtimestamp(int(ut))
            open = (plist[-1])
            high = max(plist)
            low = min(plist)
            close = plist[0]
            vol = sum(sizelist)
            #OneMinMarketData.add_tmp_ohlc(ut, dt, open, high, low, close, vol)
            print('genrated ohlc:', dt, open, high, low, close, datetime.now())
            cls.last_ohlc_min = datetime.now(cls.JST).minute


if __name__ == '__main__':
    SystemFlg.initialize()
    rwa = RealtimeWSAPI()
    while True:
        time.sleep(1)