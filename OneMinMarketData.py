from OneMinData import OneMinData
from datetime import datetime, timedelta, timezone
from DownloadMexOhlc import DownloadMexOhlc
import threading
import numpy as np
import talib as ta
import pandas as pd
import csv
import pytz
import time
from SystemFlg import SystemFlg

'''
data download and calc for bot
1. download 1m data for maximum terms
2. calc latest index
3. download 1m data from previous update
4. 
'''

class OneMinMarketData:
    @classmethod
    def initialize_for_bot(cls, num_term):
        cls.ohlc_buffer = 10 #download more ohlc than max_term
        cls.JST = pytz.timezone('Asia/Tokyo')
        print('OneMinMarketData started:', datetime.now(cls.JST))
        cls.lock_tmp_ohlc = threading.Lock()
        cls.tmp_ohlc = OneMinData()
        cls.tmp_ohlc.initialize()
        cls.flg_update_ohlc = False
        cls.lock_flg_ohlc = threading.Lock()
        cls.df = None
        cls.pred = -1
        cls.lock_pred=  threading.Lock()
        cls.lock_df = threading.Lock()
        cls.term_list = cls.generate_term_list(num_term)
        cls.max_term = cls.detect_max_term()
        DownloadMexOhlc.initial_data_download(cls.max_term+cls.ohlc_buffer, './Data/bot_ohlc.csv')
        cls.ohlc = cls.read_from_csv('./Data/bot_ohlc.csv')
        #cls.ohlc.del_data(initial_data_vol)
        start = time.time()
        cls.__generate_all_func_dict()
        cls.__read_func_dict()
        cls.__calc_all_index_dict()
        cls.set_df(cls.generate_df_from_dict_for_bot())
        cls.set_flg_ohlc_update(True)
        print('time for market data initialization=',time.time() - start)
        th = threading.Thread(target=cls.__main_thread)
        th.start()

    #to be used by another process
    @classmethod
    def initialize_for_lgbmaster(cls, kijun_val, kijun_period, num_term, train_len, valid_size, lgb_params):
        print('initializing market data for lgb master.')
        start = time.time()
        cls.ohlc_path = '.Data/lgb_ohlc.csv'
        cls.ohlc_buffer = 1
        cls.kijun_period = kijun_period
        cls.kijun_val = kijun_val
        cls.ohlc = OneMinData()
        cls.ohlc.initialize()
        cls.term_list = cls.generate_term_list(num_term)
        DownloadMexOhlc.initial_data_download(train_len + cls.ohlc_buffer, cls.ohlc_path)
        cls.ohlc = cls.read_from_csv(cls.ohlc_path)
        cls.__generate_all_func_dict()
        cls.__calc_all_index_dict()




    @classmethod
    def initialize_for_marketdata_test(cls):
        DownloadMexOhlc.download_data()
        cls.term_list = cls.generate_term_list(10)
        cls.max_term = cls.detect_max_term()
        cls.ohlc = cls.read_from_csv('./Data/mex_data.csv')
        start = time.time()
        cls.__generate_all_func_dict()
        cls.__read_func_dict()
        cls.__calc_all_index_dict()
        df = cls.generate_df_from_dict_for_bot()
        print(df)
        df.to_csv('./Data/test_df.csv')
        print('time for market data initialization=', time.time() - start)


    @classmethod
    def set_pred(cls, pred):
        with cls.lock_pred:
            cls.pred =  pred

    @classmethod
    def get_pred(cls):
        with cls.lock_pred:
            return cls.pred

    @classmethod
    def set_flg_ohlc_update(cls, flg):
        with cls.lock_flg_ohlc:
            cls.flg_update_ohlc = flg

    @classmethod
    def get_flg_ohlc_update(cls):
        with cls.lock_flg_ohlc:
            return cls.flg_update_ohlc



    '''
    1.毎分00秒からws ohlcの更新を確認。
    2.ws tickdataからのohlc更新があり、それが現在の最新のデータの次の1分のデータの場合はそのohlcを採用
    3.2秒経過してもohlc更新がない場合は、download ohlcを使用 (download ohlcは毎分動かして最新のohlcと取得する）
    '''
    @classmethod
    def __main_thread(cls):
        def __check_next_min(last_ohlc_min):
            if last_ohlc_min == 58 and datetime.now(cls.JST).minute == 0:
                return True
            if last_ohlc_min == 59 and datetime.now(cls.JST).minute == 1:
                return True
            elif datetime.now(cls.JST).minute > last_ohlc_min+1:
                return True
            else:
                return False

        while SystemFlg.get_system_flg():
            tmp_ohlc_loop_flg = True
            if __check_next_min(cls.ohlc.dt[-1].minute):
                target_min = datetime.now(cls.JST).minute -1 if datetime.now(cls.JST).minute > 0 else 59 #取得すべきohlcのminutes, 01分時点でもtaget min=58
                while tmp_ohlc_loop_flg:
                    if len(cls.tmp_ohlc.dt) > 0:
                        #print('tmp=', cls.tmp_ohlc.dt[-1], ', target_min', target_min)
                        if cls.tmp_ohlc.dt[-1].minute is target_min: #2.ws tickdataからのohlc更新があり、それが現在の最新のデータの次の1分のデータの場合はそのohlcを採用
                            cls.ohlc.add_and_pop(cls.tmp_ohlc.unix_time[-1], cls.tmp_ohlc.dt[-1], cls.tmp_ohlc.open[-1],
                                                 cls.tmp_ohlc.high[-1], cls.tmp_ohlc.low[-1], cls.tmp_ohlc.close[-1],cls.tmp_ohlc.size[-1])
                            tmp_ohlc_loop_flg = False
                            print('ws ohlc:', datetime.now(cls.JST), cls.tmp_ohlc.dt[-1], cls.tmp_ohlc.open[-1],
                                                 cls.tmp_ohlc.high[-1], cls.tmp_ohlc.low[-1], cls.tmp_ohlc.close[-1],cls.tmp_ohlc.size[-1])
                            break
                    if datetime.now(cls.JST).second > 2: #2秒以上経過してwsからのohlc更新がない場合はdownload ohlc、latest dt.minuteから
                        res = DownloadMexOhlc.bot_ohlc_download_latest(cls.max_term+cls.ohlc_buffer) #latest ohlc dtからdatetime.now().minute-1分までのデータを取得すべき。
                        if res is not None:
                            cls.ohlc.add_and_pop(res[0], res[1], res[2], res[3], res[4], res[5], res[6])
                            tmp_ohlc_loop_flg = False
                            print('download ohlc:', datetime.now(cls.JST), res[0], res[1], res[2], res[3], res[4], res[5], res[6])
                        else:
                            print('download ohlc is none!')
                        break
                    time.sleep(0.3)

                if tmp_ohlc_loop_flg == False: #when download was successfull
                    cls.__calc_all_index_dict()
                    cls.set_df(cls.generate_df_from_dict_for_bot())
                    cls.set_flg_ohlc_update(True)
                else: #failed to update ohlc
                    print('failed to update ohlc skill index calc !')

            '''
            if (datetime.now(cls.JST).minute % 5) == 0 and datetime.now(cls.JST).second > 20: #5分に一回max termまでのデータをダウンロードしてcsvに記録し、market dataをrefreshする。
                print('5min ohlc download all')
                DownloadMexOhlc.initial_data_download(cls.max_term)
                cls.ohlc = cls.read_from_csv('./Data/bot_ohlc.csv')
                #cls.__calc_all_index_dict()
                #cls.set_df(cls.generate_df_from_dict_for_bot())
            '''
            time.sleep(0.1)


    @classmethod
    def set_df(cls, df):
        with cls.lock_df:
            cls.df = df

    @classmethod
    def get_df(cls):
        with cls.lock_df:
            if cls.df is not None:
                return cls.df.iloc[:]
            else:
                return None

    @classmethod
    def add_tmp_ohlc(cls, ut, dt, o, h, l, c, v):
        with cls.lock_tmp_ohlc:
            cls.tmp_ohlc.open.append(o)
            cls.tmp_ohlc.high.append(h)
            cls.tmp_ohlc.low.append(l)
            cls.tmp_ohlc.close.append(c)
            cls.tmp_ohlc.size.append(v)
            cls.tmp_ohlc.dt.append(dt)
            cls.tmp_ohlc.unix_time.append(ut)

    @classmethod
    def get_tmp_ohlc(cls):
        with cls.lock_tmp_ohlc:
            res = (cls.tmp_ohlc.open[-1], cls.tmp_ohlc.high[-1], cls.tmp_ohlc.low[-1], cls.tmp_ohlc.high[-1], cls.tmp_ohlc.close[-1], cls.tmp_ohlc.size[-1], cls.tmp_ohlc.dt[-1], cls.tmp_ohlc.unix_time[-1])
            cls.tmp_ohlc = OneMinData()
            cls.tmp_ohlc.initialize()
            return (res)


    @classmethod
    def detect_max_term(cls):
        max_term = 0
        cols = []
        with open("./Model/bpsp_cols.csv", "r") as f:
            reader = csv.reader(f)
            for r in reader:
                cols.append(r)
        for col in cols[0]:
            if col not in ['open', 'high', 'low', 'close']:
                if max_term < int(col.split(':')[1]):
                    max_term = int(col.split(':')[1])
        return max_term



    '''
    funcname_termをcsvから読み込む
    func_dictを生成
    '''
    @classmethod
    def __read_func_dict(cls):
        #read from func / term list
        cols = []
        with open("./Model/bpsp_cols.csv", "r") as f:
            reader = csv.reader(f)
            for r in reader:
                cols.append(r)
        #copy matched key func val
        func_obj= {}
        for col in cols[0]:
            if col not in ['open', 'high', 'low', 'close', 'open_change', 'high_change', 'low_change', 'close_change']:
                func_obj[col] = cls.ohlc.func_dict[col]
            else:
                print('invalid func was found!', col)
        #replace ohlc.func_dict
        cls.ohlc.func_dict = func_obj


    @classmethod
    def update_for_bot(cls):
        cls.__calc_all_index()

    @classmethod
    def read_from_csv(cls, file_name):
        print('reading ohlc from a file..')
        ohlc = OneMinData()
        ohlc.initialize()
        df = pd.read_csv(file_name)
        ohlc.dt = list(map(lambda x: datetime.strptime(str(x), '%Y-%m-%d %H:%M:%S'), list(df['dt'])))
        ohlc.unix_time = list(df['timestamp'])
        ohlc.open = list(df['open'])
        ohlc.high = list(df['high'])
        ohlc.low = list(df['low'])
        ohlc.close = list(df['close'])
        ohlc.size = list(df['volume'])
        print('completed read ohlc.')
        return ohlc

    '''
    func name一覧の読み込み
    all func listからkeyが一致するものだけを正規のfunc listとして残す
    正規のリストに対してindex計算
    '''
    @classmethod
    def __generate_all_func_dict(cls):
        for term in cls.term_list:
            cls.ohlc.func_dict['ema:' + str(term)] = (OneMinMarketData.calc_ema, term)
            cls.ohlc.func_dict['ema_kairi:' + str(term)] = (OneMinMarketData.calc_ema_kairi, term)
            cls.ohlc.func_dict['ema_gra:' + str(term)] = (OneMinMarketData.calc_ema_gra, term)
            cls.ohlc.func_dict['dema:' + str(term)] = (OneMinMarketData.calc_dema, term)
            cls.ohlc.func_dict['dema_kairi:' + str(term)] = (OneMinMarketData.calc_dema_kairi, term)
            cls.ohlc.func_dict['dema_gra:' + str(term)] = (OneMinMarketData.calc_dema_gra, term)
            cls.ohlc.func_dict['momentum:' + str(term)] = (OneMinMarketData.calc_momentum, term)
            cls.ohlc.func_dict['rate_of_change:' + str(term)] = (OneMinMarketData.calc_rate_of_change, term)
            cls.ohlc.func_dict['rsi:' + str(term)] = (OneMinMarketData.calc_rsi, term)
            cls.ohlc.func_dict['williams_R:' + str(term)] = (OneMinMarketData.calc_williams_R, term)
            cls.ohlc.func_dict['beta:' + str(term)] = (OneMinMarketData.calc_beta, term)
            cls.ohlc.func_dict['time_series_forecast:' + str(term)] = (OneMinMarketData.calc_time_series_forecast, term)
            cls.ohlc.func_dict['correl:' + str(term)] = (OneMinMarketData.calc_correl, term)
            cls.ohlc.func_dict['linear_reg:' + str(term)] = (OneMinMarketData.calc_linear_reg, term)
            cls.ohlc.func_dict['linear_reg_angle:' + str(term)] = (OneMinMarketData.calc_linear_reg_angle, term)
            cls.ohlc.func_dict['linear_reg_intercept:' + str(term)] = (OneMinMarketData.calc_linear_reg_intercept, term)
            cls.ohlc.func_dict['linear_reg_slope:' + str(term)] = (OneMinMarketData.calc_linear_reg_slope, term)
            cls.ohlc.func_dict['stdv:' + str(term)] = (OneMinMarketData.calc_stdv, term)
            cls.ohlc.func_dict['var:' + str(term)] = (OneMinMarketData.calc_var, term)
            cls.ohlc.func_dict['adx:' + str(term)] = (OneMinMarketData.calc_adx, term)
            cls.ohlc.func_dict['aroon_os:' + str(term)] = (OneMinMarketData.calc_aroon_os, term)
            cls.ohlc.func_dict['cci:' + str(term)] = (OneMinMarketData.calc_cci, term)
            cls.ohlc.func_dict['dx:' + str(term)] = (OneMinMarketData.calc_dx, term)
            if term >= 10:
                cls.ohlc.func_dict['macd:' + str(term)] = (OneMinMarketData.calc_macd, term)
                cls.ohlc.func_dict['macd_signal:' + str(term)] = (OneMinMarketData.calc_macd_signal, term)
                cls.ohlc.func_dict['macd_hist:' + str(term)] = (OneMinMarketData.calc_macd_hist, term)
            cls.ohlc.func_dict['makairi_momentum:' + str(term)] = (
            OneMinMarketData.generate_makairi, OneMinMarketData.calc_momentum, term)
            cls.ohlc.func_dict['makairi_rate_of_change:' + str(term)] = (
            OneMinMarketData.generate_makairi, OneMinMarketData.calc_rate_of_change, term)
            cls.ohlc.func_dict['makairi_rsi:' + str(term)] = (
            OneMinMarketData.generate_makairi, OneMinMarketData.calc_rsi, term)
            cls.ohlc.func_dict['makairi_williams_R:' + str(term)] = (
            OneMinMarketData.generate_makairi, OneMinMarketData.calc_williams_R, term)
            cls.ohlc.func_dict['makairi_beta:' + str(term)] = (
            OneMinMarketData.generate_makairi, OneMinMarketData.calc_beta, term)
            cls.ohlc.func_dict['makairi_time_series_forecast:' + str(term)] = (
            OneMinMarketData.generate_makairi, OneMinMarketData.calc_time_series_forecast, term)
            cls.ohlc.func_dict['makairi_correl:' + str(term)] = (
            OneMinMarketData.generate_makairi, OneMinMarketData.calc_correl, term)
            cls.ohlc.func_dict['makairi_linear_reg:' + str(term)] = (
            OneMinMarketData.generate_makairi, OneMinMarketData.calc_linear_reg, term)
            cls.ohlc.func_dict['makairi_linear_reg_angle:' + str(term)] = (
            OneMinMarketData.generate_makairi, OneMinMarketData.calc_linear_reg_angle, term)
            cls.ohlc.func_dict['makairi_linear_reg_intercept:' + str(term)] = (
            OneMinMarketData.generate_makairi, OneMinMarketData.calc_linear_reg_intercept, term)
            cls.ohlc.func_dict['makairi_linear_reg_slope:' + str(term)] = (
            OneMinMarketData.generate_makairi, OneMinMarketData.calc_linear_reg_slope, term)
            cls.ohlc.func_dict['makairi_stdv:' + str(term)] = (
            OneMinMarketData.generate_makairi, OneMinMarketData.calc_stdv, term)
            cls.ohlc.func_dict['makairi_var:' + str(term)] = (
            OneMinMarketData.generate_makairi, OneMinMarketData.calc_var, term)
            cls.ohlc.func_dict['makairi_adx:' + str(term)] = (
            OneMinMarketData.generate_makairi, OneMinMarketData.calc_adx, term)
            cls.ohlc.func_dict['makairi_aroon_os:' + str(term)] = (
            OneMinMarketData.generate_makairi, OneMinMarketData.calc_aroon_os, term)
            cls.ohlc.func_dict['makairi_cci:' + str(term)] = (
            OneMinMarketData.generate_makairi, OneMinMarketData.calc_cci, term)
            cls.ohlc.func_dict['makairi_dx:' + str(term)] = (
            OneMinMarketData.generate_makairi, OneMinMarketData.calc_dx, term)

            cls.ohlc.func_dict['diff_momentum:' + str(term)] = (
            OneMinMarketData.generate_diff, OneMinMarketData.calc_momentum, term)
            cls.ohlc.func_dict['diff_rate_of_change:' + str(term)] = (
            OneMinMarketData.generate_diff, OneMinMarketData.calc_rate_of_change, term)
            cls.ohlc.func_dict['diff_rsi:' + str(term)] = (
            OneMinMarketData.generate_diff, OneMinMarketData.calc_rsi, term)
            cls.ohlc.func_dict['diff_williams_R:' + str(term)] = (
            OneMinMarketData.generate_diff, OneMinMarketData.calc_williams_R, term)
            cls.ohlc.func_dict['diff_beta:' + str(term)] = (
            OneMinMarketData.generate_diff, OneMinMarketData.calc_beta, term)
            cls.ohlc.func_dict['diff_time_series_forecast:' + str(term)] = (
            OneMinMarketData.generate_diff, OneMinMarketData.calc_time_series_forecast, term)
            cls.ohlc.func_dict['diff_correl:' + str(term)] = (
            OneMinMarketData.generate_diff, OneMinMarketData.calc_correl, term)
            cls.ohlc.func_dict['diff_linear_reg:' + str(term)] = (
            OneMinMarketData.generate_diff, OneMinMarketData.calc_linear_reg, term)
            cls.ohlc.func_dict['diff_linear_reg_angle:' + str(term)] = (
            OneMinMarketData.generate_diff, OneMinMarketData.calc_linear_reg_angle, term)
            cls.ohlc.func_dict['diff_linear_reg_intercept:' + str(term)] = (
            OneMinMarketData.generate_diff, OneMinMarketData.calc_linear_reg_intercept, term)
            cls.ohlc.func_dict['diff_linear_reg_slope:' + str(term)] = (
            OneMinMarketData.generate_diff, OneMinMarketData.calc_linear_reg_slope, term)
            cls.ohlc.func_dict['diff_stdv:' + str(term)] = (
            OneMinMarketData.generate_diff, OneMinMarketData.calc_stdv, term)
            cls.ohlc.func_dict['diff_var:' + str(term)] = (
            OneMinMarketData.generate_diff, OneMinMarketData.calc_var, term)
            cls.ohlc.func_dict['diff_adx:' + str(term)] = (
            OneMinMarketData.generate_diff, OneMinMarketData.calc_adx, term)
            cls.ohlc.func_dict['diff_aroon_os:' + str(term)] = (
            OneMinMarketData.generate_diff, OneMinMarketData.calc_aroon_os, term)
            cls.ohlc.func_dict['diff_cci:' + str(term)] = (
            OneMinMarketData.generate_diff, OneMinMarketData.calc_cci, term)
            cls.ohlc.func_dict['diff_dx:' + str(term)] = (
            OneMinMarketData.generate_diff, OneMinMarketData.calc_dx, term)

        cls.ohlc.func_dict['normalized_ave_true_range:' + str(0)] = (OneMinMarketData.calc_normalized_ave_true_range, 0)
        cls.ohlc.func_dict['three_outside_updown:' + str(0)] = (OneMinMarketData.calc_three_outside_updown, 0)
        cls.ohlc.func_dict['breakway:' + str(0)] = (OneMinMarketData.calc_breakway, 0)
        cls.ohlc.func_dict['dark_cloud_cover:' + str(0)] = (OneMinMarketData.calc_dark_cloud_cover, 0)
        cls.ohlc.func_dict['dragonfly_doji:' + str(0)] = (OneMinMarketData.calc_dragonfly_doji, 0)
        cls.ohlc.func_dict['updown_sidebyside_white_lines:' + str(0)] = (
        OneMinMarketData.calc_updown_sidebyside_white_lines, 0)
        cls.ohlc.func_dict['haramisen:' + str(0)] = (OneMinMarketData.calc_haramisen, 0)
        cls.ohlc.func_dict['hikkake_pattern:' + str(0)] = (OneMinMarketData.calc_hikkake_pattern, 0)
        cls.ohlc.func_dict['neck_pattern:' + str(0)] = (OneMinMarketData.calc_neck_pattern, 0)
        cls.ohlc.func_dict['upsidedownside_gap_three_method:' + str(0)] = (
        OneMinMarketData.calc_upsidedownside_gap_three_method, 0)
        cls.ohlc.func_dict['sar:' + str(0)] = (OneMinMarketData.calc_sar, 0)
        cls.ohlc.func_dict['bop:' + str(0)] = (OneMinMarketData.calc_bop, 0)



    @classmethod
    def generate_term_list(cls, num):
        term_list = []
        category_n = [5, 50, 200]
        term_list.extend(list(np.round(np.linspace(category_n[0], category_n[0] * num, num))))
        term_list.extend(list(np.round(np.linspace(category_n[1] + (category_n[0] * num),
                                                   category_n[1] + (category_n[0] * num) + category_n[1] * num), num)))
        term_list.extend(list(np.round(np.linspace(category_n[2] + category_n[1] + (category_n[0] * num) + (category_n[1] * num),
                        category_n[2] + (category_n[1] * num) + category_n[2] * num), num)))
        return list(map(int, term_list))

    @classmethod
    def __calc_all_index_dict(cls):
        print('calculating all index dict')
        start_time = time.time()

        for k in cls.ohlc.func_dict:
            if int(k.split(':')[1]) > 0:
                if k.split('_')[0] != 'makairi' and k.split('_')[0] != 'diff' and k.split(':')[0] not in ['ema_kairi','ema_gra','dema_kairi','dema_gra']:
                    cls.ohlc.index_data_dict[k] = cls.ohlc.func_dict[k][0](cls.ohlc.func_dict[k][1])
            else:
                cls.ohlc.index_data_dict[k] = cls.ohlc.func_dict[k][0]()
        for k in cls.ohlc.func_dict:
            if k.split('_')[0] == 'makairi':
                data = cls.ohlc.func_dict[k][1](cls.ohlc.func_dict[k][2])
                cls.ohlc.index_data_dict[k] = cls.ohlc.func_dict[k][0](data, cls.ohlc.func_dict[k][2])
            elif k.split('_')[0] == 'diff':
                data = cls.ohlc.func_dict[k][1](cls.ohlc.func_dict[k][2])
                cls.ohlc.index_data_dict[k] = cls.ohlc.func_dict[k][0](data)
        print('completed calc all index. time=', time.time() - start_time)

    @classmethod
    def calc_ohlc_change(cls):
        cls.ohlc.open_change.append(0)
        cls.ohlc.high_change.append(0)
        cls.ohlc.low_change.append(0)
        cls.ohlc.close_change.append(0)
        for i in range(len(cls.ohlc.close) - 1):
            close = cls.ohlc.close[i]
            cls.ohlc.open_change.append(round(cls.ohlc.open[i + 1] / close, 5))
            cls.ohlc.high_change.append(round(cls.ohlc.high[i + 1] / close, 5))
            cls.ohlc.low_change.append(round(cls.ohlc.low[i + 1] / close, 5))
            cls.ohlc.close_change.append(round(cls.ohlc.close[i + 1] / close, 5))


    @classmethod
    def generate_df_from_dict_for_bot(cls):
        df = pd.DataFrame(OneMinMarketData.ohlc.index_data_dict)
        cols = list(df.columns)
        cols.sort()
        #df = df.loc[:,cols]
        df = df[cols]
        return df.iloc[-1:]

    @classmethod
    def generate_df_from_dict(cls):
        cut_size = cls.term_list[-1] * 2
        end = len(cls.ohlc.close) - 10
        df = pd.DataFrame(OneMinMarketData.ohlc.index_data_dict)
        df = df.assign(dt=cls.ohlc.dt)
        df = df.assign(open=cls.ohlc.open)
        df = df.assign(high=cls.ohlc.high)
        df = df.assign(low=cls.ohlc.low)
        df = df.assign(close=cls.ohlc.close)
        df = df.assign(size=cls.ohlc.size)
        df = df.assign(bpsp=cls.ohlc.bpsp)
        return df.iloc[cut_size:end]

    @classmethod
    def generate_df_for_lgbmaster(cls):
        cut_size = cls.term_list[-1] + 1
        end = len(cls.ohlc.close) - cls.kijun_period
        df = pd.DataFrame(OneMinMarketData.ohlc.index_data_dict)
        df = df.assign(dt=cls.ohlc.dt)
        df = df.assign(open=cls.ohlc.open)
        df = df.assign(high=cls.ohlc.high)
        df = df.assign(low=cls.ohlc.low)
        df = df.assign(close=cls.ohlc.close)
        df = df.assign(size=cls.ohlc.size)
        df = df.assign(bpsp=cls.ohlc.bpsp)
        return df.iloc[cut_size:end]


    @classmethod
    def generate_makairi(cls, data, ma_term):
        ma = list(ta.MA(np.array(data, dtype='f8'), timeperiod=ma_term))
        return list(map(lambda c, e: (c - e) / e, data, ma))

    @classmethod
    def generate_diff(cls, data):
        return list(ta.ROC(np.array(data, dtype='f8'), timeperiod=1))


    # higher pl in next 1m for bp sp
    @classmethod
    def calc_bpsp_points(cls):
        bpsp = []  # 0: buy, 1:sell
        for i in range(1, len(cls.ohlc.close)):
            if cls.ohlc.close[i] - cls.ohlc.close[i - 1] > cls.ohlc.close[i - 1] - cls.ohlc.close[i]:
                bpsp.append(1)
            else:
                bpsp.append(0)
        bpsp.append(None)
        return bpsp

    @classmethod
    def remove_all_correlated_cols3(self, df, corr_kijun):
        print('removing all correlated columns..')
        df2 = df.copy()
        df3 = df.copy()
        df2.drop(['dt'], axis=1, inplace=True)
        corrs = np.corrcoef(np.array(df2).transpose())

        # 1. 0番目から0.9以上のindexを検索
        def check_corr_kijun(cor, cor_ind, kijun):
            rem = []
            for i, c in enumerate(cor):
                if c >= kijun and i != cor_ind:
                    rem.append(i)
            return rem

        tmp_remo = []
        for i, cor in enumerate(corrs):
            if i not in tmp_remo:  # 3. 該当indexを除いて次のindexを対象に1の操作を実行
                # 2. 該当したindexをtmp_remoに記録
                tmp_remo.extend(check_corr_kijun(cor, i, corr_kijun))
        # 4. tmp_remoに記録されたindexのcolumnをdfから削除
        target_col = []
        cols = list(df2.columns)
        for tr in tmp_remo:
            target_col.append(cols[tr])
        excludes = ['dt', 'open', 'high', 'low', 'close', 'dt']
        for ex in excludes:
            if ex in target_col:
                target_col.remove(ex)
        df3.drop(target_col, axis=1, inplace=True)
        print('removed ' + str(len(target_col)) + ' colums', 'remaining col=' + str(len(df3.columns)))
        return df3, corrs

    @classmethod
    def calc_ema(cls, term):
        return list(ta.EMA(np.array(cls.ohlc.close, dtype='f8'), timeperiod=term))

    @classmethod
    def calc_ema_kairi(cls, term):
        ema = cls.calc_ema(term)
        #return list(map(lambda c, e: (c - e) / e, cls.ohlc.close, cls.ohlc.index_data_dict['ema:' + str(term)]))
        return list(map(lambda c, e: (c - e) / e, cls.ohlc.close, ema))

    @classmethod
    def calc_dema_kairi(cls, term):
        dema = cls.calc_dema(term)
        #return list(map(lambda c, d: (c - d) / d, cls.ohlc.close, cls.ohlc.index_data_dict['dema:' + str(term)]))
        return list(map(lambda c, d: (c - d) / d, cls.ohlc.close, dema))

    @classmethod
    def calc_ema_gra(cls, term):
        return list(pd.Series(cls.ohlc.index_data_dict['ema:' + str(term)]).diff())

    @classmethod
    def calc_dema_gra(cls, term):
        return list(pd.Series(cls.ohlc.index_data_dict['dema:' + str(term)]).diff())

    @classmethod
    def calc_dema(cls, term):
        return list(ta.DEMA(np.array(cls.ohlc.close, dtype='f8'), timeperiod=term))

    #termの2倍くらいnanが続く
    @classmethod
    def calc_adx(cls, term):
        return list(
            ta.ADX(np.array(cls.ohlc.high, dtype='f8'), np.array(cls.ohlc.low, dtype='f8'),
                   np.array(cls.ohlc.close, dtype='f8'), timeperiod=term))

    @classmethod
    def calc_aroon_os(cls, term):
        return list(
            ta.AROONOSC(np.array(cls.ohlc.high, dtype='f8'), np.array(cls.ohlc.low, dtype='f8'), timeperiod=term))

    @classmethod
    def calc_cci(cls, term):
        return list(
            ta.CCI(np.array(cls.ohlc.high, dtype='f8'), np.array(cls.ohlc.low, dtype='f8'),
                   np.array(cls.ohlc.close, dtype='f8'), timeperiod=term))

    @classmethod
    def calc_dx(cls, term):
        return list(
            ta.DX(np.array(cls.ohlc.high, dtype='f8'), np.array(cls.ohlc.low, dtype='f8'),
                  np.array(cls.ohlc.close, dtype='f8'), timeperiod=term))

    @classmethod
    def calc_midprice(cls, term, high, low):
        return list(ta.MIDPRICE(np.array(high, dtype='f8'), np.array(low, dtype='f8'), timeperiod=term))

    @classmethod
    def calc_macd(cls, term):
        slowperiod = term
        fastperiod = int(term / 2.0)
        signalperiod = int(term / 3.0)
        macd, signal, hist = ta.MACD(np.array(cls.ohlc.close, dtype='f8'), np.array(fastperiod, dtype='i8'),
                                     np.array(slowperiod, dtype='i8'), np.array(signalperiod, dtype='i8'))
        return macd

    @classmethod
    def calc_macd_signal(cls, term):
        slowperiod = term
        fastperiod = int(term / 2.0)
        signalperiod = int(term / 3.0)
        macd, signal, hist = ta.MACD(np.array(cls.ohlc.close, dtype='f8'), np.array(fastperiod, dtype='i8'),
                                     np.array(slowperiod, dtype='i8'),
                                     np.array(signalperiod, dtype='i8'))
        return signal

    @classmethod
    def calc_macd_hist(cls, term):
        slowperiod = term
        fastperiod = int(term / 2.0)
        signalperiod = int(term / 3.0)
        macd, signal, hist = ta.MACD(np.array(cls.ohlc.close, dtype='f8'), np.array(fastperiod, dtype='i8'),
                                     np.array(slowperiod, dtype='i8'),
                                     np.array(signalperiod, dtype='i8'))
        return hist

    @classmethod
    def calc_momentum(cls, term):
        return list(ta.MOM(np.array(cls.ohlc.close, dtype='f8'), timeperiod=term))

    @classmethod
    def calc_rate_of_change(cls, term):
        return list(ta.ROC(np.array(cls.ohlc.close, dtype='f8'), timeperiod=term))

    @classmethod
    def calc_rsi(cls, term):
        return list(ta.RSI(np.array(cls.ohlc.close, dtype='f8'), timeperiod=term))

    @classmethod
    def calc_williams_R(cls, term):
        return list(ta.WILLR(np.array(cls.ohlc.high, dtype='f8'), np.array(cls.ohlc.low, dtype='f8'),
                             np.array(cls.ohlc.close, dtype='f8'), timeperiod=term))

    @classmethod
    def calc_beta(cls, term):
        return list(ta.BETA(np.array(cls.ohlc.high, dtype='f8'), np.array(cls.ohlc.low, dtype='f8'), timeperiod=term))

    @classmethod
    def calc_time_series_forecast(cls, term):
        return list(ta.TSF(np.array(cls.ohlc.close, dtype='f8'), timeperiod=term))

    @classmethod
    def calc_correl(cls, term):
        return list(ta.CORREL(np.array(cls.ohlc.high, dtype='f8'), np.array(cls.ohlc.low, dtype='f8'), timeperiod=term))

    @classmethod
    def calc_linear_reg(cls, term):
        return list(ta.LINEARREG(np.array(cls.ohlc.close, dtype='f8'), timeperiod=term))

    @classmethod
    def calc_linear_reg_angle(cls, term):
        return list(ta.LINEARREG_ANGLE(np.array(cls.ohlc.close, dtype='f8'), timeperiod=term))

    @classmethod
    def calc_linear_reg_intercept(cls, term):
        return list(ta.LINEARREG_SLOPE(np.array(cls.ohlc.close, dtype='f8'), timeperiod=term))

    @classmethod
    def calc_linear_reg_slope(cls, term):
        return list(ta.LINEARREG_INTERCEPT(np.array(cls.ohlc.close, dtype='f8'), timeperiod=term))

    @classmethod
    def calc_stdv(cls, term):
        return list(ta.STDDEV(np.array(cls.ohlc.close, dtype='f8'), timeperiod=term, nbdev=1))

    @classmethod
    def calc_var(cls, term):
        return list(ta.VAR(np.array(cls.ohlc.close, dtype='f8'), timeperiod=term, nbdev=1))

    @classmethod
    def calc_normalized_ave_true_range(cls):
        return list(ta.NATR(np.array(cls.ohlc.high, dtype='f8'), np.array(cls.ohlc.low, dtype='f8'),
                            np.array(cls.ohlc.close, dtype='f8')))

    @classmethod
    def calc_three_outside_updown(cls):
        return list(ta.CDL3OUTSIDE(np.array(cls.ohlc.open, dtype='f8'), np.array(cls.ohlc.high, dtype='f8'),
                                   np.array(cls.ohlc.low, dtype='f8'),
                                   np.array(cls.ohlc.close, dtype='f8')))

    @classmethod
    def calc_breakway(cls):
        return list(ta.CDLBREAKAWAY(np.array(cls.ohlc.open, dtype='f8'), np.array(cls.ohlc.high, dtype='f8'),
                                    np.array(cls.ohlc.low, dtype='f8'),
                                    np.array(cls.ohlc.close, dtype='f8')))

    @classmethod
    def calc_dark_cloud_cover(cls):
        return list(ta.CDLDARKCLOUDCOVER(np.array(cls.ohlc.open, dtype='f8'), np.array(cls.ohlc.high, dtype='f8'),
                                         np.array(cls.ohlc.low, dtype='f8'),
                                         np.array(cls.ohlc.close, dtype='f8'), penetration=0))

    @classmethod
    def calc_dragonfly_doji(cls):
        return list(ta.CDLDRAGONFLYDOJI(np.array(cls.ohlc.open, dtype='f8'), np.array(cls.ohlc.high, dtype='f8'),
                                        np.array(cls.ohlc.low, dtype='f8'),
                                        np.array(cls.ohlc.close, dtype='f8')))

    @classmethod
    def calc_updown_sidebyside_white_lines(cls):
        return list(
            ta.CDLGAPSIDESIDEWHITE(np.array(cls.ohlc.open, dtype='f8'), np.array(cls.ohlc.high, dtype='f8'),
                                   np.array(cls.ohlc.low, dtype='f8'),
                                   np.array(cls.ohlc.close, dtype='f8')))

    @classmethod
    def calc_haramisen(cls):
        return list(ta.CDLHARAMI(np.array(cls.ohlc.open, dtype='f8'), np.array(cls.ohlc.high, dtype='f8'),
                                 np.array(cls.ohlc.low, dtype='f8'), np.array(cls.ohlc.close, dtype='f8')))

    @classmethod
    def calc_hikkake_pattern(cls):
        return list(ta.CDLHIKKAKEMOD(np.array(cls.ohlc.open, dtype='f8'), np.array(cls.ohlc.high, dtype='f8'),
                                     np.array(cls.ohlc.low, dtype='f8'), np.array(cls.ohlc.close, dtype='f8')))

    @classmethod
    def calc_neck_pattern(cls):
        return list(ta.CDLINNECK(np.array(cls.ohlc.open, dtype='f8'), np.array(cls.ohlc.high, dtype='f8'),
                                 np.array(cls.ohlc.low, dtype='f8'), np.array(cls.ohlc.close, dtype='f8')))

    @classmethod
    def calc_sar(cls):
        accelation = 0.02
        maximum = 0.2
        return list(ta.SAR(np.array(cls.ohlc.high, dtype='f8'), np.array(cls.ohlc.low, dtype='f8'),
                           np.array(accelation, dtype='f8'), np.array(maximum, dtype='f8')))

    @classmethod
    def calc_bop(cls):
        return list(ta.BOP(np.array(cls.ohlc.open, dtype='f8'), np.array(cls.ohlc.high, dtype='f8'),
                           np.array(cls.ohlc.low, dtype='f8'), np.array(cls.ohlc.close, dtype='f8')))

    @classmethod
    def calc_upsidedownside_gap_three_method(cls):
        return list(ta.CDLXSIDEGAP3METHODS(np.array(cls.ohlc.open, dtype='f8'), np.array(cls.ohlc.high, dtype='f8'),
                                           np.array(cls.ohlc.low, dtype='f8'), np.array(cls.ohlc.close, dtype='f8')))


    @classmethod
    def check_matched_index(cls, test_x):
        test = list(test_x['open'])
        op = cls.ohlc.open
        for i in range(len(op)):
            flg = True
            for j in range(30):
                if test[j] != op[i + j]:
                    flg = False
                    break
            if flg:
                return i
        print('no matche index found!')
        return -1




if __name__ == '__main__':
    SystemFlg.initialize()
    OneMinMarketData.initialize_for_marketdata_test()