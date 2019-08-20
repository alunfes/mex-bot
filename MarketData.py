import pandas as pd
from datetime import datetime
import time
import json
from datetime import datetime

'''
https://www.bitmex.com/api/udf/history?symbol=XBTUSD&resolution=1&from=1555771700&to=1555858100
https://testnet.bitmex.com/app/trade/XBTUSD
'''


class MarketData:
    @classmethod
    def initialize(cls):

    '''
    bitmexのデータはアクセスlocationを判断しているので、JSTでunixtime表記される。
    一回あたりの最大ダウンロード数は10080。
    unix timeは1秒基準なので、from_utがto_utになるまで10080 * 60を足せば良い。
    '''
    @classmethod
    def download_hist_ohlc(cls, symbol, period, from_ut, to_ut):
        if from_ut < to_ut and (from_ut > 0 and to_ut > 0):
            print('downloading mex 1m data...')
            df_ohlc = pd.DataFrame()
            kijun = 10080 * 60
            current_ut = from_ut + kijun
            last_ut = 0 #新しくダウンロードしたデータの最初の部分が前回の最後の部分と重複しないためのチェックにしよう
            while current_ut <= to_ut:
                param = {"period": 1, "from": current_ut - kijun, "to": current_ut}
                url = "https://www.bitmex.com/api/udf/history?symbol=XBTUSD&resolution={period}&from={from}&to={to}".format(**param)
                res = requests.get(url)
                data = res.json()
                i = 0
                start_ind = 0
                if last_ut > 0:
                    while last_ut >= data['t'][i]:
                        i+=1
                    start_ind = i
                else:
                    start_ind = 0
                df = pd.DataFrame({
                    "timestamp": data["t"][start_ind:],
                    "dt": list(map(lambda x: datetime.fromtimestamp(float(x)), data["t"][start_ind:])),
                    "open": data["o"][start_ind:],
                    "high": data["h"][start_ind:],
                    "low": data["l"][start_ind:],
                    "close": data["c"][start_ind:],
                    "size": data["v"][start_ind:],
                }, columns=["timestamp", "dt", "open", "high", "low", "close", "size"])
                df_ohlc = pd.concat([df_ohlc,df], ignore_index=True)
                current_ut = current_ut + kijun if current_ut + kijun < to_ut else to_ut
                last_ut = data['t'][-1]
                if current_ut >= to_ut:
                    break
            print('Mex data download was completed!')
            df_ohlc.to_csv('./mex_1m_data.csv')



if __name__ == '__main__':
    MarketData.download_hist_ohlc('XBTUSD',1,1546268400,1556025180)
    #MarketData.initialize()
    #MarketData.read_quote_from_csv()



    '''
    elapsed_time:12.151946083704631[min]
train accuracy=0.9474857142857143
test accuracy=0.38903456495828365
pl=177.51999999999944,num=319,win_rate=0.6677115987460815
    '''