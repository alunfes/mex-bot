from Trade import Trade
from OneMinMarketData import OneMinMarketData
from PrivateWS import PrivateWS
from Account import Account
from RestAccount import RestAccount
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
    def __init__(self, sim_data_path, real_trade=False):
        self.pt_ratio, self.lc_ratio, self.pred_method, self.upper_kijun, self.avert_onemine, self.avert_period_kijun, self.avert_val_kijun = self.__read_config_data()
        Trade.initialize()
        self.ac = RestAccount()
        self.omd = OneMinMarketData
        self.lgb_model = LgbModel(self.pred_method, self.upper_kijun)
        self.real_trade = real_trade
        self.amount = 10000

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
        pre_order_side = ''
        pre_order_size = 0 #for detection of pt execution
        while SystemFlg.get_system_flg():
            pred = self.lgb_model.get_pred()

            self.sim_ac = self.sim.sim_model_pred_onemin(pred, self.pt_ratio, self.lc_ratio, self.amount, TickData.get_ltp(), self.sim_ac, OneMinMarketData.ohlc)
            #self.sim_ac = self.sim.sim_model_pred_onemin_avert(pred, self.pt_ratio, self.lc_ratio, self.amount, TickData.get_ltp(), self.sim_ac, self.sim_ac2, self.avert_period_kijun, self.avert_val_kijun, OneMinMarketData.ohlc)
            #self.sim_ac = self.sim.sim_model_pred_onemin_avert_limit_entry(pred, self.pt_ratio, self.lc_ratio, self.amount, TickData.get_ltp(), self.sim_ac, self.sim_ac2, self.avert_period_kijun, self.avert_val_kijun, OneMinMarketData.ohlc)

            if self.real_trade:
                posi = self.ac.get_position()

                bot_order = self.ac.get_latest_order()
                sim_order = self.sim_ac.get_latest_order()

                '''
                if len(order_side) > 1:
                    print('bot order len is bigger than 1!')
                    print(order_side)
                if len(self.sim_ac.order_side) > 1:
                    print('sim_ac order len is bigger than 1!')
                    print(order_side)
                '''

                #market entry
                if bot_order['side'] == '' and sim_order['side'] != '' and pre_order_side != '' and pre_order_size > 0: #pt exec check in bot
                    print('BOT: pt completion was detected and process sim_ac execution from bot.')
                    self.sim_ac.bot_procedss_execution(sim_order['side'], sim_order['price'], sim_order['size'], 'Limit', datetime.now())
                elif posi['side'] != self.sim_ac.holding_side: #to have same position side (botで先にpt約定完了してno posiになった時はsimに合わせるべきではない、botでpt約定を感知したらsim_acにも反映させるべき）
                    size = self.sim_ac.holding_size if posi['side'] == '' else self.sim_ac.holding_size + posi['size']
                    order_info = Trade.order(self.sim_ac.holding_side, self.sim_ac.holding_price, 'Market', size)
                    if order_info is not None:
                        print('BOT: entry order', order_info['info']['side'], order_info['info']['price'], order_info['info']['orderQty'], order_info['info']['ordType'], order_info['info']['orderID'])
                        LineNotification.send_free_message('BOT: entry order'+'\r\n'+ order_info['info']['side']+'\r\n'+ str(order_info['info']['price'])+'\r\n'+ str(order_info['info']['orderQty'])+'\r\n'+ order_info['info']['ordType']+'\r\n'+ order_info['info']['orderID'])
                        self.ac.add_order(order_info['info']['orderID'], order_info['info']['side'], order_info['info']['price'], order_info['info']['orderQty'], order_info['info']['ordType'])
                    else:
                        print('BOT: entry order failed!')
                        LineNotification.send_error('BOT: entry order failed!')
                elif bot_order['side'] != sim_order['side'] and posi['side'] == self.sim_ac.holding_side: #position side is matched but order side in unmatch
                    for oid in self.ac.order_ids_active:
                        Trade.cancel_order(oid)
                        print('BOT: cancel order', oid)
                        self.ac.bot_cancel_order(oid)
                    order_info = Trade.order(sim_order['side'], sim_order['price'], sim_order['type'], self.amount)
                    if order_info is not None:
                        print('BOT: pt order', order_info['info']['side'], order_info['info']['price'], order_info['info']['orderQty'], order_info['info']['ordType'], order_info['info']['orderID'])
                        LineNotification.send_free_message('BOT: pt order'+'\r\n'+ order_info['info']['side']+'\r\n'+ str(order_info['info']['price'])+'\r\n'+ str(order_info['info']['orderQty'])+'\r\n'+ order_info['info']['ordType']+'\r\n'+ order_info['info']['orderID'])
                        self.ac.add_order(order_info['info']['orderID'], order_info['info']['side'], order_info['info']['price'], order_info['info']['orderQty'], order_info['info']['ordType'])
                    else:
                        print('BOT: pt order failed!')
                        LineNotification.send_error('BOT: pt order failed!')

                #Limit entry
                '''
                if bot_order['side'] == '' and sim_order['side'] != '' and pre_order_side != '' and pre_order_size > 0:  # pt exec check in bot
                    print('BOT: pt completion was detected and process sim_ac execution from bot.')
                    self.sim_ac.bot_procedss_execution(sim_order['side'], sim_order['price'], sim_order['size'], 'Limit', datetime.now())
                elif posi['side'] != self.sim_ac.holding_side and :  # to have same position side (botで先にpt約定完了してno posiになった時はsimに合わせるべきではない、botでpt約定を感知したらsim_acにも反映させるべき）
                    size = self.sim_ac.holding_size if posi['side'] == '' else self.sim_ac.holding_size + posi['size']
                    order_info = Trade.order(self.sim_ac.holding_side, self.sim_ac.holding_price, 'Limit', size)
                    if order_info is not None:
                        print('BOT: entry order', order_info['info']['side'], order_info['info']['price'], order_info['info']['orderQty'], order_info['info']['ordType'], order_info['info']['orderID'])
                        LineNotification.send_free_message('BOT: entry order' + '\r\n' + order_info['info']['side'] + '\r\n' + str(order_info['info']['price']) + '\r\n' + str(order_info['info']['orderQty']) + '\r\n' + order_info['info']['ordType'] + '\r\n' + order_info['info']['orderID'])
                        self.ac.add_order(order_info['info']['orderID'], order_info['info']['side'], order_info['info']['price'], order_info['info']['orderQty'], order_info['info']['ordType'])
                    else:
                        print('BOT: entry order failed!')
                        LineNotification.send_error('BOT: entry order failed!')
                elif bot_order['side'] != sim_order['side'] and posi['side'] == self.sim_ac.holding_side:  # position side is matched but order side in unmatch
                    for oid in self.ac.order_ids_active:
                        Trade.cancel_order(oid)
                        print('BOT: cancel order', oid)
                        self.ac.bot_cancel_order(oid)
                    order_info = Trade.order(sim_order['side'], sim_order['price'], sim_order['type'], self.amount)
                    if order_info is not None:
                        print('BOT: pt order', order_info['info']['side'], order_info['info']['price'], order_info['info']['orderQty'], order_info['info']['ordType'], order_info['info']['orderID'])
                        LineNotification.send_free_message('BOT: pt order' + '\r\n' + order_info['info']['side'] + '\r\n' + str(order_info['info']['price']) + '\r\n' + str(order_info['info']['orderQty']) + '\r\n' + order_info['info']['ordType'] + '\r\n' + order_info['info']['orderID'])
                        self.ac.add_order(order_info['info']['orderID'], order_info['info']['side'], order_info['info']['price'], order_info['info']['orderQty'], order_info['info']['ordType'])
                    else:
                        print('BOT: pt order failed!')
                        LineNotification.send_error('BOT: pt order failed!')

                pre_order_side = bot_order['side']
                pre_order_size = bot_order['size']
                '''

            time.sleep(3)  # simをsleep無しで回し続けるとtickdataがlockされてltp取れなくなる
        print('exited from bot main loop')


    '''
    for minutes process
    '''
    def __bot_sub_thread(self):
        num_bot_main_loop = 0
        while SystemFlg.get_system_flg():
            time.sleep(60)

            print('')
            print('')
            print('*********************************************')
            print('num_bot_loop:',num_bot_main_loop, ' : ', datetime.now())
            print('*********************************************')
            print('')
            print('---------------------sim---------------------')
            self.sim_ac.onemine_process(TickData.get_ltp(), datetime.now())
            print('sim_posi_side:',self.sim_ac.holding_side, ', sim_posi_price:',self.sim_ac.holding_price, ', sim_posi_size:',self.sim_ac.holding_size)
            for oid in self.sim_ac.order_serial_list:
                print('sim_order_side:',self.sim_ac.order_side[oid], ', sim_order_price:',self.sim_ac.order_price[oid], ', sim_order_size:',self.sim_ac.order_size[oid], ', sim_order_type:',self.sim_ac.order_type[oid])
            print('sim_total_pl:',self.sim_ac.total_pl, 'sim_total_fee:',self.sim_ac.total_fee, 'sim_num_trade:', self.sim_ac.num_trade, 'sim_win_rate:',self.sim_ac.win_rate)

            if self.real_trade is False:
                LineNotification.send_free_message('\r\n'+'sim_total_pl:' + str(self.sim_ac.total_pl) + ', sim_total_fee:' + str(self.sim_ac.total_fee) + ', sim_num_trade:' + str(self.sim_ac.num_trade) + ', sim_win_rate:' + str(self.sim_ac.win_rate) +'\r\n'
                                                   +'pred=' + self.lgb_model.get_pred() + ', sim_posi_side:' + self.sim_ac.holding_side + ', sim_posi_price:' + str(self.sim_ac.holding_price) +
                                                   ', sim_posi_size:' + str(self.sim_ac.holding_size))
            self.__write_sim_log()


            if self.real_trade:
                print('')
                print('---------------------bot---------------------')
                #print('BOT: performance')
                performance = self.ac.get_performance()
                print('BOT Performance:', performance)
                #print('BOT: Position')
                posi = self.ac.get_position()
                print('BOT Position:', 'bot_posi_side:',posi['side'], ', bot_posi_price:', posi['price'], ', bot_posi_size:', posi['size'])
                #print('BOT: Orders')
                order_side, order_price, order_size, order_type, order_dt = self.ac.get_orders()
                for oid in order_side:
                    print('BOT Order:', 'bot_order_side:', order_side[oid], ', bot_order_price:', order_price[oid], ', bot_order_size:', order_size[oid], ', bot_order_type:', order_type[oid])

                LineNotification.send_free_message('\r\n' + 'total_pl:' + str(performance['total_pl']) + ', total_fee:' + str(performance['total_fee']) + ', num_trade:' + str(performance['num_trade']) +
                                                   ', win_rate:' + str(performance['win_rate']) + '\r\n'
                                                   + 'pred=' + self.lgb_model.get_pred() + ', posi_side:' + posi['side'] + ', posi_price:' + str(posi['price']) +
                                                   ', posi_size:' + str(posi['size']))

            num_bot_main_loop += 1
        print('exited from bot sub-loop')


    def __read_config_data(self):
        config = pd.read_csv('./Model/bpsp_config.csv', index_col=0)
        print('config data:')
        print('pt_ratio:', config['pt_ratio'])
        print('lc_ratio:', config['lc_ratio'])
        print('pred_method:', config['pred_method'])
        print('upper_kijun:', config['upper_kijun'])
        print('avert_onemine:', config['avert_onemine'])
        print('avert_period_kijun:', config['avert_period_kijun'])
        print('avert_val_kijun:', config['avert_val_kijun'])
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