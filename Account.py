import threading
from SystemFlg import SystemFlg
from PrivateWS import PrivateWSData
import time
from datetime import datetime
from RealtimeWSAPI import TickData
from Trade import Trade
import pandas as pd


'''
同一アカウントでbotと裁量が同時に取引しても対応できるように。
PrivateWSからのexec dataを元に常時約定状況をモニタリングしてbotとしてのポジションを自炊する。
'''

class Account:
    def __init__(self):
        self.lock_posi = threading.Lock()
        self.lock_order = threading.Lock()
        self.lock_performance = threading.Lock()
        self.taker_fee = 0.00075
        self.maker_fee = -0.00025
        self.posi_side = ''
        self.posi_price = 0
        self.posi_size = 0
        self.posi_dt = None
        self.order_ids_executed = []
        self.order_ids = []
        self.order_exec_ids = {} #list of processed exec data id
        self.order_side = {}
        self.order_price = {}
        self.order_size = {}
        self.order_dt = {}
        self.order_type = {} #Market or Limit
        self.order_status = {} #Sent, Onboarded
        self.exec_id = []
        self.realized_pnl = 0
        self.unrealized_pnl = 0
        self.total_pnl = 0
        self.total_fee = 0

        self.num_trade = 0
        self.num_buy = 0
        self.num_sell = 0
        self.num_win = 0
        self.win_rate = 0

        self.account_log = [] #{}

        th = threading.Thread(target = self.__account_thread)
        th.start()
        th2 = threading.Thread(target=self.__onemin_thread)
        th2.start()


    def add_order(self, order_id, side, price, size, type): #call from bot
        with self.lock_order:
            self.order_ids.append(order_id)
            self.order_side[order_id] = side
            self.order_price[order_id] = price
            self.order_size[order_id] = size
            self.order_dt[order_id] = datetime.now()
            self.order_type[order_id] = type
            self.order_status[order_id] = 'Sent'

    #to confirm added order in actual order data from ws
    def __confirm_order(self, order_id, side, price, size, order_type):
        if order_id in self.order_ids:
            if self.order_side[order_id] != side:
                print('order side is not matched !')
                self.order_side[order_id] = side
            elif self.order_price[order_id] != price:
                print('order price is not matched !')
                self.order_price[order_id] = price
            elif self.order_size[order_id] != size:
                print('order size is not matched !')
                self.order_size[order_id] = size
            elif self.order_type[order_id] != order_type:
                print('order type is not matched !')
                self.order_type[order_id] = order_type
            self.order_status[order_type] = 'Onboarded'
        else:
            print('Order ID unmacthed in confirm order!', order_id)


    def get_orders(self):
        return self.order_side, self.order_price, self.order_size, self.order_dt

    def get_order_ids(self):
        return self.order_ids

    def get_performance(self):
        with self.lock_performance:
            return {'total_pl':self.realized_pnl + self.unrealized_pnl + self.total_fee, 'num_trade':self.num_trade, 'win_rate':self.win_rate, 'total_fee':self.total_fee}

    def get_position(self):
        return {'side':self.posi_side, 'price':self.posi_price, 'size':self.posi_size, 'dt':self.posi_dt}

    def get_ac_log(self):
        return pd.DataFrame(self.account_log)

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
            PrivateWSData.remove_order_data(order_id)

    def __execute_order(self, order_id, exec_id, exec_side, exec_price, exec_qty, exec_comm, status):
        if status == 'Filled' or status == 'Canceled':
            self.__calc_realized_pnl(exec_side, exec_price, exec_qty)
            self.__update_position(exec_side,exec_price, exec_qty)
            self.__remove_order(order_id)
        elif status == 'PartiallyFilled':
            if exec_id not in self.order_exec_ids[order_id]:
                with self.lock_order:
                    self.order_exec_ids[order_id].append(exec_id)
                self.__update_position(exec_side, exec_price, exec_qty)
            else:
                pass #exec id is already processed
        else:
            print('Invalid order status in __execute_order!', status)



    def __calc_pnl(self): #called every 1min
        ltp = TickData.get_ltp()
        if ltp > 0:
            self.__calc_unrealized_pnl(ltp)
        with self.lock_performance:
            self.total_pnl = self.realized_pnl + self.unrealized_pnl - self.total_fee

    def __calc_realized_pnl(self, exec_side, exec_price, exec_size):
        if self.posi_side != '' and (self.posi_side != exec_side):
            pl = (1.0 / self.posi_price - 1.0/exec_price) * exec_size if self.posi_side == 'Buy' else (1.0/exec_price - 1.0 / self.posi_price) * exec_size
            self.realized_pnl += pl
        else: #additional execution
            pass


    def __calc_win_rate(self, pl):
        self.num_trade += 1
        if pl> 0:
            self.num_win +=1
        self.win_rate = round(self.num_win / self.num_trade, 2)

    def __calc_fee(self, oid, api_exec_data):
        self.total_fee += sum(list(map(lambda x: x['execComm'], api_exec_data))) / 100000000

    def __calc_unrealized_pnl(self, ltp):
        with self.lock_performance:
            if self.posi_side != '':
                self.unrealized_pnl = (1.0/self.posi_price - 1.0/ltp) * self.posi_size if self.posi_side == 'Buy' else (1.0/ltp - 1.0/self.posi_price) * self.posi_size
            else:
                self.unrealized_pnl = 0


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
            self.posi_dt = datetime.now()

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
    
    {'execID': '882a2887-da85-ea58-ce7b-3864232920cd', 'orderID': 'a3a2c878-8898-b766-2b07-315555290abb', 'clOrdID': '', 'clOrdLinkID': '', 
    'account': 243795, 'symbol': 'XBTUSD', 'side': 'Sell', 'lastQty': None, 'lastPx': None, 'underlyingLastPx': None, 'lastMkt': '', 'lastLiquidityInd': '', 
    'simpleOrderQty': None, 'orderQty': 10, 'price': 7525, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 
    'settlCurrency': 'XBt', 'execType': 'New', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 
    'exDestination': 'XBME', 'ordStatus': 'New', 'triggered': '', 'workingIndicator': True, 'ordRejReason': '', 'simpleLeavesQty': None, 
    'leavesQty': 10, 'simpleCumQty': None, 'cumQty': 0, 'avgPx': None, 'commission': None, 'tradePublishIndicator': '', 'multiLegReportingType': 'SingleSecurity', 
    'text': 'Submitted via API.', 'trdMatchID': '00000000-0000-0000-0000-000000000000', 'execCost': None, 'execComm': None, 'homeNotional': None, 'foreignNotional': None, 
    'transactTime': '2019-12-08T13:59:47.513Z', 'timestamp': '2019-12-08T13:59:47.513Z'}
    '''

    '''order data: {'orderID': '234bd7c9-862e-4245-8342-eef9b7a7af89', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Sell', 'simpleOrderQty': None, 'orderQty': 10, 'price': 7525.5, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'New', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 10, 'simpleCumQty': None, 'cumQty': 0, 'avgPx': None, 'multiLegReportingType': 'SingleSecurity', 'text': 'Submitted via API.', 'transactTime': '2019-12-08T14:08:14.609Z', 'timestamp': '2019-12-08T14:08:14.609Z'}
        exex data: {'execID': '7485c375-509a-a64a-a73d-8440921840e0', 'orderID': '234bd7c9-862e-4245-8342-eef9b7a7af89', 'clOrdID': '', 'clOrdLinkID': '', 'account': 243795, 'symbol': 'XBTUSD', 'side': 'Sell', 'lastQty': None, 'lastPx': None, 'underlyingLastPx': None, 'lastMkt': '', 'lastLiquidityInd': '', 'simpleOrderQty': None, 'orderQty': 10, 'price': 7525.5, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'execType': 'New', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'New', 'triggered': '', 'workingIndicator': True, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 10, 'simpleCumQty': None, 'cumQty': 0, 'avgPx': None, 'commission': None, 'tradePublishIndicator': '', 'multiLegReportingType': 'SingleSecurity', 'text': 'Submitted via API.', 'trdMatchID': '00000000-0000-0000-0000-000000000000', 'execCost': None, 'execComm': None, 'homeNotional': None, 'foreignNotional': None, 'transactTime': '2019-12-08T14:08:14.609Z', 'timestamp': '2019-12-08T14:08:14.609Z'}
        order data: {'orderID': '234bd7c9-862e-4245-8342-eef9b7a7af89', 'ordStatus': 'Filled', 'workingIndicator': False, 'leavesQty': 0, 'cumQty': 10, 'avgPx': 7525.5, 'clOrdID': '', 'account': 243795, 'symbol': 'XBTUSD', 'timestamp': '2019-12-08T14:08:14.609Z'}
    '''

    '''
    market orderの時は、order filledになった時にexecute_orderで約定を反映させる
    limit orderの時は、常に同一価格の約定と想定して、order dataのleavesQty、avgPxを使う。
    limit orderが途中でキャンセルされた場合には、status=cancelとなった時点でそれを察知してorder listから削除
    *order出した時はlimit orderだが、約定時にmarket order扱いになった時の処置　（）
    '''

    def __account_thread(self):
        while SystemFlg.get_system_flg():
            for oid in self.order_ids:
                order_data = PrivateWSData.get_order_data(oid)
                exec_data = PrivateWSData.get_exec_data(oid)
                if order_data is not None:
                    if order_data['ordStatus'] == 'New' and self.order_status[oid] == 'Sent':
                        self.__confirm_order(oid, order_data['side'],order_data['price'],order_data['orderQty'],order_data['ordType'])
                    elif exec_data['ordStatus'] == 'PartiallyFilled' and order_data['ordStatus'] == 'PartiallyFilled':
                        self.__execute_order(order_data['orderID'], exec_data['execID'], order_data['side'], order_data['price'], self.order_size[oid] - order_data['leavesQty'], order_data['prdStatus'])
                    elif order_data['ordStatus'] == 'Filled' or order_data['ordStatus'] == 'Canceled':
                        time.sleep(1)
                        trades = Trade.get_trades(10)
                        print(len(trades))
                        print(trades[0])
                        print(trades[0]['info'])
                        time.sleep(10)
                        api_exec_data = list(map(lambda x: x['info']['execComm'] if x['info']['orderID'] == oid and str(x['info']['execComm']) != 'None' else 0, trades))
                        print(api_exec_data)
                        self.__calc_fee(oid,api_exec_data)
                        if order_data['ordStatus'] == 'Filled' and order_data['leavesQty'] > 0:
                            print('status is Filled but leavesQty is not 0!', order_data)
                        self.__execute_order(order_data['orderID'], '', order_data['side'], order_data['price'], self.order_size[oid] - order_data['leavesQty'], order_data['ordStatus'])
                    else:
                        print('Unknown order status!', order_data['ordStatus'])



    def __onemin_thread(self):
        while SystemFlg.get_system_flg():
            time.sleep(60)
            self.__calc_pnl()










