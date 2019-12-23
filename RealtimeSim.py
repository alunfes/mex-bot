'''
sim levelの最適化：
loss cut, pt,
'''

import numpy as np
import talib as ta
from datetime import datetime
from RealtimeSimStrategy import RealtimeSimStrategy
from RealtimeSimAccount import RealtimeSimAccount
from OneMinData import OneMinData
import time


class RealtimeSim:
    @classmethod
    def sim_model_pred_onemin(cls, pred, pt_ratio, lc_ratio, amount, ltp, ac:RealtimeSimAccount, ohlc:OneMinData):
            ds = RealtimeSimStrategy.model_prediction_onemin(pred, lc_ratio, amount, ac, ltp)
            pt_price = int(round(ac.holding_price * (1.0 + pt_ratio))) if ac.holding_side == 'Buy' else int(round(ac.holding_price * (1.0 - pt_ratio)))
            if ds.flg_noaction == False:
                if ds.order_type == 'LC':  # losscut
                    ac.cancel_all_orders()
                    if ac.holding_side != '':  # do losscut
                        ac.entry_order('Buy' if ac.holding_side == 'Sell' else 'Sell', 0, ac.holding_size, 'Market', ltp, datetime.now())
                else:  # not losscut
                    if ds.posi_side != ac.holding_side and ds.posi_side != '':
                        if ac.holding_side == '':
                            print('kita1')
                            ac.entry_order(ds.posi_side, 0, ds.posi_size, 'Market', ltp, datetime.now())
                        else:
                            print('kita2')
                            ac.entry_order(ds.posi_side, 0, ds.posi_size + ac.holding_size, 'Market', ltp, datetime.now())
                    elif ds.order_type == 'PT' and (ds.order_side not in ac.order_side.values()):
                        print('kita3')
                        ac.entry_order('Buy' if ac.holding_side == 'Sell' else 'Sell', pt_price, ac.holding_size, 'Limit', ltp, datetime.now())
                    elif ds.posi_side == ac.holding_side and ds.posi_size != ac.holding_size:
                        print('position size unmatched!')
            ac.check_execution(ltp, datetime.now(), ohlc)
            ac.update_pnl(ltp)
            return ac


    @classmethod
    def sim_model_pred_onemin_avert(cls, pred, pt_ratio, lc_ratio, amount, ltp, ac:RealtimeSimAccount, ac2:RealtimeSimAccount, avert_period_kijun, avert_val_kijun, ohlc:OneMinData):
        ac2 = cls.sim_model_pred_onemin(pred, pt_ratio, lc_ratio, amount, ltp, ac2, ohlc)
        if len(ac2.total_pl_log) > avert_period_kijun:  # pl_check_term以上のpl logが溜まったらcheckを開始
            if np.gradient(ta.MA(np.array(ac2.total_pl_log[-avert_period_kijun:], dtype='f8'), timeperiod=avert_period_kijun))[-1] > avert_val_kijun:
                if ac2.holding_side != ac.holding_side and ac2.holding_side != '':
                    ac.entry_order(ac.holding_side, 0, ac2.holding_size, 'Market')
                    print('sim onemin avert: Market order for position  {', ac.holding_side, ' x ', ac.holding_size, ' @', ac.holding_price + '}')
                elif ac2.order_side != ac.order_side:
                    if ac.order_side != '':
                        ac.cancel_all_orders()
                    ac.entry_order(ac2.order_side, ac2.price, ac2.size, ac2.order_type, ltp, datetime.now())
                    print('sim onemin avert:' + ac2.order_type + ' entry order {', ac2.orderside, ' x ', ac.holding_size, ' @', ac.holding_price + '}')
        else:  # logがたまるまでは普通にトレード
            ac = cls.sim_model_pred_onemin(pred, pt_ratio, lc_ratio, amount, ltp, ac, ohlc)
        ac.check_execution(ltp, datetime.now(), ohlc)
        ac.update_pnl(ltp)
        ac2.check_execution(ltp, datetime.now(), ohlc)
        ac2.update_pnl(ltp)
        return ac


if __name__ == '__main__':
    pass