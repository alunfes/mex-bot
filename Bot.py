from Trade import Trade
from OneMinMarketData import OneMinMarketData
from PrivateWS import PrivateWS
from Account import Account
from SystemFlg import SystemFlg
from LgbModel import LgbModel
from BotStrategy import BotStrategy, BotStateData
from LineNotification import LineNotification
from LogMaster import LogMaster
import threading
from RealtimeWSAPI import TickData
import pytz
import pandas as pd
import time
import os
from datetime import datetime

from RealtimeSim import RealtimeSim
from RealtimeSimAccount import RealtimeSimAccount

import pickle


'''

'''



class Bot:
    def __init__(self, sim_data_path):
        #pws = PrivateWS()
        self.pt_ratio, self.lc_ratio, self.pred_method, self.upper_kijun, self.avert_onemine, self.avert_period_kijun, self.avert_val_kijun = self.__read_config_data()
        Trade.initialize()
        self.ac = Account()
        self.omd = OneMinMarketData
        self.lgb_model = LgbModel(self.pred_method, self.upper_kijun)
        LineNotification.initialize()
        self.amount = 10

        self.sim = RealtimeSim()
        self.sim_ac = RealtimeSimAccount()
        self.sim_ac2 = RealtimeSimAccount()
        self.sim_log = pd.DataFrame()
        self.sim_log_dict = {}
        self.sim_data_path = sim_data_path

        if os.path.exists(self.sim_data_path):
            os.remove(self.sim_data_path)

        th = threading.Thread(target=self.__bot_thread)
        th2 = threading.Thread(target=self.__bot_sub_thread)
        th.start()
        th2.start()


    def __bot_thread(self):
        while TickData.get_ltp() <= 0:
            time.sleep(1)

        next_min = datetime.now().minute +1 if datetime.now().minute +1 < 60 else 0
        flg = False
        while SystemFlg.get_system_flg():
            pred = self.lgb_model.get_pred()

            self.sim_ac = self.sim.sim_model_pred_onemin_avert(pred, self.pt_ratio, self.lc_ratio, self.amount, TickData.get_ltp(), self.sim_ac, self.sim_ac2, self.avert_period_kijun, self.avert_val_kijun, OneMinMarketData.ohlc)
            time.sleep(3) #simをsleep無しで回し続けるとtickdataがlockされてltp取れなくなる
            '''
            ds = BotStrategy.model_pred_onemin(pred, self.pt_ratio, self.lc_ratio, self.ac, self.amount)
            pt_price = int(round(position['price'] * (1.0 + pt_ratio))) if position['side'] == 'Buy' else int(round(position['price'] * (1.0 - pt_ratio)))
            position = self.ac.get_position()
            order_side, order_price, order_size, order_dt = self.ac.get_orders()
            if ds.flg_noaction == False:
                if ds.posi_side == '' and ds.order_price == 0 and ds.order_type == 'Market':#losscut
                    for oid in order_side: #cancel all orders before losscut
                        cancel = Trade.cancel_order(oid)
                        if 'info' not in cancel:
                            print('cancel failed in bot!', cancel)
                        else:
                            self.ac.bot_cancel_order(oid)
                    if position['side'] != '': #do losscut
                        res = Trade.order('Buy' if position['side'] == ' Sell' else 'Sell', 0, 'Market', position['size'])
                        if 'info' not in res:
                            print('order error in bot!'), res
                        else:
                            self.ac.add_order(res['info']['orderID'], res['info']['side'], res['info']['price'], res['info']['orderQty'], res['info']['ordType'])
                else: #not losscut

                    if ds.posi_side != position['side'] and ds.posi_side != '':
                        flg_trade_error = False
                        res = Trade.order(ds.posi_side, 0, 'Market', position['size']+ds.posi_size) #making same position as ds
                        if 'info' not in res:
                            print('order error in bot!', res)
                            flg_trade_error = True
                        else:
                            self.ac.add_order(res['info']['orderID'], res['info']['side'], res['info']['price'],res['info']['orderQty'], res['info']['ordType'])
                    if ds.order_type == 'PT' and flg_trade_error == False:
                        Trade.order(ds.order_side, )
                    elif ds.order_side != '' and len(order_side) > 0:
                        pass
            '''
            pass





    '''
    for minutes process
    '''
    def __bot_sub_thread(self):
        while SystemFlg.get_system_flg():
            time.sleep(60)

            self.sim_ac.onemine_process(TickData.get_ltp(), datetime.now())
            print('posi_side:',self.sim_ac.holding_side, ', posi_price:',self.sim_ac.holding_price, ', posi_size:',self.sim_ac.holding_size)
            for oid in self.sim_ac.order_serial_list:
                print('order_side:',self.sim_ac.order_side[oid], ', order_price:',self.sim_ac.order_price, ', order_size:',self.sim_ac.order_size, ', order_type:',self.sim_ac.order_type)
            print('total_pl:',self.sim_ac.total_pl, 'total_fee:',self.sim_ac.total_fee, 'num_trade:', self.sim_ac.num_trade, 'win_rate:',self.sim_ac.win_rate)

            LineNotification.send_free_message('\r\n'+'total_pl:' + str(self.sim_ac.total_pl) + ', total_fee:' + str(self.sim_ac.total_fee) + ', num_trade:' + str(self.sim_ac.num_trade) + ', win_rate:' + str(self.sim_ac.win_rate) +'\r\n'
                                               +'pred=' + self.lgb_model.get_pred() + ', posi_side:' + self.sim_ac.holding_side + ', posi_price:' + str(self.sim_ac.holding_price) +
                                               ', posi_size:' + str(self.sim_ac.holding_size))
            self.__write_sim_log()



            '''
            print(self.ac.get_position())
            order_side, order_price, order_size, order_dt = self.ac.get_orders()
            for o in order_side:
                print('order ', o, ', side=', order_side[o], ', price=', order_price[o], ', size=', order_size[o])
            print(self.ac.get_performance())

            posi_side, posi_price, posi_size, posi_dt = self.ac.get_position()
            order_side, order_price, order_size, order_dt = self.ac.get_orders()
            order_sides, order_prices, order_sizes, order_dts = ''
            for oid in order_side:
                order_sides = order_sides + ' : ' + order_side[oid]
                order_prices = order_prices + ' : ' + order_price[oid]
                order_sizes = order_sizes + ' : ' + order_size[oid]
                order_dts = order_dts + ' : ' + order_dt[oid]
            performance = self.ac.get_performance() #{'total_pl':self.realized_pnl + self.unrealized_pnl + self.total_fee, 'num_trade':self.num_trade, 'win_rate':self.win_rate, 'total_fee':self.total_fee}
            LogMaster.add_log({'log_dt':datetime.now(), 'dt':self.omd.ohlc.dt[-1], 'open':self.omd.ohlc.open[-1], 'high':self.omd.ohlc.high[-1],
                               'low':self.omd.ohlc.low[-1], 'close':self.omd.ohlc.close[-1], 'posi_side':posi_side, 'posi_price':posi_price, 'posi_size':posi_size,
                               'order_side':order_sides,'order_price':order_prices, 'order_size':order_sizes, 'num_private_access':Trade.num_private_access,
                               'num_public_access':Trade.num_public_access, 'pnl':performance['total_pnl'], 'pnl_per_min':performance['total_pnl_per_min'],
                               'num_trade':performance['num_trade'], 'win_rate':performance['win_rate'], 'prediction':LgbModel.get_pred(), 'api_error':'', 'action_message':'Move to next'})
            LineNotification.send_performance_notification()
            '''
            pass


    def __read_config_data(self):
        config = pd.read_csv('./Model/bpsp_config.csv', index_col=0)
        return float(config['pt_ratio']), float(config['lc_ratio']), int(config['pred_method']), float(config['upper_kijun']), int(config['avert_onemine']), \
               int(config['avert_period_kijun']), float(config['avert_val_kijun'])


    def __write_sim_log(self):
        order_side = ''
        order_price = ''
        order_size = ''
        for oid in self.sim_ac.order_serial_list:
            order_side = order_side + self.sim_ac.order_side[oid] + ':'
            order_price = order_price + str(self.sim_ac.order_price[oid]) + ':'
            order_size = order_size + str(self.sim_ac.order_size[oid]) + ':'

        '''
        self.sim_log_list.append()
        self.sim_log = self.sim_log.append(pd.DataFrame({'dt': self.omd.ohlc.dt[-1], 'open': self.omd.ohlc.open[-1], 'high': self.omd.ohlc.high[-1], 'low': self.omd.ohlc.low[-1], 'close': self.omd.ohlc.close[-1],
             'posi_side': self.sim_ac.holding_side, 'posi_price': self.sim_ac.holding_price, 'posi_size': self.sim_ac.holding_size,
             'order_side': order_side, 'order_price': order_price, 'order_size': order_size,
             'total_pl': self.sim_ac.total_pl, 'total_fee': self.sim_ac.total_fee, 'num_trade': self.sim_ac.num_trade, 'win_rate': self.sim_ac.win_rate}),ignore_index=True)
        self.sim_log.to_csv(self.sim_data_path)
        '''



if __name__ == '__main__':
    config = pd.read_csv('./Model/bpsp_config.csv', index_col=0)

    '''
    bot = Bot()
    bot.initialize()
    df = OneMinMarketData.generate_df_from_dict()
    df.to_csv('./Data/df.csv')
    '''