'''
sim levelの最適化：
loss cut, pt,
'''

import pickle
import matplotlib.pyplot as plt
import csv

from SimStrategy import Strategy
from SimOneMinMarketData import OneMinMarketData
from SimAccount import SimAccount
from SimLgbModel import LgbModel
import time

class Sim:
    @classmethod
    def sim_model_pred_onemin(cls, start_ind, bpsp, ac):
        omd = OneMinMarketData
        end_i = len(bpsp)
        for i in range(len(bpsp) - 1):
            ac.check_executions(i, omd.ohlc.dt[start_ind + i], omd.ohlc.open[start_ind + i],
                                omd.ohlc.high[start_ind + i], omd.ohlc.low[start_ind + i])
            dd = Strategy.model_prediction_onemin(start_ind, bpsp, i, ac)
            if dd.side != '':
                ac.entry_order(dd.side, dd.price, dd.size, dd.type, dd.expire, 0, 0, i, omd.ohlc.dt[start_ind + i])
            ac.move_to_next(i, omd.ohlc.dt[start_ind + i], omd.ohlc.open[start_ind + i],
                            omd.ohlc.high[start_ind + i], omd.ohlc.low[start_ind + i],
                            omd.ohlc.close[start_ind + i])
        ac.last_day_operation(end_i, omd.ohlc.dt[start_ind + end_i], omd.ohlc.open[start_ind + end_i],
                              omd.ohlc.high[start_ind + end_i], omd.ohlc.low[start_ind + end_i],
                              omd.ohlc.close[start_ind + end_i])
        return ac


    @classmethod
    def sim_ema_trend_follow(cls, start_ind, ac):
        omd = OneMinMarketData
        key_name = 'ema_gra:100'
        for i in range(len(omd.ohlc.index_data_dict[key_name])-1):
            if str(omd.ohlc.index_data_dict[key_name][i]).isnumric():
                dd = Strategy.index_val_kijun_comparison(start_ind, key_name, 0, False, i, ac)
                if dd.side != '':
                    ac.entry_order(dd.side, dd.price, dd.size, dd.type, dd.expire, 0, 0, i, omd.ohlc.dt[start_ind + i])
                    ac.move_to_next(i, omd.ohlc.dt[start_ind + i], omd.ohlc.open[start_ind + i],
                                    omd.ohlc.high[start_ind + i], omd.ohlc.low[start_ind + i],
                                    omd.ohlc.close[start_ind + i])
        end_i = len(omd.ohlc.index_data_dict[key_name])
        ac.last_day_operation(end_i, omd.ohlc.dt[start_ind + end_i], omd.ohlc.open[start_ind + end_i],
                                  omd.ohlc.high[start_ind + end_i], omd.ohlc.low[start_ind + end_i],
                                  omd.ohlc.close[start_ind + end_i])
        return ac


    @classmethod
    def sim_lgbmodel(cls, stdata, pl_kijun, ac):
        print('sim length:' + str(stdata.dt[0]) + str(stdata.dt[-1]))
        for i in range(len(stdata.prediction) - 1):
            dd = Strategy.model_prediction(pl_kijun, stdata, i, ac)
            if dd.cancel:
                ac.cancel_order(i, stdata.dt[i], stdata.ut[i])
            elif dd.side != '':
                ac.entry_order(dd.side, dd.price, dd.size, dd.type, dd.expire, i, stdata.dt[i], stdata.ut[i],
                               stdata.price[i])
            ac.move_to_next(i, stdata.dt[i], stdata.ut[i], stdata.price[i])
        ac.last_day_operation(len(stdata.prediction) - 1, stdata.dt[len(stdata.prediction) - 1],
                              stdata.ut[len(stdata.prediction) - 1], stdata.price[len(stdata.prediction) - 1])
        return ac

    @classmethod
    def sim_bp(cls, stdata, pl, ls, ac):
        print('sim length:' + str(stdata.dt[0]) + str(stdata.dt[-1]))
        for i in range(len(stdata.prediction) - 1):
            dd = Strategy.model_bp_prediction(pl, ls, stdata, i, ac)
            if dd.side != '':
                ac.entry_order(dd.side, dd.price, dd.size, dd.type, dd.expire, pl, ls, i, stdata.dt[i], stdata.ut[i],
                               stdata.price[
                                   i])  # ntry_order(self, side, price, size, type, expire, pl, ls, i, dt, ut, tick_price):
            ac.move_to_next(i, stdata.dt[i], stdata.ut[i], stdata.price[i])
        ac.last_day_operation(len(stdata.prediction) - 1, stdata.dt[len(stdata.prediction) - 1],
                              stdata.ut[len(stdata.prediction) - 1], stdata.price[len(stdata.prediction) - 1])
        return ac

    @classmethod
    def sim_sp(cls, stdata, pl, ls, ac):
        print('sim length:' + str(stdata.dt[0]) + str(stdata.dt[-1]))
        for i in range(len(stdata.prediction) - 1):
            dd = Strategy.model_sp_prediction(pl, ls, stdata, i, ac)
            if dd.side != '':
                ac.entry_order(dd.side, dd.price, dd.size, dd.type, dd.expire, pl, ls, i, stdata.dt[i], stdata.ut[i],
                               stdata.price[
                                   i])  # ntry_order(self, side, price, size, type, expire, pl, ls, i, dt, ut, tick_price):
            ac.move_to_next(i, stdata.dt[i], stdata.ut[i], stdata.price[i])
        ac.last_day_operation(len(stdata.prediction) - 1, stdata.dt[len(stdata.prediction) - 1],
                              stdata.ut[len(stdata.prediction) - 1], stdata.price[len(stdata.prediction) - 1])
        return ac

    @classmethod
    def sim_buysell(cls, stdata, pl, ls, ac):
        print('sim length:' + str(stdata.dt[0]) + str(stdata.dt[-1]))
        one_min_checker = 1
        for i in range(len(stdata.prediction) - 1):
            if ac.suspension_flg == False:
                dd = Strategy.model_buysell_prediction(pl, ls, stdata, i, ac)
                if dd.side != '':
                    ac.entry_order(dd.side, dd.price, dd.size, dd.type, dd.expire, pl, ls, i, stdata.dt[i],
                                   stdata.ut[i], stdata.price[
                                       i])  # ntry_order(self, side, price, size, type, expire, pl, ls, i, dt, ut, tick_price):
            if i > one_min_checker * 60:
                one_min_checker += 1
                ac.suspension_flg = False
            ac.move_to_next(i, stdata.dt[i], stdata.ut[i], stdata.price[i])
        ac.last_day_operation(len(stdata.prediction) - 1, stdata.dt[len(stdata.prediction) - 1],
                              stdata.ut[len(stdata.prediction) - 1], stdata.price[len(stdata.prediction) - 1])
        return ac

    @classmethod
    def sim_lgbmodel_opt(cls, stdata, pl, losscut, time_exit, zero_three_exit_loss, zero_three_exit_profit,
                         ac: SimAccount):
        print('sim length:' + str(stdata.dt[0]) + str(stdata.dt[-1]))
        one_min_checker = 1
        for i in range(len(stdata.prediction) - 1):
            if ac.suspension_flg == False:
                dd = Strategy.model_prediction_opt(time_exit, zero_three_exit_loss, zero_three_exit_profit, stdata, i,
                                                   ac)
                if dd.cancel:
                    ac.cancel_order(i, stdata.dt[i], stdata.ut[i])
                elif dd.side != '':
                    ac.entry_order(dd.side, dd.price, dd.size, dd.type, dd.expire, pl, losscut, i, stdata.dt[i],
                                   stdata.ut[i], stdata.price[i])
            if i > one_min_checker * 60:
                one_min_checker += 1
                ac.suspension_flg = False
            ac.move_to_next(i, stdata.dt[i], stdata.ut[i], stdata.price[i])
        ac.last_day_operation(len(stdata.prediction) - 1, stdata.dt[len(stdata.prediction) - 1],
                              stdata.ut[len(stdata.prediction) - 1], stdata.price[len(stdata.prediction) - 1])
        return ac



    @classmethod
    def sim_ema_trend_contrarian(cls, stdata, ac):
        print('sim length:' + str(stdata.dt[0]) + str(stdata.dt[-1]))
        for i in range(len(stdata.prediction) - 1):
            dd = Strategy.ema_trend_contrarian(stdata, i, ac)
            if dd.side != '':
                ac.entry_order(dd.side, dd.price, dd.size, dd.type, dd.expire, i, stdata.dt[i], stdata.ut[i],
                               stdata.price[i])
            ac.move_to_next(i, stdata.dt[i], stdata.ut[i], stdata.price[i])
        ac.last_day_operation(len(stdata.prediction) - 1, stdata.dt[len(stdata.prediction) - 1],
                              stdata.ut[len(stdata.prediction) - 1], stdata.price[len(stdata.prediction) - 1])
        return ac


