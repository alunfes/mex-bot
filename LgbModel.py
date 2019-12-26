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
    def __init__(self, pred_method, upper_kijun):
        self.model = None
        self.pred = ''
        self.lock_pred = threading.Lock()
        self.upper_kijun = upper_kijun
        self.pred_method = pred_method
        self.lock_pred = threading.Lock()
        with open('./Model/lgb_bpsp_model.dat', mode='rb') as f:
            self.model = pickle.load(f)

        if os.path.exists('./Data/data.csv'):
            os.remove('./Data/data.csv')
        th = threading.Thread(target=self.main_thread)
        th.start()

    def set_pred(self,pred):
        with self.lock_pred:
            self.pred = pred


    def get_pred(self):
            return self.pred

    def write_df_pred(self, df, pred):
        df = df.assign(dt=datetime.datetime.now())
        df = df.assign(prediction=pred)
        if os.path.exists('./Data/data.csv'):
            df.to_csv('./Data/data.csv', mode='a', header=False, index=False)
        else:
            df.to_csv('./Data/data.csv',index=False)


    def main_thread(self):
        ini_data_flg = False #flg for market data initialization
        while SystemFlg.get_system_flg():
            while ini_data_flg is False: #wait for initial update of the market data
                if len(OneMinMarketData.ohlc.dt) > 0:
                    ini_data_flg = True
                time.sleep(0.5)


            if OneMinMarketData.get_flg_ohlc_update():
                df = OneMinMarketData.get_df()
                if df is not None:
                    if True in df.isnull().any():
                        print('null is in df!')
                        self.set_pred("null")
                    else:
                        if self.pred_method == 0:
                            prediction = self.bpsp_prediction(self.model, df, self.upper_kijun)
                        elif self.pred_method == 1:
                            prediction = self.bpsp_prediction2(self.model, df)
                        elif self.pred_method == 2:
                            prediction = self.bpsp_prediction2_kai(self.model, df)
                        elif self.pred_method == 3:
                            prediction = self.bpsp_prediction3(self.model, df, self.upper_kijun)
                        else:
                            print('invalid pred_method!', self.pred_method)
                        if len(prediction) > 0:
                            self.set_pred({0: 'No', 1: 'Buy', 2: 'Sell', 3: 'Both'}[prediction[-1]])
                        else:
                            print('prediction length==0!', prediction)
                            print(df)
                        OneMinMarketData.set_flg_ohlc_update(False)
                        print('prediction = ', self.pred)
                        self.write_df_pred(df, self.pred)
                else:
                    print('df is None after completed generation!')
            time.sleep(1)
        print('Lgb main thread ended.')

    def check_train_test_index_duplication(self, train_x, test_x):
        train_list = list(train_x.index.values)
        test_list = list(test_x.index.values)
        dupli = set(train_list) & set(test_list)
        if len(dupli) > 0:
            print('Index duplication in train and test df was found!')
            print(dupli)


    def load_model(self):
        model_buy = None
        model_sell = None
        with open('/content/drive/My Drive/Model/lgb_model_buy.dat', 'rb') as f:
            model_buy = pickle.load(f)
        with open('/content/drive/My Drive/Model/lgb_model_sell.dat', 'rb') as f:
            model_sell = pickle.load(f)
        return model_buy, model_sell


    def bpsp_prediction(self, model, test_x, uppder_kijun):
        prediction = []
        pval = model.predict(test_x.values.astype(np.float32), num_iteration=model.best_iteration)
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
                prediction.append(0)  # 複数は発火した時は0にする
        return prediction

    def bpsp_prediction2(self, model, test_x):
        prediction = []
        pval = model.predict(test_x.values.astype(np.float32), num_iteration=model.best_iteration)
        for p in pval:
            prediction.append(np.argmax(p))
        return prediction

    def bpsp_prediction2_kai(self, model, test_x):
        return list(np.argmax(model.predict(test_x.values.astype(np.float32), num_iteration=model.best_iteration), axis=1))

    def bpsp_prediction3(self, model, test_x, pred_kijun):
        prediction = []
        pval = model.predict(test_x.values.astype(np.float32), num_iteration=model.best_iteration)
        for p in pval:
            if max(p) > pred_kijun:
                prediction.append(np.argmax(p))
            else:
                prediction.append(0)
        return prediction

    def calc_bpsp_accuracy(self, prediction, test_y):
        num = len(prediction)
        matched = 0
        y = np.array(test_y)
        for i in range(len(prediction)):
            if prediction[i] == y[i]:
                matched += 1
        return round(float(matched) / float(num), 4)


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
