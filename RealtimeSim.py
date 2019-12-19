'''
sim levelの最適化：
loss cut, pt,
'''

import pickle
import matplotlib.pyplot as plt
import csv
import numpy as np
import talib as ta
from datetime import datetime
from RealtimeSimStrategy import RealtimeSimStrategy
from RealtimeSimAccount import RealtimeSimAccount
import time


class RealtimeSim:
    @classmethod
    def sim_model_pred_onemin(cls, pred, pt_ratio, lc_ratio, amount, ltp, ac:RealtimeSimAccount):
            ds = RealtimeSimStrategy.model_prediction_onemin(pred, lc_ratio, amount, ac, ltp)
            pt_price = int(round(ac.holding_price * (1.0 + pt_ratio))) if ac.holding_side == 'Buy' else int(round(ac.holding_price * (1.0 - pt_ratio)))
            if ds.flg_noaction == False:
                if ds.order_type == 'LC':  # losscut
                    ac.cancel_all_orders()
                    if ac.holding_side != '':  # do losscut
                        ac.entry_order('Buy' if ac.holding_side == 'Sell' else 'Sell', 0, ac.holding_size, 'Market', ltp, datetime.now())
                else:  # not losscut
                    if ds.posi_side != ac.holding_side and ds.posi_side != '':
                        if ac.holding_side =='':
                            ac.entry_order(ds.posi_side, 0, ds.posi_size, 'Market', ltp, datetime.now())
                        else:
                            ac.entry_order(ds.posi_side, 0, ds.posi_size + ac.holding_size, 'Market', ltp, datetime.now())
                    elif ds.order_type == 'PT':
                        ac.entry_order('Buy' if ac.holding_side == 'Sell' else 'Sell', pt_price, ac.holding_size, 'Limit', ltp, datetime.now())
                    elif ds.posi_side == ac.holding_side and ds.posi_size != ac.holding_size:
                        print('position size unmatched!')
            ac.check_executions(ltp, datetime.now())
            ac.update_pnl(ltp)
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
    pass