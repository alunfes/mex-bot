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
    def initialize_for_bot(cls):
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
        cls.lock_pred = threading.Lock()
        cls.lock_df = threading.Lock()
        cls.term_list = cls.generate_term_list2(cls.__read_numterm_data())
        cls.kijun_period = cls.__read_kijunperiod()

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


    @classmethod
    def __read_numterm_data(self):
        config = pd.read_csv('./Model/bpsp_config.csv', index_col=0)
        return int(config['num_term'])

    @classmethod
    def __read_kijunperiod(self):
        config = pd.read_csv('./Model/bpsp_config.csv', index_col=0)
        return int(config['kijun_period'])


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

        #loop for generate 1m ohlc and calc df
        while SystemFlg.get_system_flg():
            tmp_ohlc_loop_flg = True
            flg_5m_ohlc = False
            if __check_next_min(cls.ohlc.dt[-1].minute):
                target_min = datetime.now(cls.JST).minute -1 if datetime.now(cls.JST).minute > 0 else 59 #取得すべきohlcのminutes, 01分時点でもtaget min=58

                if datetime.now(cls.JST).minute == 0 and flg_5m_ohlc == False:  # 60分に一回max termまでのデータをダウンロードしてcsvに記録し、market dataをrefreshする。
                    print('5min ohlc download all')
                    time.sleep(20) #wait until data is ready in bitmex
                    DownloadMexOhlc.initial_data_download(cls.max_term + cls.ohlc_buffer, './Data/bot_ohlc.csv')
                    cls.ohlc = cls.read_from_csv('./Data/bot_ohlc.csv')
                    flg_5m_ohlc = True

                while tmp_ohlc_loop_flg and flg_5m_ohlc == False:
                    if len(cls.tmp_ohlc.dt) > 0:
                        #print('tmp=', cls.tmp_ohlc.dt[-1], ', target_min', target_min)
                        if cls.tmp_ohlc.dt[-1].minute is target_min: #2.ws tickdataからのohlc更新があり、それが現在の最新のデータの次の1分のデータの場合はそのohlcを採用
                            cls.ohlc.add_and_pop(cls.tmp_ohlc.unix_time[-1], cls.tmp_ohlc.dt[-1], cls.tmp_ohlc.open[-1],
                                                 cls.tmp_ohlc.high[-1], cls.tmp_ohlc.low[-1], cls.tmp_ohlc.close[-1],cls.tmp_ohlc.size[-1])
                            tmp_ohlc_loop_flg = False
                            print('ws ohlc:', datetime.now(cls.JST), cls.tmp_ohlc.dt[-1], cls.tmp_ohlc.open[-1],cls.tmp_ohlc.high[-1], cls.tmp_ohlc.low[-1], cls.tmp_ohlc.close[-1],cls.tmp_ohlc.size[-1])
                            break

                    if datetime.now(cls.JST).second > 2: #2秒以上経過してwsからのohlc更新がない場合は必要なデータをダウンロード
                        res = DownloadMexOhlc.bot_ohlc_download_latest(1)  # latest ohlc dtからdatetime.now().minute-1分までのデータを取得すべき。
                        if res is not None:
                            cls.ohlc.add_and_pop(res[0], res[1], res[2], res[3], res[4], res[5], res[6])
                            tmp_ohlc_loop_flg = False
                            print('download ohlc:', datetime.now(cls.JST), res[0], res[1], res[2], res[3], res[4], res[5], res[6])
                        else:
                            print('download ohlc is none!')
                        break
                    time.sleep(0.3)

                cls.__calc_all_index_dict()
                cls.set_df(cls.generate_df_from_dict_for_bot())
                cls.set_flg_ohlc_update(True)
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
        func_obj= {}
        for col in cols[0]:
            func_obj[col] = cls.ohlc.func_dict[col]
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
            cls.ohlc.func_dict['ema_size:' + str(term)] = (OneMinMarketData.calc_ema_size, term)
            cls.ohlc.func_dict['ema_kairi:' + str(term)] = (OneMinMarketData.calc_ema_kairi, term)
            # cls.ohlc.func_dict['ema_gra:'+str(term)] = (OneMinMarketData.calc_ema_gra,term)
            cls.ohlc.func_dict['dema:' + str(term)] = (OneMinMarketData.calc_dema, term)
            # cls.ohlc.func_dict['dema_kairi:'+str(term)] = (OneMinMarketData.calc_dema_kairi,term)
            # cls.ohlc.func_dict['dema_gra:'+str(term)] = (OneMinMarketData.calc_dema_gra,term)
            cls.ohlc.func_dict['momentum:' + str(term)] = (OneMinMarketData.calc_momentum, term)
            cls.ohlc.func_dict['momentum_size:' + str(term)] = (OneMinMarketData.calc_momentum_size, term)
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
            cls.ohlc.func_dict['stdv_size:' + str(term)] = (OneMinMarketData.calc_stdv_size, term)
            cls.ohlc.func_dict['var:' + str(term)] = (OneMinMarketData.calc_var, term)
            cls.ohlc.func_dict['adx:' + str(term)] = (OneMinMarketData.calc_adx, term)
            cls.ohlc.func_dict['aroon_os:' + str(term)] = (OneMinMarketData.calc_aroon_os, term)
            cls.ohlc.func_dict['cci:' + str(term)] = (OneMinMarketData.calc_cci, term)
            cls.ohlc.func_dict['dx:' + str(term)] = (OneMinMarketData.calc_dx, term)
            if term >= 10:
                cls.ohlc.func_dict['macd:' + str(term)] = (OneMinMarketData.calc_macd, term)
                cls.ohlc.func_dict['macd_signal:' + str(term)] = (OneMinMarketData.calc_macd_signal, term)
                cls.ohlc.func_dict['macd_hist:' + str(term)] = (OneMinMarketData.calc_macd_hist, term)
            if term <= 300:
                cls.ohlc.func_dict['calc_high_kairi:' + str(term)] = (OneMinMarketData.calc_high_kairi, term)
                cls.ohlc.func_dict['calc_low_kairi:' + str(term)] = (OneMinMarketData.calc_low_kairi, term)

            '''
            cls.ohlc.func_dict['makairi_momentum:'+str(term)] = (OneMinMarketData.generate_makairi,OneMinMarketData.calc_momentum, term)
            cls.ohlc.func_dict['makairi_rate_of_change:'+str(term)] = (OneMinMarketData.generate_makairi,OneMinMarketData.calc_rate_of_change, term)
            cls.ohlc.func_dict['makairi_rsi:'+str(term)] = (OneMinMarketData.generate_makairi,OneMinMarketData.calc_rsi, term)
            cls.ohlc.func_dict['makairi_williams_R:'+str(term)] = (OneMinMarketData.generate_makairi,OneMinMarketData.calc_williams_R, term)
            cls.ohlc.func_dict['makairi_beta:'+str(term)] = (OneMinMarketData.generate_makairi,OneMinMarketData.calc_beta, term)
            cls.ohlc.func_dict['makairi_time_series_forecast:'+str(term)] = (OneMinMarketData.generate_makairi,OneMinMarketData.calc_time_series_forecast, term)
            cls.ohlc.func_dict['makairi_correl:'+str(term)] = (OneMinMarketData.generate_makairi,OneMinMarketData.calc_correl, term)
            cls.ohlc.func_dict['makairi_linear_reg:'+str(term)] = (OneMinMarketData.generate_makairi,OneMinMarketData.calc_linear_reg, term)
            cls.ohlc.func_dict['makairi_linear_reg_angle:'+str(term)] = (OneMinMarketData.generate_makairi,OneMinMarketData.calc_linear_reg_angle, term)
            cls.ohlc.func_dict['makairi_linear_reg_intercept:'+str(term)] = (OneMinMarketData.generate_makairi,OneMinMarketData.calc_linear_reg_intercept, term)
            cls.ohlc.func_dict['makairi_linear_reg_slope:'+str(term)] = (OneMinMarketData.generate_makairi,OneMinMarketData.calc_linear_reg_slope, term)
            cls.ohlc.func_dict['makairi_stdv:'+str(term)] = (OneMinMarketData.generate_makairi,OneMinMarketData.calc_stdv, term)
            cls.ohlc.func_dict['makairi_var:'+str(term)] = (OneMinMarketData.generate_makairi,OneMinMarketData.calc_var, term)
            cls.ohlc.func_dict['makairi_adx:'+str(term)] = (OneMinMarketData.generate_makairi,OneMinMarketData.calc_adx, term)
            cls.ohlc.func_dict['makairi_aroon_os:'+str(term)] = (OneMinMarketData.generate_makairi,OneMinMarketData.calc_aroon_os, term)
            cls.ohlc.func_dict['makairi_cci:'+str(term)] = (OneMinMarketData.generate_makairi,OneMinMarketData.calc_cci, term)
            cls.ohlc.func_dict['makairi_dx:'+str(term)] = (OneMinMarketData.generate_makairi,OneMinMarketData.calc_dx, term)

            cls.ohlc.func_dict['diff_momentum:'+str(term)] = (OneMinMarketData.generate_diff,OneMinMarketData.calc_momentum, term)
            cls.ohlc.func_dict['diff_rate_of_change:'+str(term)] = (OneMinMarketData.generate_diff,OneMinMarketData.calc_rate_of_change, term)
            cls.ohlc.func_dict['diff_rsi:'+str(term)] = (OneMinMarketData.generate_diff,OneMinMarketData.calc_rsi, term)
            cls.ohlc.func_dict['diff_williams_R:'+str(term)] = (OneMinMarketData.generate_diff,OneMinMarketData.calc_williams_R, term)
            cls.ohlc.func_dict['diff_beta:'+str(term)] = (OneMinMarketData.generate_diff,OneMinMarketData.calc_beta, term)
            cls.ohlc.func_dict['diff_time_series_forecast:'+str(term)] = (OneMinMarketData.generate_diff,OneMinMarketData.calc_time_series_forecast, term)
            cls.ohlc.func_dict['diff_correl:'+str(term)] = (OneMinMarketData.generate_diff,OneMinMarketData.calc_correl, term)
            cls.ohlc.func_dict['diff_linear_reg:'+str(term)] = (OneMinMarketData.generate_diff,OneMinMarketData.calc_linear_reg, term)
            cls.ohlc.func_dict['diff_linear_reg_angle:'+str(term)] = (OneMinMarketData.generate_diff,OneMinMarketData.calc_linear_reg_angle, term)
            cls.ohlc.func_dict['diff_linear_reg_intercept:'+str(term)] = (OneMinMarketData.generate_diff,OneMinMarketData.calc_linear_reg_intercept, term)
            cls.ohlc.func_dict['diff_linear_reg_slope:'+str(term)] = (OneMinMarketData.generate_diff,OneMinMarketData.calc_linear_reg_slope, term)
            cls.ohlc.func_dict['diff_stdv:'+str(term)] = (OneMinMarketData.generate_diff,OneMinMarketData.calc_stdv, term)
            cls.ohlc.func_dict['diff_var:'+str(term)] = (OneMinMarketData.generate_diff,OneMinMarketData.calc_var, term)
            cls.ohlc.func_dict['diff_adx:'+str(term)] = (OneMinMarketData.generate_diff,OneMinMarketData.calc_adx, term)
            cls.ohlc.func_dict['diff_aroon_os:'+str(term)] = (OneMinMarketData.generate_diff,OneMinMarketData.calc_aroon_os, term)
            cls.ohlc.func_dict['diff_cci:'+str(term)] = (OneMinMarketData.generate_diff,OneMinMarketData.calc_cci, term)
            cls.ohlc.func_dict['diff_dx:'+str(term)] = (OneMinMarketData.generate_diff,OneMinMarketData.calc_dx, term)
            '''

        cls.ohlc.func_dict['normalized_ave_true_range:' + str(0)] = (OneMinMarketData.calc_normalized_ave_true_range, 0)
        cls.ohlc.func_dict['three_outside_updown:' + str(0)] = (OneMinMarketData.calc_three_outside_updown, 0)
        cls.ohlc.func_dict['breakway:' + str(0)] = (OneMinMarketData.calc_breakway, 0)
        cls.ohlc.func_dict['dark_cloud_cover:' + str(0)] = (OneMinMarketData.calc_dark_cloud_cover, 0)
        cls.ohlc.func_dict['dragonfly_doji:' + str(0)] = (OneMinMarketData.calc_dragonfly_doji, 0)
        cls.ohlc.func_dict['updown_sidebyside_white_lines:' + str(0)] = (OneMinMarketData.calc_updown_sidebyside_white_lines, 0)
        cls.ohlc.func_dict['haramisen:' + str(0)] = (OneMinMarketData.calc_haramisen, 0)
        cls.ohlc.func_dict['hikkake_pattern:' + str(0)] = (OneMinMarketData.calc_hikkake_pattern, 0)
        cls.ohlc.func_dict['neck_pattern:' + str(0)] = (OneMinMarketData.calc_neck_pattern, 0)
        cls.ohlc.func_dict['upsidedownside_gap_three_method:' + str(0)] = (OneMinMarketData.calc_upsidedownside_gap_three_method, 0)
        cls.ohlc.func_dict['sar:' + str(0)] = (OneMinMarketData.calc_sar, 0)
        cls.ohlc.func_dict['bop:' + str(0)] = (OneMinMarketData.calc_bop, 0)
        cls.ohlc.func_dict['uwahige:' + str(0)] = (OneMinMarketData.calc_uwahige_length, 0)
        cls.ohlc.func_dict['shitahige:' + str(0)] = (OneMinMarketData.calc_shitahige_length, 0)


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
        print('completed non makairi diff index. time=', time.time() - start_time)

        start_time = time.time()
        for k in cls.ohlc.func_dict:
            if k.split('_')[0] == 'makairi':
                data = cls.ohlc.func_dict[k][1](cls.ohlc.func_dict[k][2])
                cls.ohlc.index_data_dict[k] = cls.ohlc.func_dict[k][0](data, cls.ohlc.func_dict[k][2])
            elif k.split('_')[0] == 'diff':
                data = cls.ohlc.func_dict[k][1](cls.ohlc.func_dict[k][2])
                cls.ohlc.index_data_dict[k] = cls.ohlc.func_dict[k][0](data)

        print('completed calc makairi diff index. time=', time.time() - start_time)

    @classmethod
    def generate_df_from_dict(cls):
        start_time = time.time()
        cut_size = cls.term_list[-1] + 1
        end = len(cls.ohlc.close) - cls.kijun_period  # due to bpsp
        OneMinMarketData.ohlc.index_data_dict['dt'] = cls.ohlc.dt
        OneMinMarketData.ohlc.index_data_dict['size'] = cls.ohlc.size
        OneMinMarketData.ohlc.index_data_dict['close'] = cls.ohlc.close
        df = pd.DataFrame(OneMinMarketData.ohlc.index_data_dict)
        df = df.iloc[cut_size:end]
        #df = df.assign(future_side=cls.ohlc.future_side[cut_size:])
        print('completed generate df from dict. time=', time.time() - start_time)
        return df

    @classmethod
    def generate_df_from_dict_for_bot(cls):
        df = pd.DataFrame(OneMinMarketData.ohlc.index_data_dict)
        cols = list(df.columns)
        cols.sort()
        # df = df.loc[:,cols]
        df = df[cols]
        return df.iloc[-1:]

    @classmethod
    def remove_cols_contains_nan2(cls, df):
        start_time = time.time()
        pre_n = len(df.columns)
        after_n = len(df.dropna(axis=1, how='any').columns)
        print('removed ', pre_n - after_n, 'cols contains nan.')
        print('completed remove cols contains nan. time=', time.time() - start_time)
        return df.dropna(axis=1, how='any')

    @classmethod
    def __calc_all_index(cls):
        start_time = time.time()
        cls.ohlc.ave_price = cls.calc_ave_price(cls.ohlc.open, cls.ohlc.high, cls.ohlc.low, cls.ohlc.close)
        for term in cls.term_list:
            cls.ohlc.ema[term] = cls.calc_ema(term, cls.ohlc.close)
            cls.ohlc.ema_kairi[term] = cls.calc_ema_kairi(cls.ohlc.close, cls.ohlc.ema[term])
            cls.ohlc.ema_gra[term] = cls.calc_ema_gra(cls.ohlc.ema[term])
            cls.ohlc.dema[term] = cls.calc_dema(term, cls.ohlc.close)
            cls.ohlc.dema_kairi[term] = cls.calc_dema_kairi(cls.ohlc.close, cls.ohlc.dema[term])
            cls.ohlc.dema_gra[term] = cls.calc_dema_gra(cls.ohlc.dema[term])
            cls.ohlc.momentum[term] = cls.calc_momentum(term, cls.ohlc.close)
            cls.ohlc.rate_of_change[term] = cls.calc_rate_of_change(term, cls.ohlc.close)
            cls.ohlc.rsi[term] = cls.calc_rsi(term, cls.ohlc.close)
            cls.ohlc.williams_R[term] = cls.calc_williams_R(term, cls.ohlc.high, cls.ohlc.low, cls.ohlc.close)
            cls.ohlc.beta[term] = cls.calc_beta(term, cls.ohlc.high, cls.ohlc.low)
            cls.ohlc.tsf[term] = cls.calc_time_series_forecast(term, cls.ohlc.close)
            cls.ohlc.correl[term] = cls.calc_correl(term, cls.ohlc.high, cls.ohlc.low)
            cls.ohlc.linear_reg[term] = cls.calc_linear_reg(term, cls.ohlc.close)
            cls.ohlc.linear_reg_angle[term] = cls.calc_linear_reg_angle(term, cls.ohlc.close)
            cls.ohlc.linear_reg_intercept[term] = cls.calc_linear_reg_intercept(term, cls.ohlc.close)
            cls.ohlc.linear_reg_slope[term] = cls.calc_linear_reg_slope(term, cls.ohlc.close)
            cls.ohlc.stdv[term] = cls.calc_stdv(term, cls.ohlc.close)
            cls.ohlc.var[term] = cls.calc_var(term, cls.ohlc.close)
            cls.ohlc.linear_reg_ave[term] = cls.calc_linear_reg(term, cls.ohlc.ave_price)
            cls.ohlc.linear_reg_angle_ave[term] = cls.calc_linear_reg_angle(term, cls.ohlc.ave_price)
            cls.ohlc.linear_reg_intercept_ave[term] = cls.calc_linear_reg_intercept(term, cls.ohlc.ave_price)
            cls.ohlc.linear_reg_slope_ave[term] = cls.calc_linear_reg_slope(term, cls.ohlc.ave_price)
            cls.ohlc.stdv_ave[term] = cls.calc_stdv(term, cls.ohlc.ave_price)
            cls.ohlc.var_ave[term] = cls.calc_var(term, cls.ohlc.ave_price)
            cls.ohlc.adx[term] = cls.calc_adx(term, cls.ohlc.high, cls.ohlc.low, cls.ohlc.close)
            cls.ohlc.aroon_os[term] = cls.calc_aroon_os(term, cls.ohlc.high, cls.ohlc.low)
            cls.ohlc.cci[term] = cls.calc_cci(term, cls.ohlc.high, cls.ohlc.low, cls.ohlc.close)
            cls.ohlc.dx[term] = cls.calc_dx(term, cls.ohlc.high, cls.ohlc.low, cls.ohlc.close)
            if term >= 10:
                cls.ohlc.macd[term], cls.ohlc.macdsignal[term], cls.ohlc.macdhist[term] = cls.calc_macd(cls.ohlc.close,int(float(term) / 2.0),term, int(float(term) / 3.0))
                cls.ohlc.macd[term] = list(cls.ohlc.macd[term])
                cls.ohlc.macdsignal[term] = list(cls.ohlc.macdsignal[term])
                cls.ohlc.macdhist[term] = list(cls.ohlc.macdhist[term])
                cls.ohlc.macd_ave[term], cls.ohlc.macdsignal_ave[term], cls.ohlc.macdhist_ave[term] = cls.calc_macd(
                    cls.ohlc.ave_price, int(float(term) / 2.0), term, int(float(term) / 3.0))
                cls.ohlc.macd_ave[term] = list(cls.ohlc.macd_ave[term])
                cls.ohlc.macdsignal_ave[term] = list(cls.ohlc.macdsignal_ave[term])
                cls.ohlc.macdhist_ave[term] = list(cls.ohlc.macdhist_ave[term])
        cls.ohlc.normalized_ave_true_range = cls.calc_normalized_ave_true_range(cls.ohlc.high, cls.ohlc.low,
                                                                                cls.ohlc.close)
        cls.ohlc.three_outside_updown = cls.calc_three_outside_updown(cls.ohlc.open, cls.ohlc.high, cls.ohlc.low,
                                                                      cls.ohlc.close)
        cls.ohlc.breakway = cls.calc_breakway(cls.ohlc.open, cls.ohlc.high, cls.ohlc.low, cls.ohlc.close)
        cls.ohlc.dark_cloud_cover = cls.calc_dark_cloud_cover(cls.ohlc.open, cls.ohlc.high, cls.ohlc.low,
                                                              cls.ohlc.close)
        cls.ohlc.dragonfly_doji = cls.calc_dragonfly_doji(cls.ohlc.open, cls.ohlc.high, cls.ohlc.low, cls.ohlc.close)
        cls.ohlc.updown_sidebyside_white_lines = cls.calc_updown_sidebyside_white_lines(cls.ohlc.open, cls.ohlc.high,
                                                                                        cls.ohlc.low, cls.ohlc.close)
        cls.ohlc.haramisen = cls.calc_haramisen(cls.ohlc.open, cls.ohlc.high, cls.ohlc.low, cls.ohlc.close)
        cls.ohlc.hikkake_pattern = cls.calc_hikkake_pattern(cls.ohlc.open, cls.ohlc.high, cls.ohlc.low, cls.ohlc.close)
        cls.ohlc.neck_pattern = cls.calc_neck_pattern(cls.ohlc.open, cls.ohlc.high, cls.ohlc.low, cls.ohlc.close)
        cls.ohlc.upsidedownside_gap_three_method = cls.calc_upsidedownside_gap_three_method(cls.ohlc.open,
                                                                                            cls.ohlc.high, cls.ohlc.low,
                                                                                            cls.ohlc.close)
        cls.ohlc.sar = cls.calc_sar(cls.ohlc.high, cls.ohlc.low, 0.02, 0.2)
        cls.ohlc.bop = cls.calc_bop(cls.ohlc.open, cls.ohlc.high, cls.ohlc.low, cls.ohlc.close)
        # cls.ohlc.bp, cls.ohlc.sp = cls.calc_pl_ls_points()

        # generate various index
        for term in cls.term_list:
            cls.ohlc.various_makairi['emakairi' + str(term)] = cls.ohlc.ema_kairi[term]
            cls.ohlc.various_makairi['demakairi' + str(term)] = cls.ohlc.dema_kairi[term]
            cls.ohlc.various_diff['emadiff' + str(term)] = cls.ohlc.ema_kairi[term]
            cls.ohlc.various_diff['demadiff' + str(term)] = cls.ohlc.dema_kairi[term]
            cls.ohlc.various_makairi['momkairi' + str(term)] = cls.ohlc.momentum[term]
            cls.ohlc.various_diff['momdiff' + str(term)] = cls.ohlc.momentum[term]
            cls.ohlc.various_makairi['rsikairi' + str(term)] = cls.ohlc.rsi[term]
            cls.ohlc.various_diff['rsidiff' + str(term)] = cls.ohlc.rsi[term]
            cls.ohlc.various_makairi['williams_Rkairi' + str(term)] = cls.ohlc.williams_R[term]
            cls.ohlc.various_diff['williams_Rdiff' + str(term)] = cls.ohlc.williams_R[term]
            cls.ohlc.various_makairi['betakairi' + str(term)] = cls.ohlc.beta[term]
            cls.ohlc.various_diff['betadiff' + str(term)] = cls.ohlc.beta[term]
            cls.ohlc.various_makairi['linear_regkairi' + str(term)] = cls.ohlc.linear_reg[term]
            cls.ohlc.various_diff['linear_regdiff' + str(term)] = cls.ohlc.linear_reg[term]
            cls.ohlc.various_makairi['linear_reg_slopekairi' + str(term)] = cls.ohlc.linear_reg_slope[term]
            cls.ohlc.various_diff['linear_reg_slopediff' + str(term)] = cls.ohlc.linear_reg_slope[term]
            cls.ohlc.various_makairi['adxkairi' + str(term)] = cls.ohlc.adx[term]
            cls.ohlc.various_diff['adxdiff' + str(term)] = cls.ohlc.adx[term]
            cls.ohlc.various_makairi['aroon_oskairi' + str(term)] = cls.ohlc.aroon_os[term]
            cls.ohlc.various_diff['aroon_osdiff' + str(term)] = cls.ohlc.aroon_os[term]
            cls.ohlc.various_makairi['ccikairi' + str(term)] = cls.ohlc.cci[term]
            cls.ohlc.various_diff['ccidiff' + str(term)] = cls.ohlc.cci[term]
            if term >= 10:
                cls.ohlc.various_makairi['macdkairi' + str(term)] = cls.ohlc.macd[term]
                cls.ohlc.various_diff['macddiff' + str(term)] = cls.ohlc.macd[term]
                cls.ohlc.various_makairi['macdsignalkairi' + str(term)] = cls.ohlc.macdsignal[term]
                cls.ohlc.various_diff['macdsignaldiff' + str(term)] = cls.ohlc.macdsignal[term]
                cls.ohlc.various_makairi['macdhistkairi' + str(term)] = cls.ohlc.macdhist[term]
                cls.ohlc.various_diff['macdhistdiff' + str(term)] = cls.ohlc.macdhist[term]
        cls.ohlc.future_side = cls.calc_future_side()
        print('calc all index1 time={}'.format(time.time() - start_time))

    @classmethod
    def generate_raw_df(cls):
        def __change_dict_key(d, col_name):
            newd = dict(map(lambda k: (col_name + str(k), d[k][:]), d.keys()))
            return newd

        '''data_dict = {'dt':cls.ohlc.dt[:], 'open':cls.ohlc.open[:], 'high':cls.ohlc.high[:],'low':cls.ohlc.low[:],
                    'close':cls.ohlc.close[:], 'size':cls.ohlc.size[:], 'normalized_ave_true_range':cls.ohlc.normalized_ave_true_range[:],
                    'sar':cls.ohlc.sar[:],'bop':cls.ohlc.bop[:]}'''
        data_dict = {'dt': cls.ohlc.dt[:], 'open': cls.ohlc.open[:], 'high': cls.ohlc.high[:], 'low': cls.ohlc.low[:],
                     'close': cls.ohlc.close[:], 'size': cls.ohlc.size[:],
                     'normalized_ave_true_range': cls.ohlc.normalized_ave_true_range[:],
                     'three_outside_updown': cls.ohlc.three_outside_updown[:], 'breakway': cls.ohlc.breakway[:],
                     'dark_cloud_cover': cls.ohlc.dark_cloud_cover[:],
                     'dragonfly_doji': cls.ohlc.dragonfly_doji[:],
                     'three_oupdown_sidebyside_white_linesutside_updown': cls.ohlc.updown_sidebyside_white_lines[:],
                     'haramisen': cls.ohlc.haramisen[:], 'haramhikkake_patternisen': cls.ohlc.hikkake_pattern[:],
                     'neck_pattern': cls.ohlc.neck_pattern[:],
                     'upsidedownside_gap_three_method': cls.ohlc.upsidedownside_gap_three_method[:],
                     'sar': cls.ohlc.sar[:], 'bop': cls.ohlc.bop[:]}
        data_dict = {**data_dict, **__change_dict_key(cls.ohlc.ema, 'ema'),
                     **__change_dict_key(cls.ohlc.ema_ave, 'ema_ave'),
                     **__change_dict_key(cls.ohlc.ema_kairi, 'ema_kairi'),
                     **__change_dict_key(cls.ohlc.dema_kairi, 'dema_kairi'),
                     **__change_dict_key(cls.ohlc.ema_gra, 'ema_gra'), **__change_dict_key(cls.ohlc.dema, 'dema'),
                     **__change_dict_key(cls.ohlc.dema_ave, 'dema_ave'),
                     **__change_dict_key(cls.ohlc.dema_gra, 'dema_gra'),
                     **__change_dict_key(cls.ohlc.midprice, 'midprice'),
                     **__change_dict_key(cls.ohlc.momentum, 'momentum'),
                     **__change_dict_key(cls.ohlc.momentum_ave, 'momentum_ave'),
                     **__change_dict_key(cls.ohlc.rate_of_change, 'rate_of_change'),
                     **__change_dict_key(cls.ohlc.rsi, 'rsi'), **__change_dict_key(cls.ohlc.williams_R, 'williams_R'),
                     **__change_dict_key(cls.ohlc.beta, 'beta'), **__change_dict_key(cls.ohlc.tsf, 'tsf'),
                     **__change_dict_key(cls.ohlc.correl, 'correl'),
                     **__change_dict_key(cls.ohlc.linear_reg, 'linear_reg'),
                     **__change_dict_key(cls.ohlc.linear_reg_angle, 'linear_reg_angle'),
                     **__change_dict_key(cls.ohlc.linear_reg_intercept, 'linear_reg_intercept'),
                     **__change_dict_key(cls.ohlc.linear_reg_slope, 'linear_reg_slope'),
                     **__change_dict_key(cls.ohlc.stdv, 'stdv'), **__change_dict_key(cls.ohlc.var, 'var'),
                     **__change_dict_key(cls.ohlc.linear_reg_ave, 'linear_reg_ave'),
                     **__change_dict_key(cls.ohlc.linear_reg_angle_ave, 'linear_reg_angle_ave'),
                     **__change_dict_key(cls.ohlc.linear_reg_intercept_ave, 'linear_reg_intercept_ave'),
                     **__change_dict_key(cls.ohlc.linear_reg_slope_ave, 'linear_reg_slope_ave'),
                     **__change_dict_key(cls.ohlc.stdv_ave, 'stdv_ave'),
                     **__change_dict_key(cls.ohlc.var_ave, 'var_ave'), **__change_dict_key(cls.ohlc.adx, 'adx'),
                     **__change_dict_key(cls.ohlc.aroon_os, 'aroon_os'),
                     **__change_dict_key(cls.ohlc.cci, 'cci'), **__change_dict_key(cls.ohlc.dx, 'dx'),
                     **__change_dict_key(cls.ohlc.macd, 'macd'),
                     **__change_dict_key(cls.ohlc.macdsignal, 'macdsignal'),
                     **__change_dict_key(cls.ohlc.macdhist, 'macdhist'),
                     **__change_dict_key(cls.ohlc.macd_ave, 'macd_ave'),
                     **__change_dict_key(cls.ohlc.macdsignal_ave, 'macdsignal_ave'),
                     **__change_dict_key(cls.ohlc.macdhist_ave, 'macdhist_ave'),
                     **__change_dict_key(cls.ohlc.various_makairi, 'various_makairi'),
                     **__change_dict_key(cls.ohlc.various_diff, 'various_diff')}
        df = pd.DataFrame.from_dict(data_dict)
        return df

    '''
    dema, adx, macdはnum_term * 2くらいnanが発生する
    print(df.isnull().sum())
    '''

    @classmethod
    def generate_df(cls):
        def __change_dict_key(d, col_name):
            newd = dict(map(lambda k: (col_name + '_' + str(k), d[k][cut_size:end]), d.keys()))
            return newd

        start_time = time.time()
        cut_size = cls.term_list[-1] * 2
        end = len(cls.ohlc.close) - 10  # remove last 700min data as future bp / sp maybe not precise in
        data_dict = {'dt': cls.ohlc.dt[cut_size:end], 'open': cls.ohlc.open[cut_size:end],
                     'high': cls.ohlc.high[cut_size:end], 'low': cls.ohlc.low[cut_size:end],
                     'close': cls.ohlc.close[cut_size:end], 'size': cls.ohlc.size[cut_size:end],
                     'normalized_ave_true_range': cls.ohlc.normalized_ave_true_range[cut_size:end],
                     'three_outside_updown': cls.ohlc.three_outside_updown[cut_size:end],
                     'breakway': cls.ohlc.breakway[cut_size:end],
                     'dark_cloud_cover': cls.ohlc.dark_cloud_cover[cut_size:end],
                     'dragonfly_doji': cls.ohlc.dragonfly_doji[cut_size:end],
                     'three_oupdown_sidebyside_white_linesutside_updown': cls.ohlc.updown_sidebyside_white_lines[
                                                                          cut_size:end],
                     'haramisen': cls.ohlc.haramisen[cut_size:end],
                     'haramhikkake_patternisen': cls.ohlc.hikkake_pattern[cut_size:end],
                     'neck_pattern': cls.ohlc.neck_pattern[cut_size:end],
                     'upsidedownside_gap_three_method': cls.ohlc.upsidedownside_gap_three_method[cut_size:end],
                     'sar': cls.ohlc.sar[cut_size:end], 'bop': cls.ohlc.bop[cut_size:end]}
        data_dict = {**data_dict, **__change_dict_key(cls.ohlc.ema, 'ema'),
                     **__change_dict_key(cls.ohlc.ema_ave, 'ema_ave'),
                     **__change_dict_key(cls.ohlc.ema_kairi, 'ema_kairi'),
                     **__change_dict_key(cls.ohlc.dema_kairi, 'dema_kairi'),
                     **__change_dict_key(cls.ohlc.ema_gra, 'ema_gra'), **__change_dict_key(cls.ohlc.dema, 'dema'),
                     **__change_dict_key(cls.ohlc.dema_ave, 'dema_ave'),
                     **__change_dict_key(cls.ohlc.dema_gra, 'dema_gra'),
                     **__change_dict_key(cls.ohlc.midprice, 'midprice'),
                     **__change_dict_key(cls.ohlc.momentum, 'momentum'),
                     **__change_dict_key(cls.ohlc.momentum_ave, 'momentum_ave'),
                     **__change_dict_key(cls.ohlc.rate_of_change, 'rate_of_change'),
                     **__change_dict_key(cls.ohlc.rsi, 'rsi'), **__change_dict_key(cls.ohlc.williams_R, 'williams_R'),
                     **__change_dict_key(cls.ohlc.beta, 'beta'), **__change_dict_key(cls.ohlc.tsf, 'tsf'),
                     **__change_dict_key(cls.ohlc.correl, 'correl'),
                     **__change_dict_key(cls.ohlc.linear_reg, 'linear_reg'),
                     **__change_dict_key(cls.ohlc.linear_reg_angle, 'linear_reg_angle'),
                     **__change_dict_key(cls.ohlc.linear_reg_intercept, 'linear_reg_intercept'),
                     **__change_dict_key(cls.ohlc.linear_reg_slope, 'linear_reg_slope'),
                     **__change_dict_key(cls.ohlc.stdv, 'stdv'), **__change_dict_key(cls.ohlc.var, 'var'),
                     **__change_dict_key(cls.ohlc.linear_reg_ave, 'linear_reg_ave'),
                     **__change_dict_key(cls.ohlc.linear_reg_angle_ave, 'linear_reg_angle_ave'),
                     **__change_dict_key(cls.ohlc.linear_reg_intercept_ave, 'linear_reg_intercept_ave'),
                     **__change_dict_key(cls.ohlc.linear_reg_slope_ave, 'linear_reg_slope_ave'),
                     **__change_dict_key(cls.ohlc.stdv_ave, 'stdv_ave'),
                     **__change_dict_key(cls.ohlc.var_ave, 'var_ave'), **__change_dict_key(cls.ohlc.adx, 'adx'),
                     **__change_dict_key(cls.ohlc.aroon_os, 'aroon_os'),
                     **__change_dict_key(cls.ohlc.cci, 'cci'), **__change_dict_key(cls.ohlc.dx, 'dx'),
                     **__change_dict_key(cls.ohlc.macd, 'macd'),
                     **__change_dict_key(cls.ohlc.macdsignal, 'macdsignal'),
                     **__change_dict_key(cls.ohlc.macdhist, 'macdhist'),
                     **__change_dict_key(cls.ohlc.macd_ave, 'macd_ave'),
                     **__change_dict_key(cls.ohlc.macdsignal_ave, 'macdsignal_ave'),
                     **__change_dict_key(cls.ohlc.macdhist_ave, 'macdhist_ave'),
                     **__change_dict_key(cls.ohlc.various_makairi, 'various_makairi'),
                     **__change_dict_key(cls.ohlc.various_diff, 'various_diff')}
        data_dict['bpsp'] = cls.ohlc.bpsp[cut_size:end]
        #        data_dict['bp'] = cls.ohlc.bp[cut_size:end]
        #        data_dict['sp'] = cls.ohlc.sp[cut_size:end]
        df = pd.DataFrame.from_dict(data_dict)
        return df

    @classmethod
    def generate_term_list(cls, num):
        term_list = []
        category_n = [5, 50, 200]
        term_list.extend(list(np.round(np.linspace(category_n[0], category_n[0] * num, num))))
        term_list.extend(list(np.round(np.linspace(category_n[1] + (category_n[0] * num),
                                                   category_n[1] + (category_n[0] * num) + category_n[1] * num), num)))
        term_list.extend(list(np.round(
            np.linspace(category_n[2] + category_n[1] + (category_n[0] * num) + (category_n[1] * num),
                        category_n[2] + (category_n[1] * num) + category_n[2] * num), num)))
        return list(map(int, term_list))

    @classmethod
    def generate_term_list2(cls, max_term):
        term_list = []
        term_list = list(np.linspace(10, max_term, num=(max_term - 10) / 20))
        return list(map(int, term_list))

    @classmethod
    def detect_max_term(cls):
        max_term = 0
        cols = []
        with open("./Model/bpsp_cols.csv", "r") as f:
            reader = csv.reader(f)
            for r in reader:
                cols.append(r)
        for col in cols[0]:
            if ':' in col:
                if max_term < int(col.split(':')[1]):
                    max_term = int(col.split(':')[1])
        return max_term

    # kairi of data
    @classmethod
    def generate_makairi(cls, data, ma_term):
        ma = np.array(list(ta.MA(np.array(data, dtype='f8'), timeperiod=ma_term)), dtype='f8')
        return list(map(lambda c, e: (c - e) / e, np.array(data, dtype='f8'), ma))

    @classmethod
    def generate_diff(cls, data):
        return list(ta.ROC(np.array(data, dtype='f8'), timeperiod=1))
        # return [0] + list(np.diff(np.array(data, dtype='f8')))

    @classmethod
    def calc_future_side2(cls):
        future_side = []
        num_buy = 0
        num_sell = 0
        num_no = 0
        num_both = 0
        for i in range(len(cls.ohlc.close) - cls.kijun_period):
            buy_max = 0
            sell_max = 0
            entry_p = cls.ohlc.close[i]
            kijun_price = cls.ohlc.close[i] * cls.kijun_ratio
            for j in range(cls.kijun_period):
                buy_max = max(buy_max, cls.ohlc.close[i + j] - entry_p)
                sell_max = max(sell_max, entry_p - cls.ohlc.close[i + j])
            if buy_max >= kijun_price and sell_max >= kijun_price:
                future_side.append('both')
                num_both += 1
            elif buy_max >= kijun_price and sell_max < kijun_price:
                future_side.append('buy')
                num_buy += 1
            elif buy_max < kijun_price and sell_max >= kijun_price:
                future_side.append('sell')
                num_sell += 1
            elif buy_max < kijun_price and sell_max < kijun_price:
                future_side.append('no')
                num_no += 1

        print('future_side allocation in Market Data:')
        tsum = float(len(future_side))
        print('no:', round(float(num_no) / tsum, 4), 'buy:', round(float(num_buy) / tsum, 4), 'sell:',
              round(float(num_sell) / tsum, 4), 'both:', round(float(num_both) / tsum, 4))
        return future_side


    @classmethod
    def remove_all_correlated_cols4(cls, df, corr_kijun):
        print('removing all correlated columns..')
        start_time = time.time()
        dff = df.copy()
        dff.drop(['dt', 'future_side'], axis=1, inplace=True)
        cols = list(dff.columns)
        df_res = df.copy()
        corr_matrix = np.corrcoef(np.array(dff).transpose())
        df_new = pd.DataFrame(data=corr_matrix, index=cols, columns=cols, dtype='float')
        upper = df_new.where(np.triu(np.ones(df_new.shape), k=1).astype(np.bool))
        to_drop = [column for column in upper.columns if any(upper[column] > corr_kijun)]
        excludes = ['dt', 'open', 'high', 'low', 'close', 'close_change', 'future_side', 'size']
        for ex in excludes:
            if ex in to_drop:
                to_drop.remove(ex)
        df_res.drop(to_drop, axis=1, inplace=True)
        print('removed ' + str(len(to_drop)) + ' colums', 'remaining col=' + str(len(df_res.columns)))
        print('completed remove all correlated cols4. time=', time.time() - start_time)
        return df_res


    @classmethod
    def remove_price_dependent_cols2(cls, df, corr_kijun):
        print('removing all price dependent columns..')
        dff = df.copy()
        df_res = df.copy()
        dff.drop(['dt', 'future_side'], axis=1, inplace=True)
        cols = list(dff.columns)
        to_drop = []
        for col in cols:
            corr = np.corrcoef(dff['close'], dff[col], rowvar=False)[1][0]
            if corr > corr_kijun:
                to_drop.append(col)
        excludes = ['dt', 'open', 'high', 'low', 'close', 'future_side', 'size']
        for ex in excludes:
            if ex in to_drop:
                to_drop.remove(ex)
        df_res.drop(to_drop, axis=1, inplace=True)
        print('removed ' + str(len(to_drop)) + ' colums', 'remaining col=' + str(len(df.columns)))
        return df_res


    # 5min, 15min, 1hの足でのヒゲにしたほうがいい
    @classmethod
    def calc_uwahige_length(cls):
        return list(map(lambda i: (cls.ohlc.high[i] - cls.ohlc.close[i]) / cls.ohlc.open[i] if cls.ohlc.close[i] > cls.ohlc.open[i] else (cls.ohlc.high[i] - cls.ohlc.open[i]) / cls.ohlc.open[i], range(0, len(cls.ohlc.close))))

    @classmethod
    def calc_5min_uwahige_length(cls):
        return list(map(lambda i: (cls.ohlc.high[i] - cls.ohlc.close[i]) / cls.ohlc.open[i] if cls.ohlc.close[i] > cls.ohlc.open[i] else (cls.ohlc.high[i] - cls.ohlc.open[i]) / cls.ohlc.open[i], range(0, len(cls.ohlc.close))))

    @classmethod
    def calc_shitahige_length(cls):
        return list(map(lambda i: (cls.ohlc.open[i] - cls.ohlc.low[i]) / cls.ohlc.open[i] if cls.ohlc.close[i] > cls.ohlc.open[i] else (cls.ohlc.close[i] - cls.ohlc.low[i]) / cls.ohlc.open[i], range(0, len(cls.ohlc.close))))

    @classmethod
    def calc_high_kairi(cls, term):
        max_list = []
        max_list = list(map(lambda i: max(cls.ohlc.high[i:i + term]), range(0, len(cls.ohlc.high) - term)))
        kairi = [0] * term
        kairi.extend(list(map(lambda i: max_list[i] / cls.ohlc.close[i + term], range(0, len(max_list)))))
        return kairi

    @classmethod
    def calc_low_kairi(cls, term):
        low_list = []
        low_list = list(map(lambda i: max(cls.ohlc.low[i:i + term]), range(0, len(cls.ohlc.low) - term)))
        kairi = [0] * term
        kairi.extend(list(map(lambda i: low_list[i] / cls.ohlc.close[i + term], range(0, len(low_list)))))
        return kairi

    @classmethod
    def calc_ema(cls, term):
        return list(ta.EMA(np.array(cls.ohlc.close, dtype='f8'), timeperiod=term))

    @classmethod
    def calc_ema_size(cls, term):
        return list(ta.EMA(np.array(cls.ohlc.size, dtype='f8'), timeperiod=term))

    @classmethod
    def calc_ema_kairi(cls, term):
        return list(map(lambda c, e: (c - e) / e, np.array(cls.ohlc.close, dtype='f8'), np.array(cls.ohlc.index_data_dict['ema:' + str(term)], dtype='f8')))

    @classmethod
    def calc_dema_kairi(cls, term):
        return list(map(lambda c, d: (c - d) / d, np.array(cls.ohlc.close, dtype='f8'), np.array(cls.ohlc.index_data_dict['dema:' + str(term)], dtype='f8')))

    @classmethod
    def calc_ema_gra(cls, term):
        return list(pd.Series(cls.ohlc.index_data_dict['ema:' + str(term)]).diff())

    @classmethod
    def calc_dema_gra(cls, term):
        return list(pd.Series(cls.ohlc.index_data_dict['dema:' + str(term)]).diff())

    @classmethod
    def calc_dema(cls, term):
        return list(ta.DEMA(np.array(cls.ohlc.close, dtype='f8'), timeperiod=term))

    # termの2倍くらいnanが続く
    @classmethod
    def calc_adx(cls, term):
        return list(
            ta.ADX(np.array(cls.ohlc.high, dtype='f8'), np.array(cls.ohlc.low, dtype='f8'), np.array(cls.ohlc.close, dtype='f8'), timeperiod=term))

    @classmethod
    def calc_aroon_os(cls, term):
        return list(ta.AROONOSC(np.array(cls.ohlc.high, dtype='f8'), np.array(cls.ohlc.low, dtype='f8'), timeperiod=term))

    @classmethod
    def calc_cci(cls, term):
        return list(
            ta.CCI(np.array(cls.ohlc.high, dtype='f8'), np.array(cls.ohlc.low, dtype='f8'), np.array(cls.ohlc.close, dtype='f8'), timeperiod=term))

    @classmethod
    def calc_dx(cls, term):
        return list(
            ta.DX(np.array(cls.ohlc.high, dtype='f8'), np.array(cls.ohlc.low, dtype='f8'), np.array(cls.ohlc.close, dtype='f8'), timeperiod=term))

    @classmethod
    def calc_midprice(cls, term, high, low):
        return list(ta.MIDPRICE(np.array(high, dtype='f8'), np.array(low, dtype='f8'), timeperiod=term))

    @classmethod
    def calc_macd(cls, term):
        slowperiod = term
        fastperiod = int(term / 2.0)
        signalperiod = int(term / 3.0)
        macd, signal, hist = ta.MACD(np.array(cls.ohlc.close, dtype='f8'), np.array(fastperiod, dtype='i8'), np.array(slowperiod, dtype='i8'), np.array(signalperiod, dtype='i8'))
        return macd

    @classmethod
    def calc_macd_signal(cls, term):
        slowperiod = term
        fastperiod = int(term / 2.0)
        signalperiod = int(term / 3.0)
        macd, signal, hist = ta.MACD(np.array(cls.ohlc.close, dtype='f8'), np.array(fastperiod, dtype='i8'), np.array(slowperiod, dtype='i8'),
                                     np.array(signalperiod, dtype='i8'))
        return signal

    @classmethod
    def calc_macd_hist(cls, term):
        slowperiod = term
        fastperiod = int(term / 2.0)
        signalperiod = int(term / 3.0)
        macd, signal, hist = ta.MACD(np.array(cls.ohlc.close, dtype='f8'), np.array(fastperiod, dtype='i8'), np.array(slowperiod, dtype='i8'),
                                     np.array(signalperiod, dtype='i8'))
        return hist

    @classmethod
    def calc_momentum(cls, term):
        return list(ta.MOM(np.array(cls.ohlc.close, dtype='f8'), timeperiod=term))

    @classmethod
    def calc_momentum_size(cls, term):
        return list(ta.MOM(np.array(cls.ohlc.size, dtype='f8'), timeperiod=term))

    @classmethod
    def calc_rate_of_change(cls, term):
        return list(ta.ROC(np.array(cls.ohlc.close, dtype='f8'), timeperiod=term))

    @classmethod
    def calc_rsi(cls, term):
        return list(ta.RSI(np.array(cls.ohlc.close, dtype='f8'), timeperiod=term))

    @classmethod
    def calc_williams_R(cls, term):
        return list(ta.WILLR(np.array(cls.ohlc.high, dtype='f8'), np.array(cls.ohlc.low, dtype='f8'), np.array(cls.ohlc.close, dtype='f8'), timeperiod=term))

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
    def calc_stdv_size(cls, term):
        return list(ta.STDDEV(np.array(cls.ohlc.size, dtype='f8'), timeperiod=term, nbdev=1))

    @classmethod
    def calc_var(cls, term):
        return list(ta.VAR(np.array(cls.ohlc.close, dtype='f8'), timeperiod=term, nbdev=1))

    @classmethod
    def calc_normalized_ave_true_range(cls):
        return list(ta.NATR(np.array(cls.ohlc.high, dtype='f8'), np.array(cls.ohlc.low, dtype='f8'), np.array(cls.ohlc.close, dtype='f8')))

    @classmethod
    def calc_three_outside_updown(cls):
        return list(ta.CDL3OUTSIDE(np.array(cls.ohlc.open, dtype='f8'), np.array(cls.ohlc.high, dtype='f8'), np.array(cls.ohlc.low, dtype='f8'),
                                   np.array(cls.ohlc.close, dtype='f8')))

    @classmethod
    def calc_breakway(cls):
        return list(ta.CDLBREAKAWAY(np.array(cls.ohlc.open, dtype='f8'), np.array(cls.ohlc.high, dtype='f8'), np.array(cls.ohlc.low, dtype='f8'),
                                    np.array(cls.ohlc.close, dtype='f8')))

    @classmethod
    def calc_dark_cloud_cover(cls):
        return list(ta.CDLDARKCLOUDCOVER(np.array(cls.ohlc.open, dtype='f8'), np.array(cls.ohlc.high, dtype='f8'), np.array(cls.ohlc.low, dtype='f8'),
                                         np.array(cls.ohlc.close, dtype='f8'), penetration=0))

    @classmethod
    def calc_dragonfly_doji(cls):
        return list(ta.CDLDRAGONFLYDOJI(np.array(cls.ohlc.open, dtype='f8'), np.array(cls.ohlc.high, dtype='f8'), np.array(cls.ohlc.low, dtype='f8'),
                                        np.array(cls.ohlc.close, dtype='f8')))

    @classmethod
    def calc_updown_sidebyside_white_lines(cls):
        return list(
            ta.CDLGAPSIDESIDEWHITE(np.array(cls.ohlc.open, dtype='f8'), np.array(cls.ohlc.high, dtype='f8'), np.array(cls.ohlc.low, dtype='f8'),
                                   np.array(cls.ohlc.close, dtype='f8')))

    @classmethod
    def calc_haramisen(cls):
        return list(ta.CDLHARAMI(np.array(cls.ohlc.open, dtype='f8'), np.array(cls.ohlc.high, dtype='f8'), np.array(cls.ohlc.low, dtype='f8'), np.array(cls.ohlc.close, dtype='f8')))

    @classmethod
    def calc_hikkake_pattern(cls):
        return list(ta.CDLHIKKAKEMOD(np.array(cls.ohlc.open, dtype='f8'), np.array(cls.ohlc.high, dtype='f8'), np.array(cls.ohlc.low, dtype='f8'), np.array(cls.ohlc.close, dtype='f8')))

    @classmethod
    def calc_neck_pattern(cls):
        return list(ta.CDLINNECK(np.array(cls.ohlc.open, dtype='f8'), np.array(cls.ohlc.high, dtype='f8'), np.array(cls.ohlc.low, dtype='f8'), np.array(cls.ohlc.close, dtype='f8')))

    @classmethod
    def calc_sar(cls):
        accelation = 0.02
        maximum = 0.2
        return list(ta.SAR(np.array(cls.ohlc.high, dtype='f8'), np.array(cls.ohlc.low, dtype='f8'), np.array(accelation, dtype='f8'), np.array(maximum, dtype='f8')))

    @classmethod
    def calc_bop(cls):
        return list(ta.BOP(np.array(cls.ohlc.open, dtype='f8'), np.array(cls.ohlc.high, dtype='f8'), np.array(cls.ohlc.low, dtype='f8'), np.array(cls.ohlc.close, dtype='f8')))

    @classmethod
    def calc_upsidedownside_gap_three_method(cls):
        return list(ta.CDLXSIDEGAP3METHODS(np.array(cls.ohlc.open, dtype='f8'), np.array(cls.ohlc.high, dtype='f8'), np.array(cls.ohlc.low, dtype='f8'), np.array(cls.ohlc.close, dtype='f8')))


if __name__ == '__main__':
    SystemFlg.initialize()
    OneMinMarketData.initialize_for_marketdata_test()
