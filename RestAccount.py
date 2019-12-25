import threading
from SystemFlg import SystemFlg
from PrivateWS import PrivateWSData
import time
from datetime import datetime
from RealtimeWSAPI import TickData
from Trade import Trade
import pandas as pd
from LineNotification import LineNotification


'''
Market orderの約定判定：
order entryした時点で判定開始。全約定確認できるまで繰り返す。

Limit orderの約定判定：
ltpがlimit priceを常に監視して、約定し得る価格に達したら約定を確認。1sec間隔を開ける。

'''

class RestAccount:
    def __init__(self):
        self.lock_posi = threading.Lock()
        self.lock_order = threading.Lock()
        self.lock_performance = threading.Lock()
        self.taker_fee = 0.00075
        self.maker_fee = -0.00025
        self.start_dt = time.time()
        self.posi_side = ''
        self.posi_price = 0
        self.posi_size = 0
        self.posi_dt = None
        self.order_ids_removed = []
        self.order_ids_active = []
        self.order_side = {}
        self.order_price = {}
        self.order_size = {}
        self.order_dt = {}
        self.order_type = {}  # Market or Limit
        self.order_status = {}  # Sent, Onboarded
        self.order_checkced_execid = {}
        self.exec_ids_completed = []
        self.realized_pnl = 0
        self.unrealized_pnl = 0
        self.total_pnl_per_min = 0
        self.total_pnl = 0
        self.total_fee = 0

        self.num_trade = 0
        self.num_buy = 0
        self.num_sell = 0
        self.num_win = 0
        self.win_rate = 0

        self.account_log = []  # {}

        th = threading.Thread(target=self.__account_thread)
        th2 = threading.Thread(target=self.__onemin_thread)
        th.start()
        th2.start()

    def add_order(self, order_id, side, price, size, type):  # call from bot
        with self.lock_order:
            print('entry order', order_id)
            self.order_ids_active.append(order_id)
            self.order_side[order_id] = side
            self.order_price[order_id] = price
            self.order_size[order_id] = size
            self.order_dt[order_id] = datetime.now()
            self.order_type[order_id] = type
            self.order_status[order_id] = 'Sent'
            self.order_checkced_execid[order_id] = ['dummy']
            if type == 'Market':
                i = 0
                while order_id not in self.removed_order_ids:
                    self.__check_execution(order_id)
                    time.sleep(1)
                    i += 1
                    if i > 10:
                        print('add_order - execution of market order can not be confirmed!')
                        print(order_id)
            else:
                self.__confirm_order(order_id)


    def bot_cancel_order(self, order_id):  # call from bot
        trades = Trade.get_trades(10)
        api_exec_data = list(map(lambda x: x['info'] if x['info']['orderID'] == order_id and str(x['info']['execComm']) != 'None' else None, trades))
        api_exec_data = [x for x in api_exec_data if x != None]
        if len(api_exec_data) > 0:
            self.__calc_fee(order_id, list(map(lambda x: x['execComm'], api_exec_data)))
            self.__execute_order(api_exec_data[-1]['orderID'], '', api_exec_data[-1]['side'], api_exec_data[-1]['price'], self.order_size[order_id] - api_exec_data[-1]['leavesQty'], api_exec_data[-1]['ordStatus'])
        else:
            self.__remove_order(order_id)

    # to confirm added order in actual order data from ws
    def __confirm_order(self, order_id):
        order_data = Trade.get_order_byid(order_id, 10)
        if len(order_data) > 0:
            if self.order_side[order_id] != order_data[-1]['side']:
                print('order side is not matched !')
                self.order_side[order_id] = order_data[-1]['side']
            if self.order_price[order_id] != order_data[-1]['price']:
                print('order price is not matched !')
                self.order_price[order_id] = order_data[-1]['price']
            if self.order_size[order_id] != order_data[-1]['orderQty']:
                print('order size is not matched !')
                self.order_size[order_id] = order_data[-1]['orderQty']
            if self.order_type[order_id].upper() != order_data[-1]['type'].upper():
                print('order type is not matched !')
                self.order_type[order_id] = order_data[-1]['type']
            self.order_status[order_id] = 'Onboarded'
        else:
            print('__confirm_order: order id not found in order data!')

    def get_orders(self):
        return self.order_side, self.order_price, self.order_size, self.order_dt

    def get_order_ids(self):
        return self.order_ids

    def get_performance(self):
        with self.lock_performance:
            return {'total_pl': self.realized_pnl + self.unrealized_pnl + self.total_fee, 'num_trade': self.num_trade, 'win_rate': self.win_rate, 'total_fee': self.total_fee,
                    'total_pnl_per_min': self.total_pnl_per_min}

    def get_position(self):
        return {'side': self.posi_side, 'price': self.posi_price, 'size': self.posi_size, 'dt': self.posi_dt}

    def get_ac_log(self):
        return pd.DataFrame(self.account_log)

    def __update_order(self, order_id, price, size, status, ):
        with self.lock_order:
            self.order_price[order_id] = price
            self.order_size[order_id] = size
            self.order_status[order_id] = status

    def __remove_order(self, order_id):
        with self.lock_order:
            print('remove order', order_id)
            self.order_ids_removed.append(order_id)
            self.order_ids_active.remove(order_id)
            del self.order_size[order_id]
            del self.order_price[order_id]
            del self.order_side[order_id]
            del self.order_dt[order_id]
            del self.order_type[order_id]
            del self.order_status[order_id]
            del self.order_checkced_execid[order_id]
            self.removed_order_ids.append(order_id)


    def __execute_order(self, order_id, exec_id, exec_side, exec_price, exec_qty, status):
        self.order_checkced_execid[order_id].append(exec_id)
        self.exec_ids_completed.append(exec_id)
        if status == 'Filled' or status == 'Canceled':
            self.__calc_realized_pnl(exec_side, exec_price, exec_qty)
            self.__update_position(exec_side, exec_price, exec_qty)
            self.__remove_order(order_id)
        elif status == 'PartiallyFilled':
            if exec_id not in self.order_exec_ids[order_id]:
                with self.lock_order:
                    self.order_exec_ids[order_id].append(exec_id)
                self.__update_position(exec_side, exec_price, exec_qty)
            else:
                pass  # exec id is already processed
        else:
            print('Invalid order status in __execute_order!', status)

    def __check_execution(self, order_id):
        order_data = Trade.get_order_byid(order_id, 10)
        if self.order_size[order_id] > order_data[-1]['leavesQty']:
            trades = Trade.get_trades(50)
            api_exec_data = list(map(lambda x: x['info'] if x['info']['orderID'] == order_id and str(x['info']['execComm']) != 'None' else None, trades))
            api_exec_data = [x for x in api_exec_data if x != None]
            for d in api_exec_data:
                if api_exec_data['execID'] not in self.order_checkced_execid[order_id]:
                    self.__execute_order(order_id, api_exec_data['execID'], api_exec_data['side'], api_exec_data['avgPx'], int(round(self.order_size[order_id] - api_exec_data['leavesQty'])), api_exec_data['ordStatus'])


    def __calc_pnl(self):  # called every 1min
        ltp = TickData.get_ltp()
        if ltp > 0:
            self.__calc_unrealized_pnl(ltp)
        with self.lock_performance:
            self.total_pnl = round(self.realized_pnl + self.unrealized_pnl - self.total_fee, 4)
            if abs(self.total_pnl) > 0:
                self.total_pnl_per_min = round(self.total_pnl / ((time.time() - self.start_dt) / 60.0), 4)
            else:
                self.total_pnl_per_min = 0

    def __calc_realized_pnl(self, exec_side, exec_price, exec_size):
        if self.posi_side != '' and (self.posi_side != exec_side):
            pl = (1.0 / self.posi_price - 1.0 / exec_price) * exec_size if self.posi_side == 'Buy' else (1.0 / exec_price - 1.0 / self.posi_price) * exec_size
            self.realized_pnl += pl
        else:  # additional execution
            pass

    def __calc_win_rate(self, pl):
        self.num_trade += 1
        if pl > 0:
            self.num_win += 1
        self.win_rate = round(self.num_win / self.num_trade, 2)

    def __calc_fee(self, oid, api_exec_data):
        self.total_fee += sum(api_exec_data) / 100000000
        # self.total_fee += sum(list(map(lambda x: x['execComm'], api_exec_data))) / 100000000

    def __calc_unrealized_pnl(self, ltp):
        with self.lock_performance:
            if self.posi_side != '':
                self.unrealized_pnl = (1.0 / self.posi_price - 1.0 / ltp) * self.posi_size if self.posi_side == 'Buy' else (1.0 / ltp - 1.0 / self.posi_price) * self.posi_size
            else:
                self.unrealized_pnl = 0

    def __update_position(self, side, price, size):
        with self.lock_posi:
            if self.posi_side == '':
                self.posi_side = side
                self.posi_price = price
                self.posi_size = size
            elif self.posi_side == side:
                self.posi_price = ((self.posi_price * self.posi_size) + (price * size)) / (self.posi_size + size)
                self.posi_size += size
            else:  # opposite side trade
                self.posi_side = side
                self.posi_size = size - self.posi_size
                self.posi_price = price
            self.posi_dt = datetime.now()


    def __account_thread(self):
        while SystemFlg.get_system_flg():
            for oid in self.order_ids_active:
                ltp = TickData.get_ltp()
                #check if execution of limit order is possible
                if ltp <= self.order_price[oid] and self.order_side[oid] == 'Buy' or ltp >= self.order_price[oid] and self.order_side[oid] == 'Sell':
                    self.__check_execution(oid)
            time.sleep(1)

    def __onemin_thread(self):
        while SystemFlg.get_system_flg():
            time.sleep(60)
            self.__calc_pnl()










