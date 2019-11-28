import lightgbm as lgb
from sklearn.model_selection import train_test_split
from SystemFlg import SystemFlg
from OneMinMarketData import OneMinMarketData
from RealtimeWSAPI import TickData
import numpy as np
import pandas as pd
import pickle
import threading
import time
import os
import datetime


class LgbModel:
    def __init__(self):
        self.model = None
        self.pred = -1
        self.lock_pred = threading.Lock()
        self.upper_kijun = 0.5
        self.pt_kijun = 50
        self.lock_pred = threading.Lock()
        with open('./Model/lgb_bpsp_model.dat', mode='rb') as f:
            self.model = pickle.load(f)

        self.num_buy = 0
        self.num_sell = 0
        self.total_pl = 0
        self.unrealized_pl = 0
        self.realized_pl = 0
        self.num_win = 0
        self.win_rate = 0
        self.entry_price = 0
        self.posi = ''
        self.accuracy_ratio = 0
        self.pre_pred = -1
        self.num = -1
        self.num_pred_correct = 0
        self.fee = 0.00075

        if os.path.exists('./Data/data.csv'):
            os.remove('./Data/data.csv')


        th = threading.Thread(target=self.main_thread)
        th.start()

    def set_pred(self,pred):
        with self.lock_pred:
            self.pred = pred

    def write_df_pred(self, df, pred):
        df = df.assign(dt=datetime.datetime.now())
        df = df.assign(prediction=pred)
        if os.path.exists('./Data/data.csv'):
            df.to_csv('./Data/data.csv', mode='a', header=False, index=False)
        else:
            df.to_csv('./Data/data.csv',index=False)


    def sim(self, pred, pt_kijun):
        if self.posi == '' and (pred == 1 or pred == 2):
            self.posi = 'buy' if pred == 1 else 'sell'
            self.entry_price = OneMinMarketData.ohlc.close[-1]
        elif self.posi =='buy' and pred == 2:
            self.num_buy += 1
            self.posi = 'sell'
            pl = float(TickData.get_ltp()) - ((self.fee+1) * self.entry_price)
            if pl > 0:
                self.num_win += 1
            self.realized_pl += pl
            self.unrealized_pl = 0
            self.entry_price = float(TickData.get_ltp())
        elif self.posi =='sell' and pred == 1:
            self.num_sell += 1
            self.posi = 'buy'
            pl = (1-self.fee) * self.entry_price - float(TickData.get_ltp())
            if pl > 0:
                self.num_win += 1
            self.realized_pl += pl
            self.unrealized_pl = 0
            self.entry_price = float(TickData.get_ltp())
        elif self.posi == 'buy' and (pred == 0 or pred == 3):
            if OneMinMarketData.ohlc.high[-1] - self.entry_price > pt_kijun:
                self.posi == ''
                self.num_buy += 1
                pl = float(TickData.get_ltp()) - ((self.fee + 1) * self.entry_price)
                if pl > 0:
                    self.num_win += 1
                self.realized_pl += pl
                self.unrealized_pl = 0
                self.entry_price = 0
            else:
                self.unrealized_pl = float(TickData.get_ltp()) - ((self.fee + 1) * self.entry_price)
        elif self.posi == 'sell' and (pred == 0 or pred == 3):
            if self.entry_price - OneMinMarketData.ohlc.high[-1] > pt_kijun:
                self.posi == ''
                self.num_sell += 1
                pl = (1 - self.fee) * self.entry_price - float(TickData.get_ltp())
                if pl > 0:
                    self.num_win += 1
                self.total_pl += pl
                self.entry_price = 0
            else:
                self.unrealized_pl = (1 - self.fee) * self.entry_price - float(TickData.get_ltp())
        self.total_pl = self.realized_pl + self.unrealized_pl

        self.num += 1
        if self.num_win > 0:
            self.win_rate = round(self.num_win / (self.num_buy + self.num_sell), 4)
        self.pre_pred = pred
        print('pl=', self.total_pl, 'posi=', self.posi, 'num buy=',self.num_buy, 'num sell', self.num_sell, 'entry price=', self.entry_price, 'win rate=', self.win_rate)


    def main_thread(self):
        ini_data_flg = False #flg for market data initialization
        while SystemFlg.get_system_flg():
            while ini_data_flg is False: #wait for initial update of the market data
                if len(OneMinMarketData.ohlc.dt) > 0:
                    ini_data_flg = True
                time.sleep(0.5)

            time.sleep(0.5)
            if OneMinMarketData.get_flg_ohlc_update():
                df = OneMinMarketData.get_df()
                if df is not None:
                    if True in df.isnull().any():
                        print('null is in df!')
                        self.set_pred(-1)
                    else:
                        self.set_pred(self.bpsp_prediction(self.model, df, self.upper_kijun)[-1])
                        OneMinMarketData.set_flg_ohlc_update(False)
                        print('prediction = ', self.pred)
                        self.sim(self.pred, self.pt_kijun)
                        self.write_df_pred(df, self.pred)

            '''
            df = OneMinMarketData.get_df()
            if df is not None:
                dt = df['dt'].iloc[-1]
                if dt.minute == self.next_min:
                    df = df.drop(['dt'], axis =1)
                    self.set_pred(self.bp_prediciton(self.model, df, self.upper_kijun)[-1])
                    self.next_min = int(dt.minute) +1 if dt.minute != 59 else 0
                    OneMinMarketData.set_pred(self.pred)
                    OneMinMarketData.set_flg_ohlc_update(False)
                    print('prediction = ', self.pred, 'next min=',self.next_min)
                    self.sim(self.pred)
                    '''
        print('Lgb main thread ended.')


    def generate_bpsp_data(self, df: pd.DataFrame, train_size=0.6, valid_size=0.2):
        dfx = None
        dfy = None
        dfx = df.drop(['dt', 'size', 'bpsp'], axis=1)
        dfy = df['bpsp']
        dfy.columns = ['bpsp']
        train_x, test_x, train_y, test_y = train_test_split(dfx, dfy, train_size=train_size, shuffle=False)

        # generate training data to include same num of buy / sell bpsp
        ndf = df.iloc[:len(train_x)]
        buy_df = ndf[ndf.bpsp == 1]
        sell_df = ndf[ndf.bpsp == 0]
        new_train_df = df.copy()
        if len(buy_df) > len(sell_df):
            selected = sell_df.sample(n=len(buy_df) - len(sell_df))
            new_train_df = new_train_df.append(selected)
        else:
            selected = buy_df.sample(n=len(sell_df) - len(buy_df))
            new_train_df = new_train_df.append(selected)

        train_x, valid_x, train_y, valid_y = train_test_split(new_train_df.drop(['dt', 'size', 'bpsp'], axis=1),
                                                              new_train_df['bpsp'], train_size=train_size,
                                                              shuffle=False)
        train_y.columns = ['bpsp']
        valid_y.columns = ['bpsp']

        print('buy sell point data description:')
        print('train_x', train_x.shape)
        print('train_y', train_y.shape)
        print('test_x', test_x.shape)
        print('test_y', test_y.shape)
        print('valid_x', valid_x.shape)
        print('valid_y', valid_y.shape)
        return train_x, test_x, train_y, test_y, valid_x, valid_y



    def generate_bpsp_data2(self, train_df, test_df, valid_size=0.2):
        train_df['future_side'] = train_df['future_side'].map({'no': 0, 'buy': 1, 'sell': 2, 'both': 3}).astype(int)
        test_df['future_side'] = test_df['future_side'].map({'no': 0, 'buy': 1, 'sell': 2, 'both': 3}).astype(int)
        print('train / valid period=', train_df['dt'].iloc[0], ' - ', train_df['dt'].iloc[-1])
        print('test period=', test_df['dt'].iloc[0], ' - ', test_df['dt'].iloc[-1])

        # generate training data to include same num of buy / sell bpsp
        buy_df = train_df[train_df.future_side == 1]
        sell_df = train_df[train_df.future_side == 2]
        no_df = train_df[train_df.future_side == 0]
        both_df = train_df[train_df.future_side == 3]
        max_data = max([len(buy_df), len(sell_df), len(no_df), len(both_df)])
        new_train_df = pd.DataFrame()
        if max_data > len(buy_df):
            selected = buy_df.sample(n=max_data - len(buy_df), replace=True)
            new_train_df = new_train_df.append(selected)
            new_train_df = new_train_df.append(buy_df)
        else:
            new_train_df = buy_df
        if max_data > len(sell_df):
            selected = sell_df.sample(n=max_data - len(sell_df), replace=True)
            new_train_df = new_train_df.append(selected)
            new_train_df = new_train_df.append(sell_df)
        else:
            new_train_df = new_train_df.append(sell_df)
        if max_data > len(no_df):
            selected = no_df.sample(n=max_data - len(no_df), replace=True)
            new_train_df = new_train_df.append(selected)
            new_train_df = new_train_df.append(no_df)
        else:
            new_train_df = new_train_df.append(no_df)
        if max_data > len(both_df):
            selected = both_df.sample(n=max_data - len(both_df), replace=True)
            new_train_df = new_train_df.append(selected)
        else:
            new_train_df = new_train_df.append(both_df)
            new_train_df = new_train_df.append(both_df)

        new_train_df = new_train_df.sample(frac=1)
        train_x, valid_x, train_y, valid_y = train_test_split(new_train_df.drop(['size', 'future_side'], axis=1),
                                                              new_train_df['future_side'],
                                                              train_size=(1.0 - valid_size), shuffle=True)
        train_y.columns = ['future_side']
        valid_y.columns = ['future_side']
        test_x = test_df.drop(['size', 'future_side'], axis=1)
        test_y = test_df['future_side']
        test_y.columns = ['future_side']

        self.check_train_test_index_duplication(train_x, test_x)
        print('buy sell point data description:')
        print('train_x', train_x.shape)
        print('train_y', train_y.shape)
        print('test_x', test_x.shape)
        print('test_y', test_y.shape)
        print('valid_x', valid_x.shape)
        print('valid_y', valid_y.shape)
        return train_x, test_x, train_y, test_y, valid_x, valid_y

    def generate_bsp_data_no_random(self, df: pd.DataFrame, side, train_size=0.6, valid_size=0.2):
        dfx = None
        dfy = None
        col_name = 'bp' if side == 'buy' else 'sp'
        dfx = df.drop(['dt', 'size', col_name], axis=1)
        dfy = df[col_name]
        dfy.columns = [col_name]
        train_x, test_x, train_y, test_y = train_test_split(dfx, dfy, train_size=train_size, shuffle=False)
        count_buy_in_train = train_y.values.sum()
        non_buy_list = []
        buy_list = []

        for i in range(len(train_y)):  # train_y = 0のdataをリスト化
            if train_y.iloc[i] == 0:
                non_buy_list.append(train_x.iloc[i])
            elif train_y.iloc[i] == 1:
                buy_list.append(train_x.iloc[i])
        if len(buy_list) != count_buy_in_train:
            print('len(buy_list) is not matched with count_buy_in_train !!')
        new_train_df = pd.DataFrame()
        new_train_df = new_train_df.append(non_buy_list)
        num = len(non_buy_list) // len(buy_list)
        for i in range(num):
            new_train_df = new_train_df.append(buy_list)
        num = len(non_buy_list) % len(buy_list)
        amari = int(round(len(buy_list) * num))
        new_train_df = new_train_df.append(buy_list[:amari])
        new_buy_points = [0] * len(non_buy_list)
        new_buy_points.extend([1] * (len(new_train_df) - len(non_buy_list)))
        if side == 'buy':
            new_train_df = new_train_df.assign(bp=new_buy_points)
        else:
            new_train_df = new_train_df.assign(sp=new_buy_points)
        train_y = new_train_df[col_name]
        new_train_df = new_train_df.drop([col_name], axis=1)
        train_xx, valid_x, train_yy, valid_y = train_test_split(new_train_df, train_y, train_size=1.0 - valid_size,
                                                                random_state=42)
        print('buy sell point data description:')
        print('side=', side)
        print('train_x', train_xx.shape)
        print('train_y', train_yy.shape)
        print('test_x', test_x.shape)
        print('test_y', test_y.shape)
        print('valid_x', valid_x.shape)
        print('valid_y', valid_y.shape)
        return train_xx, test_x, train_yy, test_y, valid_x, valid_y

    def train(self, train_x, train_y):
        # print('training data description')
        # print('train_x:',train_x.shape)
        # print('train_y:',train_y.shape)
        train_start_ind = OneMinMarketData.check_matched_index(train_x)
        print('train period:', OneMinMarketData.ohlc.dt[train_start_ind],
              OneMinMarketData.ohlc.dt[train_start_ind + len(train_y)])
        train = lgb.Dataset(train_x.values.astype(np.float32), train_y.values.astype(np.float32))
        lgbm_params = {
            'objective': 'multiclass',
            'num_class': 4,
            'boosting': 'dart',
            'tree_learner': 'data',
            'learning_rate': 0.05,
            'num_iterations': 200,
            #            'device':'gpu',
        }
        model = lgb.train(lgbm_params, train)
        return model

    def train_params(self, train_x, train_y, params):
        # print('training data description')
        # print('train_x:',train_x.shape)
        # print('train_y:',train_y.shape)
        train = lgb.Dataset(train_x.values.astype(np.float32), train_y.values.astype(np.float32))
        model = lgb.train(params, train)
        return model

    def load_model(self):
        model_buy = None
        model_sell = None
        with open('/content/drive/My Drive/Model/lgb_model_buy.dat', 'rb') as f:
            model_buy = pickle.load(f)
        with open('/content/drive/My Drive/Model/lgb_model_sell.dat', 'rb') as f:
            model_sell = pickle.load(f)
        return model_buy, model_sell

    def train_params_with_validations(self, train_x, train_y, valid_x, valid_y, params):
        # print('training data description')
        # print('train_x:',train_x.shape)
        # print('train_y:',train_y.shape)
        train_start_ind = OneMinMarketData.check_matched_index(train_x)
        # print('train period:', OneMinMarketData.ohlc.dt[train_start_ind], OneMinMarketData.ohlc.dt[train_start_ind + len(train_y)])
        train = lgb.Dataset(train_x.values.astype(np.float32), train_y.values.astype(np.float32))
        lgb_eval = lgb.Dataset(valid_x.values.astype(np.float32), valid_y.values.astype(np.float32), reference=train)
        model = lgb.train(params, train, valid_sets=lgb_eval)
        return model

    def prediction(self, model, test_x, pred_kijun):
        prediction = []
        pval = model.predict(test_x, num_iteration=model.best_iteration)
        for p in pval:
            if p[1] > pred_kijun and (p[0] < 1 - pred_kijun and p[2] < 1 - pred_kijun and p[3] < 1 - pred_kijun):
                prediction.append(1)
            elif p[2] > pred_kijun and (p[0] < 1 - pred_kijun and p[1] < 1 - pred_kijun and p[3] < 1 - pred_kijun):
                prediction.append(2)
            elif p[3] > pred_kijun and (p[0] < 1 - pred_kijun and p[1] < 1 - pred_kijun and p[2] < 1 - pred_kijun):
                prediction.append(3)
            else:
                prediction.append(0)
        return prediction

    def prediction2(self, model, test_x):
        prediction = []
        pval = model.predict(test_x, num_iteration=model.best_iteration)
        for p in pval:
            prediction.append(p.argmax())
        return prediction

    def bp_prediciton(self, model, test_x, kijun):
        pred = model.predict(test_x, num_iteration=model.best_iteration)
        res = []
        for i in pred:
            if i >= kijun:
                res.append(1)
            else:
                res.append(0)
        return res

    def bpsp_prediction(self, model, test_x, uppder_kijun):
        prediction = []
        pval = model.predict(test_x, num_iteration=model.best_iteration)
        for p in pval:
            res = list(map(lambda x: 1.0 if x >= uppder_kijun else 0, p))
            if (res[0] == 1 and res[1] == 0 and res[2] == 0 and res[3] == 0) or (
                    res[0] == 0 and res[1] == 0 and res[2] == 0 and res[3] == 0):
                prediction.append(0)
            elif res[0] == 0 and res[1] == 1 and res[2] == 0 and res[3] == 0:
                prediction.append(1)
            elif res[0] == 0 and res[1] == 0 and res[2] == 1 and res[3] == 0:
                prediction.append(2)
            elif res[0] == 0 and res[1] == 0 and res[2] == 0 and res[3] == 1:
                prediction.append(3)
            else:
                print('unknown output in bpsp_prediction!')
                print(res)
        return prediction

    def bp_buysell_prediction(self, prediction_buy, prediction_sell, upper_kijun, lower_kijun):
        if len(prediction_buy) == len(prediction_sell):
            res = []
            for i in range(len(prediction_buy)):
                if prediction_buy[i] >= upper_kijun and prediction_sell[i] <= lower_kijun:
                    res.append(1)
                elif prediction_sell[i] >= upper_kijun and prediction_buy[i] <= lower_kijun:
                    res.append(-1)
                else:
                    res.append(0)
            return res
        else:
            print('bp_buysell_prediction - buy prediction and sell predition num is not matched!!')
            return []

    def bp_buysell_prediction2(self, model_buy, model_sell, test_x, upper_kijun, lower_kijun):
        p_buy = model_buy.predict(test_x, num_iteration=model_buy.best_iteration)
        p_sell = model_sell.predict(test_x, num_iteration=model_sell.best_iteration)
        res = []
        for i in range(len(p_buy)):
            if p_buy[i] >= upper_kijun and p_sell[i] <= lower_kijun:
                res.append(1)
            elif p_sell[i] >= upper_kijun and p_buy[i] <= lower_kijun:
                res.append(-1)
            else:
                res.append(0)
        return res

    def calc_buysell_accuracy(self, predictions, test_y):
        num = predictions.count(1) + predictions.count(2)
        matched = 0
        y = np.array(test_y)
        for i in range(len(predictions)):
            if predictions[i] == 1 and y[i] == 1 or predictions[i] == 2 and y[i] == 2:
                matched += 1
        if num > 0:
            return float(matched) / float(num)
        else:
            return 0

    def calc_total_accuracy(self, predictions, test_y):
        matched = 0
        y = np.array(test_y)
        for i in range(len(predictions)):
            if predictions[i] == y[i]:
                matched += 1
        return float(matched) / float(len(predictions))

    def calc_bp_accuracy(self, predictions, test_y):
        matched = 0
        y = np.array(test_y)
        for i in range(len(predictions)):
            if predictions[i] == 1 and y[i] == 1:
                matched += 1
        if sum(predictions) > 0:
            return float(matched) / float(sum(predictions))
        else:
            return 0

    # count only matched with test_y (0 or 1)
    def calc_bp_accuracy2(self, predictions, test_y):
        matched = 0
        y = np.array(test_y)
        for i in range(len(predictions)):
            if predictions[i] == y[i]:
                matched += 1
        if sum(predictions) > 0:
            return float(matched) / float(len(predictions))
        else:
            return 0