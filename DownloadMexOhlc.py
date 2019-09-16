from datetime import datetime
import calendar, requests
import pandas as pd
import os

class DownloadMexOhlc:
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
                df.to_csv('./Data/mex_data.csv', index=False)
                break
        print('completed download')


    #download data for specific period and return processed df
    @classmethod
    def download_data_since_to(cls, since, to):
        now = datetime.utcnow()
        unixtime = calendar.timegm(now.utctimetuple())
        if to <= unixtime:
            if to - since <= 10080:
                try:
                    param = {"period": 1, "from": since, "to": to}
                    url = "https://www.bitmex.com/api/udf/history?symbol=XBTUSD&resolution={period}&from={from}&to={to}".format(
                        **param)
                    res = requests.get(url)
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



    @classmethod
    def download_data(cls):
        # 現在時刻のUTC naiveオブジェクト
        now = datetime.utcnow()

        since = cls.__check_current_data_latest_ut()
        unixtime = calendar.timegm(now.utctimetuple())
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
    DownloadMexOhlc.download_data()