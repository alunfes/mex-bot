import lightgbm as lgb
from sklearn import datasets
from sklearn.model_selection import train_test_split
import numpy as np
import pandas as pd
import pickle

from SimOneMinMarketData import OneMinMarketData

class LgbModel:
    def load_model(self):
        with open('/.Model/sim_lgb_bpsp_model.dat', mode='rb') as f:
            self.model = pickle.load(f)

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

    def genrate_col_removed_data(self, train_x, test_x, valid_x, cols):
        return train_x[cols], test_x[cols], valid_x[cols]

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

    def select_important_cols(self, model, train_xb):
        importance = pd.DataFrame(model.feature_importance(), index=list(train_xb.columns), columns=['importance'])
        data = importance.sort_values('importance', ascending=False)

        col = list(data.columns)[0]
        indicies = list(data.index)
        kijun = 0.9 * data[col].sum()

        cols = []
        current_sum = 0
        target = kijun
        i = 0
        while current_sum < target:
            current_sum += data[col].iloc[i]
            cols.append(indicies[i])
            i += 1
        return cols

    def select_important_cols2(self, model, train_xb):
        importance = pd.DataFrame(model.feature_importance(), index=list(train_xb.columns), columns=['importance'])
        data = importance.sort_values('importance', ascending=False)

        col = list(data.columns)[0]
        indicies = list(data.index)
        print('selected 200 cols, total importance =', data[col].iloc[:200].sum())
        return indicies[:200]

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
        model = None
        with open('./Model/sim_lgb_bpsp_model.dat', 'rb') as f:
            model = pickle.load(f)
        return model

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