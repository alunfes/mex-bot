from SystemFlg import SystemFlg
from datetime import datetime
from OneMinData import OneMinData
import time
import calendar, requests
import pandas as pd
import os
import threading


class DownloadMexOhlc:
    @classmethod
    def start_ohlc_download_thread(cls):
        cls.__initialize_ohlc()
        cls.lock_ohlc = threading.Lock()
        th = threading.Thread(target=cls.__onemin_data_download_thread)
        th.start()


    @classmethod
    def __initialize_ohlc(cls):
        cls.ohlc_ut = 0
        cls.ohlc_dt = ''
        cls.ohlc_open = 0
        cls.ohlc_high = 0
        cls.ohlc_low = 0
        cls.ohlc_close = 0
        cls.ohlc_volume = 0

    @classmethod
    def set_ohlc(cls, ut, dt, o, h, l, c, v):
        with cls.lock_ohlc:
            cls.ohlc_ut = ut
            cls.ohlc_dt = dt
            cls.ohlc_open = o
            cls.ohlc_high = h
            cls.ohlc_low = l
            cls.ohlc_close = c
            cls.ohlc_volume = v



    @classmethod
    def __onemin_data_download_thread(cls):
        while SystemFlg.get_system_flg():
            if datetime.now().second == 0:
                time.sleep(1)
                df = cls.download_latest_ohlc()
                if df is not None:
                    cls.set_ohlc(df[0], df[1], df[2], df[3], df[4], df[5], df[6])
                    print(cls.ohlc_dt, cls.ohlc_open, cls.ohlc_high, cls.ohlc_low, cls.ohlc_close, cls.ohlc_volume)
                else:
                    print('failed download ohlc in __onemin_data_download_thread !')
            time.sleep(0.1)


    #download data for initial calc
    @classmethod
    def initial_data_download(cls, max_term):
        print('downloading for initial bot data...')
        if os.path.exists('./Data/bot_ohlc.csv'):
            os.remove('./Data/bot_ohlc.csv')
        now = datetime.utcnow()
        unixtime = calendar.timegm(now.utctimetuple())
        to = unixtime
        since = to - (60 * max_term) - 1

        loop_flg = True
        df = pd.DataFrame()
        while loop_flg:
            tmp_to = since + 10080 * 60
            if tmp_to >= to: #check completion of download
                loop_flg = True
                tmp_to = to
            df = cls.download_data_since_to(since, tmp_to)
            since = since + 10080 * 60
            if loop_flg:
                df.to_csv('./Data/bot_ohlc.csv', index=False)
                break
        print('completed download')


    #download data for specific period and return processed df
    @classmethod
    def download_data_since_to(cls, since, to):
        unixtime = int(time.time())
        if to <= unixtime:
            #if to - since <= 10080 * 60:
            if to != 0:
                try:
                    param = {"period": 1, "from": since, "to": to}
                    url = "https://www.bitmex.com/api/udf/history?symbol=XBTUSD&resolution={period}&from={from}&to={to}".format(
                        **param)
                    res = requests.get(url)
                    #print(res)
                    data = res.json()
                    dt = []
                    for d in data['t']:
                        dt.append(datetime.fromtimestamp(int(d)))
                    df = pd.DataFrame({
                        "timestamp": data["t"],
                        "dt": dt,
                        "open": data["o"],
                        "high": data["h"],
                        "low": data["l"],
                        "close": data["c"],
                        "volume": data["v"],
                    }, columns=["timestamp", "dt", "open", "high", "low", "close", "volume"])
                    return df
                except:
                    print('error in download_data_since_to!')
                    import traceback
                    traceback.print_exc()
            else:
                print('to should be lower than since + 10080!')
        else:
            print('to should be lower than time.now()!')


    #for bot ohlc download when websocket tmp ohlc is not available
    @classmethod
    def download_latest_ohlc(cls):
        target_min = datetime.now().minute -1 if datetime.now().minute > 0 else 59
        df = None
        max_try = 10
        i = 0
        while df is None:
            df = DownloadMexOhlc.download_data_since_to(int(time.time()) - 180, int(time.time()) - 1)
            if df is not None:
                for i,dt in enumerate(df['dt']):
                    if int(str(dt).split(':')[1]) == target_min:
                        return (df['timestamp'].iloc[i], dt, df['open'].iloc[i], df['high'].iloc[i], df['low'].iloc[i], df['close'].iloc[i], df['volume'].iloc[i])
            time.sleep(1)
            i += 1
            if i >= max_try:
                print('download_latest_ohlc was failed!')
                return None


    @classmethod
    def bot_ohlc_download_latest(cls, max_term):
        to = int(time.time())
        since = to - (60 * max_term) - 60
        flg = True
        counter = 0
        while flg:
            df = cls.download_latest_ohlc()
            if df is not None:
                return df
            else:
                if counter > 10:
                    print('failed download ohlc in bot !')
                    return None
            time.sleep(1)



    @classmethod
    def download_data(cls):
        # 現在時刻のUTC naiveオブジェクト
        since = cls.__check_current_data_latest_ut()
        unixtime = int(time.time())
        flg = True
        if since == 0:
            # UTC naiveオブジェクト -> Unix time
            since = unixtime - 129600 * 60
            #since = unixtime - 30000 * 60
            flg = False

        loop_flg = True
        while loop_flg:
            to = since + 10080 * 60
            if to > unixtime:
                to = unixtime
                loop_flg = False
            param = {"period": 1, "from": since, "to": to}
            url = "https://www.bitmex.com/api/udf/history?symbol=XBTUSD&resolution={period}&from={from}&to={to}".format(**param)
            res = requests.get(url)
            data = res.json()
            since = to

            # レスポンスのjsonデータからOHLCVのDataFrameを作成
            dt = []
            for d in data['t']:
                dt.append(datetime.fromtimestamp(int(d)))
            df = pd.DataFrame({
                "timestamp": data["t"],
                "dt": dt,
                "open": data["o"],
                "high": data["h"],
                "low": data["l"],
                "close": data["c"],
                "volume": data["v"],
            }, columns=["timestamp", "dt", "open", "high", "low", "close", "volume"])
            if flg == False:
                df.to_csv('./Data/mex_data.csv', index=False)
                flg = True
            else:
                df.to_csv('./Data/mex_data.csv', mode='a', header=False, index=False)

    @classmethod
    def __check_current_data_latest_ut(cls):
        path = './Data/mex_data.csv'
        if os.path.exists(path):
            df = pd.read_csv(path)
            return df['timestamp'].iloc[-1]
        else:
            return 0



if __name__ == '__main__':
    #SystemFlg.initialize()
    #DownloadMexOhlc.initialize()
    DownloadMexOhlc.download_data()

