'''
sim levelの最適化：
loss cut, pt,
'''

import pickle
import matplotlib.pyplot as plt
import csv
import numpy as np
import talib as ta

from RealtimeSimStrategy import RealtimeSimStrategy
from RealtimeSimAccount import RealtimeSimAccount
import time

class RealtimeSim:
    @classmethod
    def sim_model_pred_onemin(cls, pred, pt, lc, ltp, ac):
            dd = RealtimeSimStrategy.model_prediction_onemin(pred,ac, ltp)
            if dd.side != '':
                ac.entry_order(dd.side, dd.price, dd.size, dd.type, dd.expire, pt, lc, i, omd.ohlc.dt[start_ind + i])
            ac.move_to_next(i, omd.ohlc.dt[start_ind + i], omd.ohlc.open[start_ind + i], omd.ohlc.high[start_ind + i],
                            omd.ohlc.low[start_ind + i], omd.ohlc.close[start_ind + i])
        end_i = len(prediction) - 1
        ac.last_day_operation(end_i, omd.ohlc.dt[start_ind + end_i], omd.ohlc.open[start_ind + end_i],
                              omd.ohlc.high[start_ind + end_i], omd.ohlc.low[start_ind + end_i],
                              omd.ohlc.close[start_ind + end_i])
        return ac

    @classmethod
    def sim_model_pred_onemin_avert(cls, start_ind, prediction, pt, lc, ac, avert_period_kijun=120,
                                    avert_val_kijun=-0.005):
        omd = OneMinMarketData
        ac2 = SimAccount()
        for i in range(len(prediction) - 1):
            ac.check_executions(i, omd.ohlc.dt[start_ind + i], omd.ohlc.open[start_ind + i],
                                omd.ohlc.high[start_ind + i], omd.ohlc.low[start_ind + i])
            ac2.check_executions(i, omd.ohlc.dt[start_ind + i], omd.ohlc.open[start_ind + i],
                                 omd.ohlc.high[start_ind + i], omd.ohlc.low[start_ind + i])
            dd2 = Strategy.model_prediction_onemin(start_ind, prediction, i, ac2)
            dd = Strategy.model_prediction_onemin(start_ind, prediction, i, ac)
            if dd2.side == 'no' or dd2.side == 'both':
                print('invalid dd2side!')
                print(dd2.side)
            if ac.holding_size > 0.01:
                print('large holding!', ac.holding_size)
            if dd2.side != '':
                ac2.entry_order(dd2.side, dd2.price, dd2.size, dd2.type, dd2.expire, pt, lc, i,
                                omd.ohlc.dt[start_ind + i])  # ac2は常にトレード
            if len(ac2.performance_total_pl_log) > avert_period_kijun + 10:  # pl_check_term以上のpl logが溜まったらcheckを開始
                # if ac2.performance_total_pl_log[-1] - ac2.performance_total_pl_log[-pl_check_term] > 0: #check pl of ac2
                if np.gradient(ta.MA(np.array(ac2.performance_total_pl_log[-avert_period_kijun - 10:], dtype='f8'),
                                     timeperiod=avert_period_kijun))[-1] > avert_val_kijun:
                    if dd2.side != '':
                        if dd2.side != ac.holding_side and ac.holding_side != '':  # ac2と同じポジションを取る
                            ac.entry_order('buy' if ac.holding_side == 'sell' else 'sell', 0, 0.02, 'market', 10, pt,
                                           lc, i, omd.ohlc.dt[start_ind + i])
                        elif dd2.side != ac.holding_side and ac.holding_side == '':  # ac2と同じポジションを取る
                            ac.entry_order(dd2.side, 0, 0.01, 'market', 10, pt, lc, i, omd.ohlc.dt[start_ind + i])
                        else:  # ac2のddと同じときは何もしない
                            pass
                    else:  #
                        pass
                        # if ac.holding_side != '': #ac2に合わせるためにexit all
                        #    ac.entry_order('buy' if ac.holding_side=='sell' else 'sell', 0, 0.01, 'market', 10, pt, lc, i, omd.ohlc.dt[start_ind + i])
                else:  # ac2のpl_check_termにおけるplがマイナスの時はacでのトレードを停止
                    if ac.holding_side != '':
                        ac.entry_order('buy' if ac.holding_side == 'sell' else 'sell', 0, 0.01, 'market', 10, pt, lc, i,
                                       omd.ohlc.dt[start_ind + i])
            else:  # logがたまるまでは普通にトレード
                if dd.side != '':
                    ac.entry_order(dd.side, dd.price, dd.size, dd.type, dd.expire, pt, lc, i,
                                   omd.ohlc.dt[start_ind + i])
            ac.move_to_next(i, omd.ohlc.dt[start_ind + i], omd.ohlc.open[start_ind + i], omd.ohlc.high[start_ind + i],
                            omd.ohlc.low[start_ind + i], omd.ohlc.close[start_ind + i])
            ac2.move_to_next(i, omd.ohlc.dt[start_ind + i], omd.ohlc.open[start_ind + i], omd.ohlc.high[start_ind + i],
                             omd.ohlc.low[start_ind + i], omd.ohlc.close[start_ind + i])
        end_i = len(prediction) - 1
        ac.last_day_operation(end_i, omd.ohlc.dt[start_ind + end_i], omd.ohlc.open[start_ind + end_i],
                              omd.ohlc.high[start_ind + end_i], omd.ohlc.low[start_ind + end_i],
                              omd.ohlc.close[start_ind + end_i])
        return ac


if __name__ == '__main__':
    '''
    ema trend follow sim
    '''
    num_term = 10
    initial_data_vol = 20000

    start = time.time()
    OneMinMarketData.initialize_for_bot(num_term, initial_data_vol)
    df = OneMinMarketData.genrate_df_from_dict()
    # df = OneMinMarketData.remove_cols_contains_nan(df)

    start_ind = 0
    sim = Sim()
    ac = SimAccount()
    ac = sim.sim_ema_trend_follow(start_ind, ac)
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
    fromn = len(OneMinMarketData.ohlc.close) - len(ac.performance_total_pl_log)
    ax2.plot(OneMinMarketData.ohlc.close[fromn:])
    plt.show()

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