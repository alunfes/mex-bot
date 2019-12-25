import pandas as pd
import numpy as np
import time
from OneMinData import OneMinData

class RealtimeSimAccount:
    def __init__(self):
        self.__initialize_order()
        self.__initialize_holding()

        self.log_data_list = []
        self.log_data_df = pd.DataFrame()

        self.taker_fee = 0.00075
        self.maker_fee = -0.00025
        self.exec_slip = 0.5 #process execution when price + exec_slip or price - exec_slip depends on side
        self.initial_asset = 1500000

        self.start_time = time.time()

        self.total_pl = 0
        self.realized_pl = 0
        self.unrealized_pl = 0
        self.pl_per_min = 0
        self.total_fee = 0
        self.num_trade = 0
        self.num_sell = 0
        self.num_buy = 0
        self.num_win = 0
        self.win_rate = 0
        self.asset = self.initial_asset

        self.dt_log = []
        self.total_pl_log = []
        self.pl_stability = 0

        self.start_dt = ''
        self.end_dt = ''

    def __initialize_order(self):
        self.order_serial_num = 0
        self.order_serial_list = []
        self.order_serial = {}
        self.order_side = {}
        self.order_price = {}
        self.order_size = {}
        self.order_dt = {}
        self.order_type = {}  # market / limit


    def __del_order(self, target_serial):
        if target_serial in self.order_serial_list:
            self.order_serial_list.remove(target_serial)
            del self.order_serial[target_serial]
            del self.order_side[target_serial]
            del self.order_price[target_serial]
            del self.order_size[target_serial]
            del self.order_dt[target_serial]
            del self.order_type[target_serial]

    def __initialize_holding(self):
        self.holding_side = ''
        self.holding_price = 0
        self.holding_size = 0
        self.holding_dt = ''


    def onemine_process(self, ltp, dt):
        self.total_pl_log.append(self.total_pl)
        # self.__add_log('i:'+str(i), i)

    def update_pnl(self, ltp):
        self.__calc_unrealized_pl(ltp)
        self.total_pl = round(self.realized_pl + self.unrealized_pl - self.total_fee, 6)
        self.asset = self.initial_asset + self.total_pl

    def entry_order(self, side, price, size, type, ltp, dt):
        if side == 'Buy':
            self.num_buy += 1
        elif side == 'Sell':
            self.num_sell += 1

        self.order_serial[self.order_serial_num] = self.order_serial_num
        self.order_side[self.order_serial_num] = side
        self.order_price[self.order_serial_num] = price
        self.order_size[self.order_serial_num] = size
        self.order_dt[self.order_serial_num] = dt
        self.order_type[self.order_serial_num] = type  # Limit, Market
        self.order_serial_list.append(self.order_serial_num)

        if type == 'Market': #即時約定
            self.__process_execution(side, ltp, size, 'Market', dt)
            self.__del_order(self.order_serial_list[-1])

        self.order_serial_num += 1


    def __update_holding(self, side, price, size, dt):
        self.holding_side = side
        self.holding_price = price
        self.holding_size = size
        self.holding_dt = dt

    # always cancel latest order
    def cancel_order(self, order_serial_num):
        if order_serial_num in self.order_side:
            self.__del_order(order_serial_num)

    def cancel_all_orders(self):
        for oid in self.order_side:
            self.__del_order(oid)

    '''
    ltpだけの判定では本当は約定している場合があっても捕捉できないことがある。ohlcも使う必要がある。
    '''
    def check_execution(self, ltp, dt, ohlc:OneMinData):
        for oid in self.order_serial_list:
            if self.order_type[oid] == 'Limit':
                if self.order_side[oid] == 'Buy' and self.order_price[oid] >= ltp + self.exec_slip:
                    self.__process_execution(self.order_side[oid], self.order_price[oid], self.order_size[oid], self.order_type[oid], dt)
                elif self.order_side[oid] == 'Sell' and self.order_price[oid] <= ltp - self.exec_slip:
                    self.__process_execution(self.order_side[oid], self.order_price[oid], self.order_size[oid], self.order_type[oid], dt)
                elif self.order_side[oid] == 'Buy' and self.order_price[oid] >= ohlc.low[-1] + self.exec_slip:
                    self.__process_execution(self.order_side[oid], self.order_price[oid], self.order_size[oid], self.order_type[oid], dt)
                elif self.order_side[oid] == 'Sell' and self.order_price[oid] <= ohlc.high[-1] - self.exec_slip:
                    self.__process_execution(self.order_side[oid], self.order_price[oid], self.order_size[oid], self.order_type[oid], dt)



    def __process_execution(self, side, exec_price, size, type, dt):
        if self.holding_side == '':  # no position
            self.__update_holding(side, exec_price, size, dt)
            self.__calc_fee(size, exec_price, type)
        elif self.holding_side == side:
            ave_price = round(((self.holding_price * self.holding_size) + (exec_price * size)) / (size + self.holding_size))  # averaged holding price
            self.__update_holding(side, ave_price, self.holding_size + size, dt)
            self.__calc_fee(size, exec_price, type)
        elif self.holding_side != side and self.holding_size == size:
            self.__calc_fee(size, exec_price, type)
            self.__calc_executed_pl(exec_price, size, type)
            self.__initialize_holding()
        elif self.holding_side != side and self.holding_size > size:
            self.__calc_fee(size, exec_price, type)
            self.__calc_executed_pl(exec_price, size, type)
            self.__update_holding(self.holding_side, self.holding_price, self.holding_size - size, dt)
        elif self.holding_side != side and self.holding_size < size:
            self.__calc_fee(size, exec_price, type)
            self.__calc_executed_pl(exec_price, size, type)
            self.__update_holding(side, exec_price, size - self.holding_size, dt)
        else:
            print('unknown situation in __process_execution!')

    def bot_procedss_execution(self, side, exec_price, size, type, dt):
        self.__process_execution(side, exec_price, size, type, dt)


    def __calc_executed_pl(self, exec_price, size, type):
        pl = (exec_price - self.holding_price) * size if self.holding_side == 'Buy' else (self.holding_price - exec_price) * size
        self.realized_pl += round(pl, 6)
        self.num_trade += 1
        if pl > 0:
            self.num_win += 1
        if self.num_trade > 0:
            self.win_rate = round(self.num_win / self.num_trade, 2)

    def __calc_fee(self, size, price, type):
        if type == 'Limit':
            self.total_fee += round(size * price * self.maker_fee, 6)
        elif type == 'Market':
            self.total_fee += round(size * price * self.taker_fee, 6)
        else:
            print('invalid maker_taker flg!')

    def __calc_unrealized_pl(self, ltp):
        if self.holding_side != '':
            self.unrealized_pl = round((ltp - self.holding_price) * self.holding_size if self.holding_side == 'Buy' else (self.holding_price - ltp) * self.holding_size, 6)
        else:
            self.unrealized_pl = 0

    def __calc_pl_stability(self):
        base_line = np.linspace(self.performance_total_pl_log[0], self.performance_total_pl_log[-1], num=len(self.performance_total_pl_log))
        sum_diff = 0
        for i in range(len(base_line)):
            sum_diff += (base_line[i] - self.performance_total_pl_log[i]) ** 2
        self.pl_stability = round(1.0 / ((sum_diff ** 0.5) * self.total_pl / float(len(self.performance_total_pl_log))), 4)

    def __add_log(self, log, i, dt):
        self.total_pl_log.append(self.total_pl)
        self.action_log.append(log)
        self.holding_log.append(self.holding_side + ' @' + str(self.holding_price) + ' x' + str(self.holding_size))
        if len(self.order_i) > 0:
            k = self.order_serial_list[-1]
            self.order_log.append(self.order_side[k] + ' @' + str(self.order_price[k]) + ' x' + str(
                self.order_size[k]) + ' cancel=' + str(self.order_cancel[k]) + ' type=' + self.order_type[k])
        else:
            self.order_log.append('' + ' @' + '0' + ' x' + '0' + ' cancel=' + 'False' + ' type=' + '')
        self.i_log.append(i)
        self.dt_log.append(dt)
        if len(self.order_serial_list) > 0:
            k = self.order_serial_list[-1]
            # print(';i={}, dt={}, action={}, holding side={}, holding price={}, holding size={}, order side={}, order price={}, order size={}, pl={}, num_trade={}'
            # .format(i, dt, log, self.holding_side, self.holding_price, self.holding_size, self.order_side[k], self.order_price[k], self.order_size[k], self.total_pl, self.num_trade))
            self.log_data_list.append({'i': i, 'dt': dt, 'action': log, 'holding_side': self.holding_side,
                                       'holding_price': self.holding_price, 'holding_size': self.holding_size,
                                       'order_side': self.order_side[k], 'order_price': self.order_price[k],
                                       'order_size': self.order_size[k],
                                       'total_pl': self.total_pl, 'num_trade': self.num_trade})
        else:
            # print(';i={}, dt={}, action={}, holding side={}, holding price={}, holding size={}, order side={}, order price={}, order size={}, pl={}, num_trade={}'.format(i, dt, log, self.holding_side, self.holding_price, self.holding_size, '', '0', '0', self.total_pl, self.num_trade))
            self.log_data_list.append({'i': i, 'dt': dt, 'action': log, 'holding_side': self.holding_side,
                                       'holding_price': self.holding_price, 'holding_size': self.holding_size,
                                       'order_side': 0, 'order_price': 0, 'order_size': 0,
                                       'total_pl': self.total_pl, 'num_trade': self.num_trade})