if __name__ == '__main__':



    #load model and sim
    '''
    num_term = 10
    corr_kijun = 0.9
    upper_kijun = 0.5
    lower_kijun = 0.4
    initial_data_vol = 3000

    train_size = 0.8
    valid_size = 0.1

    params = {'objective': 'binary', 'boosting': 'gbdt', 'learning_rate': 0.05, 'num_iterations': 15000, 'max_depth': 6,
              'num_leaves': 500, 'verbose_eval': False, 'verbose': -1, 'early_stopping_rounds': 50}

    start = time.time()
    OneMinMarketData.initialize_for_load_sim(num_term, initial_data_vol)
    df = OneMinMarketData.genrate_df_from_dict()
    test_y = df['bpsp']
    test_y.columns = ['bpsp']
    test_df = df.drop(['dt', 'size', 'bpsp'], axis=1)
    lgbmodel = LgbModel()
    model = lgbmodel.load_model()
    cols = list(test_df.columns)
    cols.sort()
    test_df = test_df[cols]

    predictions = lgbmodel.bp_prediciton(model, test_df, upper_kijun)
    print('test accuracy={}'.format(lgbmodel.calc_bp_accuracy(predictions, test_y)))

    start_ind = OneMinMarketData.check_matched_index(test_df)
    sim = Sim()
    ac = SimAccount()
    ac = sim.sim_model_pred_onemin(start_ind, predictions, ac)
    print('total pl={},num trade={},win rate={}, pl_stability={}, num_buy={}, num_sell={}'.format(ac.total_pl,
                                                                                                  ac.num_trade,
                                                                                                  ac.win_rate,
                                                                                                  ac.pl_stability,
                                                                                                  ac.num_buy,
                                                                                                  ac.num_sell))
    print('strategy performance={}'.format(ac.total_pl * ac.pl_stability))

    fig, ax1 = plt.subplots()
    plt.figure(figsize=(30, 30), dpi=200)
    ax1.plot(ac.performance_total_pl_log, color='red', linewidth=3.0, label='pl')
    ax2 = ax1.twinx()
    ax2.plot(OneMinMarketData.ohlc.close[start_ind:])
    plt.show()

    test_df = test_df.assign(dt=df['dt'])
    test_df = test_df.assign(prediction=predictions)
    test_df.to_csv('./Data/sim_result.csv', index=False)
    '''


    #train and sim
    '''
    num_term = 10
    corr_kijun = 0.9
    upper_kijun = 0.5
    lower_kijun = 0.4
    initial_data_vol = 20000

    train_size = 0.8
    valid_size = 0.1

    params = {'objective': 'binary', 'boosting': 'gbdt', 'learning_rate': 0.05, 'num_iterations': 15000, 'max_depth': 6,
              'num_leaves': 500, 'verbose_eval': False, 'verbose': -1, 'early_stopping_rounds': 50}

    start = time.time()
    OneMinMarketData.initialize_for_bot(num_term, initial_data_vol)
    
    df = OneMinMarketData.genrate_df_from_dict()
    df = OneMinMarketData.remove_cols_contains_nan(df)
    df, corrs = OneMinMarketData.remove_all_correlated_cols3(df, 0.9)

    lgbmodel = LgbModel()
    train_xb, test_xb, train_yb, test_yb, valid_xb, valid_yb = lgbmodel.generate_bpsp_data(df, train_size, valid_size)
    model = lgbmodel.train_params_with_validations(train_xb, train_yb, valid_xb, valid_yb, params)
    # OneMinMarketData.write_all_func_dict()

    tp = lgbmodel.bp_prediciton(model, train_xb, upper_kijun)
    print('train accuracy={}'.format(lgbmodel.calc_bp_accuracy(tp, train_yb)))
    predictions = lgbmodel.bp_prediciton(model, test_xb, upper_kijun)
    print('test accuracy={}'.format(lgbmodel.calc_bp_accuracy(predictions, test_yb)))
    print('pred num buy=' + str(sum(predictions)))

    # importanceの上位200colだけ使って再学習
    cols = lgbmodel.select_important_cols2(model, train_xb)
    cols.extend(['open', 'high', 'low', 'close'])
    cols.sort()

    with open('./Model/sim_bpsp_cols.csv', 'w') as file:
        writer = csv.writer(file, lineterminator='\n')
        writer.writerow(cols)
    print('completed write bpsp columns')

    train_xb, test_xb, valid_xb = train_xb[cols], test_xb[cols], valid_xb[cols]
    train_xb = train_xb.loc[:, cols]
    test_xb = test_xb.loc[:, cols]
    valid_xb = valid_xb.loc[:, cols]
    model = lgbmodel.train_params_with_validations(train_xb, train_yb, valid_xb, valid_yb, params)

    tp = lgbmodel.bp_prediciton(model, train_xb, upper_kijun)
    print('train accuracy={}'.format(lgbmodel.calc_bp_accuracy(tp, train_yb)))
    predictions = lgbmodel.bp_prediciton(model, test_xb, upper_kijun)
    print('test accuracy={}'.format(lgbmodel.calc_bp_accuracy(predictions, test_yb)))
    print('pred num buy=' + str(sum(predictions)))

    with open('./Model/sim_lgb_bpsp_model.dat', 'wb') as f:
        pickle.dump(model, f)

    start_ind = OneMinMarketData.check_matched_index(test_xb)
    sim = Sim()
    ac = SimAccount()
    ac = sim.sim_model_pred_onemin(start_ind, predictions, ac)
    print('total pl={},num trade={},win rate={}, pl_stability={}, num_buy={}, num_sell={}'.format(ac.total_pl,
                                                                                                  ac.num_trade,
                                                                                                  ac.win_rate,
                                                                                                  ac.pl_stability,
                                                                                                  ac.num_buy,
                                                                                                  ac.num_sell))
    print('strategy performance={}'.format(ac.total_pl * ac.pl_stability))

    fig, ax1 = plt.subplots()
    plt.figure(figsize=(30, 30), dpi=200)
    ax1.plot(ac.performance_total_pl_log, color='red', linewidth=3.0, label='pl')
    ax2 = ax1.twinx()
    ax2.plot(OneMinMarketData.ohlc.close[start_ind:])
    plt.show()
    '''