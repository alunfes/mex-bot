from datetime import datetime
import calendar, requests
import pandas as pd
import os

class DownloadMexOhlc:
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
            for
            df = pd.DataFrame({
                "timestamp": data["t"],
                "dt": datetime.fromtimestamp(int(data["t"])),
                "open": data["o"],
                "high": data["h"],
                "low": data["l"],
                "close": data["c"],
                "volume": data["v"],
            }, columns=["timestamp", "dt" "open", "high", "low", "close", "volume"])
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