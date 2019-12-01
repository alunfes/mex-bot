import threading
from SystemFlg import SystemFlg
from PrivateWS import PrivateWSData
import time

'''
同一アカウントでbotと裁量が同時に取引しても対応できるように。
PrivateWSからのexec dataを元に常時約定状況をモニタリングしてbotとしてのポジションを自炊する。
'''

class Account:
    def __init__(self):
        self.lock_posi = threading.Lock()
        self.lock_order = threading.Lock()
        self.posi_side = ''
        self.posi_price = 0
        self.posi_size = 0
        self.order_ids_executed = []
        self.order_ids = []
        self.order_side = {}
        self.order_price = {}
        self.order_size = {}
        self.exec_id = []
        self.realized_pnl = 0
        self.unrealized_pnl = 0
        self.num_trade = 0


    def add_order(self, order_id, side, price, size, status): #call from bot
        with self.lock_order:
            self.order_ids.append(order_id)
            self.order_side[order_id] = side
            self.order_price[order_id] = price
            self.order_size[order_id] = size

    def __update_order(self, order_id, price, size, status):
        with self.lock_order:
            self.order_price[order_id] = price
            self.order_size[order_id] = size
            self.order_status[order_id] = status

    def __remove_order(self, order_id):
        with self.lock_order:
            self.order_ids_executed.append(order_id)
            self.order_ids.remove(order_id)
            del self.order_size[order_id]
            del self.order_price[order_id]

    def __execute_order(self, order_id, exec_side, exec_price, last_qty, exec_comm, status):
        if status != 'New':
            self.__calc_pnl(exec_side, exec_price, last_qty, exec_comm)
            self.__update_position(exec_side, exec_price, last_qty)
            if status == 'Filled':
                self.remove_order(order_id)
            else:
                self.order_size[order_id] -= last_qty


    def __calc_pnl(self, exec_side, exec_price, exec_size, exec_comm):
        if self.posi_side!= '' and self.posi_side != exec_side: #position close execution
            self.realized_pnl += (exec_price - self.posi_price) * exec_size if self.posi_side == 'Buy' else (self.posi_price - exec_price) * exec_size
            self.realized_pnl += (exec_comm * exec_price) / 100000000
        else: #additional execution
            pass


    def calc_unrealized_pnl(self, ltp):
        self.unrealized_pnl = (ltp - self.posi_price) * self.posi_size if self.posi_side == 'Buy' else (self.posi_price - ltp) * self.posi_size


    def __update_position(self, side, price, size):
        with self.lock_posi:
            if self.posi_side =='':
                self.posi_side = side
                self.posi_price = price
                self.posi_size = size
            elif self.posi_side == side:
                self.posi_price = ((self.posi_price * self.posi_size) + (price * size)) / (self.posi_size + size)
                self.posi_size += size
            else: #opposite side trade
                self.posi_side = side
                self.posi_size = size - self.posi_size
                self.posi_price = price

    '''
    exec data:
    orderがないときは100だけ保持する
    orderがあるときは、新しくexec入ってきたら常にチェックする
    order_idが一致するexec dataがあればorderとpositionを更新
    一致しないものは100で削除
    もしorder入れた時点で対象のexec dataが消えていたら？->order dataも監視してそちらの結果を優先する
    '''

    '''
    {'orderID': '1c24c830-8b32-ac10-5bd7-11b2513c60a2', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Sell', 'simpleOrderQty': None, 
    'orderQty': 100000, 'price': 7764, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'ordType': 'Limit', 
    'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'New', 'triggered': '', 'workingIndicator': False, 
    'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 100000, 'simpleCumQty': None, 'cumQty': 0, 'avgPx': None, 'multiLegReportingType': 'SingleSecurity', 
    'text': 'Submission from www.bitmex.com', 'transactTime': '2019-11-30T06:32:51.538Z', 'timestamp': '2019-11-30T06:32:51.538Z'}]
    '''
    def __account_thread(self):
        while SystemFlg.get_system_flg():
            executions = PrivateWSData.get_exec_data()
            if len(executions) > 0:
                for exec in executions:
                    if exec['orderID'] in self.order_ids:
                        self.__execute_order(exec['orderID'], exec['side'], exec['price'], exec['lastQty'], exec['execComm'], exec['ordStatus'])
            else: #executed all or cancelled

            time.sleep(0.1)










